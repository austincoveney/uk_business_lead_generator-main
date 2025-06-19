#!/usr/bin/env python3
"""
UK Business Lead Generator - Main Application Entry Point
"""
import sys
import os
import asyncio
import argparse
from typing import Optional
import logging
from pathlib import Path

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication, Qt, QSettings, QTimer

# Use absolute imports instead of relative imports
from src.gui.main_window import MainWindow
from src.utils.helpers import setup_logging, get_resource_path
from src.utils.config import Config
from src.utils.advanced_logger import get_logger, configure_logging, LogLevel
from src.utils.error_handler import ErrorHandler
from src.utils.performance_monitor import get_performance_monitor
from src.utils.cache_manager import get_cache_manager
from src.utils.data_validator import get_data_validator
from src.core.database import LeadDatabase
from src.core.automation import AutomationManager

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="UK Business Lead Generator - Advanced business lead generation and analysis tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/main.py                    # Start the GUI application
  python src/main.py --version          # Show version information
  python src/main.py --debug            # Start with debug logging
  python src/main.py --no-gui           # Run in headless mode (future feature)

For more information, visit: https://github.com/your-repo/uk-business-lead-generator
        """
    )
    
    parser.add_argument(
        '--version', 
        action='version', 
        version='UK Business Lead Generator v2.0.0'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Set logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--no-gui',
        action='store_true',
        help='Run in headless mode without GUI (future feature)'
    )
    
    parser.add_argument(
        '--config-dir',
        type=str,
        help='Custom configuration directory path'
    )
    
    return parser.parse_args()

def main():
    """Main application entry point with comprehensive system initialization."""
    try:
        # Parse command-line arguments first
        args = parse_arguments()
        
        # Set up application metadata
        QCoreApplication.setApplicationName("UK Business Lead Generator")
        QCoreApplication.setApplicationVersion("2.0.0")
        QCoreApplication.setOrganizationName("Business Tools")
        QCoreApplication.setOrganizationDomain("businesstools.com")
        
        # Create application instance
        app = QApplication(sys.argv)
        app.setStyle('Fusion')  # Use Fusion style for better cross-platform appearance
        
        # Initialize advanced logging system with appropriate level
        log_level = LogLevel.INFO
        if args.debug:
            log_level = LogLevel.DEBUG
        elif args.log_level:
            log_level = getattr(LogLevel, args.log_level)
        
        configure_logging(
            level=log_level,
            log_dir="logs",
            enable_console=True,
            enable_file=True,
            enable_json=True
        )
        logger = get_logger("main")
        logger.info("Starting UK Business Lead Generator v2.0.0")
        
        # Handle no-gui mode (future feature)
        if args.no_gui:
            logger.info("Headless mode requested but not yet implemented")
            print("Headless mode is not yet implemented. Please run without --no-gui flag.")
            return 0
        
        # Initialize error handling
        error_handler = ErrorHandler()
        
        # Initialize performance monitoring
        performance_monitor = get_performance_monitor()
        performance_monitor.start_monitoring()
        logger.info("Performance monitoring started")
        
        # Initialize cache manager
        cache_manager = get_cache_manager()
        cache_manager.clear_expired()
        logger.info("Cache manager initialized")
        
        # Initialize data validator
        data_validator = get_data_validator()
        logger.info("Data validator initialized")
        
        # Initialize configuration
        config = Config()
        logger.info("Configuration loaded")
        
        # Initialize database
        database = LeadDatabase()
        logger.info("Database initialized")
        
        # Initialize automation manager
        automation_manager = AutomationManager(database)
        logger.info("Automation manager initialized")
        
        # Create data directories
        data_dir = os.path.join(os.path.expanduser("~"), "UKLeadGen", "data")
        export_dir = os.path.join(os.path.expanduser("~"), "UKLeadGen", "exports")
        
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(export_dir, exist_ok=True)
        
        # Create and show main window
        window = MainWindow()
        window.show()
        logger.info("Main window displayed")
        
        # Set up periodic performance monitoring
        performance_timer = QTimer()
        performance_timer.timeout.connect(lambda: performance_monitor.collect_system_metrics())
        performance_timer.start(30000)  # Every 30 seconds
        
        # Set up periodic cache cleanup
        cache_timer = QTimer()
        cache_timer.timeout.connect(lambda: cache_manager.clear_expired())
        cache_timer.start(300000)  # Every 5 minutes
        
        logger.info("Application startup completed successfully")
        
        # Start the application event loop
        result = app.exec()
        
        # Cleanup on exit
        logger.info("Application shutting down")
        performance_monitor.stop_monitoring()
        cache_manager.clear()
        
        return result
        
    except Exception as e:
        if 'error_handler' in locals():
            error_handler.handle_error(e, context={"phase": "startup"})
        else:
            print(f"Critical startup error: {e}")
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())