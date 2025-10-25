"""
In-memory store for microstructure data snapshot.
Holds the latest orderbook depth, trades, CVD, and imbalance metrics.
"""
from dataclasses import dataclass
from typing import Optional
import time


@dataclass
class MicroSnapshot:
    """
    Real-time microstructure snapshot from MEXC orderbook and trades.
    
    Attributes:
        ts: Timestamp of snapshot
        best_bid: Best bid price
        best_ask: Best ask price
        spread_bps: Spread in basis points (0.10% = 10 bps)
        bid_agg: Cumulative bid depth (top 20 levels)
        ask_agg: Cumulative ask depth (top 20 levels)
        ladder_imbalance: (bid_agg - ask_agg) / (bid_agg + ask_agg)
        cvd: Cumulative Volume Delta (tick rule)
        cvd_slope: CVD slope over rolling window (EMA or linear regression)
        trade_v: Last N trades volume sum
        ok: Overall health flag
    """
    ts: float
    best_bid: float
    best_ask: float
    spread_bps: float
    bid_agg: float
    ask_agg: float
    ladder_imbalance: float
    cvd: float
    cvd_slope: float
    trade_v: float
    ok: bool


# Global snapshot singleton
SNAP: Optional[MicroSnapshot] = None


def set_snapshot(s: MicroSnapshot):
    """Update the global microstructure snapshot."""
    global SNAP
    SNAP = s


def get_snapshot() -> Optional[MicroSnapshot]:
    """Retrieve the current microstructure snapshot."""
    return SNAP


def reset_snapshot():
    """Clear the microstructure snapshot."""
    global SNAP
    SNAP = None
