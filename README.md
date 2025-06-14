# UK Business Lead Generator

A professional desktop application for generating and managing business leads for web design companies in the UK.

## Features

- Search for businesses by location and category
- Analyze website performance and SEO metrics
- Generate detailed business reports
- Export data in multiple formats (CSV, Excel, PDF)
- Modern and intuitive user interface
- Automated web presence analysis

## Installation

### For Users

1. Download the latest release from the [releases page](https://github.com/yourusername/uk_business_lead_generator/releases)
2. Run the executable - no installation required
3. On first run, the application will create necessary data directories

### For Developers

1. Clone the repository:
```bash
git clone https://github.com/yourusername/uk_business_lead_generator.git
cd uk_business_lead_generator
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/MacOS
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install pre-commit hooks:
```bash
pre-commit install
```

## Development

### Project Structure

```
uk_business_lead_generator/
├── src/                    # Source code
│   ├── core/              # Core business logic
│   ├── gui/               # User interface
│   └── utils/             # Utilities and helpers
├── tests/                 # Test suite
├── docs/                  # Documentation
└── build_scripts/         # Build configuration
```

### Testing

Run the test suite:
```bash
pytest
```

With coverage report:
```bash
pytest --cov=src --cov-report=html
```

### Code Quality

The project uses several tools to maintain code quality:

- Black for code formatting
- Flake8 for style guide enforcement
- MyPy for static type checking
- isort for import sorting
- pre-commit hooks for automated checks

Run code quality checks:
```bash
black src tests
flake8 src tests
mypy src
isort src tests
```

### Building

Create executable:
```bash
powershell -File build_scripts\build_windows.ps1
```

The executable will be created in the `dist` directory.

## Configuration

Application settings are stored in:
- Windows: `%APPDATA%\UK Business Lead Generator`
- Linux: `~/.config/UK Business Lead Generator`
- MacOS: `~/Library/Application Support/UK Business Lead Generator`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and quality checks
5. Submit a pull request

Please follow our coding standards and include tests for new features.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Security

Report security vulnerabilities to [security@yourdomain.com](mailto:security@yourdomain.com)

## Support

For support and questions, please [open an issue](https://github.com/yourusername/uk_business_lead_generator/issues)
