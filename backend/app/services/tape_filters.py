"""
Tape Filters for 1s/5s Microstructure (Phase 1)
Implements CVD z-score, OBI ratio, and VWAP proximity checks.
Part of the SOLUSDT Swing-Capture Playbook v1.0
"""
import pandas as pd
import numpy as np
from typing import Optional, Dict, Tuple
from ..utils.logging import get_logger

logger = get_logger(__name__)


def compute_cvd_zscore(
    df: pd.DataFrame,
    window: int = 20,
    column: str = 'cvd'
) -> pd.Series:
    """
    Compute CVD z-score over rolling window.
    
    Args:
        df: DataFrame with CVD data
        window: Rolling window in seconds (default 20s)
        column: CVD column name
    
    Returns:
        Series with CVD z-scores
    """
    if column not in df.columns:
        return pd.Series(np.nan, index=df.index)
    
    cvd_mean = df[column].rolling(window=window).mean()
    cvd_std = df[column].rolling(window=window).std()
    
    z_score = (df[column] - cvd_mean) / cvd_std.replace(0, np.nan)
    
    return z_score


def compute_obi_ratio(
    df: pd.DataFrame,
    window: int = 10,
    bid_col: str = 'bid_size',
    ask_col: str = 'ask_size'
) -> pd.Series:
    """
    Compute Orderbook Imbalance (OBI) ratio over rolling window.
    OBI = size_bid / size_ask
    
    Args:
        df: DataFrame with bid/ask sizes
        window: Rolling window in seconds (default 10s)
        bid_col: Bid size column name
        ask_col: Ask size column name
    
    Returns:
        Series with OBI ratios
    """
    if bid_col not in df.columns or ask_col not in df.columns:
        return pd.Series(np.nan, index=df.index)
    
    # Average over window
    bid_avg = df[bid_col].rolling(window=window).mean()
    ask_avg = df[ask_col].rolling(window=window).mean()
    
    obi = bid_avg / ask_avg.replace(0, np.nan)
    
    return obi


def compute_vwap(df: pd.DataFrame, session_start: Optional[str] = None) -> pd.Series:
    """
    Compute VWAP (Volume Weighted Average Price).
    
    Args:
        df: DataFrame with price and volume data
        session_start: Optional session start time for reset
    
    Returns:
        Series with VWAP values
    """
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    cumulative_tp_vol = (typical_price * df['volume']).cumsum()
    cumulative_vol = df['volume'].cumsum()
    
    vwap = cumulative_tp_vol / cumulative_vol.replace(0, np.nan)
    
    return vwap


def check_vwap_proximity(
    df: pd.DataFrame,
    atr_5m: float,
    tolerance_mult: float = 0.02,
    vwap_col: str = 'vwap'
) -> Tuple[bool, float, str]:
    """
    Check if price is within tolerance of VWAP or has reclaimed/lost VWAP.
    
    Per playbook: price within ±0.02 × ATR(5m) of VWAP 
    OR has reclaimed/lost VWAP on 1s closes.
    
    Args:
        df: DataFrame with price and VWAP data
        atr_5m: ATR from 5-minute timeframe
        tolerance_mult: Tolerance multiplier (default 0.02)
        vwap_col: VWAP column name
    
    Returns:
        Tuple of (proximity_ok: bool, distance_pct: float, status: str)
    """
    if len(df) < 2 or vwap_col not in df.columns:
        return False, np.nan, 'insufficient_data'
    
    current_price = df['close'].iloc[-1]
    current_vwap = df[vwap_col].iloc[-1]
    prev_price = df['close'].iloc[-2]
    prev_vwap = df[vwap_col].iloc[-2]
    
    if pd.isna(current_vwap) or pd.isna(atr_5m) or atr_5m == 0:
        return False, np.nan, 'invalid_data'
    
    # Distance from VWAP
    distance = abs(current_price - current_vwap)
    distance_pct = distance / current_vwap
    tolerance = tolerance_mult * atr_5m
    
    # Within tolerance?
    within_tolerance = distance <= tolerance
    
    # Check for reclaim/loss
    reclaimed = (prev_price < prev_vwap) and (current_price > current_vwap)
    lost = (prev_price > prev_vwap) and (current_price < current_vwap)
    
    status = 'unknown'
    if within_tolerance:
        status = 'within_tolerance'
    elif reclaimed:
        status = 'reclaimed'
    elif lost:
        status = 'lost'
    else:
        status = 'outside_tolerance'
    
    proximity_ok = within_tolerance or reclaimed or lost
    
    return proximity_ok, distance_pct, status


