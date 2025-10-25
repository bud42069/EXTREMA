import pandas as pd
import numpy as np

def mark_local_extrema(df: pd.DataFrame, window: int = 12) -> pd.DataFrame:
    df = df.copy()
    rmin = df["close"].rolling(window*2+1, center=True).min()
    rmax = df["close"].rolling(window*2+1, center=True).max()
    df["local_min"] = (df["close"] == rmin).fillna(False)
    df["local_max"] = (df["close"] == rmax).fillna(False)
    return df

def label_swings(df: pd.DataFrame, lookahead: int = 288) -> pd.DataFrame:
    """For analysis only (no look-ahead in live)."""
    df = df.copy()
    swing_any = [0]*len(df)
    for i in range(len(df)):
        lo = i+1; hi = min(i+1+lookahead, len(df))
        if lo >= hi: break
        if df.at[i,"local_min"]:
            p0 = df.at[i,"close"]
            if (df["close"].iloc[lo:hi].max()/p0 - 1) >= 0.10:
                swing_any[i] = 1
        if df.at[i,"local_max"]:
            p0 = df.at[i,"close"]
            mn = df["close"].iloc[lo:hi].min()
            if (p0/mn - 1) >= 0.10:
                swing_any[i] = 1
    df["swing_any_24h"] = swing_any
    return df