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
    Start the MTF system (kline worker + state machine + higher TFs + Helius on-chain).
    
    Initiates:
    - 1-second kline WebSocket stream from Binance
    - Automatic resampling to 5s/15s/30s/1m
    - Higher timeframe data fetching (15m/1h/4h/1D)
    - MTF feature extraction
    - State machine for signal generation
    - Helius on-chain monitoring (if API key configured)
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
        
        # Start Helius on-chain monitoring
        await confluence_engine.start_onchain_monitoring()
        
        return {
            "success": True,
            "message": f"MTF system started for {symbol}",
            "symbol": symbol,
            "state": mtf_state_machine.state.value,
            "higher_tf_started": higher_tf_started,
            "onchain_enabled": confluence_engine.onchain_monitor is not None
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
async def get_mtf_confluence(side: Optional[str] = None, tier: str = 'B'):
    """
    Get current MTF confluence evaluation with Phase 1 & Phase 2 enhancements.
    Combines all timeframes to produce context and micro confluence scores.
    
    Phase 1 Features:
    - 1m impulse detection (RSI-12, BOS, volume)
    - 1s/5s tape filters (CVD z-score, OBI, VWAP proximity)
    - Comprehensive veto system
    
    Phase 2 Features:
    - Regime detection (Squeeze/Normal/Wide) from 5m BBWidth
    - Context gates (15m/1h EMA alignment, pivot structure, oscillator)
    - Macro gates (4h/1D alignment for A/B tier determination)
    - Enhanced confluence bottleneck with tier determination
    
    Args:
        side: Trade direction ('long' or 'short', optional for general evaluation)
        tier: Tier for volume thresholds ('A' or 'B', default 'B')
    """
    try:
        # Extract features from all available timeframes
        features_dict = {}
        df_dict = {}  # Store DataFrames for Phase 1 & Phase 2 analysis
        
        for tf in ['1s', '5s', '1m', '5m', '15m', '1h', '4h', '1d']:
            klines = get_klines(tf, limit=100)
            if klines and len(klines) >= 50:
                df = pd.DataFrame(klines)
                df['time'] = pd.to_datetime(df['timestamp'], unit='s')
                df.set_index('time', inplace=True)
                
                # Store DataFrame for Phase 1 & Phase 2 services
                df_dict[tf] = df
                
                # Extract features
                features_dict[tf] = extract_mtf_features(df, tf)
        
        # Get microstructure snapshot
        micro_snapshot = get_snapshot()
        
        # Prepare DataFrames for Phase 1 analysis
        df_1m = df_dict.get('1m')
        df_tape = df_dict.get('5s') or df_dict.get('1s')  # Prefer 5s, fallback to 1s
        
        # Prepare DataFrames for Phase 2 analysis
        df_5m = df_dict.get('5m')
        df_15m = df_dict.get('15m')
        df_1h = df_dict.get('1h')
        df_4h = df_dict.get('4h')
        df_1d = df_dict.get('1d')
        
        # Compute 5m ATR for VWAP proximity check
        atr_5m = None
        if df_5m is not None:
            if 'atr' in df_5m.columns and len(df_5m) > 0:
                atr_5m = df_5m['atr'].iloc[-1]
            elif len(df_5m) >= 14:
                # Compute ATR on the fly
                high_low = df_5m['high'] - df_5m['low']
                high_close = (df_5m['high'] - df_5m['close'].shift()).abs()
                low_close = (df_5m['low'] - df_5m['close'].shift()).abs()
                tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
                atr_5m = tr.rolling(window=14).mean().iloc[-1]
        
        # Evaluate confluence with Phase 1 & Phase 2 integration
        confluence_result = confluence_engine.evaluate(
            features_1s=features_dict.get('1s'),
            features_5s=features_dict.get('5s'),
            features_1m=features_dict.get('1m'),
            features_5m=features_dict.get('5m'),
            features_15m=features_dict.get('15m'),
            features_1h=features_dict.get('1h'),
            features_4h=features_dict.get('4h'),
            features_1d=features_dict.get('1d'),
            micro_snapshot=micro_snapshot,
            df_1m=df_1m,
            df_tape=df_tape,
            df_5m=df_5m,
            df_15m=df_15m,
            df_1h=df_1h,
            df_4h=df_4h,
            df_1d=df_1d,
            side=side,
            tier=tier,
            atr_5m=atr_5m
        )
        
        return {
            "available": True,
            "confluence": confluence_result,
            "features_available": list(features_dict.keys()),
            "phase1_enabled": {
                "impulse_1m": df_1m is not None and side is not None,
                "tape_filters": df_tape is not None and side is not None and atr_5m is not None,
                "veto_system": df_tape is not None and side is not None
            },
            "phase2_enabled": confluence_result.get('phase2_enabled', {}),
            "parameters": {
                "side": side,
                "tier": tier,
                "atr_5m": atr_5m
            }
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
