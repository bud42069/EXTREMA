"""
Microstructure feature extraction and veto logic.
Gates signal confirmation based on orderbook depth, spread, imbalance, and CVD.
"""
from typing import Optional

from ..utils.micro_store import MicroSnapshot, get_snapshot
from ..utils.logging import get_logger

logger = get_logger(__name__)


def micro_ok(
    side: str,
    snap: Optional[MicroSnapshot],
    spread_bps_max: float = 10.0,
    depth_min: float = 0.0,
    imb_threshold: float = 0.15,
    cvd_slope_min: float = 0.0
) -> tuple[bool, dict, float]:
    """
    Evaluate microstructure health and return veto flags + confluence bonus.
    
    Args:
        side: Trade direction ("long" or "short")
        snap: Current microstructure snapshot
        spread_bps_max: Maximum allowed spread in basis points
        depth_min: Minimum required depth (0 = no check)
        imb_threshold: Minimum ladder imbalance magnitude
        cvd_slope_min: Minimum CVD slope magnitude (0 = no check)
    
    Returns:
        Tuple of (ok: bool, veto: dict, bonus: float)
        - ok: True if all gates pass
        - veto: Dict of failed gates with values
        - bonus: Confluence bonus (0.0 to 0.10) based on imbalance strength
    
    Veto Reasons:
        - no_snapshot: No microstructure data available
        - spread: Spread too wide
        - depth: Insufficient depth on one or both sides
        - imbalance: Ladder imbalance not favorable
        - cvd_slope: CVD slope not aligned with trade direction
    """
    veto = {}
    ok = True
    bonus = 0.0
    
    # No snapshot = veto
    if snap is None:
        veto["no_snapshot"] = True
        return False, veto, bonus
    
    # Spread check
    if snap.spread_bps >= spread_bps_max:
        veto["spread"] = snap.spread_bps
        ok = False
        logger.debug(f"Spread veto: {snap.spread_bps:.2f} bps >= {spread_bps_max}")
    
    # Depth check
    if depth_min > 0:
        if min(snap.bid_agg, snap.ask_agg) <= depth_min:
            veto["depth"] = {
                "bid": snap.bid_agg,
                "ask": snap.ask_agg,
                "min_required": depth_min
            }
            ok = False
            logger.debug(
                f"Depth veto: bid={snap.bid_agg:.2f}, "
                f"ask={snap.ask_agg:.2f}, min={depth_min}"
            )
    
    # Ladder imbalance check
    if side == "long":
        imb_ok = snap.ladder_imbalance > imb_threshold
    else:  # short
        imb_ok = snap.ladder_imbalance < -imb_threshold
    
    if not imb_ok:
        veto["imbalance"] = snap.ladder_imbalance
        ok = False
        logger.debug(
            f"Imbalance veto ({side}): {snap.ladder_imbalance:.3f}, "
            f"threshold={imb_threshold}"
        )
    
    # CVD slope check
    if cvd_slope_min > 0:
        if side == "long":
            slope_ok = snap.cvd_slope > cvd_slope_min
        else:
            slope_ok = snap.cvd_slope < -cvd_slope_min
        
        if not slope_ok:
            veto["cvd_slope"] = snap.cvd_slope
            ok = False
            logger.debug(
                f"CVD slope veto ({side}): {snap.cvd_slope:.2f}, "
                f"threshold={cvd_slope_min}"
            )
    
    # Calculate confluence bonus if all gates passed
    if ok:
        # Bonus based on imbalance strength (up to +0.10)
        bonus = min(0.10, abs(snap.ladder_imbalance))
        logger.debug(
            f"Microstructure OK ({side}): imb={snap.ladder_imbalance:.3f}, "
            f"bonus={bonus:.3f}"
        )
    
    return ok, veto, bonus


def get_micro_summary(snap: Optional[MicroSnapshot]) -> dict:
    """
    Get a summary dict of microstructure metrics for API responses.
    
    Returns:
        Dict with spread, depth, imbalance, CVD metrics, or empty if no snapshot
    """
    if snap is None:
        return {
            "available": False,
            "message": "No microstructure data"
        }
    
    return {
        "available": True,
        "ts": snap.ts,
        "spread_bps": round(snap.spread_bps, 2),
        "best_bid": round(snap.best_bid, 4),
        "best_ask": round(snap.best_ask, 4),
        "bid_depth": round(snap.bid_agg, 2),
        "ask_depth": round(snap.ask_agg, 2),
        "ladder_imbalance": round(snap.ladder_imbalance, 3),
        "cvd": round(snap.cvd, 2),
        "cvd_slope": round(snap.cvd_slope, 4),
        "trade_volume": round(snap.trade_v, 2),
        "ok": snap.ok
    }
