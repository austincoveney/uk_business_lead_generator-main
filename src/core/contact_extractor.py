"""Enhanced contact extraction module for comprehensive business research"""

import re
import time
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import logging


class ContactExtractor:
    """Extract comprehensive contact information from business websites"""
    
    def __init__(self, session=None):
        self.session = session or requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.9',
            'DNT': '1'
        })
        
        # Common contact page patterns
        self.contact_page_patterns = [
            '/contact', '/contact-us', '/contact.html', '/contact.php',
            '/about', '/about-us', '/about.html',
            '/get-in-touch', '/reach-us', '/find-us'
        ]
        
        # Social media patterns
        self.social_patterns = {
            'facebook': r'(?:https?://)?(?:www\.)?facebook\.com/[\w\.-]+',
            'twitter': r'(?:https?://)?(?:www\.)?twitter\.com/[\w\.-]+',
            'linkedin': r'(?:https?://)?(?:www\.)?linkedin\.com/(?:company|in)/[\w\.-]+',
            'instagram': r'(?:https?://)?(?:www\.)?instagram\.com/[\w\.-]+',
            'youtube': r'(?:https?://)?(?:www\.)?youtube\.com/(?:channel|user|c)/[\w\.-]+'
        }
        
        # Email patterns
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        # Phone patterns (UK focused)
        self.phone_patterns = [
            r'\b(?:\+44\s?|0)(?:\d{2}\s?\d{4}\s?\d{4}|\d{3}\s?\d{3}\s?\d{4}|\d{4}\s?\d{6})\b',
            r'\b(?:\+44\s?)?\(?0?\d{2,4}\)?[\s.-]?\d{3,4}[\s.-]?\d{3,4}\b',
            r'\b(?:tel|phone|call)[:.]?\s*(?:\+44\s?|0)?\d{2,4}[\s.-]?\d{3,4}[\s.-]?\d{3,4}\b'
        ]
    
    def extract_comprehensive_contacts(self, business_data):
        """Extract comprehensive contact information for a business"""
        enhanced_data = business_data.copy()
        
        if not business_data.get('website'):
            return enhanced_data
        
        try:
            # Extract from main website
            main_contacts = self._extract_from_website(business_data['website'])
            enhanced_data.update(main_contacts)
            
            # Try to find and extract from contact pages
            contact_page_data = self._extract_from_contact_pages(business_data['website'])
            enhanced_data.update(contact_page_data)
            
            # Extract social media profiles
            social_profiles = self._extract_social_media(business_data['website'])
            if social_profiles:
                enhanced_data['social_media'] = social_profiles
            
            # Extract additional business information
            business_info = self._extract_business_info(business_data['website'])
            enhanced_data.update(business_info)
            
            # Calculate contact completeness score
            enhanced_data['contact_score'] = self._calculate_contact_score(enhanced_data)
            
        except Exception as e:
            logging.error(f"Error extracting contacts for {business_data.get('name', 'Unknown')}: {e}")
        
        return enhanced_data
    
    def _extract_from_website(self, url):
        """Extract contact information from main website"""
        contacts = {}
        
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return contacts
            
            soup = BeautifulSoup(response.text, 'html.parser')
            text_content = soup.get_text()
            
            # Extract emails
            emails = self._extract_emails(text_content, soup)
            if emails:
                contacts['emails'] = emails
                contacts['primary_email'] = emails[0]  # First email as primary
            
            # Extract phone numbers
            phones = self._extract_phones(text_content, soup)
            if phones:
                contacts['phone_numbers'] = phones
                if not contacts.get('phone'):  # If no phone from scraper
                    contacts['phone'] = phones[0]
            
            # Extract address information
            address_info = self._extract_address_info(soup)
            if address_info:
                contacts.update(address_info)
            
            # Extract opening hours
            hours = self._extract_opening_hours(soup)
            if hours:
                contacts['opening_hours'] = hours
            
        except Exception as e:
            logging.error(f"Error extracting from website {url}: {e}")
        
        return contacts
    
    def _extract_from_contact_pages(self, base_url):
        """Extract information from dedicated contact pages"""
        contacts = {}
        
        for pattern in self.contact_page_patterns:
            try:
                contact_url = urljoin(base_url, pattern)
                response = self.session.get(contact_url, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    text_content = soup.get_text()
                    
                    # Extract additional emails and phones
                    emails = self._extract_emails(text_content, soup)
                    phones = self._extract_phones(text_content, soup)
                    
                    if emails:
                        existing_emails = contacts.get('emails', [])
                        contacts['emails'] = list(set(existing_emails + emails))
                    
                    if phones:
                        existing_phones = contacts.get('phone_numbers', [])
                        contacts['phone_numbers'] = list(set(existing_phones + phones))
                    
                    # Extract contact form information
                    contact_form = self._extract_contact_form_info(soup)
                    if contact_form:
                        contacts['contact_form'] = contact_form
                    
                    break  # Stop after finding first working contact page
                    
            except Exception as e:
                continue
        
        return contacts
    
    def _extract_emails(self, text_content, soup):
        """Extract email addresses from content"""
        emails = []
        
        # Find emails in text content
        email_matches = re.findall(self.email_pattern, text_content, re.IGNORECASE)
        emails.extend(email_matches)
        
        # Find emails in mailto links
        mailto_links = soup.find_all('a', href=re.compile(r'^mailto:'))
        for link in mailto_links:
            email = link['href'].replace('mailto:', '').split('?')[0]
            emails.append(email)
        
        # Clean and filter emails
        cleaned_emails = []
        for email in emails:
            email = email.lower().strip()
            # Filter out common non-business emails
            if not any(skip in email for skip in ['noreply', 'no-reply', 'donotreply', 'example.com']):
                if email not in cleaned_emails:
                    cleaned_emails.append(email)
        
        return cleaned_emails[:5]  # Limit to 5 emails
    
    def _extract_phones(self, text_content, soup):
        """Extract phone numbers from content"""
        phones = []
        
        # Try each phone pattern
        for pattern in self.phone_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            phones.extend(matches)
        
        # Find phones in tel links
        tel_links = soup.find_all('a', href=re.compile(r'^tel:'))
        for link in tel_links:
            phone = link['href'].replace('tel:', '').strip()
            phones.append(phone)
        
        # Clean and normalize phone numbers
        cleaned_phones = []
        for phone in phones:
            # Remove common formatting
            cleaned = re.sub(r'[^\d+]', '', phone)
            if len(cleaned) >= 10:  # Minimum phone length
                if cleaned not in cleaned_phones:
                    cleaned_phones.append(phone.strip())  # Keep original formatting
        
        return cleaned_phones[:3]  # Limit to 3 phone numbers
    
    def _extract_social_media(self, url):
        """Extract social media profiles"""
        social_profiles = {}
        
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return social_profiles
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find social media links
            for platform, pattern in self.social_patterns.items():
                # Look in href attributes
                links = soup.find_all('a', href=re.compile(pattern, re.IGNORECASE))
                for link in links:
                    href = link.get('href', '')
                    if href and platform not in social_profiles:
                        social_profiles[platform] = href
                        break
                
                # Also search in text content
                if platform not in social_profiles:
                    text_matches = re.findall(pattern, soup.get_text(), re.IGNORECASE)
                    if text_matches:
                        social_profiles[platform] = text_matches[0]
        
        except Exception as e:
            logging.error(f"Error extracting social media from {url}: {e}")
        
        return social_profiles
    
    def _extract_address_info(self, soup):
        """Extract detailed address information"""
        address_info = {}
        
        # Look for structured address data
        address_selectors = [
            '[itemtype*="PostalAddress"]',
            '.address', '.contact-address', '.location',
            '[class*="address"]', '[id*="address"]'
        ]
        
        for selector in address_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if len(text) > 10 and ',' in text:  # Basic address validation
                    # Try to extract postcode
                    postcode_match = re.search(r'[A-Z]{1,2}[0-9][0-9A-Z]?\s?[0-9][A-Z]{2}', text.upper())
                    if postcode_match:
                        address_info['full_address'] = text
                        address_info['postcode'] = postcode_match.group(0)
                        break
        
        return address_info
    
    def _extract_opening_hours(self, soup):
        """Extract opening hours information"""
        hours_patterns = [
            r'(?:open|opening|hours?)[:.]?\s*([^\n]{20,100})',
            r'(?:mon|tue|wed|thu|fri|sat|sun)[a-z]*[\s:-]+\d{1,2}[:\.]?\d{0,2}\s*(?:am|pm)?[^\n]{0,50}',
        ]
        
        # Look for opening hours in specific elements
        hours_selectors = [
            '.hours', '.opening-hours', '.business-hours',
            '[class*="hours"]', '[id*="hours"]'
        ]
        
        for selector in hours_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if any(day in text.lower() for day in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']):
                    return text
        
        # Search in general text content
        text_content = soup.get_text()
        for pattern in hours_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE | re.MULTILINE)
            if matches:
                return matches[0]
        
        return None
    
    def _extract_contact_form_info(self, soup):
        """Extract contact form information"""
        forms = soup.find_all('form')
        
        for form in forms:
            # Check if this looks like a contact form
            form_text = form.get_text().lower()
            if any(keyword in form_text for keyword in ['contact', 'message', 'enquiry', 'inquiry']):
                action = form.get('action', '')
                method = form.get('method', 'GET')
                
                # Extract form fields
                inputs = form.find_all(['input', 'textarea', 'select'])
                fields = []
                for inp in inputs:
                    field_type = inp.get('type', inp.name)
                    field_name = inp.get('name', inp.get('id', ''))
                    if field_name:
                        fields.append({'type': field_type, 'name': field_name})
                
                return {
                    'action': action,
                    'method': method,
                    'fields': fields
                }
        
        return None
    
    def _extract_business_info(self, url):
        """Extract additional business information"""
        info = {}
        
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return info
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract business description from meta tags
            meta_desc = soup.find('meta', {'name': 'description'})
            if meta_desc:
                info['description'] = meta_desc.get('content', '')[:500]  # Limit length
            
            # Extract business keywords
            meta_keywords = soup.find('meta', {'name': 'keywords'})
            if meta_keywords:
                keywords = meta_keywords.get('content', '').split(',')
                info['keywords'] = [k.strip() for k in keywords[:10]]  # Limit to 10
            
            # Look for company registration number
            text_content = soup.get_text()
            company_patterns = [
                r'company\s+(?:registration\s+)?(?:number|no\.?)[:.]?\s*([0-9]{6,8})',
                r'registered\s+(?:in\s+england\s+)?(?:number|no\.?)[:.]?\s*([0-9]{6,8})',
                r'companies\s+house\s+(?:number|no\.?)[:.]?\s*([0-9]{6,8})'
            ]
            
            for pattern in company_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    info['company_number'] = match.group(1)
                    break
            
            # Extract VAT number
            vat_pattern = r'vat\s+(?:registration\s+)?(?:number|no\.?)[:.]?\s*([0-9]{9,12})'
            vat_match = re.search(vat_pattern, text_content, re.IGNORECASE)
            if vat_match:
                info['vat_number'] = vat_match.group(1)
        
        except Exception as e:
            logging.error(f"Error extracting business info from {url}: {e}")
        
        return info
    
    def _calculate_contact_score(self, business_data):
        """Calculate a contact completeness score (0-100)"""
        score = 0
        
        # Basic contact information (40 points)
        if business_data.get('phone') or business_data.get('phone_numbers'):
            score += 15
        if business_data.get('emails') or business_data.get('primary_email'):
            score += 15
        if business_data.get('address') or business_data.get('full_address'):
            score += 10
        
        # Website and online presence (30 points)
        if business_data.get('website'):
            score += 10
        if business_data.get('social_media'):
            score += 10 + len(business_data['social_media']) * 2  # Bonus for multiple platforms
        
        # Additional business information (30 points)
        if business_data.get('opening_hours'):
            score += 5
        if business_data.get('description'):
            score += 5
        if business_data.get('company_number'):
            score += 10
        if business_data.get('vat_number'):
            score += 5
        if business_data.get('contact_form'):
            score += 5
        
        return min(score, 100)  # Cap at 100