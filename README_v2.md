# UK Business Lead Generator v2.0 🚀

**Advanced Business Lead Generation Tool with Smart Automation & Comprehensive Data Management**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Type Checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](http://mypy-lang.org/)

## 🌟 What's New in v2.0

This major update transforms the UK Business Lead Generator into a comprehensive, enterprise-grade solution with advanced automation, intelligent retry mechanisms, and robust data management capabilities.

### 🔥 Key Improvements

- **Smart Retry Automation System** - Intelligent task execution with multiple retry strategies
- **Advanced Error Handling** - Comprehensive error tracking and recovery mechanisms
- **Performance Monitoring** - Real-time system metrics and performance analytics
- **Intelligent Caching** - Multi-level caching with automatic expiration and cleanup
- **Data Validation Engine** - Advanced validation with scoring and consistency checks
- **Structured Logging** - JSON-based logging with context and categorization
- **Type Safety** - Full type annotations with mypy validation
- **Configuration Management** - Typed configuration system with validation
- **Development Tools** - Pre-commit hooks, code formatting, and quality checks

## 📋 Table of Contents

- [Features](#-features)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Architecture](#-architecture)
- [Configuration](#-configuration)
- [Usage Examples](#-usage-examples)
- [Development](#-development)
- [API Reference](#-api-reference)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

### 🤖 Smart Automation
- **Intelligent Retry Mechanisms**: Multiple retry strategies (exponential, linear, Fibonacci, custom)
- **Task Scheduling**: Priority-based task execution with dependency management
- **Concurrency Control**: Configurable parallel task execution
- **Progress Tracking**: Real-time progress monitoring and callbacks
- **Failure Recovery**: Automatic recovery from transient failures

### 📊 Performance & Monitoring
- **System Metrics**: CPU, memory, disk, and network monitoring
- **Performance Analytics**: Execution time tracking and optimization insights
- **Alert System**: Configurable performance alerts and thresholds
- **Resource Management**: Automatic resource cleanup and optimization
- **Metrics Export**: JSON and CSV export for external analysis

### 🛡️ Error Handling & Reliability
- **Centralized Error Management**: Structured error handling with categorization
- **Error Recovery**: Automatic retry and fallback mechanisms
- **Error Analytics**: Error pattern analysis and reporting
- **Debugging Support**: Enhanced debugging with context preservation
- **Exception Decorators**: Automatic error handling for functions

### 💾 Data Management
- **Advanced Validation**: Multi-level data validation with scoring
- **Consistency Checks**: Cross-field validation and business rule enforcement
- **Data Quality Metrics**: Comprehensive data quality scoring and reporting
- **Caching System**: Intelligent multi-level caching with automatic expiration
- **Data Export**: Multiple export formats with validation

### 🔧 Development & Quality
- **Type Safety**: Full type annotations with mypy validation
- **Code Quality**: Black formatting, flake8 linting, isort imports
- **Testing Framework**: Comprehensive test suite with coverage reporting
- **Documentation**: Sphinx-based documentation with auto-generation
- **Pre-commit Hooks**: Automatic code quality checks

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Git (for development)

### Quick Installation

```bash
# Clone the repository
git clone https://github.com/businesstools/uk-business-lead-generator.git
cd uk-business-lead-generator

# Run the setup script
python setup.py

# Start the application
python src/main.py
```

### Development Installation

```bash
# Install with development tools
python setup.py --dev

# Install pre-commit hooks
pre-commit install

# Run tests
pytest tests/ --cov=src/

# Run type checking
mypy src/

# Format code
black src/
isort src/
```

## ⚡ Quick Start

### Basic Usage

```python
from src.core.automation import AutomationManager
from src.utils.config import Config
from src.utils.advanced_logger import get_logger

# Initialize components
config = Config()
automation_manager = AutomationManager()
logger = get_logger("quickstart")

# Create and start automation
engine = automation_manager.create_campaign(
    name="Quick Lead Generation",
    search_terms=["restaurants London", "cafes Manchester"],
    max_results_per_day=100
)

# Start automation
engine.start()
logger.info("Automation started successfully")

# Monitor progress
status = engine.get_status()
print(f"Progress: {status['progress']}%")
print(f"Success Rate: {status['success_rate']}%")
```

### Advanced Configuration

```python
from src.core.automation import RetryConfig, RetryStrategy
from src.utils.performance_monitor import performance_monitor

# Configure smart retry mechanism
retry_config = RetryConfig(
    max_attempts=5,
    strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
    base_delay=1.0,
    max_delay=60.0,
    jitter=True
)

# Start performance monitoring
performance_monitor.start_monitoring()

# Create automation with custom settings
engine = automation_manager.create_campaign(
    name="Advanced Campaign",
    search_terms=["tech startups London"],
    retry_config=retry_config,
    max_concurrent_tasks=3,
    timeout=300.0
)
```

## 🏗️ Architecture

### Core Components

```
src/
├── core/
│   ├── automation.py      # Smart automation engine
│   ├── database.py        # Enhanced database management
│   └── scraper.py         # Web scraping with retry logic
├── utils/
│   ├── advanced_logger.py # Structured logging system
│   ├── error_handler.py   # Centralized error management
│   ├── performance_monitor.py # Performance analytics
│   ├── cache_manager.py   # Intelligent caching
│   ├── data_validator.py  # Data validation engine
│   └── config.py          # Typed configuration
├── gui/
│   └── main_window.py     # Enhanced GUI interface
└── tests/
    └── ...                # Comprehensive test suite
```

### Data Flow

1. **Configuration Loading**: Typed configuration with validation
2. **System Initialization**: Error handling, logging, monitoring setup
3. **Task Creation**: Smart task scheduling with retry configuration
4. **Execution**: Parallel execution with progress tracking
5. **Data Processing**: Validation, caching, and storage
6. **Monitoring**: Real-time performance and error tracking
7. **Export**: Validated data export in multiple formats

## ⚙️ Configuration

### Configuration Files

```json
// config/default_config.json
{
  "app": {
    "name": "UK Business Lead Generator",
    "version": "2.0.0",
    "debug": false
  },
  "automation": {
    "max_concurrent_tasks": 5,
    "default_timeout": 300,
    "retry_attempts": 3
  },
  "performance": {
    "monitoring_enabled": true,
    "metrics_retention_days": 30
  },
  "logging": {
    "level": "INFO",
    "max_file_size": "10MB",
    "backup_count": 5
  }
}
```

### Environment Variables

```bash
# Application settings
UKLG_DEBUG=false
UKLG_LOG_LEVEL=INFO
UKLG_DATA_DIR=./data

# Performance settings
UKLG_MAX_WORKERS=5
UKLG_CACHE_SIZE=1000
UKLG_MONITORING_INTERVAL=30

# Database settings
UKLG_DB_PATH=./data/businesses.db
UKLG_BACKUP_INTERVAL=3600
```

## 📖 Usage Examples

### Smart Retry Configuration

```python
from src.core.automation import RetryConfig, RetryStrategy

# Exponential backoff with jitter
retry_config = RetryConfig(
    max_attempts=5,
    strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
    base_delay=1.0,
    max_delay=60.0,
    jitter=True,
    backoff_multiplier=2.0
)

# Custom retry strategy
def custom_delay(attempt: int, base_delay: float) -> float:
    return min(base_delay * (attempt ** 1.5), 120.0)

custom_retry = RetryConfig(
    max_attempts=3,
    strategy=RetryStrategy.CUSTOM,
    custom_delay_func=custom_delay
)
```

### Performance Monitoring

```python
from src.utils.performance_monitor import performance_monitor

# Start monitoring
performance_monitor.start_monitoring()

# Add custom metrics
performance_monitor.add_metric("api_calls", 150, {"endpoint": "/search"})

# Time operations
with performance_monitor.time_operation("data_processing"):
    # Your code here
    process_data()

# Get performance report
report = performance_monitor.get_performance_report()
print(f"Average CPU: {report['avg_cpu']}%")
print(f"Memory usage: {report['memory_usage']}MB")
```

### Data Validation

```python
from src.utils.data_validator import data_validator

# Validate business data
business_data = {
    "name": "Example Restaurant",
    "email": "contact@example.com",
    "phone": "+44 20 1234 5678",
    "website": "https://example.com",
    "postcode": "SW1A 1AA"
}

result = data_validator.validate_business(business_data)
print(f"Validation score: {result.score}/100")
print(f"Issues found: {len(result.issues)}")

for issue in result.issues:
    print(f"- {issue.field}: {issue.message}")
```

### Advanced Logging

```python
from src.utils.advanced_logger import get_logger, LogCategory

# Get categorized logger
logger = get_logger("business_scraper")

# Log with context
logger.log_business_event(
    "business_found",
    business_id="12345",
    source="google_maps",
    metadata={"location": "London", "category": "restaurant"}
)

# Log performance metrics
logger.log_performance(
    "scraping_speed",
    duration=2.5,
    metadata={"pages_scraped": 10, "businesses_found": 25}
)

# Log with automatic context
with logger.context(user_id="user123", session_id="sess456"):
    logger.info("Processing user request")
    # All logs in this block will include the context
```

## 🛠️ Development

### Setting Up Development Environment

```bash
# Install development dependencies
pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install

# Run tests with coverage
pytest tests/ --cov=src/ --cov-report=html

# Type checking
mypy src/

# Code formatting
black src/
isort src/

# Linting
flake8 src/
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_automation.py

# Run with coverage
pytest --cov=src/ --cov-report=term-missing

# Run performance tests
pytest tests/test_performance.py -v
```

### Code Quality Checks

```bash
# Run all quality checks
pre-commit run --all-files

# Security scan
bandit -r src/

# Dependency vulnerability check
safety check

# Documentation build
sphinx-build -b html docs/ docs/_build/
```

## 📚 API Reference

### AutomationEngine

```python
class AutomationEngine:
    def start(self) -> None:
        """Start the automation engine."""
    
    def stop(self) -> None:
        """Stop the automation engine."""
    
    def pause(self) -> None:
        """Pause the automation engine."""
    
    def resume(self) -> None:
        """Resume the automation engine."""
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive automation status."""
```

### SmartRetryMechanism

```python
class SmartRetryMechanism:
    def execute_with_retry(
        self,
        task: AutomationTask,
        progress_callback: Optional[Callable] = None
    ) -> TaskResult:
        """Execute task with intelligent retry logic."""
    
    def get_retry_stats(self) -> Dict[str, Any]:
        """Get comprehensive retry statistics."""
```

### PerformanceMonitor

```python
class PerformanceMonitor:
    def start_monitoring(self) -> None:
        """Start system monitoring."""
    
    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
    
    def add_metric(self, name: str, value: float, metadata: Dict = None) -> None:
        """Add custom performance metric."""
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and quality checks
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Code Standards

- Follow PEP 8 style guidelines
- Use type hints for all functions
- Write comprehensive docstrings
- Add tests for new features
- Maintain test coverage above 90%

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with modern Python best practices
- Inspired by enterprise-grade automation tools
- Community feedback and contributions
- Open source libraries and frameworks

## 📞 Support

- **Documentation**: [Full Documentation](https://docs.example.com)
- **Issues**: [GitHub Issues](https://github.com/businesstools/uk-business-lead-generator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/businesstools/uk-business-lead-generator/discussions)
- **Email**: support@businesstools.com

---

**Made with ❤️ by the Business Tools Team**