"""
Backtesting engine for swing trading strategy.
Simulates trades with stop loss/take profit ladder and trailing stop.
"""
from dataclasses import dataclass, field

import pandas as pd


@dataclass
class Trade:
    """Represents a single trade."""
    entry_idx: int
    entry_timestamp: any
    entry_price: float
    direction: str  # 'long' or 'short'
    size: float = 1.0
    
    # Stop loss and take profit levels
    initial_sl: float = 0.0
    current_sl: float = 0.0
    tp1: float = 0.0
    tp2: float = 0.0
    tp3: float = 0.0
    
    # Trade state
    status: str = 'open'  # 'open', 'closed'
    exit_idx: int | None = None
    exit_timestamp: any | None = None
    exit_price: float | None = None
    exit_reason: str | None = None
    
    # Position sizing
    position_remaining: float = 1.0  # Percentage remaining (0.0 to 1.0)
    
    # Performance
    pnl_pct: float = 0.0
    pnl_r: float = 0.0  # PnL in R multiples
    bars_held: int = 0
    
    # Partial exits
    partial_exits: list[dict] = field(default_factory=list)
    
    def add_partial_exit(self, price: float, pct_closed: float, reason: str):
        """Record a partial position exit."""
        self.partial_exits.append({
            'price': price,
            'pct_closed': pct_closed,
            'reason': reason
        })
        self.position_remaining -= pct_closed


