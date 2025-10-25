"""
KPI Tracker (Phase 4)
Implements comprehensive KPI tracking and performance metrics.
Part of the SOLUSDT Swing-Capture Playbook v1.0
"""
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
import json
from pathlib import Path
from ..utils.logging import get_logger

logger = get_logger(__name__)


class KPITracker:
    """
    Tracks and calculates trading performance KPIs.
    
    Metrics:
    - Win rate, profit factor, Sharpe ratio
    - Average R-multiple, expectancy
    - Max drawdown, recovery factor
    - Trade frequency, average hold time
    - Tier-based performance (A vs B)
    - Regime-based performance (squeeze/normal/wide)
    """
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize KPI tracker.
        
        Args:
            output_dir: Directory for KPI reports (default: ./logs/kpis/)
        """
        if output_dir is None:
            output_dir = os.path.join(
                os.path.dirname(__file__),
                "../../logs/kpis"
            )
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # KPI cache
        self.kpis: Dict = {}
        self.last_update: Optional[datetime] = None
        
        logger.info(f"KPITracker initialized: output_dir={self.output_dir}")
    
    def calculate_kpis(self, trades: List[Dict]) -> Dict:
        """
        Calculate comprehensive KPIs from trade list.
        
        Args:
            trades: List of closed trades
        
        Returns:
            Dict with all KPIs
        """
        if not trades:
            logger.warning("No trades to calculate KPIs")
            return self._empty_kpis()
        
        # Filter for closed trades only
        closed_trades = [
            t for t in trades
            if t.get('status') == 'closed' and
            t.get('performance', {}).get('realized_pnl_usd') is not None
        ]
        
        if not closed_trades:
            logger.warning("No closed trades with P&L data")
            return self._empty_kpis()
        
        kpis = {
            'summary': self._calculate_summary_kpis(closed_trades),
            'returns': self._calculate_return_kpis(closed_trades),
            'risk': self._calculate_risk_kpis(closed_trades),
            'efficiency': self._calculate_efficiency_kpis(closed_trades),
            'breakdown': {
                'by_tier': self._calculate_tier_breakdown(closed_trades),
                'by_regime': self._calculate_regime_breakdown(closed_trades),
                'by_side': self._calculate_side_breakdown(closed_trades)
            },
            'metadata': {
                'total_trades': len(closed_trades),
                'calculated_at': datetime.now(timezone.utc).isoformat(),
                'date_range': {
                    'start': min(t['created_at'] for t in closed_trades),
                    'end': max(t['exit']['exit_at'] for t in closed_trades)
                }
            }
        }
        
        self.kpis = kpis
        self.last_update = datetime.now(timezone.utc)
        
        logger.info(
            f"KPIs calculated: {len(closed_trades)} trades, "
            f"win_rate={kpis['summary']['win_rate']:.1f}%, "
            f"profit_factor={kpis['returns']['profit_factor']:.2f}"
        )
        
        return kpis
    
    def _empty_kpis(self) -> Dict:
        """Return empty KPI structure."""
        return {
            'summary': {},
            'returns': {},
            'risk': {},
            'efficiency': {},
            'breakdown': {'by_tier': {}, 'by_regime': {}, 'by_side': {}},
            'metadata': {'total_trades': 0}
        }
    
    def _calculate_summary_kpis(self, trades: List[Dict]) -> Dict:
        """Calculate summary KPIs."""
        wins = [t for t in trades if t['performance']['win']]
        losses = [t for t in trades if not t['performance']['win']]
        
        win_rate = len(wins) / len(trades) * 100 if trades else 0.0
        
        total_pnl = sum(t['performance']['realized_pnl_usd'] for t in trades)
        avg_pnl = total_pnl / len(trades) if trades else 0.0
        
        avg_win = (
            sum(t['performance']['realized_pnl_usd'] for t in wins) / len(wins)
            if wins else 0.0
        )
        avg_loss = (
            sum(t['performance']['realized_pnl_usd'] for t in losses) / len(losses)
            if losses else 0.0
        )
        
        return {
            'total_trades': len(trades),
            'winning_trades': len(wins),
            'losing_trades': len(losses),
            'win_rate': win_rate,
            'total_pnl_usd': total_pnl,
            'avg_pnl_usd': avg_pnl,
            'avg_win_usd': avg_win,
            'avg_loss_usd': avg_loss
        }
    
    def _calculate_return_kpis(self, trades: List[Dict]) -> Dict:
        """Calculate return-based KPIs."""
        wins = [t for t in trades if t['performance']['win']]
        losses = [t for t in trades if not t['performance']['win']]
        
        # Profit factor
        gross_profit = sum(t['performance']['realized_pnl_usd'] for t in wins)
        gross_loss = abs(sum(t['performance']['realized_pnl_usd'] for t in losses))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # R-multiple stats
        r_multiples = [t['performance']['r_multiple'] for t in trades]
        avg_r = np.mean(r_multiples) if r_multiples else 0.0
        median_r = np.median(r_multiples) if r_multiples else 0.0
        
        # Expectancy: (Win% × Avg Win) - (Loss% × Avg Loss)
        win_rate = len(wins) / len(trades) if trades else 0.0
        loss_rate = 1.0 - win_rate
        avg_win = np.mean([t['performance']['realized_pnl_usd'] for t in wins]) if wins else 0.0
        avg_loss = abs(np.mean([t['performance']['realized_pnl_usd'] for t in losses])) if losses else 0.0
        expectancy = (win_rate * avg_win) - (loss_rate * avg_loss)
        
        # Best and worst trades
        pnls = [t['performance']['realized_pnl_usd'] for t in trades]
        best_trade = max(pnls) if pnls else 0.0
        worst_trade = min(pnls) if pnls else 0.0
        
        return {
            'profit_factor': profit_factor,
            'avg_r_multiple': avg_r,
            'median_r_multiple': median_r,
            'expectancy_usd': expectancy,
            'best_trade_usd': best_trade,
            'worst_trade_usd': worst_trade,
            'gross_profit': gross_profit,
            'gross_loss': gross_loss
        }
    
    def _calculate_risk_kpis(self, trades: List[Dict]) -> Dict:
        """Calculate risk-adjusted KPIs."""
        # Running P&L for drawdown calculation
        pnls = [t['performance']['realized_pnl_usd'] for t in trades]
        cumulative_pnl = np.cumsum(pnls)
        
        # Max drawdown
        peak = np.maximum.accumulate(cumulative_pnl)
        drawdown = peak - cumulative_pnl
        max_drawdown = np.max(drawdown) if len(drawdown) > 0 else 0.0
        max_drawdown_pct = (max_drawdown / peak[np.argmax(drawdown)] * 100
                            if peak[np.argmax(drawdown)] > 0 else 0.0)
        
        # Sharpe ratio (assuming daily returns)
        if len(pnls) > 1:
            returns = np.array(pnls)
            sharpe = (np.mean(returns) / np.std(returns) * np.sqrt(252)
                     if np.std(returns) > 0 else 0.0)
        else:
            sharpe = 0.0
        
        # Recovery factor: Total P&L / Max Drawdown
        total_pnl = sum(pnls)
        recovery_factor = total_pnl / max_drawdown if max_drawdown > 0 else float('inf')
        
        # Consecutive wins/losses
        consecutive_wins = self._max_consecutive(trades, win=True)
        consecutive_losses = self._max_consecutive(trades, win=False)
        
        return {
            'max_drawdown_usd': max_drawdown,
            'max_drawdown_pct': max_drawdown_pct,
            'sharpe_ratio': sharpe,
            'recovery_factor': recovery_factor,
            'max_consecutive_wins': consecutive_wins,
            'max_consecutive_losses': consecutive_losses
        }
    
    def _calculate_efficiency_kpis(self, trades: List[Dict]) -> Dict:
        """Calculate efficiency KPIs."""
        # Average hold time
        hold_times = [t['exit']['hold_duration_hours'] for t in trades]
        avg_hold = np.mean(hold_times) if hold_times else 0.0
        median_hold = np.median(hold_times) if hold_times else 0.0
        
        # TP hit rates
        tp1_hits = sum(1 for t in trades if t['tp_sl']['tp1_hit'])
        tp2_hits = sum(1 for t in trades if t['tp_sl']['tp2_hit'])
        tp3_hits = sum(1 for t in trades if t['tp_sl']['tp3_hit'])
        
        total = len(trades)
        tp1_rate = tp1_hits / total * 100 if total > 0 else 0.0
        tp2_rate = tp2_hits / total * 100 if total > 0 else 0.0
        tp3_rate = tp3_hits / total * 100 if total > 0 else 0.0
        
        # Exit reason breakdown
        exit_reasons = {}
        for trade in trades:
            reason = trade['exit']['exit_reason']
            exit_reasons[reason] = exit_reasons.get(reason, 0) + 1
        
        # Time stop usage
        time_stops = sum(1 for t in trades if t['exit']['time_stop_triggered'])
        time_stop_rate = time_stops / total * 100 if total > 0 else 0.0
        
        # Early reduce usage
        early_reduces = sum(1 for t in trades if t['exit']['early_reduce_triggered'])
        early_reduce_rate = early_reduces / total * 100 if total > 0 else 0.0
        
        return {
            'avg_hold_hours': avg_hold,
            'median_hold_hours': median_hold,
            'tp1_hit_rate': tp1_rate,
            'tp2_hit_rate': tp2_rate,
            'tp3_hit_rate': tp3_rate,
            'time_stop_rate': time_stop_rate,
            'early_reduce_rate': early_reduce_rate,
            'exit_reasons': exit_reasons
        }
    
    def _calculate_tier_breakdown(self, trades: List[Dict]) -> Dict:
        """Calculate performance breakdown by tier."""
        tiers = {}
        
        for tier in ['A', 'B']:
            tier_trades = [t for t in trades if t['context']['tier'] == tier]
            
            if tier_trades:
                wins = [t for t in tier_trades if t['performance']['win']]
                win_rate = len(wins) / len(tier_trades) * 100
                
                total_pnl = sum(t['performance']['realized_pnl_usd'] for t in tier_trades)
                avg_r = np.mean([t['performance']['r_multiple'] for t in tier_trades])
                
                tiers[tier] = {
                    'count': len(tier_trades),
                    'win_rate': win_rate,
                    'total_pnl_usd': total_pnl,
                    'avg_r_multiple': avg_r
                }
        
        return tiers
    
    def _calculate_regime_breakdown(self, trades: List[Dict]) -> Dict:
        """Calculate performance breakdown by regime."""
        regimes = {}
        
        for regime in ['squeeze', 'normal', 'wide']:
            regime_trades = [t for t in trades if t['context']['regime'] == regime]
            
            if regime_trades:
                wins = [t for t in regime_trades if t['performance']['win']]
                win_rate = len(wins) / len(regime_trades) * 100
                
                total_pnl = sum(t['performance']['realized_pnl_usd'] for t in regime_trades)
                avg_r = np.mean([t['performance']['r_multiple'] for t in regime_trades])
                avg_hold = np.mean([t['exit']['hold_duration_hours'] for t in regime_trades])
                
                regimes[regime] = {
                    'count': len(regime_trades),
                    'win_rate': win_rate,
                    'total_pnl_usd': total_pnl,
                    'avg_r_multiple': avg_r,
                    'avg_hold_hours': avg_hold
                }
        
        return regimes
    
    def _calculate_side_breakdown(self, trades: List[Dict]) -> Dict:
        """Calculate performance breakdown by side."""
        sides = {}
        
        for side in ['long', 'short']:
            side_trades = [t for t in trades if t['signal']['side'] == side]
            
            if side_trades:
                wins = [t for t in side_trades if t['performance']['win']]
                win_rate = len(wins) / len(side_trades) * 100
                
                total_pnl = sum(t['performance']['realized_pnl_usd'] for t in side_trades)
                
                sides[side] = {
                    'count': len(side_trades),
                    'win_rate': win_rate,
                    'total_pnl_usd': total_pnl
                }
        
        return sides
    
    def _max_consecutive(self, trades: List[Dict], win: bool) -> int:
        """Calculate max consecutive wins or losses."""
        max_count = 0
        current_count = 0
        
        for trade in trades:
            if trade['performance']['win'] == win:
                current_count += 1
                max_count = max(max_count, current_count)
            else:
                current_count = 0
        
        return max_count
    
    def export_report(self, kpis: Optional[Dict] = None, filename: Optional[str] = None) -> str:
        """
        Export KPI report to JSON.
        
        Args:
            kpis: KPIs to export (uses cached if None)
            filename: Output filename
        
        Returns:
            Path to report file
        """
        if kpis is None:
            kpis = self.kpis
        
        if not kpis:
            logger.warning("No KPIs to export")
            return ""
        
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"kpi_report_{timestamp}.json"
        
        filepath = self.output_dir / filename
        
        try:
            with open(filepath, 'w') as f:
                json.dump(kpis, f, indent=2)
            
            logger.info(f"KPI report exported: {filepath}")
            return str(filepath)
        
        except Exception as e:
            logger.error(f"Error exporting KPI report: {e}")
            return ""
    
    def get_kpis(self) -> Dict:
        """Get cached KPIs."""
        return self.kpis.copy()
    
    def get_summary_stats(self) -> Dict:
        """Get summary statistics for dashboard."""
        if not self.kpis:
            return {}
        
        return {
            'win_rate': self.kpis['summary'].get('win_rate', 0.0),
            'total_pnl': self.kpis['summary'].get('total_pnl_usd', 0.0),
            'profit_factor': self.kpis['returns'].get('profit_factor', 0.0),
            'avg_r_multiple': self.kpis['returns'].get('avg_r_multiple', 0.0),
            'sharpe_ratio': self.kpis['risk'].get('sharpe_ratio', 0.0),
            'max_drawdown': self.kpis['risk'].get('max_drawdown_usd', 0.0),
            'total_trades': self.kpis['metadata'].get('total_trades', 0)
        }


# Import os for path operations
import os
