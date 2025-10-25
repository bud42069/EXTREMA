"""
MTF (Multi-Timeframe) API router.
Provides endpoints for MTF state machine control and status.
"""
from fastapi import APIRouter, HTTPException
from typing import Optional

from ..services.mtf_state_machine import mtf_state_machine, MTFState
from ..workers.binance_klines import BinanceKlineWorker
from ..services.binance_rest import multi_source_rest_client
from ..utils.logging import get_logger
from ..utils.mtf_store import get_store_stats, get_klines
from ..services.mtf_features import extract_mtf_features
from ..services.mtf_confluence import confluence_engine
from ..utils.micro_store import get_snapshot
import pandas as pd

router = APIRouter()
logger = get_logger(__name__)

# Global worker instances
kline_worker: Optional[BinanceKlineWorker] = None
higher_tf_started: bool = False


@router.post("/start")
async def start_mtf(symbol: str = "SOLUSDT"):
    """
    Start the MTF system (kline worker + state machine + higher TFs).
    
    Initiates:
    - 1-second kline WebSocket stream from Binance
    - Automatic resampling to 5s/15s/30s/1m
    - Higher timeframe data fetching (15m/1h/4h/1D)
    - MTF feature extraction
    - State machine for signal generation
    """
    global kline_worker, higher_tf_started
    
    try:
        if kline_worker and kline_worker.running:
            return {
                "success": False,
                "message": "MTF system already running"
            }
        
        # Start kline worker (1s stream)
        kline_worker = BinanceKlineWorker(symbol=symbol, interval="1s")
        
        # Register callbacks for resampled data
        async def on_1m_kline(df):
            logger.debug(f"1m kline received: {len(df)} bars")
        
        kline_worker.register_callback("1m", on_1m_kline)
        
        # Start worker in background
        import asyncio
        asyncio.create_task(kline_worker.start())
        
        # Start higher timeframe data fetching
        if not higher_tf_started:
            asyncio.create_task(multi_source_rest_client.start_all(symbol))
            higher_tf_started = True
        
        return {
            "success": True,
            "message": f"MTF system started for {symbol}",
            "symbol": symbol,
            "state": mtf_state_machine.state.value,
            "higher_tf_started": higher_tf_started
        }
    
    except Exception as e:
        logger.error(f"Error starting MTF system: {e}")
        raise HTTPException(500, detail=str(e))


@router.post("/stop")
async def stop_mtf():
    """
    Stop the MTF system.
    """
    global kline_worker, higher_tf_started
    
    try:
        if not kline_worker or not kline_worker.running:
            return {
                "success": False,
                "message": "MTF system not running"
            }
        
        # Stop kline worker
        kline_worker.stop()
        kline_worker = None
        
        # Stop higher TF updates
        if higher_tf_started:
            await multi_source_rest_client.stop_all()
            higher_tf_started = False
        
        # Reset state machine
        mtf_state_machine.state = MTFState.SCAN
        mtf_state_machine.candidate = None
        
        return {
            "success": True,
            "message": "MTF system stopped"
        }
    
    except Exception as e:
        logger.error(f"Error stopping MTF system: {e}")
        raise HTTPException(500, detail=str(e))


@router.get("/status")
async def get_mtf_status():
    """
    Get MTF system status including state machine and data stores.
    """
    try:
        # State machine status
        sm_status = mtf_state_machine.get_status()
        
        # Kline worker status
        worker_status = None
        if kline_worker:
            worker_status = kline_worker.get_stats()
        
        # Store statistics
        store_stats = get_store_stats()
        
        return {
            "running": kline_worker is not None and kline_worker.running,
            "state_machine": sm_status,
            "worker": worker_status,
            "stores": store_stats
        }
    
    except Exception as e:
        logger.error(f"Error getting MTF status: {e}")
        raise HTTPException(500, detail=str(e))


@router.get("/features/{timeframe}")
async def get_mtf_features(timeframe: str, limit: int = 100):
    """
    Get extracted features for a specific timeframe.
    
    Args:
        timeframe: Timeframe (1s, 5s, 15s, 30s, 1m, 5m, 15m, 1h, 4h, 1d)
        limit: Number of klines to use for feature extraction
    """
    try:
        # Get klines
        klines = get_klines(timeframe, limit=limit)
        
        if not klines or len(klines) < 50:
            return {
                "timeframe": timeframe,
                "available": False,
                "message": "Insufficient data",
                "klines_count": len(klines) if klines else 0
            }
        
        # Convert to DataFrame
        df = pd.DataFrame(klines)
        df['time'] = pd.to_datetime(df['timestamp'], unit='s')
        df.set_index('time', inplace=True)
        
        # Extract features
        features = extract_mtf_features(df, timeframe)
        
        return {
            "timeframe": timeframe,
            "available": True,
            "features": features,
            "klines_count": len(klines)
        }
    
    except Exception as e:
        logger.error(f"Error getting MTF features for {timeframe}: {e}")
        raise HTTPException(500, detail=str(e))


@router.get("/confluence")
async def get_mtf_confluence():
    """
    Get current MTF confluence evaluation.
    Combines all timeframes to produce context and micro confluence scores.
    """
    try:
        # Extract features from all available timeframes
        features_dict = {}
        
        for tf in ['1s', '5s', '1m', '5m', '15m', '1h', '4h', '1d']:
            klines = get_klines(tf, limit=100)
            if klines and len(klines) >= 50:
                df = pd.DataFrame(klines)
                df['time'] = pd.to_datetime(df['timestamp'], unit='s')
                df.set_index('time', inplace=True)
                features_dict[tf] = extract_mtf_features(df, tf)
        
        # Get microstructure snapshot
        micro_snapshot = get_snapshot()
        
        # Evaluate confluence
        confluence_result = confluence_engine.evaluate(
            features_1s=features_dict.get('1s'),
            features_5s=features_dict.get('5s'),
            features_1m=features_dict.get('1m'),
            features_5m=features_dict.get('5m'),
            features_15m=features_dict.get('15m'),
            features_1h=features_dict.get('1h'),
            features_4h=features_dict.get('4h'),
            features_1d=features_dict.get('1d'),
            micro_snapshot=micro_snapshot
        )
        
        return {
            "available": True,
            "confluence": confluence_result,
            "features_available": list(features_dict.keys())
        }
    
    except Exception as e:
        logger.error(f"Error computing MTF confluence: {e}")
        raise HTTPException(500, detail=str(e))


@router.post("/run-cycle")
async def run_mtf_cycle():
    """
    Manually trigger one MTF state machine cycle.
    Useful for testing and debugging.
    """
    try:
        # Get 5m data
        klines_5m = get_klines("5m", limit=200)
        
        if not klines_5m or len(klines_5m) < 50:
            return {
                "success": False,
                "message": "Insufficient 5m data",
                "klines_count": len(klines_5m) if klines_5m else 0
            }
        
        # Convert to DataFrame
        df_5m = pd.DataFrame(klines_5m)
        df_5m['time'] = pd.to_datetime(df_5m['timestamp'], unit='s')
        df_5m.set_index('time', inplace=True)
        
        # Run state machine
        signal = await mtf_state_machine.run(df_5m)
        
        return {
            "success": True,
            "state": mtf_state_machine.state.value,
            "signal": signal,
            "status": mtf_state_machine.get_status()
        }
    
    except Exception as e:
        logger.error(f"Error running MTF cycle: {e}")
        raise HTTPException(500, detail=str(e))