def check_tape_filters(
    df_tape: pd.DataFrame,
    side: str,
    atr_5m: float,
    cvd_z_threshold: float = 0.5,
    obi_long_threshold: float = 1.25,
    obi_short_threshold: float = 0.80,
    vwap_tolerance: float = 0.02
) -> Dict:
    """
    Comprehensive tape filter check for 1s/5s microstructure.
    
    Requirements per playbook:
    - CVD(20s) z-score >= +0.5σ (long) / <= -0.5σ (short)
    - OBI (10s) >= 1.25:1 (long) / <= 0.80:1 (short)
    - VWAP proximity: within ±0.02×ATR(5m) or reclaimed/lost
    
    Args:
        df_tape: 1s or 5s DataFrame with tape data
        side: 'long' or 'short'
        atr_5m: ATR from 5-minute timeframe
        cvd_z_threshold: CVD z-score threshold
        obi_long_threshold: OBI threshold for longs
        obi_short_threshold: OBI threshold for shorts
        vwap_tolerance: VWAP proximity tolerance multiplier
    
    Returns:
        Dict with tape filter results
    """
    result = {
        'tape_ok': False,
        'cvd_ok': False,
        'cvd_z': np.nan,
        'obi_ok': False,
        'obi_ratio': np.nan,
        'vwap_ok': False,
        'vwap_distance_pct': np.nan,
        'vwap_status': 'unknown',
        'details': {}
    }
    
    if df_tape is None or len(df_tape) < 20:
        result['details']['error'] = 'Insufficient tape data'
        return result
    
    try:
        # Compute CVD z-score if not present
        if 'cvd_z' not in df_tape.columns:
            df_tape['cvd_z'] = compute_cvd_zscore(df_tape, window=20)
        
        # Compute OBI if not present
        if 'obi' not in df_tape.columns:
            df_tape['obi'] = compute_obi_ratio(df_tape, window=10)
        
        # Compute VWAP if not present
        if 'vwap' not in df_tape.columns:
            df_tape['vwap'] = compute_vwap(df_tape)
        
        # Check CVD z-score
        cvd_z = df_tape['cvd_z'].iloc[-1]
        if side == 'long':
            cvd_ok = cvd_z >= cvd_z_threshold
        else:  # short
            cvd_ok = cvd_z <= -cvd_z_threshold
        
        result['cvd_ok'] = cvd_ok
        result['cvd_z'] = cvd_z
        
        # Check OBI
        obi_ratio = df_tape['obi'].iloc[-1]
        if side == 'long':
            obi_ok = obi_ratio >= obi_long_threshold
        else:  # short
            obi_ok = obi_ratio <= obi_short_threshold
        
        result['obi_ok'] = obi_ok
        result['obi_ratio'] = obi_ratio
        
        # Check VWAP proximity
        vwap_ok, vwap_dist, vwap_status = check_vwap_proximity(
            df_tape, atr_5m, tolerance_mult=vwap_tolerance
        )
        result['vwap_ok'] = vwap_ok
        result['vwap_distance_pct'] = vwap_dist
        result['vwap_status'] = vwap_status
        
        # Overall tape check
        result['tape_ok'] = cvd_ok and obi_ok and vwap_ok
        
        logger.info(
            f"Tape filters ({side}): "
            f"CVD_z={cvd_z:.2f} ({cvd_ok}), "
            f"OBI={obi_ratio:.2f} ({obi_ok}), "
            f"VWAP={vwap_status} ({vwap_ok}) -> "
            f"{'PASS' if result['tape_ok'] else 'FAIL'}"
        )
        
    except Exception as e:
        logger.error(f"Error in tape filter check: {e}", exc_info=True)
        result['details']['error'] = str(e)
    
    return result


def compute_tape_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute all necessary features for tape filtering.
    
    Args:
        df: 1s or 5s OHLC DataFrame with tape data
    
    Returns:
        DataFrame with computed features
    """
    df = df.copy()
    
    # CVD z-score (20s window)
    df['cvd_z'] = compute_cvd_zscore(df, window=20)
    
    # OBI ratio (10s window)
    df['obi'] = compute_obi_ratio(df, window=10)
    
    # VWAP
    df['vwap'] = compute_vwap(df)
    
    return df


def debounce_tape_signal(df: pd.DataFrame, n_of_m: int = 7, m: int = 10) -> bool:
    """
    Debounce tape signal using n-of-m logic.
    Require n out of last m bars to pass filters (anti-spoofing).
    
    Args:
        df: DataFrame with tape_ok column
        n_of_m: Number of bars that must pass
        m: Total bars to check
    
    Returns:
        True if debounced signal passes
    """
    if 'tape_ok' not in df.columns or len(df) < m:
        return False
    
    recent_signals = df['tape_ok'].iloc[-m:]
    passed_count = recent_signals.sum()
    
    return passed_count >= n_of_m
