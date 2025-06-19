"""Advanced website analyzer module with comprehensive testing capabilities"""

import os
import json
import time
import requests
import re
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException


class WebsiteAnalyzer:
    """Advanced website analysis with comprehensive testing capabilities"""

    def __init__(self, use_selenium=True):
        """
        Initialize the analyzer

        Args:
            use_selenium: Whether to use Selenium for advanced testing
        """
        self.use_selenium = use_selenium
        self.driver = None
        if use_selenium:
            self._setup_selenium()

    def _setup_selenium(self):
        """Setup Selenium WebDriver for advanced testing"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            
            # Try to find ChromeDriver
            chromedriver_paths = [
                os.path.join(os.getcwd(), 'chromedriver.exe'),
                os.path.join(os.getcwd(), 'drivers', 'chromedriver.exe'),
                'chromedriver.exe'  # If in PATH
            ]
            
            driver_path = None
            for path in chromedriver_paths:
                if os.path.exists(path):
                    driver_path = path
                    break
            
            if driver_path:
                self.driver = webdriver.Chrome(executable_path=driver_path, options=chrome_options)
            else:
                # Try without specifying path (if chromedriver is in PATH)
                self.driver = webdriver.Chrome(options=chrome_options)
                
            print("Selenium WebDriver initialized successfully")
            
        except Exception as e:
            print(f"Failed to initialize Selenium: {e}")
            self.driver = None
            self.use_selenium = False

    def analyze_website(self, url):
        """
        Analyze a website for performance, SEO, accessibility and best practices

        Args:
            url: URL of the website to analyze

        Returns:
            Dictionary with analysis results
        """
        # Initialize results with default values
        results = {
            "performance_score": 0,
            "seo_score": 0,
            "accessibility_score": 0,
            "best_practices_score": 0,
            "has_ssl": False,
            "has_mobile_viewport": False,
            "issues": [],
        }

        # Basic validation
        if not url:
            results["issues"].append("No URL provided")
            return results

        # Ensure URL has scheme
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        # First do some basic checks
        self._check_website_basics(url, results)

        # Perform comprehensive analysis
        print(f"Running comprehensive website analysis for {url}")
        self._perform_comprehensive_analysis(url, results)
        
        # If Selenium is available, run advanced tests
        if self.use_selenium and self.driver:
            print(f"Running advanced Selenium tests for {url}")
            self._perform_selenium_analysis(url, results)
        else:
            print(f"Selenium not available, using basic analysis only for {url}")
        
        # Debug: Print final scores
        print(f"Analysis results for {url}:")
        print(f"  Performance: {results['performance_score']}")
        print(f"  SEO: {results['seo_score']}")
        print(f"  Accessibility: {results['accessibility_score']}")
        print(f"  Best Practices: {results['best_practices_score']}")
        print(f"  Issues: {len(results['issues'])} found")

        # Set the priority based on results
        results["priority"] = self._calculate_priority(results)

        return results

    def _check_website_basics(self, url, results):
        """Check basic website properties and capture screenshot"""
        try:
            # Initialize additional metrics
            results.update({
                "has_ssl": False,
                "has_mobile_viewport": False,
                "has_meta_description": False,
                "has_sitemap": False,
                "has_robots_txt": False,
                "load_time": None,
                "page_size": None,
                "screenshot": None,
                "meta_tags": {},
                "social_media_presence": []
            })

            # Check for SSL (https)
            results["has_ssl"] = url.startswith("https://")
            if not results["has_ssl"]:
                results["issues"].append("Website does not use SSL (https)")
                self._check_https_availability(url, results)

            # Measure load time and get webpage
            start_time = time.time()
            response = requests.get(url, timeout=10)
            load_time = time.time() - start_time
            results["load_time"] = round(load_time, 2)

            if load_time > 3:
                results["issues"].append(f"Slow load time: {load_time:.2f} seconds")

            # Check response status
            if response.status_code >= 400:
                results["issues"].append(f"Website returns HTTP status {response.status_code}")
                return

            # Check for redirects
            final_url = response.url
            if urlparse(final_url).netloc != urlparse(url).netloc:
                results["issues"].append(f"Website redirects to {final_url}")

            # Parse HTML content
            soup = BeautifulSoup(response.text, 'lxml')

            # Check meta tags
            self._check_meta_tags(soup, results)

            # Check page size and content
            self._check_page_content(response, results)

            # Check for sitemap and robots.txt
            self._check_site_files(url, results)

            # Check social media presence
            self._check_social_media(soup, results)

            # Capture screenshot if using Selenium
            if self.use_selenium and self.driver:
                self._capture_screenshot(url, results)

        except requests.RequestException as e:
            results["issues"].append(f"Error accessing website: {str(e)}")
        except Exception as e:
            results["issues"].append(f"Error during basic analysis: {str(e)}")
            # Provide fallback scores even if analysis fails
            if results["performance_score"] == 0:
                results["performance_score"] = 50
            if results["seo_score"] == 0:
                results["seo_score"] = 50
            if results["accessibility_score"] == 0:
                results["accessibility_score"] = 50
            if results["best_practices_score"] == 0:
                results["best_practices_score"] = 50

    def _check_https_availability(self, url, results):
        """Check if HTTPS is available but not used"""
        try:
            https_url = "https://" + url[7:] if url.startswith("http://") else "https://" + url
            response = requests.head(https_url, timeout=10, allow_redirects=True)
            if response.status_code < 400:
                results["issues"].append("HTTPS is available but not used by default")
        except (requests.RequestException, requests.Timeout):
            pass

    def _check_meta_tags(self, soup, results):
        """Check meta tags and SEO elements"""
        # Check viewport
        viewport = soup.find('meta', {'name': 'viewport'})
        results["has_mobile_viewport"] = bool(viewport)
        if not results["has_mobile_viewport"]:
            results["issues"].append("No mobile viewport meta tag found")

        # Check meta description
        meta_desc = soup.find('meta', {'name': 'description'})
        results["has_meta_description"] = bool(meta_desc)
        if meta_desc:
            desc_content = meta_desc.get('content', '')
            if len(desc_content) < 50 or len(desc_content) > 160:
                results["issues"].append("Meta description length is not optimal")

        # Store important meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name', meta.get('property', ''))
            content = meta.get('content', '')
            if name and content:
                results["meta_tags"][name] = content

    def _check_page_content(self, response, results):
        """Analyze page content and structure"""
        # Check page size
        page_size_kb = len(response.content) / 1024
        results["page_size"] = round(page_size_kb, 2)
        if page_size_kb > 5000:
            results["issues"].append(f"Page size is large ({page_size_kb:.1f} KB)")

        # Parse content
        soup = BeautifulSoup(response.text, 'lxml')

        # Check heading structure
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if not soup.find('h1'):
            results["issues"].append("Missing H1 heading")
        elif len(soup.find_all('h1')) > 1:
            results["issues"].append("Multiple H1 headings found")

    def _check_site_files(self, url, results):
        """Check for sitemap.xml and robots.txt"""
        base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        
        try:
            robots_response = requests.get(f"{base_url}/robots.txt", timeout=5)
            results["has_robots_txt"] = robots_response.status_code == 200

            sitemap_response = requests.get(f"{base_url}/sitemap.xml", timeout=5)
            results["has_sitemap"] = sitemap_response.status_code == 200
        except (requests.RequestException, requests.Timeout):
            pass

    def _check_social_media(self, soup, results):
        """Check for social media presence"""
        social_patterns = {
            'facebook': r'facebook\.com',
            'twitter': r'twitter\.com|x\.com',
            'linkedin': r'linkedin\.com',
            'instagram': r'instagram\.com'
        }

        for link in soup.find_all('a', href=True):
            href = link['href']
            for platform, pattern in social_patterns.items():
                if re.search(pattern, href) and platform not in results["social_media_presence"]:
                    results["social_media_presence"].append(platform)

    def _capture_screenshot(self, url, results):
        """Capture website screenshot using Selenium"""
        try:
            self.driver.get(url)
            time.sleep(2)  # Wait for page to load
            screenshot = self.driver.get_screenshot_as_base64()
            results["screenshot"] = screenshot
        except Exception as e:
            results["issues"].append(f"Failed to capture screenshot: {str(e)}")

    def _perform_selenium_analysis(self, url, results):
        """Perform advanced analysis using Selenium WebDriver"""
        try:
            # Navigate to the website
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Test mobile responsiveness
            self._test_mobile_responsiveness(results)
            
            # Test interactive elements
            self._test_interactive_elements(results)
            
            # Test form functionality
            self._test_forms(results)
            
            # Test navigation
            self._test_navigation(results)
            
            # Capture screenshot
            self._capture_screenshot(url, results)
            
            # Test page load performance
            self._test_page_performance(results)
            
        except TimeoutException:
            results["issues"].append("Page took too long to load (>10 seconds)")
        except WebDriverException as e:
            results["issues"].append(f"Browser error during testing: {str(e)}")
        except Exception as e:
            results["issues"].append(f"Error during Selenium analysis: {str(e)}")
    
    def _test_mobile_responsiveness(self, results):
        """Test mobile responsiveness using different viewport sizes"""
        try:
            # Test different screen sizes
            screen_sizes = [
                (375, 667),   # iPhone 6/7/8
                (414, 896),   # iPhone XR
                (768, 1024),  # iPad
                (1920, 1080)  # Desktop
            ]
            
            mobile_issues = []
            
            for width, height in screen_sizes:
                self.driver.set_window_size(width, height)
                time.sleep(1)  # Wait for resize
                
                # Check for horizontal scrollbar on mobile
                if width < 768:  # Mobile sizes
                    body_width = self.driver.execute_script("return document.body.scrollWidth")
                    if body_width > width + 10:  # Allow small tolerance
                        mobile_issues.append(f"Horizontal scroll on {width}px width")
                
                # Check if navigation is accessible
                nav_elements = self.driver.find_elements(By.TAG_NAME, "nav")
                if nav_elements and width < 768:
                    # Look for mobile menu toggle
                    menu_toggles = self.driver.find_elements(By.CSS_SELECTOR, 
                        "[class*='menu'], [class*='hamburger'], [class*='toggle'], [id*='menu']")
                    if not menu_toggles:
                        mobile_issues.append("No mobile menu toggle found")
            
            if mobile_issues:
                results["issues"].extend(mobile_issues)
                if results["accessibility_score"] > 20:
                    results["accessibility_score"] -= 15
            else:
                # Bonus for good mobile responsiveness
                results["accessibility_score"] = min(100, results["accessibility_score"] + 10)
                
        except Exception as e:
            results["issues"].append(f"Error testing mobile responsiveness: {str(e)}")
    
    def _test_interactive_elements(self, results):
        """Test interactive elements like buttons and links"""
        try:
            # Test buttons
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            buttons.extend(self.driver.find_elements(By.CSS_SELECTOR, "[role='button']"))
            
            for button in buttons[:5]:  # Test first 5 buttons
                try:
                    if button.is_displayed() and button.is_enabled():
                        # Check if button has accessible text
                        text = button.text or button.get_attribute("aria-label") or button.get_attribute("title")
                        if not text:
                            results["issues"].append("Button without accessible text found")
                            break
                except Exception:
                    continue
            
            # Test links
            links = self.driver.find_elements(By.TAG_NAME, "a")
            empty_links = 0
            
            for link in links[:10]:  # Test first 10 links
                try:
                    href = link.get_attribute("href")
                    text = link.text.strip()
                    
                    if href and not text and not link.find_elements(By.TAG_NAME, "img"):
                        empty_links += 1
                        
                    if text and text.lower() in ["click here", "read more", "more"]:
                        results["issues"].append("Generic link text found (poor for accessibility)")
                        break
                        
                except Exception:
                    continue
            
            if empty_links > 2:
                results["issues"].append(f"{empty_links} empty links found")
                
        except Exception as e:
            results["issues"].append(f"Error testing interactive elements: {str(e)}")
    
    def _test_forms(self, results):
        """Test form accessibility and functionality"""
        try:
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            
            for form in forms:
                # Check for labels
                inputs = form.find_elements(By.CSS_SELECTOR, "input, textarea, select")
                unlabeled_inputs = 0
                
                for input_elem in inputs:
                    input_type = input_elem.get_attribute("type")
                    if input_type in ["hidden", "submit", "button"]:
                        continue
                        
                    # Check for label association
                    input_id = input_elem.get_attribute("id")
                    aria_label = input_elem.get_attribute("aria-label")
                    placeholder = input_elem.get_attribute("placeholder")
                    
                    has_label = False
                    if input_id:
                        labels = self.driver.find_elements(By.CSS_SELECTOR, f"label[for='{input_id}']")
                        has_label = len(labels) > 0
                    
                    if not has_label and not aria_label and not placeholder:
                        unlabeled_inputs += 1
                
                if unlabeled_inputs > 0:
                    results["issues"].append(f"Form with {unlabeled_inputs} unlabeled inputs found")
                    if results["accessibility_score"] > 15:
                        results["accessibility_score"] -= 10
                        
        except Exception as e:
            results["issues"].append(f"Error testing forms: {str(e)}")
    
    def _test_navigation(self, results):
        """Test website navigation structure"""
        try:
            # Check for main navigation
            nav_elements = self.driver.find_elements(By.TAG_NAME, "nav")
            if not nav_elements:
                nav_elements = self.driver.find_elements(By.CSS_SELECTOR, "[role='navigation']")
            
            if not nav_elements:
                results["issues"].append("No main navigation found")
                if results["accessibility_score"] > 10:
                    results["accessibility_score"] -= 10
            else:
                # Check navigation links
                nav = nav_elements[0]
                nav_links = nav.find_elements(By.TAG_NAME, "a")
                
                if len(nav_links) < 2:
                    results["issues"].append("Very few navigation links found")
                elif len(nav_links) > 10:
                    results["issues"].append("Too many navigation links (may confuse users)")
            
            # Check for breadcrumbs
            breadcrumbs = self.driver.find_elements(By.CSS_SELECTOR, 
                "[class*='breadcrumb'], [aria-label*='breadcrumb'], nav ol, nav ul")
            
            # Check for skip links (accessibility)
            skip_links = self.driver.find_elements(By.CSS_SELECTOR, 
                "a[href*='#main'], a[href*='#content'], [class*='skip']")
            
            if not skip_links:
                results["issues"].append("No skip navigation links found (accessibility issue)")
                
        except Exception as e:
            results["issues"].append(f"Error testing navigation: {str(e)}")
    
    def _test_page_performance(self, results):
        """Test page performance metrics using browser APIs"""
        try:
            # Get performance timing data
            perf_data = self.driver.execute_script("""
                var perf = window.performance;
                var timing = perf.timing;
                return {
                    loadTime: timing.loadEventEnd - timing.navigationStart,
                    domReady: timing.domContentLoadedEventEnd - timing.navigationStart,
                    firstPaint: perf.getEntriesByType('paint')[0] ? perf.getEntriesByType('paint')[0].startTime : null,
                    resourceCount: perf.getEntriesByType('resource').length
                };
            """)
            
            if perf_data:
                load_time = perf_data.get('loadTime', 0) / 1000  # Convert to seconds
                dom_ready = perf_data.get('domReady', 0) / 1000
                resource_count = perf_data.get('resourceCount', 0)
                
                # Update performance score based on metrics
                if load_time > 5:
                    results["issues"].append(f"Very slow page load: {load_time:.2f}s")
                    results["performance_score"] = max(20, results["performance_score"] - 30)
                elif load_time > 3:
                    results["issues"].append(f"Slow page load: {load_time:.2f}s")
                    results["performance_score"] = max(30, results["performance_score"] - 20)
                
                if resource_count > 100:
                    results["issues"].append(f"Too many resources loaded: {resource_count}")
                    results["performance_score"] = max(25, results["performance_score"] - 15)
                
                # Store performance metrics
                results["performance_metrics"] = {
                    "load_time": round(load_time, 2),
                    "dom_ready_time": round(dom_ready, 2),
                    "resource_count": resource_count
                }
                
        except Exception as e:
            results["issues"].append(f"Error measuring performance: {str(e)}")

    def _perform_comprehensive_analysis(self, url, results):
        """Perform comprehensive analysis with enhanced checks"""
        try:
            # Get the webpage
            response = requests.get(url, timeout=15, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            html = response.text
            html_lower = html.lower()
            
            # Parse with BeautifulSoup for better analysis
            soup = BeautifulSoup(html, 'html.parser')
            headers = response.headers

            # Enhanced Performance checks
            performance_score = 80
            self._analyze_performance(response, results, performance_score)
            
            # Enhanced SEO checks
            seo_score = 80
            self._analyze_seo(soup, html_lower, results, seo_score)
            
            # Enhanced Accessibility checks
            accessibility_score = 75
            self._analyze_accessibility(soup, html_lower, results, accessibility_score)
            
            # Enhanced Best practices checks
            best_practices_score = 75
            self._analyze_best_practices(soup, headers, html_lower, results, best_practices_score)
            
            # Additional comprehensive checks
            self._analyze_content_quality(soup, results)
            self._analyze_technical_seo(soup, url, results)
            self._analyze_user_experience(soup, results)

        except Exception as e:
            results["issues"].append(f"Error during comprehensive analysis: {str(e)}")
    
    def _analyze_performance(self, response, results, base_score):
        """Analyze website performance metrics"""
        performance_score = base_score
        
        # Page size analysis
        page_size_mb = len(response.content) / (1024 * 1024)
        if page_size_mb > 5:
            results["issues"].append(f"Very large page size: {page_size_mb:.1f}MB")
            performance_score -= 30
        elif page_size_mb > 2:
            results["issues"].append(f"Large page size: {page_size_mb:.1f}MB")
            performance_score -= 15
        
        # Load time analysis
        load_time = results.get("load_time", 0)
        if load_time > 5:
            results["issues"].append(f"Very slow load time: {load_time:.2f}s")
            performance_score -= 25
        elif load_time > 3:
            results["issues"].append(f"Slow load time: {load_time:.2f}s")
            performance_score -= 15
        
        # Check for compression
        if 'gzip' not in response.headers.get('Content-Encoding', '') and \
           'br' not in response.headers.get('Content-Encoding', ''):
            results["issues"].append("No compression detected (gzip/brotli)")
            performance_score -= 10
        
        # Check for caching headers
        cache_headers = ['Cache-Control', 'ETag', 'Last-Modified', 'Expires']
        if not any(header in response.headers for header in cache_headers):
            results["issues"].append("No caching headers found")
            performance_score -= 10
        
        results["performance_score"] = max(20, performance_score)
    
    def _analyze_seo(self, soup, html_lower, results, base_score):
        """Analyze SEO factors"""
        seo_score = base_score
        
        # Title analysis
        title_tag = soup.find('title')
        if not title_tag or not title_tag.text.strip():
            results["issues"].append("Missing or empty page title")
            seo_score -= 25
        else:
            title_length = len(title_tag.text)
            if title_length < 30:
                results["issues"].append("Page title too short (< 30 characters)")
                seo_score -= 10
            elif title_length > 60:
                results["issues"].append("Page title too long (> 60 characters)")
                seo_score -= 10
        
        # Meta description analysis
        meta_desc = soup.find('meta', {'name': 'description'})
        if not meta_desc or not meta_desc.get('content', '').strip():
            results["issues"].append("Missing meta description")
            seo_score -= 20
        else:
            desc_length = len(meta_desc.get('content', ''))
            if desc_length < 120:
                results["issues"].append("Meta description too short (< 120 characters)")
                seo_score -= 10
            elif desc_length > 160:
                results["issues"].append("Meta description too long (> 160 characters)")
                seo_score -= 10
        
        # Heading structure analysis
        h1_tags = soup.find_all('h1')
        if not h1_tags:
            results["issues"].append("Missing H1 heading")
            seo_score -= 20
        elif len(h1_tags) > 1:
            results["issues"].append("Multiple H1 headings found")
            seo_score -= 15
        
        # Check heading hierarchy
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if len(headings) < 3:
            results["issues"].append("Poor heading structure (< 3 headings)")
            seo_score -= 10
        
        # Image alt text analysis
        images = soup.find_all('img')
        images_without_alt = [img for img in images if not img.get('alt')]
        if images_without_alt:
            percentage = (len(images_without_alt) / len(images)) * 100 if images else 0
            results["issues"].append(f"{len(images_without_alt)} images missing alt text ({percentage:.0f}%)")
            seo_score -= min(20, percentage // 10 * 5)
        
        # Internal linking
        internal_links = soup.find_all('a', href=True)
        if len(internal_links) < 5:
            results["issues"].append("Very few internal links found")
            seo_score -= 10
        
        # Check for SSL
        if not results.get("has_ssl", False):
            seo_score -= 15
        
        results["seo_score"] = max(20, seo_score)
    
    def _analyze_accessibility(self, soup, html_lower, results, base_score):
        """Analyze accessibility factors"""
        accessibility_score = base_score
        
        # Form accessibility
        forms = soup.find_all('form')
        for form in forms:
            inputs = form.find_all(['input', 'textarea', 'select'])
            unlabeled_inputs = 0
            
            for input_elem in inputs:
                input_type = input_elem.get('type', '')
                if input_type in ['hidden', 'submit', 'button']:
                    continue
                
                input_id = input_elem.get('id')
                aria_label = input_elem.get('aria-label')
                
                # Check for associated label
                has_label = False
                if input_id:
                    labels = soup.find_all('label', {'for': input_id})
                    has_label = len(labels) > 0
                
                if not has_label and not aria_label:
                    unlabeled_inputs += 1
            
            if unlabeled_inputs > 0:
                results["issues"].append(f"Form with {unlabeled_inputs} unlabeled inputs")
                accessibility_score -= 15
        
        # Check for skip links
        skip_links = soup.find_all('a', href=re.compile(r'#(main|content|skip)'))
        if not skip_links:
            results["issues"].append("No skip navigation links found")
            accessibility_score -= 10
        
        # Check for ARIA landmarks
        landmarks = soup.find_all(attrs={'role': re.compile(r'(main|navigation|banner|contentinfo)')})
        if len(landmarks) < 2:
            results["issues"].append("Few or no ARIA landmarks found")
            accessibility_score -= 10
        
        # Check for focus indicators (basic check)
        if ':focus' not in html_lower and 'outline' not in html_lower:
            results["issues"].append("No focus indicators detected in CSS")
            accessibility_score -= 10
        
        results["accessibility_score"] = max(25, accessibility_score)
    
    def _analyze_best_practices(self, soup, headers, html_lower, results, base_score):
        """Analyze best practices"""
        best_practices_score = base_score
        
        # Security headers
        security_headers = {
            'Strict-Transport-Security': 'HSTS header missing',
            'Content-Security-Policy': 'CSP header missing',
            'X-Content-Type-Options': 'X-Content-Type-Options missing',
            'X-Frame-Options': 'X-Frame-Options missing',
            'Referrer-Policy': 'Referrer-Policy missing'
        }
        
        missing_headers = []
        for header, message in security_headers.items():
            if header not in headers:
                missing_headers.append(message)
                best_practices_score -= 8
        
        if missing_headers:
            results["issues"].append(f"Security issues: {', '.join(missing_headers[:3])}")
        
        # Check for outdated libraries
        risky_patterns = [
            (r'jquery[/-]1\.[0-7]', 'Outdated jQuery version'),
            (r'bootstrap[/-]2\.', 'Outdated Bootstrap version'),
            (r'angular\.js@1\.[0-5]', 'Outdated AngularJS version')
        ]
        
        for pattern, message in risky_patterns:
            if re.search(pattern, html_lower):
                results["issues"].append(message)
                best_practices_score -= 15
                break
        
        # Check for proper doctype
        if not str(soup).startswith('<!DOCTYPE html>'):
            results["issues"].append("Missing or incorrect DOCTYPE")
            best_practices_score -= 10
        
        # Check for HTTPS
        if results.get("has_ssl", False):
            best_practices_score += 5
        else:
            best_practices_score -= 20
        
        # Check for mixed content
        if results.get("has_ssl", False) and 'http://' in html_lower:
            results["issues"].append("Mixed content detected (HTTP resources on HTTPS page)")
            best_practices_score -= 15
        
        results["best_practices_score"] = max(20, best_practices_score)
    
    def _analyze_content_quality(self, soup, results):
        """Analyze content quality factors"""
        # Word count analysis
        text_content = soup.get_text()
        word_count = len(text_content.split())
        
        if word_count < 300:
            results["issues"].append(f"Low content volume: {word_count} words")
        
        # Check for duplicate content indicators
        paragraphs = soup.find_all('p')
        if len(set(p.get_text() for p in paragraphs)) < len(paragraphs) * 0.8:
            results["issues"].append("Potential duplicate content detected")
    
    def _analyze_technical_seo(self, soup, url, results):
        """Analyze technical SEO factors"""
        # Check for canonical URL
        canonical = soup.find('link', {'rel': 'canonical'})
        if not canonical:
            results["issues"].append("Missing canonical URL")
        
        # Check for Open Graph tags
        og_tags = soup.find_all('meta', {'property': re.compile(r'^og:')})
        if len(og_tags) < 3:
            results["issues"].append("Few or missing Open Graph tags")
        
        # Check for structured data
        json_ld = soup.find_all('script', {'type': 'application/ld+json'})
        microdata = soup.find_all(attrs={'itemtype': True})
        if not json_ld and not microdata:
            results["issues"].append("No structured data found")
    
    def _analyze_user_experience(self, soup, results):
        """Analyze user experience factors"""
        # Check for contact information
        contact_indicators = ['contact', 'phone', 'email', 'address']
        page_text = soup.get_text().lower()
        
        contact_found = any(indicator in page_text for indicator in contact_indicators)
        if not contact_found:
            results["issues"].append("No obvious contact information found")
        
        # Check for search functionality
        search_inputs = soup.find_all('input', {'type': 'search'})
        search_forms = soup.find_all('form', class_=re.compile(r'search', re.I))
        if not search_inputs and not search_forms:
            results["issues"].append("No search functionality detected")
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                print(f"Error closing WebDriver: {e}")
            finally:
                self.driver = None

    def _calculate_priority(self, results):
        """
        Calculate priority based on analysis results

        Priority levels:
        1 - High priority (No website or critical issues)
        2 - Medium priority (Poor website)
        3 - Low priority (Good website)
        """
        # No website - always highest priority
        if "Error accessing website" in " ".join(results["issues"]):
            return 1

        # Initialize scores with weights for different factors
        weighted_scores = {
            "seo": results["seo_score"] * 0.4,  # SEO has highest weight (40%)
            "performance": results["performance_score"]
            * 0.3,  # Performance is second (30%)
            "accessibility": results["accessibility_score"]
            * 0.15,  # Accessibility (15%)
            "best_practices": results["best_practices_score"]
            * 0.15,  # Best practices (15%)
        }

        # Calculate weighted average score
        weighted_avg = sum(weighted_scores.values())

        # Count critical issues
        critical_seo_issues = any(
            issue in " ".join(results["issues"]).lower()
            for issue in [
                "missing meta description",
                "missing page title",
                "missing h1",
                "noindex",
                "redirect",
            ]
        )

        critical_security_issues = any(
            issue in " ".join(results["issues"]).lower()
            for issue in [
                "not using https",
                "missing security headers",
                "outdated library",
            ]
        )

        # Consider critical issues regardless of scores
        if results["seo_score"] < 40 or critical_seo_issues:
            return 2  # Always medium priority at least for major SEO issues

        # SSL is very important for modern websites
        if not results["has_ssl"]:
            return 2  # Medium priority if no SSL

        # Use the weighted score for the final determination
        if weighted_avg < 55 or len(results["issues"]) > 5 or critical_security_issues:
            return 2  # Medium priority (Poor website)

        # Good website
        return 3  # Low priority (Good website)
