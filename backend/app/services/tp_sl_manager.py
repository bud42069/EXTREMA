"""
TP/SL Manager (Phase 3)
Implements 3-tier TP ladder, trailing stops, time stops, and early reduce.
Part of the SOLUSDT Swing-Capture Playbook v1.0
"""
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timezone, timedelta
from enum import Enum
import numpy as np
from ..utils.logging import get_logger

logger = get_logger(__name__)


class TPLevel(Enum):
    """Take-profit level enum."""
    TP1 = 1
    TP2 = 2
    TP3 = 3


class TrailingStopStatus(Enum):
    """Trailing stop status enum."""
    INACTIVE = "inactive"
    ACTIVE = "active"
    BREAKEVEN = "breakeven"


class TPSLManager:
    """
    Manages 3-tier TP ladder, trailing stops, time stops, and early reduce protocol.
    
    Features:
    - 3-tier TP ladder (TP1: 1.0R @ 50%, TP2: 2.0-2.5R @ 30%, TP3: 3.0-4.0R @ 20%)
    - Trailing stop (activate after TP1, 0.5×ATR trail)
    - Time stops (24h normal, 12h squeeze)
    - Early reduce (50% cut on reversal)
    """
    
    def __init__(
        self,
        tp1_r: float = 1.0,
        tp2_r: float = 2.0,
        tp3_r: float = 3.0,
        tp1_pct: float = 0.50,
        tp2_pct: float = 0.30,
        tp3_pct: float = 0.20,
        trail_atr_mult: float = 0.5,
        max_hold_hours_normal: int = 24,
        max_hold_hours_squeeze: int = 12
    ):
        """
        Initialize TP/SL manager.
        
        Args:
            tp1_r: TP1 R-multiple (default 1.0R)
            tp2_r: TP2 R-multiple (default 2.0R)
            tp3_r: TP3 R-multiple (default 3.0R)
            tp1_pct: TP1 reduction percentage (default 50%)
            tp2_pct: TP2 reduction percentage (default 30%)
            tp3_pct: TP3 reduction percentage (default 20%)
            trail_atr_mult: Trailing stop ATR multiplier (default 0.5×)
            max_hold_hours_normal: Max hold time normal/wide (default 24h)
            max_hold_hours_squeeze: Max hold time squeeze (default 12h)
        """
        self.tp1_r = tp1_r
        self.tp2_r = tp2_r
        self.tp3_r = tp3_r
        self.tp1_pct = tp1_pct
        self.tp2_pct = tp2_pct
        self.tp3_pct = tp3_pct
        self.trail_atr_mult = trail_atr_mult
        self.max_hold_hours_normal = max_hold_hours_normal
        self.max_hold_hours_squeeze = max_hold_hours_squeeze
        
        # Position tracking
        self.positions: Dict[str, Dict] = {}
        
        logger.info(
            f"TPSLManager initialized: TP ladder={tp1_r}/{tp2_r}/{tp3_r}R, "
            f"trail={trail_atr_mult}×ATR, time_stops={max_hold_hours_normal}h/{max_hold_hours_squeeze}h"
        )
    
    def calculate_tp_sl_levels(
        self,
        entry_price: float,
        stop_loss: float,
        side: str,
        regime: str = 'normal',
        atr: float = 10.0
    ) -> Dict:
        """
        Calculate 3-tier TP and SL levels.
        
        Per playbook:
        - TP1: 1.0R (take 50% off)
        - TP2: 2.0R normal, 2.5R squeeze (take 30% off)
        - TP3: 3.0R normal, 4.0R squeeze (take 20% off)
        - SL: Given (ATR-based from signal detection)
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            side: 'long' or 'short'
            regime: Market regime ('squeeze', 'normal', 'wide')
            atr: Current ATR for trailing calculation
        
        Returns:
            Dict with TP/SL levels and percentages
        """
        # Calculate R (risk amount)
        risk = abs(entry_price - stop_loss)
        
        # Adjust TP2/TP3 based on regime
        if regime == 'squeeze':
            tp2_r = 2.5
            tp3_r = 4.0
        else:
            tp2_r = self.tp2_r
            tp3_r = self.tp3_r
        
        # Calculate TP levels
        if side == 'long':
            tp1 = entry_price + (self.tp1_r * risk)
            tp2 = entry_price + (tp2_r * risk)
            tp3 = entry_price + (tp3_r * risk)
        else:  # short
            tp1 = entry_price - (self.tp1_r * risk)
            tp2 = entry_price - (tp2_r * risk)
            tp3 = entry_price - (tp3_r * risk)
        
        result = {
            'entry': entry_price,
            'stop_loss': stop_loss,
            'risk': risk,
            'tp1': tp1,
            'tp2': tp2,
            'tp3': tp3,
            'tp1_r': self.tp1_r,
            'tp2_r': tp2_r,
            'tp3_r': tp3_r,
            'tp1_pct': self.tp1_pct,
            'tp2_pct': self.tp2_pct,
            'tp3_pct': self.tp3_pct,
            'regime': regime,
            'atr': atr,
            'trail_distance': self.trail_atr_mult * atr
        }
        
        logger.info(
            f"TP/SL levels calculated: {side}, regime={regime}, "
            f"entry={entry_price}, SL={stop_loss}, "
            f"TP1={tp1} ({self.tp1_r}R), TP2={tp2} ({tp2_r}R), TP3={tp3} ({tp3_r}R)"
        )
        
        return result
    
    def create_position(
        self,
        position_id: str,
        entry_price: float,
        stop_loss: float,
        side: str,
        quantity: float,
        regime: str,
        atr: float
    ) -> Dict:
        """
        Create a new position with TP/SL management.
        
        Args:
            position_id: Position ID
            entry_price: Entry price
            stop_loss: Stop loss price
            side: 'long' or 'short'
            quantity: Position quantity
            regime: Market regime
            atr: Current ATR
        
        Returns:
            Position dict
        """
        # Calculate TP/SL levels
        levels = self.calculate_tp_sl_levels(entry_price, stop_loss, side, regime, atr)
        
        # Create position object
        position = {
            'position_id': position_id,
            'side': side,
            'entry_price': entry_price,
            'current_quantity': quantity,
            'original_quantity': quantity,
            'levels': levels,
            'tp_hits': {
                'tp1': False,
                'tp2': False,
                'tp3': False
            },
            'trailing_stop': {
                'status': TrailingStopStatus.INACTIVE.value,
                'current_stop': stop_loss,
                'highest_price': entry_price if side == 'long' else None,
                'lowest_price': entry_price if side == 'short' else None
            },
            'entry_time': datetime.now(timezone.utc),
            'max_hold_hours': (
                self.max_hold_hours_squeeze if regime == 'squeeze'
                else self.max_hold_hours_normal
            ),
            'early_reduce_triggered': False,
            'closed': False
        }
        
        # Store position
        self.positions[position_id] = position
        
        logger.info(
            f"Position created: {position_id}, {side}, qty={quantity}, "
            f"entry={entry_price}, max_hold={position['max_hold_hours']}h"
        )
        
        return position
    
    def check_tp_hits(
        self,
        position_id: str,
        current_price: float
    ) -> Dict:
        """
        Check if any TP levels have been hit.
        
        Args:
            position_id: Position ID
            current_price: Current market price
        
        Returns:
            Dict with TP hit results and reduction actions
        """
        if position_id not in self.positions:
            return {'error': 'Position not found'}
        
        position = self.positions[position_id]
        levels = position['levels']
        side = position['side']
        
        result = {
            'tp_hits': [],
            'reductions': [],
            'activate_trailing': False
        }
        
        # Check TP1
        if not position['tp_hits']['tp1']:
            tp1_hit = (
                (side == 'long' and current_price >= levels['tp1']) or
                (side == 'short' and current_price <= levels['tp1'])
            )
            
            if tp1_hit:
                position['tp_hits']['tp1'] = True
                reduction_qty = position['original_quantity'] * levels['tp1_pct']
                
                result['tp_hits'].append('TP1')
                result['reductions'].append({
                    'level': 'TP1',
                    'price': levels['tp1'],
                    'quantity': reduction_qty,
                    'pct': levels['tp1_pct']
                })
                result['activate_trailing'] = True
                
                logger.info(
                    f"TP1 HIT: {position_id}, price={current_price}, "
                    f"reduce={reduction_qty} ({levels['tp1_pct']*100}%)"
                )
        
        # Check TP2
        if not position['tp_hits']['tp2']:
            tp2_hit = (
                (side == 'long' and current_price >= levels['tp2']) or
                (side == 'short' and current_price <= levels['tp2'])
            )
            
            if tp2_hit:
                position['tp_hits']['tp2'] = True
                reduction_qty = position['original_quantity'] * levels['tp2_pct']
                
                result['tp_hits'].append('TP2')
                result['reductions'].append({
                    'level': 'TP2',
                    'price': levels['tp2'],
                    'quantity': reduction_qty,
                    'pct': levels['tp2_pct']
                })
                
                logger.info(
                    f"TP2 HIT: {position_id}, price={current_price}, "
                    f"reduce={reduction_qty} ({levels['tp2_pct']*100}%)"
                )
        
        # Check TP3
        if not position['tp_hits']['tp3']:
            tp3_hit = (
                (side == 'long' and current_price >= levels['tp3']) or
                (side == 'short' and current_price <= levels['tp3'])
            )
            
            if tp3_hit:
                position['tp_hits']['tp3'] = True
                reduction_qty = position['original_quantity'] * levels['tp3_pct']
                
                result['tp_hits'].append('TP3')
                result['reductions'].append({
                    'level': 'TP3',
                    'price': levels['tp3'],
                    'quantity': reduction_qty,
                    'pct': levels['tp3_pct']
                })
                
                logger.info(
                    f"TP3 HIT: {position_id}, price={current_price}, "
                    f"reduce={reduction_qty} ({levels['tp3_pct']*100}%)"
                )
        
        return result
    
    def update_trailing_stop(
        self,
        position_id: str,
        current_price: float
    ) -> Dict:
        """
        Update trailing stop if TP1 has been hit.
        
        Per playbook:
        - Activate after TP1 hit
        - First move to breakeven
        - Then trail by 0.5× ATR(14, 5m)
        
        Args:
            position_id: Position ID
            current_price: Current market price
        
        Returns:
            Dict with trailing stop update
        """
        if position_id not in self.positions:
            return {'error': 'Position not found'}
        
        position = self.positions[position_id]
        trailing = position['trailing_stop']
        side = position['side']
        levels = position['levels']
        
        result = {
            'updated': False,
            'new_stop': trailing['current_stop'],
            'status': trailing['status']
        }
        
        # Only trail if TP1 hit
        if not position['tp_hits']['tp1']:
            return result
        
        # Activate trailing if not already active
        if trailing['status'] == TrailingStopStatus.INACTIVE.value:
            # Move to breakeven first
            trailing['status'] = TrailingStopStatus.BREAKEVEN.value
            trailing['current_stop'] = position['entry_price']
            result['updated'] = True
            result['new_stop'] = position['entry_price']
            result['status'] = TrailingStopStatus.BREAKEVEN.value
            
            logger.info(
                f"Trailing stop activated: {position_id}, moved to breakeven "
                f"(entry={position['entry_price']})"
            )
            
            return result
        
        # Update trailing stop
        if side == 'long':
            # Track highest price
            if trailing['highest_price'] is None or current_price > trailing['highest_price']:
                trailing['highest_price'] = current_price
            
            # Calculate new stop
            new_stop = trailing['highest_price'] - levels['trail_distance']
            
            # Only move stop up
            if new_stop > trailing['current_stop']:
                trailing['current_stop'] = new_stop
                trailing['status'] = TrailingStopStatus.ACTIVE.value
                result['updated'] = True
                result['new_stop'] = new_stop
                result['status'] = TrailingStopStatus.ACTIVE.value
                
                logger.info(
                    f"Trailing stop updated (long): {position_id}, "
                    f"new_stop={new_stop}, highest={trailing['highest_price']}"
                )
        
        else:  # short
            # Track lowest price
            if trailing['lowest_price'] is None or current_price < trailing['lowest_price']:
                trailing['lowest_price'] = current_price
            
            # Calculate new stop
            new_stop = trailing['lowest_price'] + levels['trail_distance']
            
            # Only move stop down
            if new_stop < trailing['current_stop']:
                trailing['current_stop'] = new_stop
                trailing['status'] = TrailingStopStatus.ACTIVE.value
                result['updated'] = True
                result['new_stop'] = new_stop
                result['status'] = TrailingStopStatus.ACTIVE.value
                
                logger.info(
                    f"Trailing stop updated (short): {position_id}, "
                    f"new_stop={new_stop}, lowest={trailing['lowest_price']}"
                )
        
        return result
    
    def check_time_stop(self, position_id: str) -> Dict:
        """
        Check if position has exceeded max hold time.
        
        Per playbook:
        - Normal/Wide: 24h max hold
        - Squeeze: 12h max hold
        
        Args:
            position_id: Position ID
        
        Returns:
            Dict with time stop check result
        """
        if position_id not in self.positions:
            return {'error': 'Position not found'}
        
        position = self.positions[position_id]
        
        # Calculate hold duration
        current_time = datetime.now(timezone.utc)
        hold_duration = current_time - position['entry_time']
        hold_hours = hold_duration.total_seconds() / 3600
        
        # Check against max hold
        max_hold = position['max_hold_hours']
        time_stop_triggered = hold_hours >= max_hold
        
        result = {
            'time_stop_triggered': time_stop_triggered,
            'hold_hours': hold_hours,
            'max_hold_hours': max_hold,
            'entry_time': position['entry_time'].isoformat(),
            'current_time': current_time.isoformat()
        }
        
        if time_stop_triggered:
            logger.warning(
                f"Time stop triggered: {position_id}, hold={hold_hours:.1f}h >= "
                f"{max_hold}h"
            )
        
        return result
    
    def check_early_reduce(
        self,
        position_id: str,
        reversal_signal: bool
    ) -> Dict:
        """
        Check if early reduce protocol should be triggered.
        
        Per playbook:
        - If opposite signal appears, cut 50% immediately
        - Move stop to breakeven on remainder
        - Exit fully on second reversal signal
        
        Args:
            position_id: Position ID
            reversal_signal: Whether opposite signal detected
        
        Returns:
            Dict with early reduce decision
        """
        if position_id not in self.positions:
            return {'error': 'Position not found'}
        
        position = self.positions[position_id]
        
        result = {
            'early_reduce_triggered': False,
            'reduction_pct': 0.0,
            'move_to_breakeven': False,
            'full_exit': False
        }
        
        if not reversal_signal:
            return result
        
        # Check if already reduced
        if position['early_reduce_triggered']:
            # Second reversal signal - full exit
            result['full_exit'] = True
            logger.warning(
                f"Second reversal signal: {position_id}, FULL EXIT"
            )
        else:
            # First reversal signal - 50% reduce
            result['early_reduce_triggered'] = True
            result['reduction_pct'] = 0.50
            result['move_to_breakeven'] = True
            
            position['early_reduce_triggered'] = True
            
            logger.warning(
                f"Early reduce triggered: {position_id}, reduce 50%, "
                f"move stop to breakeven"
            )
        
        return result
    
    def get_position(self, position_id: str) -> Optional[Dict]:
        """Get position by ID."""
        return self.positions.get(position_id)
    
    def close_position(self, position_id: str, reason: str = "manual_close"):
        """Close a position."""
        if position_id in self.positions:
            self.positions[position_id]['closed'] = True
            logger.info(f"Position closed: {position_id}, reason={reason}")
