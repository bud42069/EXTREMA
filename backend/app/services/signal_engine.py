import pandas as pd
from typing import Optional

def mark_candidates(df: pd.DataFrame, atr_min=0.6, volz_min=0.5, bbw_min=0.005) -> pd.DataFrame:
    df = df.copy()
    df["cand_long"]  = (df["local_min"]) & (df["ATR14"]>=atr_min) & (df["vol_z"]>=volz_min) & (df["BBWidth"]>=bbw_min)
    df["cand_short"] = (df["local_max"]) & (df["ATR14"]>=atr_min) & (df["vol_z"]>=volz_min) & (df["BBWidth"]>=bbw_min)
    return df

def micro_confirm(df: pd.DataFrame, i: int, side: str,
                  confirm_window=6, breakout_atr_mult=0.5, vol_mult=1.5) -> Optional[int]:
    """Return index j of confirmation bar, else None."""
    if side == "long":
        base = df.at[i,"high"]
    else:
        base = df.at[i,"low"]

    # rough proxy for ATR5 using ATR14 scaling (keeps things simple)
    atr5 = df.at[i,"ATR14"] * (5/14)

    lo = i+1
    hi = min(i+1+confirm_window, len(df)-1)
    med_vol = df["Volume"].rolling(50).median()

    for j in range(lo, hi+1):
        if side == "long":
            brk = df.at[j,"close"] > base + breakout_atr_mult*atr5
        else:
            brk = df.at[j,"close"] < base - breakout_atr_mult*atr5
        vol_ok = df.at[j,"Volume"] >= vol_mult * (med_vol.at[j] if pd.notna(med_vol.at[j]) else 0)
        if brk and vol_ok:
            return j
    return None