
import pandas as pd

from ..utils.micro_store import get_snapshot
from .microstructure import micro_ok


def mark_candidates(
    df: pd.DataFrame,
    atr_min=0.6,
    volz_min=0.5,
    bbw_min=0.005,
    obv_z_veto=2.0
) -> pd.DataFrame:
    """
    Mark candidate entries at local extrema with coarse filters.
    
    Adds OBV-cliff veto: reject candidates with adverse OBV momentum.
    
    Args:
        df: DataFrame with indicators and extrema
        atr_min: Minimum ATR14
        volz_min: Minimum volume z-score
        bbw_min: Minimum Bollinger Band width
        obv_z_veto: OBV z-score threshold for veto (default 2.0)
    
    Returns:
        DataFrame with cand_long and cand_short columns
    """
    df = df.copy()
    
    # Coarse filters
    base_filter_long = (
        (df["local_min"]) &
        (df["ATR14"] >= atr_min) &
        (df["vol_z"] >= volz_min) &
        (df["BBWidth"] >= bbw_min)
    )
    
    base_filter_short = (
        (df["local_max"]) &
        (df["ATR14"] >= atr_min) &
        (df["vol_z"] >= volz_min) &
        (df["BBWidth"] >= bbw_min)
    )
    
    # OBV-cliff veto
    # For longs: veto if OBV_z10 <= -obv_z_veto (selling pressure cliff)
    # For shorts: veto if OBV_z10 >= +obv_z_veto (buying pressure cliff)
    if "OBV_z10" in df.columns:
        obv_ok_long = df["OBV_z10"] > -obv_z_veto
        obv_ok_short = df["OBV_z10"] < obv_z_veto
    else:
        obv_ok_long = True
        obv_ok_short = True
    
    df["cand_long"] = base_filter_long & obv_ok_long
    df["cand_short"] = base_filter_short & obv_ok_short
    
    return df


def micro_confirm(
    df: pd.DataFrame,
    i: int,
    side: str,
    confirm_window=6,
    breakout_atr_mult=0.5,
    vol_mult=1.5,
    enable_micro_gate=True,
    spread_bps_max=10.0,
    imb_threshold=0.15
) -> tuple[int | None, dict]:
    """
    Confirm candidate with breakout + volume + microstructure gates.
    
    Returns:
        Tuple of (confirmation_index, veto_dict)
        - confirmation_index: Bar index where confirmation occurred (or None)
        - veto_dict: Microstructure veto reasons (empty if confirmed)
    """
    if side == "long":
        base = df.at[i, "high"]
    else:
        base = df.at[i, "low"]

    # Rough proxy for ATR5 using ATR14 scaling
    atr5 = df.at[i, "ATR14"] * (5/14)

    lo = i + 1
    hi = min(i + 1 + confirm_window, len(df) - 1)
    med_vol = df["Volume"].rolling(50).median()

    for j in range(lo, hi + 1):
        # Breakout check
        if side == "long":
            brk = df.at[j, "close"] > base + breakout_atr_mult * atr5
        else:
            brk = df.at[j, "close"] < base - breakout_atr_mult * atr5
        
        # Volume check
        med_vol_val = med_vol.at[j] if pd.notna(med_vol.at[j]) else 0
        vol_ok = df.at[j, "Volume"] >= vol_mult * med_vol_val
        
        # If breakout + volume pass, check microstructure
        if brk and vol_ok:
            if enable_micro_gate:
                snap = get_snapshot()
                ok, veto, bonus = micro_ok(
                    side,
                    snap,
                    spread_bps_max=spread_bps_max,
                    imb_threshold=imb_threshold
                )
                
                if ok:
                    # Confirmed with microstructure approval
                    return j, {}
                # Continue searching within window if micro veto
                # (allows for micro conditions to improve)
            else:
                # Micro gate disabled - confirm on breakout + volume alone
                return j, {}
    
    # No confirmation within window
    return None, {}
