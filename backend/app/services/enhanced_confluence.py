"""
Enhanced Confluence Bottleneck Engine (Phase 2)
Integrates all Phase 1 & 2 components with bottleneck logic.
Final score = min(Context, Micro)
Part of the SOLUSDT Swing-Capture Playbook v1.0
"""
import pandas as pd
import numpy as np
from typing import Optional, Dict
from ..utils.logging import get_logger

logger = get_logger(__name__)


class EnhancedConfluenceEngine:
    """
    Enhanced MTF Confluence Engine with Phase 2 enhancements.
    
    Scoring Breakdown (per playbook):
    - Context (50%): 20% EMA alignment, 10% oscillator, 10% pivot, 10% macro
    - Micro (50%): 20% 5m trigger, 15% 1m impulse, 10% tape, 5% hygiene
    
    Final score = min(Context, Micro) - Bottleneck logic
    """
    
    def __init__(self):
        # Context weights (total 50%)
        self.context_weights = {
            'ema_alignment': 0.20,      # 20% - EMA alignment 15m/1h/4h
            'oscillator_agreement': 0.10,  # 10% - RSI agreement 15m/1h
            'pivot_structure': 0.10,    # 10% - Pivot/VWAP structure
            'macro_gate': 0.10          # 10% - 4h/1D with 15m/1h
        }
        
        # Micro weights (total 50%)
        self.micro_weights = {
            'trigger_5m': 0.20,         # 20% - 5m trigger (price & volume)
            'impulse_1m': 0.15,         # 15% - 1m impulse (RSI + BOS + vol)
            'tape_micro': 0.10,         # 10% - 1s/5s tape (CVD/OBI/VWAP)
            'veto_hygiene': 0.05        # 5% - No vetoes
        }
        
        logger.info("EnhancedConfluenceEngine initialized with bottleneck logic")
    
    def compute_context_score(
        self,
        context_gate_result: Dict,
        macro_result: Dict
    ) -> Dict:
        """
        Compute context confluence score (50% total weight).
        
        Components:
        - EMA alignment (20%): 15m/1h/4h alignment
        - Oscillator agreement (10%): RSI 15m/1h
        - Pivot structure (10%): VWAP/pivot positioning
        - Macro gate (10%): 4h/1D alignment
        
        Args:
            context_gate_result: Result from check_context_gates()
            macro_result: Result from check_macro_alignment()
        
        Returns:
            Dict with context score breakdown
        """
        scores = {}
        
        # EMA Alignment (20%)
        # Average alignment from 15m/1h
        ema_15m_ratio = context_gate_result.get('ema_alignment', {}).get('15m', {}).get('alignment_ratio', 0.0)
        ema_1h_ratio = context_gate_result.get('ema_alignment', {}).get('1h', {}).get('alignment_ratio', 0.0)
        ema_avg = (ema_15m_ratio + ema_1h_ratio) / 2
        scores['ema_alignment'] = ema_avg * self.context_weights['ema_alignment'] * 100
        
        # Oscillator Agreement (10%)
        osc_15m_ok = context_gate_result.get('oscillator', {}).get('15m', {}).get('oscillator_ok', False)
        osc_1h_ok = context_gate_result.get('oscillator', {}).get('1h', {}).get('oscillator_ok', False)
        osc_score = ((1.0 if osc_15m_ok else 0.0) + (1.0 if osc_1h_ok else 0.0)) / 2
        scores['oscillator_agreement'] = osc_score * self.context_weights['oscillator_agreement'] * 100
        
        # Pivot Structure (10%)
        pivot_ok = context_gate_result.get('pivot_structure', {}).get('structure_ok', False)
        scores['pivot_structure'] = (1.0 if pivot_ok else 0.0) * self.context_weights['pivot_structure'] * 100
        
        # Macro Gate (10%)
        macro_score = macro_result.get('score', 0.0)  # Already 0-100
        scores['macro_gate'] = (macro_score / 100.0) * self.context_weights['macro_gate'] * 100
        
        # Total context score
        total = sum(scores.values())
        
        result = {
            'total': total,
            'components': scores,
            'max_possible': 50.0,
            'percentage': (total / 50.0) * 100
        }
        
        logger.info(f"Context score: {total:.1f}/50.0 ({result['percentage']:.1f}%)")
        
        return result
    
    def compute_micro_score(
        self,
        trigger_result: Dict,
        impulse_result: Dict,
        tape_result: Dict,
        veto_result: Dict
    ) -> Dict:
        """
        Compute micro confluence score (50% total weight).
        
        Components:
        - 5m trigger (20%): Price breakout + volume spike
        - 1m impulse (15%): RSI hold + BOS + volume
        - Tape micro (10%): CVD z-score + OBI + VWAP
        - Veto hygiene (5%): No vetoes triggered
        
        Args:
            trigger_result: 5m trigger validation result
            impulse_result: Result from check_1m_impulse()
            tape_result: Result from check_tape_filters()
            veto_result: Result from run_comprehensive_veto_checks()
        
        Returns:
            Dict with micro score breakdown
        """
        scores = {}
        
        # 5m Trigger + Volume (20%)
        trigger_ok = trigger_result.get('trigger_ok', False)
        vol_ok = trigger_result.get('volume_ok', False)
        trigger_score = ((1.0 if trigger_ok else 0.0) + (1.0 if vol_ok else 0.0)) / 2
        scores['trigger_5m'] = trigger_score * self.micro_weights['trigger_5m'] * 100
        
        # 1m Impulse (15%)
        # RSI hold + BOS + Volume (all must pass)
        rsi_ok = impulse_result.get('rsi_hold_ok', False)
        bos_ok = impulse_result.get('bos_ok', False)
        vol_1m_ok = impulse_result.get('volume_ok', False)
        impulse_score = sum([1.0 if x else 0.0 for x in [rsi_ok, bos_ok, vol_1m_ok]]) / 3
        scores['impulse_1m'] = impulse_score * self.micro_weights['impulse_1m'] * 100
        
        # Tape Micro (10%)
        # CVD + OBI + VWAP (all must pass)
        cvd_ok = tape_result.get('cvd_ok', False)
        obi_ok = tape_result.get('obi_ok', False)
        vwap_ok = tape_result.get('vwap_ok', False)
        tape_score = sum([1.0 if x else 0.0 for x in [cvd_ok, obi_ok, vwap_ok]]) / 3
        scores['tape_micro'] = tape_score * self.micro_weights['tape_micro'] * 100
        
        # Veto Hygiene (5%)
        # No vetoes = full points
        any_veto = veto_result.get('any_veto', False)
        veto_score = 0.0 if any_veto else 1.0
        scores['veto_hygiene'] = veto_score * self.micro_weights['veto_hygiene'] * 100
        
        # Total micro score
        total = sum(scores.values())
        
        result = {
            'total': total,
            'components': scores,
            'max_possible': 50.0,
            'percentage': (total / 50.0) * 100
        }
        
        logger.info(f"Micro score: {total:.1f}/50.0 ({result['percentage']:.1f}%)")
        
        return result
    
    def apply_bottleneck_logic(
        self,
        context_score: Dict,
        micro_score: Dict
    ) -> Dict:
        """
        Apply bottleneck logic: Final = min(Context, Micro).
        
        Per playbook: \"Final score = min(Context, Micro)\"
        This ensures both legs must be strong for signal approval.
        
        Args:
            context_score: Context score result
            micro_score: Micro score result
        
        Returns:
            Dict with final confluence score
        """
        context_total = context_score['total']
        micro_total = micro_score['total']
        
        # Bottleneck: take minimum
        final_score = min(context_total, micro_total)
        
        # Identify bottleneck
        if context_total < micro_total:
            bottleneck = 'context'
            bottleneck_details = context_score['components']
        elif micro_total < context_total:
            bottleneck = 'micro'
            bottleneck_details = micro_score['components']
        else:
            bottleneck = 'balanced'
            bottleneck_details = {}
        
        result = {
            'final_score': final_score,
            'max_possible': 50.0,  # Since we took min of two 50s
            'final_percentage': (final_score / 50.0) * 100,
            'context_score': context_total,
            'micro_score': micro_total,
            'bottleneck': bottleneck,
            'bottleneck_details': bottleneck_details,
            'breakdown': {
                'context': context_score,
                'micro': micro_score
            }
        }
        
        logger.info(
            f"Confluence bottleneck applied: "
            f"Context={context_total:.1f}, Micro={micro_total:.1f} -> "
            f"Final={final_score:.1f} (bottleneck={bottleneck})"
        )
        
        return result
    
    def compute_full_confluence(
        self,
        context_gate_result: Dict,
        macro_result: Dict,
        trigger_result: Dict,
        impulse_result: Dict,
        tape_result: Dict,
        veto_result: Dict
    ) -> Dict:
        """
        Compute full confluence score with all components.
        
        Args:
            context_gate_result: Context gates (15m/1h)
            macro_result: Macro gates (4h/1D)
            trigger_result: 5m trigger validation
            impulse_result: 1m impulse check
            tape_result: Tape filters (1s/5s)
            veto_result: Comprehensive veto checks
        
        Returns:
            Dict with complete confluence analysis
        """
        result = {
            'final_score': 0.0,
            'tier': 'SKIP',
            'context': {},
            'micro': {},
            'bottleneck': {},
            'details': {}
        }
        
        try:
            # Compute context score
            context_score = self.compute_context_score(
                context_gate_result,
                macro_result
            )
            result['context'] = context_score
            
            # Compute micro score
            micro_score = self.compute_micro_score(
                trigger_result,
                impulse_result,
                tape_result,
                veto_result
            )
            result['micro'] = micro_score
            
            # Apply bottleneck logic
            bottleneck = self.apply_bottleneck_logic(
                context_score,
                micro_score
            )
            result['bottleneck'] = bottleneck
            result['final_score'] = bottleneck['final_score']
            
            # Determine tier based on final score + macro clearance
            # A-tier: Context ≥75 AND Micro ≥80 with macro aligned
            # B-tier: Context ≥60 AND Micro ≥70 with macro neutral/mixed
            
            context_pct = context_score['percentage']
            micro_pct = micro_score['percentage']
            macro_tier = macro_result.get('tier_clearance', 'B')
            
            if (macro_tier == 'A' and 
                context_pct >= 75.0 and 
                micro_pct >= 80.0 and
                not veto_result.get('any_veto', False)):
                result['tier'] = 'A'
            elif (context_pct >= 60.0 and 
                  micro_pct >= 70.0 and
                  not veto_result.get('any_veto', False)):
                result['tier'] = 'B'
            else:
                result['tier'] = 'SKIP'
            
            result['details'] = {
                'context_percentage': context_pct,
                'micro_percentage': micro_pct,
                'macro_tier_clearance': macro_tier,
                'veto_triggered': veto_result.get('any_veto', False),
                'veto_count': veto_result.get('veto_count', 0)
            }
            
            logger.info(
                f"Full confluence: Score={result['final_score']:.1f}, "
                f"Tier={result['tier']}, "
                f"Context={context_pct:.1f}%, Micro={micro_pct:.1f}%"
            )
            
        except Exception as e:
            logger.error(f"Error computing full confluence: {e}", exc_info=True)
            result['details']['error'] = str(e)
        
        return result
