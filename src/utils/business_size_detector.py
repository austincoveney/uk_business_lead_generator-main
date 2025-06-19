"""Business size detection utility"""

import re
from typing import Dict, Optional, Tuple

class BusinessSizeDetector:
    """Utility class for detecting business size from various indicators"""
    
    def __init__(self):
        """Initialize the business size detector"""
        # Keywords that indicate business size
        self.size_keywords = {
            'small': [
                'local', 'family', 'independent', 'sole trader', 'freelance',
                'startup', 'boutique', 'artisan', 'craft', 'home-based',
                'micro', 'small business', 'ltd', 'limited'
            ],
            'medium': [
                'regional', 'growing', 'established', 'professional services',
                'consultancy', 'agency', 'firm', 'group', 'associates',
                'partners', 'medium', 'mid-size'
            ],
            'large': [
                'national', 'nationwide', 'chain', 'franchise', 'corporation',
                'corporate', 'enterprise', 'international', 'global',
                'multinational', 'plc', 'public limited company', 'holdings'
            ],
            'enterprise': [
                'fortune', 'ftse', 'multinational corporation', 'conglomerate',
                'international corporation', 'global enterprise', 'major corporation'
            ]
        }
        
        # Employee count ranges
        self.employee_ranges = {
            'Small': (1, 49),
            'Medium': (50, 249),
            'Large': (250, 999),
            'Enterprise': (1000, float('inf'))
        }
        
        # Website indicators
        self.website_indicators = {
            'small': [
                'wordpress', 'wix', 'squarespace', 'weebly', 'godaddy',
                'basic template', 'simple design'
            ],
            'medium': [
                'professional design', 'custom cms', 'e-commerce',
                'online booking', 'customer portal'
            ],
            'large': [
                'enterprise cms', 'multi-language', 'advanced features',
                'api integration', 'complex functionality'
            ]
        }
    
    def detect_size(self, business_data: Dict) -> Tuple[str, int, str]:
        """
        Detect business size from available data
        
        Args:
            business_data: Dictionary containing business information
            
        Returns:
            Tuple of (size_category, confidence_score, reasoning)
        """
        indicators = []
        total_score = 0
        size_scores = {'Small': 0, 'Medium': 0, 'Large': 0, 'Enterprise': 0}
        
        # Check employee count if available
        employee_count = business_data.get('employee_count', 0)
        if employee_count > 0:
            for size, (min_emp, max_emp) in self.employee_ranges.items():
                if min_emp <= employee_count <= max_emp:
                    size_scores[size] += 50
                    indicators.append(f"Employee count: {employee_count}")
                    break
        
        # Analyze business name
        name = business_data.get('name', '').lower()
        name_score = self._analyze_text_for_size(name)
        for size, score in name_score.items():
            size_scores[size] += score * 0.3
        if any(name_score.values()):
            indicators.append("Business name analysis")
        
        # Analyze business description
        description = business_data.get('description', '').lower()
        if description:
            desc_score = self._analyze_text_for_size(description)
            for size, score in desc_score.items():
                size_scores[size] += score * 0.2
            if any(desc_score.values()):
                indicators.append("Description analysis")
        
        # Analyze website if available
        website = business_data.get('website', '')
        if website:
            website_score = self._analyze_website_indicators(business_data)
            for size, score in website_score.items():
                size_scores[size] += score * 0.15
            if any(website_score.values()):
                indicators.append("Website analysis")
        
        # Check company structure indicators
        company_number = business_data.get('company_number', '')
        vat_number = business_data.get('vat_number', '')
        if company_number or vat_number:
            size_scores['Medium'] += 10
            size_scores['Large'] += 5
            indicators.append("Registered company")
        
        # Analyze address for business park/office indicators
        address = business_data.get('address', '').lower()
        if address:
            address_score = self._analyze_address_indicators(address)
            for size, score in address_score.items():
                size_scores[size] += score * 0.1
            if any(address_score.values()):
                indicators.append("Address analysis")
        
        # Determine final size
        max_score = max(size_scores.values())
        if max_score == 0:
            return 'Unknown', 0, 'Insufficient data for size determination'
        
        predicted_size = max(size_scores, key=size_scores.get)
        confidence = min(int(max_score), 100)
        reasoning = f"Based on: {', '.join(indicators)}"
        
        return predicted_size, confidence, reasoning
    
    def _analyze_text_for_size(self, text: str) -> Dict[str, int]:
        """Analyze text for size-indicating keywords"""
        scores = {'Small': 0, 'Medium': 0, 'Large': 0, 'Enterprise': 0}
        
        for size_category, keywords in self.size_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    if size_category == 'small':
                        scores['Small'] += 10
                    elif size_category == 'medium':
                        scores['Medium'] += 10
                    elif size_category == 'large':
                        scores['Large'] += 10
                    elif size_category == 'enterprise':
                        scores['Enterprise'] += 15
        
        return scores
    
    def _analyze_website_indicators(self, business_data: Dict) -> Dict[str, int]:
        """Analyze website-related indicators for business size"""
        scores = {'Small': 0, 'Medium': 0, 'Large': 0, 'Enterprise': 0}
        
        # Check website performance scores
        performance_score = business_data.get('performance_score', 0)
        seo_score = business_data.get('seo_score', 0)
        
        if performance_score > 80 and seo_score > 80:
            scores['Large'] += 15
            scores['Enterprise'] += 10
        elif performance_score > 60 and seo_score > 60:
            scores['Medium'] += 15
        elif performance_score > 0 or seo_score > 0:
            scores['Small'] += 10
        
        # Check for social media presence
        social_media = business_data.get('social_media', {})
        if isinstance(social_media, dict):
            social_count = len([v for v in social_media.values() if v])
            if social_count >= 3:
                scores['Large'] += 10
            elif social_count >= 2:
                scores['Medium'] += 10
            elif social_count >= 1:
                scores['Small'] += 5
        
        return scores
    
    def _analyze_address_indicators(self, address: str) -> Dict[str, int]:
        """Analyze address for business size indicators"""
        scores = {'Small': 0, 'Medium': 0, 'Large': 0, 'Enterprise': 0}
        
        # Business park/office indicators
        large_business_indicators = [
            'business park', 'office park', 'corporate center', 'tower',
            'plaza', 'complex', 'headquarters', 'hq'
        ]
        
        small_business_indicators = [
            'high street', 'main street', 'home', 'flat', 'apartment',
            'cottage', 'house'
        ]
        
        for indicator in large_business_indicators:
            if indicator in address:
                scores['Large'] += 15
                scores['Enterprise'] += 10
        
        for indicator in small_business_indicators:
            if indicator in address:
                scores['Small'] += 15
        
        return scores
    
    def estimate_employee_count(self, business_size: str) -> int:
        """
        Estimate employee count based on business size category
        
        Args:
            business_size: Size category (Small, Medium, Large, Enterprise)
            
        Returns:
            Estimated employee count (midpoint of range)
        """
        if business_size in self.employee_ranges:
            min_emp, max_emp = self.employee_ranges[business_size]
            if max_emp == float('inf'):
                return 1500  # Reasonable estimate for enterprise
            return int((min_emp + max_emp) / 2)
        return 0
    
    def get_size_categories(self) -> list:
        """Get list of available size categories"""
        return ['All', 'Small', 'Medium', 'Large', 'Enterprise', 'Unknown']