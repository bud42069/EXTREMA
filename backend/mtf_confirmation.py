"""
Multi-timeframe confirmation for higher quality signals.
Checks 1H and 4H alignment for A-tier signal validation.
"""
from dataclasses import dataclass

import pandas as pd


@dataclass
class MTFConfirmation:
    """Multi-timeframe confirmation result."""
    h1_aligned: bool = False
    h4_aligned: bool = False
    h1_ema_alignment: bool = False
    h1_momentum: str = "neutral"  # bullish | bearish | neutral
    h4_ema_alignment: bool = False
    h4_momentum: str = "neutral"
    overall_score: float = 0.0
    tier_upgrade: bool = False  # Upgrade to A-tier if true


class MultiTimeframeAnalyzer:
    """
    Analyzes higher timeframes (1H, 4H) for signal confirmation.
    """
    
    def __init__(self):
        self.h1_candles = []
        self.h4_candles = []
    
    def build_higher_tf_candles(self, df_5m: pd.DataFrame) -> dict[str, pd.DataFrame]:
        """
        Build 1H and 4H candles from 5-minute data.
        
        Args:
            df_5m: DataFrame with 5-minute OHLCV data
        
        Returns:
            Dict with '1H' and '4H' DataFrames
        """
        if len(df_5m) < 12:  # Need at least 1 hour of data
            return {'1H': pd.DataFrame(), '4H': pd.DataFrame()}
        
        df = df_5m.copy()
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        
        # Resample to 1H
        df_1h = df.resample('1H').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'Volume': 'sum'
        }).dropna()
        
        # Resample to 4H
        df_4h = df.resample('4H').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'Volume': 'sum'
        }).dropna()
        
        # Reset index to get time as column
        df_1h.reset_index(inplace=True)
        df_4h.reset_index(inplace=True)
        
        return {'1H': df_1h, '4H': df_4h}
    
    def calculate_ema(self, df: pd.DataFrame, period: int) -> pd.Series:
        """Calculate EMA for higher timeframe."""
        return df['close'].ewm(span=period, adjust=False).mean()
    
    def check_ema_alignment(self, df: pd.DataFrame, direction: str) -> bool:
        """
        Check if EMAs are aligned with trade direction.
        
        Args:
            df: DataFrame with price data
            direction: 'long' or 'short'
        
        Returns:
            True if aligned
        """
        if len(df) < 20:
            return False
        
        # Calculate EMAs
        ema9 = self.calculate_ema(df, 9)
        ema20 = self.calculate_ema(df, 20)
        ema50 = self.calculate_ema(df, 50) if len(df) >= 50 else ema20
        
        close = df['close'].iloc[-1]
        
        if direction == 'long':
            # For longs: price > EMA9 > EMA20 > EMA50
            return (close > ema9.iloc[-1] and 
                   ema9.iloc[-1] > ema20.iloc[-1] and
                   ema20.iloc[-1] > ema50.iloc[-1])
        else:
            # For shorts: price < EMA9 < EMA20 < EMA50
            return (close < ema9.iloc[-1] and 
                   ema9.iloc[-1] < ema20.iloc[-1] and
                   ema20.iloc[-1] < ema50.iloc[-1])
    
    def detect_momentum(self, df: pd.DataFrame) -> str:
        """
        Detect momentum on higher timeframe.
        
        Returns:
            'bullish' | 'bearish' | 'neutral'
        """
        if len(df) < 10:
            return 'neutral'
        
        # Simple momentum: compare last close to close 5 bars ago
        current = df['close'].iloc[-1]
        past = df['close'].iloc[-6] if len(df) >= 6 else df['close'].iloc[0]
        
        change_pct = ((current - past) / past) * 100
        
        if change_pct > 2.0:
            return 'bullish'
        elif change_pct < -2.0:
            return 'bearish'
        else:
            return 'neutral'
    
    def check_mtf_confirmation(self, df_5m: pd.DataFrame, direction: str) -> MTFConfirmation:
        """
        Check multi-timeframe confirmation for a signal.
        
        Args:
            df_5m: 5-minute DataFrame with sufficient history
            direction: 'long' or 'short'
        
        Returns:
            MTFConfirmation object with alignment results
        """
        # Build higher TF candles
        tf_data = self.build_higher_tf_candles(df_5m)
        df_1h = tf_data['1H']
        df_4h = tf_data['4H']
        
        confirmation = MTFConfirmation()
        
        # Check 1H alignment
        if len(df_1h) >= 20:
            confirmation.h1_ema_alignment = self.check_ema_alignment(df_1h, direction)
            confirmation.h1_momentum = self.detect_momentum(df_1h)
            
            # 1H aligned if EMA aligned AND momentum matches direction
            if direction == 'long':
                confirmation.h1_aligned = (confirmation.h1_ema_alignment and 
                                          confirmation.h1_momentum == 'bullish')
            else:
                confirmation.h1_aligned = (confirmation.h1_ema_alignment and 
                                          confirmation.h1_momentum == 'bearish')
        
        # Check 4H alignment
        if len(df_4h) >= 20:
            confirmation.h4_ema_alignment = self.check_ema_alignment(df_4h, direction)
            confirmation.h4_momentum = self.detect_momentum(df_4h)
            
            # 4H aligned if EMA aligned AND momentum matches direction
            if direction == 'long':
                confirmation.h4_aligned = (confirmation.h4_ema_alignment and 
                                          confirmation.h4_momentum == 'bullish')
            else:
                confirmation.h4_aligned = (confirmation.h4_ema_alignment and 
                                          confirmation.h4_momentum == 'bearish')
        
        # Calculate overall score (0-100)
        score = 0
        if confirmation.h1_aligned:
            score += 50
        if confirmation.h4_aligned:
            score += 50
        
        confirmation.overall_score = score
        
        # Tier upgrade: both 1H and 4H aligned = A-tier quality
        confirmation.tier_upgrade = (confirmation.h1_aligned and confirmation.h4_aligned)
        
        return confirmation
    
    def enhance_signal_with_mtf(self, signal: dict, df_5m: pd.DataFrame) -> dict:
        """
        Enhance a signal with multi-timeframe confirmation data.
        
        Args:
            signal: Signal dictionary
            df_5m: 5-minute DataFrame
        
        Returns:
            Enhanced signal with MTF data
        """
        direction = signal.get('direction', 'long')
        
        # Get MTF confirmation
        mtf = self.check_mtf_confirmation(df_5m, direction)
        
        # Add MTF data to signal
        signal['mtf_1h_aligned'] = mtf.h1_aligned
        signal['mtf_4h_aligned'] = mtf.h4_aligned
        signal['mtf_1h_ema'] = mtf.h1_ema_alignment
        signal['mtf_4h_ema'] = mtf.h4_ema_alignment
        signal['mtf_1h_momentum'] = mtf.h1_momentum
        signal['mtf_4h_momentum'] = mtf.h4_momentum
        signal['mtf_score'] = mtf.overall_score
        signal['mtf_tier_upgrade'] = mtf.tier_upgrade
        
        # Upgrade tier if MTF confirms
        if mtf.tier_upgrade and signal.get('tier') == 'B':
            signal['tier'] = 'A'
            signal['tier_reason'] = 'MTF_UPGRADE'
        
        return signal
