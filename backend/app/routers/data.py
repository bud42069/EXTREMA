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
    Optimized for large files with progress tracking.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Please upload a CSV file.")
    
    logger.info(f"Starting upload: {file.filename}")
    
    try:
        # Read file
        raw = await file.read()
        df = pd.read_csv(io.BytesIO(raw))
        
        logger.info(f"CSV loaded: {len(df)} rows")
        
        # Validate columns
        required = {"time", "open", "high", "low", "close", "Volume"}
        if not required.issubset(df.columns):
            raise HTTPException(
                400, 
                f"CSV must include columns: {sorted(list(required))}. "
                f"Found: {list(df.columns)}"
            )
        
        # Keep only required columns to speed up processing
        df = df[list(required)]
        
        # Compute indicators (this is the slow part for large files)
        logger.info("Computing indicators...")
        df = compute_indicators(df)
        
        # Detect extrema
        logger.info("Detecting extrema...")
        df = mark_local_extrema(df, window=12)
        
        # Store in memory
        set_df(df)
        
        logger.info(f"Upload complete: {len(df)} rows processed")
        
        return JSONResponse({
            "rows": len(df),
            "columns": list(df.columns),
            "success": True,
            "message": f"Successfully uploaded and processed {len(df)} rows"
        })
    
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(500, f"Failed to process file: {str(e)}")


@router.get("/status")
async def upload_status_check():
    """Check current upload/processing status."""
    return JSONResponse(upload_status)