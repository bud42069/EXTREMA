"""
Two-stage swing detection methodology.
Stage 1: Candidate detection using ATR/volume/BB filters at extrema
Stage 2: Micro confirmation using breakout candle + volume spike
"""

import pandas as pd


class CandidateDetector:
    """
    Stage 1: Detect candidate swing starts at local extrema.
    """
    
    def __init__(self, 
                 atr_threshold: float = 0.6,
                 vol_z_threshold: float = 0.5,
                 bb_width_threshold: float = 0.005):
        """
        Initialize candidate detector with thresholds.
        
        Args:
            atr_threshold: Minimum ATR14 value
            vol_z_threshold: Minimum volume z-score
            bb_width_threshold: Minimum BB width
        """
        self.atr_threshold = atr_threshold
        self.vol_z_threshold = vol_z_threshold
        self.bb_width_threshold = bb_width_threshold
    
    def check_candidate_long(self, row: pd.Series) -> bool:
        """
        Check if a local minimum qualifies as a long candidate.
        
        Args:
            row: DataFrame row with indicator values
        
        Returns:
            True if candidate conditions are met
        """
        conditions = [
            row.get('ATR14', 0) >= self.atr_threshold,
            row.get('Volume_ZScore', -999) >= self.vol_z_threshold,
            row.get('BB_Width', 0) >= self.bb_width_threshold
        ]
        
        return all(conditions)
    
    def check_candidate_short(self, row: pd.Series) -> bool:
        """
        Check if a local maximum qualifies as a short candidate.
        
        Args:
            row: DataFrame row with indicator values
        
        Returns:
            True if candidate conditions are met
        """
        conditions = [
            row.get('ATR14', 0) >= self.atr_threshold,
            row.get('Volume_ZScore', -999) >= self.vol_z_threshold,
            row.get('BB_Width', 0) >= self.bb_width_threshold
        ]
        
        return all(conditions)
    
    def detect_candidates(self, df: pd.DataFrame, minima_mask: pd.Series, maxima_mask: pd.Series) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Detect all candidates in the dataset.
        
        Args:
            df: DataFrame with indicators
            minima_mask: Boolean mask for local minima
            maxima_mask: Boolean mask for local maxima
        
        Returns:
            Tuple of (long_candidates_df, short_candidates_df)
        """
        # Long candidates (at minima)
        long_candidates = []
        for idx in df[minima_mask].index:
            row = df.loc[idx]
            if self.check_candidate_long(row):
                candidate = {
                    'index': idx,
                    'timestamp': row.get('time', idx),
                    'price': row['close'],
                    'local_high': row['high'],
                    'local_low': row['low'],
                    'ATR14': row.get('ATR14'),
                    'ATR5': row.get('ATR5'),
                    'Volume_ZScore': row.get('Volume_ZScore'),
                    'BB_Width': row.get('BB_Width'),
                    'RSI14': row.get('RSI14'),
                    'direction': 'long',
                    'status': 'candidate'
                }
                long_candidates.append(candidate)
        
        # Short candidates (at maxima)
        short_candidates = []
        for idx in df[maxima_mask].index:
            row = df.loc[idx]
            if self.check_candidate_short(row):
                candidate = {
                    'index': idx,
                    'timestamp': row.get('time', idx),
                    'price': row['close'],
                    'local_high': row['high'],
                    'local_low': row['low'],
                    'ATR14': row.get('ATR14'),
                    'ATR5': row.get('ATR5'),
                    'Volume_ZScore': row.get('Volume_ZScore'),
                    'BB_Width': row.get('BB_Width'),
                    'RSI14': row.get('RSI14'),
                    'direction': 'short',
                    'status': 'candidate'
                }
                short_candidates.append(candidate)
        
        return pd.DataFrame(long_candidates), pd.DataFrame(short_candidates)


class MicroConfirmation:
    """
    Stage 2: Confirm candidates using breakout candle + volume spike within confirmation window.
    """
    
    def __init__(self,
                 confirmation_window: int = 6,
                 atr_multiplier: float = 0.5,
                 volume_multiplier: float = 1.5):
        """
        Initialize micro confirmation with parameters.
        
        Args:
            confirmation_window: Number of bars to wait for confirmation (default 6 = 30 min on 5m)
            atr_multiplier: ATR multiplier for breakout threshold
            volume_multiplier: Volume multiplier for confirmation
        """
        self.confirmation_window = confirmation_window
        self.atr_multiplier = atr_multiplier
        self.volume_multiplier = volume_multiplier
    
    def check_long_confirmation(self, df: pd.DataFrame, candidate_idx: int, 
                               local_high: float, atr5: float) -> dict | None:
        """
        Check if a long candidate gets confirmed within the window.
        
        Args:
            df: Full DataFrame
            candidate_idx: Index position of candidate
            local_high: High at the candidate extrema
            atr5: ATR5 value at candidate
        
        Returns:
            Dict with confirmation info if confirmed, None otherwise
        """
        start_pos = df.index.get_loc(candidate_idx)
        end_pos = min(start_pos + self.confirmation_window + 1, len(df))
        
        # Breakout threshold
        breakout_level = local_high + (self.atr_multiplier * atr5)
        
        # Get median volume for comparison
        vol_median = df['Volume'].rolling(window=50).median()
        
        # Check each bar in the confirmation window
        for i in range(start_pos + 1, end_pos):
            bar = df.iloc[i]
            bar_idx = df.index[i]
            
            # Check breakout: close above breakout level
            breakout_confirmed = bar['close'] > breakout_level
            
            # Check volume spike
            vol_threshold = vol_median.iloc[i] * self.volume_multiplier
            volume_confirmed = bar['Volume'] >= vol_threshold
            
            # Both conditions must be met
            if breakout_confirmed and volume_confirmed:
                return {
                    'confirmed': True,
                    'confirmation_bar': i - start_pos,
                    'confirmation_idx': bar_idx,
                    'entry_price': bar['close'],
                    'volume': bar['Volume'],
                    'breakout_level': breakout_level
                }
        
        return None
    
    def check_short_confirmation(self, df: pd.DataFrame, candidate_idx: int,
                                local_low: float, atr5: float) -> dict | None:
        """
        Check if a short candidate gets confirmed within the window.
        
        Args:
            df: Full DataFrame
            candidate_idx: Index position of candidate
            local_low: Low at the candidate extrema
            atr5: ATR5 value at candidate
        
        Returns:
            Dict with confirmation info if confirmed, None otherwise
        """
        start_pos = df.index.get_loc(candidate_idx)
        end_pos = min(start_pos + self.confirmation_window + 1, len(df))
        
        # Breakout threshold
        breakout_level = local_low - (self.atr_multiplier * atr5)
        
        # Get median volume for comparison
        vol_median = df['Volume'].rolling(window=50).median()
        
        # Check each bar in the confirmation window
        for i in range(start_pos + 1, end_pos):
            bar = df.iloc[i]
            bar_idx = df.index[i]
            
            # Check breakout: close below breakout level
            breakout_confirmed = bar['close'] < breakout_level
            
            # Check volume spike
            vol_threshold = vol_median.iloc[i] * self.volume_multiplier
            volume_confirmed = bar['Volume'] >= vol_threshold
            
            # Both conditions must be met
            if breakout_confirmed and volume_confirmed:
                return {
                    'confirmed': True,
                    'confirmation_bar': i - start_pos,
                    'confirmation_idx': bar_idx,
                    'entry_price': bar['close'],
                    'volume': bar['Volume'],
                    'breakout_level': breakout_level
                }
        
        return None
    
    def confirm_candidates(self, df: pd.DataFrame, 
                          long_candidates: pd.DataFrame,
                          short_candidates: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Process all candidates and return confirmed signals.
        
        Args:
            df: Full DataFrame with price/indicator data
            long_candidates: DataFrame of long candidates
            short_candidates: DataFrame of short candidates
        
        Returns:
            Tuple of (confirmed_longs, confirmed_shorts) DataFrames
        """
        confirmed_longs = []
        confirmed_shorts = []
        
        # Process long candidates
        for _, candidate in long_candidates.iterrows():
            confirmation = self.check_long_confirmation(
                df, 
                candidate['index'],
                candidate['local_high'],
                candidate['ATR5']
            )
            
            if confirmation:
                signal = candidate.to_dict()
                signal.update(confirmation)
                signal['status'] = 'confirmed'
                confirmed_longs.append(signal)
        
        # Process short candidates
        for _, candidate in short_candidates.iterrows():
            confirmation = self.check_short_confirmation(
                df,
                candidate['index'],
                candidate['local_low'],
                candidate['ATR5']
            )
            
            if confirmation:
                signal = candidate.to_dict()
                signal.update(confirmation)
                signal['status'] = 'confirmed'
                confirmed_shorts.append(signal)
        
        return pd.DataFrame(confirmed_longs), pd.DataFrame(confirmed_shorts)


