
import pandas as pd

from .signal_engine import mark_candidates, micro_confirm


def _place_trade(df, i_ext, j_conf, side, breakout_atr_mult=0.5):
    entry = df.at[j_conf, "close"]
    atr5  = df.at[i_ext, "ATR14"] * (5/14)

    if side == "long":
        sl = min(df.at[i_ext, "low"], entry - 0.9*atr5)
        r = entry - sl
        tp1, tp2, tp3 = entry + 1.0*r, entry + 2.0*r, entry + 3.0*r
    else:
        sl = max(df.at[i_ext, "high"], entry + 0.9*atr5)
        r = sl - entry
        tp1, tp2, tp3 = entry - 1.0*r, entry - 2.0*r, entry - 3.0*r

    return dict(entry=entry, sl=sl, tp1=tp1, tp2=tp2, tp3=tp3, R=r)

def run_backtest(df: pd.DataFrame,
                 atr_min=0.6, volz_min=1.0, bbw_min=0.005,
                 breakout_atr_mult=0.5, vol_mult=1.5, confirm_window=6) -> dict:
    df = mark_candidates(df, atr_min, volz_min, bbw_min)
    trades: list[dict] = []

    for i, row in df.iterrows():
        side = None
        if row.get("cand_long", False):
            side = "long"
        elif row.get("cand_short", False):
            side = "short"
        else:
            continue

        j = micro_confirm(df, i, side, confirm_window, breakout_atr_mult, vol_mult)
        if j is None:
            continue

        t = _place_trade(df, i, j, side, breakout_atr_mult)
        t.update(dict(i=i, j=j, side=side))

        # walk forward to see outcome (simple simulator: first touch wins)
        k = j+1
        outcome = None
        while k < len(df):
            px = df.at[k, "low"] if side=="long" else df.at[k, "high"]
            high = df.at[k, "high"]; low = df.at[k, "low"]
            if side=="long":
                if low <= t["sl"]:
                    outcome, R = "loss", -1.0
                    break
                if high >= t["tp1"]:
                    # move SL to BE+fees ~0 → for simplicity we assume BE
                    if high >= t["tp2"]:
                        if high >= t["tp3"]:
                            outcome, R = "win3", 3.0
                        else:
                            outcome, R = "win2", 2.0
                    else:
                        outcome, R = "win1", 1.0
                    break
            else:
                if high >= t["sl"]:
                    outcome, R = "loss", -1.0
                    break
                if low <= t["tp1"]:
                    if low <= t["tp2"]:
                        if low <= t["tp3"]:
                            outcome, R = "win3", 3.0
                        else:
                            outcome, R = "win2", 2.0
                    else:
                        outcome, R = "win1", 1.0
                    break
            k += 1

        if outcome is None:
            outcome, R = "open", 0.0

        t["outcome"] = outcome
        t["R"] = R
        trades.append(t)

    if not trades:
        return dict(summary=dict(trades=0,wins=0,losses=0,win_rate=0,avg_R=0,pnl_R=0,max_dd_R=0), ledger=[])

    df_ledger = pd.DataFrame(trades)
    wins = (df_ledger["R"]>0).sum()
    losses = (df_ledger["R"]<0).sum()
    pnl_R = df_ledger["R"].sum()
    avg_R = df_ledger["R"].mean()
    # naive max drawdown in R (cum)
    cum = df_ledger["R"].cumsum()
    run_max = cum.cummax()
    dd = (cum - run_max).min()
    summary = dict(trades=len(df_ledger), wins=wins, losses=losses,
                   win_rate= (wins/len(df_ledger))*100.0, avg_R=avg_R,
                   pnl_R=pnl_R, max_dd_R=dd)
    return dict(summary=summary, ledger=df_ledger.to_dict(orient="records"))