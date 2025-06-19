"""
Scraper module for finding business information
"""
import re
import time
import random
import requests
import logging
from urllib.parse import quote_plus, unquote
from bs4 import BeautifulSoup
from .contact_extractor import ContactExtractor
from ..utils.business_size_detector import BusinessSizeDetector
from ..utils.timing_config import get_timing_manager


class BusinessScraper:
    """Class for scraping business data from various online sources"""
    
    def __init__(self, use_selenium=False):
        self.timing_manager = get_timing_manager()
        """
        Initialize the scraper
        
        Args:
            use_selenium: Whether to use Selenium for JavaScript-heavy sites
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Referer': 'https://www.google.com/',
            'DNT': '1',  # Do Not Track request header
            'Upgrade-Insecure-Requests': '1'
        })
        
        self.driver = None
        self.use_selenium = use_selenium
        self.contact_extractor = ContactExtractor()
        self.business_size_detector = BusinessSizeDetector()
        
        if use_selenium:
            self._setup_selenium()
    
    def _setup_selenium(self):
        """Set up Selenium WebDriver"""
        try:
            from selenium import webdriver
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.by import By
            from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException, WebDriverException
            
            options = Options()
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-notifications")
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Add realistic user agent
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.set_page_load_timeout(30)
            
            # Set window size
            self.driver.set_window_size(1920, 1080)
            
            # Execute script to mask WebDriver
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Add a delay
            time.sleep(self.timing_manager.config.scraping.selenium_init_delay)
            
            print("Selenium WebDriver set up successfully")
            
        except Exception as e:
            print(f"Failed to initialize Selenium: {e}")
            self.use_selenium = False
    
    def find_businesses(self, location, category=None, limit=20):
        """
        Find businesses in a location
        
        Args:
            location: UK location (city, town, or postal code)
            category: Optional business category/type
            limit: Maximum number of businesses to return
            
        Returns:
            List of business dictionaries
        """
        all_businesses = []
        
        # Enhanced location targeting and search query construction
        location_variants = self._generate_location_variants(location)
        
        # Define primary search query with better targeting
        if category:
            search_query = f"{category} in {location}"
        else:
            # For general area searches, use multiple query variations
            search_query = f"businesses in {location}"
            print(f"General area search - will try multiple query variations")
        
        print(f"Starting search for: {search_query}")
        print(f"Location variants: {location_variants}")
        
        # Validate location is UK-based
        is_uk_location = self._validate_uk_location(location)
        if not is_uk_location:
            print(f"Warning: '{location}' may not be a valid UK location")
        
        # Try UK-specific sources first, then fallback to general sources
        uk_sources = [
            self._search_yell,
            self._search_uk_business_directory,
            self._search_thomson_local,
            self._search_192_directory,
            self._search_uk_local_directories,  # New method added
            self._search_scoot_uk            # New method added
        ]
        
        general_sources = [
            self._search_google_maps,
            self._search_google_business,
            self._search_google
        ]
        
        # Combine and randomize sources
        # Prioritize UK sources for UK locations
        sources = uk_sources + general_sources
        random.shuffle(sources)
        
        for source_func in sources:
            # Check if we've reached the limit
            if len(all_businesses) >= limit:
                break
                
            try:
                print(f"Searching using {source_func.__name__}...")
                
                # Get remaining businesses needed
                remaining = limit - len(all_businesses)
                businesses = source_func(search_query, remaining)
                
                print(f"Found {len(businesses)} businesses from {source_func.__name__}")
                
                # Deduplicate based on name and partial address
                for business in businesses:
                    # Check for duplicates using name and address similarity
                    is_duplicate = False
                    business_name_lower = business['name'].lower().strip()
                    business_address = business.get('address', '').lower().strip()
                    
                    for existing in all_businesses:
                        existing_name_lower = existing['name'].lower().strip()
                        existing_address = existing.get('address', '').lower().strip()
                        
                        # Check if names are identical or very similar
                        if business_name_lower == existing_name_lower:
                            is_duplicate = True
                            break
                        
                        # Check if names are similar and addresses match partially
                        if (business_address and existing_address and 
                            len(business_address) > 10 and len(existing_address) > 10):
                            # Check if addresses share significant common parts
                            if (business_address in existing_address or 
                                existing_address in business_address or
                                len(set(business_address.split()) & set(existing_address.split())) > 2):
                                # If addresses are similar, check name similarity
                                if (business_name_lower in existing_name_lower or 
                                    existing_name_lower in business_name_lower):
                                    is_duplicate = True
                                    break
                    
                    if not is_duplicate:
                        # Process and clean business data
                        business = self._process_found_business(business)
                        if business:
                            all_businesses.append(business)
                        
                        # Break if we've reached the limit
                        if len(all_businesses) >= limit:
                            break
                
                # Add a longer delay between sources
                min_delay = self.timing_manager.config.scraping.request_delay
                max_delay = min_delay * 3
                time.sleep(random.uniform(min_delay, max_delay))
                
            except Exception as e:
                # Only log unique errors to avoid spam
                error_key = f"{source_func.__name__}:{str(e)[:50]}"
                if not hasattr(self, '_logged_errors'):
                    self._logged_errors = set()
                if error_key not in self._logged_errors:
                    print(f"Error in {source_func.__name__}: {e}")
                    self._logged_errors.add(error_key)
        
        print(f"Total businesses found: {len(all_businesses)}")
        
        # If we didn't find any businesses, try enhanced fallback searches
        if not all_businesses and limit > 0:
            print("No businesses found with specific search. Trying enhanced fallback searches...")
            
            # For general area searches (no category), try multiple broad search terms
            if not category:
                general_search_terms = [
                    f"companies in {location}",
                    f"local business {location}",
                    f"services {location}",
                    f"shops {location}",
                    f"directory {location}",
                    f"business listings {location}"
                ]
                
                for search_term in general_search_terms:
                    if len(all_businesses) >= limit:
                        break
                    
                    try:
                        print(f"Trying general search: {search_term}")
                        general_businesses = self._search_google(search_term, limit - len(all_businesses))
                        if general_businesses:
                            # Filter businesses to ensure they're actually in the target location
                            filtered_businesses = self._filter_businesses_by_location(general_businesses, location)
                            all_businesses.extend(filtered_businesses)
                            print(f"Found {len(filtered_businesses)} relevant businesses with general search")
                            
                    except Exception as e:
                        print(f"General search failed for {search_term}: {e}")
            
            # Try searches with location variants
            for variant in location_variants[:3]:  # Try up to 3 variants
                if len(all_businesses) >= limit:
                    break
                    
                try:
                    variant_query = f"{category} in {variant}" if category else f"businesses in {variant}"
                    print(f"Trying variant search: {variant_query}")
                    
                    variant_businesses = self._search_google(variant_query, limit - len(all_businesses))
                    if variant_businesses:
                        # Filter businesses to ensure they're actually in the target location
                        filtered_businesses = self._filter_businesses_by_location(variant_businesses, location)
                        all_businesses.extend(filtered_businesses)
                        print(f"Found {len(filtered_businesses)} relevant businesses with variant search")
                        
                except Exception as e:
                    print(f"Variant search failed for {variant}: {e}")
            
            # Try a more generic search without category as final fallback
            if not all_businesses:
                try:
                    generic_businesses = self._search_google(f"businesses in {location}", limit)
                    if generic_businesses:
                        all_businesses.extend(generic_businesses[:limit])
                        print(f"Found {len(generic_businesses)} businesses with generic search")
                except Exception as e:
                    print(f"Generic search failed: {e}")
            
            # Only create placeholder data if absolutely no businesses found and in development mode
            if not all_businesses:
                print("Warning: No real businesses found. This may indicate network issues or location problems.")
                # Create minimal realistic sample data for demonstration
                sample_business_types = [
                    "Local Restaurant", "Hair Salon", "Dental Practice", 
                    "Accounting Firm", "Plumbing Services"
                ]
                
                # Provide helpful guidance instead of placeholder data
                print("\n=== SEARCH GUIDANCE ===")
                print(f"No businesses found for '{search_query}'")
                print("Possible reasons:")
                print("1. Location may be misspelled or not recognized")
                print("2. Category may be too specific")
                print("3. Network connectivity issues")
                print("4. Rate limiting from search sources")
                print("\nSuggestions:")
                print(f"- Try broader location terms (e.g., nearest city to {location})")
                print("- Use more general business categories")
                print("- Check internet connection")
                print("- Wait a few minutes before retrying")
                print("=====================\n")
                
                # Return empty list instead of placeholder data
                return []
        
        return all_businesses[:limit]
    
    def _process_found_business(self, business):
        """Process and clean business data before storing"""
        # Ensure all required fields exist
        if 'name' not in business:
            return None
            
        # Clean up fields
        if 'website' in business and business['website']:
            business['website'] = self._clean_url(business['website'])
            
            # Check if website is a directory/aggregator site
            if self._is_directory_site(business['website']):
                return None
            
            # Verify the website belongs to the business
            if not self._verify_business_website(business['name'], business['website']):
                business['website'] = None
        
        # Extract and validate post code from address
        if 'address' in business and business['address']:
            postcode = self._extract_uk_postcode(business['address'])
            if postcode:
                business['postal_code'] = postcode
                
            # Validate UK address format
            if not self._validate_uk_address(business['address']):
                business['address_verified'] = False
        
        # Enhanced contact extraction for businesses with websites
        if business.get('website'):
            try:
                enhanced_business = self.contact_extractor.extract_comprehensive_contacts(business)
                
                # Merge extracted contact data with existing business data
                if enhanced_business:
                    # Update phone if not already present or if extracted phone is more complete
                    if enhanced_business.get('phone') and (not business.get('phone') or len(enhanced_business['phone']) > len(business.get('phone', ''))):
                        business['phone'] = enhanced_business['phone']
                    
                    # Add primary email if found
                    if enhanced_business.get('primary_email'):
                        business['email'] = enhanced_business['primary_email']
                    
                    # Add all emails
                    if enhanced_business.get('emails'):
                        business['emails'] = enhanced_business['emails']
                    
                    # Add phone numbers list
                    if enhanced_business.get('phone_numbers'):
                        business['phone_numbers'] = enhanced_business['phone_numbers']
                    
                    # Add social media links
                    if enhanced_business.get('social_media'):
                        business['social_media'] = enhanced_business['social_media']
                    
                    # Update address if extracted address is more complete
                    if enhanced_business.get('full_address') and (not business.get('address') or len(enhanced_business['full_address']) > len(business.get('address', ''))):
                        business['address'] = enhanced_business['full_address']
                        # Re-extract postcode from new address
                        postcode = self._extract_uk_postcode(business['address'])
                        if postcode:
                            business['postal_code'] = postcode
                    
                    # Add opening hours
                    if enhanced_business.get('opening_hours'):
                        business['opening_hours'] = enhanced_business['opening_hours']
                    
                    # Add business description
                    if enhanced_business.get('description'):
                        business['description'] = enhanced_business['description']
                    
                    # Add company registration details
                    if enhanced_business.get('company_number'):
                        business['company_number'] = enhanced_business['company_number']
                    
                    if enhanced_business.get('vat_number'):
                        business['vat_number'] = enhanced_business['vat_number']
                    
                    # Add contact completeness score
                    if enhanced_business.get('contact_score'):
                        business['contact_completeness'] = enhanced_business['contact_score']
                        print(f"Enhanced contact data for {business['name']}: {business['contact_completeness']}% complete")
                    
            except Exception as e:
                print(f"Error extracting contact data for {business['name']}: {e}")
                # Continue processing even if contact extraction fails
        
        # Detect business size
        try:
            size_category, confidence, reasoning = self.business_size_detector.detect_size(business)
            business['business_size'] = size_category
            business['size_confidence'] = confidence
            business['size_reasoning'] = reasoning
            
            # Use the detector's employee count estimation method
            if 'employee_count' not in business or business['employee_count'] == 0:
                business['employee_count'] = self.business_size_detector.estimate_employee_count(size_category)
            
            print(f"Detected business size for {business['name']}: {size_category} (confidence: {confidence}%)")
        except (AttributeError, ValueError, KeyError) as e:
            print(f"Error detecting business size for {business['name']}: {e}")
            business['business_size'] = 'Unknown'
            business['employee_count'] = 0
        
        # Set priority based on multiple factors (including contact completeness)
        business['priority'] = self._calculate_business_priority(business)
        
        return business
        
    def _is_directory_site(self, url):
        """Check if the URL is a business directory or aggregator site"""
        directory_patterns = [
            r'yell\.com', r'thomsonlocal\.com', r'192\.com',
            r'scoot\.co\.uk', r'yelp\.co\.uk', r'cylex-uk\.co\.uk',
            r'directory', r'listings', r'businesses'
        ]
        return any(re.search(pattern, url.lower()) for pattern in directory_patterns)
    
    def _verify_business_website(self, business_name, website):
        """Verify if the website likely belongs to the business"""
        try:
            response = self.session.get(website, timeout=10)
            if response.status_code != 200:
                return False
                
            # Convert business name to a search pattern
            name_pattern = re.sub(r'[^a-zA-Z0-9\s]', '', business_name.lower())
            name_words = set(name_pattern.split())
            
            # Check title and meta description
            soup = BeautifulSoup(response.text, 'lxml')
            title = soup.title.string.lower() if soup.title else ''
            meta_desc = soup.find('meta', {'name': 'description'})
            meta_desc = meta_desc['content'].lower() if meta_desc else ''
            
            # Calculate word match percentage
            title_words = set(re.sub(r'[^a-zA-Z0-9\s]', '', title).split())
            desc_words = set(re.sub(r'[^a-zA-Z0-9\s]', '', meta_desc).split())
            
            matches = len(name_words.intersection(title_words.union(desc_words)))
            match_percentage = matches / len(name_words) if name_words else 0
            
            return match_percentage >= 0.5
            
        except Exception as e:
            print(f"Error verifying website {website}: {e}")
            return False
    
    def _validate_uk_address(self, address):
        """Validate if the address follows UK format"""
        uk_patterns = [
            r'\b[A-Z]{1,2}[0-9][A-Z0-9]? [0-9][ABD-HJLNP-UW-Z]{2}\b',  # Postcode
            r'\b(road|street|avenue|lane|court|close|way|drive)\b',  # Street types
            r'\b[0-9]+[a-zA-Z]?\b.*\b(road|street|avenue|lane)\b'  # House number + street
        ]
        return any(re.search(pattern, address, re.IGNORECASE) for pattern in uk_patterns)
    
    def _calculate_business_priority(self, business):
        """Calculate business priority based on multiple factors"""
        priority_score = 50  # Start with base score (higher is better)
        
        # Website availability (20 points)
        if business.get('website'):
            priority_score += 20
        else:
            priority_score -= 10  # Penalize missing website
        
        # Contact completeness (30 points max)
        contact_completeness = business.get('contact_completeness', 0)
        priority_score += (contact_completeness * 0.3)  # Scale to 30 points max
        
        # Phone number availability (15 points)
        if business.get('phone'):
            priority_score += 15
        else:
            priority_score -= 5
        
        # Email availability (10 points)
        if business.get('email'):
            priority_score += 10
        
        # Address verification (10 points)
        if business.get('address_verified') is not False:
            priority_score += 10
        else:
            priority_score -= 5
        
        # Social media presence (5 points)
        if business.get('social_media'):
            priority_score += 5
        
        # Opening hours (5 points)
        if business.get('opening_hours'):
            priority_score += 5
        
        # Company registration details (5 points)
        if business.get('company_number') or business.get('vat_number'):
            priority_score += 5
        
        # Convert to 1-5 scale (1 = highest priority, 5 = lowest)
        if priority_score >= 90:
            return 1  # Excellent - complete contact info
        elif priority_score >= 75:
            return 2  # Good - most contact info available
        elif priority_score >= 60:
            return 3  # Average - some contact info
        elif priority_score >= 45:
            return 4  # Poor - minimal contact info
        else:
            return 5  # Very poor - very little contact info
    
    def _clean_url(self, url):
        """Clean and normalize a URL"""
        if not url:
            return ""
            
        # Ensure URL has a scheme
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Remove tracking parameters
        url = re.sub(r'\?utm_.*', '', url)
        url = re.sub(r'&utm_.*', '', url)
        
        # Remove trailing slash
        if url.endswith('/'):
            url = url[:-1]
            
        return url
    
    def _extract_uk_postcode(self, text):
        """Extract UK postcode from text"""
        if not text:
            return None
            
        # UK postcode pattern
        postcode_pattern = r'[A-Z]{1,2}[0-9][0-9A-Z]?\s?[0-9][A-Z]{2}'
        match = re.search(postcode_pattern, text.upper())
        return match.group(0) if match else None
    
    def _generate_location_variants(self, location):
        """Generate location variants for better search coverage"""
        variants = [location]
        
        # Common UK location patterns
        location_lower = location.lower()
        
        # Add variants with common suffixes/prefixes
        if not any(suffix in location_lower for suffix in [' uk', ' england', ' scotland', ' wales']):
            variants.extend([
                f"{location}, UK",
                f"{location}, England",
                f"{location} UK"
            ])
        
        # Handle common abbreviations
        abbreviations = {
            'st ': 'saint ',
            'st.': 'saint',
            'upon ': 'on ',
            'under ': 'under-'
        }
        
        for abbrev, full in abbreviations.items():
            if abbrev in location_lower:
                variants.append(location.lower().replace(abbrev, full).title())
            elif full in location_lower:
                variants.append(location.lower().replace(full, abbrev).title())
        
        # Add nearby major cities for small towns
        major_cities = {
            'london': ['greater london', 'london borough'],
            'manchester': ['greater manchester'],
            'birmingham': ['west midlands'],
            'leeds': ['west yorkshire'],
            'glasgow': ['greater glasgow'],
            'liverpool': ['merseyside'],
            'bristol': ['south west england'],
            'sheffield': ['south yorkshire'],
            'edinburgh': ['lothian'],
            'cardiff': ['south wales']
        }
        
        for city, areas in major_cities.items():
            if city in location_lower:
                variants.extend(areas)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_variants = []
        for variant in variants:
            if variant.lower() not in seen:
                seen.add(variant.lower())
                unique_variants.append(variant)
        
        return unique_variants
    
    def _validate_uk_location(self, location):
        """Validate if location appears to be UK-based"""
        location_lower = location.lower()
        
        # UK indicators
        uk_indicators = [
            'uk', 'england', 'scotland', 'wales', 'northern ireland',
            'london', 'manchester', 'birmingham', 'leeds', 'glasgow',
            'liverpool', 'bristol', 'sheffield', 'edinburgh', 'cardiff',
            'yorkshire', 'lancashire', 'surrey', 'kent', 'essex',
            'hampshire', 'devon', 'cornwall', 'dorset', 'somerset'
        ]
        
        # Check for UK postcodes pattern
        uk_postcode_pattern = r'\b[A-Z]{1,2}[0-9][A-Z0-9]?\s?[0-9][A-Z]{2}\b'
        if re.search(uk_postcode_pattern, location.upper()):
            return True
        
        # Check for UK indicators
        return any(indicator in location_lower for indicator in uk_indicators)
    
    def _filter_businesses_by_location(self, businesses, target_location):
        """Filter businesses to ensure they're relevant to the target location"""
        filtered = []
        target_lower = target_location.lower()
        
        for business in businesses:
            # Check if business address contains target location
            address = business.get('address', '').lower()
            
            # Direct match
            if target_lower in address:
                filtered.append(business)
                continue
            
            # Check for partial matches (for compound location names)
            target_words = target_lower.split()
            if len(target_words) > 1:
                if any(word in address for word in target_words if len(word) > 3):
                    filtered.append(business)
                    continue
            
            # Check business name for location
            name = business.get('name', '').lower()
            if target_lower in name:
                filtered.append(business)
                continue
        
        return filtered
    
    def _search_google_maps(self, query, limit=20):
        """Search for businesses on Google Maps"""
        businesses = []
        
        try:
            # Format the query for URL
            search_query = f"{query}"
            url = f"https://www.google.com/maps/search/{quote_plus(search_query)}"
            
            if self.use_selenium and self.driver:
                # Use direct requests first for a less-detectable approach
                direct_results = self._google_maps_direct_request(search_query, limit)
                if direct_results:
                    return direct_results
                
                # Fallback to Selenium
                print(f"Searching Google Maps for: {search_query}")
                self.driver.get(url)
                
                # Wait for results to load with explicit wait
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-result-index]"))
                    )
                except TimeoutException:
                    time.sleep(self.timing_manager.config.scraping.page_load_delay)  # Fallback to shorter sleep
                
                # Print page source debug
                page_source = self.driver.page_source
                if "sorry" in page_source.lower() and "blocking" in page_source.lower():
                    print("Google Maps detection issue, trying alternative approach")
                    return []
                
                # Find business listings using various selectors
                business_elements = []
                selectors = [
                    "//div[contains(@class, 'Nv2PK')]",
                    "//div[contains(@class, 'qBF1Pd')]",
                    "//div[contains(@class, 'gPq6rf')]",
                    "//div[contains(@class, 'bfdHYd')]",
                    "//div[contains(@class, 'THOPZb')]",
                    "//div[contains(@class, 'hfpxzc')]",
                    "//div[@role='article']",
                    "//div[contains(@role, 'feed')]/div"
                ]
                
                for selector in selectors:
                    try:
                        elements = self.driver.find_elements("xpath", selector)
                        if elements:
                            business_elements = elements
                            print(f"Found {len(elements)} elements with selector: {selector}")
                            break
                    except Exception as e:
                        print(f"Selector {selector} failed: {e}")
                
                if not business_elements:
                    # Try to click on the first visible result and extract info
                    try:
                        search_results = self.driver.find_elements("xpath", "//a[@role='link' and contains(@href, 'maps/place')]")
                        if search_results:
                            for result in search_results[:min(5, len(search_results))]:
                                try:
                                    # Extract business name from the result
                                    business_name = result.text.split('\n')[0]
                                    if not business_name:
                                        continue
                                    
                                    # Extract href for potential address/website data
                                    href = result.get_attribute('href')
                                    place_data = href.split('/maps/place/')[1].split('/')[0]
                                    place_data = unquote(place_data)
                                    
                                    business = {
                                        'name': business_name,
                                        'source': 'Google Maps Link',
                                        'address': place_data if ',' in place_data else None
                                    }
                                    
                                    # Extract business category if possible
                                    if "in " in query:
                                        business_type = query.split("in ")[0].strip()
                                        if business_type != "businesses":
                                            business['business_type'] = business_type
                                    
                                    businesses.append(business)
                                except Exception as e:
                                    print(f"Error extracting from search result: {e}")
                    except Exception as e:
                        print(f"Error finding search results: {e}")
                else:
                    # Process the business elements found
                    processed_count = 0
                    for element in business_elements[:limit]:
                        try:
                            # Try to extract business name
                            name = None
                            name_selectors = [
                                ".//div[contains(@class, 'qBF1Pd')]",
                                ".//div[contains(@class, 'fontHeadlineSmall')]",
                                ".//span[contains(@class, 'fontHeadlineSmall')]",
                                ".//div[@role='heading']",
                                ".//h3",
                                ".//div[contains(@class, 'dmRWX')]"
                            ]
                            
                            for selector in name_selectors:
                                try:
                                    name_elem = element.find_element("xpath", selector)
                                    if name_elem and name_elem.text.strip():
                                        name = name_elem.text.strip()
                                        break
                                except (NoSuchElementException, StaleElementReferenceException, WebDriverException):
                                    continue
                            
                            # If no name found, try using the first line of text in the element
                            if not name:
                                try:
                                    element_text = element.text.strip()
                                    if element_text:
                                        name = element_text.split('\n')[0]
                                except (AttributeError, IndexError):
                                    pass
                            
                            if not name:
                                continue
                            
                            business = {'name': name, 'source': 'Google Maps'}
                            processed_count += 1
                            
                            # Extract address
                            try:
                                address_selectors = [
                                    ".//div[contains(@class, 'W4Efsd')][1]//div[contains(@class, 'fontBodyMedium')]",
                                    ".//div[contains(@class, 'W4Efsd')]//span[contains(@class, 'fontBodyMedium')]",
                                    ".//div[contains(@class, 'W4Efsd')][1]",
                                    ".//div[contains(@jsan, 'address')]"
                                ]
                                
                                for selector in address_selectors:
                                    try:
                                        addr_elem = element.find_element("xpath", selector)
                                        if addr_elem and addr_elem.text.strip():
                                            addr_text = addr_elem.text.strip()
                                            # Check if this looks like an address (contains commas, numbers, etc.)
                                            if (',' in addr_text or any(c.isdigit() for c in addr_text)) and len(addr_text) > 5:
                                                business['address'] = addr_text
                                                break
                                    except (NoSuchElementException, StaleElementReferenceException, WebDriverException):
                                        continue
                            except Exception as e:
                                print(f"Error extracting address: {e}")
                            
                            # Extract business type
                            try:
                                type_selectors = [
                                    ".//div[contains(@class, 'W4Efsd')][2]//div[contains(@class, 'fontBodyMedium')]",
                                    ".//div[contains(@class, 'fontBodyMedium')][contains(text(), 'Restaurant') or contains(text(), 'Shop') or contains(text(), 'Service')]"
                                ]
                                
                                for selector in type_selectors:
                                    try:
                                        type_elem = element.find_element("xpath", selector)
                                        if type_elem and type_elem.text.strip():
                                            business['business_type'] = type_elem.text.strip()
                                            break
                                    except (NoSuchElementException, StaleElementReferenceException, WebDriverException):
                                        continue
                            except Exception as e:
                                print(f"Error extracting business type: {e}")
                            
                            # If no business type was found, use the one from the search query
                            if 'business_type' not in business and "in " in query:
                                business_type = query.split("in ")[0].strip()
                                if business_type != "businesses":
                                    business['business_type'] = business_type
                            
                            # Try to click on the element to get more details
                            try:
                                element.click()
                                time.sleep(self.timing_manager.config.scraping.element_interaction_delay)
                                
                                # Extract website
                                website_buttons = self.driver.find_elements("xpath", "//a[contains(@href, 'http') and @data-item-id='authority' or contains(@href, 'website')]")
                                if website_buttons:
                                    business['website'] = website_buttons[0].get_attribute('href')
                                
                                # Extract phone
                                phone_buttons = self.driver.find_elements("xpath", "//button[contains(@data-item-id, 'phone')]")
                                if phone_buttons:
                                    phone_text = phone_buttons[0].text.strip()
                                    # Extract just the phone number with a regex
                                    phone_match = re.search(r'[\d\s()+\-]{9,}', phone_text)
                                    if phone_match:
                                        business['phone'] = phone_match.group(0)
                                
                                # Go back
                                self.driver.back()
                                time.sleep(self.timing_manager.config.scraping.navigation_delay)
                            except Exception as e:
                                print(f"Error getting details: {e}")
                                # Try to recover
                                try:
                                    self.driver.get(url)
                                    time.sleep(self.timing_manager.config.scraping.page_load_delay)
                                except (WebDriverException, TimeoutException):
                                    pass
                            
                            businesses.append(business)
                            
                        except Exception as e:
                            print(f"Error processing business element: {e}")
                    
                    print(f"Processed {processed_count} business elements")
            else:
                print("Selenium not available for Google Maps, using fallback method")
        
        except Exception as e:
            print(f"Error in Google Maps search: {e}")
        
        return businesses
    
    def _google_maps_direct_request(self, query, limit=20):
        """Try to get Google Maps results using direct requests"""
        businesses = []
        
        try:
            # Use a more specific URL format
            search_url = f"https://www.google.com/maps/search/{quote_plus(query)}/"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'en-GB,en;q=0.9',
                'Referer': 'https://www.google.com/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'dnt': '1',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = requests.get(search_url, headers=headers)
            
            if response.status_code == 200:
                # Process the HTML response
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for places data in the page
                # This is tricky as Google often embeds data in JavaScript
                script_tags = soup.select('script')
                
                for script in script_tags:
                    script_text = script.string
                    if not script_text:
                        continue
                    
                    # Look for JSON data in the script
                    if '"places"' in script_text and '"name"' in script_text:
                        try:
                            # Extract JSON-like data
                            json_start = script_text.find('[{')
                            if json_start == -1:
                                continue
                                
                            json_text = script_text[json_start:]
                            json_end = self._find_matching_bracket(json_text, 0)
                            
                            if json_end == -1:
                                continue
                                
                            json_data = json_text[:json_end+1]
                            
                            # Extract business data from text using regex
                            business_matches = re.finditer(r'"name":"([^"]+)".*?"address":\["([^"]+)"', script_text)
                            
                            count = 0
                            for match in business_matches:
                                if count >= limit:
                                    break
                                    
                                name = match.group(1)
                                address = match.group(2)
                                
                                # Extract website if present
                                website_pattern = f'"name":"{re.escape(name)}".*?"website":"([^"]+)"'
                                website_match = re.search(website_pattern, script_text)
                                website = website_match.group(1) if website_match else None
                                
                                # Extract phone if present
                                phone_pattern = f'"name":"{re.escape(name)}".*?"phone":"([^"]+)"'
                                phone_match = re.search(phone_pattern, script_text)
                                phone = phone_match.group(1) if phone_match else None
                                
                                # Create business entry
                                business = {
                                    'name': name,
                                    'address': address,
                                    'source': 'Google Maps Direct',
                                }
                                
                                if website:
                                    business['website'] = website
                                    
                                if phone:
                                    business['phone'] = phone
                                
                                # Extract business type
                                if "in " in query:
                                    business_type = query.split("in ")[0].strip()
                                    if business_type != "businesses":
                                        business['business_type'] = business_type
                                
                                businesses.append(business)
                                count += 1
                        except Exception as e:
                            print(f"Error parsing Google Maps script data: {e}")
        
        except Exception as e:
            print(f"Error in Google Maps direct request: {e}")
        
        return businesses
    
    def _find_matching_bracket(self, text, start_pos):
        """Find the position of the matching closing bracket"""
        if text[start_pos] != '[':
            return -1
            
        stack = 1
        for i in range(start_pos + 1, len(text)):
            if text[i] == '[':
                stack += 1
            elif text[i] == ']':
                stack -= 1
                if stack == 0:
                    return i
        
        return -1
    
    def _search_yell(self, query, limit=20):
        """Search for businesses on Yell.com"""
        businesses = []
        
        # Parse the query to match Yell's format
        if "in " in query:
            parts = query.split("in ")
            what = parts[0].strip()
            where = parts[1].strip()
        else:
            what = "businesses"
            where = query
        
        # Format for Yell's URL structure
        url = f"https://www.yell.com/ucs/UcsSearchAction.do?keywords={quote_plus(what)}&location={quote_plus(where)}"
        
        try:
            print(f"Searching Yell.com for: {what} in {where}")
            
            # First try direct request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'en-GB,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Referer': 'https://www.yell.com/',
                'Connection': 'keep-alive'
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Try various selectors for Yell.com
                selectors = [
                    '.businessCapsule--mainRow',
                    '.businessCapsule',
                    'article.businessCapsule',
                    'div[data-tracking=businesscapsule]',
                    '.col-sm-12[itemtype="http://schema.org/LocalBusiness"]'
                ]
                
                business_elements = []
                for selector in selectors:
                    elements = soup.select(selector)
                    if elements:
                        business_elements = elements
                        print(f"Found {len(elements)} elements with selector: {selector}")
                        break
                
                # Process business elements
                for element in business_elements[:limit]:
                    try:
                        # Extract business name
                        name_elem = element.select_one('.businessCapsule--name, h2 a, .business-name')
                        if not name_elem:
                            continue
                            
                        name = name_elem.text.strip()
                        if not name:
                            continue
                        
                        business = {'name': name, 'source': 'Yell.com'}
                        
                        # Extract address
                        address_elem = element.select_one('.businessCapsule--address, .address, [itemprop=address]')
                        if address_elem:
                            business['address'] = address_elem.text.strip()
                        
                        # Extract phone
                        phone_elem = element.select_one('.businessCapsule--telephone, .telephone, [itemprop=telephone]')
                        if phone_elem:
                            business['phone'] = phone_elem.text.strip()
                        
                        # Extract website
                        website_elem = element.select_one('a.businessCapsule--websiteUrl, a.website, [itemprop=url]')
                        if website_elem and 'href' in website_elem.attrs:
                            website_url = website_elem['href']
                            
                            # Handle Yell redirects
                            if 'ucs/redirectws' in website_url:
                                # Extract actual URL from redirect parameter
                                redirect_match = re.search(r'to=([^&]+)', website_url)
                                if redirect_match:
                                    website_url = redirect_match.group(1)
                            
                            business['website'] = website_url
                        
                        # Extract business type
                        type_elem = element.select_one('.businessCapsule--classification, .business-category, [itemprop=category]')
                        if type_elem:
                            business['business_type'] = type_elem.text.strip()
                        elif what != "businesses":
                            business['business_type'] = what
                        
                        businesses.append(business)
                        
                    except Exception as e:
                        print(f"Error extracting Yell business data: {e}")
            
            # If direct request didn't work and Selenium is available, try that
            if not businesses and self.use_selenium and self.driver:
                try:
                    self.driver.get(url)
                    time.sleep(3)
                    
                    # Try to find business listings
                    business_elements = []
                    selectors = [
                        "//div[contains(@class, 'businessCapsule--mainRow')]",
                        "//div[contains(@class, 'businessCapsule')]",
                        "//article[contains(@class, 'businessCapsule')]",
                        "//div[@data-tracking='businesscapsule']"
                    ]
                    
                    for selector in selectors:
                        try:
                            found_elements = self.driver.find_elements("xpath", selector)
                            if found_elements:
                                business_elements = found_elements
                                print(f"Found {len(business_elements)} elements with selector: {selector}")
                                break
                        except Exception as e:
                            # Reduce selector error spam
                            if not hasattr(self, '_selector_errors'):
                                self._selector_errors = set()
                            selector_key = f"{selector}:{str(e)[:30]}"
                            if selector_key not in self._selector_errors:
                                print(f"Selector {selector} failed: {e}")
                                self._selector_errors.add(selector_key)
                    
                    for element in business_elements[:limit]:
                        try:
                            # Extract business name
                            name_selectors = [
                                ".//h2[contains(@class, 'businessCapsule--name')]",
                                ".//h2/a",
                                ".//a[contains(@class, 'businessCapsule--title')]"
                            ]
                            
                            name = None
                            for selector in name_selectors:
                                try:
                                    name_elem = element.find_element("xpath", selector)
                                    name = name_elem.text.strip()
                                    if name:
                                        break
                                except (NoSuchElementException, StaleElementReferenceException, WebDriverException):
                                    # Silently continue to next selector without logging
                                    continue
                            
                            if not name:
                                continue
                            
                            business = {'name': name, 'source': 'Yell.com (Selenium)'}
                            print(f"Found business: {name}")
                            
                            # Extract address
                            address_selectors = [
                                ".//span[contains(@class, 'businessCapsule--address')]",
                                ".//span[contains(@class, 'address')]",
                                ".//div[contains(@class, 'businessCapsule--address')]",
                                ".//*[contains(@itemprop, 'address')]"
                            ]
                            
                            for selector in address_selectors:
                                try:
                                    address_elem = element.find_element("xpath", selector)
                                    address = address_elem.text.strip()
                                    if address:
                                        business['address'] = address
                                        break
                                except (NoSuchElementException, StaleElementReferenceException, WebDriverException):
                                    # Silently continue to next selector
                                    continue
                            
                            # Extract phone
                            phone_selectors = [
                                ".//span[contains(@class, 'businessCapsule--telephone')]",
                                ".//span[contains(@class, 'phone')]",
                                ".//a[contains(@class, 'telephone')]",
                                ".//*[contains(@itemprop, 'telephone')]"
                            ]
                            
                            for selector in phone_selectors:
                                try:
                                    phone_elem = element.find_element("xpath", selector)
                                    phone = phone_elem.text.strip()
                                    if phone:
                                        business['phone'] = phone
                                        break
                                except (AttributeError, ValueError, IndexError) as e:
                                    # Skip invalid elements and continue with next
                                    continue
                            
                            # Extract website
                            website_selectors = [
                                ".//a[contains(@class, 'businessCapsule--websiteUrl')]",
                                ".//a[contains(@class, 'website')]"
                            ]
                            
                            for selector in website_selectors:
                                try:
                                    website_elem = element.find_element("xpath", selector)
                                    website_url = website_elem.get_attribute('href')
                                    
                                    # Handle Yell redirects
                                    if 'ucs/redirectws' in website_url:
                                        # Extract actual URL from redirect parameter
                                        redirect_match = re.search(r'to=([^&]+)', website_url)
                                        if redirect_match:
                                            website_url = redirect_match.group(1)
                                    
                                    business['website'] = website_url
                                    break
                                except (AttributeError, ValueError, IndexError):
                                    continue
                            
                            # Extract business type
                            type_selectors = [
                                ".//span[contains(@class, 'businessCapsule--classification')]",
                                ".//span[contains(@class, 'category')]",
                                ".//*[contains(@itemprop, 'category')]"
                            ]
                            
                            for selector in type_selectors:
                                try:
                                    type_elem = element.find_element("xpath", selector)
                                    business_type = type_elem.text.strip()
                                    if business_type:
                                        business['business_type'] = business_type
                                        break
                                except (AttributeError, ValueError, IndexError):
                                    pass
                            continue
                            
                            if 'business_type' not in business and what != "businesses":
                                business['business_type'] = what
                            
                            businesses.append(business)
                            
                        except Exception as e:
                            print(f"Error extracting Yell business data: {e}")
                except Exception as e:
                    print(f"Error using Selenium for Yell.com: {e}")
        
        except Exception as e:
            print(f"Error in Yell.com search: {e}")
        
        print(f"Found {len(businesses)} businesses from Yell.com")
        return businesses
    
    def _search_uk_business_directory(self, query, limit=20):
        """Search for businesses on UK Business Directory"""
        businesses = []
        
        # Parse the query to match the directory's format
        if "in " in query:
            parts = query.split("in ")
            what = parts[0].strip()
            where = parts[1].strip()
        else:
            what = "businesses"
            where = query
        
        # Format for UK Business Directory URL structure
        url = f"https://www.ukbusinessdirectory.com/search/?q={quote_plus(what)}&l={quote_plus(where)}"
        
        try:
            print(f"Searching UK Business Directory for: {what} in {where}")
            
            # First try direct request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'en-GB,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Referer': 'https://www.ukbusinessdirectory.com/',
                'Connection': 'keep-alive'
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find business listings
                business_elements = soup.select('.listing, .business-listing, .result-item')
                print(f"Found {len(business_elements)} elements with direct request")
                
                for element in business_elements[:limit]:
                    try:
                        # Extract business name
                        name_elem = element.select_one('h3 a, h2 a, .business-name a')
                        if not name_elem:
                            continue
                            
                        name = name_elem.text.strip()
                        
                        business = {'name': name, 'source': 'UK Business Directory'}
                        
                        # Extract address
                        address_elem = element.select_one('.address, .business-address')
                        if address_elem:
                            business['address'] = address_elem.text.strip()
                        
                        # Extract phone
                        phone_elem = element.select_one('.phone, .telephone, .business-phone')
                        if phone_elem:
                            business['phone'] = phone_elem.text.strip()
                        
                        # Extract website
                        website_elem = element.select_one('a.website, .business-website a')
                        if website_elem and 'href' in website_elem.attrs:
                            business['website'] = website_elem['href']
                        
                        # Extract business type
                        type_elem = element.select_one('.category, .business-category')
                        if type_elem:
                            business['business_type'] = type_elem.text.strip()
                        elif what != "businesses":
                            business['business_type'] = what
                        
                        businesses.append(business)
                        
                    except Exception as e:
                        print(f"Error extracting UK Business Directory data: {e}")
            
            # If direct request didn't work and Selenium is available, try that
            if not businesses and self.use_selenium and self.driver:
                try:
                    self.driver.get(url)
                    time.sleep(3)
                    
                    # Try to find business listings
                    business_elements = []
                    selectors = [
                        "//div[contains(@class, 'listing')]",
                        "//div[contains(@class, 'business-listing')]",
                        "//li[contains(@class, 'listing')]",
                        "//div[contains(@class, 'result-item')]"
                    ]
                    
                    for selector in selectors:
                        try:
                            found_elements = self.driver.find_elements("xpath", selector)
                            if found_elements:
                                business_elements = found_elements
                                print(f"Found {len(business_elements)} elements with Selenium selector: {selector}")
                                break
                        except Exception as e:
                            print(f"Selector {selector} failed: {e}")
                    
                    for element in business_elements[:limit]:
                        try:
                            # Extract business name
                            name_selectors = [
                                ".//h3/a",
                                ".//h2/a",
                                ".//div[contains(@class, 'business-name')]/a"
                            ]
                            
                            name = None
                            for selector in name_selectors:
                                try:
                                    name_elem = element.find_element("xpath", selector)
                                    name = name_elem.text.strip()
                                    if name:
                                        break
                                except:
                                    continue
                            
                            if not name:
                                continue
                            
                            business = {'name': name, 'source': 'UK Business Directory (Selenium)'}
                            print(f"Found business: {name}")
                            
                            # Extract address
                            address_selectors = [
                                ".//div[contains(@class, 'address')]",
                                ".//span[contains(@class, 'address')]",
                                ".//div[contains(@class, 'business-address')]"
                            ]
                            
                            for selector in address_selectors:
                                try:
                                    address_elem = element.find_element("xpath", selector)
                                    address = address_elem.text.strip()
                                    if address:
                                        business['address'] = address
                                        break
                                except:
                                    continue
                            
                            # Extract phone
                            phone_selectors = [
                                ".//div[contains(@class, 'phone')]",
                                ".//span[contains(@class, 'phone')]",
                                ".//div[contains(@class, 'telephone')]"
                            ]
                            
                            for selector in phone_selectors:
                                try:
                                    phone_elem = element.find_element("xpath", selector)
                                    phone = phone_elem.text.strip()
                                    if phone:
                                        business['phone'] = phone
                                        break
                                except:
                                    continue
                            
                            # Extract website
                            website_selectors = [
                                ".//a[contains(@class, 'website')]",
                                ".//a[contains(text(), 'website')]",
                                ".//div[contains(@class, 'business-website')]//a"
                            ]
                            
                            for selector in website_selectors:
                                try:
                                    website_elem = element.find_element("xpath", selector)
                                    website = website_elem.get_attribute('href')
                                    if website:
                                        business['website'] = website
                                        break
                                except:
                                    continue
                            
                            # Extract business type
                            type_selectors = [
                                ".//div[contains(@class, 'category')]",
                                ".//span[contains(@class, 'category')]",
                                ".//div[contains(@class, 'business-category')]"
                            ]
                            
                            for selector in type_selectors:
                                try:
                                    type_elem = element.find_element("xpath", selector)
                                    business_type = type_elem.text.strip()
                                    if business_type:
                                        business['business_type'] = business_type
                                        break
                                except:
                                    continue
                            
                            if 'business_type' not in business and what != "businesses":
                                business['business_type'] = what
                            
                            businesses.append(business)
                            
                        except Exception as e:
                            print(f"Error extracting UK Business Directory data with Selenium: {e}")
                except Exception as e:
                    print(f"Error using Selenium for UK Business Directory: {e}")
        
        except Exception as e:
            print(f"Error in UK Business Directory search: {e}")
        
        print(f"Found {len(businesses)} businesses from UK Business Directory")
        return businesses
    
    def _search_thomson_local(self, query, limit=20):
        """Search for businesses on Thomson Local directory"""
        businesses = []
        
        # Parse the query to match the directory's format
        if "in " in query:
            parts = query.split("in ")
            what = parts[0].strip()
            where = parts[1].strip()
        else:
            what = "businesses"
            where = query
        
        # Format for Thomson Local URL structure
        url = f"https://www.thomsonlocal.com/search/{quote_plus(what)}/{quote_plus(where)}"
        
        try:
            print(f"Searching Thomson Local for: {what} in {where}")
            
            # First try direct request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'en-GB,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Referer': 'https://www.thomsonlocal.com/',
                'Connection': 'keep-alive'
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find business listings
                business_elements = soup.select('.biz-listing, .listing, .business-item')
                print(f"Found {len(business_elements)} Thomson Local elements with direct request")
                
                for element in business_elements[:limit]:
                    try:
                        # Extract business name
                        name_elem = element.select_one('h2 a, h3 a, .business-name')
                        if not name_elem:
                            continue
                            
                        name = name_elem.text.strip()
                        
                        business = {'name': name, 'source': 'Thomson Local'}
                        
                        # Extract address
                        address_elem = element.select_one('.address, .listing-address')
                        if address_elem:
                            business['address'] = address_elem.text.strip()
                        
                        # Extract phone
                        phone_elem = element.select_one('.tel, .phone, .telephone')
                        if phone_elem:
                            business['phone'] = phone_elem.text.strip()
                        
                        # Extract website
                        website_elem = element.select_one('a.website, .url a')
                        if website_elem and 'href' in website_elem.attrs:
                            business['website'] = website_elem['href']
                        
                        # Extract business type
                        type_elem = element.select_one('.category, .business-category')
                        if type_elem:
                            business['business_type'] = type_elem.text.strip()
                        elif what != "businesses":
                            business['business_type'] = what
                        
                        businesses.append(business)
                        
                    except Exception as e:
                        print(f"Error extracting Thomson Local data: {e}")
            
            # If direct request didn't work and Selenium is available, try that
            if not businesses and self.use_selenium and self.driver:
                try:
                    self.driver.get(url)
                    time.sleep(3)
                    
                    # Try to find business listings
                    business_elements = []
                    selectors = [
                        "//div[contains(@class, 'biz-listing')]",
                        "//div[contains(@class, 'listing')]",
                        "//div[contains(@class, 'business-item')]"
                    ]
                    
                    for selector in selectors:
                        try:
                            found_elements = self.driver.find_elements("xpath", selector)
                            if found_elements:
                                business_elements = found_elements
                                print(f"Found {len(business_elements)} Thomson Local elements with Selenium selector: {selector}")
                                break
                        except Exception as e:
                            print(f"Selector {selector} failed: {e}")
                    
                    for element in business_elements[:limit]:
                        try:
                            # Extract business name
                            name_selectors = [
                                ".//h2/a",
                                ".//h3/a",
                                ".//div[contains(@class, 'business-name')]"
                            ]
                            
                            name = None
                            for selector in name_selectors:
                                try:
                                    name_elem = element.find_element("xpath", selector)
                                    name = name_elem.text.strip()
                                    if name:
                                        break
                                except:
                                    continue
                            
                            if not name:
                                continue
                            
                            business = {'name': name, 'source': 'Thomson Local (Selenium)'}
                            print(f"Found Thomson Local business: {name}")
                            
                            # Extract address
                            address_selectors = [
                                ".//div[contains(@class, 'address')]",
                                ".//span[contains(@class, 'address')]",
                                ".//div[contains(@class, 'listing-address')]"
                            ]
                            
                            for selector in address_selectors:
                                try:
                                    address_elem = element.find_element("xpath", selector)
                                    address = address_elem.text.strip()
                                    if address:
                                        business['address'] = address
                                        break
                                except:
                                    continue
                            
                            # Extract phone
                            phone_selectors = [
                                ".//div[contains(@class, 'tel')]",
                                ".//span[contains(@class, 'phone')]",
                                ".//div[contains(@class, 'telephone')]"
                            ]
                            
                            for selector in phone_selectors:
                                try:
                                    phone_elem = element.find_element("xpath", selector)
                                    phone = phone_elem.text.strip()
                                    if phone:
                                        business['phone'] = phone
                                        break
                                except:
                                    continue
                            
                            # Extract website
                            website_selectors = [
                                ".//a[contains(@class, 'website')]",
                                ".//a[contains(@class, 'url')]"
                            ]
                            
                            for selector in website_selectors:
                                try:
                                    website_elem = element.find_element("xpath", selector)
                                    website = website_elem.get_attribute('href')
                                    if website:
                                        business['website'] = website
                                        break
                                except:
                                    continue
                            
                            # Extract business type
                            type_selectors = [
                                ".//div[contains(@class, 'category')]",
                                ".//span[contains(@class, 'category')]"
                            ]
                            
                            for selector in type_selectors:
                                try:
                                    type_elem = element.find_element("xpath", selector)
                                    business_type = type_elem.text.strip()
                                    if business_type:
                                        business['business_type'] = business_type
                                        break
                                except:
                                    continue
                            
                            if 'business_type' not in business and what != "businesses":
                                business['business_type'] = what
                            
                            businesses.append(business)
                            
                        except Exception as e:
                            print(f"Error extracting Thomson Local data with Selenium: {e}")
                except Exception as e:
                    print(f"Error using Selenium for Thomson Local: {e}")
        
        except Exception as e:
            print(f"Error in Thomson Local search: {e}")
        
        print(f"Found {len(businesses)} businesses from Thomson Local")
        return businesses
    
    def _search_192_directory(self, query, limit=20):
        """Search for businesses on 192.com directory"""
        businesses = []
        
        # Parse the query to match the directory's format
        if "in " in query:
            parts = query.split("in ")
            what = parts[0].strip()
            where = parts[1].strip()
        else:
            what = "businesses"
            where = query
        
        # Format for 192.com URL structure
        url = f"https://www.192.com/business/{quote_plus(what)}/{quote_plus(where)}/"
        
        try:
            print(f"Searching 192.com for: {what} in {where}")
            
            # First try direct request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'en-GB,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Referer': 'https://www.192.com/',
                'Connection': 'keep-alive'
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find business listings
                business_elements = soup.select('.business-listing, .business-result, .listing-item')
                print(f"Found {len(business_elements)} 192.com elements with direct request")
                
                for element in business_elements[:limit]:
                    try:
                        # Extract business name
                        name_elem = element.select_one('h2, h3, .business-name')
                        if not name_elem:
                            continue
                            
                        name = name_elem.text.strip()
                        
                        business = {'name': name, 'source': '192.com'}
                        
                        # Extract address
                        address_elem = element.select_one('.address, .business-address')
                        if address_elem:
                            business['address'] = address_elem.text.strip()
                        
                        # Extract phone
                        phone_elem = element.select_one('.phone, .telephone, .contact-number')
                        if phone_elem:
                            business['phone'] = phone_elem.text.strip()
                        
                        # Extract website
                        website_elem = element.select_one('a.website, a.url')
                        if website_elem and 'href' in website_elem.attrs:
                            business['website'] = website_elem['href']
                        
                        # Extract business type
                        type_elem = element.select_one('.category, .business-category')
                        if type_elem:
                            business['business_type'] = type_elem.text.strip()
                        elif what != "businesses":
                            business['business_type'] = what
                        
                        businesses.append(business)
                        
                    except Exception as e:
                        print(f"Error extracting 192.com data: {e}")
            
            # If direct request didn't work and Selenium is available, try that
            if not businesses and self.use_selenium and self.driver:
                try:
                    self.driver.get(url)
                    time.sleep(3)
                    
                    # Try an alternative URL format if the first one didn't work
                    if "No results found" in self.driver.page_source:
                        alt_url = f"https://www.192.com/business/search/{quote_plus(what)}/?location={quote_plus(where)}"
                        self.driver.get(alt_url)
                        time.sleep(3)
                    
                    # Try to find business listings
                    business_elements = []
                    selectors = [
                        "//div[contains(@class, 'business-listing')]",
                        "//div[contains(@class, 'business-result')]",
                        "//div[contains(@class, 'listing-item')]",
                        "//div[contains(@class, 'SearchResult')]"
                    ]
                    
                    for selector in selectors:
                        try:
                            found_elements = self.driver.find_elements("xpath", selector)
                            if found_elements:
                                business_elements = found_elements
                                print(f"Found {len(business_elements)} 192.com elements with Selenium selector: {selector}")
                                break
                        except Exception as e:
                            print(f"Selector {selector} failed: {e}")
                    
                    for element in business_elements[:limit]:
                        try:
                            # Extract business name
                            name_selectors = [
                                ".//h2",
                                ".//h3",
                                ".//div[contains(@class, 'business-name')]",
                                ".//div[contains(@class, 'Title')]"
                            ]
                            
                            name = None
                            for selector in name_selectors:
                                try:
                                    name_elem = element.find_element("xpath", selector)
                                    name = name_elem.text.strip()
                                    if name:
                                        break
                                except:
                                    continue
                            
                            if not name:
                                continue
                            
                            business = {'name': name, 'source': '192.com (Selenium)'}
                            print(f"Found 192.com business: {name}")
                            
                            # Try clicking on the element for more details
                            try:
                                element.click()
                                time.sleep(2)
                                
                                # Extract details from the opened modal or detail page
                                detail_elements = self.driver.find_elements("xpath", "//div[contains(@class, 'detail') or contains(@class, 'Detail')]")
                                if detail_elements:
                                    detail_text = ' '.join([e.text for e in detail_elements if e.text])
                                    
                                    # Extract address
                                    address_match = re.search(r'(?:Address|Location):\s*([^•]+)', detail_text)
                                    if address_match:
                                        business['address'] = address_match.group(1).strip()
                                    
                                    # Extract phone
                                    phone_match = re.search(r'(?:Phone|Tel):\s*([0-9\s+]+)', detail_text)
                                    if phone_match:
                                        business['phone'] = phone_match.group(1).strip()
                                
                                # Try to find website
                                website_elements = self.driver.find_elements("xpath", "//a[contains(@href, 'http') and (contains(text(), 'website') or contains(@class, 'website'))]")
                                if website_elements:
                                    business['website'] = website_elements[0].get_attribute('href')
                                
                                # Go back or close detail view
                                back_buttons = self.driver.find_elements("xpath", "//button[contains(@class, 'close') or contains(text(), 'Back')]")
                                if back_buttons:
                                    back_buttons[0].click()
                                    time.sleep(1)
                                else:
                                    self.driver.get(url)
                                    time.sleep(2)
                            except Exception as e:
                                print(f"Error getting 192.com details: {e}")
                                # Try to recover
                                try:
                                    self.driver.get(url)
                                    time.sleep(2)
                                except:
                                    pass
                            
                            # If we couldn't get the address from the detail view, try from the list view
                            if 'address' not in business:
                                address_selectors = [
                                    ".//div[contains(@class, 'address')]",
                                    ".//span[contains(@class, 'address')]",
                                    ".//div[contains(@class, 'location')]"
                                ]
                                
                                for selector in address_selectors:
                                    try:
                                        address_elem = element.find_element("xpath", selector)
                                        address = address_elem.text.strip()
                                        if address:
                                            business['address'] = address
                                            break
                                    except:
                                        continue
                            
                            # If we couldn't get the phone from the detail view, try from the list view
                            if 'phone' not in business:
                                phone_selectors = [
                                    ".//div[contains(@class, 'phone')]",
                                    ".//span[contains(@class, 'phone')]",
                                    ".//div[contains(@class, 'telephone')]"
                                ]
                                
                                for selector in phone_selectors:
                                    try:
                                        phone_elem = element.find_element("xpath", selector)
                                        phone = phone_elem.text.strip()
                                        if phone:
                                            business['phone'] = phone
                                            break
                                    except:
                                        continue
                            
                            # Extract business type
                            if 'business_type' not in business:
                                type_selectors = [
                                    ".//div[contains(@class, 'category')]",
                                    ".//span[contains(@class, 'category')]",
                                    ".//div[contains(@class, 'business-type')]"
                                ]
                                
                                for selector in type_selectors:
                                    try:
                                        type_elem = element.find_element("xpath", selector)
                                        business_type = type_elem.text.strip()
                                        if business_type:
                                            business['business_type'] = business_type
                                            break
                                    except:
                                        continue
                            
                            if 'business_type' not in business and what != "businesses":
                                business['business_type'] = what
                            
                            businesses.append(business)
                            
                        except Exception as e:
                            print(f"Error extracting 192.com data with Selenium: {e}")
                except Exception as e:
                    print(f"Error using Selenium for 192.com: {e}")
        
        except Exception as e:
            print(f"Error in 192.com search: {e}")
        
        print(f"Found {len(businesses)} businesses from 192.com")
        return businesses
    
    def _search_google_business(self, query, limit=20):
        """Search for businesses using Google Business Profiles"""
        businesses = []
        
        try:
            # Format the query for URL
            search_query = f"{query} business profiles"
            url = f"https://www.google.com/search?q={quote_plus(search_query)}"
            
            if self.use_selenium and self.driver:
                # Use Selenium for Google Business
                print(f"Searching Google Business Profiles for: {search_query}")
                self.driver.get(url)
                
                # Wait for results to load
                time.sleep(3)
                
                # Look for business profile sections
                business_elements = []
                selectors = [
                    "//div[contains(@class, 'kp-wholepage')]//div[contains(@class, 'JX') or contains(@class, 'nGydZ')]",  # Fixed XPath syntax
                    "//div[contains(@class, 'commercial-unit-desktop-top')]",
                    "//div[contains(@class, 'PZPZlf')]",
                    "//div[contains(@class, 'Gx5Zad')]//div[contains(@class, 'fP1Qef')]",
                    "//div[@role='main']//div[contains(@class, 'g')]"
                ]
                
                for selector in selectors:
                    try:
                        elements = self.driver.find_elements("xpath", selector)
                        if elements:
                            business_elements = elements
                            print(f"Found {len(elements)} business profile elements with selector: {selector}")
                            break
                    except Exception as e:
                        print(f"Selector {selector} failed: {e}")
                
                # Process the business elements
                for i, element in enumerate(business_elements[:limit]):
                    try:
                        # Get the element's text content
                        text_content = element.text
                        
                        # Skip if no text
                        if not text_content:
                            continue
                        
                        # Parse the text content to extract business information
                        lines = text_content.split('\n')
                        
                        # First line is usually the business name
                        if not lines:
                            continue
                            
                        name = lines[0]
                        business = {'name': name, 'source': 'Google Business'}
                        print(f"Found business: {name}")
                        
                        # Extract address, phone, and business type from the text content
                        for line in lines[1:]:
                            # Skip short lines
                            if len(line) < 3:
                                continue
                                
                            # Look for phone numbers
                            if re.search(r'^\+?[\d\s\(\)-]{7,}$', line):
                                business['phone'] = line
                                continue
                            
                            # Look for addresses (contains street, road, etc.)
                            address_words = ['street', 'road', 'avenue', 'lane', 'drive', 'way', 'place', 'boulevard', 'terrace']
                            if any(word in line.lower() for word in address_words) or re.search(r'\b[A-Z]{1,2}[0-9][0-9A-Z]?\s?[0-9][A-Z]{2}\b', line):
                                business['address'] = line
                                continue
                            
                            # Look for business types
                            business_type_words = ['restaurant', 'shop', 'store', 'salon', 'service', 'company', 'business', 'agency', 'firm']
                            if any(word in line.lower() for word in business_type_words) and len(line) < 30:
                                business['business_type'] = line
                                continue
                        
                        # Try to find a website link
                        try:
                            website_elem = element.find_element("xpath", ".//a[contains(@href, 'http') and not(contains(@href, 'google.com'))]")
                            website = website_elem.get_attribute('href')
                            if website:
                                business['website'] = website
                        except:
                            pass
                        
                        # Add business type from query if not found
                        if 'business_type' not in business and "in " in query:
                            business_type = query.split("in ")[0].strip()
                            if business_type != "businesses":
                                business['business_type'] = business_type
                        
                        businesses.append(business)
                        
                    except Exception as e:
                        print(f"Error extracting Google Business data: {e}")
            else:
                print("Selenium not available for Google Business, using fallback method")
                
                # Fallback to using web_search directly
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept-Language': 'en-GB,en;q=0.9',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                    'Referer': 'https://www.google.com/'
                }
                
                response = requests.get(url, headers=headers)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Look for business listings
                    business_elements = soup.select('.g, .xpd, .kp-wholepage, .mnr-c')
                    
                    for element in business_elements[:limit]:
                        try:
                            # Extract business name
                            name_elem = element.select_one('h3, .dyjrff, .qrShPb')
                            if not name_elem:
                                continue
                                
                            name = name_elem.text.strip()
                            
                            business = {'name': name, 'source': 'Google Business'}
                            
                            # Extract business information from the snippet
                            snippet = element.select_one('.yXK7lf, .MUxGbd, .VwiC3b, .U3A9Ac')
                            if snippet:
                                snippet_text = snippet.text
                                
                                # Try to extract address
                                address_match = re.search(r'[0-9].*?(?:Street|Road|Avenue|Lane|Drive|Way|Place|Boulevard|Terrace),?.*?(?:[A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2})?', snippet_text)
                                if address_match:
                                    business['address'] = address_match.group(0)
                                
                                # Try to extract phone
                                phone_match = re.search(r'(?:0|\+44)[0-9 ]{9,13}', snippet_text)
                                if phone_match:
                                    business['phone'] = phone_match.group(0)
                            
                            # Extract website
                            link_elem = element.select_one('a')
                            if link_elem and 'href' in link_elem.attrs:
                                href = link_elem['href']
                                if href.startswith('http') and not 'google.com' in href:
                                    business['website'] = href
                            
                            # Add business type from query
                            if "in " in query:
                                business_type = query.split("in ")[0].strip()
                                if business_type != "businesses":
                                    business['business_type'] = business_type
                            
                            businesses.append(business)
                            
                        except Exception as e:
                            print(f"Error extracting Google Business data: {e}")
        
        except Exception as e:
            print(f"Error in Google Business search: {e}")
        
        print(f"Found {len(businesses)} businesses from Google Business")
        return businesses
    
    def _search_google(self, query, limit=20):
        """Fallback to regular Google search"""
        businesses = []
        
        # Format the query
        search_query = f"{query} business contact"
        search_url = f"https://www.google.com/search?q={quote_plus(search_query)}"
        
        try:
            print(f"Searching Google for: {search_query}")
            
            if self.use_selenium and self.driver:
                self.driver.get(search_url)
                time.sleep(3)
                
                # Try to find local business results
                local_business_elements = []
                selectors = [
                    "//div[contains(@class, 'g')]",
                    "//div[contains(@class, 'Gx5Zad')]",
                    "//div[contains(@class, 'tF2Cxc')]",
                    "//div[contains(@class, 'lEXIrb')]",
                    "//div[contains(@class, 'kp-wholepage')]/div"
                ]
                
                for selector in selectors:
                    try:
                        found_elements = self.driver.find_elements("xpath", selector)
                        if found_elements:
                            local_business_elements = found_elements
                            print(f"Found {len(local_business_elements)} elements with selector: {selector}")
                            break
                    except Exception as e:
                        print(f"Selector {selector} failed: {e}")
                
                for i, element in enumerate(local_business_elements[:limit]):
                    try:
                        # Try different selectors for name
                        name_selectors = [
                            ".//h3",
                            ".//div[@role='heading']",
                            ".//div[contains(@class, 'mCBkyc')]"
                        ]
                        
                        name = None
                        for selector in name_selectors:
                            try:
                                name_elem = element.find_element("xpath", selector)
                                name = name_elem.text.strip()
                                if name:
                                    break
                            except (AttributeError, ValueError, IndexError):
                                continue
                        
                        if not name:
                            continue
                        
                        business = {'name': name, 'source': 'Google Search'}
                        print(f"Found business: {name}")
                        
                        # Extract all text content from the element
                        element_text = element.text
                        
                        # Print element text for debugging
                        print(f"Element text: {element_text[:200]}...")
                        
                        # Extract potential address using regex patterns
                        address_patterns = [
                            r'[0-9]+\s+[A-Za-z\s]+(?:Road|Street|Avenue|Lane|Drive|Way|Place|Hill|Broadway|Court)\b[^,\.\n]*',
                            r'[A-Za-z\s]+(?:Road|Street|Avenue|Lane|Drive|Way|Place|Hill|Broadway|Court)[^,\.\n]*',
                            r'[0-9]+\s+[A-Za-z\s]+,\s+[A-Za-z\s]+,\s+[A-Z]{1,2}[0-9]'
                        ]
                        
                        for pattern in address_patterns:
                            address_match = re.search(pattern, element_text)
                            if address_match:
                                address = address_match.group(0).strip()
                                if len(address) > 5:  # Avoid too short matches
                                    business['address'] = address
                                    break
                        
                        # Extract potential UK postcode
                        postcode_match = re.search(r'[A-Z]{1,2}[0-9][0-9A-Z]?\s?[0-9][A-Z]{2}', element_text)
                        if postcode_match and 'address' in business:
                            postcode = postcode_match.group(0)
                            if postcode not in business['address']:
                                business['address'] += ", " + postcode
                        
                        # Extract potential phone using regex patterns
                        phone_patterns = [
                            r'(?:Tel|Phone|Contact)(?:ephone)?:?\s*(\+?(?:44)?[0-9\s\(\)-]{9,})',
                            r'(?:0|\+44)[0-9\s\(\)-]{9,}',
                            r'[0-9]{3,5}\s*[0-9]{3,4}\s*[0-9]{3,4}'
                        ]
                        
                        for pattern in phone_patterns:
                            phone_match = re.search(pattern, element_text)
                            if phone_match:
                                phone = phone_match.group(0).strip()
                                if 'Tel:' in phone or 'Phone:' in phone:
                                    phone = phone.split(':', 1)[1].strip()
                                business['phone'] = phone
                                break
                        
                        # Try to find website
                        link_selectors = [
                            ".//a[contains(@href, 'http')]",
                            ".//a[contains(@href, '://')]",
                            ".//a"
                        ]
                        
                        for selector in link_selectors:
                            try:
                                link_elem = element.find_element("xpath", selector)
                                href = link_elem.get_attribute('href')
                                if href and 'google.com' not in href and 'googleusercontent.com' not in href:
                                    business['website'] = href
                                    break
                            except:
                                continue
                        
                        # Try to extract business type
                        if "in " in query:
                            business_type = query.split("in ")[0].strip()
                            if business_type != "businesses":
                                business['business_type'] = business_type
                        else:
                            # Try to infer business type from element text
                            business_types = ['restaurant', 'shop', 'store', 'hotel', 'salon', 'café', 'cafe', 'pub', 'bar', 'clinic', 'agency']
                            for btype in business_types:
                                if btype in element_text.lower():
                                    business['business_type'] = btype.capitalize()
                                    break
                        
                        businesses.append(business)
                        
                    except Exception as e:
                        print(f"Error extracting Google business data: {e}")
            
            else:
                # Fallback to requests
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept-Language': 'en-GB,en;q=0.9',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                    'Referer': 'https://www.google.com/'
                }
                
                response = requests.get(search_url, headers=headers)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Look for business listings in search results
                    business_elements = soup.select('.g, .Gx5Zad')
                    
                    for element in business_elements[:limit]:
                        try:
                            name_elem = element.select_one('h3')
                            if not name_elem:
                                continue
                                
                            name = name_elem.text.strip()
                            
                            business = {'name': name, 'source': 'Google Search'}
                            
                            # Try to find website
                            link_elem = element.select_one('a')
                            if link_elem and 'href' in link_elem.attrs:
                                href = link_elem['href']
                                if href.startswith('http') and not 'google.com' in href:
                                    business['website'] = href
                            
                            # Try to find address and phone
                            snippet = element.select_one('.VwiC3b, .MUxGbd')
                            if snippet:
                                text = snippet.text
                                
                                # Look for potential address
                                address_match = re.search(r'[0-9].*?(?:Road|Street|Avenue|Lane|Drive|Way|Place|Hill|Broadway|Court|Gardens|Park),?.*?[A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2}', text)
                                if address_match:
                                    business['address'] = address_match.group(0)
                                
                                # Look for potential phone number
                                phone_match = re.search(r'(?:0|\+44)[0-9 ]{9,13}', text)
                                if phone_match:
                                    business['phone'] = phone_match.group(0)
                            
                            # Add business type from query
                            if "in " in query:
                                business_type = query.split("in ")[0].strip()
                                if business_type != "businesses":
                                    business['business_type'] = business_type
                            
                            businesses.append(business)
                        except Exception as e:
                            print(f"Error extracting business data: {e}")
                
        except Exception as e:
            print(f"Error in Google search: {e}")
        
        print(f"Found {len(businesses)} businesses from Google")
        return businesses
        
    def _search_uk_local_directories(self, query, limit=20):
        """Search UK local business directories"""
        businesses = []
        
        # Parse the query
        if "in " in query:
            parts = query.split("in ")
            what = parts[0].strip()
            where = parts[1].strip()
        else:
            what = "businesses"
            where = query
        
        # List of UK local directories to try
        directories = [
            f"https://www.thomsonlocal.com/search/{quote_plus(what)}/{quote_plus(where)}",
            f"https://www.scoot.co.uk/find/{quote_plus(what)}-in-{quote_plus(where)}",
            f"https://www.locallife.co.uk/search/{quote_plus(where)}/{quote_plus(what)}.asp",
            f"https://www.cylex-uk.co.uk/company/{quote_plus(what)}_{quote_plus(where)}.html"
        ]
        
        for directory_url in directories:
            try:
                print(f"Searching UK local directory: {directory_url}")
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept-Language': 'en-GB,en;q=0.9',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                    'Referer': 'https://www.google.com/',
                    'DNT': '1'
                }
                
                response = requests.get(directory_url, headers=headers)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Common selectors for business listings across different directories
                    selectors = [
                        '.listing', '.business', '.result', '.company-info',
                        'article', '.business-listing', '.searchresult'
                    ]
                    
                    # Find business elements
                    business_elements = []
                    for selector in selectors:
                        business_elements = soup.select(selector)
                        if business_elements:
                            print(f"Found {len(business_elements)} elements with selector '{selector}'")
                            break
                    
                    # Process found elements
                    for element in business_elements[:limit]:
                        try:
                            # Extract business name - common selectors across directories
                            name_elem = element.select_one('h2, h3, h4, .name, .title, .business-name')
                            if not name_elem:
                                continue
                                
                            name = name_elem.text.strip()
                            if not name:
                                continue
                            
                            business = {'name': name, 'source': 'UK Local Directory'}
                            
                            # Extract address
                            address_elem = element.select_one('.address, .location, [itemprop="address"]')
                            if address_elem:
                                business['address'] = address_elem.text.strip()
                            
                            # Extract phone
                            phone_elem = element.select_one('.phone, .tel, .telephone, [itemprop="telephone"]')
                            if phone_elem:
                                business['phone'] = phone_elem.text.strip()
                            
                            # Extract website
                            website_elem = element.select_one('a.website, [itemprop="url"], a[href*="http"]')
                            if website_elem and 'href' in website_elem.attrs:
                                website_url = website_elem['href']
                                # Skip directory internal links
                                if not any(domain in website_url for domain in ['thomsonlocal.com', 'scoot.co.uk', 'locallife.co.uk', 'cylex-uk.co.uk']):
                                    business['website'] = website_url
                            
                            # Extract business type
                            type_elem = element.select_one('.category, [itemprop="category"]')
                            if type_elem:
                                business['business_type'] = type_elem.text.strip()
                            elif what != "businesses":
                                business['business_type'] = what
                            
                            businesses.append(business)
                            
                        except Exception as e:
                            print(f"Error extracting business data: {e}")
                    
                    # If we found some businesses, don't try other directories
                    if businesses:
                        break
            
            except Exception as e:
                print(f"Error searching directory {directory_url}: {e}")
        
        print(f"Found {len(businesses)} businesses from UK local directories")
        return businesses
    
    def _search_scoot_uk(self, query, limit=20):
        """Search for businesses on Scoot UK directory"""
        businesses = []
        
        # Parse the query to match the directory's format
        if "in " in query:
            parts = query.split("in ")
            what = parts[0].strip()
            where = parts[1].strip()
        else:
            what = "businesses"
            where = query
            
        # Format for Scoot URL structure
        url = f"https://www.scoot.co.uk/find/{quote_plus(what)}-in-{quote_plus(where)}"
        
        try:
            print(f"Searching Scoot.co.uk for: {what} in {where}")
            
            # Try direct request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'en-GB,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Referer': 'https://www.scoot.co.uk/',
                'Connection': 'keep-alive'
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find business listings
                selectors = ['.business-listing', '.company-info', '.search-item', '.result-item']
                
                business_elements = []
                for selector in selectors:
                    elements = soup.select(selector)
                    if elements:
                        business_elements = elements
                        print(f"Found {len(elements)} Scoot elements with selector: {selector}")
                        break
                
                # Process found elements
                for element in business_elements[:limit]:
                    try:
                        # Extract business name
                        name_elem = element.select_one('h2, h3, .business-name, .company-name')
                        if not name_elem:
                            continue
                            
                        name = name_elem.text.strip()
                        if not name:
                            continue
                        
                        business = {'name': name, 'source': 'Scoot UK'}
                        
                        # Extract address
                        address_elem = element.select_one('.address, .location, .company-address')
                        if address_elem:
                            business['address'] = address_elem.text.strip()
                        
                        # Extract phone
                        phone_elem = element.select_one('.phone, .tel, .telephone')
                        if phone_elem:
                            business['phone'] = phone_elem.text.strip()
                        
                        # Extract website
                        website_elem = element.select_one('a.website, a.url, a[href*="http"]')
                        if website_elem and 'href' in website_elem.attrs:
                            website_url = website_elem['href']
                            # Skip scoot internal links
                            if 'scoot.co.uk' not in website_url:
                                business['website'] = website_url
                        
                        # Extract business type
                        type_elem = element.select_one('.category, .business-category')
                        if type_elem:
                            business['business_type'] = type_elem.text.strip()
                        elif what != "businesses":
                            business['business_type'] = what
                        
                        businesses.append(business)
                        
                    except Exception as e:
                        print(f"Error extracting Scoot data: {e}")
            
            # If direct request didn't work and Selenium is available, try that
            if not businesses and self.use_selenium and self.driver:
                try:
                    self.driver.get(url)
                    time.sleep(3)
                    
                    # Find business listings
                    business_elements = []
                    selectors = [
                        "//div[contains(@class, 'business-listing')]",
                        "//div[contains(@class, 'company-info')]",
                        "//div[contains(@class, 'search-item')]"
                    ]
                    
                    for selector in selectors:
                        try:
                            found_elements = self.driver.find_elements("xpath", selector)
                            if found_elements:
                                business_elements = found_elements
                                print(f"Found {len(business_elements)} Scoot elements with Selenium selector: {selector}")
                                break
                        except Exception as e:
                            print(f"Selector {selector} failed: {e}")
                    
                    # Process found elements
                    for element in business_elements[:limit]:
                        try:
                            # Extract business name
                            name_selectors = [
                                ".//h2",
                                ".//h3",
                                ".//div[contains(@class, 'business-name')]",
                                ".//div[contains(@class, 'company-name')]"
                            ]
                            
                            name = None
                            for selector in name_selectors:
                                try:
                                    name_elem = element.find_element("xpath", selector)
                                    name = name_elem.text.strip()
                                    if name:
                                        break
                                except:
                                    continue
                            
                            if not name:
                                continue
                            
                            business = {'name': name, 'source': 'Scoot UK (Selenium)'}
                            print(f"Found Scoot business: {name}")
                            
                            # Extract address
                            address_selectors = [
                                ".//div[contains(@class, 'address')]",
                                ".//div[contains(@class, 'location')]",
                                ".//div[contains(@class, 'company-address')]"
                            ]
                            
                            for selector in address_selectors:
                                try:
                                    address_elem = element.find_element("xpath", selector)
                                    address = address_elem.text.strip()
                                    if address:
                                        business['address'] = address
                                        break
                                except:
                                    continue
                            
                            # Extract phone
                            phone_selectors = [
                                ".//div[contains(@class, 'phone')]",
                                ".//div[contains(@class, 'tel')]",
                                ".//div[contains(@class, 'telephone')]"
                            ]
                            
                            for selector in phone_selectors:
                                try:
                                    phone_elem = element.find_element("xpath", selector)
                                    phone = phone_elem.text.strip()
                                    if phone:
                                        business['phone'] = phone
                                        break
                                except:
                                    continue
                            
                            # Extract website
                            website_selectors = [
                                ".//a[contains(@class, 'website')]",
                                ".//a[contains(@class, 'url')]",
                                ".//a[contains(@href, 'http')]"
                            ]
                            
                            for selector in website_selectors:
                                try:
                                    website_elem = element.find_element("xpath", selector)
                                    website = website_elem.get_attribute('href')
                                    if website and 'scoot.co.uk' not in website:
                                        business['website'] = website
                                        break
                                except:
                                    continue
                            
                            # Extract business type
                            type_selectors = [
                                ".//div[contains(@class, 'category')]",
                                ".//div[contains(@class, 'business-category')]"
                            ]
                            
                            for selector in type_selectors:
                                try:
                                    type_elem = element.find_element("xpath", selector)
                                    business_type = type_elem.text.strip()
                                    if business_type:
                                        business['business_type'] = business_type
                                        break
                                except:
                                    continue
                            
                            if 'business_type' not in business and what != "businesses":
                                business['business_type'] = what
                            
                            businesses.append(business)
                            
                        except Exception as e:
                            print(f"Error extracting Scoot data with Selenium: {e}")
                            
                except Exception as e:
                    print(f"Error using Selenium for Scoot UK: {e}")
            
        except Exception as e:
            print(f"Error in Scoot UK search: {e}")
            
        print(f"Found {len(businesses)} businesses from Scoot UK")
        return businesses
    
    def close(self):
        """Clean up resources with improved error handling"""
        if self.use_selenium and self.driver:
            try:
                # Close all windows first
                for handle in self.driver.window_handles:
                    try:
                        self.driver.switch_to.window(handle)
                        self.driver.close()
                    except:
                        pass
                
                # Quit the driver
                self.driver.quit()
                self.driver = None
                logging.info("Selenium WebDriver closed successfully")
                
            except Exception as e:
                logging.error(f"Error closing Selenium WebDriver: {e}")
                # Force cleanup
                try:
                    if self.driver:
                        self.driver.quit()
                        self.driver = None
                except:
                    pass
        
        # Close requests session
        try:
            if hasattr(self, 'session') and self.session:
                self.session.close()
                logging.info("Requests session closed")
        except Exception as e:
            logging.error(f"Error closing requests session: {e}")