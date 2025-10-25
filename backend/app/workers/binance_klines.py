"""
Binance 1-second kline WebSocket stream worker.
Provides the foundation for MTF (1s/5s/15s/30s/1m) feature extraction.
"""
import asyncio
import json
import time
from collections import deque
from typing import Optional, Callable
from datetime import datetime, timezone

import websockets
import pandas as pd

from ..utils.logging import get_logger
from ..utils.mtf_store import update_kline, get_resampled

logger = get_logger(__name__)


class BinanceKlineWorker:
    """
    WebSocket worker for Binance 1-second klines.
    Streams klines and triggers resampling to higher timeframes.
    """
    
    def __init__(
        self,
        symbol: str = "SOLUSDT",
        interval: str = "1s"
    ):
        self.symbol = symbol.lower()
        self.interval = interval
        
        # Binance kline stream URL
        kline_stream = f"{self.symbol}@kline_{interval}"
        self.ws_url = f"wss://data-stream.binance.vision/ws/{kline_stream}"
        
        # State
        self.running = False
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        
        # Callbacks for resampled data
        self.callbacks: dict[str, Callable] = {}
        
        # Stats
        self.kline_count = 0
        self.last_kline_time = 0
    
    async def start(self):
        """Start the WebSocket stream worker."""
        self.running = True
        logger.info(f"Starting Binance kline worker for {self.symbol} ({self.interval})")
        
        while self.running:
            try:
                await self._connect_and_stream()
            except Exception as e:
                logger.error(f"Kline stream error: {e}")
                await asyncio.sleep(5)  # Reconnect delay
        
        logger.info("Binance kline worker stopped")
    
    def stop(self):
        """Stop the WebSocket stream worker."""
        self.running = False
    
    async def _connect_and_stream(self):
        """Connect to Binance WebSocket and stream klines."""
        async with websockets.connect(
            self.ws_url,
            ping_interval=20,
            ping_timeout=60
        ) as ws:
            self.ws = ws
            logger.info(f"Connected to Binance kline stream for {self.symbol}")
            
            # Main message loop
            async for message in ws:
                try:
                    await self._handle_message(message)
                except Exception as e:
                    logger.error(f"Kline message handling error: {e}")
    
    async def _handle_message(self, message: str):
        """Process incoming kline WebSocket messages."""
        data = json.loads(message)
        
        # Binance kline format: {"e":"kline","E":timestamp,"s":"SOLUSDT","k":{...}}
        if data.get("e") == "kline":
            kline_data = data["k"]
            
            # Extract kline fields
            kline = {
                "timestamp": int(kline_data["t"]) // 1000,  # Convert to seconds
                "open": float(kline_data["o"]),
                "high": float(kline_data["h"]),
                "low": float(kline_data["l"]),
                "close": float(kline_data["c"]),
                "volume": float(kline_data["v"]),
                "is_closed": kline_data["x"]  # True if kline is finalized
            }
            
            # Only process closed klines for consistency
            if kline["is_closed"]:
                self.kline_count += 1
                self.last_kline_time = kline["timestamp"]
                
                # Update MTF store
                await self._process_kline(kline)
    
    async def _process_kline(self, kline: dict):
        """
        Process a closed 1s kline and trigger resampling.
        """
        try:
            # Update 1s kline store
            update_kline("1s", kline)
            
            # Trigger resampling for higher TFs
            # Check if we need to resample (every 5s, 15s, 30s, 60s)
            ts = kline["timestamp"]
            
            # 5s resampling (every 5 seconds)
            if ts % 5 == 0:
                df_5s = get_resampled("5s")
                if df_5s is not None and "5s" in self.callbacks:
                    await self.callbacks["5s"](df_5s)
            
            # 15s resampling (every 15 seconds)
            if ts % 15 == 0:
                df_15s = get_resampled("15s")
                if df_15s is not None and "15s" in self.callbacks:
                    await self.callbacks["15s"](df_15s)
            
            # 30s resampling (every 30 seconds)
            if ts % 30 == 0:
                df_30s = get_resampled("30s")
                if df_30s is not None and "30s" in self.callbacks:
                    await self.callbacks["30s"](df_30s)
            
            # 1m resampling (every 60 seconds)
            if ts % 60 == 0:
                df_1m = get_resampled("1m")
                if df_1m is not None and "1m" in self.callbacks:
                    await self.callbacks["1m"](df_1m)
        
        except Exception as e:
            logger.error(f"Error processing kline: {e}")
    
    def register_callback(self, timeframe: str, callback: Callable):
        """
        Register callback functions for specific timeframes.
        """
        self.callbacks[timeframe] = callback
        logger.info(f"Registered callback for {timeframe} klines")
    
    def get_stats(self) -> dict:
        """Get worker statistics."""
        return {
            "symbol": self.symbol,
            "interval": self.interval,
            "running": self.running,
            "kline_count": self.kline_count,
            "last_kline_time": self.last_kline_time,
            "connected": self.ws is not None
        }
