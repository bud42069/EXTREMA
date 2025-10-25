"""
Multi-Timeframe Feature Extraction Engine.
Computes RSI, EMA, BOS, volume gates, and other indicators per timeframe.
"""
import pandas as pd
import numpy as np
from typing import Optional

from ..utils.logging import get_logger

logger = get_logger(__name__)


def compute_rsi(df: pd.DataFrame, period: int = 12, column: str = 'close') -> pd.Series:
    """
    Compute RSI indicator.
    
    Args:
        df: DataFrame with OHLC data
        period: RSI period (default 12)
        column: Column to compute RSI on
    
    Returns:
        Series with RSI values
    """
    delta = df[column].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def compute_ema(df: pd.DataFrame, span: int, column: str = 'close') -> pd.Series:
    """Compute EMA indicator."""
    return df[column].ewm(span=span, adjust=False).mean()


def compute_volume_gate(df: pd.DataFrame, window: int = 50) -> pd.Series:
    """
    Compute volume gate (volume / median volume).
    
    Args:
        df: DataFrame with volume column
        window: Rolling window for median
    
    Returns:
        Series with volume ratio
    """
    vol_median = df['volume'].rolling(window=window).median()
    return df['volume'] / vol_median


def detect_break_of_structure(df: pd.DataFrame, window: int = 20, atr_mult: float = 0.1) -> pd.Series:
    """
    Detect Break of Structure (BOS).
    A body close beyond local high/low by at least atr_mult * ATR.
    
    Args:
        df: DataFrame with OHLC data
        window: Window for local high/low detection
        atr_mult: Multiplier for ATR threshold
    
    Returns:
        Series with BOS signals (1 = bullish BOS, -1 = bearish BOS, 0 = none)
    """
    # Compute ATR
    high_low = df['high'] - df['low']
    high_close = (df['high'] - df['close'].shift()).abs()
    low_close = (df['low'] - df['close'].shift()).abs()
    
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(window=14).mean()
    
    # Local high/low
    local_high = df['high'].rolling(window=window).max()
    local_low = df['low'].rolling(window=window).min()
    
    # BOS detection
    bos = pd.Series(0, index=df.index)
    
    # Bullish BOS: close > local_high + atr_mult * ATR
    bullish_bos = df['close'] > (local_high + atr_mult * atr)
    bos[bullish_bos] = 1
    
    # Bearish BOS: close < local_low - atr_mult * ATR
    bearish_bos = df['close'] < (local_low - atr_mult * atr)
    bos[bearish_bos] = -1
    
    return bos


def compute_ema_alignment(df: pd.DataFrame, spans: list[int] = [5, 9, 21, 38]) -> dict:
    """
    Compute EMA alignment score.
    
    Args:
        df: DataFrame with close prices
        spans: List of EMA periods
    
    Returns:
        Dict with alignment metrics
    """
    emas = {}
    for span in spans:
        emas[f'ema_{span}'] = compute_ema(df, span)
    
    # Check alignment (bullish: each EMA > next longer EMA)
    aligned_count = 0
    total_checks = len(spans) - 1
    
    for i in range(len(spans) - 1):
        ema_short = emas[f'ema_{spans[i]}']
        ema_long = emas[f'ema_{spans[i+1]}']
        
        if ema_short.iloc[-1] > ema_long.iloc[-1]:
            aligned_count += 1
    
    alignment_score = aligned_count / total_checks if total_checks > 0 else 0
    
    return {
        'alignment_score': alignment_score,
        'aligned_count': aligned_count,
        'total_emas': len(spans),
        'bullish': alignment_score >= 0.75,
        'bearish': alignment_score <= 0.25,
        'emas': emas
    }


def extract_mtf_features(df: pd.DataFrame, timeframe: str) -> dict:
    """
    Extract all MTF features for a given timeframe.
    
    Args:
        df: DataFrame with OHLCV data
        timeframe: Timeframe string (5s, 15s, 30s, 1m, etc.)
    
    Returns:
        Dict with extracted features
    """
    if df is None or len(df) < 50:
        return None
    
    try:
        features = {
            'timeframe': timeframe,
            'timestamp': df.index[-1] if not df.empty else None,
            'close': df['close'].iloc[-1],
            'volume': df['volume'].iloc[-1]
        }
        
        # RSI
        rsi = compute_rsi(df, period=12)
        features['rsi_12'] = rsi.iloc[-1] if len(rsi) > 0 else None
        features['rsi_side'] = 'bull' if features['rsi_12'] and features['rsi_12'] > 50 else 'bear'
        
        # RSI cross detection (last 2 bars)
        if len(rsi) >= 2:
            rsi_prev = rsi.iloc[-2]
            rsi_curr = rsi.iloc[-1]
            features['rsi_crossed_50'] = (rsi_prev < 50 and rsi_curr > 50) or (rsi_prev > 50 and rsi_curr < 50)
            features['rsi_cross_direction'] = 'up' if (rsi_prev < 50 and rsi_curr > 50) else ('down' if (rsi_prev > 50 and rsi_curr < 50) else None)
        else:
            features['rsi_crossed_50'] = False
            features['rsi_cross_direction'] = None
        
        # EMA alignment
        ema_data = compute_ema_alignment(df, spans=[5, 9, 21, 38])
        features['ema_alignment'] = ema_data['alignment_score']
        features['ema_aligned_count'] = ema_data['aligned_count']
        features['ema_bullish'] = ema_data['bullish']
        features['ema_bearish'] = ema_data['bearish']
        
        # Volume gate
        vol_gate = compute_volume_gate(df, window=50)
        features['volume_gate'] = vol_gate.iloc[-1] if len(vol_gate) > 0 else None
        features['volume_sufficient'] = features['volume_gate'] and features['volume_gate'] >= 1.5
        
        # Break of Structure
        bos = detect_break_of_structure(df, window=20, atr_mult=0.1)
        features['bos'] = bos.iloc[-1] if len(bos) > 0 else 0
        features['bos_detected'] = features['bos'] != 0
        
        return features
    
    except Exception as e:
        logger.error(f"Error extracting MTF features for {timeframe}: {e}")
        return None


def compute_vwap_deviation(df: pd.DataFrame, atr_mult: float = 0.02) -> dict:
    """
    Compute VWAP and deviation from it.
    
    Args:
        df: DataFrame with OHLCV data
        atr_mult: Multiplier for ATR threshold
    
    Returns:
        Dict with VWAP metrics
    """
    if df is None or len(df) < 2:
        return None
    
    try:
        # Compute VWAP
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        vwap = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
        
        # Compute ATR
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift()).abs()
        low_close = (df['low'] - df['close'].shift()).abs()
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=14).mean()
        
        # Current price vs VWAP
        current_price = df['close'].iloc[-1]
        current_vwap = vwap.iloc[-1]
        current_atr = atr.iloc[-1]
        
        deviation = abs(current_price - current_vwap)
        threshold = atr_mult * current_atr
        
        return {
            'vwap': current_vwap,
            'price': current_price,
            'deviation': deviation,
            'deviation_pct': (deviation / current_vwap) * 100 if current_vwap > 0 else 0,
            'within_threshold': deviation <= threshold,
            'above_vwap': current_price > current_vwap,
            'below_vwap': current_price < current_vwap
        }
    
    except Exception as e:
        logger.error(f"Error computing VWAP deviation: {e}")
        return None
