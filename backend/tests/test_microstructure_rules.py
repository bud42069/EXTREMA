"""
Tests for microstructure veto logic.
"""
import time
from app.utils.micro_store import MicroSnapshot
from app.services.microstructure import micro_ok, get_micro_summary


def test_micro_ok_long_favorable():
    """Test microstructure approval for long with favorable conditions."""
    snap = MicroSnapshot(
        ts=time.time(),
        best_bid=100.0,
        best_ask=100.08,  # 8 bps spread
        spread_bps=8.0,
        bid_agg=5000.0,
        ask_agg=4000.0,
        ladder_imbalance=0.20,  # Strong bid-side imbalance
        cvd=1500.0,
        cvd_slope=0.8,  # Positive CVD slope
        trade_v=250.0,
        ok=True
    )
    
    ok, veto, bonus = micro_ok("long", snap, spread_bps_max=10.0, imb_threshold=0.15)
    
    assert ok is True
    assert len(veto) == 0
    assert bonus > 0


def test_micro_ok_short_favorable():
    """Test microstructure approval for short with favorable conditions."""
    snap = MicroSnapshot(
        ts=time.time(),
        best_bid=100.0,
        best_ask=100.08,
        spread_bps=8.0,
        bid_agg=4000.0,
        ask_agg=5000.0,
        ladder_imbalance=-0.20,  # Strong ask-side imbalance
        cvd=1500.0,
        cvd_slope=-0.8,  # Negative CVD slope
        trade_v=250.0,
        ok=True
    )
    
    ok, veto, bonus = micro_ok("short", snap, spread_bps_max=10.0, imb_threshold=0.15)
    
    assert ok is True
    assert len(veto) == 0
    assert bonus > 0


def test_micro_veto_spread():
    """Test veto due to wide spread."""
    snap = MicroSnapshot(
        ts=time.time(),
        best_bid=100.0,
        best_ask=100.15,  # 15 bps spread
        spread_bps=15.0,
        bid_agg=5000.0,
        ask_agg=4000.0,
        ladder_imbalance=0.20,
        cvd=1500.0,
        cvd_slope=0.8,
        trade_v=250.0,
        ok=True
    )
    
    ok, veto, bonus = micro_ok("long", snap, spread_bps_max=10.0, imb_threshold=0.15)
    
    assert ok is False
    assert "spread" in veto
    assert bonus == 0


def test_micro_veto_imbalance():
    """Test veto due to unfavorable imbalance."""
    snap = MicroSnapshot(
        ts=time.time(),
        best_bid=100.0,
        best_ask=100.08,
        spread_bps=8.0,
        bid_agg=4000.0,
        ask_agg=5000.0,
        ladder_imbalance=-0.20,  # Wrong direction for long
        cvd=1500.0,
        cvd_slope=0.8,
        trade_v=250.0,
        ok=True
    )
    
    ok, veto, bonus = micro_ok("long", snap, spread_bps_max=10.0, imb_threshold=0.15)
    
    assert ok is False
    assert "imbalance" in veto
    assert bonus == 0


def test_micro_veto_cvd_slope():
    """Test veto due to adverse CVD slope."""
    snap = MicroSnapshot(
        ts=time.time(),
        best_bid=100.0,
        best_ask=100.08,
        spread_bps=8.0,
        bid_agg=5000.0,
        ask_agg=4000.0,
        ladder_imbalance=0.20,
        cvd=1500.0,
        cvd_slope=-0.8,  # Negative slope for long
        trade_v=250.0,
        ok=True
    )
    
    ok, veto, bonus = micro_ok(
        "long", snap,
        spread_bps_max=10.0,
        imb_threshold=0.15,
        cvd_slope_min=0.5
    )
    
    assert ok is False
    assert "cvd_slope" in veto
    assert bonus == 0


def test_micro_no_snapshot():
    """Test veto when no snapshot available."""
    ok, veto, bonus = micro_ok("long", None)
    
    assert ok is False
    assert "no_snapshot" in veto
    assert bonus == 0


def test_get_micro_summary_with_data():
    """Test micro summary generation with valid snapshot."""
    snap = MicroSnapshot(
        ts=time.time(),
        best_bid=100.0,
        best_ask=100.08,
        spread_bps=8.0,
        bid_agg=5000.0,
        ask_agg=4000.0,
        ladder_imbalance=0.20,
        cvd=1500.0,
        cvd_slope=0.8,
        trade_v=250.0,
        ok=True
    )
    
    summary = get_micro_summary(snap)
    
    assert summary["available"] is True
    assert summary["spread_bps"] == 8.0
    assert summary["best_bid"] == 100.0
    assert summary["ladder_imbalance"] == 0.2
    assert summary["ok"] is True


def test_get_micro_summary_no_data():
    """Test micro summary when no snapshot."""
    summary = get_micro_summary(None)
    
    assert summary["available"] is False
    assert "message" in summary
