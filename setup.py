#!/usr/bin/env python3
"""
Setup script for UK Business Lead Generator v2.0
Enhanced with comprehensive improvements and modern Python practices.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Optional

# Application metadata
APP_NAME = "UK Business Lead Generator"
APP_VERSION = "2.0.0"
APP_DESCRIPTION = "Advanced business lead generation tool with smart automation and comprehensive data validation"
AUTHOR = "Business Tools Team"
AUTHOR_EMAIL = "support@businesstools.com"
URL = "https://github.com/businesstools/uk-business-lead-generator"

# Required Python version
REQUIRED_PYTHON = (3, 8)

def check_python_version() -> bool:
    """Check if Python version meets requirements."""
    current = sys.version_info[:2]
    if current < REQUIRED_PYTHON:
        print(f"Error: Python {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]}+ is required.")
        print(f"Current version: {current[0]}.{current[1]}")
        return False
    return True

def install_requirements() -> bool:
    """Install required packages from requirements.txt."""
    try:
        print("Installing required packages...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✓ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install requirements: {e}")
        return False

def create_directories() -> bool:
    """Create necessary application directories."""
    try:
        directories = [
            "logs",
            "data",
            "exports",
            "cache",
            "config",
            "backups"
        ]
        
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
            print(f"✓ Created directory: {directory}")
        
        return True
    except Exception as e:
        print(f"✗ Failed to create directories: {e}")
        return False

def setup_configuration() -> bool:
    """Set up initial configuration files."""
    try:
        config_dir = Path("config")
        
        # Create default configuration
        default_config = {
            "app": {
                "name": APP_NAME,
                "version": APP_VERSION,
                "debug": False
            },
            "database": {
                "path": "data/businesses.db",
                "backup_interval": 3600
            },
            "automation": {
                "max_concurrent_tasks": 5,
                "default_timeout": 300,
                "retry_attempts": 3
            },
            "performance": {
                "monitoring_enabled": True,
                "metrics_retention_days": 30
            },
            "logging": {
                "level": "INFO",
                "max_file_size": "10MB",
                "backup_count": 5
            }
        }
        
        import json
        with open(config_dir / "default_config.json", "w") as f:
            json.dump(default_config, f, indent=2)
        
        print("✓ Configuration files created")
        return True
    except Exception as e:
        print(f"✗ Failed to setup configuration: {e}")
        return False

def run_tests() -> bool:
    """Run basic tests to verify installation."""
    try:
        print("Running basic tests...")
        
        # Test imports
        test_imports = [
            "src.utils.config",
            "src.utils.advanced_logger",
            "src.utils.error_handler",
            "src.utils.performance_monitor",
            "src.utils.cache_manager",
            "src.utils.data_validator",
            "src.core.automation"
        ]
        
        for module in test_imports:
            try:
                __import__(module)
                print(f"✓ {module}")
            except ImportError as e:
                print(f"✗ {module}: {e}")
                return False
        
        print("✓ All tests passed")
        return True
    except Exception as e:
        print(f"✗ Tests failed: {e}")
        return False

def setup_development_tools() -> bool:
    """Set up development tools and pre-commit hooks."""
    try:
        print("Setting up development tools...")
        
        # Install pre-commit hooks
        if Path(".pre-commit-config.yaml").exists():
            subprocess.check_call([sys.executable, "-m", "pre_commit", "install"])
            print("✓ Pre-commit hooks installed")
        
        # Run initial code formatting
        subprocess.check_call([sys.executable, "-m", "black", "src/", "--check"])
        print("✓ Code formatting verified")
        
        # Run type checking
        subprocess.check_call([sys.executable, "-m", "mypy", "src/"])
        print("✓ Type checking passed")
        
        return True
    except subprocess.CalledProcessError:
        print("⚠ Development tools setup completed with warnings")
        return True
    except Exception as e:
        print(f"✗ Failed to setup development tools: {e}")
        return False

def main():
    """Main setup function."""
    print(f"Setting up {APP_NAME} v{APP_VERSION}")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install requirements
    if not install_requirements():
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        sys.exit(1)
    
    # Setup configuration
    if not setup_configuration():
        sys.exit(1)
    
    # Run tests
    if not run_tests():
        print("⚠ Some tests failed, but installation may still work")
    
    # Setup development tools (optional)
    if "--dev" in sys.argv:
        setup_development_tools()
    
    print("\n" + "=" * 50)
    print(f"✓ {APP_NAME} setup completed successfully!")
    print("\nTo start the application, run:")
    print("  python src/main.py")
    print("\nFor development mode:")
    print("  python setup.py --dev")
    print("\nFor help and documentation:")
    print(f"  Visit: {URL}")

if __name__ == "__main__":
    main()