"""
Multi-Timeframe State Machine.
Implements 6-state flow: Scan → Candidate → Micro Confirm → Execute → Manage → Post-trade
"""
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List
from enum import Enum
import pandas as pd

from ..utils.logging import get_logger
from ..utils.mtf_store import get_klines
from ..utils.micro_store import get_snapshot
from .mtf_features import extract_mtf_features
from .mtf_confluence import confluence_engine
from .extrema import label_swings
from .indicators import compute_indicators

logger = get_logger(__name__)


class MTFState(Enum):
    """State machine states."""
    SCAN = "scan"
    CANDIDATE = "candidate"
    MICRO_CONFIRM = "micro_confirm"
    EXECUTE = "execute"
    MANAGE = "manage"
    POST_TRADE = "post_trade"


class Candidate:
    """Candidate signal structure."""
    def __init__(
        self,
        timestamp: int,
        index: int,
        side: str,  # 'long' or 'short'
        price: float,
        extremum_type: str  # 'min' or 'max'
    ):
        self.timestamp = timestamp
        self.index = index
        self.side = side
        self.price = price
        self.extremum_type = extremum_type
        self.created_at = datetime.now(timezone.utc)
        self.timeout_minutes = 30
        self.micro_confirmed = False
        self.confluence_score = None
        
    def is_expired(self) -> bool:
        """Check if candidate has exceeded timeout."""
        elapsed = (datetime.now(timezone.utc) - self.created_at).total_seconds() / 60
        return elapsed > self.timeout_minutes


