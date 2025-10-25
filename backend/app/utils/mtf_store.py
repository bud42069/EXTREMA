"""
Multi-Timeframe (MTF) data store with resampling.
Maintains rolling windows for 1s/5s/15s/30s/1m klines and provides resampling.
"""
from collections import deque
from typing import Optional
import pandas as pd
from datetime import datetime

from .logging import get_logger

logger = get_logger(__name__)

# Global stores for each timeframe (deque for memory efficiency)
KLINE_STORES = {
    "1s": deque(maxlen=3600),   # Last 1 hour of 1s klines
    "5s": deque(maxlen=720),    # Last 1 hour of 5s klines
    "15s": deque(maxlen=240),   # Last 1 hour of 15s klines
    "30s": deque(maxlen=120),   # Last 1 hour of 30s klines
    "1m": deque(maxlen=500),    # Last ~8 hours of 1m klines
    "15m": deque(maxlen=200),   # Last ~50 hours of 15m klines
    "1h": deque(maxlen=200),    # Last ~8 days of 1h klines
    "4h": deque(maxlen=200),    # Last ~33 days of 4h klines
    "1d": deque(maxlen=90),     # Last ~3 months of 1d klines
}


def update_kline(timeframe: str, kline: dict):
    """
    Update kline store for a specific timeframe.
    
    Args:
        timeframe: Timeframe string (1s, 5s, 15s, 30s, 1m, etc.)
        kline: Dict with keys: timestamp, open, high, low, close, volume
    """
    if timeframe not in KLINE_STORES:
        logger.warning(f"Unknown timeframe: {timeframe}")
        return
    
    KLINE_STORES[timeframe].append(kline)


def get_klines(timeframe: str, limit: Optional[int] = None) -> list:
    """
    Get klines for a specific timeframe.
    
    Args:
        timeframe: Timeframe string
        limit: Maximum number of klines to return (most recent)
    
    Returns:
        List of kline dicts
    """
    if timeframe not in KLINE_STORES:
        return []
    
    klines = list(KLINE_STORES[timeframe])
    
    if limit is not None and len(klines) > limit:
        return klines[-limit:]
    
    return klines


def get_resampled(target_tf: str) -> Optional[pd.DataFrame]:
    """
    Resample 1s klines to target timeframe.
    
    Args:
        target_tf: Target timeframe (5s, 15s, 30s, 1m)
    
    Returns:
        DataFrame with OHLCV columns, or None if insufficient data
    """
    # Get 1s klines
    klines_1s = get_klines("1s")
    
    if not klines_1s:
        return None
    
    # Convert to DataFrame
    df = pd.DataFrame(klines_1s)
    df['time'] = pd.to_datetime(df['timestamp'], unit='s')
    df.set_index('time', inplace=True)
    
    # Resample based on target timeframe
    resample_map = {
        "5s": "5S",
        "15s": "15S",
        "30s": "30S",
        "1m": "1T"
    }
    
    if target_tf not in resample_map:
        logger.warning(f"Unsupported target timeframe: {target_tf}")
        return None
    
    rule = resample_map[target_tf]
    
    # Resample OHLCV
    resampled = df.resample(rule).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()
    
    # Store resampled data in appropriate store
    for idx, row in resampled.iterrows():
        kline = {
            'timestamp': int(idx.timestamp()),
            'open': row['open'],
            'high': row['high'],
            'low': row['low'],
            'close': row['close'],
            'volume': row['volume']
        }
        update_kline(target_tf, kline)
    
    return resampled


def reset_stores():
    """Clear all kline stores."""
    for store in KLINE_STORES.values():
        store.clear()
    logger.info("All MTF stores cleared")


def get_store_stats() -> dict:
    """Get statistics about all stores."""
    return {
        tf: len(store) for tf, store in KLINE_STORES.items()
    }
