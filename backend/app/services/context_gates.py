"""
Context Gates (Phase 2)
Implements 15m/1h EMA alignment, oscillator agreement, and pivot/VWAP structure checks.
Part of the SOLUSDT Swing-Capture Playbook v1.0
"""
import pandas as pd
import numpy as np
from typing import Optional, Dict, List
from ..utils.logging import get_logger

logger = get_logger(__name__)


def compute_ema_set(df: pd.DataFrame, spans: List[int] = [5, 9, 21, 38]) -> pd.DataFrame:
    """
    Compute set of EMAs for alignment checks.
    
    Args:
        df: DataFrame with close prices
        spans: List of EMA spans (default [5,9,21,38])
    
    Returns:
        DataFrame with EMA columns added
    """
    df = df.copy()
    
    for span in spans:
        df[f'EMA_{span}'] = df['close'].ewm(span=span, adjust=False).mean()
    
    return df


def check_ema_alignment(
    df: pd.DataFrame,
    side: str,
    ema_spans: List[int] = [5, 9, 21, 38],
    min_aligned: int = 3
) -> Dict:
    """
    Check EMA alignment for continuation plays.
    Per playbook: EMAs (5/9/21/38) ≥3/4 aligned in trade direction.
    
    Args:
        df: DataFrame with EMA data
        side: 'long' or 'short'
        ema_spans: List of EMA spans to check
        min_aligned: Minimum aligned EMAs required (default 3 out of 4)
    
    Returns:
        Dict with alignment results
    """
    result = {
        'aligned': False,
        'aligned_count': 0,
        'total_count': len(ema_spans),
        'alignment_ratio': 0.0,
        'ema_values': {},
        'details': {}
    }
    
    if df is None or len(df) < max(ema_spans):
        result['details']['error'] = 'Insufficient data'
        return result
    
    try:
        # Get latest EMA values
        ema_values = {}
        for span in ema_spans:
            col = f'EMA_{span}'
            if col in df.columns:
                ema_values[span] = df[col].iloc[-1]
            else:
                result['details']['error'] = f'Missing {col}'
                return result
        
        result['ema_values'] = ema_values
        
        # Check alignment
        # For long: EMA_5 > EMA_9 > EMA_21 > EMA_38 (faster above slower)
        # For short: EMA_5 < EMA_9 < EMA_21 < EMA_38 (faster below slower)
        
        aligned_count = 0
        for i in range(len(ema_spans) - 1):
            fast_span = ema_spans[i]
            slow_span = ema_spans[i + 1]
            fast_val = ema_values[fast_span]
            slow_val = ema_values[slow_span]
            
            if side == 'long':
                if fast_val > slow_val:
                    aligned_count += 1
            else:  # short
                if fast_val < slow_val:
                    aligned_count += 1
        
        result['aligned_count'] = aligned_count
        result['alignment_ratio'] = aligned_count / (len(ema_spans) - 1)
        result['aligned'] = bool(aligned_count >= min_aligned)
        
        logger.info(
            f"EMA alignment ({side}): {aligned_count}/{len(ema_spans)-1} aligned "
            f"-> {'PASS' if result['aligned'] else 'FAIL'}"
        )
        
    except Exception as e:
        logger.error(f"Error in EMA alignment check: {e}", exc_info=True)
        result['details']['error'] = str(e)
    
    return result


def compute_pivot_points(df: pd.DataFrame) -> Dict:
    """
    Compute classic daily pivot points (R1, S1).
    
    Args:
        df: DataFrame with OHLC data
    
    Returns:
        Dict with pivot levels
    """
    if df is None or len(df) < 1:
        return {}
    
    # Use previous day's high/low/close for pivot calculation
    # Simplified: use rolling window to approximate daily
    high = df['high'].max()
    low = df['low'].min()
    close = df['close'].iloc[-1]
    
    pivot = (high + low + close) / 3
    r1 = (2 * pivot) - low
    s1 = (2 * pivot) - high
    
    return {
        'pivot': pivot,
        'r1': r1,
        's1': s1,
        'high': high,
        'low': low
    }


