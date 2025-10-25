"""
Hybrid Swing Detection System - Combines Two Methodologies
Tier 1: Macro Filter (EMA/SAR/FVG context for directional bias)
Tier 2: Micro Trigger (ATR/BB/Vol-Z + breakout confirmation)
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

from methodology_detector import (
    calculate_sar, 
    detect_ema_crossover, 
    detect_fvg_levels,
    check_fvg_bounce
)


@dataclass
class HybridSignal:
    """
    Complete signal with both macro context and micro confirmation.
    """
    # Identification
    signal_id: str
    timestamp: int
    direction: str  # 'long' or 'short'
    
    # Tier 1: Macro Filter (Your Methodology)
    macro_bias: str  # 'bullish' | 'bearish' | 'neutral'
    ema_cross: bool
    ema_fast: float
    ema_slow: float
    sar_aligned: bool
    sar_level: float
    fvg_aligned: bool
    fvg_price: Optional[float]
    
    # Tier 2: Micro Trigger (Empirical Methodology)
    extrema_detected: bool
    atr14: float
    bb_width: float
    volume_zscore: float
    breakout_confirmed: bool
    breakout_price: float
    
    # Confluence & Tier
    macro_score: float  # 0-100 from Tier 1
    micro_score: float  # 0-100 from Tier 2
    total_confluence: float  # Combined score
    tier: str  # 'A' | 'B' | 'C'
    
    # Entry/Exit Plan
    entry_price: float
    stop_loss: float
    tp1: float
    tp2: float
    tp3: float
    
    # Metadata
    confidence: str  # 'high' | 'medium' | 'low'
    play_type: str
    regime: str


class HybridDetector:
    """
    Two-tier hybrid swing detector combining macro context + micro confirmation.
    """
    
    def __init__(self,
                 # Macro thresholds
                 ema_fast_period: int = 9,
                 ema_slow_period: int = 21,
                 sar_acceleration: float = 0.02,
                 
                 # Micro thresholds
                 atr_threshold: float = 0.6,
                 bb_width_threshold: float = 0.005,
                 vol_z_threshold: float = 0.5,
                 
                 # Confirmation
                 confirmation_window: int = 6,
                 breakout_atr_mult: float = 0.5,
                 volume_multiplier: float = 1.5):
        """
        Initialize hybrid detector with both methodology parameters.
        """
        # Macro parameters
        self.ema_fast_period = ema_fast_period
        self.ema_slow_period = ema_slow_period
        self.sar_acceleration = sar_acceleration
        
        # Micro parameters
        self.atr_threshold = atr_threshold
        self.bb_width_threshold = bb_width_threshold
        self.vol_z_threshold = vol_z_threshold
        self.confirmation_window = confirmation_window
        self.breakout_atr_mult = breakout_atr_mult
        self.volume_multiplier = volume_multiplier
    
    def calculate_macro_bias(self, df: pd.DataFrame, idx: int) -> Dict:
        """
        TIER 1: Calculate macro bias using EMA/SAR/FVG.
        
        Returns:
            Dict with macro bias information
        """
        row = df.iloc[idx]
        
        # EMA values
        ema_fast = row.get('EMA_Fast', row.get('EMA20', 0))
        ema_slow = row.get('EMA_Slow', row.get('EMA50', 0))
        
        # Detect if we're on an EMA cross
        if idx > 0:
            prev_fast = df.iloc[idx-1].get('EMA_Fast', df.iloc[idx-1].get('EMA20', 0))
            prev_slow = df.iloc[idx-1].get('EMA_Slow', df.iloc[idx-1].get('EMA50', 0))
            
            bullish_cross = (ema_fast > ema_slow) and (prev_fast <= prev_slow)
            bearish_cross = (ema_fast < ema_slow) and (prev_fast >= prev_slow)
        else:
            bullish_cross = False
            bearish_cross = False
        
        # SAR alignment
        sar = row.get('SAR', 0)
        close = row['close']
        
        sar_bullish = sar < close
        sar_bearish = sar > close
        
        # Determine macro bias
        if (bullish_cross or (ema_fast > ema_slow and sar_bullish)):
            macro_bias = 'bullish'
            ema_cross = bullish_cross
            sar_aligned = sar_bullish
        elif (bearish_cross or (ema_fast < ema_slow and sar_bearish)):
            macro_bias = 'bearish'
            ema_cross = bearish_cross
            sar_aligned = sar_bearish
        else:
            macro_bias = 'neutral'
            ema_cross = False
            sar_aligned = False
        
        # Calculate macro score
        macro_score = 0
        if ema_cross:
            macro_score += 40
        elif abs(ema_fast - ema_slow) / close > 0.02:  # Strong EMA separation
            macro_score += 20
        
        if sar_aligned:
            macro_score += 30
        
        # FVG check would add +30 if aligned
        
        return {
            'macro_bias': macro_bias,
            'ema_cross': ema_cross,
            'ema_fast': ema_fast,
            'ema_slow': ema_slow,
            'sar_aligned': sar_aligned,
            'sar_level': sar,
            'macro_score': macro_score
        }
    
    def check_micro_trigger(self, df: pd.DataFrame, idx: int, direction: str) -> Dict:
        """
        TIER 2: Check micro trigger conditions (ATR/BB/Vol-Z + breakout).
        
        Returns:
            Dict with micro trigger information
        """
        row = df.iloc[idx]
        
        # Get indicator values
        atr14 = row.get('ATR14', 0)
        bb_width = row.get('BB_Width', 0)
        vol_z = row.get('Volume_ZScore', 0)
        atr5 = row.get('ATR5', atr14)
        
        # Check thresholds
        atr_ok = atr14 >= self.atr_threshold
        bb_ok = bb_width >= self.bb_width_threshold
        vol_ok = vol_z >= self.vol_z_threshold
        
        # Calculate micro score
        micro_score = 0
        if atr_ok:
            micro_score += 33
        if bb_ok:
            micro_score += 33
        if vol_ok:
            micro_score += 34
        
        # Check for breakout confirmation in next bars
        breakout_confirmed = False
        breakout_price = row['close']
        
        if idx + self.confirmation_window < len(df):
            # Look ahead for breakout
            for i in range(idx + 1, min(idx + self.confirmation_window + 1, len(df))):
                future_bar = df.iloc[i]
                
                if direction == 'long':
                    # Breakout above local high + 0.5*ATR5
                    breakout_level = row['high'] + (self.breakout_atr_mult * atr5)
                    if future_bar['close'] > breakout_level:
                        # Check volume
                        vol_median = df['Volume'].iloc[max(0, i-50):i].median()
                        if future_bar['Volume'] >= vol_median * self.volume_multiplier:
                            breakout_confirmed = True
                            breakout_price = future_bar['close']
                            micro_score = min(100, micro_score + 20)  # Bonus for confirmation
                            break
                
                else:  # short
                    # Breakout below local low - 0.5*ATR5
                    breakout_level = row['low'] - (self.breakout_atr_mult * atr5)
                    if future_bar['close'] < breakout_level:
                        # Check volume
                        vol_median = df['Volume'].iloc[max(0, i-50):i].median()
                        if future_bar['Volume'] >= vol_median * self.volume_multiplier:
                            breakout_confirmed = True
                            breakout_price = future_bar['close']
                            micro_score = min(100, micro_score + 20)
                            break
        
        return {
            'extrema_detected': True,  # Assuming we're at an extrema
            'atr14': atr14,
            'bb_width': bb_width,
            'volume_zscore': vol_z,
            'breakout_confirmed': breakout_confirmed,
            'breakout_price': breakout_price,
            'micro_score': micro_score
        }
    
    def detect_signals(self, df: pd.DataFrame) -> List[HybridSignal]:
        """
        Run complete hybrid detection:
        1. Calculate macro bias (EMA/SAR/FVG)
        2. Detect local extrema (20-bar window)
        3. Check micro triggers (ATR/BB/Vol-Z)
        4. Confirm with breakout
        5. Generate signals with tier classification
        
        Returns:
            List of HybridSignal objects
        """
        if len(df) < 100:
            return []
        
        signals = []
        
        # Ensure we have required indicators
        if 'SAR' not in df.columns:
            df['SAR'] = calculate_sar(df, acceleration=self.sar_acceleration)
        
        if 'EMA_Fast' not in df.columns:
            df['EMA_Fast'] = df['close'].ewm(span=self.ema_fast_period, adjust=False).mean()
        
        if 'EMA_Slow' not in df.columns:
            df['EMA_Slow'] = df['close'].ewm(span=self.ema_slow_period, adjust=False).mean()
        
        # Detect FVG levels
        fvgs = detect_fvg_levels(df)
        
        # Detect local extrema (20-bar window as per methodology)
        from scipy.signal import argrelextrema
        
        # Find local minima
        minima_idx = argrelextrema(df['close'].values, np.less_equal, order=20)[0]
        # Find local maxima
        maxima_idx = argrelextrema(df['close'].values, np.greater_equal, order=20)[0]
        
        # Process minima for long signals
        for idx in minima_idx:
            if idx < 50 or idx > len(df) - self.confirmation_window:
                continue
            
            # TIER 1: Macro bias
            macro = self.calculate_macro_bias(df, idx)
            
            # Only proceed if bullish bias
            if macro['macro_bias'] != 'bullish':
                continue
            
            # TIER 2: Micro trigger
            micro = self.check_micro_trigger(df, idx, 'long')
            
            # Require minimum micro score
            if micro['micro_score'] < 60:
                continue
            
            # Calculate total confluence
            total_confluence = (macro['macro_score'] * 0.4) + (micro['micro_score'] * 0.6)
            
            # Tier classification
            if total_confluence >= 80 and micro['breakout_confirmed']:
                tier = 'A'
                confidence = 'high'
            elif total_confluence >= 60:
                tier = 'B'
                confidence = 'medium'
            else:
                tier = 'C'
                confidence = 'low'
            
            # Calculate entry/exit levels
            row = df.iloc[idx]
            entry_price = micro['breakout_price']
            atr5 = row.get('ATR5', row.get('ATR14', 0))
            
            stop_loss = row['low'] - (0.9 * atr5)
            risk = entry_price - stop_loss
            
            tp1 = entry_price + (risk * 1.0)
            tp2 = entry_price + (risk * 2.0)
            tp3 = entry_price + (risk * 3.5)
            
            # Determine play type
            if macro['ema_cross']:
                play_type = 'Breakout Expansion' if micro['bb_width'] < 0.01 else 'Trend Continuation'
            else:
                play_type = 'Reversal Reclaim'
            
            regime = 'S' if micro['bb_width'] < 0.01 else ('W' if micro['bb_width'] > 0.02 else 'N')
            
            # FVG check
            fvg_aligned = check_fvg_bounce(df, idx, 'long', fvgs, lookback=20)
            fvg_price = None
            if fvg_aligned:
                # Find nearest FVG
                for fvg in fvgs:
                    if abs(fvg['index'] - idx) <= 20 and fvg['type'] == 'bullish':
                        fvg_price = fvg['price']
                        macro['macro_score'] = min(100, macro['macro_score'] + 30)
                        total_confluence = min(100, total_confluence + 10)
                        break
            
            # Create signal
            signal = HybridSignal(
                signal_id=f"HYBRID-{int(datetime.now().timestamp())}-L",
                timestamp=int(row.get('time', 0)),
                direction='long',
                macro_bias=macro['macro_bias'],
                ema_cross=macro['ema_cross'],
                ema_fast=macro['ema_fast'],
                ema_slow=macro['ema_slow'],
                sar_aligned=macro['sar_aligned'],
                sar_level=macro['sar_level'],
                fvg_aligned=fvg_aligned,
                fvg_price=fvg_price,
                extrema_detected=micro['extrema_detected'],
                atr14=micro['atr14'],
                bb_width=micro['bb_width'],
                volume_zscore=micro['volume_zscore'],
                breakout_confirmed=micro['breakout_confirmed'],
                breakout_price=micro['breakout_price'],
                macro_score=macro['macro_score'],
                micro_score=micro['micro_score'],
                total_confluence=total_confluence,
                tier=tier,
                entry_price=entry_price,
                stop_loss=stop_loss,
                tp1=tp1,
                tp2=tp2,
                tp3=tp3,
                confidence=confidence,
                play_type=play_type,
                regime=regime
            )
            
            signals.append(signal)
        
        # Process maxima for short signals (similar logic)
        for idx in maxima_idx:
            if idx < 50 or idx > len(df) - self.confirmation_window:
                continue
            
            macro = self.calculate_macro_bias(df, idx)
            
            if macro['macro_bias'] != 'bearish':
                continue
            
            micro = self.check_micro_trigger(df, idx, 'short')
            
            if micro['micro_score'] < 60:
                continue
            
            total_confluence = (macro['macro_score'] * 0.4) + (micro['micro_score'] * 0.6)
            
            if total_confluence >= 80 and micro['breakout_confirmed']:
                tier = 'A'
                confidence = 'high'
            elif total_confluence >= 60:
                tier = 'B'
                confidence = 'medium'
            else:
                tier = 'C'
                confidence = 'low'
            
            row = df.iloc[idx]
            entry_price = micro['breakout_price']
            atr5 = row.get('ATR5', row.get('ATR14', 0))
            
            stop_loss = row['high'] + (0.9 * atr5)
            risk = stop_loss - entry_price
            
            tp1 = entry_price - (risk * 1.0)
            tp2 = entry_price - (risk * 2.0)
            tp3 = entry_price - (risk * 3.5)
            
            play_type = 'Breakout Expansion' if micro['bb_width'] < 0.01 else ('Trend Continuation' if macro['ema_cross'] else 'Reversal Reclaim')
            regime = 'S' if micro['bb_width'] < 0.01 else ('W' if micro['bb_width'] > 0.02 else 'N')
            
            fvg_aligned = check_fvg_bounce(df, idx, 'short', fvgs, lookback=20)
            fvg_price = None
            if fvg_aligned:
                for fvg in fvgs:
                    if abs(fvg['index'] - idx) <= 20 and fvg['type'] == 'bearish':
                        fvg_price = fvg['price']
                        macro['macro_score'] = min(100, macro['macro_score'] + 30)
                        total_confluence = min(100, total_confluence + 10)
                        break
            
            signal = HybridSignal(
                signal_id=f"HYBRID-{int(datetime.now().timestamp())}-S",
                timestamp=int(row.get('time', 0)),
                direction='short',
                macro_bias=macro['macro_bias'],
                ema_cross=macro['ema_cross'],
                ema_fast=macro['ema_fast'],
                ema_slow=macro['ema_slow'],
                sar_aligned=macro['sar_aligned'],
                sar_level=macro['sar_level'],
                fvg_aligned=fvg_aligned,
                fvg_price=fvg_price,
                extrema_detected=micro['extrema_detected'],
                atr14=micro['atr14'],
                bb_width=micro['bb_width'],
                volume_zscore=micro['volume_zscore'],
                breakout_confirmed=micro['breakout_confirmed'],
                breakout_price=micro['breakout_price'],
                macro_score=macro['macro_score'],
                micro_score=micro['micro_score'],
                total_confluence=total_confluence,
                tier=tier,
                entry_price=entry_price,
                stop_loss=stop_loss,
                tp1=tp1,
                tp2=tp2,
                tp3=tp3,
                confidence=confidence,
                play_type=play_type,
                regime=regime
            )
            
            signals.append(signal)
        
        return signals
