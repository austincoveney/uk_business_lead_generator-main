# UK Business Lead Generator 🇬🇧

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A powerful, comprehensive tool for finding and analyzing UK businesses with advanced website analysis capabilities. Built for sales teams, marketers, and business developers who need high-quality lead generation.

## ✨ Key Features

### 🔍 **Multi-Source Business Discovery**
- Search across multiple UK business directories simultaneously
- Advanced filtering by location, industry, and business size
- Intelligent duplicate detection and merging
- Real-time search progress tracking

### 📊 **Advanced Website Analysis**
- **Performance Scoring**: Page load times, Core Web Vitals
- **SEO Analysis**: Meta tags, structured data, keyword optimization
- **Accessibility Testing**: WCAG compliance checking
- **Best Practices**: Security, mobile-friendliness, modern standards
- **Content Quality Assessment**: Readability and engagement metrics

### 📞 **Contact Intelligence**
- Automatic extraction of emails, phone numbers, and social media
- Contact validation and verification
- Social media presence detection
- Business size classification

### 💾 **Data Management**
- SQLite database with optimized performance
- Advanced export options (CSV, JSON, Excel)
- Search history and campaign tracking
- Data backup and recovery

### 🎨 **Modern User Interface**
- Intuitive GUI built with PySide6
- Real-time memory monitoring
- Progress tracking and notifications
- Customizable themes and layouts

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** (3.9+ recommended)
- **Chrome Browser** (for advanced web analysis)
- **4GB RAM minimum** (8GB recommended for large datasets)

### Installation

#### Option 1: Standard Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/uk_business_lead_generator.git
cd uk_business_lead_generator

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python src/main.py
```

#### Option 2: Development Installation

```bash
# Install with development dependencies
pip install -r requirements.txt
pip install -e .

# Set up pre-commit hooks
pre-commit install

# Run tests
pytest tests/
```

#### Option 3: Executable (Coming Soon)

Download the latest release from the [Releases](https://github.com/yourusername/uk_business_lead_generator/releases) page.

## 📖 Usage Guide

### Basic Workflow

1. **Launch Application**
   ```bash
   python src/main.py
   ```

2. **Configure Search**
   - Enter UK location (e.g., "London", "Manchester", "SW1A 1AA")
   - Specify business category (optional)
   - Set search limits and filters

3. **Execute Search**
   - Click "Search" to begin discovery
   - Monitor progress in real-time
   - Review found businesses

4. **Analyze Results**
   - Click any business for detailed analysis
   - Review performance scores and recommendations
   - Check contact information and social presence

5. **Export Data**
   - Choose export format (CSV, JSON, Excel)
   - Select specific fields to include
   - Save to desired location

### Advanced Features

#### 🔧 **Custom Analysis Settings**
```python
# Configure analysis parameters
config = {
    'lighthouse_timeout': 60,
    'max_threads': 3,
    'enable_screenshots': False,  # Disabled by default
    'deep_analysis': True
}
```

#### 📊 **Batch Processing**
- Process multiple locations simultaneously
- Schedule automated searches
- Bulk export and reporting

#### 🎯 **Lead Scoring**
- Automatic priority calculation
- Custom scoring criteria
- Lead qualification filters

## ⚙️ Configuration

### Application Settings

Configure the application through the GUI settings dialog or by editing configuration files:

```json
{
  "search": {
    "default_limit": 50,
    "max_concurrent": 3,
    "timeout": 30
  },
  "analysis": {
    "lighthouse_timeout": 60,
    "enable_core_web_vitals": true,
    "screenshot_enabled": false,
    "max_threads": 3
  },
  "export": {
    "default_format": "CSV",
    "include_analysis": true,
    "auto_backup": true
  },
  "ui": {
    "theme": "light",
    "auto_save": true,
    "memory_monitoring": true
  }
}
```

### Environment Variables

```bash
# Optional: Set custom data directory
export LEAD_GEN_DATA_DIR="/path/to/data"

# Optional: Enable debug logging
export LEAD_GEN_DEBUG=1

# Optional: Set custom Chrome path
export CHROME_PATH="/path/to/chrome"
```

### Performance Tuning

- **Memory Usage**: Adjust `max_threads` based on available RAM
- **Network**: Configure timeouts for slow connections
- **Storage**: Set up automatic cleanup for old data

## 🛠️ Development

### Project Architecture

```
uk_business_lead_generator/
├── src/
│   ├── core/                 # Core business logic
│   │   ├── analyzer.py       # Website analysis engine
│   │   ├── database.py       # Data persistence layer
│   │   └── scraper.py        # Business discovery engine
│   ├── gui/                  # User interface components
│   │   ├── main_window.py    # Main application window
│   │   ├── results_panel.py  # Results display
│   │   └── search_panel.py   # Search interface
│   ├── utils/                # Utility modules
│   │   ├── analytics.py      # Data analysis tools
│   │   ├── config.py         # Configuration management
│   │   └── export_manager.py # Export functionality
│   └── main.py               # Application entry point
├── tests/                    # Comprehensive test suite
├── docs/                     # Documentation
├── build_scripts/            # Build and deployment
└── .github/                  # CI/CD workflows
```

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install

# Run code formatting
black src/ tests/
isort src/ tests/

# Run linting
flake8 src/ tests/
mypy src/

# Run tests with coverage
pytest tests/ --cov=src --cov-report=html
```

### Contributing Guidelines

1. **Fork & Clone**: Fork the repository and clone your fork
2. **Branch**: Create a feature branch (`git checkout -b feature/amazing-feature`)
3. **Code**: Write clean, documented code following our style guide
4. **Test**: Add comprehensive tests for new functionality
5. **Commit**: Use conventional commit messages
6. **Push**: Push to your fork and submit a pull request

### Code Quality Standards

- **Code Coverage**: Maintain >90% test coverage
- **Type Hints**: Use type hints for all public APIs
- **Documentation**: Document all public functions and classes
- **Performance**: Profile and optimize critical paths

## 📈 Performance & Scalability

### Benchmarks

- **Search Speed**: 50-100 businesses per minute
- **Analysis Throughput**: 10-20 websites per minute
- **Memory Usage**: 200-500MB typical, 1GB+ for large datasets
- **Database**: Handles 100K+ businesses efficiently

### Optimization Tips

- Use SSD storage for better database performance
- Increase `max_threads` on powerful machines
- Enable caching for repeated analyses
- Regular database maintenance and cleanup

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Quick Contribution Checklist

- [ ] Code follows style guidelines (black, isort, flake8)
- [ ] Tests added for new functionality
- [ ] Documentation updated
- [ ] Type hints included
- [ ] Performance impact considered

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **PySide6**: Modern Qt-based GUI framework
- **Selenium**: Web automation and testing
- **BeautifulSoup**: HTML/XML parsing
- **Lighthouse**: Web performance analysis
- **SQLite**: Embedded database engine

## 📞 Support

- **Documentation**: [Full Documentation](https://docs.example.com)
- **Issues**: [GitHub Issues](https://github.com/yourusername/uk_business_lead_generator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/uk_business_lead_generator/discussions)
- **Email**: support@example.com

---

**Made with ❤️ for the UK business community**
