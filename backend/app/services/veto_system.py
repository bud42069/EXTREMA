"""
Comprehensive Veto System (Phase 1)
Implements all veto rules from SOLUSDT Swing-Capture Playbook v1.0:
- OBV/CVD cliff detection
- Spread limits
- Depth checks
- Mark-last deviation
- Funding rate monitoring
- ADL warnings
- Liquidation shock detection
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional
from ..utils.logging import get_logger
from ..utils.micro_store import MicroSnapshot

logger = get_logger(__name__)


def check_obv_cliff_veto(
    df_tape: pd.DataFrame,
    side: str,
    z_threshold: float = 2.0,
    window: int = 10
) -> Dict:
    """
    Check for OBV/CVD cliff veto.
    Veto if 10s z-score >= 2σ **against** direction.
    
    Args:
        df_tape: Tape DataFrame with CVD/OBV data
        side: 'long' or 'short'
        z_threshold: Z-score threshold for veto
        window: Rolling window for z-score calculation
    
    Returns:
        Dict with veto status and details
    """
    result = {
        'veto': False,
        'z_score': np.nan,
        'reason': None
    }
    
    if df_tape is None or len(df_tape) < window:
        return result
    
    try:
        # Compute CVD z-score if not present
        if 'cvd' in df_tape.columns:
            cvd = df_tape['cvd']
            cvd_mean = cvd.rolling(window=window).mean()
            cvd_std = cvd.rolling(window=window).std()
            z_score = ((cvd.iloc[-1] - cvd_mean.iloc[-1]) / 
                      cvd_std.iloc[-1]) if cvd_std.iloc[-1] != 0 else 0
            
            result['z_score'] = z_score
            
            # For longs: veto if z <= -2 (strong selling pressure)
            # For shorts: veto if z >= +2 (strong buying pressure)
            if side == 'long' and z_score <= -z_threshold:
                result['veto'] = True
                result['reason'] = f'CVD cliff against long: z={z_score:.2f}'
            elif side == 'short' and z_score >= z_threshold:
                result['veto'] = True
                result['reason'] = f'CVD cliff against short: z={z_score:.2f}'
                
    except Exception as e:
        logger.error(f"Error in OBV cliff check: {e}")
    
    return result


def check_spread_veto(
    micro_snap: Optional[MicroSnapshot],
    max_spread_pct: float = 0.10
) -> Dict:
    """
    Check spread veto: spread > 0.10% is too wide.
    
    Args:
        micro_snap: Microstructure snapshot
        max_spread_pct: Maximum allowed spread percentage
    
    Returns:
        Dict with veto status
    """
    result = {
        'veto': False,
        'spread_bps': np.nan,
        'spread_pct': np.nan,
        'reason': None
    }
    
    if micro_snap is None or not micro_snap.ok:
        return result
    
    try:
        spread_bps = micro_snap.spread_bps
        spread_pct = spread_bps / 100  # Convert bps to percentage
        
        result['spread_bps'] = spread_bps
        result['spread_pct'] = spread_pct
        
        if spread_pct > max_spread_pct:
            result['veto'] = True
            result['reason'] = f'Spread too wide: {spread_pct:.3f}% > {max_spread_pct}%'
            
    except Exception as e:
        logger.error(f"Error in spread check: {e}")
    
    return result


def check_depth_veto(
    micro_snap: Optional[MicroSnapshot],
    min_depth_ratio: float = 0.50,
    baseline_depth: Optional[float] = None
) -> Dict:
    """
    Check depth veto: depth < 50% of 30-day median is insufficient.
    
    Args:
        micro_snap: Microstructure snapshot
        min_depth_ratio: Minimum depth ratio (default 0.5 = 50%)
        baseline_depth: 30-day median depth (if available)
    
    Returns:
        Dict with veto status
    """
    result = {
        'veto': False,
        'bid_depth': np.nan,
        'ask_depth': np.nan,
        'total_depth': np.nan,
        'depth_ratio': np.nan,
        'reason': None
    }
    
    if micro_snap is None or not micro_snap.ok:
        return result
    
    try:
        bid_depth = micro_snap.bid_depth
        ask_depth = micro_snap.ask_depth
        total_depth = bid_depth + ask_depth
        
        result['bid_depth'] = bid_depth
        result['ask_depth'] = ask_depth
        result['total_depth'] = total_depth
        
        if baseline_depth is not None and baseline_depth > 0:
            depth_ratio = total_depth / baseline_depth
            result['depth_ratio'] = depth_ratio
            
            if depth_ratio < min_depth_ratio:
                result['veto'] = True
                result['reason'] = f'Depth insufficient: {depth_ratio:.2f} < {min_depth_ratio}'
        else:
            # If no baseline, use absolute threshold (e.g., 100k)
            min_absolute_depth = 100000
            if total_depth < min_absolute_depth:
                result['veto'] = True
                result['reason'] = f'Depth too low: ${total_depth:.0f}'
                
    except Exception as e:
        logger.error(f"Error in depth check: {e}")
    
    return result


def check_mark_last_veto(
    mark_price: Optional[float],
    last_price: Optional[float],
    max_deviation_pct: float = 0.15
) -> Dict:
    """
    Check mark-last deviation veto: |mark - last| >= 0.15% indicates risk.
    
    Args:
        mark_price: Mark price (index price)
        last_price: Last traded price
        max_deviation_pct: Maximum allowed deviation percentage
    
    Returns:
        Dict with veto status
    """
    result = {
        'veto': False,
        'mark_price': mark_price,
        'last_price': last_price,
        'deviation_pct': np.nan,
        'reason': None
    }
    
    if mark_price is None or last_price is None or last_price == 0:
        return result
    
    try:
        deviation = abs(mark_price - last_price) / last_price
        deviation_pct = deviation * 100
        
        result['deviation_pct'] = deviation_pct
        
        if deviation_pct >= max_deviation_pct:
            result['veto'] = True
            result['reason'] = f'Mark-last deviation: {deviation_pct:.3f}% >= {max_deviation_pct}%'
            
    except Exception as e:
        logger.error(f"Error in mark-last check: {e}")
    
    return result


def check_funding_veto(
    current_funding: Optional[float],
    median_funding: Optional[float],
    max_funding_mult: float = 3.0
) -> Dict:
    """
    Check funding rate veto: funding > 3× median is extreme.
    
    Args:
        current_funding: Current funding rate
        median_funding: Median funding rate (30-day)
        max_funding_mult: Maximum funding multiplier
    
    Returns:
        Dict with veto status
    """
    result = {
        'veto': False,
        'current_funding': current_funding,
        'median_funding': median_funding,
        'funding_ratio': np.nan,
        'reason': None
    }
    
    if current_funding is None or median_funding is None or median_funding == 0:
        return result
    
    try:
        funding_ratio = abs(current_funding) / abs(median_funding)
        result['funding_ratio'] = funding_ratio
        
        if funding_ratio > max_funding_mult:
            result['veto'] = True
            result['reason'] = f'Funding extreme: {funding_ratio:.2f}× median'
            
    except Exception as e:
        logger.error(f"Error in funding check: {e}")
    
    return result


def check_adl_veto(adl_status: Optional[str]) -> Dict:
    """
    Check ADL (Auto-Deleveraging) warning veto.
    
    Args:
        adl_status: ADL status indicator (e.g., 'warning', 'ok', 'high')
    
    Returns:
        Dict with veto status
    """
    result = {
        'veto': False,
        'adl_status': adl_status,
        'reason': None
    }
    
    if adl_status in ['warning', 'high', 'critical']:
        result['veto'] = True
        result['reason'] = f'ADL warning: {adl_status}'
    
    return result


def check_liquidation_shock_veto(
    current_liq_volume: Optional[float],
    baseline_liq_volume: Optional[float],
    shock_mult: float = 10.0
) -> Dict:
    """
    Check liquidation shock veto: liq volume >= 10× baseline.
    
    Args:
        current_liq_volume: Current liquidation volume
        baseline_liq_volume: Baseline liquidation volume (30-day median)
        shock_mult: Shock multiplier threshold
    
    Returns:
        Dict with veto status
    """
    result = {
        'veto': False,
        'current_liq': current_liq_volume,
        'baseline_liq': baseline_liq_volume,
        'liq_ratio': np.nan,
        'reason': None
    }
    
    if current_liq_volume is None or baseline_liq_volume is None or baseline_liq_volume == 0:
        return result
    
    try:
        liq_ratio = current_liq_volume / baseline_liq_volume
        result['liq_ratio'] = liq_ratio
        
        if liq_ratio >= shock_mult:
            result['veto'] = True
            result['reason'] = f'Liquidation shock: {liq_ratio:.2f}× baseline'
            
    except Exception as e:
        logger.error(f"Error in liquidation shock check: {e}")
    
    return result


def run_comprehensive_veto_checks(
    df_tape: Optional[pd.DataFrame],
    micro_snap: Optional[MicroSnapshot],
    side: str,
    config: Optional[Dict] = None,
    market_data: Optional[Dict] = None
) -> Dict:
    """
    Run all veto checks comprehensively.
    
    Args:
        df_tape: Tape DataFrame (1s/5s)
        micro_snap: Microstructure snapshot
        side: 'long' or 'short'
        config: Configuration dict with thresholds
        market_data: Optional market data (funding, ADL, liquidations)
    
    Returns:
        Dict with all veto results
    """
    if config is None:
        config = {
            'obv_cliff_z': 2.0,
            'max_spread_pct': 0.10,
            'min_depth_ratio': 0.50,
            'max_mark_last_pct': 0.15,
            'max_funding_mult': 3.0,
            'liq_shock_mult': 10.0
        }
    
    if market_data is None:
        market_data = {}
    
    result = {
        'any_veto': False,
        'veto_count': 0,
        'vetos': {},
        'details': {}
    }
    
    # Check all veto conditions
    veto_checks = {
        'obv_cliff': check_obv_cliff_veto(
            df_tape, side, z_threshold=config.get('obv_cliff_z', 2.0)
        ),
        'spread': check_spread_veto(
            micro_snap, max_spread_pct=config.get('max_spread_pct', 0.10)
        ),
        'depth': check_depth_veto(
            micro_snap,
            min_depth_ratio=config.get('min_depth_ratio', 0.50),
            baseline_depth=market_data.get('baseline_depth')
        ),
        'mark_last': check_mark_last_veto(
            market_data.get('mark_price'),
            market_data.get('last_price'),
            max_deviation_pct=config.get('max_mark_last_pct', 0.15)
        ),
        'funding': check_funding_veto(
            market_data.get('current_funding'),
            market_data.get('median_funding'),
            max_funding_mult=config.get('max_funding_mult', 3.0)
        ),
        'adl': check_adl_veto(market_data.get('adl_status')),
        'liquidation_shock': check_liquidation_shock_veto(
            market_data.get('current_liq_volume'),
            market_data.get('baseline_liq_volume'),
            shock_mult=config.get('liq_shock_mult', 10.0)
        )
    }
    
    # Aggregate results
    veto_reasons = []
    for check_name, check_result in veto_checks.items():
        result['vetos'][check_name] = check_result['veto']
        result['details'][check_name] = check_result
        
        if check_result['veto']:
            result['veto_count'] += 1
            if check_result.get('reason'):
                veto_reasons.append(check_result['reason'])
    
    result['any_veto'] = result['veto_count'] > 0
    result['veto_reasons'] = veto_reasons
    
    if result['any_veto']:
        logger.warning(
            f"Veto triggered ({result['veto_count']} checks failed): "
            f"{', '.join(veto_reasons)}"
        )
    else:
        logger.info("All veto checks passed")
    
    return result