def check_pivot_structure(
    df: pd.DataFrame,
    side: str,
    pivot_levels: Optional[Dict] = None
) -> Dict:
    """
    Check if price is on correct side of pivot/VWAP for continuation.
    
    Args:
        df: DataFrame with price data
        side: 'long' or 'short'
        pivot_levels: Optional pre-computed pivot levels
    
    Returns:
        Dict with pivot structure results
    """
    result = {
        'pivot_ok': False,
        'vwap_ok': False,
        'structure_ok': False,
        'current_price': np.nan,
        'pivot': np.nan,
        's1': np.nan,
        'r1': np.nan,
        'vwap': np.nan,
        'details': {}
    }
    
    if df is None or len(df) < 1:
        result['details']['error'] = 'Insufficient data'
        return result
    
    try:
        current_price = df['close'].iloc[-1]
        result['current_price'] = current_price
        
        # Compute pivots if not provided
        if pivot_levels is None:
            pivot_levels = compute_pivot_points(df)
        
        result['pivot'] = pivot_levels.get('pivot', np.nan)
        result['s1'] = pivot_levels.get('s1', np.nan)
        result['r1'] = pivot_levels.get('r1', np.nan)
        
        # Check pivot structure
        pivot = pivot_levels.get('pivot')
        s1 = pivot_levels.get('s1')
        r1 = pivot_levels.get('r1')
        
        if side == 'long':
            # For long: prefer close above pivot or above S1
            result['pivot_ok'] = bool(current_price > pivot) if pivot else False
        else:  # short
            # For short: prefer close below pivot or below R1
            result['pivot_ok'] = current_price < pivot if pivot else False
        
        # Check VWAP if available
        if 'vwap' in df.columns:
            vwap = df['vwap'].iloc[-1]
            result['vwap'] = vwap
            
            if side == 'long':
                result['vwap_ok'] = current_price > vwap
            else:
                result['vwap_ok'] = current_price < vwap
        else:
            result['vwap_ok'] = True  # Not required if unavailable
        
        # Overall structure
        result['structure_ok'] = result['pivot_ok'] or result['vwap_ok']
        
        logger.info(
            f"Pivot structure ({side}): "
            f"pivot_ok={result['pivot_ok']}, vwap_ok={result['vwap_ok']} "
            f"-> {'PASS' if result['structure_ok'] else 'FAIL'}"
        )
        
    except Exception as e:
        logger.error(f"Error in pivot structure check: {e}", exc_info=True)
        result['details']['error'] = str(e)
    
    return result


def check_oscillator_agreement(
    df: pd.DataFrame,
    side: str,
    rsi_period: int = 12
) -> Dict:
    """
    Check RSI-12 oscillator agreement (not extreme against direction).
    
    Args:
        df: DataFrame with price data
        side: 'long' or 'short'
        rsi_period: RSI period (default 12)
    
    Returns:
        Dict with oscillator results
    """
    result = {
        'oscillator_ok': False,
        'rsi': np.nan,
        'extreme': False,
        'details': {}
    }
    
    if df is None or len(df) < rsi_period + 1:
        result['details']['error'] = 'Insufficient data'
        return result
    
    try:
        # Compute RSI if not present
        if f'RSI_{rsi_period}' not in df.columns:
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
            rs = gain / loss.replace(0, np.nan)
            rsi = 100 - (100 / (1 + rs))
        else:
            rsi = df[f'RSI_{rsi_period}']
        
        current_rsi = rsi.iloc[-1]
        result['rsi'] = current_rsi
        
        # Check for extremes against direction
        # For long: RSI shouldn't be <30 (oversold against)
        # For short: RSI shouldn't be >70 (overbought against)
        
        if side == 'long':
            result['extreme'] = current_rsi < 30
            result['oscillator_ok'] = not result['extreme']
        else:  # short
            result['extreme'] = current_rsi > 70
            result['oscillator_ok'] = not result['extreme']
        
        logger.info(
            f"Oscillator agreement ({side}): RSI={current_rsi:.1f}, "
            f"extreme={result['extreme']} -> "
            f"{'PASS' if result['oscillator_ok'] else 'FAIL'}"
        )
        
    except Exception as e:
        logger.error(f"Error in oscillator check: {e}", exc_info=True)
        result['details']['error'] = str(e)
    
    return result


