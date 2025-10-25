from fastapi import APIRouter, HTTPException
from ..utils.store import get_df
from ..services.extrema import label_swings

router = APIRouter()

@router.get("/")
def swings_overview():
    df = get_df()
    if df is None:
        raise HTTPException(400, "No data loaded")
    out = label_swings(df)
    total = int(out["swing_any_24h"].sum())
    return {"rows": len(out), "swings_24h": total}