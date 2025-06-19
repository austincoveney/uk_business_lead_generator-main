"""Unit tests for helper functions"""

import pytest
import os
from unittest.mock import patch, Mock
from src.utils.helpers import (
    validate_uk_location,
    clean_url,
    format_phone_number,
    extract_email_from_text,
    calculate_contact_completeness,
    normalize_business_name,
    is_valid_email,
    get_domain_from_url,
    format_address,
    clean_text,
    validate_postcode,
    extract_social_media_links,
    calculate_priority_score,
    format_currency,
    parse_opening_hours,
    get_file_size_mb,
    create_backup_filename,
    sanitize_filename,
    get_memory_usage_mb,
    format_duration
)

class TestValidateUKLocation:
    """Test UK location validation"""
    
    def test_valid_postcodes(self):
        """Test valid UK postcodes"""
        valid_postcodes = [
            "SW1A 1AA",
            "M1 1AA",
            "B33 8TH",
            "W1A 0AX",
            "EC1A 1BB",
            "sw1a 1aa",  # lowercase
            "SW1A1AA",   # no space
        ]
        for postcode in valid_postcodes:
            assert validate_uk_location(postcode), f"Failed for {postcode}"
    
    def test_valid_cities(self):
        """Test valid UK cities"""
        valid_cities = [
            "London",
            "Manchester",
            "Birmingham",
            "Edinburgh",
            "Cardiff",
            "Belfast",
            "liverpool",  # lowercase
            "GLASGOW",    # uppercase
        ]
        for city in valid_cities:
            assert validate_uk_location(city), f"Failed for {city}"
    
    def test_valid_counties(self):
        """Test valid UK counties"""
        valid_counties = [
            "Kent",
            "Surrey",
            "Yorkshire",
            "Lancashire",
            "Gloucestershire",
        ]
        for county in valid_counties:
            assert validate_uk_location(county), f"Failed for {county}"
    
    def test_valid_compound_names(self):
        """Test valid compound place names"""
        valid_names = [
            "Stratford-upon-Avon",
            "Newcastle upon Tyne",
            "Stoke-on-Trent",
            "Southend-on-Sea",
            "Kingston upon Hull",
        ]
        for name in valid_names:
            assert validate_uk_location(name), f"Failed for {name}"
    
    def test_invalid_locations(self):
        """Test invalid locations"""
        invalid_locations = [
            "",
            "   ",
            "123",
            "New York",
            "Paris",
            "Tokyo",
            "@#$%",
            "A",  # too short
            "This is a very long invalid location name that should not be accepted",
        ]
        for location in invalid_locations:
            assert not validate_uk_location(location), f"Should fail for {location}"

class TestCleanUrl:
    """Test URL cleaning functionality"""
    
    def test_add_https_scheme(self):
        """Test adding https scheme to URLs"""
        assert clean_url("example.com") == "https://example.com"
        assert clean_url("www.example.com") == "https://www.example.com"
    
    def test_preserve_existing_scheme(self):
        """Test preserving existing URL schemes"""
        assert clean_url("https://example.com") == "https://example.com"
        assert clean_url("http://example.com") == "http://example.com"
    
    def test_remove_tracking_parameters(self):
        """Test removal of tracking parameters"""
        url_with_tracking = "https://example.com/page?utm_source=google&utm_medium=cpc&normal_param=value"
        expected = "https://example.com/page?normal_param=value"
        assert clean_url(url_with_tracking) == expected
    
    def test_empty_url(self):
        """Test handling of empty URLs"""
        assert clean_url("") == ""
        assert clean_url(None) == ""

class TestFormatPhoneNumber:
    """Test phone number formatting"""
    
    def test_uk_mobile_numbers(self):
        """Test UK mobile number formatting"""
        assert format_phone_number("07123456789") == "07123 456789"
        assert format_phone_number("+447123456789") == "+44 7123 456789"
    
    def test_uk_landline_numbers(self):
        """Test UK landline number formatting"""
        assert format_phone_number("02071234567") == "020 7123 4567"
        assert format_phone_number("+442071234567") == "+44 20 7123 4567"
    
    def test_invalid_numbers(self):
        """Test handling of invalid phone numbers"""
        assert format_phone_number("123") == "123"  # too short
        assert format_phone_number("abcdefghijk") == "abcdefghijk"  # non-numeric
        assert format_phone_number("") == ""

class TestEmailValidation:
    """Test email validation and extraction"""
    
    def test_valid_emails(self):
        """Test valid email addresses"""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "info@business-name.com",
            "contact+support@example.org",
        ]
        for email in valid_emails:
            assert is_valid_email(email), f"Failed for {email}"
    
    def test_invalid_emails(self):
        """Test invalid email addresses"""
        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "user@",
            "user@domain",
            "user name@domain.com",
            "",
        ]
        for email in invalid_emails:
            assert not is_valid_email(email), f"Should fail for {email}"
    
    def test_extract_email_from_text(self):
        """Test email extraction from text"""
        text = "Contact us at info@example.com or support@test.co.uk for help."
        emails = extract_email_from_text(text)
        assert "info@example.com" in emails
        assert "support@test.co.uk" in emails
        assert len(emails) == 2

