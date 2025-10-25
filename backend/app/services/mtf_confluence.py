"""
Multi-Timeframe Confluence Engine (Enhanced with Phase 1 & Phase 2 Integration).
Computes context and micro confluence scores based on TF alignment.
Includes Helius on-chain data integration.

Phase 1 Enhancements:
- 1m impulse detection (RSI-12, BOS, volume) via impulse_detector
- 1s/5s tape filters (CVD z-score, OBI, VWAP proximity) via tape_filters
- Comprehensive veto system (OBV cliff, spread, depth, mark-last, funding, ADL, liq shock) via veto_system

Phase 2 Enhancements:
- Regime detection (Squeeze/Normal/Wide) via regime_detector
- Context gates (15m/1h EMA alignment, pivot structure, oscillator) via context_gates
- Macro gates (4h/1D alignment for A/B tiering) via macro_gates
- Enhanced confluence bottleneck logic with tier determination
"""
from typing import Optional, Dict
import pandas as pd
import asyncio
import os

from ..utils.logging import get_logger
from ..utils.mtf_store import get_klines
from .mtf_features import extract_mtf_features, compute_vwap_deviation
from ..utils.micro_store import get_snapshot

# Import Phase 1 services
from .impulse_detector import check_1m_impulse
from .tape_filters import check_tape_filters
from .veto_system import run_comprehensive_veto_checks

# Import Phase 2 services
from .regime_detector import RegimeDetector
from .context_gates import check_context_gates, compute_ema_set
from .macro_gates import check_macro_alignment, determine_final_tier, check_macro_conflict

# Import Helius monitor
try:
    from .onchain_monitor import HeliusOnChainMonitor
    HELIUS_AVAILABLE = True
except ImportError:
    HELIUS_AVAILABLE = False
    logger = get_logger(__name__)
    logger.warning("Helius on-chain monitor not available")

logger = get_logger(__name__)


