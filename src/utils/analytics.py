"""Analytics and Insights Module

Provides analytics, statistics, and insights for business lead data.
Includes data visualization and trend analysis capabilities.
"""

import json
import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import statistics

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

class BusinessAnalytics:
    """Provides analytics and insights for business data"""
    
    def __init__(self):
        self.data_cache = {}
        self.last_analysis = None
    
    def analyze_data(self, businesses):
        """Analyze business data and return comprehensive insights"""
        if not businesses:
            return self._get_empty_analysis()
        
        try:
            return self._perform_analysis(businesses)
        except Exception as e:
            print(f"Error in data analysis: {e}")
            return self._get_empty_analysis()
    
    def _get_empty_analysis(self):
        """Return empty analysis structure"""
        return {
            'total_businesses': 0,
            'avg_performance_score': 0,
            'avg_seo_score': 0,
            'avg_accessibility_score': 0,
            'avg_best_practices_score': 0,
            'top_issues': [],
            'score_distribution': {},
            'recommendations': [],
            'analysis_timestamp': datetime.now().isoformat(),
            'data_quality': 'no_data'
        }
    
    def _perform_analysis(self, businesses):
        """Perform the actual analysis with validation"""
        # Validate and clean data
        valid_businesses = self._validate_business_data(businesses)
        total = len(valid_businesses)
        
        if total == 0:
            return self._get_empty_analysis()
        
        # Calculate averages with proper validation
        performance_scores = self._extract_valid_scores(valid_businesses, 'performance_score')
        seo_scores = self._extract_valid_scores(valid_businesses, 'seo_score')
        accessibility_scores = self._extract_valid_scores(valid_businesses, 'accessibility_score')
        best_practices_scores = self._extract_valid_scores(valid_businesses, 'best_practices_score')
        
        return {
            'total_businesses': total,
            'avg_performance_score': sum(performance_scores) / len(performance_scores) if performance_scores else 0,
            'avg_seo_score': sum(seo_scores) / len(seo_scores) if seo_scores else 0,
            'avg_accessibility_score': sum(accessibility_scores) / len(accessibility_scores) if accessibility_scores else 0,
            'avg_best_practices_score': sum(best_practices_scores) / len(best_practices_scores) if best_practices_scores else 0,
            'top_issues': self._identify_top_issues(valid_businesses),
            'score_distribution': self._calculate_score_distribution(valid_businesses),
            'recommendations': self._generate_score_recommendations(valid_businesses),
            'analysis_timestamp': datetime.now().isoformat(),
            'data_quality': 'valid'
        }
    
    def _validate_business_data(self, businesses):
        """Validate and filter business data"""
        valid_businesses = []
        for business in businesses:
            if isinstance(business, dict) and business.get('name'):
                valid_businesses.append(business)
        return valid_businesses
    
    def _extract_valid_scores(self, businesses, score_field):
        """Extract valid numeric scores from businesses"""
        scores = []
        for business in businesses:
            score = business.get(score_field)
            if isinstance(score, (int, float)) and 0 <= score <= 100:
                scores.append(score)
        return scores
    
    def _identify_top_issues(self, businesses):
        """Identify top performance issues"""
        issues = []
        for business in businesses:
            if business.get('performance_score', 0) < 50:
                issues.append(f"Low performance: {business.get('name', 'Unknown')}")
            if business.get('seo_score', 0) < 50:
                issues.append(f"SEO issues: {business.get('name', 'Unknown')}")
        return issues[:10]  # Return top 10 issues
    
    def _calculate_score_distribution(self, businesses):
        """Calculate score distribution ranges"""
        distribution = {'0-25': 0, '26-50': 0, '51-75': 0, '76-100': 0}
        for business in businesses:
            avg_score = sum([
                business.get('performance_score', 0),
                business.get('seo_score', 0),
                business.get('accessibility_score', 0),
                business.get('best_practices_score', 0)
            ]) / 4
            
            if avg_score <= 25:
                distribution['0-25'] += 1
            elif avg_score <= 50:
                distribution['26-50'] += 1
            elif avg_score <= 75:
                distribution['51-75'] += 1
            else:
                distribution['76-100'] += 1
        return distribution
    
    def _generate_score_recommendations(self, businesses):
        """Generate recommendations based on scores"""
        recommendations = []
        total = len(businesses)
        
        low_performance = sum(1 for b in businesses if b.get('performance_score', 0) < 50)
        if low_performance > total * 0.3:
            recommendations.append("Focus on improving website performance and loading speeds")
        
        low_seo = sum(1 for b in businesses if b.get('seo_score', 0) < 50)
        if low_seo > total * 0.3:
            recommendations.append("Implement better SEO practices and meta tags")
        
        return recommendations
    
    def analyze_business_data(self, businesses: List[Dict]) -> Dict[str, Any]:
        """Perform comprehensive analysis of business data
        
        Args:
            businesses: List of business data dictionaries
            
        Returns:
            Dictionary containing analysis results
        """
        if not businesses:
            return {'error': 'No data to analyze'}
        
        analysis = {
            'summary': self._get_summary_stats(businesses),
            'location_analysis': self._analyze_locations(businesses),
            'business_type_analysis': self._analyze_business_types(businesses),
            'contact_analysis': self._analyze_contact_info(businesses),
            'data_quality': self._analyze_data_quality(businesses),
            'trends': self._analyze_trends(businesses),
            'generated_at': datetime.now().isoformat()
        }
        
        self.last_analysis = analysis
        return analysis
    
    def _get_summary_stats(self, businesses: List[Dict]) -> Dict[str, Any]:
        """Get basic summary statistics"""
        total_businesses = len(businesses)
        
        # Count businesses with different contact methods
        with_email = sum(1 for b in businesses if b.get('email'))
        with_phone = sum(1 for b in businesses if b.get('phone'))
        with_website = sum(1 for b in businesses if b.get('website'))
        with_address = sum(1 for b in businesses if b.get('address'))
        
        return {
            'total_businesses': total_businesses,
            'with_email': with_email,
            'with_phone': with_phone,
            'with_website': with_website,
            'with_address': with_address,
            'email_percentage': (with_email / total_businesses * 100) if total_businesses > 0 else 0,
            'phone_percentage': (with_phone / total_businesses * 100) if total_businesses > 0 else 0,
            'website_percentage': (with_website / total_businesses * 100) if total_businesses > 0 else 0,
            'address_percentage': (with_address / total_businesses * 100) if total_businesses > 0 else 0
        }
    
    def _analyze_locations(self, businesses: List[Dict]) -> Dict[str, Any]:
        """Analyze location distribution"""
        locations = []
        postcodes = []
        
        for business in businesses:
            if business.get('location'):
                locations.append(business['location'])
            if business.get('postcode'):
                postcodes.append(business['postcode'][:2])  # First two characters for area
        
        location_counts = Counter(locations)
        postcode_area_counts = Counter(postcodes)
        
        return {
            'total_unique_locations': len(location_counts),
            'top_locations': dict(location_counts.most_common(10)),
            'location_distribution': dict(location_counts),
            'postcode_areas': dict(postcode_area_counts.most_common(10)),
            'geographic_spread': len(postcode_area_counts)
        }
    
    def _analyze_business_types(self, businesses: List[Dict]) -> Dict[str, Any]:
        """Analyze business type distribution"""
        business_types = []
        categories = []
        
        for business in businesses:
            if business.get('business_type'):
                business_types.append(business['business_type'])
            if business.get('category'):
                categories.append(business['category'])
        
        type_counts = Counter(business_types)
        category_counts = Counter(categories)
        
        return {
            'total_unique_types': len(type_counts),
            'top_business_types': dict(type_counts.most_common(10)),
            'business_type_distribution': dict(type_counts),
            'category_distribution': dict(category_counts),
            'diversity_index': len(type_counts) / len(businesses) if businesses else 0
        }
    
    def _analyze_contact_info(self, businesses: List[Dict]) -> Dict[str, Any]:
        """Analyze contact information completeness and patterns"""
        email_domains = []
        phone_prefixes = []
        website_domains = []
        
        for business in businesses:
            # Email domain analysis
            if business.get('email'):
                email = business['email']
                if '@' in email:
                    domain = email.split('@')[1].lower()
                    email_domains.append(domain)
            
            # Phone prefix analysis
            if business.get('phone'):
                phone = business['phone']
                # Extract area code (first 4-5 digits after country code)
                clean_phone = ''.join(filter(str.isdigit, phone))
                if len(clean_phone) >= 6:
                    if clean_phone.startswith('44'):
                        prefix = clean_phone[2:5]  # UK area code
                    else:
                        prefix = clean_phone[:3]
                    phone_prefixes.append(prefix)
            
            # Website domain analysis
            if business.get('website'):
                website = business['website']
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(website).netloc.lower()
                    if domain:
                        website_domains.append(domain)
                except (ValueError, AttributeError) as e:
                    # Skip invalid URLs
                    continue
        
        email_domain_counts = Counter(email_domains)
        phone_prefix_counts = Counter(phone_prefixes)
        website_domain_counts = Counter(website_domains)
        
        return {
            'email_domains': dict(email_domain_counts.most_common(10)),
            'phone_area_codes': dict(phone_prefix_counts.most_common(10)),
            'website_domains': dict(website_domain_counts.most_common(10)),
            'contact_completeness': self._calculate_contact_completeness(businesses)
        }
    
    def _calculate_contact_completeness(self, businesses: List[Dict]) -> Dict[str, Any]:
        """Calculate contact information completeness scores"""
        scores = []
        
        for business in businesses:
            score = 0
            max_score = 4
            
            if business.get('email'):
                score += 1
            if business.get('phone'):
                score += 1
            if business.get('website'):
                score += 1
            if business.get('address'):
                score += 1
            
            scores.append(score / max_score * 100)
        
        if scores:
            return {
                'average_completeness': sum(scores) / len(scores),
                'min_completeness': min(scores),
                'max_completeness': max(scores),
                'completeness_distribution': Counter([int(score // 25) * 25 for score in scores])
            }
        
        return {'average_completeness': 0}
    
    def _analyze_data_quality(self, businesses: List[Dict]) -> Dict[str, Any]:
        """Analyze data quality metrics"""
        quality_issues = {
            'missing_name': 0,
            'missing_address': 0,
            'invalid_email': 0,
            'invalid_phone': 0,
            'invalid_website': 0,
            'duplicate_entries': 0
        }
        
        seen_businesses = set()
        
        for business in businesses:
            # Check for missing critical fields
            if not business.get('name'):
                quality_issues['missing_name'] += 1
            if not business.get('address'):
                quality_issues['missing_address'] += 1
            
            # Basic validation checks
            if business.get('email') and '@' not in business['email']:
                quality_issues['invalid_email'] += 1
            
            if business.get('phone'):
                phone = ''.join(filter(str.isdigit, business['phone']))
                if len(phone) < 10:
                    quality_issues['invalid_phone'] += 1
            
            if business.get('website'):
                website = business['website']
                if not (website.startswith('http') or '.' in website):
                    quality_issues['invalid_website'] += 1
            
            # Check for duplicates (simple name + address check)
            business_key = (business.get('name', '').lower(), business.get('address', '').lower())
            if business_key in seen_businesses:
                quality_issues['duplicate_entries'] += 1
            else:
                seen_businesses.add(business_key)
        
        total_businesses = len(businesses)
        quality_score = 100
        
        if total_businesses > 0:
            # Calculate quality score (percentage of businesses without issues)
            total_issues = sum(quality_issues.values())
            quality_score = max(0, 100 - (total_issues / total_businesses * 100))
        
        return {
            'quality_score': quality_score,
            'issues': quality_issues,
            'issue_percentages': {
                key: (value / total_businesses * 100) if total_businesses > 0 else 0
                for key, value in quality_issues.items()
            }
        }
    
    def _analyze_trends(self, businesses: List[Dict]) -> Dict[str, Any]:
        """Analyze trends in the data"""
        # This would be more meaningful with timestamp data
        # For now, provide basic trend indicators
        
        trends = {
            'data_collection_date': datetime.now().isoformat(),
            'sample_size': len(businesses),
            'recommendations': self._generate_recommendations(businesses)
        }
        
        return trends
    
    def _generate_recommendations(self, businesses: List[Dict]) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []
        
        if not businesses:
            return ['No data available for analysis']
        
        total = len(businesses)
        
        # Email recommendations
        with_email = sum(1 for b in businesses if b.get('email'))
        email_percentage = (with_email / total * 100) if total > 0 else 0
        
        if email_percentage < 50:
            recommendations.append(f"Only {email_percentage:.1f}% of businesses have email addresses. Consider focusing on email collection.")
        
        # Phone recommendations
        with_phone = sum(1 for b in businesses if b.get('phone'))
        phone_percentage = (with_phone / total * 100) if total > 0 else 0
        
        if phone_percentage < 70:
            recommendations.append(f"Phone coverage is {phone_percentage:.1f}%. Phone numbers are often easier to find than emails.")
        
        # Website recommendations
        with_website = sum(1 for b in businesses if b.get('website'))
        website_percentage = (with_website / total * 100) if total > 0 else 0
        
        if website_percentage > 80:
            recommendations.append(f"High website coverage ({website_percentage:.1f}%) indicates good digital presence in this area.")
        elif website_percentage < 30:
            recommendations.append(f"Low website coverage ({website_percentage:.1f}%) suggests opportunities for web development services.")
        
        # Location diversity
        locations = [b.get('location') for b in businesses if b.get('location')]
        unique_locations = len(set(locations))
        
        if unique_locations == 1:
            recommendations.append("All businesses are from the same location. Consider expanding search area.")
        elif unique_locations > total * 0.8:
            recommendations.append("High location diversity. Consider focusing on specific areas for better targeting.")
        
        return recommendations
    
    def generate_report(self, businesses: List[Dict], output_path: Optional[str] = None) -> str:
        """Generate a comprehensive analytics report
        
        Args:
            businesses: List of business data
            output_path: Optional path to save report
            
        Returns:
            Report content as string
        """
        analysis = self.analyze_business_data(businesses)
        
        report_lines = [
            "# Business Lead Analytics Report",
            f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary Statistics",
            f"- Total Businesses: {analysis['summary']['total_businesses']}",
            f"- Businesses with Email: {analysis['summary']['with_email']} ({analysis['summary']['email_percentage']:.1f}%)",
            f"- Businesses with Phone: {analysis['summary']['with_phone']} ({analysis['summary']['phone_percentage']:.1f}%)",
            f"- Businesses with Website: {analysis['summary']['with_website']} ({analysis['summary']['website_percentage']:.1f}%)",
            "",
            "## Location Analysis",
            f"- Unique Locations: {analysis['location_analysis']['total_unique_locations']}",
            f"- Geographic Spread: {analysis['location_analysis']['geographic_spread']} postcode areas",
            "",
            "### Top Locations:"
        ]
        
        for location, count in analysis['location_analysis']['top_locations'].items():
            report_lines.append(f"- {location}: {count} businesses")
        
        report_lines.extend([
            "",
            "## Business Type Analysis",
            f"- Unique Business Types: {analysis['business_type_analysis']['total_unique_types']}",
            f"- Type Diversity Index: {analysis['business_type_analysis']['diversity_index']:.2f}",
            "",
            "### Top Business Types:"
        ])
        
        for btype, count in analysis['business_type_analysis']['top_business_types'].items():
            report_lines.append(f"- {btype}: {count} businesses")
        
        report_lines.extend([
            "",
            "## Data Quality",
            f"- Overall Quality Score: {analysis['data_quality']['quality_score']:.1f}%",
            "",
            "### Quality Issues:"
        ])
        
        for issue, percentage in analysis['data_quality']['issue_percentages'].items():
            if percentage > 0:
                report_lines.append(f"- {issue.replace('_', ' ').title()}: {percentage:.1f}%")
        
        report_lines.extend([
            "",
            "## Recommendations"
        ])
        
        for rec in analysis['trends']['recommendations']:
            report_lines.append(f"- {rec}")
        
        report_content = "\n".join(report_lines)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
        
        return report_content
    
    def create_visualizations(self, businesses: List[Dict], output_dir: str = "analytics_charts") -> Dict[str, str]:
        """Create data visualizations
        
        Args:
            businesses: List of business data
            output_dir: Directory to save charts
            
        Returns:
            Dictionary mapping chart names to file paths
        """
        if not MATPLOTLIB_AVAILABLE:
            return {'error': 'Matplotlib not available for visualizations'}
        
        Path(output_dir).mkdir(exist_ok=True)
        chart_files = {}
        
        analysis = self.analyze_business_data(businesses)
        
        # Contact method distribution pie chart
        plt.figure(figsize=(10, 6))
        contact_data = [
            analysis['summary']['with_email'],
            analysis['summary']['with_phone'],
            analysis['summary']['with_website']
        ]
        contact_labels = ['Email', 'Phone', 'Website']
        
        plt.pie(contact_data, labels=contact_labels, autopct='%1.1f%%', startangle=90)
        plt.title('Contact Information Distribution')
        chart_path = Path(output_dir) / 'contact_distribution.png'
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        chart_files['contact_distribution'] = str(chart_path)
        
        # Top locations bar chart
        if analysis['location_analysis']['top_locations']:
            plt.figure(figsize=(12, 6))
            locations = list(analysis['location_analysis']['top_locations'].keys())[:10]
            counts = list(analysis['location_analysis']['top_locations'].values())[:10]
            
            plt.bar(locations, counts)
            plt.title('Top 10 Business Locations')
            plt.xlabel('Location')
            plt.ylabel('Number of Businesses')
            plt.xticks(rotation=45, ha='right')
            chart_path = Path(output_dir) / 'top_locations.png'
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            chart_files['top_locations'] = str(chart_path)
        
        # Business type distribution
        if analysis['business_type_analysis']['top_business_types']:
            plt.figure(figsize=(12, 8))
            types = list(analysis['business_type_analysis']['top_business_types'].keys())[:10]
            counts = list(analysis['business_type_analysis']['top_business_types'].values())[:10]
            
            plt.barh(types, counts)
            plt.title('Top 10 Business Types')
            plt.xlabel('Number of Businesses')
            plt.ylabel('Business Type')
            chart_path = Path(output_dir) / 'business_types.png'
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            chart_files['business_types'] = str(chart_path)
        
        return chart_files
    
    def export_analysis(self, businesses: List[Dict], output_path: str) -> bool:
        """Export complete analysis to JSON file
        
        Args:
            businesses: List of business data
            output_path: Path to save analysis JSON
            
        Returns:
            True if successful
        """
        try:
            analysis = self.analyze_business_data(businesses)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error exporting analysis: {e}")
            return False

# Global analytics instance
analytics = BusinessAnalytics()