class TestContactCompleteness:
    """Test contact completeness calculation"""
    
    def test_complete_contact_info(self):
        """Test calculation with complete contact info"""
        business = {
            "name": "Test Business",
            "phone": "020 7123 4567",
            "email": "info@test.com",
            "website": "https://test.com",
            "address": "123 Test Street, London",
            "social_media": {"linkedin": "https://linkedin.com/company/test"}
        }
        score = calculate_contact_completeness(business)
        assert score >= 90  # Should be high for complete info
    
    def test_minimal_contact_info(self):
        """Test calculation with minimal contact info"""
        business = {
            "name": "Test Business",
            "phone": "",
            "email": "",
            "website": "",
            "address": "",
            "social_media": {}
        }
        score = calculate_contact_completeness(business)
        assert score <= 20  # Should be low for minimal info

class TestUtilityFunctions:
    """Test various utility functions"""
    
    def test_normalize_business_name(self):
        """Test business name normalization"""
        assert normalize_business_name("  Test Business Ltd  ") == "Test Business Ltd"
        assert normalize_business_name("TEST BUSINESS") == "Test Business"
        assert normalize_business_name("test business") == "Test Business"
    
    def test_get_domain_from_url(self):
        """Test domain extraction from URLs"""
        assert get_domain_from_url("https://www.example.com/path") == "example.com"
        assert get_domain_from_url("http://subdomain.example.co.uk") == "subdomain.example.co.uk"
        assert get_domain_from_url("invalid-url") == ""
    
    def test_sanitize_filename(self):
        """Test filename sanitization"""
        assert sanitize_filename("file<>name.txt") == "file__name.txt"
        assert sanitize_filename("file|name?.txt") == "file_name_.txt"
        assert sanitize_filename("normal_file.txt") == "normal_file.txt"
    
    def test_format_currency(self):
        """Test currency formatting"""
        assert format_currency(1234.56) == "£1,234.56"
        assert format_currency(0) == "£0.00"
        assert format_currency(1000000) == "£1,000,000.00"
    
    def test_format_duration(self):
        """Test duration formatting"""
        assert format_duration(3661) == "1h 1m 1s"  # 1 hour, 1 minute, 1 second
        assert format_duration(61) == "1m 1s"      # 1 minute, 1 second
        assert format_duration(30) == "30s"        # 30 seconds
        assert format_duration(0) == "0s"          # 0 seconds
    
    @patch('psutil.virtual_memory')
    def test_get_memory_usage_mb(self, mock_memory):
        """Test memory usage calculation"""
        mock_memory.return_value.used = 1024 * 1024 * 1024  # 1GB in bytes
        assert get_memory_usage_mb() == 1024.0
    
    def test_create_backup_filename(self):
        """Test backup filename creation"""
        original = "data.db"
        backup = create_backup_filename(original)
        assert backup.startswith("data_backup_")
        assert backup.endswith(".db")
        assert len(backup) > len(original)

class TestDataValidation:
    """Test data validation functions"""
    
    def test_validate_postcode(self):
        """Test postcode validation"""
        assert validate_postcode("SW1A 1AA")
        assert validate_postcode("M1 1AA")
        assert not validate_postcode("INVALID")
        assert not validate_postcode("")
    
    def test_clean_text(self):
        """Test text cleaning"""
        dirty_text = "  Hello\n\tWorld!  \r\n"
        clean = clean_text(dirty_text)
        assert clean == "Hello World!"
        assert "\n" not in clean
        assert "\t" not in clean
    
    def test_extract_social_media_links(self):
        """Test social media link extraction"""
        text = "Follow us on https://facebook.com/company and https://twitter.com/company"
        links = extract_social_media_links(text)
        assert "facebook" in links
        assert "twitter" in links
        assert links["facebook"] == "https://facebook.com/company"
        assert links["twitter"] == "https://twitter.com/company"

class TestPerformanceFunctions:
    """Test performance-related functions"""
    
    def test_calculate_priority_score(self):
        """Test priority score calculation"""
        high_quality_business = {
            "contact_completeness": 95,
            "seo_score": 85,
            "performance_score": 90,
            "social_media": {"linkedin": "test", "facebook": "test"}
        }
        score = calculate_priority_score(high_quality_business)
        assert score >= 80  # Should be high priority
        
        low_quality_business = {
            "contact_completeness": 20,
            "seo_score": 10,
            "performance_score": 15,
            "social_media": {}
        }
        score = calculate_priority_score(low_quality_business)
        assert score <= 30  # Should be low priority
    
    @patch('os.path.getsize')
    def test_get_file_size_mb(self, mock_getsize):
        """Test file size calculation"""
        mock_getsize.return_value = 1024 * 1024  # 1MB in bytes
        assert get_file_size_mb("test.txt") == 1.0
        
        mock_getsize.side_effect = OSError("File not found")
        assert get_file_size_mb("nonexistent.txt") == 0.0

if __name__ == "__main__":
    pytest.main([__file__])