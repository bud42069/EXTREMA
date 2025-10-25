"""
Multi-source REST API client for fetching historical klines.
Uses CryptoCompare API (no geo-restrictions) as fallback for higher TF data.
"""
import httpx
import asyncio
from typing import Optional, List
from datetime import datetime, timezone, timedelta

from ..utils.logging import get_logger
from ..utils.mtf_store import update_kline

logger = get_logger(__name__)


class MultiSourceRestClient:
    """
    REST API client for fetching historical klines from multiple sources.
    Primary: CryptoCompare (no geo-restrictions)
    Fallback: Can add others as needed
    """
    
    def __init__(self):
        self.base_url = "https://min-api.cryptocompare.com/data/v2"
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Timeframe mapping (internal -> CryptoCompare API)
        self.interval_map = {
            "5m": ("histominute", 5),
            "15m": ("histominute", 15),
            "1h": ("histohour", 1),
            "4h": ("histohour", 4),
            "1d": ("histoday", 1)
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
        Fetch historical klines from CryptoCompare.
        
        Args:
            symbol: Trading pair (e.g., SOLUSDT -> SOL/USDT)
            interval: Timeframe (5m, 15m, 1h, 4h, 1d)
            limit: Number of klines to fetch
        
        Returns:
            List of kline dicts, or None on error
        """
        try:
            # Map interval
            if interval not in self.interval_map:
                logger.error(f"Unsupported interval: {interval}")
                return None
            
            endpoint_type, aggregate = self.interval_map[interval]
            
            # Parse symbol (SOLUSDT -> SOL, USDT)
            if "USDT" in symbol.upper():
                base = symbol.upper().replace("USDT", "")
                quote = "USDT"
            else:
                base = "SOL"
                quote = "USDT"
            
            # Build request
            url = f"{self.base_url}/{endpoint_type}"
            params = {
                "fsym": base,
                "tsym": quote,
                "limit": min(limit, 2000),  # CryptoCompare max
                "aggregate": aggregate
            }
            
            logger.debug(f"Fetching {limit} {interval} klines for {base}/{quote}")
            
            # Make request
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            if data.get("Response") != "Success":
                logger.error(f"CryptoCompare API error: {data.get('Message')}")
                return None
            
            # Convert to internal format
            klines = []
            for item in data["Data"]["Data"]:
                kline = {
                    "timestamp": item["time"],
                    "open": float(item["open"]),
                    "high": float(item["high"]),
                    "low": float(item["low"]),
                    "close": float(item["close"]),
                    "volume": float(item["volumeto"])  # volumeto is in quote currency
                }
                klines.append(kline)
            
            logger.info(f"Fetched {len(klines)} {interval} klines for {base}/{quote}")
            return klines
        
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching klines: {e.response.status_code}")
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
                # Fetch latest klines
                klines = await self.fetch_klines(symbol, interval, limit=5)
                
                if klines:
                    # Update store with latest klines
                    for kline in klines[-2:]:  # Last 2 klines
                        update_kline(interval, kline)
                    logger.debug(f"Updated {interval} store with latest klines")
                
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
        logger.info("Populating higher timeframe stores with CryptoCompare...")
        
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
multi_source_rest_client = MultiSourceRestClient()

