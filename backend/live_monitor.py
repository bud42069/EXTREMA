"""
Live price monitoring and signal generation using Pyth Network.
Monitors SOL/USD and generates real-time swing signals.
"""
import asyncio
import aiohttp
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Optional, Deque
from collections import deque
import logging
from dataclasses import dataclass, asdict

from indicators import calculate_atr, calculate_rsi, calculate_bollinger_bands, calculate_ema, calculate_volume_zscore
from extrema_detection import detect_local_extrema
from signal_detection import TwoStageDetector
from mtf_confirmation import MultiTimeframeAnalyzer
from onchain_monitor import HeliusOnChainMonitor

logger = logging.getLogger(__name__)


@dataclass
class Candle:
    """5-minute OHLCV candle."""
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class SignalCard:
    """
    Swing Capture Scalp Card - matches user template.
    """
    # Header
    symbol: str = "SOLUSDT"
    exchange: str = "MEXC"
    play_type: str = ""  # Trend Continuation | Reversal Reclaim | Breakout Expansion | Mean Reversion
    bias: str = ""  # Long | Short
    regime: str = ""  # S (Squeeze) | N (Normal) | W (Wide)
    tier: str = ""  # A | B
    
    # Entry Plan
    trigger_zone: float = 0.0
    entry_trigger: str = ""
    entry_price: float = 0.0
    sl_placement: float = 0.0
    
    # Target Ladder
    tp1_price: float = 0.0
    tp1_allocation: float = 50.0
    tp2_price: float = 0.0
    tp2_allocation: float = 30.0
    tp3_price: float = 0.0
    tp3_allocation: float = 20.0
    
    # Structure & Confluence
    ema_alignment: bool = False
    oscillator_agreement: bool = False
    supply_demand_valid: bool = False
    vwap_structure: bool = False
    volume_behavior: bool = False
    confluence_score: float = 0.0
    
    # Indicators
    atr14: float = 0.0
    atr5: float = 0.0
    rsi14: float = 0.0
    bb_width: float = 0.0
    volume_zscore: float = 0.0
    
    # Metadata
    signal_time: str = ""
    signal_id: str = ""
    status: str = "ACTIVE"  # ACTIVE | FILLED | STOPPED


