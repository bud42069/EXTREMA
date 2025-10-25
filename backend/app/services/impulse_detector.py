"""
1-Minute Impulse Detection Engine (Phase 1)
Implements RSI-12 hold, BOS, and volume gates for micro-confirmation.
Part of the SOLUSDT Swing-Capture Playbook v1.0
"""
import pandas as pd
import numpy as np
from typing import Optional, Tuple, Dict
from ..utils.logging import get_logger

logger = get_logger(__name__)


def compute_rsi_12(df: pd.DataFrame, column: str = 'close') -> pd.Series:
    """
    Compute RSI-12 for 1-minute impulse detection.
    
    Args:
        df: DataFrame with price data
        column: Column to compute RSI on
    
    Returns:
        Series with RSI-12 values
    """
    delta = df[column].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=12).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=12).mean()
    
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def compute_atr_1m(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Compute ATR for 1-minute timeframe.
    
    Args:
        df: DataFrame with OHLC data
        period: ATR period
    
    Returns:
        Series with ATR values
    """
    high_low = df['high'] - df['low']
    high_close = (df['high'] - df['close'].shift()).abs()
    low_close = (df['low'] - df['close'].shift()).abs()
    
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    return atr


def detect_bos_1m(df: pd.DataFrame, window: int = 20, atr_mult: float = 0.1) -> pd.Series:
    """
    Detect Break of Structure on 1-minute timeframe.
    Body close beyond prior micro HL/LH by >= 0.1 × ATR(1m).
    
    Args:
        df: DataFrame with OHLC data
        window: Window for local high/low detection
        atr_mult: Multiplier for ATR threshold (default 0.1)
    
    Returns:
        Series with BOS signals (1 = bullish, -1 = bearish, 0 = none)
    """
    # Compute ATR
    atr = compute_atr_1m(df)
    
    # Local high/low (prior micro structure)
    local_high = df['high'].rolling(window=window).max().shift(1)
    local_low = df['low'].rolling(window=window).min().shift(1)
    
    # BOS detection
    bos = pd.Series(0, index=df.index)
    
    # Bullish BOS: close > local_high + atr_mult * ATR
    bullish_bos = df['close'] > (local_high + atr_mult * atr)
    bos[bullish_bos] = 1
    
    # Bearish BOS: close < local_low - atr_mult * ATR
    bearish_bos = df['close'] < (local_low - atr_mult * atr)
    bos[bearish_bos] = -1
    
    return bos


def check_rsi_hold(df: pd.DataFrame, side: str, min_bars: int = 2) -> Tuple[bool, int]:
    """
    Check if RSI-12 holds on the trade side for >= min_bars consecutive bars.
    
    Args:
        df: DataFrame with RSI-12 computed
        side: 'long' or 'short'
        min_bars: Minimum consecutive bars required (default 2)
    
    Returns:
        Tuple of (hold_ok: bool, consecutive_bars: int)
    """
    if 'RSI_12' not in df.columns or len(df) < min_bars:
        return False, 0
    
    # Check last min_bars
    recent_rsi = df['RSI_12'].iloc[-min_bars:]
    
    if side == 'long':
        # For long: RSI should be above 50 (bullish)
        hold_ok = (recent_rsi >= 50).all()
    else:
        # For short: RSI should be below 50 (bearish)
        hold_ok = (recent_rsi <= 50).all()
    
    # Count consecutive bars
    consecutive = 0
    for val in df['RSI_12'].iloc[::-1]:  # Reverse order
        if pd.isna(val):
            break
        if (side == 'long' and val >= 50) or (side == 'short' and val <= 50):
            consecutive += 1
        else:
            break
    
    return hold_ok, consecutive


def check_volume_gate_1m(df: pd.DataFrame, mult: float = 1.5, window: int = 50) -> Tuple[bool, float]:
    """
    Check 1m volume gate: current volume >= mult × vol_med50(1m).
    
    Args:
        df: DataFrame with volume data
        mult: Volume multiplier (default 1.5, use 2.0 for A-tier)
        window: Rolling window for median
    
    Returns:
        Tuple of (gate_ok: bool, volume_ratio: float)
    """
    if len(df) < window:
        return False, 0.0
    
    vol_median = df['volume'].rolling(window=window).median()
    current_vol = df['volume'].iloc[-1]
    median_vol = vol_median.iloc[-1]
    
    if pd.isna(median_vol) or median_vol == 0:
        return False, 0.0
    
    vol_ratio = current_vol / median_vol
    gate_ok = vol_ratio >= mult
    
    return gate_ok, vol_ratio


def check_1m_impulse(
    df_1m: pd.DataFrame,
    side: str,
    rsi_hold_bars: int = 2,
    bos_atr_mult: float = 0.1,
    vol_mult: float = 1.5,
    vol_mult_tier_a: float = 2.0,
    tier: str = 'B'
) -> Dict:
    """
    Comprehensive 1-minute impulse check.
    
    Requirements per playbook:
    - RSI-12 cross and hold on trade side (>= 2 consecutive bars)
    - 1m BOS: body close beyond prior micro HL/LH by >= 0.1 × ATR(1m)
    - 1m Volume: >= 1.5× vol_med50(1m) (2.0× for A-tier)
    
    Args:
        df_1m: 1-minute DataFrame with OHLC data
        side: 'long' or 'short'
        rsi_hold_bars: Minimum consecutive bars for RSI hold
        bos_atr_mult: ATR multiplier for BOS threshold
        vol_mult: Volume multiplier for B-tier
        vol_mult_tier_a: Volume multiplier for A-tier
        tier: 'A' or 'B' (affects volume threshold)
    
    Returns:
        Dict with impulse check results
    """
    result = {
        'impulse_ok': False,
        'rsi_hold_ok': False,
        'rsi_hold_bars': 0,
        'bos_ok': False,
        'bos_signal': 0,
        'volume_ok': False,
        'volume_ratio': 0.0,
        'details': {}
    }
    
    if df_1m is None or len(df_1m) < 20:
        result['details']['error'] = 'Insufficient 1m data'
        return result
    
    try:
        # Compute indicators if not present
        if 'RSI_12' not in df_1m.columns:
            df_1m['RSI_12'] = compute_rsi_12(df_1m)
        
        if 'BOS' not in df_1m.columns:
            df_1m['BOS'] = detect_bos_1m(df_1m, atr_mult=bos_atr_mult)
        
        # Check RSI-12 hold
        rsi_hold_ok, rsi_bars = check_rsi_hold(df_1m, side, min_bars=rsi_hold_bars)
        result['rsi_hold_ok'] = rsi_hold_ok
        result['rsi_hold_bars'] = rsi_bars
        result['details']['rsi_last'] = df_1m['RSI_12'].iloc[-1]
        
        # Check BOS
        bos_signal = df_1m['BOS'].iloc[-1]
        expected_bos = 1 if side == 'long' else -1
        bos_ok = (bos_signal == expected_bos)
        result['bos_ok'] = bos_ok
        result['bos_signal'] = bos_signal
        
        # Check volume
        vol_threshold = vol_mult_tier_a if tier == 'A' else vol_mult
        vol_ok, vol_ratio = check_volume_gate_1m(df_1m, mult=vol_threshold)
        result['volume_ok'] = vol_ok
        result['volume_ratio'] = vol_ratio
        
        # Overall impulse check
        result['impulse_ok'] = rsi_hold_ok and bos_ok and vol_ok
        
        logger.info(
            f"1m impulse check ({side}, tier={tier}): "
            f"RSI={rsi_hold_ok} ({rsi_bars} bars), "
            f"BOS={bos_ok} ({bos_signal}), "
            f"Vol={vol_ok} ({vol_ratio:.2f}x) -> "
            f"{'PASS' if result['impulse_ok'] else 'FAIL'}"
        )
        
    except Exception as e:
        logger.error(f"Error in 1m impulse check: {e}", exc_info=True)
        result['details']['error'] = str(e)
    
    return result


def compute_1m_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute all necessary features for 1m impulse detection.
    
    Args:
        df: 1-minute OHLC DataFrame
    
    Returns:
        DataFrame with computed features
    """
    df = df.copy()
    
    # RSI-12
    df['RSI_12'] = compute_rsi_12(df)
    
    # ATR(1m)
    df['ATR_1m'] = compute_atr_1m(df)
    
    # BOS
    df['BOS'] = detect_bos_1m(df, atr_mult=0.1)
    
    # Volume median and ratio
    df['vol_med50'] = df['volume'].rolling(window=50).median()
    df['vol_ratio'] = df['volume'] / df['vol_med50']
    
    return df
