"""
Technical indicator calculations for trading signals.
Implements ATR14, RSI14, Bollinger Bands, EMA slope, and volume z-score.
"""
import pandas as pd
import numpy as np
from typing import Tuple


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Average True Range (ATR).
    
    Args:
        df: DataFrame with 'high', 'low', 'close' columns
        period: ATR period (default 14)
    
    Returns:
        Series with ATR values
    """
    high = df['high']
    low = df['low']
    close = df['close']
    
    # True Range calculation
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    return atr


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index (RSI).
    
    Args:
        df: DataFrame with 'close' column
        period: RSI period (default 14)
    
    Returns:
        Series with RSI values (0-100)
    """
    close = df['close']
    delta = close.diff()
    
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate Bollinger Bands.
    
    Args:
        df: DataFrame with 'close' column
        period: Moving average period (default 20)
        std_dev: Standard deviation multiplier (default 2.0)
    
    Returns:
        Tuple of (upper_band, middle_band, lower_band, bb_width)
    """
    close = df['close']
    
    middle = close.rolling(window=period).mean()
    std = close.rolling(window=period).std()
    
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    
    # BB width as percentage
    bb_width = (upper - lower) / middle
    
    return upper, middle, lower, bb_width


def calculate_ema(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """
    Calculate Exponential Moving Average (EMA).
    
    Args:
        df: DataFrame with 'close' column
        period: EMA period
    
    Returns:
        Series with EMA values
    """
    return df['close'].ewm(span=period, adjust=False).mean()


def calculate_ema_slope(df: pd.DataFrame, period: int = 20, lookback: int = 5) -> pd.Series:
    """
    Calculate EMA slope (rate of change).
    
    Args:
        df: DataFrame with 'close' column
        period: EMA period
        lookback: Number of bars to calculate slope over
    
    Returns:
        Series with EMA slope values
    """
    ema = calculate_ema(df, period)
    slope = ema.diff(lookback) / lookback
    
    return slope


def calculate_volume_zscore(df: pd.DataFrame, period: int = 50) -> pd.Series:
    """
    Calculate volume z-score (standardized volume).
    
    Args:
        df: DataFrame with 'Volume' column
        period: Lookback period for mean and std calculation
    
    Returns:
        Series with volume z-scores
    """
    volume = df['Volume']
    
    mean = volume.rolling(window=period).mean()
    std = volume.rolling(window=period).std()
    
    z_score = (volume - mean) / std
    
    return z_score


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add all indicators to the dataframe.
    
    Args:
        df: DataFrame with OHLCV data
    
    Returns:
        DataFrame with added indicator columns
    """
    df = df.copy()
    
    # ATR14
    df['ATR14'] = calculate_atr(df, period=14)
    
    # RSI14
    df['RSI14'] = calculate_rsi(df, period=14)
    
    # Bollinger Bands
    df['BB_Upper'], df['BB_Middle'], df['BB_Lower'], df['BB_Width'] = calculate_bollinger_bands(df, period=20)
    
    # EMA20 and slope
    df['EMA20'] = calculate_ema(df, period=20)
    df['EMA_Slope'] = calculate_ema_slope(df, period=20, lookback=5)
    
    # Volume z-score
    df['Volume_ZScore'] = calculate_volume_zscore(df, period=50)
    
    # ATR5 for micro confirmation
    df['ATR5'] = calculate_atr(df, period=5)
    
    return df


def normalize_price(price: float, close: float) -> float:
    """Normalize price relative to close for percentage calculations."""
    return (price - close) / close * 100