class TwoStageDetector:
    """
    Complete two-stage detection pipeline.
    """
    
    def __init__(self,
                 atr_threshold: float = 0.6,
                 vol_z_threshold: float = 0.5,
                 bb_width_threshold: float = 0.005,
                 confirmation_window: int = 6,
                 atr_multiplier: float = 0.5,
                 volume_multiplier: float = 1.5):
        """Initialize with all parameters."""
        self.candidate_detector = CandidateDetector(
            atr_threshold=atr_threshold,
            vol_z_threshold=vol_z_threshold,
            bb_width_threshold=bb_width_threshold
        )
        
        self.micro_confirmation = MicroConfirmation(
            confirmation_window=confirmation_window,
            atr_multiplier=atr_multiplier,
            volume_multiplier=volume_multiplier
        )
    
    def detect_signals(self, df: pd.DataFrame, 
                      minima_mask: pd.Series, 
                      maxima_mask: pd.Series) -> dict:
        """
        Run complete two-stage detection.
        
        Args:
            df: DataFrame with indicators
            minima_mask: Boolean mask for local minima
            maxima_mask: Boolean mask for local maxima
        
        Returns:
            Dict with candidates and confirmed signals
        """
        # Stage 1: Detect candidates
        long_candidates, short_candidates = self.candidate_detector.detect_candidates(
            df, minima_mask, maxima_mask
        )
        
        # Stage 2: Confirm candidates
        confirmed_longs, confirmed_shorts = self.micro_confirmation.confirm_candidates(
            df, long_candidates, short_candidates
        )
        
        return {
            'long_candidates': long_candidates,
            'short_candidates': short_candidates,
            'confirmed_longs': confirmed_longs,
            'confirmed_shorts': confirmed_shorts,
            'total_candidates': len(long_candidates) + len(short_candidates),
            'total_confirmed': len(confirmed_longs) + len(confirmed_shorts)
        }