class BacktestEngine:
    """
    Backtesting engine with position sizing, TP ladder, and trailing stop.
    """
    
    def __init__(self,
                 initial_capital: float = 10000.0,
                 risk_per_trade: float = 0.02,
                 tp1_r: float = 1.0,
                 tp2_r: float = 2.0,
                 tp3_r: float = 3.5,
                 tp1_scale: float = 0.5,
                 tp2_scale: float = 0.3,
                 trail_atr_multiplier: float = 0.5):
        """
        Initialize backtest engine.
        
        Args:
            initial_capital: Starting capital
            risk_per_trade: Risk per trade as fraction of capital (e.g., 0.02 = 2%)
            tp1_r: First TP in R multiples
            tp2_r: Second TP in R multiples
            tp3_r: Third TP in R multiples
            tp1_scale: Percentage to close at TP1 (e.g., 0.5 = 50%)
            tp2_scale: Percentage to close at TP2
            trail_atr_multiplier: Trailing stop ATR multiplier
        """
        self.initial_capital = initial_capital
        self.risk_per_trade = risk_per_trade
        self.tp1_r = tp1_r
        self.tp2_r = tp2_r
        self.tp3_r = tp3_r
        self.tp1_scale = tp1_scale
        self.tp2_scale = tp2_scale
        self.trail_atr_multiplier = trail_atr_multiplier
        
        self.capital = initial_capital
        self.trades: list[Trade] = []
        self.open_trades: list[Trade] = []
    
    def calculate_stop_loss(self, df: pd.DataFrame, entry_idx: int, 
                           entry_price: float, direction: str,
                           local_price: float, atr5: float) -> float:
        """
        Calculate initial stop loss.
        
        Args:
            df: Price DataFrame
            entry_idx: Entry bar index
            entry_price: Entry price
            direction: 'long' or 'short'
            local_price: Local extrema price (low for longs, high for shorts)
            atr5: ATR5 value
        
        Returns:
            Stop loss price
        """
        if direction == 'long':
            # SL below local low - 0.9 * ATR5
            sl = local_price - (0.9 * atr5)
        else:
            # SL above local high + 0.9 * ATR5
            sl = local_price + (0.9 * atr5)
        
        return sl
    
    def calculate_take_profits(self, entry_price: float, sl_price: float, direction: str) -> dict[str, float]:
        """
        Calculate TP levels based on R multiples.
        
        Args:
            entry_price: Entry price
            sl_price: Stop loss price
            direction: 'long' or 'short'
        
        Returns:
            Dict with TP1, TP2, TP3 prices
        """
        risk_distance = abs(entry_price - sl_price)
        
        if direction == 'long':
            tp1 = entry_price + (risk_distance * self.tp1_r)
            tp2 = entry_price + (risk_distance * self.tp2_r)
            tp3 = entry_price + (risk_distance * self.tp3_r)
        else:
            tp1 = entry_price - (risk_distance * self.tp1_r)
            tp2 = entry_price - (risk_distance * self.tp2_r)
            tp3 = entry_price - (risk_distance * self.tp3_r)
        
        return {'tp1': tp1, 'tp2': tp2, 'tp3': tp3}
    
    def open_trade(self, df: pd.DataFrame, signal: dict) -> Trade:
        """
        Open a new trade based on confirmed signal.
        
        Args:
            df: Price DataFrame
            signal: Signal dictionary with entry details
        
        Returns:
            Trade object
        """
        entry_idx = signal['confirmation_idx']
        entry_price = signal['entry_price']
        direction = signal['direction']
        
        # Get bar data
        entry_bar = df.loc[entry_idx]
        
        # Calculate SL
        if direction == 'long':
            local_price = signal['local_low']
        else:
            local_price = signal['local_high']
        
        sl_price = self.calculate_stop_loss(
            df, entry_idx, entry_price, direction, 
            local_price, signal['ATR5']
        )
        
        # Calculate TPs
        tps = self.calculate_take_profits(entry_price, sl_price, direction)
        
        # Create trade
        trade = Trade(
            entry_idx=entry_idx,
            entry_timestamp=entry_bar.get('time', entry_idx),
            entry_price=entry_price,
            direction=direction,
            initial_sl=sl_price,
            current_sl=sl_price,
            tp1=tps['tp1'],
            tp2=tps['tp2'],
            tp3=tps['tp3']
        )
        
        self.trades.append(trade)
        self.open_trades.append(trade)
        
        return trade
    
    def update_trailing_stop(self, trade: Trade, current_price: float, atr5: float):
        """
        Update trailing stop after TP1 is hit.
        
        Args:
            trade: Trade object
            current_price: Current price
            atr5: Current ATR5
        """
        trail_distance = atr5 * self.trail_atr_multiplier
        
        if trade.direction == 'long':
            new_sl = current_price - trail_distance
            # Only move SL up, never down
            if new_sl > trade.current_sl:
                trade.current_sl = new_sl
        else:
            new_sl = current_price + trail_distance
            # Only move SL down, never up
            if new_sl < trade.current_sl:
                trade.current_sl = new_sl
    
    def check_exit(self, df: pd.DataFrame, trade: Trade, bar_idx: int) -> str | None:
        """
        Check if trade should be exited on current bar.
        
        Args:
            df: Price DataFrame
            trade: Trade object
            bar_idx: Current bar index (position)
        
        Returns:
            Exit reason if exit triggered, None otherwise
        """
        bar = df.iloc[bar_idx]
        bar_idx_label = df.index[bar_idx]
        high = bar['high']
        low = bar['low']
        close = bar['close']
        atr5 = bar.get('ATR5', 0)
        
        tp1_hit = False
        
        if trade.direction == 'long':
            # Check stop loss
            if low <= trade.current_sl:
                trade.exit_price = trade.current_sl
                trade.exit_idx = bar_idx_label
                trade.exit_timestamp = bar.get('time', bar_idx_label)
                return 'stop_loss'
            
            # Check TP1
            if high >= trade.tp1 and trade.position_remaining == 1.0:
                trade.add_partial_exit(trade.tp1, self.tp1_scale, 'TP1')
                # Move SL to breakeven + fees
                trade.current_sl = trade.entry_price * 1.001  # BE + 0.1% for fees
                tp1_hit = True
            
            # Check TP2
            if high >= trade.tp2 and trade.position_remaining > (1.0 - self.tp1_scale) and trade.position_remaining < 1.0:
                trade.add_partial_exit(trade.tp2, self.tp2_scale, 'TP2')
            
            # Check TP3 (close remaining)
            if high >= trade.tp3 and trade.position_remaining > 0:
                trade.exit_price = trade.tp3
                trade.exit_idx = bar_idx_label
                trade.exit_timestamp = bar.get('time', bar_idx_label)
                return 'tp3'
            
            # Update trailing stop after TP1
            if trade.position_remaining < 1.0 and atr5 > 0:
                self.update_trailing_stop(trade, close, atr5)
        
        else:  # short
            # Check stop loss
            if high >= trade.current_sl:
                trade.exit_price = trade.current_sl
                trade.exit_idx = bar_idx_label
                trade.exit_timestamp = bar.get('time', bar_idx_label)
                return 'stop_loss'
            
            # Check TP1
            if low <= trade.tp1 and trade.position_remaining == 1.0:
                trade.add_partial_exit(trade.tp1, self.tp1_scale, 'TP1')
                # Move SL to breakeven + fees
                trade.current_sl = trade.entry_price * 0.999
                tp1_hit = True
            
            # Check TP2
            if low <= trade.tp2 and trade.position_remaining > (1.0 - self.tp1_scale) and trade.position_remaining < 1.0:
                trade.add_partial_exit(trade.tp2, self.tp2_scale, 'TP2')
            
            # Check TP3 (close remaining)
            if low <= trade.tp3 and trade.position_remaining > 0:
                trade.exit_price = trade.tp3
                trade.exit_idx = bar_idx_label
                trade.exit_timestamp = bar.get('time', bar_idx_label)
                return 'tp3'
            
            # Update trailing stop after TP1
            if trade.position_remaining < 1.0 and atr5 > 0:
                self.update_trailing_stop(trade, close, atr5)
        
        return None
    
    def close_trade(self, trade: Trade, exit_reason: str):
        """
        Close a trade and calculate PnL.
        
        Args:
            trade: Trade object
            exit_reason: Reason for exit
        """
        trade.status = 'closed'
        trade.exit_reason = exit_reason
        
        # Calculate bars held
        if hasattr(self, 'df') and trade.exit_idx is not None:
            try:
                trade.bars_held = self.df.index.get_loc(trade.exit_idx) - self.df.index.get_loc(trade.entry_idx)
            except:
                trade.bars_held = 0
        else:
            trade.bars_held = 0
        
        # Calculate PnL
        if trade.direction == 'long':
            # Weighted average exit price
            total_pnl_pct = 0
            for partial in trade.partial_exits:
                pnl = ((partial['price'] - trade.entry_price) / trade.entry_price) * 100
                total_pnl_pct += pnl * partial['pct_closed']
            
            # Remaining position
            if trade.position_remaining > 0 and trade.exit_price:
                pnl = ((trade.exit_price - trade.entry_price) / trade.entry_price) * 100
                total_pnl_pct += pnl * trade.position_remaining
            
            trade.pnl_pct = total_pnl_pct
        else:
            total_pnl_pct = 0
            for partial in trade.partial_exits:
                pnl = ((trade.entry_price - partial['price']) / trade.entry_price) * 100
                total_pnl_pct += pnl * partial['pct_closed']
            
            if trade.position_remaining > 0 and trade.exit_price:
                pnl = ((trade.entry_price - trade.exit_price) / trade.entry_price) * 100
                total_pnl_pct += pnl * trade.position_remaining
            
            trade.pnl_pct = total_pnl_pct
        
        # Calculate R multiple
        risk_pct = abs((trade.entry_price - trade.initial_sl) / trade.entry_price) * 100
        trade.pnl_r = trade.pnl_pct / risk_pct if risk_pct > 0 else 0
        
        # Remove from open trades
        if trade in self.open_trades:
            self.open_trades.remove(trade)
    
    def run_backtest(self, df: pd.DataFrame, confirmed_signals: list[dict]) -> dict:
        """
        Run complete backtest on confirmed signals.
        
        Args:
            df: Price DataFrame with indicators
            confirmed_signals: List of confirmed signal dictionaries
        
        Returns:
            Dict with backtest results and statistics
        """
        self.df = df  # Store for reference
        
        # Sort signals by confirmation index
        signals = sorted(confirmed_signals, key=lambda x: x['confirmation_idx'])
        
        # Track signal index for processing
        signal_idx = 0
        
        # Iterate through each bar
        for bar_pos in range(len(df)):
            bar_idx = df.index[bar_pos]
            
            # Open new trades if signal matches current bar
            while signal_idx < len(signals):
                signal = signals[signal_idx]
                if signal['confirmation_idx'] == bar_idx:
                    self.open_trade(df, signal)
                    signal_idx += 1
                elif df.index.get_loc(signal['confirmation_idx']) > bar_pos:
                    break
                else:
                    signal_idx += 1
            
            # Update open trades
            for trade in self.open_trades[:]:  # Copy list to allow modification
                exit_reason = self.check_exit(df, trade, bar_pos)
                if exit_reason:
                    self.close_trade(trade, exit_reason)
        
        # Close any remaining open trades at end of data
        for trade in self.open_trades[:]:
            last_bar = df.iloc[-1]
            trade.exit_price = last_bar['close']
            trade.exit_idx = df.index[-1]
            trade.exit_timestamp = last_bar.get('time', df.index[-1])
            self.close_trade(trade, 'end_of_data')
        
        # Calculate statistics
        return self.calculate_statistics()
    
    def calculate_statistics(self) -> dict:
        """
        Calculate backtest performance statistics.
        
        Returns:
            Dict with performance metrics
        """
        if not self.trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'avg_pnl_pct': 0,
                'avg_r': 0,
                'profit_factor': 0,
                'total_pnl_pct': 0
            }
        
        wins = [t for t in self.trades if t.pnl_pct > 0]
        losses = [t for t in self.trades if t.pnl_pct <= 0]
        
        total_win_pct = sum(t.pnl_pct for t in wins) if wins else 0
        total_loss_pct = abs(sum(t.pnl_pct for t in losses)) if losses else 0
        
        stats = {
            'total_trades': len(self.trades),
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': (len(wins) / len(self.trades) * 100) if self.trades else 0,
            'avg_win': (total_win_pct / len(wins)) if wins else 0,
            'avg_loss': (total_loss_pct / len(losses)) if losses else 0,
            'avg_pnl_pct': sum(t.pnl_pct for t in self.trades) / len(self.trades),
            'avg_r': sum(t.pnl_r for t in self.trades) / len(self.trades),
            'profit_factor': (total_win_pct / total_loss_pct) if total_loss_pct > 0 else 0,
            'total_pnl_pct': sum(t.pnl_pct for t in self.trades),
            'avg_bars_held': sum(t.bars_held for t in self.trades) / len(self.trades) if self.trades else 0,
            'max_pnl_pct': max(t.pnl_pct for t in self.trades) if self.trades else 0,
            'min_pnl_pct': min(t.pnl_pct for t in self.trades) if self.trades else 0
        }
        
        return stats
    
    def get_trades_df(self) -> pd.DataFrame:
        """
        Convert trades to DataFrame for analysis.
        
        Returns:
            DataFrame with trade details
        """
        if not self.trades:
            return pd.DataFrame()
        
        trades_data = []
        for trade in self.trades:
            trades_data.append({
                'entry_timestamp': trade.entry_timestamp,
                'entry_price': trade.entry_price,
                'exit_timestamp': trade.exit_timestamp,
                'exit_price': trade.exit_price,
                'direction': trade.direction,
                'exit_reason': trade.exit_reason,
                'pnl_pct': trade.pnl_pct,
                'pnl_r': trade.pnl_r,
                'bars_held': trade.bars_held,
                'partial_exits': len(trade.partial_exits)
            })
        
        return pd.DataFrame(trades_data)
