import numpy as np
import pandas as pd


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.sort_values("time").reset_index(drop=True)
    close = df["close"]
    high = df["high"]
    low = df["low"]
    vol = df["Volume"]

    # ATR14
    prev_close = close.shift(1)
    tr = pd.concat([
        (high - low).abs(),
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)
    df["ATR14"] = tr.rolling(14).mean()

    # RSI14
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean().replace(0, np.nan)
    rs = avg_gain / avg_loss
    df["RSI14"] = 100 - (100/(1+rs))

    # BB(20,2)
    sma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    df["BB_upper"] = sma20 + 2*std20
    df["BB_lower"] = sma20 - 2*std20
    df["BBWidth"] = (df["BB_upper"] - df["BB_lower"]) / df["BB_upper"]

    # EMAs & slope
    df["EMA_fast"] = close.ewm(span=9, adjust=False).mean()
    df["EMA_slow"] = close.ewm(span=38, adjust=False).mean()
    df["EMA_diff"] = df["EMA_fast"] - df["EMA_slow"]
    df["EMA_slope"] = df["EMA_diff"].diff()

    # Volume z-score(50)
    med = vol.rolling(50).mean()
    std = vol.rolling(50).std()
    df["vol_z"] = (vol - med) / std

    # OBV (On-Balance Volume) and OBV z-score
    price_change = close.diff()
    df["OBV"] = (
        (price_change > 0) * vol -
        (price_change < 0) * vol
    ).fillna(0).cumsum()
    
    # OBV z-score over 10 bars (for cliff detection)
    obv_mean = df["OBV"].rolling(10).mean()
    obv_std = df["OBV"].rolling(10).std()
    df["OBV_z10"] = (df["OBV"] - obv_mean) / obv_std

    return df