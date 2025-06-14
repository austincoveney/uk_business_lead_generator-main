#!/usr/bin/env python3
"""
Test script to check database content and score data
"""

import os
import sys
sys.path.append('.')

from src.core.database import LeadDatabase

def test_database_content():
    """Test what's in the database"""
    # Find database files
    db_dir = os.path.join(os.path.expanduser("~"), "UKLeadGen", "data")
    
    if not os.path.exists(db_dir):
        print("No database directory found")
        return
    
    db_files = [f for f in os.listdir(db_dir) if f.endswith('.db')]
    
    if not db_files:
        print("No database files found")
        return
    
    print(f"Found {len(db_files)} database files:")
    for db_file in db_files:
        print(f"  - {db_file}")
    
    # Test the first database
    db_path = os.path.join(db_dir, db_files[0])
    print(f"\nTesting database: {db_path}")
    
    try:
        db = LeadDatabase(db_path)
        businesses = db.get_all_businesses()
        
        print(f"Found {len(businesses)} businesses")
        
        for i, business in enumerate(businesses[:3]):
            print(f"\nBusiness {i+1}: {business.get('name', 'Unknown')}")
            print(f"  Website: {business.get('website', 'None')}")
            print(f"  SEO Score: {business.get('seo_score', 'None')}")
            print(f"  Performance Score: {business.get('performance_score', 'None')}")
            print(f"  Accessibility Score: {business.get('accessibility_score', 'None')}")
            print(f"  Best Practices Score: {business.get('best_practices_score', 'None')}")
            print(f"  Priority: {business.get('priority', 'None')}")
            print(f"  Issues: {business.get('issues', [])}")
            
        db.close()
        
    except Exception as e:
        print(f"Error testing database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_database_content()