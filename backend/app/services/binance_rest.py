"""
Binance REST API client for fetching historical klines.
Provides higher timeframe data (15m/1h/4h/1D) for context confluence.
"""
import httpx
import asyncio
from typing import Optional, List
from datetime import datetime, timezone

from ..utils.logging import get_logger
from ..utils.mtf_store import update_kline

logger = get_logger(__name__)


class BinanceRestClient:
    """
    REST API client for fetching historical klines from Binance.
    """
    
    def __init__(self):
        # Try futures API which has different geo-restrictions
        self.base_url = "https://fapi.binance.com/fapi/v1"
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Timeframe mapping (internal -> Binance API)
        self.interval_map = {
            "5m": "5m",
            "15m": "15m",
            "1h": "1h",
            "4h": "4h",
            "1d": "1d"
        }
        
        # Update intervals (in seconds)
        self.update_intervals = {
            "5m": 5 * 60,      # Update every 5 minutes
            "15m": 15 * 60,    # Update every 15 minutes
            "1h": 60 * 60,     # Update every 1 hour
            "4h": 4 * 60 * 60, # Update every 4 hours
            "1d": 24 * 60 * 60 # Update every 24 hours
        }
        
        # Tasks for periodic updates
        self.update_tasks = {}
        self.running = False
    
    async def fetch_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 500
    ) -> Optional[List[dict]]:
        """
        Fetch historical klines from Binance REST API.
        
        Args:
            symbol: Trading pair (e.g., SOLUSDT)
            interval: Timeframe (5m, 15m, 1h, 4h, 1d)
            limit: Number of klines to fetch (max 1000)
        
        Returns:
            List of kline dicts, or None on error
        """
        try:
            # Map internal interval to Binance format
            binance_interval = self.interval_map.get(interval)
            if not binance_interval:
                logger.error(f"Unsupported interval: {interval}")
                return None
            
            # Build request
            url = f"{self.base_url}/klines"
            params = {
                "symbol": symbol.upper(),
                "interval": binance_interval,
                "limit": min(limit, 1000)  # Binance max is 1000
            }
            
            logger.debug(f"Fetching {limit} {interval} klines for {symbol}")
            
            # Make request
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            # Convert to internal format
            klines = []
            for item in data:
                kline = {
                    "timestamp": int(item[0]) // 1000,  # Convert ms to seconds
                    "open": float(item[1]),
                    "high": float(item[2]),
                    "low": float(item[3]),
                    "close": float(item[4]),
                    "volume": float(item[5])
                }
                klines.append(kline)
            
            logger.info(f"Fetched {len(klines)} {interval} klines for {symbol}")
            return klines
        
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching klines: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error fetching klines: {e}")
            return None
    
    async def populate_store(
        self,
        symbol: str,
        interval: str,
        limit: int = 500
    ) -> bool:
        """
        Fetch klines and populate the MTF store.
        
        Args:
            symbol: Trading pair
            interval: Timeframe
            limit: Number of klines to fetch
        
        Returns:
            True if successful, False otherwise
        """
        try:
            klines = await self.fetch_klines(symbol, interval, limit)
            
            if not klines:
                return False
            
            # Update store with all klines
            for kline in klines:
                update_kline(interval, kline)
            
            logger.info(f"Populated {interval} store with {len(klines)} klines")
            return True
        
        except Exception as e:
            logger.error(f"Error populating {interval} store: {e}")
            return False
    
    async def periodic_update(self, symbol: str, interval: str):
        """
        Periodically update klines for a specific timeframe.
        
        Args:
            symbol: Trading pair
            interval: Timeframe to update
        """
        update_interval = self.update_intervals.get(interval, 60)
        
        logger.info(f"Starting periodic updates for {symbol} {interval} (every {update_interval}s)")
        
        while self.running:
            try:
                # Fetch latest kline
                klines = await self.fetch_klines(symbol, interval, limit=2)
                
                if klines:
                    # Update store with latest kline
                    latest = klines[-1]
                    update_kline(interval, latest)
                    logger.debug(f"Updated {interval} store with latest kline")
                
                # Wait for next update
                await asyncio.sleep(update_interval)
            
            except Exception as e:
                logger.error(f"Error in periodic update for {interval}: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def start_all(self, symbol: str = "SOLUSDT"):
        """
        Start periodic updates for all higher timeframes.
        
        Args:
            symbol: Trading pair
        """
        self.running = True
        
        # Initial population
        logger.info("Populating higher timeframe stores...")
        
        for interval in ["5m", "15m", "1h", "4h", "1d"]:
            success = await self.populate_store(symbol, interval, limit=200)
            if success:
                logger.info(f"✅ {interval} store populated")
            else:
                logger.warning(f"⚠️ Failed to populate {interval} store")
        
        # Start periodic update tasks
        logger.info("Starting periodic update tasks...")
        
        for interval in ["15m", "1h", "4h", "1d"]:
            task = asyncio.create_task(self.periodic_update(symbol, interval))
            self.update_tasks[interval] = task
            logger.info(f"✅ {interval} periodic updates started")
        
        logger.info("All higher timeframe updates active")
    
    async def stop_all(self):
        """
        Stop all periodic update tasks.
        """
        self.running = False
        
        # Cancel all tasks
        for interval, task in self.update_tasks.items():
            task.cancel()
            logger.info(f"Stopped {interval} updates")
        
        self.update_tasks.clear()
        
        # Close HTTP client
        await self.client.aclose()
        
        logger.info("All higher timeframe updates stopped")


# Global instance
binance_rest_client = BinanceRestClient()
