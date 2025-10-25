"""
Live monitoring router for real-time signal generation.
Integrates Pyth Network price feeds with signal detection.
"""
import os
import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from ..services.live_monitor import LiveMonitor
from ..utils.logging import logger
from .signals import broadcast_signal

router = APIRouter()

# Global live monitor instance
live_monitor: LiveMonitor | None = None


async def signal_callback(signal_card):
    """
    Callback function triggered when a new signal is generated.
    Broadcasts the signal to all connected WebSocket clients.
    """
    signal_dict = (
        signal_card.__dict__
        if hasattr(signal_card, '__dict__')
        else signal_card
    )
    
    logger.info(
        f"New signal: {signal_dict.get('signal_id')} - "
        f"{signal_dict.get('bias')} @ {signal_dict.get('entry_price')}"
    )
    
    # Broadcast to WebSocket clients
    await broadcast_signal(signal_dict)


@router.post("/start")
async def start_live_monitor():
    """
    Start the live price monitoring and signal generation.
    Uses Pyth Network for real-time SOL/USD price feeds.
    """
    global live_monitor
    
    try:
        if live_monitor and live_monitor.running:
            return JSONResponse({
                'success': True,
                'message': 'Monitor already running'
            })
        
        # Get optional Helius API key for on-chain data
        helius_api_key = os.environ.get('HELIUS_API_KEY')
        
        # Create monitor instance with two-stage methodology
        live_monitor = LiveMonitor(
            candle_window=500,
            atr_threshold=0.6,
            vol_z_threshold=0.5,
            bb_width_threshold=0.005,
            helius_api_key=helius_api_key
        )
        
        # Register signal callback for WebSocket broadcasting
        live_monitor.register_signal_callback(signal_callback)
        
        # Start monitor in background
        asyncio.create_task(live_monitor.start())
        
        return JSONResponse({
            'success': True,
            'message': 'Live monitor started successfully',
            'details': {
                'price_feed': 'Pyth Network SOL/USD',
                'methodology': 'Two-stage (Candidate + Micro Confirmation)',
                'on_chain': 'Enabled' if helius_api_key else 'Disabled'
            }
        })
    
    except Exception as e:
        logger.error(f"Error starting live monitor: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/stop")
async def stop_live_monitor():
    """Stop the live monitoring."""
    global live_monitor
    
    try:
        if live_monitor:
            live_monitor.stop()
            logger.info("Live monitor stopped")
            return JSONResponse({
                'success': True,
                'message': 'Monitor stopped'
            })
        return JSONResponse({
            'success': False,
            'message': 'Monitor not running'
        })
    
    except Exception as e:
        logger.error(f"Error stopping monitor: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/status")
async def get_monitor_status():
    """Get current live monitor status and statistics."""
    global live_monitor
    
    if live_monitor:
        return JSONResponse({
            'running': live_monitor.running,
            'candles_count': len(live_monitor.candles),
            'active_signals_count': len(live_monitor.active_signals),
            'last_price': live_monitor.last_price,
            'uptime': 'Active'
        })
    
    return JSONResponse({
        'running': False,
        'candles_count': 0,
        'active_signals_count': 0,
        'last_price': 0.0,
        'uptime': 'Stopped'
    })


@router.get("/signals")
async def get_live_signals():
    """Get all active live signals from the monitor."""
    global live_monitor
    
    try:
        if live_monitor:
            signals = live_monitor.get_active_signals()
            return JSONResponse({'signals': signals})
        
        return JSONResponse({'signals': []})
    
    except Exception as e:
        logger.error(f"Error fetching live signals: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e
