"""
Local extrema detection for swing identification.
Detects local minima and maxima using a rolling window approach.
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from scipy.signal import argrelextrema


def detect_local_extrema(df: pd.DataFrame, window: int = 12, column: str = 'close') -> Tuple[pd.Series, pd.Series]:
    """
    Detect local minima and maxima using rolling window.
    
    Args:
        df: DataFrame with price data
        window: Number of bars on each side to check (default 12 = ±1 hour on 5m)
        column: Column to detect extrema on
    
    Returns:
        Tuple of (minima_mask, maxima_mask) as boolean Series
    """
    prices = df[column].values
    
    # Find local minima (order=window means ±window bars on each side)
    local_min_idx = argrelextrema(prices, np.less_equal, order=window)[0]
    
    # Find local maxima
    local_max_idx = argrelextrema(prices, np.greater_equal, order=window)[0]
    
    # Create boolean masks
    minima_mask = pd.Series(False, index=df.index)
    maxima_mask = pd.Series(False, index=df.index)
    
    if len(local_min_idx) > 0:
        minima_mask.iloc[local_min_idx] = True
    
    if len(local_max_idx) > 0:
        maxima_mask.iloc[local_max_idx] = True
    
    return minima_mask, maxima_mask


def get_extrema_features(df: pd.DataFrame, extrema_mask: pd.Series) -> pd.DataFrame:
    """
    Extract features at extrema points.
    
    Args:
        df: DataFrame with indicators
        extrema_mask: Boolean mask indicating extrema locations
    
    Returns:
        DataFrame with extrema features
    """
    extrema_df = df[extrema_mask].copy()
    
    required_columns = ['ATR14', 'RSI14', 'BB_Width', 'EMA_Slope', 'Volume_ZScore', 
                       'close', 'high', 'low', 'ATR5']
    
    # Select only the required columns that exist
    available_columns = [col for col in required_columns if col in extrema_df.columns]
    extrema_features = extrema_df[available_columns].copy()
    
    return extrema_features


def check_future_swing(df: pd.DataFrame, start_idx: int, is_long: bool, 
                       swing_threshold: float = 10.0, lookahead_bars: int = 288) -> Dict:
    """
    Check if a future swing of >= threshold% occurs within lookahead period.
    
    Args:
        df: DataFrame with price data
        start_idx: Starting index (extrema point)
        is_long: True for long swing (upward), False for short swing (downward)
        swing_threshold: Minimum percentage move to qualify as swing (default 10%)
        lookahead_bars: Number of bars to look ahead (default 288 = 24 hours on 5m)
    
    Returns:
        Dict with swing information: {'occurred': bool, 'peak_idx': int, 'pct_move': float, 'bars_to_peak': int}
    """
    if start_idx >= len(df) - 1:
        return {'occurred': False, 'peak_idx': None, 'pct_move': 0.0, 'bars_to_peak': None}
    
    start_price = df.iloc[start_idx]['close']
    end_idx = min(start_idx + lookahead_bars, len(df))
    
    future_slice = df.iloc[start_idx+1:end_idx]
    
    if is_long:
        # For long: find maximum high
        if len(future_slice) == 0:
            return {'occurred': False, 'peak_idx': None, 'pct_move': 0.0, 'bars_to_peak': None}
        
        peak_idx = future_slice['high'].idxmax()
        peak_price = future_slice.loc[peak_idx, 'high']
        pct_move = ((peak_price - start_price) / start_price) * 100
        
    else:
        # For short: find minimum low
        if len(future_slice) == 0:
            return {'occurred': False, 'peak_idx': None, 'pct_move': 0.0, 'bars_to_peak': None}
        
        peak_idx = future_slice['low'].idxmin()
        peak_price = future_slice.loc[peak_idx, 'low']
        pct_move = ((start_price - peak_price) / start_price) * 100
    
    occurred = pct_move >= swing_threshold
    bars_to_peak = df.index.get_loc(peak_idx) - start_idx if occurred else None
    
    return {
        'occurred': occurred,
        'peak_idx': peak_idx,
        'peak_price': peak_price,
        'pct_move': pct_move,
        'bars_to_peak': bars_to_peak
    }


def label_extrema_with_swings(df: pd.DataFrame, minima_mask: pd.Series, maxima_mask: pd.Series,
                              swing_threshold: float = 10.0, lookahead_bars: int = 288) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Label each extrema with whether a swing occurred in the future.
    
    Args:
        df: DataFrame with price data
        minima_mask: Boolean mask for local minima
        maxima_mask: Boolean mask for local maxima
        swing_threshold: Minimum percentage move
        lookahead_bars: Bars to look ahead
    
    Returns:
        Tuple of (minima_labeled, maxima_labeled) DataFrames
    """
    minima_indices = df[minima_mask].index.tolist()
    maxima_indices = df[maxima_mask].index.tolist()
    
    # Label minima (potential long swings)
    minima_results = []
    for idx in minima_indices:
        idx_pos = df.index.get_loc(idx)
        swing_info = check_future_swing(df, idx_pos, is_long=True, 
                                       swing_threshold=swing_threshold, 
                                       lookahead_bars=lookahead_bars)
        
        result = {
            'index': idx,
            'timestamp': df.loc[idx, 'time'] if 'time' in df.columns else idx,
            'price': df.loc[idx, 'close'],
            'swing_occurred': swing_info['occurred'],
            'peak_price': swing_info['peak_price'] if swing_info['occurred'] else None,
            'pct_move': swing_info['pct_move'],
            'bars_to_peak': swing_info['bars_to_peak'],
            'direction': 'long'
        }
        
        # Add indicator values
        for col in ['ATR14', 'RSI14', 'BB_Width', 'EMA_Slope', 'Volume_ZScore']:
            if col in df.columns:
                result[col] = df.loc[idx, col]
        
        minima_results.append(result)
    
    # Label maxima (potential short swings)
    maxima_results = []
    for idx in maxima_indices:
        idx_pos = df.index.get_loc(idx)
        swing_info = check_future_swing(df, idx_pos, is_long=False, 
                                       swing_threshold=swing_threshold, 
                                       lookahead_bars=lookahead_bars)
        
        result = {
            'index': idx,
            'timestamp': df.loc[idx, 'time'] if 'time' in df.columns else idx,
            'price': df.loc[idx, 'close'],
            'swing_occurred': swing_info['occurred'],
            'peak_price': swing_info['peak_price'] if swing_info['occurred'] else None,
            'pct_move': swing_info['pct_move'],
            'bars_to_peak': swing_info['bars_to_peak'],
            'direction': 'short'
        }
        
        # Add indicator values
        for col in ['ATR14', 'RSI14', 'BB_Width', 'EMA_Slope', 'Volume_ZScore']:
            if col in df.columns:
                result[col] = df.loc[idx, col]
        
        maxima_results.append(result)
    
    minima_df = pd.DataFrame(minima_results)
    maxima_df = pd.DataFrame(maxima_results)
    
    return minima_df, maxima_df
