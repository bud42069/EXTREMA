from fastapi import APIRouter, HTTPException

from ..services.signal_engine import mark_candidates, micro_confirm
from ..utils.store import get_df

router = APIRouter()

@router.get("/latest")
def latest_signal(atr_min: float = 0.6, volz_min: float = 1.0, bbw_min: float = 0.005,
                  breakout_atr_mult: float = 0.5, vol_mult: float = 1.5, confirm_window: int = 6):
    df = get_df()
    if df is None:
        raise HTTPException(400, "No data loaded")
    df2 = mark_candidates(df, atr_min, volz_min, bbw_min)

    for i in range(len(df2)-1, -1, -1):
        side = "long" if bool(df2.at[i,"cand_long"]) else ("short" if bool(df2.at[i,"cand_short"]) else None)
        if not side:
            continue
        j = micro_confirm(df2, i, side, confirm_window, breakout_atr_mult, vol_mult)
        if j is None:
            continue
        entry = float(df2.at[j,"close"])
        atr5  = float(df2.at[i,"ATR14"] * (5/14))
        if side=="long":
            sl  = float(min(df2.at[i,"low"], entry - 0.9*atr5))
            r   = entry - sl
            tp1, tp2, tp3 = entry + 1.0*r, entry + 2.0*r, entry + 3.0*r
        else:
            sl  = float(max(df2.at[i,"high"], entry + 0.9*atr5))
            r   = sl - entry
            tp1, tp2, tp3 = entry - 1.0*r, entry - 2.0*r, entry - 3.0*r
        return {
            "side": side, "extremum_index": i, "confirm_index": j,
            "entry": entry, "sl": float(sl), "tp1": float(tp1), "tp2": float(tp2), "tp3": float(tp3),
            "trail_atr_mult": 0.5
        }
    return {"message":"no confirmed signal"}