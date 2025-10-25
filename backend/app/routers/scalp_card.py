"""
Scalp Card endpoint for manual execution.
Generates a complete trade card with entry, SL, TPs, and microstructure checks.
"""
from fastapi import APIRouter, HTTPException, Query

from ..config import settings
from ..services.signal_engine import mark_candidates, micro_confirm
from ..utils.micro_store import get_snapshot
from ..utils.store import get_df

router = APIRouter()


@router.get("/card")
def scalp_card(
    atr_min: float = Query(default=None),
    volz_min: float = Query(default=None),
    bbw_min: float = Query(default=None),
    breakout_atr_mult: float = Query(default=None),
    vol_mult: float = Query(default=None),
    confirm_window: int = Query(default=None),
    enable_micro_gate: bool = Query(default=True),
    force: bool = Query(default=False),
    symbol: str = Query(default="SOLUSDT"),
):
    """
    Generate a manual-execution Scalp Card.
    
    Returns a complete trade specification card with:
    - Entry, SL, TP ladder (R1, R2, R3)
    - Confirmation rule
    - Trail rule
    - Order path & attempts
    - Microstructure checks & veto reasons
    
    Args:
        atr_min: Minimum ATR14 (default from settings)
        volz_min: Minimum volume z-score (default from settings)
        bbw_min: Minimum BB width (default from settings)
        breakout_atr_mult: Breakout ATR multiplier (default from settings)
        vol_mult: Volume confirmation multiplier (default from settings)
        confirm_window: Confirmation window bars (default from settings)
        enable_micro_gate: Enable microstructure gating
        force: Force card generation even if no confirmation (demo mode)
        symbol: Trading symbol
    
    Returns:
        Dict with "card" containing full trade spec, or "message" if no signal
    """
    # Use settings defaults if not provided
    atr_min = atr_min if atr_min is not None else settings.ATR_MIN
    volz_min = volz_min if volz_min is not None else settings.VOLZ_MIN
    bbw_min = bbw_min if bbw_min is not None else settings.BBW_MIN
    breakout_atr_mult = (
        breakout_atr_mult if breakout_atr_mult is not None
        else settings.BREAKOUT_ATR_MULT
    )
    vol_mult = vol_mult if vol_mult is not None else settings.VOL_MULT
    confirm_window = (
        confirm_window if confirm_window is not None
        else settings.CONFIRM_WINDOW
    )
    
    df = get_df()
    if df is None:
        raise HTTPException(400, "No data loaded. Upload CSV first.")

    df2 = mark_candidates(df, atr_min, volz_min, bbw_min)

    # Search for most recent confirmed signal
    for i in range(len(df2) - 1, -1, -1):
        is_long = bool(df2.at[i, "cand_long"])
        is_short = bool(df2.at[i, "cand_short"])
        side = "long" if is_long else ("short" if is_short else None)
        if not side:
            continue

        j, veto = micro_confirm(
            df2, i, side,
            confirm_window=confirm_window,
            breakout_atr_mult=breakout_atr_mult,
            vol_mult=vol_mult,
            enable_micro_gate=enable_micro_gate
        )

        if j is None:
            # Not confirmed - show why if we have veto
            return {"message": "no confirmed signal", "veto": veto or {}}

        # Calculate trade parameters
        entry = float(df2.at[j, "close"])
        atr5 = float(df2.at[i, "ATR14"] * (5/14))
        
        if side == "long":
            sl = float(min(df2.at[i, "low"], entry - 0.9 * atr5))
            R = entry - sl
            tp1, tp2, tp3 = entry + 1.0*R, entry + 2.0*R, entry + 3.0*R
            breakout_level = df2.at[i, 'high'] + 0.5*atr5
            confirm = f"after fill, 5m close ≥ {round(breakout_level, 4)}"
            play, regime = "Long-B", "N"
        else:
            sl = float(max(df2.at[i, "high"], entry + 0.9 * atr5))
            R = sl - entry
            tp1, tp2, tp3 = entry - 1.0*R, entry - 2.0*R, entry - 3.0*R
            breakout_level = df2.at[i, 'low'] - 0.5*atr5
            confirm = f"after fill, 5m close ≤ {round(breakout_level, 4)}"
            play, regime = "Short-B", "N"

        # Get microstructure snapshot for checks
        snap = get_snapshot()
        spread_ok = (snap.spread_bps < 10.0) if snap else False
        
        # Build the complete scalp card
        card = {
            "symbol": symbol,
            "play": play,  # Long-A | Long-B | Short-A | Short-B
            "regime": regime,  # S | N | W (frontend can infer from BB width)
            "size": "A",  # A | B (frontend can downgrade based on micro)
            "entry": round(entry, 4),
            "confirm": confirm,
            "sl": round(sl, 4),
            "tp1": round(tp1, 4),
            "tp2": round(tp2, 4),
            "tp3": round(tp3, 4),
            "trail_rule": "0.5×ATR(5m) after TP1",
            "attempts": "1/2",
            "order_path": (
                "post-only (offset 2 ticks) → "
                "if unfilled after 3 bars, convert ≤50% to market (slip ≤0.05%)"
            ),
            "checks": {
                "spread_ok": spread_ok,
                "micro_veto": veto or {},
            },
            "indices": {
                "extremum_idx": int(i),
                "confirm_idx": int(j)
            },
        }
        return {"card": card}

    return {"message": "no candidates found"}