class LiveMonitor:
    """
    Live monitoring system for SOL price action.
    Uses Pyth Network for price feeds.
    """
    
    def __init__(self, 
                 candle_window: int = 500,
                 atr_threshold: float = 0.6,
                 vol_z_threshold: float = 0.5,
                 bb_width_threshold: float = 0.005,
                 helius_api_key: Optional[str] = None):
        """
        Initialize live monitor.
        
        Args:
            candle_window: Number of candles to maintain in memory
            atr_threshold: ATR threshold for candidate detection
            vol_z_threshold: Volume z-score threshold
            bb_width_threshold: BB width threshold
            helius_api_key: Optional Helius API key for on-chain monitoring
        """
        self.candle_window = candle_window
        self.candles: Deque[Candle] = deque(maxlen=candle_window)
        
        # Pyth price feed ID for SOL/USD
        # https://pyth.network/price-feeds
        self.sol_price_feed_id = "0xef0d8b6fda2ceba41da15d4095d1da392a0d2f8ed0c6c7bc0f4cfac8c280b56d"
        
        # Signal detector
        self.detector = TwoStageDetector(
            atr_threshold=atr_threshold,
            vol_z_threshold=vol_z_threshold,
            bb_width_threshold=bb_width_threshold,
            confirmation_window=6,
            atr_multiplier=0.5,
            volume_multiplier=1.5
        )
        
        # Multi-timeframe analyzer
        self.mtf_analyzer = MultiTimeframeAnalyzer()
        
        # On-chain monitor (if API key provided)
        self.onchain_monitor = None
        if helius_api_key:
            self.onchain_monitor = HeliusOnChainMonitor(helius_api_key)
            logger.info("Helius on-chain monitor initialized")
        
        # Signal storage
        self.active_signals: List[SignalCard] = []
        self.signal_callbacks: List[callable] = []
        
        # State
        self.running = False
        self.last_price = 0.0
        
    def register_signal_callback(self, callback: callable):
        """Register callback to be called when new signal is generated."""
        self.signal_callbacks.append(callback)
    
    async def fetch_pyth_price(self) -> Optional[float]:
        """
        Fetch current SOL/USD price from Pyth Network Hermes API.
        
        Returns:
            Current price or None if error
        """
        try:
            # Pyth Hermes API endpoint
            url = f"https://hermes.pyth.network/api/latest_price_feeds?ids[]={self.sol_price_feed_id}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data and len(data) > 0:
                            price_data = data[0]
                            price = float(price_data['price']['price'])
                            expo = int(price_data['price']['expo'])
                            
                            # Adjust for exponent (Pyth uses integer with exponent)
                            actual_price = price * (10 ** expo)
                            return actual_price
            
            return None
        
        except Exception as e:
            logger.error(f"Error fetching Pyth price: {e}")
            return None
    
    async def build_5min_candle(self) -> Optional[Candle]:
        """
        Build a 5-minute candle from tick data.
        In production, you'd aggregate ticks. For now, we'll use current price.
        
        Returns:
            5-minute candle
        """
        try:
            # Fetch current price
            price = await self.fetch_pyth_price()
            
            if price is None:
                return None
            
            # Get current 5-min timestamp (round down to nearest 5 min)
            now = datetime.now(timezone.utc)
            timestamp = int(now.timestamp())
            timestamp = (timestamp // 300) * 300  # Round to 5-min
            
            # If this is a new candle period
            if not self.candles or self.candles[-1].timestamp < timestamp:
                # Create new candle
                candle = Candle(
                    timestamp=timestamp,
                    open=price,
                    high=price,
                    low=price,
                    close=price,
                    volume=0.0  # We don't have volume from Pyth, set to 0 or estimate
                )
                return candle
            else:
                # Update existing candle
                last_candle = self.candles[-1]
                last_candle.high = max(last_candle.high, price)
                last_candle.low = min(last_candle.low, price)
                last_candle.close = price
                return None  # No new candle yet
        
        except Exception as e:
            logger.error(f"Error building candle: {e}")
            return None
    
    def candles_to_dataframe(self) -> pd.DataFrame:
        """Convert candles deque to DataFrame."""
        if not self.candles:
            return pd.DataFrame()
        
        data = []
        for candle in self.candles:
            data.append({
                'time': candle.timestamp,
                'open': candle.open,
                'high': candle.high,
                'low': candle.low,
                'close': candle.close,
                'Volume': candle.volume if candle.volume > 0 else 1.0  # Default to 1 if no volume
            })
        
        return pd.DataFrame(data)
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators."""
        if len(df) < 50:
            return df
        
        try:
            # ATR
            df['ATR14'] = calculate_atr(df, period=14)
            df['ATR5'] = calculate_atr(df, period=5)
            
            # RSI
            df['RSI14'] = calculate_rsi(df, period=14)
            
            # Bollinger Bands
            upper, middle, lower, bb_width = calculate_bollinger_bands(df, period=20)
            df['BB_Upper'] = upper
            df['BB_Middle'] = middle
            df['BB_Lower'] = lower
            df['BB_Width'] = bb_width
            
            # EMA
            df['EMA20'] = calculate_ema(df, period=20)
            
            # Volume Z-Score (use synthetic if no volume)
            if df['Volume'].sum() > 0:
                df['Volume_ZScore'] = calculate_volume_zscore(df, period=50)
            else:
                df['Volume_ZScore'] = 0.0
            
            return df
        
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return df
    
    def determine_play_type(self, df: pd.DataFrame, idx: int, direction: str) -> str:
        """
        Determine play type based on price action.
        
        Returns:
            Play type string
        """
        if len(df) < 20:
            return "Unknown"
        
        row = df.iloc[idx]
        ema20 = row.get('EMA20', 0)
        close = row['close']
        bb_width = row.get('BB_Width', 0)
        
        if bb_width < 0.01:
            return "Breakout Expansion"
        elif direction == 'long' and close < ema20:
            return "Reversal Reclaim"
        elif direction == 'short' and close > ema20:
            return "Reversal Reclaim"
        else:
            return "Trend Continuation"
    
    def determine_regime(self, bb_width: float) -> str:
        """
        Determine market regime from BB width.
        
        Returns:
            S (Squeeze) | N (Normal) | W (Wide)
        """
        if bb_width < 0.01:
            return "S"
        elif bb_width > 0.02:
            return "W"
        else:
            return "N"
    
    def calculate_confluence(self, row: pd.Series, direction: str) -> Dict:
        """
        Calculate confluence score and component checks.
        
        Returns:
            Dict with confluence info
        """
        checks = {
            'ema_alignment': False,
            'oscillator_agreement': False,
            'supply_demand_valid': True,  # Assume true for now
            'vwap_structure': True,  # Assume true for now
            'volume_behavior': False
        }
        
        # EMA alignment
        close = row['close']
        ema20 = row.get('EMA20', close)
        if direction == 'long' and close > ema20:
            checks['ema_alignment'] = True
        elif direction == 'short' and close < ema20:
            checks['ema_alignment'] = True
        
        # Oscillator (RSI)
        rsi = row.get('RSI14', 50)
        if direction == 'long' and rsi > 50:
            checks['oscillator_agreement'] = True
        elif direction == 'short' and rsi < 50:
            checks['oscillator_agreement'] = True
        
        # Volume
        vol_z = row.get('Volume_ZScore', 0)
        if vol_z > 0.5:
            checks['volume_behavior'] = True
        
        # Calculate score (equal weights)
        score = sum(checks.values()) / len(checks) * 100
        
        return {**checks, 'confluence_score': score}
    
    def create_signal_card(self, signal: Dict, df: pd.DataFrame) -> SignalCard:
        """
        Create a scalp card from detected signal.
        
        Args:
            signal: Signal dictionary from detector
            df: Full DataFrame with indicators
        
        Returns:
            SignalCard object
        """
        direction = signal['direction']
        entry_price = signal['entry_price']
        
        # Get indicator values
        signal_idx = df.index.get_loc(signal['index'])
        row = df.iloc[signal_idx]
        
        # Calculate SL
        atr5 = row.get('ATR5', 0)
        if direction == 'long':
            sl = signal['local_low'] - (0.9 * atr5)
        else:
            sl = signal['local_high'] + (0.9 * atr5)
        
        # Calculate risk distance
        risk = abs(entry_price - sl)
        
        # Calculate TPs (1R, 2R, 3.5R)
        if direction == 'long':
            tp1 = entry_price + (risk * 1.0)
            tp2 = entry_price + (risk * 2.0)
            tp3 = entry_price + (risk * 3.5)
        else:
            tp1 = entry_price - (risk * 1.0)
            tp2 = entry_price - (risk * 2.0)
            tp3 = entry_price - (risk * 3.5)
        
        # Determine play characteristics
        play_type = self.determine_play_type(df, signal_idx, direction)
        regime = self.determine_regime(row.get('BB_Width', 0.01))
        
        # Calculate confluence
        confluence = self.calculate_confluence(row, direction)
        tier = "A" if confluence['confluence_score'] >= 60 else "B"
        
        # Create signal card
        card = SignalCard(
            play_type=play_type,
            bias=direction.upper(),
            regime=regime,
            tier=tier,
            trigger_zone=entry_price,
            entry_trigger=f"close {'≥' if direction == 'long' else '≤'} {entry_price:.2f}",
            entry_price=entry_price,
            sl_placement=sl,
            tp1_price=tp1,
            tp2_price=tp2,
            tp3_price=tp3,
            ema_alignment=confluence['ema_alignment'],
            oscillator_agreement=confluence['oscillator_agreement'],
            supply_demand_valid=confluence['supply_demand_valid'],
            vwap_structure=confluence['vwap_structure'],
            volume_behavior=confluence['volume_behavior'],
            confluence_score=confluence['confluence_score'],
            atr14=row.get('ATR14', 0),
            atr5=row.get('ATR5', 0),
            rsi14=row.get('RSI14', 50),
            bb_width=row.get('BB_Width', 0),
            volume_zscore=row.get('Volume_ZScore', 0),
            signal_time=datetime.now(timezone.utc).isoformat(),
            signal_id=f"SOL-{int(datetime.now().timestamp())}-{direction[:1].upper()}"
        )
        
        return card
    
    async def check_for_signals(self):
        """Check if new signals should be generated."""
        try:
            # Need minimum candles for analysis
            if len(self.candles) < 100:
                return
            
            # Convert to DataFrame
            df = self.candles_to_dataframe()
            
            # Calculate indicators
            df = self.calculate_indicators(df)
            
            # Detect extrema
            minima_mask, maxima_mask = detect_local_extrema(df, window=12)
            
            # Run two-stage detection
            results = self.detector.detect_signals(df, minima_mask, maxima_mask)
            
            # Process confirmed signals
            confirmed_longs = results['confirmed_longs']
            confirmed_shorts = results['confirmed_shorts']
            
            all_signals = []
            if not confirmed_longs.empty:
                all_signals.extend(confirmed_longs.to_dict('records'))
            if not confirmed_shorts.empty:
                all_signals.extend(confirmed_shorts.to_dict('records'))
            
            # Generate signal cards for new signals
            for signal in all_signals:
                # Check if this is a new signal (confirmed on last candle)
                if signal['confirmation_idx'] == df.index[-1]:
                    card = self.create_signal_card(signal, df)
                    self.active_signals.append(card)
                    
                    # Notify callbacks
                    for callback in self.signal_callbacks:
                        try:
                            await callback(card)
                        except Exception as e:
                            logger.error(f"Error in signal callback: {e}")
                    
                    logger.info(f"New signal generated: {card.signal_id} - {card.bias} @ {card.entry_price}")
        
        except Exception as e:
            logger.error(f"Error checking for signals: {e}")
    
    async def start(self):
        """Start live monitoring."""
        self.running = True
        logger.info("Live monitor started")
        
        while self.running:
            try:
                # Build 5-min candle
                new_candle = await self.build_5min_candle()
                
                if new_candle:
                    self.candles.append(new_candle)
                    logger.info(f"New candle: {new_candle.timestamp} | Close: {new_candle.close:.2f}")
                    
                    # Check for signals on new candle
                    await self.check_for_signals()
                
                # Update every 10 seconds
                await asyncio.sleep(10)
            
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                await asyncio.sleep(5)
    
    def stop(self):
        """Stop live monitoring."""
        self.running = False
        logger.info("Live monitor stopped")
    
    def get_active_signals(self) -> List[Dict]:
        """Get all active signals as dictionaries."""
        return [asdict(card) for card in self.active_signals]
