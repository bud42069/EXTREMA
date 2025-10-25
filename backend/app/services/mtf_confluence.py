"""
Multi-Timeframe Confluence Engine.
Computes context and micro confluence scores based on TF alignment.
Includes Helius on-chain data integration.
"""
from typing import Optional
import pandas as pd
import asyncio

from ..utils.logging import get_logger
from ..utils.mtf_store import get_klines
from .mtf_features import extract_mtf_features, compute_vwap_deviation
from ..utils.micro_store import get_snapshot
from .onchain_monitor import HeliusOnChainMonitor

logger = get_logger(__name__)


class MTFConfluenceEngine:
    """
    Computes confluence scores for MTF signal validation.
    Uses weighted scoring for context (15m/1h/4h/1D) and micro (1s→1m→5m).
    Integrates Helius on-chain data for enhanced validation.
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
        
        # Helius integration
        self.onchain_monitor = None
        if helius_api_key:
            self.onchain_monitor = HeliusOnChainMonitor(helius_api_key)
            logger.info("Helius on-chain monitoring enabled")
        else:
            logger.info("Helius on-chain monitoring disabled (no API key)")
        
        # Feature cache
        self.features_cache = {}
    
    async def start_onchain_monitoring(self):
        """Start the Helius on-chain monitoring loop in background."""
        if self.onchain_monitor:
            asyncio.create_task(self.onchain_monitor.monitor_loop())
            logger.info("Helius on-chain monitor loop started")
    
    def compute_context_confluence(
        self,
        features_15m: dict,
        features_1h: dict,
        features_4h: Optional[dict] = None,
        features_1d: Optional[dict] = None
    ) -> dict:
        """
        Compute context confluence score (15m/1h/4h/1D).
        
        Returns:
            Dict with score breakdown and total
        """
        scores = {}
        
        # EMA Alignment (20%)
        ema_score = 0.0
        if features_15m and features_1h:
            # Average alignment across available TFs
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
            # Check if RSI sides agree
            rsi_15m_side = features_15m.get('rsi_side')
            rsi_1h_side = features_1h.get('rsi_side')
            
            if rsi_15m_side and rsi_1h_side and rsi_15m_side == rsi_1h_side:
                osc_score = self.context_weights['oscillator_agreement'] * 100
        
        scores['oscillator_agreement'] = osc_score
        
        # Pivot/VWAP Structure (10%)
        # For now, simplified - check if price is on correct side of VWAP
        pivot_score = 0.0
        # TODO: Implement full pivot logic when we have pivot data
        scores['pivot_structure'] = pivot_score
        
        # Macro Gate (10%)
        macro_score = 0.0
        if features_4h and features_1d and features_15m and features_1h:
            # Check if 4h/1D agree with 15m/1h direction
            bullish_count = sum([
                1 for f in [features_15m, features_1h, features_4h, features_1d]
                if f and f.get('ema_bullish')
            ])
            bearish_count = sum([
                1 for f in [features_15m, features_1h, features_4h, features_1d]
                if f and f.get('ema_bearish')
            ])
            
            # Strong agreement = macro score
            if bullish_count >= 3 or bearish_count >= 3:
                macro_score = self.context_weights['macro_gate'] * 100
        
        scores['macro_gate'] = macro_score
        
        # Total context score
        total = sum(scores.values())
        
        return {
            'scores': scores,
            'total': total,
            'tier': 'A' if total >= 75 else ('B' if total >= 60 else 'C')
        }
    
    def compute_micro_confluence(
        self,
        features_1s: Optional[dict],
        features_5s: Optional[dict],
        features_1m: Optional[dict],
        features_5m: Optional[dict],
        micro_snapshot: Optional[dict]
    ) -> dict:
        """
        Compute micro confluence score (1s→1m→5m).
        
        Returns:
            Dict with score breakdown and total
        """
        scores = {}
        
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
        
        # 1m Impulse (15%)
        impulse_score = 0.0
        if features_1m:
            # RSI cross through 50
            if features_1m.get('rsi_crossed_50'):
                impulse_score += self.micro_weights['impulse_1m'] * 33.3  # 5%
            
            # BOS detected
            if features_1m.get('bos_detected'):
                impulse_score += self.micro_weights['impulse_1m'] * 33.3  # 5%
            
            # Volume gate
            if features_1m.get('volume_sufficient'):
                impulse_score += self.micro_weights['impulse_1m'] * 33.3  # 5%
        
        scores['impulse_1m'] = impulse_score
        
        # Tape Micro (10%)
        tape_score = 0.0
        if micro_snapshot and micro_snapshot.get('ok'):
            # CVD check - assume positive CVD for longs, negative for shorts
            # For now, give points if CVD magnitude is significant
            cvd = micro_snapshot.get('cvd', 0)
            if abs(cvd) > 10:  # Threshold for significant CVD
                tape_score += self.micro_weights['tape_micro'] * 50  # 5%
            
            # Ladder imbalance check
            ladder_imb = micro_snapshot.get('ladder_imbalance', 0)
            if abs(ladder_imb) > 0.15:  # Threshold for imbalance
                tape_score += self.micro_weights['tape_micro'] * 50  # 5%
        
        scores['tape_micro'] = tape_score
        
        # Veto Hygiene (5%)
        veto_score = self.micro_weights['veto_hygiene'] * 100  # Default full points
        
        # Check for vetoes
        if micro_snapshot and micro_snapshot.get('ok'):
            # OBV cliff veto (large negative CVD slope)
            cvd_slope = micro_snapshot.get('cvd_slope', 0)
            if abs(cvd_slope) > 2.0:  # Threshold for cliff
                veto_score = 0.0  # Veto triggered
            
            # Spread veto (too wide)
            spread = micro_snapshot.get('spread_bps', 0)
            if spread > 10.0:  # 10 bps threshold
                veto_score = 0.0  # Veto triggered
        
        scores['veto_hygiene'] = veto_score
        
        # Total micro score
        total = sum(scores.values())
        
        return {
            'scores': scores,
            'total': total,
            'tier': 'A' if total >= 80 else ('B' if total >= 70 else 'C')
        }
    
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
        micro_snapshot: Optional[dict] = None
    ) -> dict:
        """
        Main evaluation method - computes full MTF confluence.
        
        Returns:
            Dict with complete confluence breakdown
        """
        # Context confluence
        context = self.compute_context_confluence(
            features_15m, features_1h, features_4h, features_1d
        )
        
        # Micro confluence
        micro = self.compute_micro_confluence(
            features_1s, features_5s, features_1m, features_5m, micro_snapshot
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


# Global instance
confluence_engine = MTFConfluenceEngine()