class MTFStateMachine:
    """
    Multi-Timeframe State Machine for signal generation.
    Implements anti-whipsaw hygiene with hysteresis and timeouts.
    """
    
    def __init__(self):
        self.state = MTFState.SCAN
        self.candidate: Optional[Candidate] = None
        self.active_position: Optional[Dict] = None
        
        # Configuration
        self.candidate_params = {
            'atr_min': 0.6,
            'volz_min': 0.5,
            'bbw_min': 0.005,
            'extrema_window': 12
        }
        
        # Hysteresis for micro conditions (n-of-m passes)
        self.hysteresis_window = 10  # Last 10 seconds
        self.hysteresis_threshold = 8  # 8 of 10 must pass
        self.micro_checks_history = []
        
        # Invalidated candidates (one-way valve)
        self.invalidated_candidates = {}  # {index: timestamp}
        self.invalidation_cooldown = 15 * 60  # 15 minutes in seconds
        
        # Statistics
        self.stats = {
            'candidates_detected': 0,
            'candidates_expired': 0,
            'micro_confirms': 0,
            'micro_rejects': 0,
            'executions': 0,
            'vetoes': 0
        }
    
    async def scan(self, df_5m: pd.DataFrame) -> Optional[Candidate]:
        """
        State 0: Scan for candidates on 5m timeframe.
        
        Args:
            df_5m: 5-minute DataFrame
        
        Returns:
            Candidate if detected, None otherwise
        """
        if df_5m is None or len(df_5m) < 50:
            return None
        
        try:
            # Compute indicators
            df_with_indicators = compute_indicators(df_5m)
            
            # Label swings
            df_with_swings = label_swings(df_with_indicators)
            
            # Find local extrema (±12 bars)
            window = self.candidate_params['extrema_window']
            
            for i in range(len(df_with_swings) - window, len(df_with_swings)):
                if i < window or i >= len(df_with_swings):
                    continue
                
                # Check if this is a local minimum (long candidate)
                is_min = True
                for j in range(i - window, i + window + 1):
                    if j != i and df_with_swings.at[j, 'low'] <= df_with_swings.at[i, 'low']:
                        is_min = False
                        break
                
                # Check if this is a local maximum (short candidate)
                is_max = True
                for j in range(i - window, i + window + 1):
                    if j != i and df_with_swings.at[j, 'high'] >= df_with_swings.at[i, 'high']:
                        is_max = False
                        break
                
                if not is_min and not is_max:
                    continue
                
                # Check if already invalidated
                if i in self.invalidated_candidates:
                    invalidated_time = self.invalidated_candidates[i]
                    if (datetime.now(timezone.utc).timestamp() - invalidated_time) < self.invalidation_cooldown:
                        continue  # Still in cooldown
                
                # Apply candidate filters (ATR, volume z-score, BB width)
                atr = df_with_swings.at[i, 'ATR14']
                vol_z = df_with_swings.at[i, 'volume_zscore']
                bbw = df_with_swings.at[i, 'BBWidth']
                
                if (atr >= self.candidate_params['atr_min'] and
                    vol_z >= self.candidate_params['volz_min'] and
                    bbw >= self.candidate_params['bbw_min']):
                    
                    # Create candidate
                    side = 'long' if is_min else 'short'
                    price = df_with_swings.at[i, 'low'] if is_min else df_with_swings.at[i, 'high']
                    
                    candidate = Candidate(
                        timestamp=int(df_with_swings.index[i].timestamp()),
                        index=i,
                        side=side,
                        price=price,
                        extremum_type='min' if is_min else 'max'
                    )
                    
                    self.stats['candidates_detected'] += 1
                    logger.info(f"Candidate detected: {side} at {price} (index {i})")
                    
                    return candidate
            
            return None
        
        except Exception as e:
            logger.error(f"Error in scan state: {e}")
            return None
    
    async def micro_confirm(self, candidate: Candidate) -> Dict:
        """
        State 2: Micro Confirm - validate with 1s/5s/1m conditions.
        
        Args:
            candidate: Candidate to validate
        
        Returns:
            Dict with confirmation result and confluence scores
        """
        if candidate is None:
            return {'confirmed': False, 'reason': 'no_candidate'}
        
        # Check timeout
        if candidate.is_expired():
            self.stats['candidates_expired'] += 1
            logger.info(f"Candidate expired: {candidate.side} at {candidate.price}")
            return {'confirmed': False, 'reason': 'timeout'}
        
        try:
            # Extract features from all timeframes
            features_1s = None
            features_5s = None
            features_1m = None
            features_5m = None
            
            # Get klines for each TF
            klines_1s = get_klines("1s", limit=100)
            klines_5s = get_klines("5s", limit=100)
            klines_1m = get_klines("1m", limit=100)
            klines_5m = get_klines("5m", limit=100)
            
            # Convert to DataFrames and extract features
            if klines_1s and len(klines_1s) >= 50:
                df_1s = pd.DataFrame(klines_1s)
                df_1s['time'] = pd.to_datetime(df_1s['timestamp'], unit='s')
                df_1s.set_index('time', inplace=True)
                features_1s = extract_mtf_features(df_1s, '1s')
            
            if klines_5s and len(klines_5s) >= 50:
                df_5s = pd.DataFrame(klines_5s)
                df_5s['time'] = pd.to_datetime(df_5s['timestamp'], unit='s')
                df_5s.set_index('time', inplace=True)
                features_5s = extract_mtf_features(df_5s, '5s')
            
            if klines_1m and len(klines_1m) >= 50:
                df_1m = pd.DataFrame(klines_1m)
                df_1m['time'] = pd.to_datetime(df_1m['timestamp'], unit='s')
                df_1m.set_index('time', inplace=True)
                features_1m = extract_mtf_features(df_1m, '1m')
            
            if klines_5m and len(klines_5m) >= 50:
                df_5m = pd.DataFrame(klines_5m)
                df_5m['time'] = pd.to_datetime(df_5m['timestamp'], unit='s')
                df_5m.set_index('time', inplace=True)
                features_5m = extract_mtf_features(df_5m, '5m')
            
            # Get microstructure snapshot
            micro_snapshot = get_snapshot()
            
            # Get higher TF features (for now, use placeholders)
            # TODO: Fetch 15m/1h/4h/1D from REST API
            features_15m = None
            features_1h = None
            features_4h = None
            features_1d = None
            
            # Compute confluence
            confluence_result = confluence_engine.evaluate(
                features_1s=features_1s,
                features_5s=features_5s,
                features_1m=features_1m,
                features_5m=features_5m,
                features_15m=features_15m,
                features_1h=features_1h,
                features_4h=features_4h,
                features_1d=features_1d,
                micro_snapshot=micro_snapshot
            )
            
            # Check if confluence allows entry
            final_score = confluence_result['final']
            
            if final_score['allow_entry']:
                self.stats['micro_confirms'] += 1
                candidate.micro_confirmed = True
                candidate.confluence_score = final_score
                
                logger.info(f"Micro confirmed: {candidate.side} - Tier {final_score['tier']}, Score {final_score['final_score']:.1f}")
                
                return {
                    'confirmed': True,
                    'tier': final_score['tier'],
                    'confluence': confluence_result,
                    'size_multiplier': final_score['size_multiplier']
                }
            else:
                self.stats['micro_rejects'] += 1
                
                # Check for vetoes
                if confluence_result['micro']['scores'].get('veto_hygiene', 0) == 0:
                    self.stats['vetoes'] += 1
                
                logger.info(f"Micro rejected: {candidate.side} - Score {final_score['final_score']:.1f}")
                
                return {
                    'confirmed': False,
                    'reason': 'insufficient_confluence',
                    'confluence': confluence_result
                }
        
        except Exception as e:
            logger.error(f"Error in micro_confirm: {e}")
            return {'confirmed': False, 'reason': 'error', 'error': str(e)}
    
    async def execute(self, candidate: Candidate, confluence_result: Dict) -> Dict:
        """
        State 3: Execute - check 5m trigger and create signal.
        
        Args:
            candidate: Confirmed candidate
            confluence_result: Confluence evaluation result
        
        Returns:
            Dict with execution result
        """
        try:
            # Get current 5m data
            klines_5m = get_klines("5m", limit=10)
            if not klines_5m or len(klines_5m) < 2:
                return {'executed': False, 'reason': 'insufficient_data'}
            
            df_5m = pd.DataFrame(klines_5m)
            
            # Check if price has broken through trigger level
            last_close = df_5m.iloc[-1]['close']
            trigger_offset = 0.5  # 0.5x ATR (from framework)
            
            # Compute ATR
            df_5m_full = pd.DataFrame(get_klines("5m", limit=50))
            if len(df_5m_full) < 14:
                return {'executed': False, 'reason': 'insufficient_history'}
            
            high_low = df_5m_full['high'] - df_5m_full['low']
            high_close = (df_5m_full['high'] - df_5m_full['close'].shift()).abs()
            low_close = (df_5m_full['low'] - df_5m_full['close'].shift()).abs()
            
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = tr.rolling(window=14).mean().iloc[-1]
            
            # Check trigger
            triggered = False
            if candidate.side == 'long':
                trigger_level = candidate.price + trigger_offset * atr
                triggered = last_close > trigger_level
            else:  # short
                trigger_level = candidate.price - trigger_offset * atr
                triggered = last_close < trigger_level
            
            if not triggered:
                return {'executed': False, 'reason': 'trigger_not_reached'}
            
            # Calculate SL and TPs
            atr5 = atr * (5/14)
            
            if candidate.side == 'long':
                sl = min(candidate.price, last_close - 0.9 * atr5)
                r = last_close - sl
                tp1 = last_close + 1.0 * r
                tp2 = last_close + 2.0 * r
                tp3 = last_close + 3.0 * r
            else:  # short
                sl = max(candidate.price, last_close + 0.9 * atr5)
                r = sl - last_close
                tp1 = last_close - 1.0 * r
                tp2 = last_close - 2.0 * r
                tp3 = last_close - 3.0 * r
            
            # Create signal
            signal = {
                'side': candidate.side,
                'entry': last_close,
                'sl': sl,
                'tp1': tp1,
                'tp2': tp2,
                'tp3': tp3,
                'trail_atr_mult': 0.5,
                'extremum_index': candidate.index,
                'confirm_index': len(df_5m) - 1,
                'candidate_timestamp': candidate.timestamp,
                'execution_timestamp': int(datetime.now(timezone.utc).timestamp()),
                'tier': confluence_result.get('tier', 'B'),
                'confluence_score': confluence_result.get('final_score', 0),
                'size_multiplier': confluence_result.get('size_multiplier', 0.5)
            }
            
            self.stats['executions'] += 1
            logger.info(f"Signal executed: {candidate.side} at {last_close} - Tier {signal['tier']}")
            
            return {
                'executed': True,
                'signal': signal
            }
        
        except Exception as e:
            logger.error(f"Error in execute: {e}")
            return {'executed': False, 'reason': 'error', 'error': str(e)}
    
    async def run(self, df_5m: pd.DataFrame) -> Optional[Dict]:
        """
        Main state machine run loop.
        
        Args:
            df_5m: 5-minute DataFrame
        
        Returns:
            Signal dict if executed, None otherwise
        """
        try:
            if self.state == MTFState.SCAN:
                # Look for candidates
                candidate = await self.scan(df_5m)
                
                if candidate:
                    self.candidate = candidate
                    self.state = MTFState.CANDIDATE
                    logger.info(f"State: SCAN → CANDIDATE")
                
                return None
            
            elif self.state == MTFState.CANDIDATE:
                # Move to micro confirm
                self.state = MTFState.MICRO_CONFIRM
                logger.info(f"State: CANDIDATE → MICRO_CONFIRM")
                return None
            
            elif self.state == MTFState.MICRO_CONFIRM:
                # Validate candidate
                confirm_result = await self.micro_confirm(self.candidate)
                
                if confirm_result['confirmed']:
                    self.state = MTFState.EXECUTE
                    logger.info(f"State: MICRO_CONFIRM → EXECUTE")
                    
                    # Store confluence for execution
                    self.candidate.confluence_score = confirm_result['confluence']
                else:
                    # Failed confirmation - invalidate and return to scan
                    if self.candidate:
                        self.invalidated_candidates[self.candidate.index] = datetime.now(timezone.utc).timestamp()
                    
                    self.candidate = None
                    self.state = MTFState.SCAN
                    logger.info(f"State: MICRO_CONFIRM → SCAN (rejected)")
                
                return None
            
            elif self.state == MTFState.EXECUTE:
                # Execute signal
                exec_result = await self.execute(
                    self.candidate,
                    self.candidate.confluence_score['final']
                )
                
                if exec_result['executed']:
                    signal = exec_result['signal']
                    
                    # Move to manage state (for future position management)
                    self.active_position = signal
                    self.state = MTFState.MANAGE
                    logger.info(f"State: EXECUTE → MANAGE")
                    
                    # Reset candidate
                    self.candidate = None
                    
                    return signal
                else:
                    # Execution failed - check reason
                    if exec_result['reason'] == 'trigger_not_reached':
                        # Stay in execute state, wait for trigger
                        return None
                    else:
                        # Failed execution - return to scan
                        self.candidate = None
                        self.state = MTFState.SCAN
                        logger.info(f"State: EXECUTE → SCAN (failed)")
                
                return None
            
            elif self.state == MTFState.MANAGE:
                # Position management (placeholder for now)
                # In a full implementation, this would handle trailing stops, TP management, etc.
                # For now, just return to scan after a signal is generated
                self.state = MTFState.SCAN
                logger.info(f"State: MANAGE → SCAN")
                return None
        
        except Exception as e:
            logger.error(f"Error in state machine: {e}")
            # Reset to scan on error
            self.candidate = None
            self.state = MTFState.SCAN
            return None
    
    def get_status(self) -> Dict:
        """Get current state machine status."""
        return {
            'state': self.state.value,
            'has_candidate': self.candidate is not None,
            'candidate_info': {
                'side': self.candidate.side,
                'price': self.candidate.price,
                'age_seconds': (datetime.now(timezone.utc) - self.candidate.created_at).total_seconds(),
                'expired': self.candidate.is_expired()
            } if self.candidate else None,
            'stats': self.stats,
            'invalidated_count': len(self.invalidated_candidates)
        }


# Global instance
mtf_state_machine = MTFStateMachine()
