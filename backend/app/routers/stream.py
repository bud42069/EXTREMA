"""
Microstructure stream control endpoints.
Start/stop Binance orderbook+trades worker and retrieve snapshots.
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..workers.mexc_stream import start_mexc_worker, stop_mexc_worker
from ..utils.micro_store import get_snapshot
from ..services.microstructure import get_micro_summary
from ..utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/start")
async def start_stream(symbol: str = "SOLUSDT"):
    """
    Start the Binance microstructure stream worker.
    
    Connects to Binance WebSocket for:
    - Depth (L2, top 20 levels)
    - Trades (for CVD calculation)
    
    Args:
        symbol: Trading pair (default: SOLUSDT)
    
    Returns:
        Success status and message
    """
    try:
        await start_mexc_worker(symbol)
        return JSONResponse({
            "success": True,
            "message": f"Binance stream started for {symbol}",
            "symbol": symbol
        })
    except Exception as e:
        logger.error(f"Error starting MEXC stream: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@router.post("/stop")
async def stop_stream():
    """
    Stop the MEXC microstructure stream worker.
    
    Returns:
        Success status and message
    """
    try:
        stop_mexc_worker()
        return JSONResponse({
            "success": True,
            "message": "MEXC stream stopped"
        })
    except Exception as e:
        logger.error(f"Error stopping MEXC stream: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@router.get("/snapshot")
async def get_stream_snapshot():
    """
    Get the current microstructure snapshot.
    
    Returns:
        Dict with spread, depth, imbalance, CVD metrics.
        Returns empty dict if stream not running or no data available.
    """
    snap = get_snapshot()
    summary = get_micro_summary(snap)
    
    return JSONResponse(summary)


@router.get("/health")
async def stream_health():
    """
    Check microstructure stream health.
    
    Returns:
        Status of stream: running, data age, metrics availability
    """
    snap = get_snapshot()
    
    if snap is None:
        return JSONResponse({
            "running": False,
            "available": False,
            "message": "No microstructure data available"
        })
    
    import time
    age_seconds = time.time() - snap.ts
    
    return JSONResponse({
        "running": True,
        "available": snap.ok,
        "age_seconds": round(age_seconds, 2),
        "spread_bps": round(snap.spread_bps, 2),
        "message": "Stream active" if age_seconds < 10 else "Stream stale"
    })
