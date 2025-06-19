"""Configurable timing system for the UK Business Lead Generator.

This module provides centralized timing configuration to replace hardcoded
sleep values throughout the application, improving maintainability and
allowing environment-specific optimizations.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Optional
from enum import Enum


class TimingProfile(Enum):
    """Predefined timing profiles for different environments."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"
    AGGRESSIVE = "aggressive"  # For high-performance scenarios


@dataclass
class ScrapingTimings:
    """Timing configuration for web scraping operations."""
    selenium_init_delay: float = 1.0
    page_load_timeout: float = 10.0
    element_wait_timeout: float = 5.0
    retry_delay: float = 3.0
    fallback_delay: float = 2.0
    navigation_delay: float = 1.0
    form_submission_delay: float = 2.0
    captcha_detection_delay: float = 3.0
    rate_limit_delay: float = 3.0
    request_delay: float = 2.0
    
    def __post_init__(self):
        """Validate timing values."""
        for field_name, value in self.__dict__.items():
            if not isinstance(value, (int, float)) or value < 0:
                raise ValueError(f"Invalid timing value for {field_name}: {value}")


@dataclass
class AutomationTimings:
    """Timing configuration for automation operations."""
    task_check_interval: float = 30.0
    retry_check_interval: float = 60.0
    status_update_interval: float = 5.0
    cleanup_interval: float = 300.0  # 5 minutes
    thread_join_timeout: float = 5.0
    
    def __post_init__(self):
        """Validate timing values."""
        for field_name, value in self.__dict__.items():
            if not isinstance(value, (int, float)) or value < 0:
                raise ValueError(f"Invalid timing value for {field_name}: {value}")


@dataclass
class NetworkTimings:
    """Timing configuration for network operations."""
    request_timeout: float = 10.0
    connection_timeout: float = 5.0
    read_timeout: float = 15.0
    retry_backoff_base: float = 1.0
    retry_backoff_max: float = 60.0
    dns_timeout: float = 3.0
    
    def __post_init__(self):
        """Validate timing values."""
        for field_name, value in self.__dict__.items():
            if not isinstance(value, (int, float)) or value < 0:
                raise ValueError(f"Invalid timing value for {field_name}: {value}")


@dataclass
class DatabaseTimings:
    """Timing configuration for database operations."""
    connection_timeout: float = 30.0
    query_timeout: float = 10.0
    transaction_timeout: float = 60.0
    backup_timeout: float = 300.0
    
    def __post_init__(self):
        """Validate timing values."""
        for field_name, value in self.__dict__.items():
            if not isinstance(value, (int, float)) or value < 0:
                raise ValueError(f"Invalid timing value for {field_name}: {value}")