def check_context_gates(
    df_15m: pd.DataFrame,
    df_1h: pd.DataFrame,
    side: str,
    ema_spans: List[int] = [5, 9, 21, 38],
    min_ema_aligned: int = 3
) -> Dict:
    """
    Comprehensive context gate check for 15m/1h timeframes.
    
    Requirements per playbook:
    - Continuation (Long-A/Short-A): EMAs ≥3/4 aligned in trade direction
    - 15m close on correct side of session VWAP or pivot (S1/R1)
    - RSI-12 not extreme against
    
    Args:
        df_15m: 15-minute DataFrame
        df_1h: 1-hour DataFrame
        side: 'long' or 'short'
        ema_spans: EMA spans to check
        min_ema_aligned: Minimum aligned EMAs
    
    Returns:
        Dict with context gate results
    """
    result = {
        'context_ok': False,
        'play_type': 'unknown',
        'ema_alignment': {},
        'pivot_structure': {},
        'oscillator': {},
        'score': 0.0,
        'details': {}
    }
    
    try:
        # Check EMA alignment on both timeframes
        ema_15m = check_ema_alignment(df_15m, side, ema_spans, min_ema_aligned)
        ema_1h = check_ema_alignment(df_1h, side, ema_spans, min_ema_aligned)
        
        result['ema_alignment'] = {
            '15m': ema_15m,
            '1h': ema_1h,
            'both_aligned': ema_15m['aligned'] and ema_1h['aligned']
        }
        
        # Check pivot/VWAP structure (15m)
        pivot_struct = check_pivot_structure(df_15m, side)
        result['pivot_structure'] = pivot_struct
        
        # Check oscillator agreement (15m and 1h)
        osc_15m = check_oscillator_agreement(df_15m, side)
        osc_1h = check_oscillator_agreement(df_1h, side)
        
        result['oscillator'] = {
            '15m': osc_15m,
            '1h': osc_1h,
            'both_ok': osc_15m['oscillator_ok'] and osc_1h['oscillator_ok']
        }
        
        # Determine play type
        if result['ema_alignment']['both_aligned'] and pivot_struct['structure_ok']:
            result['play_type'] = 'continuation'  # A-tier eligible
        else:
            result['play_type'] = 'deviation'  # B-tier only
        
        # Overall context gate
        result['context_ok'] = (
            result['ema_alignment']['both_aligned'] and
            pivot_struct['structure_ok'] and
            result['oscillator']['both_ok']
        )
        
        # Compute score (0-100)
        score_components = []
        
        # EMA alignment (40%)
        ema_score = (ema_15m['alignment_ratio'] + ema_1h['alignment_ratio']) / 2
        score_components.append(ema_score * 40)
        
        # Pivot structure (30%)
        pivot_score = 1.0 if pivot_struct['structure_ok'] else 0.0
        score_components.append(pivot_score * 30)
        
        # Oscillator (30%)
        osc_score = (
            (1.0 if osc_15m['oscillator_ok'] else 0.0) +
            (1.0 if osc_1h['oscillator_ok'] else 0.0)
        ) / 2
        score_components.append(osc_score * 30)
        
        result['score'] = sum(score_components)
        
        logger.info(
            f"Context gates ({side}): "
            f"play_type={result['play_type']}, "
            f"score={result['score']:.1f} -> "
            f"{'PASS' if result['context_ok'] else 'FAIL'}"
        )
        
    except Exception as e:
        logger.error(f"Error in context gate check: {e}", exc_info=True)
        result['details']['error'] = str(e)
    
    return result
