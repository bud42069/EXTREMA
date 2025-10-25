"""
Macro Gates (Phase 2)
Implements 4h/1D alignment checks for A/B tier classification.
Part of the SOLUSDT Swing-Capture Playbook v1.0
"""
import pandas as pd
import numpy as np
from typing import Optional, Dict, List
from ..utils.logging import get_logger

logger = get_logger(__name__)


def check_macro_alignment(
    df_4h: pd.DataFrame,
    df_1d: pd.DataFrame,
    side: str,
    ema_spans: List[int] = [5, 9, 21, 38]
) -> Dict:
    """
    Check 4h/1D macro alignment for A-tier clearance.
    Per playbook: If aligned with 15m/1h → A-tier sizing allowed, if mixed → B-tier only.
    
    Args:
        df_4h: 4-hour DataFrame
        df_1d: 1-day DataFrame
        side: 'long' or 'short'
        ema_spans: EMA spans to check
    
    Returns:
        Dict with macro alignment results
    """
    result = {
        'macro_aligned': False,
        'tier_clearance': 'B',  # Default to B-tier
        '4h_aligned': False,
        '1d_aligned': False,
        '4h_trend': 'neutral',
        '1d_trend': 'neutral',
        'ema_4h': {},
        'ema_1d': {},
        'score': 0.0,
        'details': {}
    }
    
    if df_4h is None or len(df_4h) < max(ema_spans):
        result['details']['error_4h'] = 'Insufficient 4h data'
    
    if df_1d is None or len(df_1d) < max(ema_spans):
        result['details']['error_1d'] = 'Insufficient 1D data'
    
    if result['details']:
        return result
    
    try:
        # Check 4h EMAs
        ema_4h_values = {}
        for span in ema_spans:
            col = f'EMA_{span}'
            if col in df_4h.columns:
                ema_4h_values[span] = df_4h[col].iloc[-1]
            else:
                # Compute on the fly
                ema_4h_values[span] = df_4h['close'].ewm(span=span, adjust=False).mean().iloc[-1]
        
        result['ema_4h'] = ema_4h_values
        
        # Check 4h alignment
        aligned_4h = 0
        for i in range(len(ema_spans) - 1):
            fast = ema_4h_values[ema_spans[i]]
            slow = ema_4h_values[ema_spans[i + 1]]
            
            if side == 'long' and fast > slow:
                aligned_4h += 1
            elif side == 'short' and fast < slow:
                aligned_4h += 1
        
        result['4h_aligned'] = aligned_4h >= (len(ema_spans) - 2)  # At least 2/3
        
        # Determine 4h trend
        if aligned_4h >= (len(ema_spans) - 1):
            result['4h_trend'] = 'bullish' if side == 'long' else 'bearish'
        elif aligned_4h <= 1:
            result['4h_trend'] = 'bearish' if side == 'long' else 'bullish'
        else:
            result['4h_trend'] = 'neutral'
        
        # Check 1D EMAs
        ema_1d_values = {}
        for span in ema_spans:
            col = f'EMA_{span}'
            if col in df_1d.columns:
                ema_1d_values[span] = df_1d[col].iloc[-1]
            else:
                # Compute on the fly
                ema_1d_values[span] = df_1d['close'].ewm(span=span, adjust=False).mean().iloc[-1]
        
        result['ema_1d'] = ema_1d_values
        
        # Check 1D alignment
        aligned_1d = 0
        for i in range(len(ema_spans) - 1):
            fast = ema_1d_values[ema_spans[i]]
            slow = ema_1d_values[ema_spans[i + 1]]
            
            if side == 'long' and fast > slow:
                aligned_1d += 1
            elif side == 'short' and fast < slow:
                aligned_1d += 1
        
        result['1d_aligned'] = bool(aligned_1d >= (len(ema_spans) - 2))  # At least 2/3
        
        # Determine 1D trend
        if aligned_1d >= (len(ema_spans) - 1):
            result['1d_trend'] = 'bullish' if side == 'long' else 'bearish'
        elif aligned_1d <= 1:
            result['1d_trend'] = 'bearish' if side == 'long' else 'bullish'
        else:
            result['1d_trend'] = 'neutral'
        
        # Overall macro alignment
        result['macro_aligned'] = bool(result['4h_aligned'] and result['1d_aligned'])
        
        # Tier clearance
        if result['macro_aligned']:
            result['tier_clearance'] = 'A'  # A-tier eligible
        else:
            result['tier_clearance'] = 'B'  # B-tier only
        
        # Score (0-100)
        score_4h = aligned_4h / (len(ema_spans) - 1) * 100
        score_1d = aligned_1d / (len(ema_spans) - 1) * 100
        result['score'] = (score_4h + score_1d) / 2
        
        logger.info(
            f"Macro alignment ({side}): "
            f"4h={result['4h_trend']}, 1D={result['1d_trend']}, "
            f"tier={result['tier_clearance']}, score={result['score']:.1f}"
        )
        
    except Exception as e:
        logger.error(f"Error in macro alignment check: {e}", exc_info=True)
        result['details']['error'] = str(e)
    
    return result


