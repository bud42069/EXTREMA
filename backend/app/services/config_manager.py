"""
Config Manager (Phase 4)
Implements JSON-based configuration system for all playbook parameters.
Part of the SOLUSDT Swing-Capture Playbook v1.0
"""
import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
from ..utils.logging import get_logger

logger = get_logger(__name__)


class ConfigManager:
    """
    Manages JSON-based configuration for the trading system.
    
    Features:
    - Load/save config from JSON file
    - Parameter validation
    - Default config generation
    - Environment variable overrides
    - Config sections: detection, risk, execution, tp_sl, system
    """
    
    DEFAULT_CONFIG = {
        "detection": {
            "atr_min": 0.6,
            "volz_min": 0.5,
            "rsi_period": 14,
            "rsi_12_period": 12,
            "bos_atr_mult": 0.1,
            "vol_mult_b_tier": 1.5,
            "vol_mult_a_tier": 2.0,
            "cvd_z_threshold": 0.5,
            "obi_long_threshold": 1.25,
            "obi_short_threshold": 0.80,
            "vwap_tolerance": 0.02
        },
        "risk": {
            "base_position_size_usd": 1000.0,
            "max_leverage": 5.0,
            "default_leverage": 3.0,
            "min_liq_gap_multiplier": 3.0,
            "max_risk_per_trade_pct": 2.0,
            "maintenance_margin_rate": 0.005
        },
        "execution": {
            "max_slip_attempts": 3,
            "max_slip_pct": 0.05,
            "unfilled_wait_seconds": 2,
            "tick_size": 0.01,
            "use_post_only": True,
            "market_fallback_on_urgent": True
        },
        "tp_sl": {
            "tp1_r": 1.0,
            "tp2_r_normal": 2.0,
            "tp2_r_squeeze": 2.5,
            "tp3_r_normal": 3.0,
            "tp3_r_squeeze": 4.0,
            "tp1_pct": 0.50,
            "tp2_pct": 0.30,
            "tp3_pct": 0.20,
            "trail_atr_mult": 0.5,
            "max_hold_hours_normal": 24,
            "max_hold_hours_squeeze": 12,
            "early_reduce_pct": 0.50
        },
        "regime": {
            "squeeze_threshold": 30.0,
            "wide_threshold": 70.0,
            "bbwidth_window": 90
        },
        "confluence": {
            "min_context_a": 75.0,
            "min_micro_a": 80.0,
            "min_context_b": 60.0,
            "min_micro_b": 70.0,
            "context_weight": 0.50,
            "micro_weight": 0.50
        },
        "veto": {
            "obv_cliff_z": 2.0,
            "max_spread_pct": 0.10,
            "min_depth_ratio": 0.50,
            "max_mark_last_pct": 0.15,
            "max_funding_mult": 3.0,
            "liq_shock_mult": 10.0
        },
        "system": {
            "symbol": "SOLUSDT",
            "timeframes": ["1s", "5s", "1m", "5m", "15m", "1h", "4h", "1d"],
            "primary_timeframe": "5m",
            "log_level": "INFO",
            "enable_trade_logging": True,
            "enable_kpi_tracking": True,
            "config_hot_reload": False
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize config manager.
        
        Args:
            config_path: Path to JSON config file (default: ./config/trading_config.json)
        """
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__),
                "../../config/trading_config.json"
            )
        
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        
        # Load or create config
        if self.config_path.exists():
            self.load_config()
        else:
            logger.info(f"Config file not found, creating default: {self.config_path}")
            self.config = self.DEFAULT_CONFIG.copy()
            self.save_config()
        
        logger.info(f"ConfigManager initialized with config from: {self.config_path}")
    
    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from JSON file.
        
        Returns:
            Loaded configuration dict
        """
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            
            # Merge with defaults for any missing keys
            self.config = self._merge_with_defaults(self.config)
            
            # Apply environment variable overrides
            self._apply_env_overrides()
            
            logger.info(f"Config loaded successfully from {self.config_path}")
            return self.config
        
        except Exception as e:
            logger.error(f"Error loading config: {e}", exc_info=True)
            logger.info("Using default configuration")
            self.config = self.DEFAULT_CONFIG.copy()
            return self.config
    
    def save_config(self) -> bool:
        """
        Save current configuration to JSON file.
        
        Returns:
            True if saved successfully
        """
        try:
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            logger.info(f"Config saved successfully to {self.config_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving config: {e}", exc_info=True)
            return False
    
    def _merge_with_defaults(self, config: Dict) -> Dict:
        """
        Merge loaded config with defaults for missing keys.
        
        Args:
            config: Loaded config
        
        Returns:
            Merged config
        """
        merged = self.DEFAULT_CONFIG.copy()
        
        for section, values in config.items():
            if section in merged and isinstance(values, dict):
                merged[section].update(values)
            else:
                merged[section] = values
        
        return merged
    
    def _apply_env_overrides(self):
        """
        Apply environment variable overrides to config.
        
        Environment variables should be in format:
        TRADING_<SECTION>_<KEY> = value
        
        Example: TRADING_RISK_MAX_LEVERAGE=10.0
        """
        env_prefix = "TRADING_"
        
        for key, value in os.environ.items():
            if not key.startswith(env_prefix):
                continue
            
            # Parse env var name
            parts = key[len(env_prefix):].lower().split('_', 1)
            if len(parts) != 2:
                continue
            
            section, param = parts
            
            if section in self.config and param in self.config[section]:
                # Try to convert value to appropriate type
                try:
                    original_type = type(self.config[section][param])
                    if original_type == bool:
                        self.config[section][param] = value.lower() in ['true', '1', 'yes']
                    elif original_type == int:
                        self.config[section][param] = int(value)
                    elif original_type == float:
                        self.config[section][param] = float(value)
                    else:
                        self.config[section][param] = value
                    
                    logger.info(
                        f"Environment override: {section}.{param} = {value}"
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to apply env override {key}={value}: {e}"
                    )
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get config value.
        
        Args:
            section: Config section
            key: Config key
            default: Default value if not found
        
        Returns:
            Config value or default
        """
        return self.config.get(section, {}).get(key, default)
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get entire config section.
        
        Args:
            section: Config section name
        
        Returns:
            Section config dict
        """
        return self.config.get(section, {})
    
    def set(self, section: str, key: str, value: Any, save: bool = False) -> bool:
        """
        Set config value.
        
        Args:
            section: Config section
            key: Config key
            value: Config value
            save: Whether to save to file immediately
        
        Returns:
            True if set successfully
        """
        if section not in self.config:
            self.config[section] = {}
        
        self.config[section][key] = value
        
        logger.info(f"Config updated: {section}.{key} = {value}")
        
        if save:
            return self.save_config()
        
        return True
    
    def update_section(self, section: str, values: Dict[str, Any], save: bool = False) -> bool:
        """
        Update entire config section.
        
        Args:
            section: Config section name
            values: New values dict
            save: Whether to save to file immediately
        
        Returns:
            True if updated successfully
        """
        if section not in self.config:
            self.config[section] = {}
        
        self.config[section].update(values)
        
        logger.info(f"Config section updated: {section}")
        
        if save:
            return self.save_config()
        
        return True
    
    def validate_config(self) -> Dict[str, list]:
        """
        Validate configuration values.
        
        Returns:
            Dict with validation errors by section
        """
        errors = {}
        
        # Validate detection parameters
        detection = self.config.get('detection', {})
        det_errors = []
        
        if detection.get('atr_min', 0) <= 0:
            det_errors.append("atr_min must be > 0")
        if detection.get('volz_min', 0) <= 0:
            det_errors.append("volz_min must be > 0")
        if not (0 < detection.get('bos_atr_mult', 0) < 1):
            det_errors.append("bos_atr_mult must be between 0 and 1")
        
        if det_errors:
            errors['detection'] = det_errors
        
        # Validate risk parameters
        risk = self.config.get('risk', {})
        risk_errors = []
        
        if risk.get('base_position_size_usd', 0) <= 0:
            risk_errors.append("base_position_size_usd must be > 0")
        if not (1 <= risk.get('max_leverage', 0) <= 20):
            risk_errors.append("max_leverage must be between 1 and 20")
        if risk.get('min_liq_gap_multiplier', 0) < 1.0:
            risk_errors.append("min_liq_gap_multiplier must be >= 1.0")
        if not (0 < risk.get('max_risk_per_trade_pct', 0) <= 10):
            risk_errors.append("max_risk_per_trade_pct must be between 0 and 10")
        
        if risk_errors:
            errors['risk'] = risk_errors
        
        # Validate TP/SL parameters
        tp_sl = self.config.get('tp_sl', {})
        tp_errors = []
        
        if tp_sl.get('tp1_r', 0) <= 0:
            tp_errors.append("tp1_r must be > 0")
        if tp_sl.get('tp2_r_normal', 0) <= tp_sl.get('tp1_r', 0):
            tp_errors.append("tp2_r_normal must be > tp1_r")
        if tp_sl.get('tp3_r_normal', 0) <= tp_sl.get('tp2_r_normal', 0):
            tp_errors.append("tp3_r_normal must be > tp2_r_normal")
        
        total_pct = (
            tp_sl.get('tp1_pct', 0) +
            tp_sl.get('tp2_pct', 0) +
            tp_sl.get('tp3_pct', 0)
        )
        if abs(total_pct - 1.0) > 0.01:
            tp_errors.append(f"TP percentages must sum to 1.0 (got {total_pct})")
        
        if tp_errors:
            errors['tp_sl'] = tp_errors
        
        if errors:
            logger.warning(f"Config validation errors: {errors}")
        else:
            logger.info("Config validation passed")
        
        return errors
    
    def export_config(self, export_path: Optional[str] = None) -> str:
        """
        Export current config to JSON file.
        
        Args:
            export_path: Path to export file
        
        Returns:
            Path to exported file
        """
        if export_path is None:
            export_path = str(self.config_path).replace('.json', '_export.json')
        
        try:
            with open(export_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            logger.info(f"Config exported to {export_path}")
            return export_path
        
        except Exception as e:
            logger.error(f"Error exporting config: {e}", exc_info=True)
            return ""
    
    def reset_to_defaults(self, save: bool = False) -> bool:
        """
        Reset configuration to defaults.
        
        Args:
            save: Whether to save to file
        
        Returns:
            True if reset successfully
        """
        self.config = self.DEFAULT_CONFIG.copy()
        logger.info("Config reset to defaults")
        
        if save:
            return self.save_config()
        
        return True
    
    def get_all(self) -> Dict[str, Any]:
        """Get entire configuration."""
        return self.config.copy()
