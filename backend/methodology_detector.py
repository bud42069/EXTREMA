"""
Enhanced swing detection based on proven SOLUSDT methodology.
Uses EMA crossovers, SAR flips, and FVG levels as per historical analysis.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class SwingSignal:
    """Enhanced swing signal with methodology-specific data."""
    direction: str  # 'long' or 'short'
    entry_price: float
    ema_cross: bool  # EMA Fast crossed EMA Slow
    sar_aligned: bool  # SAR below price (long) or above (short)
    fvg_bounce: bool  # Price bounced off FVG level
    volume_spike: bool  # Volume > 1.5x 20-period avg
    sar_level: float  # SAR value for trailing stop
    confidence: str  # 'high' | 'medium' | 'low'
    

def calculate_sar(df: pd.DataFrame, acceleration: float = 0.02, maximum: float = 0.2) -> pd.Series:
    """
    Calculate Parabolic SAR (Stop and Reverse).
    
    Args:
        df: DataFrame with 'high' and 'low' columns
        acceleration: Acceleration factor (default 0.02)
        maximum: Maximum acceleration (default 0.2)
    
    Returns:
        Series with SAR values
    """
    high = df['high'].values
    low = df['low'].values
    close = df['close'].values
    
    sar = np.zeros(len(df))
    ep = np.zeros(len(df))
    af = np.zeros(len(df))
    trend = np.zeros(len(df))  # 1 for uptrend, -1 for downtrend
    
    # Initialize
    sar[0] = low[0]
    ep[0] = high[0]
    af[0] = acceleration
    trend[0] = 1
    
    for i in range(1, len(df)):
        # Previous values
        prev_sar = sar[i-1]
        prev_ep = ep[i-1]
        prev_af = af[i-1]
        prev_trend = trend[i-1]
        
        # Calculate SAR
        if prev_trend == 1:  # Uptrend
            sar[i] = prev_sar + prev_af * (prev_ep - prev_sar)
            
            # Check if trend reverses
            if low[i] < sar[i]:
                trend[i] = -1
                sar[i] = prev_ep
                ep[i] = low[i]
                af[i] = acceleration
            else:
                trend[i] = 1
                # Update EP if new high
                if high[i] > prev_ep:
                    ep[i] = high[i]
                    af[i] = min(prev_af + acceleration, maximum)
                else:
                    ep[i] = prev_ep
                    af[i] = prev_af
        
        else:  # Downtrend
            sar[i] = prev_sar - prev_af * (prev_sar - prev_ep)
            
            # Check if trend reverses
            if high[i] > sar[i]:
                trend[i] = 1
                sar[i] = prev_ep
                ep[i] = high[i]
                af[i] = acceleration
            else:
                trend[i] = -1
                # Update EP if new low
                if low[i] < prev_ep:
                    ep[i] = low[i]
                    af[i] = min(prev_af + acceleration, maximum)
                else:
                    ep[i] = prev_ep
                    af[i] = prev_af
    
    return pd.Series(sar, index=df.index)


def detect_ema_crossover(df: pd.DataFrame, fast_period: int = 9, slow_period: int = 21) -> Tuple[pd.Series, pd.Series]:
    """
    Detect EMA crossovers (Fast crossing Slow).
    
    Args:
        df: DataFrame with 'close' column
        fast_period: Fast EMA period
        slow_period: Slow EMA period
    
    Returns:
        Tuple of (bullish_cross, bearish_cross) boolean Series
    """
    ema_fast = df['close'].ewm(span=fast_period, adjust=False).mean()
    ema_slow = df['close'].ewm(span=slow_period, adjust=False).mean()
    
    # Detect crossovers
    bullish_cross = (ema_fast > ema_slow) & (ema_fast.shift(1) <= ema_slow.shift(1))
    bearish_cross = (ema_fast < ema_slow) & (ema_fast.shift(1) >= ema_slow.shift(1))
    
    return bullish_cross, bearish_cross


def detect_fvg_levels(df: pd.DataFrame, threshold: float = 0.002) -> List[Dict]:
    """
    Detect Fair Value Gaps (FVG) - imbalances in price action.
    FVG occurs when gap between candles leaves unfilled area.
    
    Args:
        df: DataFrame with OHLC data
        threshold: Minimum gap size as fraction of price
    
    Returns:
        List of FVG dictionaries with 'start', 'end', 'price', 'type'
    """
    fvgs = []
    
    for i in range(2, len(df)):
        # Bullish FVG: gap between candle[i-2].high and candle[i].low
        if df['low'].iloc[i] > df['high'].iloc[i-2]:
            gap = df['low'].iloc[i] - df['high'].iloc[i-2]
            if gap / df['close'].iloc[i] > threshold:
                fvgs.append({
                    'index': i,
                    'type': 'bullish',
                    'top': df['low'].iloc[i],
                    'bottom': df['high'].iloc[i-2],
                    'price': (df['low'].iloc[i] + df['high'].iloc[i-2]) / 2
                })
        
        # Bearish FVG: gap between candle[i-2].low and candle[i].high
        elif df['high'].iloc[i] < df['low'].iloc[i-2]:
            gap = df['low'].iloc[i-2] - df['high'].iloc[i]
            if gap / df['close'].iloc[i] > threshold:
                fvgs.append({
                    'index': i,
                    'type': 'bearish',
                    'top': df['low'].iloc[i-2],
                    'bottom': df['high'].iloc[i],
                    'price': (df['low'].iloc[i-2] + df['high'].iloc[i]) / 2
                })
    
    return fvgs


def check_fvg_bounce(df: pd.DataFrame, idx: int, direction: str, fvgs: List[Dict], 
                     lookback: int = 20) -> bool:
    """
    Check if price bounced off a nearby FVG level.
    
    Args:
        df: DataFrame
        idx: Current bar index
        direction: 'long' or 'short'
        fvgs: List of FVG levels
        lookback: Bars to look back for FVG
    
    Returns:
        True if bounced off FVG
    """
    current_price = df['close'].iloc[idx]
    
    # Find nearby FVGs
    nearby_fvgs = [
        fvg for fvg in fvgs 
        if abs(fvg['index'] - idx) <= lookback
    ]
    
    for fvg in nearby_fvgs:
        if direction == 'long' and fvg['type'] == 'bullish':
            # Check if price near FVG bottom (support)
            if abs(current_price - fvg['bottom']) / current_price < 0.01:  # Within 1%
                return True
        
        elif direction == 'short' and fvg['type'] == 'bearish':
            # Check if price near FVG top (resistance)
            if abs(current_price - fvg['top']) / current_price < 0.01:
                return True
    
    return False


def detect_swing_signals_methodology(df: pd.DataFrame) -> List[SwingSignal]:
    """
    Detect swing signals using the proven SOLUSDT methodology:
    - EMA crossover (Fast vs Slow)
    - SAR alignment
    - FVG bounce
    - Volume spike (>1.5x 20-period average)
    
    Args:
        df: DataFrame with OHLCV and indicators
    
    Returns:
        List of SwingSignal objects
    """
    if len(df) < 50:
        return []
    
    signals = []
    
    # Calculate SAR
    df['SAR'] = calculate_sar(df)
    
    # Detect EMA crossovers
    bullish_cross, bearish_cross = detect_ema_crossover(df, fast_period=9, slow_period=21)
    
    # Detect FVG levels
    fvgs = detect_fvg_levels(df)
    
    # Calculate 20-period volume average
    vol_avg_20 = df['Volume'].rolling(window=20).mean()
    
    # Scan for signals
    for i in range(50, len(df)):
        idx = df.index[i]
        row = df.iloc[i]
        
        # Volume spike check
        volume_spike = row['Volume'] > (vol_avg_20.iloc[i] * 1.5)
        
        # Long signal: Bullish EMA cross + SAR below price + volume
        if bullish_cross.iloc[i]:
            sar_aligned = row['SAR'] < row['close']
            fvg_bounce = check_fvg_bounce(df, i, 'long', fvgs)
            
            # Confidence based on confluence
            confidence_score = sum([sar_aligned, volume_spike, fvg_bounce])
            confidence = 'high' if confidence_score >= 2 else ('medium' if confidence_score == 1 else 'low')
            
            signal = SwingSignal(
                direction='long',
                entry_price=row['close'],
                ema_cross=True,
                sar_aligned=sar_aligned,
                fvg_bounce=fvg_bounce,
                volume_spike=volume_spike,
                sar_level=row['SAR'],
                confidence=confidence
            )
            
            signals.append(signal)
        
        # Short signal: Bearish EMA cross + SAR above price + volume
        elif bearish_cross.iloc[i]:
            sar_aligned = row['SAR'] > row['close']
            fvg_bounce = check_fvg_bounce(df, i, 'short', fvgs)
            
            # Confidence based on confluence
            confidence_score = sum([sar_aligned, volume_spike, fvg_bounce])
            confidence = 'high' if confidence_score >= 2 else ('medium' if confidence_score == 1 else 'low')
            
            signal = SwingSignal(
                direction='short',
                entry_price=row['close'],
                ema_cross=True,
                sar_aligned=sar_aligned,
                fvg_bounce=fvg_bounce,
                volume_spike=volume_spike,
                sar_level=row['SAR'],
                confidence=confidence
            )
            
            signals.append(signal)
    
    return signals


def calculate_sar_exit(df: pd.DataFrame, entry_idx: int, direction: str) -> Dict:
    """
    Calculate exit based on SAR flip (trailing stop method).
    
    Args:
        df: DataFrame with SAR column
        entry_idx: Entry bar index
        direction: 'long' or 'short'
    
    Returns:
        Dict with exit info
    """
    entry_sar = df['SAR'].iloc[entry_idx]
    
    for i in range(entry_idx + 1, len(df)):
        current_sar = df['SAR'].iloc[i]
        current_price = df['close'].iloc[i]
        
        # SAR flip detection
        if direction == 'long':
            if current_sar > current_price:  # SAR flipped above price
                return {
                    'exit_idx': i,
                    'exit_price': current_price,
                    'exit_reason': 'SAR_FLIP',
                    'bars_held': i - entry_idx
                }
        else:
            if current_sar < current_price:  # SAR flipped below price
                return {
                    'exit_idx': i,
                    'exit_price': current_price,
                    'exit_reason': 'SAR_FLIP',
                    'bars_held': i - entry_idx
                }
    
    # No exit found (end of data)
    return {
        'exit_idx': len(df) - 1,
        'exit_price': df['close'].iloc[-1],
        'exit_reason': 'END_OF_DATA',
        'bars_held': len(df) - 1 - entry_idx
    }
