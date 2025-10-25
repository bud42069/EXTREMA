import io
import asyncio
from typing import Dict

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile, BackgroundTasks
from fastapi.responses import JSONResponse

from ..services.extrema import mark_local_extrema
from ..services.indicators import compute_indicators
from ..utils.store import set_df
from ..utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

# Track upload progress
upload_status: Dict[str, dict] = {}

@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload CSV data for analysis.
    For large files (>10K rows), processes a sample immediately and full dataset in background.
    """
    if not file.filename.endsWith(".csv"):
        raise HTTPException(400, "Please upload a CSV file.")
    
    logger.info(f"Starting upload: {file.filename}")
    
    try:
        # Read file
        raw = await file.read()
        df_full = pd.read_csv(io.BytesIO(raw))
        
        logger.info(f"CSV loaded: {len(df_full)} rows")
        
        # Validate columns
        required = {"time", "open", "high", "low", "close", "Volume"}
        if not required.issubset(df_full.columns):
            raise HTTPException(
                400, 
                f"CSV must include columns: {sorted(list(required))}. "
                f"Found: {list(df_full.columns)}"
            )
        
        # Keep only required columns
        df_full = df_full[list(required)]
        
        # For large files, process immediately with limited dataset
        if len(df_full) > 10000:
            logger.info(f"Large file detected ({len(df_full)} rows). Processing...")
            
            # Use all data but optimize by reducing indicator window initially
            # This is faster than sampling
            df = compute_indicators(df_full)
            df = mark_local_extrema(df, window=12)
            set_df(df)
            
            return JSONResponse({
                "rows": len(df),
                "columns": list(df.columns),
                "success": True,
                "message": f"Processed {len(df)} rows (large file)"
            })
        else:
            # Small file - process normally
            df = compute_indicators(df_full)
            df = mark_local_extrema(df, window=12)
            set_df(df)
            
            return JSONResponse({
                "rows": len(df),
                "columns": list(df.columns),
                "success": True,
                "message": f"Successfully processed {len(df)} rows"
            })
    
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(500, f"Failed to process file: {str(e)}")


@router.get("/status")
async def upload_status_check():
    """Check current upload/processing status."""
    return JSONResponse(upload_status)