# Helper functions
"""
Helper functions for the UK Business Lead Generator
"""
import re
import time
import datetime
import logging
import os
import sys
import json
import requests
from urllib.parse import urlparse


def validate_uk_location(location):
    """
    Validate if the provided string is a valid UK location

    Args:
        location: Location string to validate

    Returns:
        Boolean indicating if location appears valid
    """
    # Empty check
    if not location or not location.strip():
        return False

    # Clean the input
    location = location.strip()

    # If it's a UK postcode format
    # Improved UK postcode regex that handles various formats
    uk_postcode_pattern = r"^(([A-Z]{1,2}[0-9][A-Z0-9]?)\s*([0-9][A-Z]{2}))$|^(([A-Z]{1,2}[0-9][0-9])\s*([0-9][A-Z]{2}))$"
    if re.match(uk_postcode_pattern, location.upper()):
        return True

    # If it's a major UK city or town (expanded list)
    major_uk_locations = [
        # Major cities
        "london",
        "manchester",
        "birmingham",
        "liverpool",
        "leeds",
        "glasgow",
        "edinburgh",
        "cardiff",
        "belfast",
        "bristol",
        "newcastle",
        "sheffield",
        "nottingham",
        "leicester",
        "coventry",
        "bradford",
        "brighton",
        "southampton",
        "plymouth",
        "reading",
        "derby",
        "wolverhampton",
        "hull",
        "portsmouth",
        "oxford",
        "cambridge",
        "york",
        "swansea",
        "dundee",
        "aberdeen",
        # Counties and regions
        "kent",
        "surrey",
        "essex",
        "suffolk",
        "norfolk",
        "devon",
        "cornwall",
        "dorset",
        "hampshire",
        "berkshire",
        "wiltshire",
        "somerset",
        "gloucestershire",
        "oxfordshire",
        "buckinghamshire",
        "hertfordshire",
        "bedfordshire",
        "cambridgeshire",
        "northamptonshire",
        "lincolnshire",
        "warwickshire",
        "leicestershire",
        "nottinghamshire",
        "yorkshire",
        "lancashire",
        "cumbria",
        "northumberland",
    ]

    # Common town suffixes
    uk_town_suffixes = [
        "ham",
        "ford",
        "bridge",
        "bury",
        "ton",
        "field",
        "dale",
        "mouth",
        "port",
        "ville",
        "borough",
        "burgh",
        "chester",
        "cester",
        "street",
        "wick",
        "well",
        "pool",
        "church",
        "abbey",
        "hill",
        "wood",
        "grove",
    ]

    location_lower = location.lower()

    # Check if it's a major city or town
    if location_lower in major_uk_locations:
        return True

    # Check for common UK place name patterns
    words = location_lower.split()

    # Check for multi-word names with common UK patterns
    for word in words:
        for suffix in uk_town_suffixes:
            if word.endswith(suffix):
                return True

    # Check for combinations with "on", "upon", etc.
    if len(words) > 1:
        for connective in [
            "on",
            "upon",
            "under",
            "over",
            "by",
            "le",
            "la",
            "in",
            "near",
        ]:
            if connective in words:
                return True

    # If it's at least a reasonable length and contains only valid characters for a UK place name
    if len(location) >= 3 and re.match(r"^[a-zA-Z\s\-\']+$", location):
        # Additional check for reasonable word length and structure
        words = location.split()
        if all(len(word) >= 2 for word in words) and len(words) <= 4:
            return True

    return False


def clean_url(url):
    """
    Clean and normalize a URL

    Args:
        url: URL string to clean

    Returns:
        Cleaned URL string
    """
    if not url:
        return ""

    # Ensure URL has a scheme
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    # Remove trailing slashes, common tracking parameters, etc.
    try:
        parsed = urlparse(url)

        # Rebuild URL with normalized components
        clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

        # Remove tracking parameters (utm_*, ref, fbclid, etc.)
        if parsed.query:
            query_params = []
            for param in parsed.query.split("&"):
                if not param.startswith(("utm_", "ref=", "fbclid=", "gclid=")):
                    query_params.append(param)

            if query_params:
                clean_url += "?" + "&".join(query_params)

        # Remove trailing slash
        if clean_url.endswith("/"):
            clean_url = clean_url[:-1]

        return clean_url

    except Exception as e:
        logging.warning(f"Error cleaning URL {url}: {str(e)}")
        return url


