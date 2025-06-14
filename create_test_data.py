#!/usr/bin/env python3
"""
Create test data for the UK Business Lead Generator
"""

import os
import sys
sys.path.append('.')

from src.core.database import LeadDatabase

def create_test_data():
    """Create test business data"""
    # Create database directory if it doesn't exist
    db_dir = os.path.join(os.path.expanduser("~"), "UKLeadGen", "data")
    os.makedirs(db_dir, exist_ok=True)
    
    # Create test database
    db_file = os.path.join(db_dir, "leads_london.db")
    db = LeadDatabase(db_file)
    
    # Sample business data
    test_businesses = [
        {
            "name": "Tech Solutions Ltd",
            "business_type": "Technology",
            "address": "123 Tech Street, London, SW1A 1AA",
            "phone": "020 7123 4567",
            "email": "info@techsolutions.co.uk",
            "website": "https://www.techsolutions.co.uk",
            "contact_completeness": 85,
            "social_media": {"linkedin": "https://linkedin.com/company/techsolutions", "twitter": "https://twitter.com/techsolutions"},
            "opening_hours": "Mon-Fri 9:00-17:00",
            "company_number": "12345678",
            "vat_number": "GB123456789",
            "seo_score": 78,
            "performance_score": 85,
            "accessibility_score": 72,
            "best_practices_score": 90,
            "priority": 1,
            "issues": ["Missing meta description", "Slow loading images"],
            "notes": "High priority lead - excellent website performance"
        },
        {
            "name": "Green Garden Services",
            "business_type": "Landscaping",
            "address": "456 Garden Lane, London, E1 6AN",
            "phone": "020 7987 6543",
            "email": "contact@greengardens.co.uk",
            "website": "https://www.greengardens.co.uk",
            "contact_completeness": 65,
            "social_media": {"facebook": "https://facebook.com/greengardens"},
            "opening_hours": "Mon-Sat 8:00-18:00",
            "company_number": "87654321",
            "seo_score": 45,
            "performance_score": 60,
            "accessibility_score": 55,
            "best_practices_score": 70,
            "priority": 2,
            "issues": ["Poor mobile optimization", "Missing alt tags", "No SSL certificate"],
            "notes": "Medium priority - needs website improvements"
        },
        {
            "name": "City Cafe",
            "business_type": "Restaurant",
            "address": "789 Food Street, London, W1D 3QU",
            "phone": "020 7555 0123",
            "email": "",
            "website": "https://www.citycafe.co.uk",
            "contact_completeness": 40,
            "social_media": {},
            "opening_hours": "Daily 7:00-22:00",
            "seo_score": 30,
            "performance_score": 45,
            "accessibility_score": 35,
            "best_practices_score": 50,
            "priority": 3,
            "issues": ["No contact email", "Poor SEO", "Slow website", "No social media presence"],
            "notes": "Low priority - basic website needs major improvements"
        },
        {
            "name": "Professional Consulting Group",
            "business_type": "Consulting",
            "address": "321 Business Plaza, London, EC2A 4DP",
            "phone": "020 7444 5555",
            "email": "hello@procons.co.uk",
            "website": "https://www.procons.co.uk",
            "contact_completeness": 95,
            "social_media": {
                "linkedin": "https://linkedin.com/company/procons",
                "twitter": "https://twitter.com/procons",
                "facebook": "https://facebook.com/procons"
            },
            "opening_hours": "Mon-Fri 8:30-17:30",
            "company_number": "11223344",
            "vat_number": "GB987654321",
            "seo_score": 92,
            "performance_score": 88,
            "accessibility_score": 85,
            "best_practices_score": 95,
            "priority": 1,
            "issues": [],
            "notes": "Excellent lead - perfect website and strong online presence"
        },
        {
            "name": "Local Plumbing Services",
            "business_type": "Plumbing",
            "address": "567 Pipe Road, London, SE1 9RT",
            "phone": "020 7333 2222",
            "email": "info@localplumbing.co.uk",
            "website": "",
            "contact_completeness": 50,
            "social_media": {},
            "opening_hours": "24/7 Emergency Service",
            "seo_score": 0,
            "performance_score": 0,
            "accessibility_score": 0,
            "best_practices_score": 0,
            "priority": 2,
            "issues": ["No website", "No online presence"],
            "notes": "No website - potential for digital transformation"
        }
    ]
    
    # Add businesses to database
    for business in test_businesses:
        business_id = db.add_business(business)
        print(f"Added business: {business['name']} (ID: {business_id})")
    
    # Set last location in settings
    from PySide6.QtCore import QSettings
    settings = QSettings("UK Business Lead Generator", "LeadGen")
    settings.setValue("search/last_location", "london")
    
    print(f"\nCreated test database with {len(test_businesses)} businesses")
    print(f"Database location: {db_file}")
    print("Set last search location to 'london'")
    
    db.close()

if __name__ == "__main__":
    create_test_data()