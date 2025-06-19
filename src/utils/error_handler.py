"""Centralized error handling system for UK Business Lead Generator"""

import sys
import traceback
import logging
import functools
import threading
from typing import Any, Callable, Dict, List, Optional, Type, Union
from datetime import datetime
from pathlib import Path
from enum import Enum
from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox, QWidget


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better classification"""
    NETWORK = "network"
    DATABASE = "database"
    SCRAPING = "scraping"
    ANALYSIS = "analysis"
    EXPORT = "export"
    UI = "ui"
    CONFIG = "config"
    AUTOMATION = "automation"
    SYSTEM = "system"
    VALIDATION = "validation"
    UNKNOWN = "unknown"


@dataclass
class ErrorInfo:
    """Structured error information"""
    error_id: str
    timestamp: datetime
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    details: str
    traceback_info: str
    context: Dict[str, Any]
    user_action: Optional[str] = None
    resolution_steps: List[str] = None
    
    def __post_init__(self):
        if self.resolution_steps is None:
            self.resolution_steps = []


class ErrorHandler(QObject):
    """Centralized error handling system"""
    
    # Signals for error notifications
    error_occurred = Signal(ErrorInfo)
    critical_error = Signal(ErrorInfo)
    
    def __init__(self, log_dir: Optional[str] = None):
        """Initialize error handler
        
        Args:
            log_dir: Directory for error logs
        """
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        
        # Set up error log directory
        if log_dir:
            self.error_log_dir = Path(log_dir)
        else:
            self.error_log_dir = Path.home() / "UKLeadGen" / "logs" / "errors"
        
        self.error_log_dir.mkdir(parents=True, exist_ok=True)
        
        # Error tracking
        self.error_history: List[ErrorInfo] = []
        self.error_counts: Dict[str, int] = {}
        
        # Set up error log file
        self._setup_error_logging()
        
        # Install global exception handler
        self._install_exception_handler()
    
    def _setup_error_logging(self) -> None:
        """Set up dedicated error logging"""
        error_log_file = self.error_log_dir / "errors.log"
        
        # Create error-specific logger
        self.error_logger = logging.getLogger("error_handler")
        self.error_logger.setLevel(logging.ERROR)
        
        # File handler for errors
        file_handler = logging.FileHandler(error_log_file)
        file_handler.setLevel(logging.ERROR)
        
        # Detailed formatter for error logs
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(name)s - %(funcName)s:%(lineno)d\n'
            'Message: %(message)s\n'
            'Details: %(details)s\n'
            'Context: %(context)s\n'
            '%(separator)s\n',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        self.error_logger.addHandler(file_handler)
    
    def _install_exception_handler(self) -> None:
        """Install global exception handler"""
        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            
            # Create error info for unhandled exceptions
            error_info = ErrorInfo(
                error_id=self._generate_error_id(),
                timestamp=datetime.now(),
                severity=ErrorSeverity.CRITICAL,
                category=ErrorCategory.SYSTEM,
                message=f"Unhandled {exc_type.__name__}: {exc_value}",
                details=str(exc_value),
                traceback_info=''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)),
                context={"exception_type": exc_type.__name__},
                resolution_steps=["Restart the application", "Check logs for details", "Report bug if persistent"]
            )
            
            self.handle_error(error_info)
        
        sys.excepthook = handle_exception
    
    def _generate_error_id(self) -> str:
        """Generate unique error ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"ERR_{timestamp}_{len(self.error_history):04d}"
    
    def handle_error(
        self,
        error: Union[Exception, ErrorInfo],
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        context: Optional[Dict[str, Any]] = None,
        user_action: Optional[str] = None,
        show_dialog: bool = True
    ) -> ErrorInfo:
        """Handle an error with comprehensive logging and user notification
        
        Args:
            error: Exception or ErrorInfo object
            severity: Error severity level
            category: Error category
            context: Additional context information
            user_action: Action user was performing when error occurred
            show_dialog: Whether to show error dialog to user
            
        Returns:
            ErrorInfo object
        """
        if isinstance(error, ErrorInfo):
            error_info = error
        else:
            error_info = self._create_error_info(
                error, severity, category, context, user_action
            )
        
        # Add to error history
        self.error_history.append(error_info)
        
        # Update error counts
        error_key = f"{error_info.category.value}_{error_info.message[:50]}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # Log the error
        self._log_error(error_info)
        
        # Emit signals
        self.error_occurred.emit(error_info)
        if error_info.severity == ErrorSeverity.CRITICAL:
            self.critical_error.emit(error_info)
        
        # Show user dialog if requested
        if show_dialog:
            self._show_error_dialog(error_info)
        
        return error_info
    
    def _create_error_info(
        self,
        error: Exception,
        severity: ErrorSeverity,
        category: ErrorCategory,
        context: Optional[Dict[str, Any]],
        user_action: Optional[str]
    ) -> ErrorInfo:
        """Create ErrorInfo from exception"""
        return ErrorInfo(
            error_id=self._generate_error_id(),
            timestamp=datetime.now(),
            severity=severity,
            category=category,
            message=str(error),
            details=f"{type(error).__name__}: {error}",
            traceback_info=traceback.format_exc(),
            context=context or {},
            user_action=user_action,
            resolution_steps=self._get_resolution_steps(error, category)
        )
    
    def _get_resolution_steps(self, error: Exception, category: ErrorCategory) -> List[str]:
        """Get suggested resolution steps based on error type and category"""
        steps = []
        
        if category == ErrorCategory.NETWORK:
            steps.extend([
                "Check internet connection",
                "Verify website URL is accessible",
                "Try again in a few minutes",
                "Check firewall settings"
            ])
        elif category == ErrorCategory.DATABASE:
            steps.extend([
                "Check database file permissions",
                "Ensure sufficient disk space",
                "Restart the application",
                "Check database integrity"
            ])
        elif category == ErrorCategory.SCRAPING:
            steps.extend([
                "Check if target website is accessible",
                "Verify website structure hasn't changed",
                "Try with different search parameters",
                "Check rate limiting settings"
            ])
        elif category == ErrorCategory.ANALYSIS:
            steps.extend([
                "Check if website is responsive",
                "Verify analysis tools are installed",
                "Try with simpler analysis settings",
                "Check system resources"
            ])
        elif category == ErrorCategory.EXPORT:
            steps.extend([
                "Check file permissions",
                "Ensure sufficient disk space",
                "Verify export path exists",
                "Try different export format"
            ])
        elif category == ErrorCategory.UI:
            steps.extend([
                "Restart the application",
                "Check display settings",
                "Try different theme",
                "Update graphics drivers"
            ])
        else:
            steps.extend([
                "Restart the application",
                "Check system resources",
                "Review error logs",
                "Contact support if persistent"
            ])
        
        return steps
    
    def _log_error(self, error_info: ErrorInfo) -> None:
        """Log error with detailed information"""
        log_data = {
            'details': error_info.details,
            'context': str(error_info.context),
            'separator': '-' * 80
        }
        
        self.error_logger.error(
            f"[{error_info.error_id}] {error_info.message}",
            extra=log_data
        )
        
        # Also log to main logger based on severity
        if error_info.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(f"Critical error: {error_info.message}")
        elif error_info.severity == ErrorSeverity.HIGH:
            self.logger.error(f"High severity error: {error_info.message}")
        elif error_info.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(f"Medium severity error: {error_info.message}")
        else:
            self.logger.info(f"Low severity error: {error_info.message}")
    
    def _show_error_dialog(self, error_info: ErrorInfo) -> None:
        """Show error dialog to user"""
        try:
            # Determine dialog icon based on severity
            if error_info.severity == ErrorSeverity.CRITICAL:
                icon = QMessageBox.Critical
                title = "Critical Error"
            elif error_info.severity == ErrorSeverity.HIGH:
                icon = QMessageBox.Warning
                title = "Error"
            else:
                icon = QMessageBox.Information
                title = "Notice"
            
            # Create message box
            msg_box = QMessageBox()
            msg_box.setIcon(icon)
            msg_box.setWindowTitle(title)
            msg_box.setText(error_info.message)
            
            # Add detailed information
            details = f"Error ID: {error_info.error_id}\n"
            details += f"Time: {error_info.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
            details += f"Category: {error_info.category.value.title()}\n\n"
            
            if error_info.user_action:
                details += f"User Action: {error_info.user_action}\n\n"
            
            if error_info.resolution_steps:
                details += "Suggested Solutions:\n"
                for i, step in enumerate(error_info.resolution_steps, 1):
                    details += f"{i}. {step}\n"
            
            msg_box.setDetailedText(details)
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()
            
        except Exception as e:
            # Fallback logging if dialog fails
            self.logger.error(f"Failed to show error dialog: {e}")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics"""
        if not self.error_history:
            return {"total_errors": 0}
        
        # Count by severity
        severity_counts = {}
        for severity in ErrorSeverity:
            severity_counts[severity.value] = sum(
                1 for error in self.error_history 
                if error.severity == severity
            )
        
        # Count by category
        category_counts = {}
        for category in ErrorCategory:
            category_counts[category.value] = sum(
                1 for error in self.error_history 
                if error.category == category
            )
        
        # Recent errors (last 24 hours)
        recent_errors = [
            error for error in self.error_history
            if (datetime.now() - error.timestamp).total_seconds() < 86400
        ]
        
        return {
            "total_errors": len(self.error_history),
            "recent_errors": len(recent_errors),
            "severity_breakdown": severity_counts,
            "category_breakdown": category_counts,
            "most_common_errors": dict(sorted(
                self.error_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5])
        }
    
    def clear_error_history(self, older_than_days: int = 30) -> int:
        """Clear old errors from history
        
        Args:
            older_than_days: Clear errors older than this many days
            
        Returns:
            Number of errors cleared
        """
        cutoff_date = datetime.now().timestamp() - (older_than_days * 86400)
        
        original_count = len(self.error_history)
        self.error_history = [
            error for error in self.error_history
            if error.timestamp.timestamp() > cutoff_date
        ]
        
        cleared_count = original_count - len(self.error_history)
        self.logger.info(f"Cleared {cleared_count} old errors from history")
        
        return cleared_count


def error_handler_decorator(
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    show_dialog: bool = True,
    reraise: bool = False
):
    """Decorator for automatic error handling
    
    Args:
        severity: Default error severity
        category: Error category
        show_dialog: Whether to show error dialog
        reraise: Whether to reraise the exception after handling
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Get global error handler
                error_handler = get_error_handler()
                
                # Handle the error
                error_handler.handle_error(
                    e,
                    severity=severity,
                    category=category,
                    context={
                        "function": func.__name__,
                        "args": str(args)[:200],
                        "kwargs": str(kwargs)[:200]
                    },
                    show_dialog=show_dialog
                )
                
                if reraise:
                    raise
                
                return None
        
        return wrapper
    return decorator


# Global error handler instance
_error_handler = None
_error_handler_lock = threading.Lock()


def get_error_handler() -> ErrorHandler:
    """Get global error handler instance"""
    global _error_handler
    if _error_handler is None:
        with _error_handler_lock:
            # Double-check locking pattern
            if _error_handler is None:
                _error_handler = ErrorHandler()
    return _error_handler


def handle_error(
    error: Union[Exception, ErrorInfo],
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    **kwargs
) -> ErrorInfo:
    """Convenience function for error handling"""
    return get_error_handler().handle_error(error, severity, category, **kwargs)