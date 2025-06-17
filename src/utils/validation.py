"""Data Validation Utilities

Provides validation functions for business data including emails, phone numbers,
websites, and UK-specific location validation.
"""

import re
import requests
from typing import Optional, Dict, List, Tuple
from urllib.parse import urlparse

try:
    from validate_email import validate_email as validate_email_lib
    EMAIL_VALIDATOR_AVAILABLE = True
except ImportError:
    EMAIL_VALIDATOR_AVAILABLE = False

class DataValidator:
    """Validates various types of business data"""
    
    def __init__(self):
        # UK phone number patterns
        self.uk_phone_patterns = [
            r'^\+44\s?[1-9]\d{8,9}$',  # +44 format
            r'^0[1-9]\d{8,9}$',        # 0 prefix format
            r'^[1-9]\d{8,9}$'          # Without prefix
        ]
        
        # UK postcode pattern
        self.uk_postcode_pattern = r'^[A-Z]{1,2}[0-9R][0-9A-Z]?\s?[0-9][A-Z]{2}$'
        
        # Email pattern (basic)
        self.email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        # UK cities and towns (major ones)
        self.uk_locations = {
            'london', 'birmingham', 'manchester', 'liverpool', 'leeds', 'sheffield',
            'bristol', 'glasgow', 'edinburgh', 'newcastle', 'cardiff', 'belfast',
            'nottingham', 'leicester', 'coventry', 'bradford', 'stoke-on-trent',
            'wolverhampton', 'plymouth', 'southampton', 'reading', 'derby',
            'luton', 'northampton', 'portsmouth', 'preston', 'milton keynes',
            'aberdeen', 'swansea', 'dundee', 'york', 'norwich', 'oxford',
            'cambridge', 'ipswich', 'exeter', 'gloucester', 'bath', 'chester',
            'canterbury', 'winchester', 'salisbury', 'chichester', 'truro'
        }
    
    def validate_email(self, email: str) -> Dict[str, any]:
        """Validate email address
        
        Args:
            email: Email address to validate
            
        Returns:
            Dictionary with validation results
        """
        if not email or not isinstance(email, str):
            return {
                'valid': False,
                'email': email,
                'issues': ['Empty or invalid email']
            }
        
        email = email.strip().lower()
        issues = []
        
        # Basic format check
        if not re.match(self.email_pattern, email):
            issues.append('Invalid email format')
        
        # Check for common issues
        if '..' in email:
            issues.append('Contains consecutive dots')
        
        if email.startswith('.') or email.endswith('.'):
            issues.append('Starts or ends with dot')
        
        if '@.' in email or '.@' in email:
            issues.append('Dot adjacent to @ symbol')
        
        # Advanced validation if library available
        if EMAIL_VALIDATOR_AVAILABLE and not issues:
            try:
                is_valid = validate_email_lib(email)
                if not is_valid:
                    issues.append('Failed advanced validation')
            except Exception as e:
                issues.append(f'Validation error: {str(e)}')
        
        return {
            'valid': len(issues) == 0,
            'email': email,
            'issues': issues
        }
    
    def validate_phone(self, phone: str, country_code: str = 'UK') -> Dict[str, any]:
        """Validate phone number
        
        Args:
            phone: Phone number to validate
            country_code: Country code (currently only UK supported)
            
        Returns:
            Dictionary with validation results
        """
        if not phone or not isinstance(phone, str):
            return {
                'valid': False,
                'phone': phone,
                'formatted': None,
                'issues': ['Empty or invalid phone number']
            }
        
        # Clean phone number
        cleaned = re.sub(r'[^0-9+]', '', phone.strip())
        issues = []
        formatted_phone = None
        
        if country_code.upper() == 'UK':
            # Check against UK patterns
            valid_pattern = False
            for pattern in self.uk_phone_patterns:
                if re.match(pattern, cleaned):
                    valid_pattern = True
                    break
            
            if not valid_pattern:
                issues.append('Invalid UK phone number format')
            else:
                # Format the phone number
                if cleaned.startswith('+44'):
                    formatted_phone = cleaned
                elif cleaned.startswith('0'):
                    formatted_phone = '+44' + cleaned[1:]
                else:
                    formatted_phone = '+44' + cleaned
        else:
            issues.append(f'Country code {country_code} not supported')
        
        return {
            'valid': len(issues) == 0,
            'phone': phone,
            'formatted': formatted_phone,
            'issues': issues
        }
    
    def validate_website(self, url: str) -> Dict[str, any]:
        """Validate website URL
        
        Args:
            url: Website URL to validate
            
        Returns:
            Dictionary with validation results
        """
        if not url or not isinstance(url, str):
            return {
                'valid': False,
                'url': url,
                'formatted': None,
                'accessible': False,
                'issues': ['Empty or invalid URL']
            }
        
        url = url.strip()
        issues = []
        formatted_url = url
        accessible = False
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            formatted_url = 'https://' + url
        
        # Parse URL
        try:
            parsed = urlparse(formatted_url)
            
            if not parsed.netloc:
                issues.append('Invalid URL format')
            
            # Check for valid domain
            if not re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', parsed.netloc):
                issues.append('Invalid domain format')
            
        except Exception as e:
            issues.append(f'URL parsing error: {str(e)}')
        
        # Test accessibility (optional, can be slow)
        if len(issues) == 0:
            try:
                response = requests.head(formatted_url, timeout=5, allow_redirects=True)
                accessible = response.status_code < 400
                if not accessible:
                    issues.append(f'Website not accessible (HTTP {response.status_code})')
            except requests.RequestException:
                issues.append('Website not accessible')
        
        return {
            'valid': len(issues) == 0,
            'url': url,
            'formatted': formatted_url,
            'accessible': accessible,
            'issues': issues
        }
    
    def validate_uk_postcode(self, postcode: str) -> Dict[str, any]:
        """Validate UK postcode
        
        Args:
            postcode: UK postcode to validate
            
        Returns:
            Dictionary with validation results
        """
        if not postcode or not isinstance(postcode, str):
            return {
                'valid': False,
                'postcode': postcode,
                'formatted': None,
                'issues': ['Empty or invalid postcode']
            }
        
        # Clean and format postcode
        cleaned = postcode.strip().upper().replace(' ', '')
        issues = []
        
        # Add space in correct position
        if len(cleaned) >= 5:
            formatted = cleaned[:-3] + ' ' + cleaned[-3:]
        else:
            formatted = cleaned
            issues.append('Postcode too short')
        
        # Validate format
        if not re.match(self.uk_postcode_pattern, formatted):
            issues.append('Invalid UK postcode format')
        
        return {
            'valid': len(issues) == 0,
            'postcode': postcode,
            'formatted': formatted if len(issues) == 0 else None,
            'issues': issues
        }
    
    def validate_uk_location(self, location: str) -> Dict[str, any]:
        """Validate UK location
        
        Args:
            location: Location name to validate
            
        Returns:
            Dictionary with validation results
        """
        if not location or not isinstance(location, str):
            return {
                'valid': False,
                'location': location,
                'suggestions': [],
                'issues': ['Empty or invalid location']
            }
        
        location_clean = location.strip().lower()
        issues = []
        suggestions = []
        
        # Check if it's a known UK location
        is_known = location_clean in self.uk_locations
        
        if not is_known:
            # Find similar locations
            for uk_location in self.uk_locations:
                if location_clean in uk_location or uk_location in location_clean:
                    suggestions.append(uk_location.title())
            
            if not suggestions:
                issues.append('Location not recognized as major UK city/town')
        
        return {
            'valid': is_known or len(suggestions) > 0,
            'location': location,
            'suggestions': suggestions[:5],  # Limit to 5 suggestions
            'issues': issues
        }
    
    def validate_business_data(self, business_data: Dict) -> Dict[str, any]:
        """Validate complete business data record
        
        Args:
            business_data: Dictionary containing business information
            
        Returns:
            Dictionary with validation results for all fields
        """
        results = {
            'valid': True,
            'field_results': {},
            'overall_issues': []
        }
        
        # Validate email if present
        if 'email' in business_data and business_data['email']:
            email_result = self.validate_email(business_data['email'])
            results['field_results']['email'] = email_result
            if not email_result['valid']:
                results['valid'] = False
        
        # Validate phone if present
        if 'phone' in business_data and business_data['phone']:
            phone_result = self.validate_phone(business_data['phone'])
            results['field_results']['phone'] = phone_result
            if not phone_result['valid']:
                results['valid'] = False
        
        # Validate website if present
        if 'website' in business_data and business_data['website']:
            website_result = self.validate_website(business_data['website'])
            results['field_results']['website'] = website_result
            if not website_result['valid']:
                results['valid'] = False
        
        # Validate postcode if present
        if 'postcode' in business_data and business_data['postcode']:
            postcode_result = self.validate_uk_postcode(business_data['postcode'])
            results['field_results']['postcode'] = postcode_result
            if not postcode_result['valid']:
                results['valid'] = False
        
        # Check for required fields
        required_fields = ['name', 'address']
        for field in required_fields:
            if field not in business_data or not business_data[field]:
                results['overall_issues'].append(f'Missing required field: {field}')
                results['valid'] = False
        
        return results
    
    def clean_business_data(self, business_data: Dict) -> Dict:
        """Clean and format business data
        
        Args:
            business_data: Raw business data
            
        Returns:
            Cleaned business data
        """
        cleaned = business_data.copy()
        
        # Clean email
        if 'email' in cleaned and cleaned['email']:
            email_result = self.validate_email(cleaned['email'])
            if email_result['valid']:
                cleaned['email'] = email_result['email']
        
        # Clean phone
        if 'phone' in cleaned and cleaned['phone']:
            phone_result = self.validate_phone(cleaned['phone'])
            if phone_result['valid'] and phone_result['formatted']:
                cleaned['phone'] = phone_result['formatted']
        
        # Clean website
        if 'website' in cleaned and cleaned['website']:
            website_result = self.validate_website(cleaned['website'])
            if website_result['valid'] and website_result['formatted']:
                cleaned['website'] = website_result['formatted']
        
        # Clean postcode
        if 'postcode' in cleaned and cleaned['postcode']:
            postcode_result = self.validate_uk_postcode(cleaned['postcode'])
            if postcode_result['valid'] and postcode_result['formatted']:
                cleaned['postcode'] = postcode_result['formatted']
        
        # Clean text fields
        text_fields = ['name', 'address', 'description']
        for field in text_fields:
            if field in cleaned and cleaned[field]:
                # Remove extra whitespace and normalize
                cleaned[field] = ' '.join(cleaned[field].strip().split())
        
        return cleaned

# Global validator instance
validator = DataValidator()

# Convenience functions
def validate_email(email: str) -> bool:
    """Quick email validation"""
    return validator.validate_email(email)['valid']

def validate_phone(phone: str) -> bool:
    """Quick phone validation"""
    return validator.validate_phone(phone)['valid']

def validate_website(url: str) -> bool:
    """Quick website validation"""
    return validator.validate_website(url)['valid']

def validate_uk_location(location: str) -> bool:
    """Quick UK location validation"""
    return validator.validate_uk_location(location)['valid']