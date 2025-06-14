"""Unit tests for database operations"""

import pytest
from datetime import datetime

def test_add_business(test_db):
    """Test adding a business to the database"""
    business_data = {
        'name': 'Test Business',
        'address': '123 Test St',
        'city': 'London',
        'postal_code': 'SW1A 1AA',
        'phone': '+44 20 1234 5678',
        'email': 'test@business.com',
        'website': 'https://testbusiness.com',
        'business_type': 'Retail',
        'notes': 'Test notes'
    }
    
    # Add business
    business_id = test_db.add_business(business_data)
    
    # Verify business was added
    assert business_id is not None
    assert business_id > 0
    
    # Retrieve and verify business data
    stored_business = test_db.get_business(business_id)
    assert stored_business is not None
    assert stored_business['name'] == business_data['name']
    assert stored_business['website'] == business_data['website']

def test_update_business(test_db):
    """Test updating business information"""
    # First add a business
    business_data = {
        'name': 'Original Name',
        'city': 'London',
        'website': 'https://original.com'
    }
    business_id = test_db.add_business(business_data)
    
    # Update business
    updated_data = {
        'name': 'Updated Name',
        'website': 'https://updated.com'
    }
    test_db.update_business(business_id, updated_data)
    
    # Verify updates
    stored_business = test_db.get_business(business_id)
    assert stored_business['name'] == updated_data['name']
    assert stored_business['website'] == updated_data['website']
    assert stored_business['city'] == business_data['city']  # Unchanged field

def test_delete_business(test_db):
    """Test deleting a business"""
    # Add business
    business_id = test_db.add_business({'name': 'To Delete'})
    
    # Verify business exists
    assert test_db.get_business(business_id) is not None
    
    # Delete business
    test_db.delete_business(business_id)
    
    # Verify business was deleted
    assert test_db.get_business(business_id) is None

def test_add_website_metrics(test_db):
    """Test adding website metrics"""
    # Add business
    business_id = test_db.add_business({'name': 'Test Metrics'})
    
    # Add metrics
    metrics = {
        'performance_score': 85,
        'seo_score': 90,
        'accessibility_score': 95,
        'best_practices_score': 88,
        'issues': '["Minor SEO issues"]'
    }
    
    test_db.add_website_metrics(business_id, metrics)
    
    # Verify metrics
    stored_metrics = test_db.get_website_metrics(business_id)
    assert stored_metrics is not None
    assert stored_metrics['performance_score'] == metrics['performance_score']
    assert stored_metrics['seo_score'] == metrics['seo_score']

def test_search_businesses(test_db):
    """Test searching businesses"""
    # Add test businesses
    test_db.add_business({
        'name': 'London Shop',
        'city': 'London',
        'business_type': 'Retail'
    })
    test_db.add_business({
        'name': 'Manchester Store',
        'city': 'Manchester',
        'business_type': 'Retail'
    })
    
    # Search by city
    london_results = test_db.search_businesses(city='London')
    assert len(london_results) == 1
    assert london_results[0]['city'] == 'London'
    
    # Search by type
    retail_results = test_db.search_businesses(business_type='Retail')
    assert len(retail_results) == 2