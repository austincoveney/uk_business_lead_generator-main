# Configuration handling
"""
Configuration utility for UK Business Lead Generator
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from PySide6.QtCore import QSettings

class Config:
    """Enhanced configuration manager with validation and error handling"""
    
    def __init__(self):
        """Initialize configuration"""
        self.settings = QSettings("UK Business Lead Generator", "LeadGen")
        self._init_default_settings()
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