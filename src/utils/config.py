# Configuration handling
"""Enhanced configuration management for UK Business Lead Generator"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from PySide6.QtCore import QSettings


@dataclass
class SearchConfig:
    """Search configuration settings"""
    default_limit: int = 50
    max_concurrent: int = 3
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0
    user_agent: str = "UK Business Lead Generator/1.0"
    enable_caching: bool = True
    cache_duration_hours: int = 24


@dataclass
class AnalysisConfig:
    """Website analysis configuration"""
    lighthouse_timeout: int = 60
    enable_core_web_vitals: bool = True
    screenshot_enabled: bool = False
    max_threads: int = 3
    performance_threshold: int = 70
    seo_threshold: int = 60
    accessibility_threshold: int = 70
    best_practices_threshold: int = 80
    enable_detailed_analysis: bool = True
    analysis_timeout: int = 120


@dataclass
class ExportConfig:
    """Export configuration settings"""
    default_format: str = "CSV"
    include_analysis: bool = True
    auto_backup: bool = True
    backup_retention_days: int = 30
    max_export_size_mb: int = 100
    compression_enabled: bool = True
    include_timestamps: bool = True
    custom_fields: List[str] = None

    def __post_init__(self):
        if self.custom_fields is None:
            self.custom_fields = []


@dataclass
class UIConfig:
    """User interface configuration"""
    theme: str = "light"
    auto_save: bool = True
    memory_monitoring: bool = True
    show_tooltips: bool = True
    animation_enabled: bool = True
    font_size: int = 10
    window_opacity: float = 1.0
    remember_window_state: bool = True
    show_status_bar: bool = True
    compact_mode: bool = False


@dataclass
class AutomationConfig:
    """Automation configuration settings"""
    enabled: bool = False
    check_interval_minutes: int = 60
    max_daily_searches: int = 100
    operating_hours_start: str = "09:00"
    operating_hours_end: str = "17:00"
    weekend_enabled: bool = False
    pause_on_error: bool = True
    max_consecutive_errors: int = 5
    notification_enabled: bool = True


@dataclass
class PerformanceConfig:
    """Performance monitoring configuration"""
    enable_monitoring: bool = True
    memory_warning_threshold_mb: int = 1024
    memory_critical_threshold_mb: int = 2048
    cpu_warning_threshold_percent: int = 80
    disk_warning_threshold_percent: int = 90
    log_performance_metrics: bool = True
    metrics_collection_interval: int = 60

class Config:
    """Enhanced configuration manager with validation and error handling"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize configuration
        
        Args:
            config_dir: Custom configuration directory path
        """
        self.logger = logging.getLogger(__name__)
        self.settings = QSettings("UK Business Lead Generator", "LeadGen")
        
        # Set up configuration directory
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path.home() / "UKLeadGen" / "config"
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "config.json"
        
        # Initialize typed configuration objects
        self.search_config = SearchConfig()
        self.analysis_config = AnalysisConfig()
        self.export_config = ExportConfig()
        self.ui_config = UIConfig()
        self.automation_config = AutomationConfig()
        self.performance_config = PerformanceConfig()
        
        self._init_default_settings()
        self._load_typed_config()
        self._validate_config()
    
    def _init_default_settings(self):
        """Initialize default settings if not already set"""
        # General settings
        if not self.settings.contains("general/data_folder"):
            self.settings.setValue(
                "general/data_folder",
                os.path.join(os.path.expanduser("~"), "UKLeadGen", "data")
            )
        
        if not self.settings.contains("general/keep_data_on_uninstall"):
            self.settings.setValue("general/keep_data_on_uninstall", True)
        
        # Search settings
        if not self.settings.contains("search/limit"):
            self.settings.setValue("search/limit", 20)
        
        if not self.settings.contains("search/analyze_websites"):
            self.settings.setValue("search/analyze_websites", True)
        
        if not self.settings.contains("search/use_selenium"):
            self.settings.setValue("search/use_selenium", True)
        
        # Analysis settings
        if not self.settings.contains("analysis/use_lighthouse"):
            self.settings.setValue("analysis/use_lighthouse", True)
        
        if not self.settings.contains("analysis/lighthouse_timeout"):
            self.settings.setValue("analysis/lighthouse_timeout", 60)
        
        if not self.settings.contains("analysis/use_fallback"):
            self.settings.setValue("analysis/use_fallback", True)
        
        if not self.settings.contains("analysis/max_threads"):
            self.settings.setValue("analysis/max_threads", 3)
        
        # Export settings
        if not self.settings.contains("export/default_format"):
            self.settings.setValue("export/default_format", "CSV")
        
        if not self.settings.contains("export/default_path"):
            self.settings.setValue(
                "export/default_path",
                os.path.join(os.path.expanduser("~"), "UKLeadGen", "exports")
            )
    
    def get(self, key, default=None):
        """
        Get a configuration value
        
        Args:
            key: Setting key (e.g., "general/data_folder")
            default: Default value if setting not found
            
        Returns:
            Setting value or default
        """
        return self.settings.value(key, default)
    
    def set(self, key, value):
        """
        Set a configuration value
        
        Args:
            key: Setting key (e.g., "general/data_folder")
            value: Setting value
        """
        self.settings.setValue(key, value)
    
    def get_data_folder(self):
        """Get the data folder path"""
        return self.get("general/data_folder")
    
    def get_export_folder(self):
        """Get the export folder path"""
        return self.get("export/default_path")
    
    def get_search_limit(self):
        """Get the default search limit"""
        return self.get("search/limit", 20)
    
    def should_analyze_websites(self):
        """Check if websites should be analyzed by default"""
        return self.get("search/analyze_websites", True)
    
    def should_use_selenium(self):
        """Check if Selenium should be used"""
        return self.get("search/use_selenium", True)
    
    def should_use_lighthouse(self):
        """Check if Lighthouse should be used"""
        return self.get("analysis/use_lighthouse", True)
    
    def get_lighthouse_timeout(self):
        """Get the Lighthouse timeout"""
        return self.get("analysis/lighthouse_timeout", 60)
    
    def should_use_fallback(self):
        """Check if fallback analysis should be used"""
        return self.get("analysis/use_fallback", True)
    
    def get_max_threads(self):
        """Get the maximum number of analysis threads"""
        return self.get("analysis/max_threads", 3)
    
    def get_default_export_format(self):
        """Get the default export format"""
        return self.get("export/default_format", "CSV")
    
    def _validate_config(self):
        """Validate configuration settings"""
        try:
            # Validate search limit
            limit = self.get_search_limit()
            if not isinstance(limit, int) or limit <= 0:
                logging.warning(f"Invalid search limit: {limit}, resetting to 20")
                self.set("search/limit", 20)
            
            # Validate max threads
            threads = self.get_max_threads()
            if not isinstance(threads, int) or threads <= 0 or threads > 10:
                logging.warning(f"Invalid max threads: {threads}, resetting to 3")
                self.set("analysis/max_threads", 3)
            
            # Validate timeout
            timeout = self.get_lighthouse_timeout()
            if not isinstance(timeout, int) or timeout <= 0:
                logging.warning(f"Invalid lighthouse timeout: {timeout}, resetting to 60")
                self.set("analysis/lighthouse_timeout", 60)
                
        except Exception as e:
            logging.error(f"Error validating config: {e}")
    
    def _load_typed_config(self) -> None:
        """Load typed configuration from JSON file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # Update configuration objects
                if 'search' in config_data:
                    self.search_config = SearchConfig(**config_data['search'])
                if 'analysis' in config_data:
                    self.analysis_config = AnalysisConfig(**config_data['analysis'])
                if 'export' in config_data:
                    self.export_config = ExportConfig(**config_data['export'])
                if 'ui' in config_data:
                    self.ui_config = UIConfig(**config_data['ui'])
                if 'automation' in config_data:
                    self.automation_config = AutomationConfig(**config_data['automation'])
                if 'performance' in config_data:
                    self.performance_config = PerformanceConfig(**config_data['performance'])
                
                self.logger.info("Typed configuration loaded successfully")
        except Exception as e:
            self.logger.warning(f"Error loading typed configuration: {e}")
    
    def save_typed_config(self) -> None:
        """Save typed configuration to JSON file"""
        try:
            config_data = {
                'search': asdict(self.search_config),
                'analysis': asdict(self.analysis_config),
                'export': asdict(self.export_config),
                'ui': asdict(self.ui_config),
                'automation': asdict(self.automation_config),
                'performance': asdict(self.performance_config)
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info("Typed configuration saved successfully")
        except (PermissionError, OSError, IOError) as e:
            self.logger.error(f"Error writing configuration file {self.config_file}: {e}")
            raise
        except (TypeError, ValueError) as e:
            self.logger.error(f"Error serializing configuration data: {e}")
            raise
    
    def get_typed_config(self, config_type: str) -> Any:
        """Get typed configuration object
        
        Args:
            config_type: Type of configuration ('search', 'analysis', etc.)
            
        Returns:
            Configuration object or None
        """
        config_map = {
            'search': self.search_config,
            'analysis': self.analysis_config,
            'export': self.export_config,
            'ui': self.ui_config,
            'automation': self.automation_config,
            'performance': self.performance_config
        }
        return config_map.get(config_type)
    
    def validate_typed_config(self) -> List[str]:
        """Validate typed configuration settings
        
        Returns:
            List of validation errors
        """
        errors = []
        
        # Validate search config
        if self.search_config.default_limit <= 0:
            errors.append("Search default_limit must be positive")
        if self.search_config.max_concurrent <= 0:
            errors.append("Search max_concurrent must be positive")
        if self.search_config.timeout <= 0:
            errors.append("Search timeout must be positive")
        
        # Validate analysis config
        if self.analysis_config.max_threads <= 0:
            errors.append("Analysis max_threads must be positive")
        if not 0 <= self.analysis_config.performance_threshold <= 100:
            errors.append("Analysis performance_threshold must be 0-100")
        
        # Validate UI config
        if self.ui_config.theme not in ["light", "dark", "auto"]:
            errors.append("UI theme must be 'light', 'dark', or 'auto'")
        if not 0.1 <= self.ui_config.window_opacity <= 1.0:
            errors.append("UI window_opacity must be 0.1-1.0")
        
        return errors
    
    def reset_to_defaults(self, section: Optional[str] = None) -> None:
        """Reset configuration to defaults
        
        Args:
            section: Specific section to reset, or None for all
        """
        if section is None or section == 'search':
            self.search_config = SearchConfig()
        if section is None or section == 'analysis':
            self.analysis_config = AnalysisConfig()
        if section is None or section == 'export':
            self.export_config = ExportConfig()
        if section is None or section == 'ui':
            self.ui_config = UIConfig()
        if section is None or section == 'automation':
            self.automation_config = AutomationConfig()
        if section is None or section == 'performance':
            self.performance_config = PerformanceConfig()
        
        self.logger.info(f"Reset configuration section: {section or 'all'}")


# Global configuration instance
_config_instance = None


def get_config() -> Config:
    """Get global configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance