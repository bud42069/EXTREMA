from fastapi import APIRouter, HTTPException
from ..utils.store import get_df
from ..models.schemas import BacktestParams
from ..services.backtester import run_backtest

router = APIRouter()

@router.post("/run")
def run(params: BacktestParams):
    df = get_df()
    if df is None:
        raise HTTPException(400, "No data loaded")
    result = run_backtest(
        df,
        atr_min=params.atr_min,
        volz_min=params.volz_min,
        bbw_min=params.bbw_min,
        breakout_atr_mult=params.breakout_atr_mult,
        vol_mult=params.vol_mult,
        confirm_window=params.confirm_window
    )
    return result