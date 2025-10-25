import io

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile

from ..services.extrema import mark_local_extrema
from ..services.indicators import compute_indicators
from ..utils.store import set_df

router = APIRouter()

@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Please upload a CSV.")
    raw = await file.read()
    df = pd.read_csv(io.BytesIO(raw))
    required = {"time","open","high","low","close","Volume"}
    if not required.issubset(df.columns):
        raise HTTPException(400, f"CSV must include columns: {sorted(list(required))}")

    df = compute_indicators(df)
    df = mark_local_extrema(df, window=12)
    set_df(df)
    return {"rows": len(df), "columns": list(df.columns)}