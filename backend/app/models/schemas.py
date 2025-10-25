
from pydantic import BaseModel


class Candle(BaseModel):
    time: int
    open: float
    high: float
    low: float
    close: float
    Volume: float

class BacktestParams(BaseModel):
    atr_min: float = 0.6
    volz_min: float = 1.0
    bbw_min: float = 0.005
    breakout_atr_mult: float = 0.5
    vol_mult: float = 1.5
    confirm_window: int = 6

class SignalOut(BaseModel):
    side: str
    extremum_index: int
    confirm_index: int
    entry: float
    sl: float
    tp1: float
    tp2: float
    tp3: float
    trail_atr_mult: float = 0.5
    veto: str | None = None

class BacktestSummary(BaseModel):
    trades: int
    wins: int
    losses: int
    win_rate: float
    avg_R: float
    pnl_R: float
    max_dd_R: float