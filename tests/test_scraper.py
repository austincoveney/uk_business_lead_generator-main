"""Unit tests for web scraping functionality"""

import pytest
from unittest.mock import Mock, patch
from bs4 import BeautifulSoup

def test_scraper_initialization(mock_scraper):
    """Test scraper initialization"""
    assert mock_scraper.session is not None
    assert 'User-Agent' in mock_scraper.session.headers
    assert not mock_scraper.use_selenium

@patch('requests.Session.get')
def test_find_businesses(mock_get, mock_scraper):
    """Test business search functionality"""
    # Mock response data
    mock_html = '''
    <div class="business-listing">
        <h2>Test Business 1</h2>
        <p class="address">123 Test St, London</p>
        <p class="phone">020 1234 5678</p>
        <a href="https://testbusiness1.com">Website</a>
    </div>
    <div class="business-listing">
        <h2>Test Business 2</h2>
        <p class="address">456 Sample Rd, London</p>
        <p class="phone">020 8765 4321</p>
        <a href="https://testbusiness2.com">Website</a>
    </div>
    '''
    
    mock_response = Mock()
    mock_response.text = mock_html
    mock_response.status_code = 200
    mock_get.return_value = mock_response
    
    # Test search
    businesses = mock_scraper.find_businesses('London', limit=2)
    
    assert len(businesses) == 2
    assert businesses[0]['name'] == 'Test Business 1'
    assert businesses[0]['website'] == 'https://testbusiness1.com'
    assert businesses[1]['name'] == 'Test Business 2'

def test_rate_limiting(mock_scraper):
    """Test rate limiting functionality"""
    with patch('time.sleep') as mock_sleep:
        mock_scraper._rate_limit()
        mock_sleep.assert_called_once()

@patch('requests.Session.get')
def test_error_handling(mock_get, mock_scraper):
    """Test error handling during scraping"""
    # Test connection error
    mock_get.side_effect = Exception('Connection error')
    
    with pytest.raises(Exception):
        mock_scraper.find_businesses('London')
    
    # Test invalid response
    mock_response = Mock()
    mock_response.status_code = 404
    mock_get.side_effect = None
    mock_get.return_value = mock_response
    
    with pytest.raises(Exception):
        mock_scraper.find_businesses('London')

@patch('selenium.webdriver.Chrome')
def test_selenium_setup(mock_chrome):
    """Test Selenium setup"""
    from src.core.scraper import BusinessScraper
    
    # Initialize scraper with Selenium
    scraper = BusinessScraper(use_selenium=True)
    
    assert scraper.use_selenium
    mock_chrome.assert_called_once()

def test_data_extraction(mock_scraper):
    """Test business data extraction from HTML"""
    html = '''
    <div class="business-listing">
        <h2>Sample Business</h2>
        <p class="address">789 Example Ave, Manchester, M1 1AA</p>
        <p class="phone">0161 234 5678</p>
        <p class="email">contact@samplebusiness.com</p>
        <a href="https://samplebusiness.com">Website</a>
        <p class="description">A sample business description</p>
    </div>
    '''
    
    soup = BeautifulSoup(html, 'lxml')
    business_data = mock_scraper._extract_business_data(soup.find('div', class_='business-listing'))
    
    assert business_data['name'] == 'Sample Business'
    assert 'Manchester' in business_data['address']
    assert business_data['phone'] == '0161 234 5678'
    assert business_data['email'] == 'contact@samplebusiness.com'
    assert business_data['website'] == 'https://samplebusiness.com'