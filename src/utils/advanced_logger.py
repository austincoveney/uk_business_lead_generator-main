"""Advanced logging system with structured logging and multiple handlers."""

import os
import json
import logging
import logging.handlers
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field, asdict
from pathlib import Path
import threading
from enum import Enum
import traceback
import sys


class LogLevel(Enum):
    """Custom log levels."""
    TRACE = 5
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class LogCategory(Enum):
    """Log categories for better organization."""
    SYSTEM = "system"
    BUSINESS = "business"
    PERFORMANCE = "performance"
    SECURITY = "security"
    USER_ACTION = "user_action"
    API = "api"
    DATABASE = "database"
    SCRAPING = "scraping"
    ANALYSIS = "analysis"
    AUTOMATION = "automation"


@dataclass
class LogContext:
    """Context information for structured logging."""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    operation_id: Optional[str] = None
    component: Optional[str] = None
    function: Optional[str] = None
    line_number: Optional[int] = None
    file_name: Optional[str] = None
    thread_id: Optional[str] = None
    process_id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class StructuredLogRecord:
    """Structured log record with rich metadata."""
    timestamp: datetime
    level: str
    message: str
    category: LogCategory
    context: LogContext = field(default_factory=LogContext)
    extra_data: Dict[str, Any] = field(default_factory=dict)
    exception_info: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        record = {
            'timestamp': self.timestamp.isoformat(),
            'level': self.level,
            'message': self.message,
            'category': self.category.value,
            'context': self.context.to_dict(),
            'extra_data': self.extra_data
        }
        
        if self.exception_info:
            record['exception'] = self.exception_info
        
        return record
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), default=str)


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging."""
    
    def __init__(self, include_context: bool = True, pretty_print: bool = False):
        super().__init__()
        self.include_context = include_context
        self.pretty_print = pretty_print
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        # Extract structured data if available
        structured_record = getattr(record, 'structured_record', None)
        
        if structured_record:
            if self.pretty_print:
                return json.dumps(structured_record.to_dict(), indent=2, default=str)
            else:
                return structured_record.to_json()
        
        # Fallback to standard formatting
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        if self.pretty_print:
            return json.dumps(log_data, indent=2, default=str)
        else:
            return json.dumps(log_data, default=str)


class ColoredConsoleFormatter(logging.Formatter):
    """Colored console formatter for better readability."""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def __init__(self, use_colors: bool = True):
        super().__init__()
        self.use_colors = use_colors and sys.stdout.isatty()
    
    def format(self, record: logging.LogRecord) -> str:
        """Format with colors if enabled."""
        if self.use_colors:
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            reset = self.COLORS['RESET']
            
            # Format: [TIMESTAMP] [LEVEL] [LOGGER] MESSAGE
            timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
            formatted = f"[{timestamp}] {color}[{record.levelname}]{reset} [{record.name}] {record.getMessage()}"
            
            if record.exc_info:
                formatted += f"\n{color}{self.formatException(record.exc_info)}{reset}"
            
            return formatted
        else:
            return super().format(record)


class AdvancedLogger:
    """Advanced logger with structured logging capabilities."""
    
    def __init__(self, 
                 name: str,
                 log_dir: str = "logs",
                 level: LogLevel = LogLevel.INFO,
                 enable_console: bool = True,
                 enable_file: bool = True,
                 enable_json: bool = True,
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5):
        
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level.value)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Thread-local storage for context
        self._local = threading.local()
        
        # Setup handlers
        if enable_console:
            self._setup_console_handler()
        
        if enable_file:
            self._setup_file_handler(max_file_size, backup_count)
        
        if enable_json:
            self._setup_json_handler(max_file_size, backup_count)
        
        # Performance tracking
        self._log_counts = {
            level.name: 0 for level in LogLevel
        }
        self._start_time = datetime.now()
    
    def _setup_console_handler(self) -> None:
        """Setup colored console handler."""
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(ColoredConsoleFormatter())
        self.logger.addHandler(handler)
    
    def _setup_file_handler(self, max_size: int, backup_count: int) -> None:
        """Setup rotating file handler."""
        file_path = self.log_dir / f"{self.name}.log"
        handler = logging.handlers.RotatingFileHandler(
            file_path, maxBytes=max_size, backupCount=backup_count
        )
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def _setup_json_handler(self, max_size: int, backup_count: int) -> None:
        """Setup JSON file handler for structured logs."""
        file_path = self.log_dir / f"{self.name}_structured.jsonl"
        handler = logging.handlers.RotatingFileHandler(
            file_path, maxBytes=max_size, backupCount=backup_count
        )
        
        handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(handler)
    
    def set_context(self, **kwargs) -> None:
        """Set logging context for current thread."""
        if not hasattr(self._local, 'context'):
            self._local.context = LogContext()
        
        for key, value in kwargs.items():
            if hasattr(self._local.context, key):
                setattr(self._local.context, key, value)
    
    def get_context(self) -> LogContext:
        """Get current logging context."""
        if not hasattr(self._local, 'context'):
            self._local.context = LogContext()
        return self._local.context
    
    def clear_context(self) -> None:
        """Clear logging context for current thread."""
        self._local.context = LogContext()
    
    def _create_structured_record(self, 
                                 level: LogLevel,
                                 message: str,
                                 category: LogCategory,
                                 extra_data: Optional[Dict[str, Any]] = None,
                                 exception_info: Optional[Exception] = None) -> StructuredLogRecord:
        """Create a structured log record."""
        context = self.get_context()
        
        # Add caller information
        frame = sys._getframe(3)  # Go up the call stack
        context.file_name = frame.f_code.co_filename
        context.function = frame.f_code.co_name
        context.line_number = frame.f_lineno
        context.thread_id = str(threading.current_thread().ident)
        context.process_id = os.getpid()
        
        # Handle exception info
        exc_info = None
        if exception_info:
            exc_info = {
                'type': type(exception_info).__name__,
                'message': str(exception_info),
                'traceback': traceback.format_exception(
                    type(exception_info), exception_info, exception_info.__traceback__
                )
            }
        
        return StructuredLogRecord(
            timestamp=datetime.now(),
            level=level.name,
            message=message,
            category=category,
            context=context,
            extra_data=extra_data or {},
            exception_info=exc_info
        )
    
    def _log(self, 
            level: LogLevel,
            message: str,
            category: LogCategory = LogCategory.SYSTEM,
            extra_data: Optional[Dict[str, Any]] = None,
            exception_info: Optional[Exception] = None) -> None:
        """Internal logging method."""
        
        # Create structured record
        structured_record = self._create_structured_record(
            level, message, category, extra_data, exception_info
        )
        
        # Create standard log record
        log_record = self.logger.makeRecord(
            self.logger.name,
            level.value,
            structured_record.context.file_name or "",
            structured_record.context.line_number or 0,
            message,
            (),
            exc_info=None
        )
        
        # Attach structured record
        log_record.structured_record = structured_record
        
        # Handle the record
        self.logger.handle(log_record)
        
        # Update counters
        self._log_counts[level.name] += 1
    
    def trace(self, message: str, category: LogCategory = LogCategory.SYSTEM, **kwargs) -> None:
        """Log trace message."""
        self._log(LogLevel.TRACE, message, category, kwargs)
    
    def debug(self, message: str, category: LogCategory = LogCategory.SYSTEM, **kwargs) -> None:
        """Log debug message."""
        self._log(LogLevel.DEBUG, message, category, kwargs)
    
    def info(self, message: str, category: LogCategory = LogCategory.SYSTEM, **kwargs) -> None:
        """Log info message."""
        self._log(LogLevel.INFO, message, category, kwargs)
    
    def warning(self, message: str, category: LogCategory = LogCategory.SYSTEM, **kwargs) -> None:
        """Log warning message."""
        self._log(LogLevel.WARNING, message, category, kwargs)
    
    def error(self, message: str, category: LogCategory = LogCategory.SYSTEM, 
             exception: Optional[Exception] = None, **kwargs) -> None:
        """Log error message."""
        self._log(LogLevel.ERROR, message, category, kwargs, exception)
    
    def critical(self, message: str, category: LogCategory = LogCategory.SYSTEM,
                exception: Optional[Exception] = None, **kwargs) -> None:
        """Log critical message."""
        self._log(LogLevel.CRITICAL, message, category, kwargs, exception)
    
    def log_business_event(self, event: str, details: Dict[str, Any]) -> None:
        """Log business-specific events."""
        self.info(f"Business event: {event}", LogCategory.BUSINESS, **details)
    
    def log_performance(self, operation: str, duration: float, **metrics) -> None:
        """Log performance metrics."""
        data = {'operation': operation, 'duration_seconds': duration, **metrics}
        self.info(f"Performance: {operation} completed in {duration:.3f}s", 
                 LogCategory.PERFORMANCE, **data)
    
    def log_user_action(self, user_id: str, action: str, details: Dict[str, Any]) -> None:
        """Log user actions."""
        self.set_context(user_id=user_id)
        self.info(f"User action: {action}", LogCategory.USER_ACTION, **details)
    
    def log_api_call(self, method: str, endpoint: str, status_code: int, 
                    duration: float, **details) -> None:
        """Log API calls."""
        data = {
            'method': method,
            'endpoint': endpoint,
            'status_code': status_code,
            'duration_seconds': duration,
            **details
        }
        level = LogLevel.ERROR if status_code >= 400 else LogLevel.INFO
        self._log(level, f"API {method} {endpoint} -> {status_code}", LogCategory.API, data)
    
    def log_database_operation(self, operation: str, table: str, duration: float, 
                              rows_affected: Optional[int] = None) -> None:
        """Log database operations."""
        data = {
            'operation': operation,
            'table': table,
            'duration_seconds': duration
        }
        if rows_affected is not None:
            data['rows_affected'] = rows_affected
        
        self.info(f"Database {operation} on {table}", LogCategory.DATABASE, **data)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get logging statistics."""
        runtime = datetime.now() - self._start_time
        total_logs = sum(self._log_counts.values())
        
        return {
            'logger_name': self.name,
            'runtime_seconds': runtime.total_seconds(),
            'total_logs': total_logs,
            'logs_per_level': self._log_counts.copy(),
            'logs_per_second': total_logs / runtime.total_seconds() if runtime.total_seconds() > 0 else 0
        }
    
    def export_logs(self, output_file: str, start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None, levels: Optional[List[LogLevel]] = None) -> None:
        """Export logs to file with filtering."""
        # This is a simplified implementation
        # In a real system, you'd read from the log files and filter
        stats = self.get_statistics()
        
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'filter_criteria': {
                'start_time': start_time.isoformat() if start_time else None,
                'end_time': end_time.isoformat() if end_time else None,
                'levels': [level.name for level in levels] if levels else None
            },
            'statistics': stats
        }
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)


