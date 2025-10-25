"""
Tests for microstructure data store.
"""
import time
from app.utils.micro_store import (
    MicroSnapshot,
    set_snapshot,
    get_snapshot,
    reset_snapshot
)


def test_snapshot_roundtrip():
    """Test setting and retrieving a snapshot."""
    # Reset first
    reset_snapshot()
    
    # Create a snapshot
    snap = MicroSnapshot(
        ts=time.time(),
        best_bid=100.0,
        best_ask=100.1,
        spread_bps=10.0,
        bid_agg=5000.0,
        ask_agg=4500.0,
        ladder_imbalance=0.05,
        cvd=1500.0,
        cvd_slope=0.5,
        trade_v=250.0,
        ok=True
    )
    
    # Set and retrieve
    set_snapshot(snap)
    retrieved = get_snapshot()
    
    assert retrieved is not None
    assert retrieved.best_bid == 100.0
    assert retrieved.best_ask == 100.1
    assert retrieved.ladder_imbalance == 0.05
    assert retrieved.ok is True


def test_snapshot_reset():
    """Test resetting the snapshot."""
    # Create and set a snapshot
    snap = MicroSnapshot(
        ts=time.time(),
        best_bid=100.0,
        best_ask=100.1,
        spread_bps=10.0,
        bid_agg=5000.0,
        ask_agg=4500.0,
        ladder_imbalance=0.05,
        cvd=1500.0,
        cvd_slope=0.5,
        trade_v=250.0,
        ok=True
    )
    set_snapshot(snap)
    
    # Reset
    reset_snapshot()
    
    # Should be None
    retrieved = get_snapshot()
    assert retrieved is None


def test_snapshot_overwrite():
    """Test overwriting an existing snapshot."""
    # Set first snapshot
    snap1 = MicroSnapshot(
        ts=time.time(),
        best_bid=100.0,
        best_ask=100.1,
        spread_bps=10.0,
        bid_agg=5000.0,
        ask_agg=4500.0,
        ladder_imbalance=0.05,
        cvd=1500.0,
        cvd_slope=0.5,
        trade_v=250.0,
        ok=True
    )
    set_snapshot(snap1)
    
    # Set second snapshot
    snap2 = MicroSnapshot(
        ts=time.time(),
        best_bid=101.0,
        best_ask=101.2,
        spread_bps=20.0,
        bid_agg=6000.0,
        ask_agg=5500.0,
        ladder_imbalance=0.10,
        cvd=2000.0,
        cvd_slope=1.0,
        trade_v=350.0,
        ok=True
    )
    set_snapshot(snap2)
    
    # Should get the second snapshot
    retrieved = get_snapshot()
    assert retrieved.best_bid == 101.0
    assert retrieved.ladder_imbalance == 0.10
