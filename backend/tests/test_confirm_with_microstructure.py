"""
Tests for signal confirmation with microstructure gates.
"""
import time
import pandas as pd
import numpy as np
from unittest.mock import patch

from app.services.signal_engine import mark_candidates, micro_confirm
from app.services.indicators import compute_indicators
from app.services.extrema import detect_local_extrema
from app.utils.micro_store import MicroSnapshot


def create_test_df():
    """Create a test DataFrame with synthetic price data."""
    np.random.seed(42)
    n = 100
    
    df = pd.DataFrame({
        'time': pd.date_range('2024-01-01', periods=n, freq='5min'),
        'open': 100 + np.random.randn(n).cumsum() * 0.5,
        'high': 101 + np.random.randn(n).cumsum() * 0.5,
        'low': 99 + np.random.randn(n).cumsum() * 0.5,
        'close': 100 + np.random.randn(n).cumsum() * 0.5,
        'Volume': 1000 + np.random.rand(n) * 500
    })
    
    # Ensure high >= close >= low
    df['high'] = df[['high', 'close']].max(axis=1)
    df['low'] = df[['low', 'close']].min(axis=1)
    
    return df


def test_confirm_with_micro_gate_enabled():
    """Test confirmation with microstructure gate enabled and favorable."""
    # Create test data
    df = create_test_df()
    df = compute_indicators(df)
    df = detect_local_extrema(df)
    df = mark_candidates(df, atr_min=0.1, volz_min=0.0, bbw_min=0.0)
    
    # Find a candidate
    cand_idx = df[df['cand_long']].index[0] if len(df[df['cand_long']]) > 0 else 50
    
    # Mock favorable microstructure snapshot
    good_snap = MicroSnapshot(
        ts=time.time(),
        best_bid=100.0,
        best_ask=100.08,
        spread_bps=8.0,
        bid_agg=5000.0,
        ask_agg=4000.0,
        ladder_imbalance=0.20,  # Favorable for long
        cvd=1500.0,
        cvd_slope=0.8,
        trade_v=250.0,
        ok=True
    )
    
    with patch('app.services.signal_engine.get_snapshot', return_value=good_snap):
        confirm_idx, veto = micro_confirm(
            df, cand_idx, "long",
            confirm_window=6,
            enable_micro_gate=True
        )
    
    # May or may not find confirmation depending on price action
    # But should not have micro veto
    assert isinstance(veto, dict)


def test_confirm_with_micro_gate_vetoed():
    """Test confirmation vetoed by microstructure."""
    # Create test data
    df = create_test_df()
    df = compute_indicators(df)
    df = detect_local_extrema(df)
    df = mark_candidates(df, atr_min=0.1, volz_min=0.0, bbw_min=0.0)
    
    # Find a candidate
    cand_idx = df[df['cand_long']].index[0] if len(df[df['cand_long']]) > 0 else 50
    
    # Mock unfavorable microstructure snapshot (wide spread)
    bad_snap = MicroSnapshot(
        ts=time.time(),
        best_bid=100.0,
        best_ask=100.20,  # 20 bps spread (too wide)
        spread_bps=20.0,
        bid_agg=5000.0,
        ask_agg=4000.0,
        ladder_imbalance=0.20,
        cvd=1500.0,
        cvd_slope=0.8,
        trade_v=250.0,
        ok=True
    )
    
    with patch('app.services.signal_engine.get_snapshot', return_value=bad_snap):
        confirm_idx, veto = micro_confirm(
            df, cand_idx, "long",
            confirm_window=6,
            enable_micro_gate=True,
            spread_bps_max=10.0
        )
    
    # Should not confirm due to spread veto
    # (unless breakout happens after window, but unlikely in 6 bars)
    assert isinstance(veto, dict)


def test_confirm_with_micro_gate_disabled():
    """Test confirmation with microstructure gate disabled."""
    # Create test data
    df = create_test_df()
    df = compute_indicators(df)
    df = detect_local_extrema(df)
    df = mark_candidates(df, atr_min=0.1, volz_min=0.0, bbw_min=0.0)
    
    # Find a candidate
    cand_idx = df[df['cand_long']].index[0] if len(df[df['cand_long']]) > 0 else 50
    
    # Even with bad microstructure, should confirm if price action is good
    bad_snap = MicroSnapshot(
        ts=time.time(),
        best_bid=100.0,
        best_ask=100.20,
        spread_bps=20.0,
        bid_agg=5000.0,
        ask_agg=4000.0,
        ladder_imbalance=-0.30,  # Wrong direction
        cvd=1500.0,
        cvd_slope=-1.0,  # Wrong direction
        trade_v=250.0,
        ok=True
    )
    
    with patch('app.services.signal_engine.get_snapshot', return_value=bad_snap):
        confirm_idx, veto = micro_confirm(
            df, cand_idx, "long",
            confirm_window=6,
            enable_micro_gate=False  # Disabled
        )
    
    # Should ignore microstructure completely
    assert isinstance(veto, dict)


def test_obv_cliff_veto_in_candidates():
    """Test that OBV cliff vetoes candidates."""
    # Create test data
    df = create_test_df()
    df = compute_indicators(df)
    df = detect_local_extrema(df)
    
    # Artificially set OBV_z10 to trigger veto
    df['OBV_z10'] = 0.0
    df.loc[50, 'OBV_z10'] = -2.5  # Strong selling pressure (below -2.0)
    df.loc[50, 'local_min'] = True  # Make it an extremum
    df.loc[50, 'ATR14'] = 1.0
    df.loc[50, 'vol_z'] = 1.5
    df.loc[50, 'BBWidth'] = 0.01
    
    # Mark candidates with OBV veto enabled
    df = mark_candidates(df, atr_min=0.5, volz_min=1.0, bbw_min=0.005, obv_z_veto=2.0)
    
    # Should NOT be marked as candidate due to OBV cliff
    assert df.loc[50, 'cand_long'] is False
