"""
Regime Detector (Phase 2)
Implements Squeeze/Normal/Wide regime classification based on BBWidth percentiles.
Part of the SOLUSDT Swing-Capture Playbook v1.0
"""
import pandas as pd
import numpy as np
from typing import Optional, Dict, Tuple
from ..utils.logging import get_logger

logger = get_logger(__name__)


class RegimeDetector:
    """
    Detects market regime based on Bollinger Band Width percentiles.
    
    Regimes (5m BBWidth, 90-bar percentiles):
    - Squeeze: ≤30th percentile
    - Normal: 30-70th percentile  
    - Wide: ≥70th percentile
    """
    
    def __init__(
        self,
        squeeze_threshold: float = 30.0,
        wide_threshold: float = 70.0,
        window: int = 90
    ):
        """
        Initialize regime detector.
        
        Args:
            squeeze_threshold: Percentile threshold for squeeze (default 30)
            wide_threshold: Percentile threshold for wide (default 70)
            window: Rolling window for percentile calculation (default 90 bars)
        """
        self.squeeze_threshold = squeeze_threshold
        self.wide_threshold = wide_threshold
        self.window = window
        
        logger.info(
            f"RegimeDetector initialized: "
            f"squeeze≤{squeeze_threshold}%, wide≥{wide_threshold}%, window={window}"
        )
    
    def compute_bbwidth(self, df: pd.DataFrame, period: int = 20, std_dev: int = 2) -> pd.Series:
        """
        Compute Bollinger Band Width.
        BBWidth = (BBupper - BBlower) / BBupper
        
        Args:
            df: DataFrame with close prices
            period: BB period (default 20)
            std_dev: Standard deviations (default 2)
        
        Returns:
            Series with BBWidth values
        """
        close = df['close']
        sma = close.rolling(window=period).mean()
        std = close.rolling(window=period).std()
        
        bb_upper = sma + (std_dev * std)
        bb_lower = sma - (std_dev * std)
        
        bbwidth = (bb_upper - bb_lower) / bb_upper
        
        return bbwidth
    
    def compute_percentile(self, df: pd.DataFrame, column: str = 'BBWidth') -> pd.Series:
        """
        Compute rolling percentile rank for BBWidth.
        
        Args:
            df: DataFrame with BBWidth data
            column: Column name for BBWidth
        
        Returns:
            Series with percentile values (0-100)
        """
        if column not in df.columns:
            return pd.Series(np.nan, index=df.index)
        
        percentile = df[column].rolling(window=self.window).apply(
            lambda x: pd.Series(x).rank(pct=True).iloc[-1] * 100,
            raw=False
        )
        
        return percentile
    
    def detect_regime(self, bbwidth_pct: float) -> str:
        """
        Classify regime based on BBWidth percentile.
        
        Args:
            bbwidth_pct: BBWidth percentile value
        
        Returns:
            Regime string: 'squeeze', 'normal', or 'wide'
        """
        if pd.isna(bbwidth_pct):
            return 'unknown'
        
        if bbwidth_pct <= self.squeeze_threshold:
            return 'squeeze'
        elif bbwidth_pct >= self.wide_threshold:
            return 'wide'
        else:
            return 'normal'
    
    def get_regime_params(self, regime: str) -> Dict:
        """
        Get regime-specific parameters from playbook.
        
        Args:
            regime: Regime string
        
        Returns:
            Dict with regime parameters
        """
        params = {
            'squeeze': {
                'need_two_closes': True,
                'trigger_atr_mult': 0.50,  # Default, tighter
                'tp1_r': 1.0,
                'tp2_r': 2.5,  # Extended in squeeze
                'tp3_r': 4.0,  # Extended in squeeze
                'vol_spike_mult': 1.5
            },
            'normal': {
                'need_two_closes': False,
                'trigger_atr_mult': 0.50,
                'tp1_r': 1.0,
                'tp2_r': 2.0,
                'tp3_r': 3.0,
                'vol_spike_mult': 1.5
            },
            'wide': {
                'need_two_closes': False,
                'trigger_atr_mult': 0.35,  # Looser in wide
                'tp1_r': 1.0,
                'tp2_r': 2.0,
                'tp3_r': 3.0,
                'vol_spike_mult': 1.5,
                'early_trail': True  # Consider earlier trail if whipsaw
            }
        }
        
        return params.get(regime, params['normal'])
    
    def analyze_regime(self, df: pd.DataFrame) -> Dict:
        """
        Comprehensive regime analysis.
        
        Args:
            df: DataFrame with 5m OHLC data
        
        Returns:
            Dict with regime analysis
        """
        result = {
            'regime': 'unknown',
            'bbwidth': np.nan,
            'bbwidth_pct': np.nan,
            'params': {},
            'details': {}
        }
        
        if df is None or len(df) < self.window:
            result['details']['error'] = 'Insufficient data'
            return result
        
        try:
            # Compute BBWidth if not present
            if 'BBWidth' not in df.columns:
                df['BBWidth'] = self.compute_bbwidth(df)
            
            # Compute percentile if not present
            if 'BBWidth_pct' not in df.columns:
                df['BBWidth_pct'] = self.compute_percentile(df, 'BBWidth')
            
            # Get current values
            current_bbwidth = df['BBWidth'].iloc[-1]
            current_pct = df['BBWidth_pct'].iloc[-1]
            
            result['bbwidth'] = current_bbwidth
            result['bbwidth_pct'] = current_pct
            
            # Detect regime
            regime = self.detect_regime(current_pct)
            result['regime'] = regime
            
            # Get regime parameters
            result['params'] = self.get_regime_params(regime)
            
            # Additional details
            result['details'] = {
                'threshold_squeeze': self.squeeze_threshold,
                'threshold_wide': self.wide_threshold,
                'window': self.window,
                'bbwidth_mean': df['BBWidth'].rolling(self.window).mean().iloc[-1],
                'bbwidth_std': df['BBWidth'].rolling(self.window).std().iloc[-1]
            }
            
            logger.info(
                f"Regime detected: {regime.upper()} "
                f"(BBWidth={current_bbwidth:.5f}, pct={current_pct:.1f})"
            )
            
        except Exception as e:
            logger.error(f"Error in regime analysis: {e}", exc_info=True)
            result['details']['error'] = str(e)
        
        return result
    
    def compute_regime_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute all regime-related features.
        
        Args:
            df: DataFrame with 5m OHLC data
        
        Returns:
            DataFrame with regime features added
        """
        df = df.copy()
        
        # BBWidth
        df['BBWidth'] = self.compute_bbwidth(df)
        
        # BBWidth percentile
        df['BBWidth_pct'] = self.compute_percentile(df, 'BBWidth')
        
        # Regime classification
        df['regime'] = df['BBWidth_pct'].apply(self.detect_regime)
        
        return df


def get_regime_adjustment(regime: str, param_type: str) -> float:
    """
    Get regime-specific adjustment factors.
    
    Args:
        regime: Regime string ('squeeze', 'normal', 'wide')
        param_type: Parameter type ('tp2_r', 'tp3_r', 'trigger_mult', etc.)
    
    Returns:
        Adjustment factor
    """
    adjustments = {
        'squeeze': {
            'tp2_r': 2.5,
            'tp3_r': 4.0,
            'trigger_mult': 0.50,
            'confirmation_bars': 2
        },
        'normal': {
            'tp2_r': 2.0,
            'tp3_r': 3.0,
            'trigger_mult': 0.50,
            'confirmation_bars': 1
        },
        'wide': {
            'tp2_r': 2.0,
            'tp3_r': 3.0,
            'trigger_mult': 0.35,
            'confirmation_bars': 1
        }
    }
    
    return adjustments.get(regime, adjustments['normal']).get(param_type, 1.0)
