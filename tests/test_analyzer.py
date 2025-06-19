"""Unit tests for website analyzer functionality"""

import pytest
from unittest.mock import Mock, patch
import json

def test_analyzer_initialization(mock_analyzer):
    """Test analyzer initialization"""
    assert not mock_analyzer.lighthouse_available

@patch('subprocess.run')
def test_lighthouse_check(mock_run):
    """Test Lighthouse availability check"""
    from src.core.analyzer import WebsiteAnalyzer
    
    # Mock successful Lighthouse check
    mock_run.return_value = Mock(returncode=0)
    analyzer = WebsiteAnalyzer(use_selenium=True)
    assert analyzer.lighthouse_available
    
    # Mock failed Lighthouse check
    mock_run.return_value = Mock(returncode=1)
    analyzer = WebsiteAnalyzer(use_selenium=True)
    assert not analyzer.lighthouse_available

def test_basic_analysis(mock_analyzer):
    """Test basic website analysis without Lighthouse"""
    test_url = 'https://example.com'
    results = mock_analyzer.analyze_website(test_url)
    
    assert isinstance(results, dict)
    assert 'performance_score' in results
    assert 'seo_score' in results
    assert 'accessibility_score' in results
    assert 'best_practices_score' in results
    assert 'issues' in results

@patch('requests.get')
def test_ssl_check(mock_get, mock_analyzer):
    """Test SSL certificate verification"""
    # Mock HTTPS response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_get.return_value = mock_response
    
    results = mock_analyzer.analyze_website('https://example.com')
    assert results['has_ssl']
    
    # Mock HTTP response
    mock_get.side_effect = Exception('SSL Error')
    results = mock_analyzer.analyze_website('http://example.com')
    assert not results['has_ssl']

@patch('requests.get')
def test_mobile_viewport_check(mock_get, mock_analyzer):
    """Test mobile viewport detection"""
    # Mock response with viewport
    mock_response = Mock()
    mock_response.text = '<html><head><meta name="viewport" content="width=device-width"></head></html>'
    mock_get.return_value = mock_response
    
    results = mock_analyzer.analyze_website('https://example.com')
    assert results['has_mobile_viewport']
    
    # Mock response without viewport
    mock_response.text = '<html><head></head></html>'
    results = mock_analyzer.analyze_website('https://example.com')
    assert not results['has_mobile_viewport']

@patch('subprocess.run')
def test_lighthouse_analysis(mock_run):
    """Test Lighthouse integration"""
    # Mock Lighthouse output
    lighthouse_output = {
        'categories': {
            'performance': {'score': 0.95},
            'accessibility': {'score': 0.88},
            'best-practices': {'score': 0.92},
            'seo': {'score': 0.89}
        }
    }
    
    mock_process = Mock()
    mock_process.stdout = json.dumps(lighthouse_output)
    mock_process.returncode = 0
    mock_run.return_value = mock_process
    
    analyzer = WebsiteAnalyzer(use_selenium=True)
    results = analyzer.analyze_website('https://example.com')
    
    assert results['performance_score'] == 95
    assert results['accessibility_score'] == 88
    assert results['best_practices_score'] == 92
    assert results['seo_score'] == 89

def test_error_handling(mock_analyzer):
    """Test error handling during analysis"""
    # Test invalid URL
    with pytest.raises(ValueError):
        mock_analyzer.analyze_website('')
    
    with pytest.raises(ValueError):
        mock_analyzer.analyze_website('invalid-url')
    
    # Test connection timeout
    with patch('requests.get', side_effect=Exception('Timeout')):
        results = mock_analyzer.analyze_website('https://example.com')
        assert 'Connection timeout' in results['issues']

def test_performance_metrics(mock_analyzer):
    """Test performance metrics calculation"""
    with patch('requests.get') as mock_get:
        # Mock response time
        mock_get.return_value = Mock(
            elapsed=Mock(total_seconds=lambda: 1.5),
            headers={'content-length': '15000'}
        )
        
        results = mock_analyzer.analyze_website('https://example.com')
        
        assert 'load_time' in results
        assert results['load_time'] > 0
        assert 'page_size' in results
        assert results['page_size'] > 0