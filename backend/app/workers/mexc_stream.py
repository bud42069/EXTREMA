"""
Binance Futures WebSocket stream worker.
Maintains real-time orderbook depth, trades, CVD, and imbalance metrics.
"""
import asyncio
import json
import time
from collections import deque
from typing import Optional

import websockets
import numpy as np

from ..utils.logging import get_logger
from ..utils.micro_store import MicroSnapshot, set_snapshot, reset_snapshot

logger = get_logger(__name__)


class MexcStreamWorker:
    """
    WebSocket worker for Binance perpetual futures data.
    Streams depth (L2, top 20) and trades for a symbol.
    Computes real-time CVD, imbalance, and spread metrics.
    """
    
    def __init__(
        self,
        symbol: str = "SOLUSDT",
        depth_levels: int = 20,
        cvd_window: int = 100,
        update_interval: float = 0.5
    ):
        self.symbol = symbol.lower()  # Binance uses lowercase symbols
        self.depth_levels = depth_levels
        self.cvd_window = cvd_window
        self.update_interval = update_interval
        
        # Binance WebSocket URLs - Using combined streams
        # Try data-stream endpoint for market data access
        depth_stream = f"{self.symbol}@depth@100ms"
        trade_stream = f"{self.symbol}@trade"
        self.ws_url = f"wss://data-stream.binance.vision/stream?streams={depth_stream}/{trade_stream}"
        
        # State
        self.running = False
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        
        # Orderbook
        self.bids: dict[float, float] = {}  # price -> qty
        self.asks: dict[float, float] = {}
        
        # Trades & CVD
        self.last_mid = 0.0
        self.cvd = 0.0
        self.cvd_history = deque(maxlen=cvd_window)
        self.trade_volume = deque(maxlen=50)
        
        # Metrics
        self.best_bid = 0.0
        self.best_ask = 0.0
        self.spread_bps = 0.0
        self.bid_agg = 0.0
        self.ask_agg = 0.0
        self.ladder_imbalance = 0.0
        self.cvd_slope = 0.0
    
    async def start(self):
        """Start the WebSocket stream worker."""
        self.running = True
        logger.info(f"Starting Binance stream worker for {self.symbol}")
        
        while self.running:
            try:
                await self._connect_and_stream()
            except Exception as e:
                logger.error(f"Stream error: {e}")
                await asyncio.sleep(5)  # Reconnect delay
        
        logger.info("Binance stream worker stopped")
    
    def stop(self):
        """Stop the WebSocket stream worker."""
        self.running = False
        # Close the websocket if it's open
        if self.ws:
            import asyncio
            try:
                asyncio.create_task(self.ws.close())
            except:
                pass
        reset_snapshot()
        logger.info("Binance stream worker stop requested")
    
    async def _connect_and_stream(self):
        """Connect to Binance WebSocket and stream data."""
        async with websockets.connect(
            self.ws_url,
            ping_interval=20,
            ping_timeout=60
        ) as ws:
            self.ws = ws
            logger.info(f"Connected to Binance WebSocket for {self.symbol}")
            
            # No subscription needed for combined streams - they auto-start
            # Main message loop
            async for message in ws:
                try:
                    await self._handle_message(message)
                except Exception as e:
                    logger.error(f"Message handling error: {e}")
    
    async def _handle_message(self, message: str):
        """Process incoming WebSocket messages from Binance combined streams."""
        data = json.loads(message)
        
        # Combined stream format: {"stream":"<streamName>","data":{...}}
        if "stream" in data and "data" in data:
            stream_name = data["stream"]
            stream_data = data["data"]
            
            # Handle depth updates
            if "depth" in stream_name or stream_data.get("e") == "depthUpdate":
                await self._handle_depth(stream_data)
            # Handle trade updates
            elif "trade" in stream_name or stream_data.get("e") == "trade":
                await self._handle_trade(stream_data)
    
    
    async def _handle_depth(self, data: dict):
        """Process Binance orderbook depth update."""
        try:
            # Binance depth update format:
            # {"e":"depthUpdate","E":timestamp,"s":"SOLUSDT","U":firstUpdateId,"u":finalUpdateId,
            #  "b":[["price","qty"]],"a":[["price","qty"]]}
            
            # Update bids (remove zero-qty levels, update others)
            for price_str, qty_str in data.get("b", []):
                price, qty = float(price_str), float(qty_str)
                if qty == 0:
                    self.bids.pop(price, None)
                else:
                    self.bids[price] = qty
            
            # Update asks (remove zero-qty levels, update others)
            for price_str, qty_str in data.get("a", []):
                price, qty = float(price_str), float(qty_str)
                if qty == 0:
                    self.asks.pop(price, None)
                else:
                    self.asks[price] = qty
            
            # Calculate metrics
            self._calculate_depth_metrics()
            
            # Update snapshot
            self._update_snapshot()
            
        except Exception as e:
            logger.error(f"Depth processing error: {e}")
    
    async def _handle_trade(self, data: dict):
        """Process Binance trade update and update CVD."""
        try:
            # Binance trade format:
            # {"e":"trade","E":timestamp,"s":"SOLUSDT","t":tradeId,
            #  "p":"price","q":"quantity","T":tradeTime,"m":isBuyerMaker}
            
            price = float(data.get("p", 0))
            qty = float(data.get("q", 0))
            is_buyer_maker = data.get("m", False)  # True if buyer is maker (sell aggressor)
            
            # Update last mid
            if self.best_bid > 0 and self.best_ask > 0:
                self.last_mid = (self.best_bid + self.best_ask) / 2
            
            # Binance: m=True means buyer is maker -> sell market order (-)
            #          m=False means buyer is taker -> buy market order (+)
            if is_buyer_maker:
                delta = -qty  # Sell aggressor
            else:
                delta = qty  # Buy aggressor
            
            self.cvd += delta
            self.cvd_history.append(self.cvd)
            self.trade_volume.append(qty)
            
            # Calculate CVD slope
            self._calculate_cvd_slope()
            
        except Exception as e:
            logger.error(f"Trade processing error: {e}")
    
    def _calculate_depth_metrics(self):
        """Calculate spread, depth aggregates, and ladder imbalance."""
        if not self.bids or not self.asks:
            return
        
        # Best bid/ask
        self.best_bid = max(self.bids.keys())
        self.best_ask = min(self.asks.keys())
        
        # Spread in basis points
        mid = (self.best_bid + self.best_ask) / 2
        self.spread_bps = ((self.best_ask - self.best_bid) / mid) * 10000
        
        # Aggregate depth (top N levels)
        self.bid_agg = sum(self.bids.values())
        self.ask_agg = sum(self.asks.values())
        
        # Ladder imbalance
        total_depth = self.bid_agg + self.ask_agg
        if total_depth > 0:
            self.ladder_imbalance = (self.bid_agg - self.ask_agg) / total_depth
        else:
            self.ladder_imbalance = 0.0
    
    def _calculate_cvd_slope(self):
        """Calculate CVD slope using linear regression over rolling window."""
        if len(self.cvd_history) < 10:
            self.cvd_slope = 0.0
            return
        
        # Simple linear regression
        y = np.array(list(self.cvd_history))
        x = np.arange(len(y))
        
        # Slope = covariance(x, y) / variance(x)
        x_mean = x.mean()
        y_mean = y.mean()
        
        numerator = np.sum((x - x_mean) * (y - y_mean))
        denominator = np.sum((x - x_mean) ** 2)
        
        if denominator > 0:
            self.cvd_slope = numerator / denominator
        else:
            self.cvd_slope = 0.0
    
    def _update_snapshot(self):
        """Update the global microstructure snapshot."""
        trade_v = sum(self.trade_volume) if self.trade_volume else 0.0
        
        ok = (
            self.best_bid > 0 and
            self.best_ask > 0 and
            self.spread_bps < 50 and  # Reasonable spread
            self.bid_agg > 0 and
            self.ask_agg > 0
        )
        
        snapshot = MicroSnapshot(
            ts=time.time(),
            best_bid=self.best_bid,
            best_ask=self.best_ask,
            spread_bps=self.spread_bps,
            bid_agg=self.bid_agg,
            ask_agg=self.ask_agg,
            ladder_imbalance=self.ladder_imbalance,
            cvd=self.cvd,
            cvd_slope=self.cvd_slope,
            trade_v=trade_v,
            ok=ok
        )
        
        set_snapshot(snapshot)


# Global worker instance
_worker: Optional[MexcStreamWorker] = None


async def start_mexc_worker(symbol: str = "SOLUSDT"):
    """Start the MEXC stream worker."""
    global _worker
    
    if _worker and _worker.running:
        logger.warning("MEXC worker already running")
        return
    
    _worker = MexcStreamWorker(symbol=symbol)
    asyncio.create_task(_worker.start())
    logger.info("MEXC stream worker started")


def stop_mexc_worker():
    """Stop the MEXC stream worker."""
    global _worker
    
    if _worker:
        _worker.stop()
        _worker = None
        logger.info("MEXC stream worker stopped")


def is_worker_running() -> bool:
    """Check if the worker is currently running."""
    global _worker
    return _worker is not None and _worker.running
