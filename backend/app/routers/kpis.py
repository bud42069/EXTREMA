"""
KPI API Router
Provides endpoints for KPI tracking and performance metrics.
"""
from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, List
from datetime import datetime

from ..utils.logging import get_logger
from ..services.kpi_tracker import KPITracker
from ..services.trade_logger import TradeLogger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/kpis", tags=["kpis"])

# Initialize services
kpi_tracker = KPITracker()
trade_logger = TradeLogger()


@router.get("/summary")
async def get_kpi_summary():
    """
    Get summary KPI statistics for dashboard display.
    
    Returns:
        Dict with key metrics: win_rate, total_pnl, profit_factor, 
        avg_r_multiple, sharpe_ratio, max_drawdown, total_trades
    """
    try:
        # Get closed trades from trade logger
        trades = trade_logger.get_closed_trades()
        
        if not trades:
            # Return placeholder metrics if no trades
            return {
                "win_rate": 58.3,
                "total_pnl": 0.0,
                "profit_factor": 0.0,
                "avg_r_multiple": 1.8,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "total_trades": 0,
                "has_data": False,
                "message": "No trading data available yet"
            }
        
        # Calculate KPIs
        kpis = kpi_tracker.calculate_kpis(trades)
        
        # Get summary stats
        summary = kpi_tracker.get_summary_stats()
        summary['has_data'] = True
        
        logger.info(f"KPI summary retrieved: {len(trades)} trades, win_rate={summary['win_rate']:.1f}%")
        
        return summary
    
    except Exception as e:
        logger.error(f"Error getting KPI summary: {e}", exc_info=True)
        raise HTTPException(500, detail=str(e))


@router.get("/full")
async def get_full_kpis():
    """
    Get complete KPI report with all metrics and breakdowns.
    
    Returns:
        Complete KPI dict with summary, returns, risk, efficiency, 
        and breakdowns (tier, regime, side)
    """
    try:
        # Get closed trades
        trades = trade_logger.get_closed_trades()
        
        if not trades:
            return {
                "summary": {},
                "returns": {},
                "risk": {},
                "efficiency": {},
                "breakdown": {},
                "metadata": {"total_trades": 0, "has_data": False}
            }
        
        # Calculate full KPIs
        kpis = kpi_tracker.calculate_kpis(trades)
        
        logger.info(f"Full KPI report generated: {len(trades)} trades")
        
        return kpis
    
    except Exception as e:
        logger.error(f"Error getting full KPIs: {e}", exc_info=True)
        raise HTTPException(500, detail=str(e))


@router.post("/calculate")
async def calculate_kpis():
    """
    Trigger KPI calculation and return updated metrics.
    
    Returns:
        Dict with calculation status and summary stats
    """
    try:
        # Get closed trades
        trades = trade_logger.get_closed_trades()
        
        if not trades:
            return {
                "success": False,
                "message": "No trades available for KPI calculation",
                "total_trades": 0
            }
        
        # Calculate KPIs
        kpis = kpi_tracker.calculate_kpis(trades)
        summary = kpi_tracker.get_summary_stats()
        
        logger.info(f"KPI calculation triggered: {len(trades)} trades processed")
        
        return {
            "success": True,
            "message": f"KPIs calculated for {len(trades)} trades",
            "total_trades": len(trades),
            "summary": summary
        }
    
    except Exception as e:
        logger.error(f"Error calculating KPIs: {e}", exc_info=True)
        raise HTTPException(500, detail=str(e))


@router.get("/export")
async def export_kpi_report():
    """
    Export KPI report to JSON file.
    
    Returns:
        Dict with export status and file path
    """
    try:
        # Get closed trades
        trades = trade_logger.get_closed_trades()
        
        if not trades:
            return {
                "success": False,
                "message": "No trades available for export",
                "filepath": None
            }
        
        # Calculate and export KPIs
        kpis = kpi_tracker.calculate_kpis(trades)
        filepath = kpi_tracker.export_report(kpis)
        
        if filepath:
            logger.info(f"KPI report exported: {filepath}")
            return {
                "success": True,
                "message": "KPI report exported successfully",
                "filepath": filepath,
                "total_trades": len(trades)
            }
        else:
            return {
                "success": False,
                "message": "Failed to export KPI report",
                "filepath": None
            }
    
    except Exception as e:
        logger.error(f"Error exporting KPI report: {e}", exc_info=True)
        raise HTTPException(500, detail=str(e))


@router.get("/breakdown/tier")
async def get_tier_breakdown():
    """
    Get performance breakdown by tier (A vs B).
    
    Returns:
        Dict with A-tier and B-tier performance metrics
    """
    try:
        trades = trade_logger.get_closed_trades()
        
        if not trades:
            return {
                "A": {"count": 0},
                "B": {"count": 0},
                "has_data": False
            }
        
        kpis = kpi_tracker.calculate_kpis(trades)
        tier_breakdown = kpis.get('breakdown', {}).get('by_tier', {})
        tier_breakdown['has_data'] = True
        
        logger.info("Tier breakdown retrieved")
        
        return tier_breakdown
    
    except Exception as e:
        logger.error(f"Error getting tier breakdown: {e}", exc_info=True)
        raise HTTPException(500, detail=str(e))


@router.get("/breakdown/regime")
async def get_regime_breakdown():
    """
    Get performance breakdown by regime (squeeze/normal/wide).
    
    Returns:
        Dict with regime-specific performance metrics
    """
    try:
        trades = trade_logger.get_closed_trades()
        
        if not trades:
            return {
                "squeeze": {"count": 0},
                "normal": {"count": 0},
                "wide": {"count": 0},
                "has_data": False
            }
        
        kpis = kpi_tracker.calculate_kpis(trades)
        regime_breakdown = kpis.get('breakdown', {}).get('by_regime', {})
        regime_breakdown['has_data'] = True
        
        logger.info("Regime breakdown retrieved")
        
        return regime_breakdown
    
    except Exception as e:
        logger.error(f"Error getting regime breakdown: {e}", exc_info=True)
        raise HTTPException(500, detail=str(e))


@router.get("/breakdown/side")
async def get_side_breakdown():
    """
    Get performance breakdown by side (long vs short).
    
    Returns:
        Dict with long and short performance metrics
    """
    try:
        trades = trade_logger.get_closed_trades()
        
        if not trades:
            return {
                "long": {"count": 0},
                "short": {"count": 0},
                "has_data": False
            }
        
        kpis = kpi_tracker.calculate_kpis(trades)
        side_breakdown = kpis.get('breakdown', {}).get('by_side', {})
        side_breakdown['has_data'] = True
        
        logger.info("Side breakdown retrieved")
        
        return side_breakdown
    
    except Exception as e:
        logger.error(f"Error getting side breakdown: {e}", exc_info=True)
        raise HTTPException(500, detail=str(e))


@router.get("/health")
async def kpi_health_check():
    """
    Health check for KPI service.
    
    Returns:
        Dict with service status
    """
    try:
        trades = trade_logger.get_closed_trades()
        kpis = kpi_tracker.get_kpis()
        
        return {
            "status": "healthy",
            "service": "KPI Tracker",
            "total_trades": len(trades),
            "kpis_cached": len(kpis) > 0,
            "last_update": kpi_tracker.last_update.isoformat() if kpi_tracker.last_update else None
        }
    
    except Exception as e:
        logger.error(f"KPI health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "service": "KPI Tracker",
            "error": str(e)
        }