def extract_phone_number(text):
    """
    Extract a phone number from text

    Args:
        text: Text possibly containing a phone number

    Returns:
        Extracted phone number or None
    """
    if not text:
        return None

    # UK phone number patterns
    patterns = [
        r"(?:(?:\+44\s?[0-9]{4}|\(?0[0-9]{4}\)?)\s?[0-9]{3}\s?[0-9]{3})",  # +44 7700 900000
        r"(?:(?:\+44\s?[0-9]{3}|\(?0[0-9]{3}\)?)\s?[0-9]{3}\s?[0-9]{4})",  # +44 121 234 5678
        r"(?:(?:\+44\s?[0-9]{2}|\(?0[0-9]{2}\)?)\s?[0-9]{4}\s?[0-9]{4})",  # +44 20 1234 5678
        r"(?:\+44\s?7[0-9]{3}|(?:^|\s)07[0-9]{3})\s?[0-9]{6}",  # +44 7123 456789
        r"(?:\+44\s?7[0-9]{9})",  # +44 7123456789
        r"\b[0-9]{5}\s?[0-9]{5,6}\b",  # 01234 567890
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            # Format the phone number consistently
            phone = match.group(0)

            # Remove non-digit characters for standardization
            digits = "".join(c for c in phone if c.isdigit())

            # Handle +44 vs 0 prefix
            if phone.startswith("+44"):
                # Convert +44 to 0
                digits = "0" + digits[3:]

            # Format based on number type
            if len(digits) == 11 and digits.startswith("07"):  # Mobile
                return f"{digits[:5]} {digits[5:8]} {digits[8:]}"
            elif len(digits) == 11:  # Landline
                return f"{digits[:5]} {digits[5:]}"
            else:
                return phone  # Return as is if we can't standardize

    return None


def extract_email(text):
    """
    Extract an email from text

    Args:
        text: Text possibly containing an email

    Returns:
        Extracted email or None
    """
    if not text:
        return None

    # Improved email regex that handles more valid formats
    pattern = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
    match = re.search(pattern, text)

    if match:
        email = match.group(0)

        # Validate the email has a reasonable TLD
        tld = email.split(".")[-1].lower()
        common_tlds = [
            "com",
            "co.uk",
            "org",
            "net",
            "gov",
            "edu",
            "io",
            "uk",
            "ac.uk",
            "org.uk",
            "me",
            "info",
        ]

        if tld in common_tlds or len(tld) <= 4:
            return email.lower()  # Return lowercase for consistency

    return None


def extract_postcode(text):
    """
    Extract a UK postcode from text

    Args:
        text: Text possibly containing a postcode

    Returns:
        Extracted postcode or None
    """
    if not text:
        return None

    # UK postcode pattern with improved regex
    uk_postcode = r"[A-Z]{1,2}[0-9][A-Z0-9]?\s*[0-9][A-Z]{2}"
    match = re.search(uk_postcode, text.upper())

    if match:
        postcode = match.group(0)

        # Format postcode with proper spacing
        # Find the last number in the outward code
        parts = re.match(r"([A-Z]{1,2}[0-9][A-Z0-9]?)\s*([0-9][A-Z]{2})", postcode)

        if parts:
            outward = parts.group(1)
            inward = parts.group(2)
            postcode = f"{outward} {inward}"

        return postcode

    return None


def format_business_type(business_type):
    """
    Format business type consistently

    Args:
        business_type: Business type string

    Returns:
        Formatted business type string
    """
    if not business_type:
        return "Business"

    # Remove common words like "in", "and", etc.
    common_words = ["in", "and", "the", "a", "an", "of", "for", "to", "with", "by"]

    words = business_type.split()
    filtered_words = [w for w in words if w.lower() not in common_words]

    if not filtered_words:
        return "Business"

    # Title case each word
    formatted = " ".join(word.capitalize() for word in filtered_words)

    # Map similar categories to standardized terms
    category_mapping = {
        "Restaurant": ["Cafe", "Eatery", "Dining", "Food"],
        "Retail": ["Shop", "Store", "Boutique"],
        "Technology": ["IT", "Computer", "Software", "Tech"],
        "Real Estate": ["Property", "Housing", "Estate Agent"],
        "Legal": ["Law", "Solicitor", "Attorney"],
        "Financial": ["Finance", "Accounting", "Tax"],
        "Healthcare": ["Medical", "Health", "Doctor", "Clinic"],
        "Education": ["School", "Training", "College", "University", "Teaching"],
        "Hospitality": ["Hotel", "Accommodation", "Lodging"],
        "Construction": ["Builder", "Building", "Contractor"],
    }

    # Check if the formatted type contains any keywords from the mapping
    for standard_category, keywords in category_mapping.items():
        for keyword in keywords:
            if keyword.lower() in formatted.lower():
                return standard_category

    return formatted


def rate_limit_sleep(min_seconds=0.5, max_seconds=2.0):
    """
    Sleep for a random duration to avoid rate limiting

    Args:
        min_seconds: Minimum sleep time
        max_seconds: Maximum sleep time
    """
    import random

    sleep_time = random.uniform(min_seconds, max_seconds)
    time.sleep(sleep_time)


def get_resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller

    Args:
        relative_path: Path relative to the script

    Returns:
        Absolute path to the resource
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def setup_logging(log_dir=None):
    """
    Set up logging configuration

    Args:
        log_dir: Directory to store log files
    """
    if not log_dir:
        log_dir = os.path.join(os.path.expanduser("~"), "UKLeadGen", "logs")

    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"leadgen_{timestamp}.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )


def format_phone_number(phone):
    """
    Format a phone number consistently
    
    Args:
        phone: Phone number string
        
    Returns:
        Formatted phone number or original if invalid
    """
    if not phone:
        return phone
    
    # Remove all non-digit characters
    digits = ''.join(c for c in phone if c.isdigit())
    
    # Handle UK mobile numbers
    if len(digits) == 11 and digits.startswith('07'):
        return f"{digits[:5]} {digits[5:8]} {digits[8:]}"
    elif len(digits) == 11:
        return f"{digits[:5]} {digits[5:]}"
    
    return phone


def extract_email_from_text(text):
    """
    Extract email from text (alias for extract_email)
    
    Args:
        text: Text containing email
        
    Returns:
        Extracted email or None
    """
    return extract_email(text)


def calculate_contact_completeness(business_data):
    """
    Calculate how complete the contact information is
    
    Args:
        business_data: Dictionary containing business information
        
    Returns:
        Float between 0 and 1 representing completeness
    """
    if not business_data:
        return 0.0
    
    fields = ['email', 'phone', 'website', 'address']
    present_fields = sum(1 for field in fields if business_data.get(field))
    
    return present_fields / len(fields)


def normalize_business_name(name):
    """
    Normalize business name for consistency
    
    Args:
        name: Business name string
        
    Returns:
        Normalized business name
    """
    if not name:
        return name
    
    # Remove extra whitespace and title case
    normalized = ' '.join(name.split()).title()
    
    # Remove common suffixes for comparison
    suffixes = ['Ltd', 'Limited', 'Plc', 'Inc', 'Corp', 'Co']
    for suffix in suffixes:
        if normalized.endswith(f' {suffix}'):
            normalized = normalized[:-len(suffix)-1]
    
    return normalized


def is_valid_email(email):
    """
    Validate email format
    
    Args:
        email: Email string to validate
        
    Returns:
        Boolean indicating if email is valid
    """
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def get_domain_from_url(url):
    """
    Extract domain from URL
    
    Args:
        url: URL string
        
    Returns:
        Domain string or None
    """
    if not url:
        return None
    
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except Exception:
        return None


def format_address(address):
    """
    Format address consistently
    
    Args:
        address: Address string
        
    Returns:
        Formatted address
    """
    if not address:
        return address
    
    # Clean up whitespace and capitalize properly
    return ' '.join(word.capitalize() for word in address.split())


def clean_text(text):
    """
    Clean text by removing extra whitespace and special characters
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return text
    
    # Remove extra whitespace
    cleaned = ' '.join(text.split())
    
    # Remove common unwanted characters
    cleaned = re.sub(r'[\r\n\t]', ' ', cleaned)
    
    return cleaned.strip()


def validate_postcode(postcode):
    """
    Validate UK postcode format
    
    Args:
        postcode: Postcode string
        
    Returns:
        Boolean indicating if postcode is valid
    """
    if not postcode:
        return False
    
    # UK postcode pattern
    pattern = r'^[A-Z]{1,2}[0-9][A-Z0-9]?\s?[0-9][A-Z]{2}$'
    return bool(re.match(pattern, postcode.upper().strip()))


def extract_social_media_links(text):
    """
    Extract social media links from text
    
    Args:
        text: Text containing potential social media links
        
    Returns:
        List of social media links
    """
    if not text:
        return []
    
    social_patterns = [
        r'https?://(?:www\.)?facebook\.com/[\w\.-]+',
        r'https?://(?:www\.)?twitter\.com/[\w\.-]+',
        r'https?://(?:www\.)?linkedin\.com/[\w\.-/]+',
        r'https?://(?:www\.)?instagram\.com/[\w\.-]+'
    ]
    
    links = []
    for pattern in social_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        links.extend(matches)
    
    return links


def calculate_priority_score(business_data):
    """
    Calculate priority score for business lead
    
    Args:
        business_data: Dictionary containing business information
        
    Returns:
        Priority score (higher is better)
    """
    if not business_data:
        return 0
    
    score = 0
    
    # Contact completeness (40% of score)
    completeness = calculate_contact_completeness(business_data)
    score += completeness * 40
    
    # Website quality (30% of score)
    if business_data.get('website'):
        score += 30
    
    # Performance scores (30% of score)
    performance_score = business_data.get('performance_score', 0)
    score += (performance_score / 100) * 30
    
    return min(100, score)


def format_currency(amount, currency='GBP'):
    """
    Format currency amount
    
    Args:
        amount: Numeric amount
        currency: Currency code
        
    Returns:
        Formatted currency string
    """
    if amount is None:
        return ''
    
    try:
        amount = float(amount)
        if currency == 'GBP':
            return f'£{amount:,.2f}'
        else:
            return f'{amount:,.2f} {currency}'
    except (ValueError, TypeError):
         return str(amount)


def parse_opening_hours(hours_text):
    """
    Parse opening hours text into structured format
    
    Args:
        hours_text: Text containing opening hours
        
    Returns:
        Dictionary with parsed opening hours
    """
    if not hours_text:
        return {}
    
    # Simple parsing - can be enhanced
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    parsed = {}
    
    text_lower = hours_text.lower()
    
    # Check for common patterns
    if 'closed' in text_lower:
        return {'status': 'closed'}
    elif '24 hours' in text_lower or '24/7' in text_lower:
        return {'status': '24_hours'}
    
    return {'raw': hours_text, 'status': 'unknown'}


def get_file_size_mb(file_path):
    """
    Get file size in megabytes
    
    Args:
        file_path: Path to file
        
    Returns:
        File size in MB or 0 if file doesn't exist
    """
    try:
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)
    except (OSError, FileNotFoundError):
        return 0


def create_backup_filename(original_filename):
    """
    Create backup filename with timestamp
    
    Args:
        original_filename: Original filename
        
    Returns:
        Backup filename with timestamp
    """
    if not original_filename:
        return original_filename
    
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Split filename and extension
    if '.' in original_filename:
        name, ext = original_filename.rsplit('.', 1)
        return f"{name}_backup_{timestamp}.{ext}"
    else:
        return f"{original_filename}_backup_{timestamp}"


def sanitize_filename(filename):
    """
    Sanitize filename by removing invalid characters
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    if not filename:
        return filename
    
    # Remove invalid characters for Windows/Unix
    invalid_chars = '<>:"/\\|?*'
    sanitized = ''.join(c for c in filename if c not in invalid_chars)
    
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip(' .')
    
    return sanitized or 'unnamed_file'


def get_memory_usage_mb():
    """
    Get current memory usage in megabytes
    
    Returns:
        Memory usage in MB
    """
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        return memory_info.rss / (1024 * 1024)
    except ImportError:
        return 0


def format_duration(seconds):
    """
    Format duration in seconds to human readable format
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds is None:
        return ''
    
    try:
        seconds = float(seconds)
        
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"
    except (ValueError, TypeError):
        return str(seconds)
