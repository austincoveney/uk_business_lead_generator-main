"""Test configuration and fixtures for UK Business Lead Generator"""

import os
import sys
import pytest
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import project modules
from src.core.database import LeadDatabase
from src.core.scraper import BusinessScraper
from src.core.analyzer import WebsiteAnalyzer
from src.utils.config import Config

@pytest.fixture
def test_config():
    """Fixture for test configuration"""
    config = Config()
    # Override settings for testing
    config.set('general/data_folder', str(project_root / 'tests' / 'data'))
    config.set('export/default_path', str(project_root / 'tests' / 'exports'))
    config.set('search/limit', 5)
    return config

@pytest.fixture
def test_db(test_config):
    """Fixture for test database"""
    db_path = os.path.join(test_config.get_data_folder(), 'test.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Create test database
    db = LeadDatabase(db_path)
    
    yield db
    
    # Cleanup
    try:
        os.remove(db_path)
    except OSError:
        pass

@pytest.fixture
def mock_scraper():
    """Fixture for mocked scraper"""
    scraper = BusinessScraper(use_selenium=False)
    return scraper

@pytest.fixture
def mock_analyzer():
    """Fixture for mocked analyzer"""
    analyzer = WebsiteAnalyzer(use_selenium=False)
    return analyzer