def check_macro_conflict(
    macro_result: Dict,
    context_result: Dict
) -> Dict:
    """
    Check for conflicts between macro and context timeframes.
    
    Args:
        macro_result: Macro alignment result (4h/1D)
        context_result: Context gate result (15m/1h)
    
    Returns:
        Dict with conflict analysis
    """
    result = {
        'has_conflict': False,
        'conflict_type': None,
        'resolution': 'unknown',
        'recommended_tier': 'B',
        'details': {}
    }
    
    try:
        macro_trend_4h = macro_result.get('4h_trend', 'neutral')
        macro_trend_1d = macro_result.get('1d_trend', 'neutral')
        context_play = context_result.get('play_type', 'unknown')
        
        # Check for conflicts
        if macro_result.get('macro_aligned'):
            # No conflict if fully aligned
            result['has_conflict'] = False
            result['resolution'] = 'aligned'
            result['recommended_tier'] = 'A'
        elif context_play == 'deviation':
            # Context already flagged as deviation (B-tier)
            result['has_conflict'] = False
            result['resolution'] = 'context_deviation'
            result['recommended_tier'] = 'B'
        else:
            # Potential conflict: context says continuation but macro mixed
            result['has_conflict'] = True
            result['conflict_type'] = 'macro_mixed_with_context_continuation'
            result['resolution'] = 'defer_to_macro'
            result['recommended_tier'] = 'B'  # Safer to go B-tier
            
            result['details'] = {
                'macro_4h': macro_trend_4h,
                'macro_1d': macro_trend_1d,
                'context_play': context_play,
                'reason': 'Macro trends not fully aligned, defaulting to B-tier for safety'
            }
        
        logger.info(
            f"Macro conflict check: "
            f"conflict={result['has_conflict']}, "
            f"resolution={result['resolution']}, "
            f"tier={result['recommended_tier']}"
        )
        
    except Exception as e:
        logger.error(f"Error in macro conflict check: {e}", exc_info=True)
        result['details']['error'] = str(e)
    
    return result


def compute_macro_score(
    df_4h: pd.DataFrame,
    df_1d: pd.DataFrame,
    side: str
) -> Dict:
    """
    Compute comprehensive macro score for confluence engine.
    
    Args:
        df_4h: 4-hour DataFrame
        df_1d: 1-day DataFrame
        side: 'long' or 'short'
    
    Returns:
        Dict with macro scoring
    """
    result = {
        'macro_score': 0.0,
        'alignment': {},
        'components': {},
        'details': {}
    }
    
    try:
        # Get alignment
        alignment = check_macro_alignment(df_4h, df_1d, side)
        result['alignment'] = alignment
        
        # Component scores
        components = {
            'ema_alignment_4h': 50.0 if alignment['4h_aligned'] else 0.0,
            'ema_alignment_1d': 50.0 if alignment['1d_aligned'] else 0.0
        }
        
        result['components'] = components
        
        # Total score (0-100)
        result['macro_score'] = sum(components.values())
        
        # Additional context
        result['details'] = {
            'tier_clearance': alignment['tier_clearance'],
            '4h_trend': alignment['4h_trend'],
            '1d_trend': alignment['1d_trend'],
            'raw_alignment_score': alignment['score']
        }
        
        logger.info(
            f"Macro score: {result['macro_score']:.1f} "
            f"(tier={result['details']['tier_clearance']})"
        )
        
    except Exception as e:
        logger.error(f"Error computing macro score: {e}", exc_info=True)
        result['details']['error'] = str(e)
    
    return result


def determine_final_tier(
    macro_result: Dict,
    context_result: Dict,
    confluence_score: float,
    min_context_a: float = 75.0,
    min_micro_a: float = 80.0,
    min_context_b: float = 60.0,
    min_micro_b: float = 70.0
) -> str:
    """
    Determine final tier classification based on all gates.
    
    Per playbook:
    - A-tier (full): Context ≥75 AND Micro ≥80 with macro aligned
    - B-tier (half): Context ≥60 AND Micro ≥70 with macro neutral/mixed
    - Skip: Either leg below threshold or any veto triggered
    
    Args:
        macro_result: Macro alignment result
        context_result: Context gate result
        confluence_score: Final confluence score
        min_context_a: Minimum context score for A-tier
        min_micro_a: Minimum micro score for A-tier
        min_context_b: Minimum context score for B-tier
        min_micro_b: Minimum micro score for B-tier
    
    Returns:
        Tier string: 'A', 'B', or 'SKIP'
    """
    tier = 'SKIP'
    
    try:
        macro_tier = macro_result.get('tier_clearance', 'B')
        context_score = context_result.get('score', 0.0)
        
        # Extract micro score from confluence (assuming it's passed separately)
        # For now, use a simple threshold on total confluence
        
        # A-tier requirements
        if (macro_tier == 'A' and 
            context_score >= min_context_a and
            confluence_score >= min_micro_a):
            tier = 'A'
        # B-tier requirements  
        elif (context_score >= min_context_b and
              confluence_score >= min_micro_b):
            tier = 'B'
        else:
            tier = 'SKIP'
        
        logger.info(
            f"Final tier determination: {tier} "
            f"(macro={macro_tier}, context={context_score:.1f}, "
            f"confluence={confluence_score:.1f})"
        )
        
    except Exception as e:
        logger.error(f"Error determining tier: {e}", exc_info=True)
        tier = 'SKIP'
    
    return tier
