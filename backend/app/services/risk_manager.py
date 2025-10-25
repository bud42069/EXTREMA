"""
Risk Manager (Phase 3)
Implements liq-gap guards, position sizing, and risk limit checks.
Part of the SOLUSDT Swing-Capture Playbook v1.0
"""
import numpy as np
from typing import Optional, Dict, Tuple
from ..utils.logging import get_logger

logger = get_logger(__name__)


class RiskManager:
    """
    Manages risk limits, liq-gap guards, and position sizing.
    
    Features:
    - Liq-gap guards (minimum 3× stop distance)
    - Position sizing based on tier (A-tier: 1.0×, B-tier: 0.5×)
    - Margin calculations
    - Risk limit checks
    """
    
    def __init__(
        self,
        base_position_size: float = 1000.0,  # Base position in USD
        max_leverage: float = 5.0,
        min_liq_gap_multiplier: float = 3.0,
        account_balance: float = 10000.0,
        max_risk_per_trade_pct: float = 2.0
    ):
        """
        Initialize risk manager.
        
        Args:
            base_position_size: Base position size in USD (default 1000)
            max_leverage: Maximum leverage allowed (default 5×)
            min_liq_gap_multiplier: Minimum liq-gap as multiple of stop distance (default 3×)
            account_balance: Account balance in USD (default 10000)
            max_risk_per_trade_pct: Max risk per trade as % of account (default 2%)
        """
        self.base_position_size = base_position_size
        self.max_leverage = max_leverage
        self.min_liq_gap_multiplier = min_liq_gap_multiplier
        self.account_balance = account_balance
        self.max_risk_per_trade_pct = max_risk_per_trade_pct
        
        logger.info(
            f"RiskManager initialized: base_size=${base_position_size}, "
            f"max_leverage={max_leverage}×, min_liq_gap={min_liq_gap_multiplier}×stop"
        )
    
    def calculate_liquidation_price(
        self,
        entry_price: float,
        side: str,
        leverage: float,
        maintenance_margin_rate: float = 0.005  # 0.5% for most perps
    ) -> float:
        """
        Calculate liquidation price for a leveraged position.
        
        Args:
            entry_price: Entry price
            side: 'long' or 'short'
            leverage: Leverage used
            maintenance_margin_rate: Maintenance margin rate (default 0.5%)
        
        Returns:
            Liquidation price
        """
        if side == 'long':
            # Liq price = Entry × (1 - 1/leverage + maintenance_margin_rate)
            liq_price = entry_price * (1 - 1/leverage + maintenance_margin_rate)
        else:  # short
            # Liq price = Entry × (1 + 1/leverage - maintenance_margin_rate)
            liq_price = entry_price * (1 + 1/leverage - maintenance_margin_rate)
        
        return liq_price
    
    def calculate_liq_gap(
        self,
        entry_price: float,
        stop_loss: float,
        side: str,
        leverage: float
    ) -> Dict:
        """
        Calculate liquidation gap and check if it meets minimum requirements.
        
        Per playbook: Liq-gap must be ≥ 3× stop distance to ensure safety margin.
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            side: 'long' or 'short'
            leverage: Leverage used
        
        Returns:
            Dict with liq-gap analysis
        """
        # Calculate liquidation price
        liq_price = self.calculate_liquidation_price(entry_price, side, leverage)
        
        # Calculate distances
        if side == 'long':
            stop_distance = abs(entry_price - stop_loss)
            liq_distance = abs(liq_price - entry_price)
        else:  # short
            stop_distance = abs(stop_loss - entry_price)
            liq_distance = abs(entry_price - liq_price)
        
        # Calculate liq-gap as multiple of stop distance
        if stop_distance > 0:
            liq_gap_multiplier = liq_distance / stop_distance
        else:
            liq_gap_multiplier = 0.0
        
        # Check if liq-gap is sufficient
        liq_gap_ok = liq_gap_multiplier >= self.min_liq_gap_multiplier
        
        result = {
            'liq_price': liq_price,
            'liq_distance': liq_distance,
            'stop_distance': stop_distance,
            'liq_gap_multiplier': liq_gap_multiplier,
            'liq_gap_ok': liq_gap_ok,
            'min_required_multiplier': self.min_liq_gap_multiplier
        }
        
        if not liq_gap_ok:
            logger.warning(
                f"Liq-gap insufficient: {liq_gap_multiplier:.2f}× < "
                f"{self.min_liq_gap_multiplier}× (entry={entry_price}, "
                f"stop={stop_loss}, liq={liq_price})"
            )
        else:
            logger.info(
                f"Liq-gap OK: {liq_gap_multiplier:.2f}× ≥ "
                f"{self.min_liq_gap_multiplier}×"
            )
        
        return result
    
    def calculate_position_size(
        self,
        tier: str,
        entry_price: float,
        stop_loss: float,
        leverage: float = 3.0
    ) -> Dict:
        """
        Calculate position size based on tier and risk parameters.
        
        Per playbook:
        - A-tier: Full size (1.0× base)
        - B-tier: Half size (0.5× base)
        - Risk-based sizing: Limit risk to max_risk_per_trade_pct of account
        
        Args:
            tier: 'A' or 'B'
            entry_price: Entry price
            stop_loss: Stop loss price
            leverage: Leverage to use (default 3×)
        
        Returns:
            Dict with position sizing details
        """
        # Tier multiplier
        if tier == 'A':
            tier_multiplier = 1.0
        elif tier == 'B':
            tier_multiplier = 0.5
        else:
            logger.warning(f"Invalid tier '{tier}', using B-tier sizing")
            tier_multiplier = 0.5
        
        # Calculate risk amount
        risk_distance = abs(entry_price - stop_loss)
        risk_distance_pct = risk_distance / entry_price * 100
        
        # Position size from base
        position_size_usd = self.base_position_size * tier_multiplier
        
        # Calculate risk in USD
        risk_usd = position_size_usd * (risk_distance_pct / 100)
        
        # Check against max risk per trade
        max_risk_usd = self.account_balance * (self.max_risk_per_trade_pct / 100)
        
        if risk_usd > max_risk_usd:
            # Reduce position size to meet risk limit
            position_size_usd = max_risk_usd / (risk_distance_pct / 100)
            logger.warning(
                f"Position size reduced to meet risk limit: "
                f"${position_size_usd:.2f} (risk=${max_risk_usd:.2f})"
            )
        
        # Calculate quantity
        quantity = position_size_usd / entry_price
        
        # Calculate margin required
        margin_required = position_size_usd / leverage
        
        result = {
            'tier': tier,
            'tier_multiplier': tier_multiplier,
            'position_size_usd': position_size_usd,
            'quantity': quantity,
            'leverage': leverage,
            'margin_required': margin_required,
            'risk_distance_pct': risk_distance_pct,
            'risk_usd': risk_usd,
            'max_risk_usd': max_risk_usd,
            'risk_ok': risk_usd <= max_risk_usd
        }
        
        logger.info(
            f"Position sizing: tier={tier}, size=${position_size_usd:.2f}, "
            f"qty={quantity:.4f}, risk=${risk_usd:.2f} ({risk_distance_pct:.2f}%)"
        )
        
        return result
    
    def check_entry_risk(
        self,
        entry_price: float,
        stop_loss: float,
        side: str,
        tier: str,
        leverage: float = 3.0
    ) -> Dict:
        """
        Comprehensive entry risk check.
        
        Checks:
        1. Liq-gap guard (≥3× stop distance)
        2. Position sizing within limits
        3. Risk per trade within max %
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            side: 'long' or 'short'
            tier: 'A' or 'B'
            leverage: Leverage to use
        
        Returns:
            Dict with comprehensive risk assessment
        """
        result = {
            'entry_allowed': False,
            'liq_gap': {},
            'position_sizing': {},
            'warnings': [],
            'reasons': []
        }
        
        # Check liq-gap
        liq_gap = self.calculate_liq_gap(entry_price, stop_loss, side, leverage)
        result['liq_gap'] = liq_gap
        
        if not liq_gap['liq_gap_ok']:
            result['reasons'].append(
                f"Liq-gap insufficient: {liq_gap['liq_gap_multiplier']:.2f}× < "
                f"{self.min_liq_gap_multiplier}×"
            )
        
        # Calculate position sizing
        position_sizing = self.calculate_position_size(
            tier, entry_price, stop_loss, leverage
        )
        result['position_sizing'] = position_sizing
        
        if not position_sizing['risk_ok']:
            result['warnings'].append(
                f"Risk adjusted: ${position_sizing['risk_usd']:.2f} > "
                f"${position_sizing['max_risk_usd']:.2f}"
            )
        
        # Check margin available
        if position_sizing['margin_required'] > self.account_balance * 0.8:
            result['reasons'].append(
                f"Insufficient margin: required ${position_sizing['margin_required']:.2f}, "
                f"available ${self.account_balance * 0.8:.2f}"
            )
        
        # Overall decision
        result['entry_allowed'] = (
            liq_gap['liq_gap_ok'] and
            len(result['reasons']) == 0
        )
        
        if result['entry_allowed']:
            logger.info(
                f"Entry risk check PASSED: tier={tier}, "
                f"liq_gap={liq_gap['liq_gap_multiplier']:.2f}×, "
                f"size=${position_sizing['position_size_usd']:.2f}"
            )
        else:
            logger.warning(
                f"Entry risk check FAILED: {', '.join(result['reasons'])}"
            )
        
        return result
    
    def check_ongoing_risk(
        self,
        current_price: float,
        entry_price: float,
        stop_loss: float,
        side: str,
        leverage: float
    ) -> Dict:
        """
        Check ongoing position risk (called periodically).
        
        Monitors:
        - Distance to liquidation
        - Current P&L
        - Stop distance
        
        Args:
            current_price: Current market price
            entry_price: Entry price
            stop_loss: Current stop loss
            side: 'long' or 'short'
            leverage: Leverage used
        
        Returns:
            Dict with ongoing risk assessment
        """
        # Calculate liq-gap at current price
        liq_gap = self.calculate_liq_gap(entry_price, stop_loss, side, leverage)
        
        # Calculate current P&L
        if side == 'long':
            pnl_pct = (current_price - entry_price) / entry_price * 100
            distance_to_stop = current_price - stop_loss
        else:
            pnl_pct = (entry_price - current_price) / entry_price * 100
            distance_to_stop = stop_loss - current_price
        
        result = {
            'liq_gap': liq_gap,
            'current_price': current_price,
            'pnl_pct': pnl_pct,
            'distance_to_stop': distance_to_stop,
            'near_stop': distance_to_stop < (entry_price * 0.005),  # Within 0.5%
            'risk_ok': liq_gap['liq_gap_ok']
        }
        
        if not result['risk_ok']:
            logger.warning(
                f"Ongoing risk issue: liq_gap={liq_gap['liq_gap_multiplier']:.2f}×, "
                f"pnl={pnl_pct:.2f}%"
            )
        
        return result
