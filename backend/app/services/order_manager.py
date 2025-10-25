"""
Order Manager (Phase 3)
Implements post-only order placement logic, unfilled protocol, and order tracking.
Part of the SOLUSDT Swing-Capture Playbook v1.0
"""
import asyncio
from typing import Optional, Dict, List
from enum import Enum
from datetime import datetime, timezone
from ..utils.logging import get_logger

logger = get_logger(__name__)


class OrderSide(Enum):
    """Order side enum."""
    LONG = "long"
    SHORT = "short"


class OrderType(Enum):
    """Order type enum."""
    LIMIT = "limit"
    MARKET = "market"
    POST_ONLY = "post_only"


class OrderStatus(Enum):
    """Order status enum."""
    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class Order:
    """
    Order object representing a single order.
    """
    
    def __init__(
        self,
        order_id: str,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: Optional[float] = None,
        reduce_only: bool = False
    ):
        self.order_id = order_id
        self.symbol = symbol
        self.side = side
        self.order_type = order_type
        self.quantity = quantity
        self.price = price
        self.reduce_only = reduce_only
        self.status = OrderStatus.PENDING
        self.filled_quantity = 0.0
        self.average_fill_price = 0.0
        self.created_at = datetime.now(timezone.utc)
        self.filled_at: Optional[datetime] = None
        self.cancelled_at: Optional[datetime] = None
        self.reject_reason: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert order to dictionary."""
        return {
            'order_id': self.order_id,
            'symbol': self.symbol,
            'side': self.side.value,
            'type': self.order_type.value,
            'quantity': self.quantity,
            'price': self.price,
            'reduce_only': self.reduce_only,
            'status': self.status.value,
            'filled_quantity': self.filled_quantity,
            'average_fill_price': self.average_fill_price,
            'created_at': self.created_at.isoformat(),
            'filled_at': self.filled_at.isoformat() if self.filled_at else None,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None,
            'reject_reason': self.reject_reason
        }


class OrderManager:
    """
    Manages order placement, tracking, and the unfilled protocol.
    
    Features:
    - Post-only order placement (limit orders at bid/ask)
    - Unfilled protocol (cancel and retry with slip caps)
    - Order status tracking
    - Fill monitoring
    """
    
    def __init__(
        self,
        max_slip_attempts: int = 3,
        max_slip_pct: float = 0.05,
        unfilled_wait_seconds: int = 2,
        tick_size: float = 0.01
    ):
        """
        Initialize order manager.
        
        Args:
            max_slip_attempts: Maximum slip attempts (default 3)
            max_slip_pct: Maximum total slippage percentage (default 0.05%)
            unfilled_wait_seconds: Seconds to wait before checking fill (default 2)
            tick_size: Tick size for price increments (default 0.01)
        """
        self.max_slip_attempts = max_slip_attempts
        self.max_slip_pct = max_slip_pct
        self.unfilled_wait_seconds = unfilled_wait_seconds
        self.tick_size = tick_size
        
        # Order tracking
        self.orders: Dict[str, Order] = {}
        self.active_orders: List[str] = []
        
        logger.info(
            f"OrderManager initialized: max_slip_attempts={max_slip_attempts}, "
            f"max_slip_pct={max_slip_pct}%, unfilled_wait={unfilled_wait_seconds}s"
        )
    
    def calculate_post_only_price(
        self,
        side: OrderSide,
        best_bid: float,
        best_ask: float,
        spread_bps: float
    ) -> float:
        """
        Calculate post-only order price.
        
        Per playbook: Place limit order at best bid (long) / best ask (short)
        to ensure maker fee and avoid crossing the spread.
        
        Args:
            side: Order side (long/short)
            best_bid: Current best bid price
            best_ask: Current best ask price
            spread_bps: Current spread in basis points
        
        Returns:
            Post-only limit price
        """
        if side == OrderSide.LONG:
            # For long: bid at best bid (passive buy)
            post_price = best_bid
        else:
            # For short: ask at best ask (passive sell)
            post_price = best_ask
        
        logger.info(
            f"Post-only price calculated: side={side.value}, "
            f"bid={best_bid}, ask={best_ask}, spread={spread_bps:.1f}bps, "
            f"post_price={post_price}"
        )
        
        return post_price
    
    async def place_post_only_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        best_bid: float,
        best_ask: float,
        spread_bps: float,
        reduce_only: bool = False
    ) -> Order:
        """
        Place a post-only limit order.
        
        Args:
            symbol: Trading symbol
            side: Order side (long/short)
            quantity: Order quantity
            best_bid: Current best bid
            best_ask: Current best ask
            spread_bps: Current spread in bps
            reduce_only: Whether order is reduce-only
        
        Returns:
            Order object
        """
        # Calculate post-only price
        price = self.calculate_post_only_price(side, best_bid, best_ask, spread_bps)
        
        # Create order
        order_id = f"ORDER_{datetime.now(timezone.utc).timestamp()}"
        order = Order(
            order_id=order_id,
            symbol=symbol,
            side=side,
            order_type=OrderType.POST_ONLY,
            quantity=quantity,
            price=price,
            reduce_only=reduce_only
        )
        
        # Store order
        self.orders[order_id] = order
        self.active_orders.append(order_id)
        
        # Simulate order placement (in production, call exchange API)
        order.status = OrderStatus.OPEN
        
        logger.info(
            f"Post-only order placed: {order_id}, {side.value}, "
            f"qty={quantity}, price={price}, reduce_only={reduce_only}"
        )
        
        return order
    
    async def check_order_fill(self, order_id: str) -> Dict:
        """
        Check if order is filled.
        
        Args:
            order_id: Order ID
        
        Returns:
            Dict with fill status
        """
        if order_id not in self.orders:
            return {'filled': False, 'error': 'Order not found'}
        
        order = self.orders[order_id]
        
        # Simulate fill check (in production, query exchange)
        # For now, return not filled to trigger unfilled protocol
        
        result = {
            'filled': order.status == OrderStatus.FILLED,
            'partially_filled': order.status == OrderStatus.PARTIALLY_FILLED,
            'filled_quantity': order.filled_quantity,
            'remaining_quantity': order.quantity - order.filled_quantity,
            'status': order.status.value
        }
        
        logger.debug(f"Order fill check: {order_id}, filled={result['filled']}")
        
        return result
    
    async def cancel_order(self, order_id: str, reason: str = "user_cancel") -> bool:
        """
        Cancel an order.
        
        Args:
            order_id: Order ID
            reason: Cancellation reason
        
        Returns:
            True if cancelled successfully
        """
        if order_id not in self.orders:
            logger.warning(f"Cannot cancel order {order_id}: not found")
            return False
        
        order = self.orders[order_id]
        
        if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED]:
            logger.warning(
                f"Cannot cancel order {order_id}: already {order.status.value}"
            )
            return False
        
        # Cancel order
        order.status = OrderStatus.CANCELLED
        order.cancelled_at = datetime.now(timezone.utc)
        
        # Remove from active orders
        if order_id in self.active_orders:
            self.active_orders.remove(order_id)
        
        logger.info(f"Order cancelled: {order_id}, reason={reason}")
        
        return True
    
    async def unfilled_protocol(
        self,
        order: Order,
        best_bid: float,
        best_ask: float,
        current_price: float,
        is_urgent: bool = False
    ) -> Dict:
        """
        Execute unfilled protocol with slip caps.
        
        Per playbook:
        1. Wait 2s after order placement
        2. If not filled, cancel and repost with +1 tick slip
        3. Max 3 attempts, max 0.05% total slippage
        4. If urgent (near stop), fallback to market order
        
        Args:
            order: Original order
            best_bid: Current best bid
            best_ask: Current best ask
            current_price: Current market price
            is_urgent: Whether execution is urgent
        
        Returns:
            Dict with protocol result
        """
        result = {
            'filled': False,
            'attempts': 0,
            'total_slip_pct': 0.0,
            'final_order': None,
            'reason': None
        }
        
        original_price = order.price
        current_attempt = 0
        total_slip = 0.0
        
        while current_attempt < self.max_slip_attempts:
            current_attempt += 1
            result['attempts'] = current_attempt
            
            # Wait for fill
            await asyncio.sleep(self.unfilled_wait_seconds)
            
            # Check fill status
            fill_status = await self.check_order_fill(order.order_id)
            
            if fill_status['filled']:
                result['filled'] = True
                result['final_order'] = order
                result['reason'] = 'filled'
                logger.info(
                    f"Unfilled protocol: Order filled on attempt {current_attempt}"
                )
                return result
            
            # Calculate slip for next attempt
            slip_amount = self.tick_size * current_attempt
            
            if order.side == OrderSide.LONG:
                new_price = original_price + slip_amount
            else:
                new_price = original_price - slip_amount
            
            slip_pct = abs(new_price - original_price) / original_price * 100
            total_slip = slip_pct
            result['total_slip_pct'] = total_slip
            
            # Check slip cap
            if total_slip > self.max_slip_pct:
                result['reason'] = 'slip_cap_exceeded'
                logger.warning(
                    f"Unfilled protocol: Slip cap exceeded ({total_slip:.3f}% > "
                    f"{self.max_slip_pct}%), abandoning"
                )
                await self.cancel_order(order.order_id, "slip_cap_exceeded")
                return result
            
            # Cancel and repost
            logger.info(
                f"Unfilled protocol: Attempt {current_attempt}, cancelling and "
                f"reposting with slip={slip_pct:.3f}%"
            )
            
            await self.cancel_order(order.order_id, "unfilled_repost")
            
            # Place new order with slip
            new_order = await self.place_post_only_order(
                symbol=order.symbol,
                side=order.side,
                quantity=order.quantity - order.filled_quantity,
                best_bid=best_bid if order.side == OrderSide.LONG else best_bid,
                best_ask=best_ask if order.side == OrderSide.SHORT else best_ask,
                spread_bps=0.0,  # Will be recalculated
                reduce_only=order.reduce_only
            )
            new_order.price = new_price
            order = new_order
        
        # Max attempts reached
        if is_urgent:
            # Use market order as fallback
            result['reason'] = 'urgent_market_fallback'
            logger.warning(
                f"Unfilled protocol: Max attempts reached, using market order "
                f"(urgent=True)"
            )
            # Place market order (simulated)
            order.order_type = OrderType.MARKET
            order.status = OrderStatus.FILLED
            result['filled'] = True
            result['final_order'] = order
        else:
            result['reason'] = 'max_attempts_reached'
            logger.warning(
                f"Unfilled protocol: Max attempts reached, abandoning order"
            )
            await self.cancel_order(order.order_id, "max_attempts_reached")
        
        return result
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID."""
        return self.orders.get(order_id)
    
    def get_active_orders(self) -> List[Order]:
        """Get all active orders."""
        return [self.orders[oid] for oid in self.active_orders if oid in self.orders]
    
    def get_order_history(self, limit: int = 100) -> List[Order]:
        """Get order history."""
        all_orders = sorted(
            self.orders.values(),
            key=lambda o: o.created_at,
            reverse=True
        )
        return all_orders[:limit]