# Global logger registry
_loggers: Dict[str, AdvancedLogger] = {}
_default_config = {
    'log_dir': 'logs',
    'level': LogLevel.INFO,
    'enable_console': True,
    'enable_file': True,
    'enable_json': True
}


def get_logger(name: str, **config) -> AdvancedLogger:
    """Get or create a logger with the given name."""
    if name not in _loggers:
        # Merge with default config
        logger_config = {**_default_config, **config}
        _loggers[name] = AdvancedLogger(name, **logger_config)
    
    return _loggers[name]


def configure_logging(log_dir: str = "logs", level: LogLevel = LogLevel.INFO,
                     enable_console: bool = True, enable_file: bool = True,
                     enable_json: bool = True) -> None:
    """Configure global logging settings."""
    global _default_config
    _default_config.update({
        'log_dir': log_dir,
        'level': level,
        'enable_console': enable_console,
        'enable_file': enable_file,
        'enable_json': enable_json
    })


def log_context(**kwargs):
    """Decorator to set logging context for a function."""
    def decorator(func):
        def wrapper(*args, **func_kwargs):
            logger = get_logger(func.__module__)
            
            # Set context
            logger.set_context(
                component=func.__module__,
                function=func.__name__,
                **kwargs
            )
            
            try:
                return func(*args, **func_kwargs)
            finally:
                logger.clear_context()
        
        return wrapper
    return decorator