@dataclass
class TimingConfiguration:
    """Complete timing configuration for the application."""
    profile: TimingProfile = TimingProfile.PRODUCTION
    scraping: ScrapingTimings = field(default_factory=ScrapingTimings)
    automation: AutomationTimings = field(default_factory=AutomationTimings)
    network: NetworkTimings = field(default_factory=NetworkTimings)
    database: DatabaseTimings = field(default_factory=DatabaseTimings)
    
    @classmethod
    def for_profile(cls, profile: TimingProfile) -> 'TimingConfiguration':
        """Create timing configuration for a specific profile."""
        if profile == TimingProfile.DEVELOPMENT:
            return cls._development_config()
        elif profile == TimingProfile.TESTING:
            return cls._testing_config()
        elif profile == TimingProfile.PRODUCTION:
            return cls._production_config()
        elif profile == TimingProfile.AGGRESSIVE:
            return cls._aggressive_config()
        else:
            raise ValueError(f"Unknown timing profile: {profile}")
    
    @classmethod
    def _development_config(cls) -> 'TimingConfiguration':
        """Development environment configuration - shorter timeouts for faster feedback."""
        return cls(
            profile=TimingProfile.DEVELOPMENT,
            scraping=ScrapingTimings(
                selenium_init_delay=0.5,
                page_load_timeout=8.0,
                element_wait_timeout=3.0,
                retry_delay=1.0,
                fallback_delay=1.0,
                navigation_delay=0.5,
                form_submission_delay=1.0,
                captcha_detection_delay=2.0,
                rate_limit_delay=1.0
            ),
            automation=AutomationTimings(
                task_check_interval=10.0,
                retry_check_interval=30.0,
                status_update_interval=2.0,
                cleanup_interval=120.0,
                thread_join_timeout=3.0
            ),
            network=NetworkTimings(
                request_timeout=8.0,
                connection_timeout=3.0,
                read_timeout=10.0,
                retry_backoff_base=0.5,
                retry_backoff_max=30.0,
                dns_timeout=2.0
            ),
            database=DatabaseTimings(
                connection_timeout=15.0,
                query_timeout=5.0,
                transaction_timeout=30.0,
                backup_timeout=120.0
            )
        )
    
    @classmethod
    def _testing_config(cls) -> 'TimingConfiguration':
        """Testing environment configuration - minimal delays for fast test execution."""
        return cls(
            profile=TimingProfile.TESTING,
            scraping=ScrapingTimings(
                selenium_init_delay=0.1,
                page_load_timeout=5.0,
                element_wait_timeout=2.0,
                retry_delay=0.5,
                fallback_delay=0.5,
                navigation_delay=0.1,
                form_submission_delay=0.5,
                captcha_detection_delay=1.0,
                rate_limit_delay=0.5
            ),
            automation=AutomationTimings(
                task_check_interval=1.0,
                retry_check_interval=5.0,
                status_update_interval=0.5,
                cleanup_interval=30.0,
                thread_join_timeout=1.0
            ),
            network=NetworkTimings(
                request_timeout=5.0,
                connection_timeout=2.0,
                read_timeout=5.0,
                retry_backoff_base=0.1,
                retry_backoff_max=10.0,
                dns_timeout=1.0
            ),
            database=DatabaseTimings(
                connection_timeout=10.0,
                query_timeout=3.0,
                transaction_timeout=15.0,
                backup_timeout=60.0
            )
        )
    
    @classmethod
    def _production_config(cls) -> 'TimingConfiguration':
        """Production environment configuration - balanced timeouts for reliability."""
        return cls(
            profile=TimingProfile.PRODUCTION,
            scraping=ScrapingTimings(
                selenium_init_delay=1.0,
                page_load_timeout=10.0,
                element_wait_timeout=5.0,
                retry_delay=3.0,
                fallback_delay=2.0,
                navigation_delay=1.0,
                form_submission_delay=2.0,
                captcha_detection_delay=3.0,
                rate_limit_delay=3.0
            ),
            automation=AutomationTimings(
                task_check_interval=30.0,
                retry_check_interval=60.0,
                status_update_interval=5.0,
                cleanup_interval=300.0,
                thread_join_timeout=5.0
            ),
            network=NetworkTimings(
                request_timeout=10.0,
                connection_timeout=5.0,
                read_timeout=15.0,
                retry_backoff_base=1.0,
                retry_backoff_max=60.0,
                dns_timeout=3.0
            ),
            database=DatabaseTimings(
                connection_timeout=30.0,
                query_timeout=10.0,
                transaction_timeout=60.0,
                backup_timeout=300.0
            )
        )
    
    @classmethod
    def _aggressive_config(cls) -> 'TimingConfiguration':
        """Aggressive configuration - shorter timeouts for high-performance scenarios."""
        return cls(
            profile=TimingProfile.AGGRESSIVE,
            scraping=ScrapingTimings(
                selenium_init_delay=0.5,
                page_load_timeout=6.0,
                element_wait_timeout=3.0,
                retry_delay=1.5,
                fallback_delay=1.0,
                navigation_delay=0.5,
                form_submission_delay=1.0,
                captcha_detection_delay=2.0,
                rate_limit_delay=2.0
            ),
            automation=AutomationTimings(
                task_check_interval=15.0,
                retry_check_interval=30.0,
                status_update_interval=3.0,
                cleanup_interval=180.0,
                thread_join_timeout=3.0
            ),
            network=NetworkTimings(
                request_timeout=6.0,
                connection_timeout=3.0,
                read_timeout=8.0,
                retry_backoff_base=0.5,
                retry_backoff_max=30.0,
                dns_timeout=2.0
            ),
            database=DatabaseTimings(
                connection_timeout=20.0,
                query_timeout=6.0,
                transaction_timeout=30.0,
                backup_timeout=180.0
            )
        )
    
    def to_dict(self) -> Dict:
        """Convert configuration to dictionary format."""
        return {
            'profile': self.profile.value,
            'scraping': self.scraping.__dict__,
            'automation': self.automation.__dict__,
            'network': self.network.__dict__,
            'database': self.database.__dict__
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TimingConfiguration':
        """Create configuration from dictionary."""
        profile = TimingProfile(data.get('profile', TimingProfile.PRODUCTION.value))
        
        scraping_data = data.get('scraping', {})
        automation_data = data.get('automation', {})
        network_data = data.get('network', {})
        database_data = data.get('database', {})
        
        return cls(
            profile=profile,
            scraping=ScrapingTimings(**scraping_data),
            automation=AutomationTimings(**automation_data),
            network=NetworkTimings(**network_data),
            database=DatabaseTimings(**database_data)
        )


class TimingManager:
    """Manager for timing configuration throughout the application."""
    
    def __init__(self, config: Optional[TimingConfiguration] = None):
        """Initialize timing manager with configuration."""
        self._config = config or TimingConfiguration.for_profile(TimingProfile.PRODUCTION)
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Timing manager initialized with profile: {self._config.profile.value}")
    
    @property
    def config(self) -> TimingConfiguration:
        """Get current timing configuration."""
        return self._config
    
    def update_config(self, config: TimingConfiguration) -> None:
        """Update timing configuration."""
        old_profile = self._config.profile
        self._config = config
        self.logger.info(f"Timing configuration updated from {old_profile.value} to {config.profile.value}")
    
    def set_profile(self, profile: TimingProfile) -> None:
        """Set timing profile."""
        self.update_config(TimingConfiguration.for_profile(profile))
    
    def get_scraping_delay(self, operation: str) -> float:
        """Get delay for specific scraping operation."""
        delays = {
            'selenium_init': self._config.scraping.selenium_init_delay,
            'retry': self._config.scraping.retry_delay,
            'fallback': self._config.scraping.fallback_delay,
            'navigation': self._config.scraping.navigation_delay,
            'form_submission': self._config.scraping.form_submission_delay,
            'captcha_detection': self._config.scraping.captcha_detection_delay,
            'rate_limit': self._config.scraping.rate_limit_delay
        }
        
        delay = delays.get(operation)
        if delay is None:
            self.logger.warning(f"Unknown scraping operation: {operation}, using default delay of 1.0")
            return 1.0
        
        return delay
    
    def get_automation_interval(self, operation: str) -> float:
        """Get interval for specific automation operation."""
        intervals = {
            'task_check': self._config.automation.task_check_interval,
            'retry_check': self._config.automation.retry_check_interval,
            'status_update': self._config.automation.status_update_interval,
            'cleanup': self._config.automation.cleanup_interval
        }
        
        interval = intervals.get(operation)
        if interval is None:
            self.logger.warning(f"Unknown automation operation: {operation}, using default interval of 30.0")
            return 30.0
        
        return interval
    
    def get_network_timeout(self, operation: str) -> float:
        """Get timeout for specific network operation."""
        timeouts = {
            'request': self._config.network.request_timeout,
            'connection': self._config.network.connection_timeout,
            'read': self._config.network.read_timeout,
            'dns': self._config.network.dns_timeout
        }
        
        timeout = timeouts.get(operation)
        if timeout is None:
            self.logger.warning(f"Unknown network operation: {operation}, using default timeout of 10.0")
            return 10.0
        
        return timeout
    
    def get_database_timeout(self, operation: str) -> float:
        """Get timeout for specific database operation."""
        timeouts = {
            'connection': self._config.database.connection_timeout,
            'query': self._config.database.query_timeout,
            'transaction': self._config.database.transaction_timeout,
            'backup': self._config.database.backup_timeout
        }
        
        timeout = timeouts.get(operation)
        if timeout is None:
            self.logger.warning(f"Unknown database operation: {operation}, using default timeout of 30.0")
            return 30.0
        
        return timeout


# Global timing manager instance
_timing_manager: Optional[TimingManager] = None


def get_timing_manager() -> TimingManager:
    """Get the global timing manager instance."""
    global _timing_manager
    if _timing_manager is None:
        _timing_manager = TimingManager()
    return _timing_manager


def set_timing_profile(profile: TimingProfile) -> None:
    """Set the global timing profile."""
    get_timing_manager().set_profile(profile)


def get_delay(category: str, operation: str) -> float:
    """Convenience function to get delay/timeout for any operation."""
    manager = get_timing_manager()
    
    if category == 'scraping':
        return manager.get_scraping_delay(operation)
    elif category == 'automation':
        return manager.get_automation_interval(operation)
    elif category == 'network':
        return manager.get_network_timeout(operation)
    elif category == 'database':
        return manager.get_database_timeout(operation)
    else:
        logging.warning(f"Unknown timing category: {category}, using default delay of 1.0")
        return 1.0