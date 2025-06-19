#!/usr/bin/env python3
"""
Test script for the enhanced website analyzer with advanced SEO and screenshot capabilities.
"""

import sys
import os
import json
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.analyzer import WebsiteAnalyzer

def test_website_analysis():
    """Test the enhanced website analyzer"""
    print("=" * 60)
    print("Enhanced Website Analyzer Test")
    print("=" * 60)
    
    # Initialize analyzer with Selenium enabled
    analyzer = WebsiteAnalyzer(use_selenium=True)
    
    # Test websites
    test_urls = [
        "https://www.bbc.co.uk",
        "https://www.gov.uk",
        "https://www.example.com"
    ]
    
    results = {}
    
    for url in test_urls:
        print(f"\n{'='*40}")
        print(f"Analyzing: {url}")
        print(f"{'='*40}")
        
        try:
            # Perform analysis
            analysis = analyzer.analyze_website(url)
            results[url] = analysis
            
            # Display key results
            print(f"\n📊 Analysis Results for {url}:")
            print(f"   🚀 Performance Score: {analysis.get('performance_score', 'N/A')}/100")
            print(f"   🔍 SEO Score: {analysis.get('seo_score', 'N/A')}/100")
            print(f"   ♿ Accessibility Score: {analysis.get('accessibility_score', 'N/A')}/100")
            print(f"   ✅ Best Practices Score: {analysis.get('best_practices_score', 'N/A')}/100")
            print(f"   ⭐ Priority Score: {analysis.get('priority', 'N/A')}/100")
            
            # Core Web Vitals
            if 'core_web_vitals' in analysis:
                vitals = analysis['core_web_vitals']
                print(f"\n🎯 Core Web Vitals:")
                print(f"   📏 LCP (Largest Contentful Paint): {vitals.get('lcp', 0)/1000:.2f}s")
                print(f"   ⚡ FID (First Input Delay): {vitals.get('fid', 0):.0f}ms")
                print(f"   📐 CLS (Cumulative Layout Shift): {vitals.get('cls', 0):.3f}")
            
            # Advanced SEO features
            print(f"\n🔍 Advanced SEO Features:")
            print(f"   📋 Schema Markup: {'✅' if analysis.get('has_schema_markup') else '❌'}")
            print(f"   🔗 Canonical URL: {'✅' if analysis.get('has_canonical') else '❌'}")
            print(f"   📱 Open Graph: {'✅' if analysis.get('has_open_graph') else '❌'}")
            print(f"   🐦 Twitter Cards: {'✅' if analysis.get('has_twitter_cards') else '❌'}")
            print(f"   🔗 Internal Links: {analysis.get('internal_links_count', 0)}")
            
            # Heading structure
            if 'heading_structure' in analysis:
                headings = analysis['heading_structure']
                print(f"\n📝 Heading Structure:")
                for level, count in headings.items():
                    if count > 0:
                        print(f"   {level.upper()}: {count}")
            
            # Screenshots
            if 'screenshots' in analysis:
                screenshots = analysis['screenshots']
                print(f"\n📸 Screenshots Captured:")
                for viewport, path in screenshots.items():
                    if path and os.path.exists(path):
                        size = os.path.getsize(path)
                        print(f"   📱 {viewport}: {path} ({size:,} bytes)")
                    else:
                        print(f"   ❌ {viewport}: Failed to capture")
            elif analysis.get('screenshot'):
                path = analysis['screenshot']
                if path and os.path.exists(path):
                    size = os.path.getsize(path)
                    print(f"\n📸 Screenshot: {path} ({size:,} bytes)")
            
            # Mobile responsiveness
            if 'mobile_responsive' in analysis:
                print(f"\n📱 Mobile Responsive: {'✅' if analysis['mobile_responsive'] else '❌'}")
            
            # Issues found
            issues = analysis.get('issues', [])
            if issues:
                print(f"\n⚠️  Issues Found ({len(issues)}):")
                for i, issue in enumerate(issues[:10], 1):  # Show first 10 issues
                    print(f"   {i}. {issue}")
                if len(issues) > 10:
                    print(f"   ... and {len(issues) - 10} more issues")
            else:
                print(f"\n✅ No issues found!")
                
        except Exception as e:
            print(f"❌ Error analyzing {url}: {str(e)}")
            results[url] = {"error": str(e)}
    
    # Save detailed results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"analysis_results_{timestamp}.json"
    
    try:
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Detailed results saved to: {results_file}")
    except Exception as e:
        print(f"❌ Error saving results: {str(e)}")
    
    # Cleanup
    analyzer.cleanup()
    
    print(f"\n{'='*60}")
    print("✅ Enhanced Website Analysis Test Complete!")
    print(f"{'='*60}")

def test_screenshot_functionality():
    """Test screenshot functionality specifically"""
    print("\n" + "=" * 40)
    print("Testing Screenshot Functionality")
    print("=" * 40)
    
    analyzer = WebsiteAnalyzer(use_selenium=True)
    
    test_url = "https://www.example.com"
    
    try:
        print(f"Capturing screenshots for: {test_url}")
        analysis = analyzer.analyze_website(test_url)
        
        if 'screenshots' in analysis:
            screenshots = analysis['screenshots']
            print(f"\n📸 Screenshot Results:")
            
            for viewport, path in screenshots.items():
                if path and os.path.exists(path):
                    size = os.path.getsize(path)
                    print(f"   ✅ {viewport}: {os.path.basename(path)} ({size:,} bytes)")
                else:
                    print(f"   ❌ {viewport}: Failed")
        else:
            print("❌ No screenshots captured")
            
    except Exception as e:
        print(f"❌ Error in screenshot test: {str(e)}")
    finally:
        analyzer.cleanup()

if __name__ == "__main__":
    # Run the enhanced analyzer test
    test_website_analysis()
    
    # Test screenshot functionality
    test_screenshot_functionality()
    
    print("\n🎉 All tests completed!")