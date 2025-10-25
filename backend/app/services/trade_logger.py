"""
Trade Logger (Phase 4)
Implements comprehensive trade logging for the trading system.
Part of the SOLUSDT Swing-Capture Playbook v1.0
"""
import json
import csv
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from pathlib import Path
from enum import Enum
from ..utils.logging import get_logger

logger = get_logger(__name__)


class TradeStatus(Enum):
    """Trade status enum."""
    SIGNAL_DETECTED = "signal_detected"
    RISK_CHECK = "risk_check"
    ENTRY_PENDING = "entry_pending"
    ENTRY_FILLED = "entry_filled"
    POSITION_OPEN = "position_open"
    TP1_HIT = "tp1_hit"
    TP2_HIT = "tp2_hit"
    TP3_HIT = "tp3_hit"
    TRAILING_ACTIVE = "trailing_active"
    STOP_HIT = "stop_hit"
    TIME_STOP = "time_stop"
    EARLY_REDUCE = "early_reduce"
    CLOSED = "closed"


class TradeLogger:
    """
    Comprehensive trade logging system.
    
    Features:
    - Trade lifecycle tracking (signal → entry → TP hits → exit)
    - Execution details (fills, slippage, fees)
    - Decision logging (rationale, confluence scores)
    - Export to CSV/JSON
    - MongoDB integration (optional)
    """
    
    def __init__(
        self,
        log_dir: Optional[str] = None,
        enable_db: bool = False,
        db_collection: Optional[Any] = None
    ):
        """
        Initialize trade logger.
        
        Args:
            log_dir: Directory for log files (default: ./logs/trades/)
            enable_db: Whether to log to database
            db_collection: MongoDB collection for trade logs
        """
        if log_dir is None:
            log_dir = os.path.join(
                os.path.dirname(__file__),
                "../../logs/trades"
            )
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.enable_db = enable_db
        self.db_collection = db_collection
        
        # In-memory trade log
        self.trades: Dict[str, Dict] = {}
        self.trade_events: Dict[str, List[Dict]] = {}
        
        logger.info(f"TradeLogger initialized: log_dir={self.log_dir}, db={enable_db}")
    
    def create_trade(
        self,
        trade_id: str,
        signal: Dict,
        confluence: Dict,
        regime: str,
        tier: str
    ) -> Dict:
        """
        Create a new trade log entry.
        
        Args:
            trade_id: Unique trade ID
            signal: Signal details
            confluence: Confluence scores
            regime: Market regime
            tier: Trade tier (A/B)
        
        Returns:
            Trade log entry
        """
        trade = {
            'trade_id': trade_id,
            'status': TradeStatus.SIGNAL_DETECTED.value,
            'created_at': datetime.now(timezone.utc).isoformat(),
            
            # Signal details
            'signal': {
                'side': signal.get('side'),
                'entry_price': signal.get('entry'),
                'stop_loss': signal.get('sl'),
                'tp1': signal.get('tp1'),
                'tp2': signal.get('tp2'),
                'tp3': signal.get('tp3'),
                'extremum_index': signal.get('extremum_index'),
                'confirm_index': signal.get('confirm_index')
            },
            
            # Context
            'context': {
                'regime': regime,
                'tier': tier,
                'confluence': {
                    'context_score': confluence.get('context', {}).get('total'),
                    'micro_score': confluence.get('micro', {}).get('total'),
                    'final_score': confluence.get('final', {}).get('final_score'),
                    'bottleneck': confluence.get('final', {}).get('bottleneck')
                }
            },
            
            # Execution (to be filled)
            'execution': {
                'entry_filled_at': None,
                'entry_fill_price': None,
                'entry_slippage_pct': None,
                'quantity': None,
                'position_size_usd': None,
                'leverage': None
            },
            
            # Risk metrics
            'risk': {
                'liq_price': None,
                'liq_gap_multiplier': None,
                'risk_amount_usd': None,
                'risk_pct': None
            },
            
            # TP/SL tracking
            'tp_sl': {
                'tp1_hit': False,
                'tp2_hit': False,
                'tp3_hit': False,
                'tp1_hit_at': None,
                'tp2_hit_at': None,
                'tp3_hit_at': None,
                'trailing_activated': False,
                'trailing_activated_at': None,
                'highest_price': None,
                'lowest_price': None
            },
            
            # Exit details
            'exit': {
                'exit_reason': None,
                'exit_price': None,
                'exit_at': None,
                'hold_duration_hours': None,
                'time_stop_triggered': False,
                'early_reduce_triggered': False
            },
            
            # Performance
            'performance': {
                'realized_pnl_usd': None,
                'realized_pnl_pct': None,
                'r_multiple': None,
                'win': None,
                'fees_usd': None
            }
        }
        
        # Store trade
        self.trades[trade_id] = trade
        self.trade_events[trade_id] = []
        
        # Log event
        self._log_event(trade_id, TradeStatus.SIGNAL_DETECTED.value, {
            'signal': signal,
            'confluence': confluence,
            'regime': regime,
            'tier': tier
        })
        
        logger.info(
            f"Trade created: {trade_id}, {signal.get('side')}, "
            f"tier={tier}, regime={regime}"
        )
        
        return trade
    
    def log_risk_check(
        self,
        trade_id: str,
        risk_result: Dict,
        passed: bool
    ):
        """
        Log risk check results.
        
        Args:
            trade_id: Trade ID
            risk_result: Risk check result
            passed: Whether risk check passed
        """
        if trade_id not in self.trades:
            logger.warning(f"Trade {trade_id} not found for risk check logging")
            return
        
        trade = self.trades[trade_id]
        trade['status'] = TradeStatus.RISK_CHECK.value
        
        # Update risk metrics
        if 'liq_gap' in risk_result:
            trade['risk']['liq_price'] = risk_result['liq_gap'].get('liq_price')
            trade['risk']['liq_gap_multiplier'] = risk_result['liq_gap'].get('liq_gap_multiplier')
        
        if 'position_sizing' in risk_result:
            ps = risk_result['position_sizing']
            trade['risk']['risk_amount_usd'] = ps.get('risk_usd')
            trade['risk']['risk_pct'] = ps.get('risk_distance_pct')
        
        # Log event
        self._log_event(trade_id, TradeStatus.RISK_CHECK.value, {
            'passed': passed,
            'risk_result': risk_result
        })
        
        logger.info(f"Risk check logged: {trade_id}, passed={passed}")
    
    def log_entry(
        self,
        trade_id: str,
        fill_price: float,
        quantity: float,
        position_size_usd: float,
        leverage: float,
        slippage_pct: float,
        fees_usd: float = 0.0
    ):
        """
        Log trade entry execution.
        
        Args:
            trade_id: Trade ID
            fill_price: Actual fill price
            quantity: Position quantity
            position_size_usd: Position size in USD
            leverage: Leverage used
            slippage_pct: Slippage percentage
            fees_usd: Fees paid in USD
        """
        if trade_id not in self.trades:
            logger.warning(f"Trade {trade_id} not found for entry logging")
            return
        
        trade = self.trades[trade_id]
        trade['status'] = TradeStatus.ENTRY_FILLED.value
        
        # Update execution details
        trade['execution']['entry_filled_at'] = datetime.now(timezone.utc).isoformat()
        trade['execution']['entry_fill_price'] = fill_price
        trade['execution']['entry_slippage_pct'] = slippage_pct
        trade['execution']['quantity'] = quantity
        trade['execution']['position_size_usd'] = position_size_usd
        trade['execution']['leverage'] = leverage
        
        trade['performance']['fees_usd'] = fees_usd
        
        # Log event
        self._log_event(trade_id, TradeStatus.ENTRY_FILLED.value, {
            'fill_price': fill_price,
            'quantity': quantity,
            'slippage_pct': slippage_pct,
            'fees_usd': fees_usd
        })
        
        logger.info(
            f"Entry logged: {trade_id}, fill={fill_price}, "
            f"qty={quantity}, slip={slippage_pct:.3f}%"
        )
    
    def log_tp_hit(
        self,
        trade_id: str,
        tp_level: str,
        hit_price: float,
        reduction_qty: float
    ):
        """
        Log TP level hit.
        
        Args:
            trade_id: Trade ID
            tp_level: TP level ('tp1', 'tp2', 'tp3')
            hit_price: Price at TP hit
            reduction_qty: Quantity reduced
        """
        if trade_id not in self.trades:
            logger.warning(f"Trade {trade_id} not found for TP logging")
            return
        
        trade = self.trades[trade_id]
        
        # Update TP tracking
        tp_key = f"{tp_level}_hit"
        tp_time_key = f"{tp_level}_hit_at"
        
        trade['tp_sl'][tp_key] = True
        trade['tp_sl'][tp_time_key] = datetime.now(timezone.utc).isoformat()
        
        # Update status
        if tp_level == 'tp1':
            trade['status'] = TradeStatus.TP1_HIT.value
        elif tp_level == 'tp2':
            trade['status'] = TradeStatus.TP2_HIT.value
        elif tp_level == 'tp3':
            trade['status'] = TradeStatus.TP3_HIT.value
        
        # Log event
        self._log_event(trade_id, trade['status'], {
            'tp_level': tp_level,
            'hit_price': hit_price,
            'reduction_qty': reduction_qty
        })
        
        logger.info(f"TP hit logged: {trade_id}, {tp_level}, price={hit_price}")
    
    def log_trailing_activation(self, trade_id: str):
        """Log trailing stop activation."""
        if trade_id not in self.trades:
            return
        
        trade = self.trades[trade_id]
        trade['status'] = TradeStatus.TRAILING_ACTIVE.value
        trade['tp_sl']['trailing_activated'] = True
        trade['tp_sl']['trailing_activated_at'] = datetime.now(timezone.utc).isoformat()
        
        self._log_event(trade_id, TradeStatus.TRAILING_ACTIVE.value, {})
        logger.info(f"Trailing stop activated: {trade_id}")
    
    def log_exit(
        self,
        trade_id: str,
        exit_price: float,
        exit_reason: str,
        realized_pnl_usd: float,
        time_stop: bool = False,
        early_reduce: bool = False
    ):
        """
        Log trade exit.
        
        Args:
            trade_id: Trade ID
            exit_price: Exit price
            exit_reason: Reason for exit
            realized_pnl_usd: Realized P&L in USD
            time_stop: Whether time stop triggered
            early_reduce: Whether early reduce triggered
        """
        if trade_id not in self.trades:
            logger.warning(f"Trade {trade_id} not found for exit logging")
            return
        
        trade = self.trades[trade_id]
        trade['status'] = TradeStatus.CLOSED.value
        
        exit_time = datetime.now(timezone.utc)
        entry_time = datetime.fromisoformat(trade['created_at'])
        hold_duration = (exit_time - entry_time).total_seconds() / 3600
        
        # Update exit details
        trade['exit']['exit_reason'] = exit_reason
        trade['exit']['exit_price'] = exit_price
        trade['exit']['exit_at'] = exit_time.isoformat()
        trade['exit']['hold_duration_hours'] = hold_duration
        trade['exit']['time_stop_triggered'] = time_stop
        trade['exit']['early_reduce_triggered'] = early_reduce
        
        # Calculate performance
        entry_price = trade['execution']['entry_fill_price']
        side = trade['signal']['side']
        
        if entry_price:
            pnl_pct = (
                (exit_price - entry_price) / entry_price * 100
                if side == 'long'
                else (entry_price - exit_price) / entry_price * 100
            )
            
            stop_loss = trade['signal']['stop_loss']
            risk_distance = abs(entry_price - stop_loss)
            if risk_distance > 0:
                r_multiple = abs(exit_price - entry_price) / risk_distance
                if pnl_pct < 0:
                    r_multiple *= -1
            else:
                r_multiple = 0.0
            
            trade['performance']['realized_pnl_usd'] = realized_pnl_usd
            trade['performance']['realized_pnl_pct'] = pnl_pct
            trade['performance']['r_multiple'] = r_multiple
            trade['performance']['win'] = realized_pnl_usd > 0
        
        # Log event
        self._log_event(trade_id, TradeStatus.CLOSED.value, {
            'exit_price': exit_price,
            'exit_reason': exit_reason,
            'realized_pnl_usd': realized_pnl_usd,
            'hold_hours': hold_duration
        })
        
        # Save to file
        self._save_trade_to_file(trade_id)
        
        logger.info(
            f"Exit logged: {trade_id}, price={exit_price}, "
            f"pnl=${realized_pnl_usd:.2f}, reason={exit_reason}"
        )
    
    def _log_event(self, trade_id: str, event_type: str, data: Dict):
        """Log a trade event."""
        if trade_id not in self.trade_events:
            self.trade_events[trade_id] = []
        
        event = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'event_type': event_type,
            'data': data
        }
        
        self.trade_events[trade_id].append(event)
        
        # Save to DB if enabled
        if self.enable_db and self.db_collection:
            try:
                self.db_collection.insert_one({
                    'trade_id': trade_id,
                    'event': event
                })
            except Exception as e:
                logger.error(f"Error saving event to DB: {e}")
    
    def _save_trade_to_file(self, trade_id: str):
        """Save trade to JSON file."""
        if trade_id not in self.trades:
            return
        
        trade = self.trades[trade_id]
        trade['events'] = self.trade_events.get(trade_id, [])
        
        filename = f"{trade_id}.json"
        filepath = self.log_dir / filename
        
        try:
            with open(filepath, 'w') as f:
                json.dump(trade, f, indent=2)
            logger.info(f"Trade saved to file: {filepath}")
        except Exception as e:
            logger.error(f"Error saving trade to file: {e}")
    
    def export_to_csv(self, output_path: Optional[str] = None) -> str:
        """
        Export all trades to CSV.
        
        Args:
            output_path: Output CSV path
        
        Returns:
            Path to CSV file
        """
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = self.log_dir / f"trades_{timestamp}.csv"
        
        fieldnames = [
            'trade_id', 'created_at', 'side', 'tier', 'regime',
            'entry_price', 'exit_price', 'stop_loss',
            'tp1_hit', 'tp2_hit', 'tp3_hit',
            'realized_pnl_usd', 'realized_pnl_pct', 'r_multiple',
            'win', 'exit_reason', 'hold_duration_hours'
        ]
        
        try:
            with open(output_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for trade_id, trade in self.trades.items():
                    if trade['status'] == TradeStatus.CLOSED.value:
                        row = {
                            'trade_id': trade_id,
                            'created_at': trade['created_at'],
                            'side': trade['signal']['side'],
                            'tier': trade['context']['tier'],
                            'regime': trade['context']['regime'],
                            'entry_price': trade['execution']['entry_fill_price'],
                            'exit_price': trade['exit']['exit_price'],
                            'stop_loss': trade['signal']['stop_loss'],
                            'tp1_hit': trade['tp_sl']['tp1_hit'],
                            'tp2_hit': trade['tp_sl']['tp2_hit'],
                            'tp3_hit': trade['tp_sl']['tp3_hit'],
                            'realized_pnl_usd': trade['performance']['realized_pnl_usd'],
                            'realized_pnl_pct': trade['performance']['realized_pnl_pct'],
                            'r_multiple': trade['performance']['r_multiple'],
                            'win': trade['performance']['win'],
                            'exit_reason': trade['exit']['exit_reason'],
                            'hold_duration_hours': trade['exit']['hold_duration_hours']
                        }
                        writer.writerow(row)
            
            logger.info(f"Trades exported to CSV: {output_path}")
            return str(output_path)
        
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return ""
    
    def get_trade(self, trade_id: str) -> Optional[Dict]:
        """Get trade by ID."""
        return self.trades.get(trade_id)
    
    def get_all_trades(self) -> Dict[str, Dict]:
        """Get all trades."""
        return self.trades.copy()
    
    def get_closed_trades(self) -> List[Dict]:
        """Get all closed trades."""
        return [
            trade for trade in self.trades.values()
            if trade['status'] == TradeStatus.CLOSED.value
        ]


# Import os for path operations
import os