class MTFConfluenceEngine:
    """
    Computes confluence scores for MTF signal validation.
    Uses weighted scoring for context (15m/1h/4h/1D) and micro (1s→1m→5m).
    Integrates Helius on-chain data for enhanced validation.
    
    Phase 2: Includes regime detection, context gates, and macro gates.
    """
    
    def __init__(self, helius_api_key: Optional[str] = None):
        # Context weights (total 50%)
        self.context_weights = {
            'ema_alignment': 0.15,      # 15% - EMA alignment across 15m/1h/4h
            'oscillator_agreement': 0.10,  # 10% - RSI/MACD agreement
            'pivot_structure': 0.10,    # 10% - Pivot/VWAP structure
            'macro_gate': 0.10,         # 10% - 4h/1D with 15m/1h
            'onchain_confluence': 0.05  # 5% - On-chain alignment (NEW!)
        }
        
        # Micro weights (total 50%)
        self.micro_weights = {
            'trigger_5m': 0.20,         # 20% - 5m trigger (price & volume)
            'impulse_1m': 0.15,         # 15% - 1m impulse (RSI + BOS + vol)
            'tape_micro': 0.10,         # 10% - 1s/5s tape (CVD/OB + VWAP)
            'veto_hygiene': 0.03,       # 3% - No vetoes (OBV-cliff, spoof)
            'onchain_veto': 0.02        # 2% - On-chain veto check (NEW!)
        }
        
        # Phase 2: Initialize regime detector
        self.regime_detector = RegimeDetector(
            squeeze_threshold=30.0,
            wide_threshold=70.0,
            window=90
        )
        
        # Helius integration
        self.onchain_monitor = None
        if helius_api_key and HELIUS_AVAILABLE:
            self.onchain_monitor = HeliusOnChainMonitor(helius_api_key)
            logger.info("✅ Helius on-chain monitoring ENABLED")
        else:
            if not helius_api_key:
                logger.info("⚠️ Helius on-chain monitoring disabled (no API key)")
            else:
                logger.info("⚠️ Helius on-chain monitoring disabled (module not available)")
        
        # Feature cache
        self.features_cache = {}
        
        logger.info("✅ Phase 2: Regime detector, context gates, and macro gates initialized")
    
    async def start_onchain_monitoring(self):
        """Start the Helius on-chain monitoring loop in background."""
        if self.onchain_monitor:
            asyncio.create_task(self.onchain_monitor.monitor_loop())
            logger.info("Helius on-chain monitor loop started")
    
    def compute_regime_features(self, df_5m: pd.DataFrame) -> Dict:
        """
        Compute regime features using Phase 2 regime detector.
        
        Args:
            df_5m: 5-minute DataFrame with OHLC data
        
        Returns:
            Dict with regime analysis and parameters
        """
        if df_5m is None or len(df_5m) < 90:
            return {
                'regime': 'unknown',
                'available': False,
                'reason': 'Insufficient 5m data'
            }
        
        try:
            # Run regime analysis
            regime_result = self.regime_detector.analyze_regime(df_5m)
            regime_result['available'] = True
            
            logger.info(
                f"Regime detected: {regime_result['regime'].upper()} "
                f"(BBWidth pct={regime_result['bbwidth_pct']:.1f})"
            )
            
            return regime_result
        
        except Exception as e:
            logger.error(f"Error computing regime features: {e}", exc_info=True)
            return {
                'regime': 'unknown',
                'available': False,
                'error': str(e)
            }
    
    def compute_context_confluence(
        self,
        features_15m: dict,
        features_1h: dict,
        features_4h: Optional[dict] = None,
        features_1d: Optional[dict] = None,
        df_15m: Optional[pd.DataFrame] = None,
        df_1h: Optional[pd.DataFrame] = None,
        df_4h: Optional[pd.DataFrame] = None,
        df_1d: Optional[pd.DataFrame] = None,
        side: Optional[str] = None
    ) -> dict:
        """
        Compute context confluence score (15m/1h/4h/1D) with Phase 2 integration.
        
        Phase 2 Enhancements:
        - Uses context_gates for 15m/1h EMA alignment, pivot structure, oscillator
        - Uses macro_gates for 4h/1D alignment and tier clearance
        
        Returns:
            Dict with score breakdown and total
        """
        scores = {}
        details = {}
        
        # Phase 2: Use context_gates if DataFrames available
        if df_15m is not None and df_1h is not None and side:
            # Ensure EMAs are computed
            if 'EMA_5' not in df_15m.columns:
                df_15m = compute_ema_set(df_15m)
            if 'EMA_5' not in df_1h.columns:
                df_1h = compute_ema_set(df_1h)
            
            # Run comprehensive context gate check
            context_result = check_context_gates(
                df_15m=df_15m,
                df_1h=df_1h,
                side=side,
                ema_spans=[5, 9, 21, 38],
                min_ema_aligned=3
            )
            
            details['context_gates'] = context_result
            
            # Score based on context gate results
            # EMA alignment (15%)
            ema_score = context_result['score'] * 0.15 / 100  # Normalize to 15%
            scores['ema_alignment'] = ema_score * 100
            
            # Oscillator agreement (10%)
            osc_score = (self.context_weights['oscillator_agreement'] * 100 
                        if context_result['oscillator']['both_ok'] else 0.0)
            scores['oscillator_agreement'] = osc_score
            
            # Pivot structure (10%)
            pivot_score = (self.context_weights['pivot_structure'] * 100
                          if context_result['pivot_structure']['structure_ok'] else 0.0)
            scores['pivot_structure'] = pivot_score
            
        else:
            # Fallback to simplified logic
            # EMA Alignment (15%)
            ema_score = 0.0
            if features_15m and features_1h:
                alignments = []
                
                if features_15m.get('ema_alignment') is not None:
                    alignments.append(features_15m['ema_alignment'])
                if features_1h.get('ema_alignment') is not None:
                    alignments.append(features_1h['ema_alignment'])
                if features_4h and features_4h.get('ema_alignment') is not None:
                    alignments.append(features_4h['ema_alignment'])
                
                if alignments:
                    avg_alignment = sum(alignments) / len(alignments)
                    ema_score = avg_alignment * self.context_weights['ema_alignment'] * 100
            
            scores['ema_alignment'] = ema_score
            
            # Oscillator Agreement (10%)
            osc_score = 0.0
            if features_15m and features_1h:
                rsi_15m_side = features_15m.get('rsi_side')
                rsi_1h_side = features_1h.get('rsi_side')
                
                if rsi_15m_side and rsi_1h_side and rsi_15m_side == rsi_1h_side:
                    osc_score = self.context_weights['oscillator_agreement'] * 100
            
            scores['oscillator_agreement'] = osc_score
            
            # Pivot/VWAP Structure (10%)
            pivot_score = 0.0
            scores['pivot_structure'] = pivot_score
            
            details['context_gates'] = {'mode': 'fallback'}
        
        # Phase 2: Macro Gate (10%) - Use macro_gates
        macro_score = 0.0
        macro_details = {}
        
        if df_4h is not None and df_1d is not None and side:
            # Ensure EMAs are computed
            if 'EMA_5' not in df_4h.columns:
                df_4h = compute_ema_set(df_4h)
            if 'EMA_5' not in df_1d.columns:
                df_1d = compute_ema_set(df_1d)
            
            # Run macro alignment check
            macro_result = check_macro_alignment(
                df_4h=df_4h,
                df_1d=df_1d,
                side=side,
                ema_spans=[5, 9, 21, 38]
            )
            
            macro_details = macro_result
            
            # Score based on macro alignment
            if macro_result['macro_aligned']:
                macro_score = self.context_weights['macro_gate'] * 100  # Full 10%
            else:
                # Partial credit based on score
                macro_score = macro_result['score'] * self.context_weights['macro_gate']
        
        elif features_4h and features_1d and features_15m and features_1h:
            # Fallback to simplified logic
            bullish_count = sum([
                1 for f in [features_15m, features_1h, features_4h, features_1d]
                if f and f.get('ema_bullish')
            ])
            bearish_count = sum([
                1 for f in [features_15m, features_1h, features_4h, features_1d]
                if f and f.get('ema_bearish')
            ])
            
            if bullish_count >= 3 or bearish_count >= 3:
                macro_score = self.context_weights['macro_gate'] * 100
            macro_details = {'mode': 'fallback'}
        
        scores['macro_gate'] = macro_score
        details['macro_gates'] = macro_details
        
        # On-Chain Confluence (5%)
        onchain_score = 0.0
        scores['onchain_confluence'] = onchain_score
        details['onchain_confluence'] = {'enabled': False}
        
        # Total context score
        total = sum(scores.values())
        
        result = {
            'scores': scores,
            'total': total,
            'tier': 'A' if total >= 75 else ('B' if total >= 60 else 'C'),
            'details': details
        }
        
        logger.info(
            f"Context confluence: total={total:.1f}, tier={result['tier']}, "
            f"ema={scores['ema_alignment']:.1f}, osc={scores['oscillator_agreement']:.1f}, "
            f"pivot={scores['pivot_structure']:.1f}, macro={scores['macro_gate']:.1f}"
        )
        
        return result
    
    async def compute_context_confluence_async(
        self,
        features_15m: dict,
        features_1h: dict,
        features_4h: Optional[dict] = None,
        features_1d: Optional[dict] = None,
        signal_direction: Optional[str] = None
    ) -> dict:
        """
        Async version with on-chain integration.
        
        Returns:
            Dict with score breakdown and total
        """
        # Get base context scores
        result = self.compute_context_confluence(features_15m, features_1h, features_4h, features_1d)
        
        # Add on-chain confluence if available and direction is known
        if self.onchain_monitor and signal_direction:
            try:
                onchain_data = await self.onchain_monitor.get_on_chain_confluence(
                    direction=signal_direction,
                    lookback_minutes=60
                )
                
                if onchain_data['aligned']:
                    # Award up to 5% for on-chain alignment
                    onchain_score = min(
                        self.context_weights['onchain_confluence'] * 100,
                        onchain_data['score'] * 0.05
                    )
                    result['scores']['onchain_confluence'] = onchain_score
                    result['total'] = sum(result['scores'].values())
                    result['tier'] = 'A' if result['total'] >= 75 else ('B' if result['total'] >= 60 else 'C')
                    
                    logger.info(f"On-chain confluence: {onchain_score:.1f} (aligned={onchain_data['aligned']})")
            
            except Exception as e:
                logger.error(f"Error computing on-chain confluence: {e}")
        
        return result
    
    def compute_micro_confluence(
        self,
        features_1s: Optional[dict],
        features_5s: Optional[dict],
        features_1m: Optional[dict],
        features_5m: Optional[dict],
        micro_snapshot: Optional[dict],
        df_1m: Optional[pd.DataFrame] = None,
        df_tape: Optional[pd.DataFrame] = None,
        side: Optional[str] = None,
        tier: str = 'B',
        atr_5m: Optional[float] = None
    ) -> dict:
        """
        Compute micro confluence score (1s→1m→5m) with Phase 1 integration.
        
        Phase 1 Enhancements:
        - Uses impulse_detector for 1m impulse requirements
        - Uses tape_filters for 1s/5s microstructure
        - Uses veto_system for comprehensive veto checks
        
        Args:
            features_1s: 1-second features (optional)
            features_5s: 5-second features (optional)
            features_1m: 1-minute features (optional)
            features_5m: 5-minute features (required for trigger)
            micro_snapshot: Microstructure snapshot
            df_1m: 1-minute DataFrame for impulse detection
            df_tape: 1s or 5s DataFrame for tape filters
            side: Trade direction ('long' or 'short')
            tier: Tier for volume threshold ('A' or 'B')
            atr_5m: 5-minute ATR for VWAP proximity check
        
        Returns:
            Dict with score breakdown and total
        """
        scores = {}
        details = {}
        
        # 5m Trigger (20%)
        trigger_score = 0.0
        if features_5m:
            # Check volume gate
            if features_5m.get('volume_sufficient'):
                trigger_score += self.micro_weights['trigger_5m'] * 50  # 10%
            
            # Check if BOS detected
            if features_5m.get('bos_detected'):
                trigger_score += self.micro_weights['trigger_5m'] * 50  # 10%
        
        scores['trigger_5m'] = trigger_score
        details['trigger_5m'] = features_5m or {}
        
        # 1m Impulse (15%) - ENHANCED WITH PHASE 1
        impulse_score = 0.0
        impulse_details = {}
        
        if df_1m is not None and side:
            # Use comprehensive impulse detector
            impulse_result = check_1m_impulse(
                df_1m=df_1m,
                side=side,
                tier=tier,
                rsi_hold_bars=2,
                bos_atr_mult=0.1,
                vol_mult=1.5,
                vol_mult_tier_a=2.0
            )
            
            impulse_details = impulse_result
            
            # Score based on comprehensive check
            if impulse_result['impulse_ok']:
                impulse_score = self.micro_weights['impulse_1m'] * 100  # Full 15%
            else:
                # Partial credit for passing components
                component_score = 0.0
                if impulse_result['rsi_hold_ok']:
                    component_score += 33.3
                if impulse_result['bos_ok']:
                    component_score += 33.3
                if impulse_result['volume_ok']:
                    component_score += 33.3
                impulse_score = self.micro_weights['impulse_1m'] * component_score
        
        elif features_1m:
            # Fallback to simplified logic if DataFrame not available
            if features_1m.get('rsi_crossed_50'):
                impulse_score += self.micro_weights['impulse_1m'] * 33.3
            if features_1m.get('bos_detected'):
                impulse_score += self.micro_weights['impulse_1m'] * 33.3
            if features_1m.get('volume_sufficient'):
                impulse_score += self.micro_weights['impulse_1m'] * 33.3
            impulse_details = features_1m
        
        scores['impulse_1m'] = impulse_score
        details['impulse_1m'] = impulse_details
        
        # Tape Micro (10%) - ENHANCED WITH PHASE 1
        tape_score = 0.0
        tape_details = {}
        
        if df_tape is not None and side and atr_5m:
            # Use comprehensive tape filters
            tape_result = check_tape_filters(
                df_tape=df_tape,
                side=side,
                atr_5m=atr_5m,
                cvd_z_threshold=0.5,
                obi_long_threshold=1.25,
                obi_short_threshold=0.80,
                vwap_tolerance=0.02
            )
            
            tape_details = tape_result
            
            # Score based on comprehensive check
            if tape_result['tape_ok']:
                tape_score = self.micro_weights['tape_micro'] * 100  # Full 10%
            else:
                # Partial credit for passing components
                component_score = 0.0
                if tape_result['cvd_ok']:
                    component_score += 33.3
                if tape_result['obi_ok']:
                    component_score += 33.3
                if tape_result['vwap_ok']:
                    component_score += 33.3
                tape_score = self.micro_weights['tape_micro'] * component_score
        
        elif micro_snapshot and micro_snapshot.ok:
            # Fallback to simplified logic
            cvd = micro_snapshot.cvd or 0
            if abs(cvd) > 10:
                tape_score += self.micro_weights['tape_micro'] * 50
            
            ladder_imb = micro_snapshot.ladder_imbalance or 0
            if abs(ladder_imb) > 0.15:
                tape_score += self.micro_weights['tape_micro'] * 50
            tape_details = {'micro_snapshot': 'simplified_fallback'}
        
        scores['tape_micro'] = tape_score
        details['tape_micro'] = tape_details
        
        # Veto Hygiene (3%) - ENHANCED WITH PHASE 1
        veto_score = self.micro_weights['veto_hygiene'] * 100  # Default full points
        veto_details = {}
        
        if df_tape is not None and micro_snapshot and side:
            # Use comprehensive veto system
            veto_config = {
                'obv_cliff_z': 2.0,
                'max_spread_pct': 0.10,
                'min_depth_ratio': 0.50,
                'max_mark_last_pct': 0.15,
                'max_funding_mult': 3.0,
                'liq_shock_mult': 10.0
            }
            
            # Additional market data (if available)
            market_data = {}
            if micro_snapshot.ok:
                market_data['last_price'] = getattr(micro_snapshot, 'last_price', None)
                market_data['mark_price'] = getattr(micro_snapshot, 'mark_price', None)
            
            veto_result = run_comprehensive_veto_checks(
                df_tape=df_tape,
                micro_snap=micro_snapshot,
                side=side,
                config=veto_config,
                market_data=market_data
            )
            
            veto_details = veto_result
            
            # If any veto triggered, score = 0
            if veto_result['any_veto']:
                veto_score = 0.0
                logger.warning(
                    f"Veto triggered: {veto_result['veto_count']} checks failed - "
                    f"{', '.join(veto_result.get('veto_reasons', []))}"
                )
        
        elif micro_snapshot and micro_snapshot.ok:
            # Fallback to simplified veto checks
            cvd_slope = micro_snapshot.cvd_slope or 0
            if abs(cvd_slope) > 2.0:
                veto_score = 0.0
            
            spread = micro_snapshot.spread_bps or 0
            if spread > 10.0:
                veto_score = 0.0
            veto_details = {'simplified_fallback': True}
        
        scores['veto_hygiene'] = veto_score
        details['veto_hygiene'] = veto_details
        
        # On-Chain Veto (2%)
        onchain_veto_score = self.micro_weights['onchain_veto'] * 100
        scores['onchain_veto'] = onchain_veto_score
        details['onchain_veto'] = {'enabled': False}
        
        # Total micro score
        total = sum(scores.values())
        
        result = {
            'scores': scores,
            'total': total,
            'tier': 'A' if total >= 80 else ('B' if total >= 70 else 'C'),
            'details': details
        }
        
        logger.info(
            f"Micro confluence: total={total:.1f}, tier={result['tier']}, "
            f"trigger={scores['trigger_5m']:.1f}, impulse={scores['impulse_1m']:.1f}, "
            f"tape={scores['tape_micro']:.1f}, veto={scores['veto_hygiene']:.1f}"
        )
        
        return result
    
    async def compute_micro_confluence_async(
        self,
        features_1s: Optional[dict],
        features_5s: Optional[dict],
        features_1m: Optional[dict],
        features_5m: Optional[dict],
        micro_snapshot: Optional[dict],
        signal_direction: Optional[str] = None,
        df_1m: Optional[pd.DataFrame] = None,
        df_tape: Optional[pd.DataFrame] = None,
        tier: str = 'B',
        atr_5m: Optional[float] = None
    ) -> dict:
        """
        Async version with on-chain veto integration and Phase 1 enhancements.
        
        Returns:
            Dict with score breakdown and total
        """
        # Get base micro scores with Phase 1 integration
        result = self.compute_micro_confluence(
            features_1s, features_5s, features_1m, features_5m, micro_snapshot,
            df_1m=df_1m, df_tape=df_tape, side=signal_direction, tier=tier, atr_5m=atr_5m
        )
        
        # Add on-chain veto check if available
        if self.onchain_monitor and signal_direction:
            try:
                onchain_data = await self.onchain_monitor.get_on_chain_confluence(
                    direction=signal_direction,
                    lookback_minutes=15  # Short lookback for veto
                )
                
                # Check for conflicting on-chain signals
                if signal_direction == 'long' and onchain_data['bearish_signals'] > onchain_data['bullish_signals'] * 2:
                    # Strong bearish on-chain conflicts with long signal
                    result['scores']['onchain_veto'] = 0.0
                    result['total'] = sum(result['scores'].values())
                    result['tier'] = 'A' if result['total'] >= 80 else ('B' if result['total'] >= 70 else 'C')
                    logger.warning(f"On-chain VETO triggered: bearish on-chain conflicts with long signal")
                
                elif signal_direction == 'short' and onchain_data['bullish_signals'] > onchain_data['bearish_signals'] * 2:
                    # Strong bullish on-chain conflicts with short signal
                    result['scores']['onchain_veto'] = 0.0
                    result['total'] = sum(result['scores'].values())
                    result['tier'] = 'A' if result['total'] >= 80 else ('B' if result['total'] >= 70 else 'C')
                    logger.warning(f"On-chain VETO triggered: bullish on-chain conflicts with short signal")
            
            except Exception as e:
                logger.error(f"Error computing on-chain veto: {e}")
        
        return result
    
    def compute_final_confluence(
        self,
        context_score: float,
        micro_score: float
    ) -> dict:
        """
        Compute final confluence using min(context, micro) bottleneck logic.
        
        Returns:
            Dict with final score and tier
        """
        # Bottleneck: use minimum of the two
        final_score = min(context_score, micro_score)
        
        # Tier determination
        if final_score >= 75 and context_score >= 75 and micro_score >= 80:
            tier = 'A'
            size_multiplier = 1.0
        elif final_score >= 60 and context_score >= 60 and micro_score >= 70:
            tier = 'B'
            size_multiplier = 0.5
        else:
            tier = 'SKIP'
            size_multiplier = 0.0
        
        return {
            'final_score': final_score,
            'context_score': context_score,
            'micro_score': micro_score,
            'tier': tier,
            'size_multiplier': size_multiplier,
            'allow_entry': tier in ['A', 'B']
        }
    
    def evaluate(
        self,
        features_1s: Optional[dict] = None,
        features_5s: Optional[dict] = None,
        features_1m: Optional[dict] = None,
        features_5m: Optional[dict] = None,
        features_15m: Optional[dict] = None,
        features_1h: Optional[dict] = None,
        features_4h: Optional[dict] = None,
        features_1d: Optional[dict] = None,
        micro_snapshot: Optional[dict] = None,
        df_1m: Optional[pd.DataFrame] = None,
        df_tape: Optional[pd.DataFrame] = None,
        side: Optional[str] = None,
        tier: str = 'B',
        atr_5m: Optional[float] = None
    ) -> dict:
        """
        Main evaluation method - computes full MTF confluence with Phase 1 integration.
        
        Phase 1 Enhancements:
        - Accepts DataFrames (df_1m, df_tape) for detailed impulse and tape analysis
        - Uses side parameter for directional checks
        - Uses tier parameter for volume threshold adjustment
        - Uses atr_5m for VWAP proximity checks
        
        Returns:
            Dict with complete confluence breakdown
        """
        # Context confluence
        context = self.compute_context_confluence(
            features_15m, features_1h, features_4h, features_1d
        )
        
        # Micro confluence with Phase 1 integration
        micro = self.compute_micro_confluence(
            features_1s, features_5s, features_1m, features_5m, micro_snapshot,
            df_1m=df_1m, df_tape=df_tape, side=side, tier=tier, atr_5m=atr_5m
        )
        
        # Final score
        final = self.compute_final_confluence(
            context['total'],
            micro['total']
        )
        
        return {
            'context': context,
            'micro': micro,
            'final': final,
            'timestamp': pd.Timestamp.now()
        }


# Global instance - initialize with Helius API key from config
from ..config import settings
confluence_engine = MTFConfluenceEngine(helius_api_key=settings.HELIUS_API_KEY)
