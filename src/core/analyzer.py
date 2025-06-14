"""
Website analyzer module using Lighthouse integration
"""

import os
import json
import time
import tempfile
import subprocess
import requests
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup


class WebsiteAnalyzer:
    """Website analysis with Lighthouse integration"""

    def __init__(self, use_lighthouse=True):
        """
        Initialize the analyzer

        Args:
            use_lighthouse: Whether to attempt to use Lighthouse
        """
        self.use_lighthouse = use_lighthouse
        self.lighthouse_available = (
            self._check_lighthouse() if use_lighthouse else False
        )

    def _check_lighthouse(self):
        """Check if Lighthouse dependencies are available"""
        try:
            # First check if Node.js is installed
            try:
                node_version = subprocess.run(
                    ["node", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if node_version.returncode != 0:
                    print("Node.js not found, installing Lighthouse not possible")
                    return False
            except (subprocess.SubprocessError, FileNotFoundError, OSError):
                print("Node.js not found, installing Lighthouse not possible")
                return False

            # Then check if npm is installed
            try:
                npm_version = subprocess.run(
                    ["npm", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if npm_version.returncode != 0:
                    print("npm not found, installing Lighthouse not possible")
                    return False
            except (subprocess.SubprocessError, FileNotFoundError, OSError):
                print("npm not found, installing Lighthouse not possible")
                return False

            # Check if Lighthouse is installed globally
            try:
                lighthouse_version = subprocess.run(
                    ["lighthouse", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if lighthouse_version.returncode != 0:
                    # Try to install Lighthouse globally
                    print("Lighthouse not found, attempting to install...")
                    install_result = subprocess.run(
                        ["npm", "install", "-g", "lighthouse"],
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                    if install_result.returncode != 0:
                        print("Failed to install Lighthouse")
                        return False
                    print("Lighthouse installed successfully")
            except Exception as e:
                print(f"Error checking/installing Lighthouse: {e}")
                return False

            # Check for Chrome
            chrome_paths = [
                os.path.join(
                    os.environ.get("PROGRAMFILES", "C:\\Program Files"),
                    "Google\\Chrome\\Application\\chrome.exe",
                ),
                os.path.join(
                    os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"),
                    "Google\\Chrome\\Application\\chrome.exe",
                )
            ]

            chrome_found = False
            for path in chrome_paths:
                if os.path.exists(path):
                    chrome_found = True
                    print(f"Chrome found at: {path}")
                    break

            if not chrome_found:
                print("Chrome not found, Lighthouse will use bundled Chromium")

            return True

        except Exception as e:
            print(f"Error during Lighthouse setup: {e}")
            return False

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

        # If Lighthouse is available, run it
        if self.lighthouse_available:
            print(f"Running Lighthouse analysis for {url}")
            lighthouse_results = self._run_lighthouse(url)
            if lighthouse_results:
                self._process_lighthouse_results(lighthouse_results, results)
                print(f"Lighthouse analysis completed for {url}")
            else:
                print(f"Lighthouse failed for {url}, falling back to basic analysis")
                self._perform_basic_analysis(url, results)
        else:
            print(f"Lighthouse not available, using basic analysis for {url}")
            results["issues"].append("Lighthouse not available for detailed analysis")
            # Perform basic web checks as fallback
            self._perform_basic_analysis(url, results)
        
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
            if self.use_lighthouse and hasattr(self, 'driver'):
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

    def _run_lighthouse(self, url):
        """Run Lighthouse analysis on a website using globally installed Lighthouse"""
        # Create a temporary file for the output
        fd, output_path = tempfile.mkstemp(suffix=".json")
        os.close(fd)

        try:
            # Run Lighthouse with minimal output categories and use bundled Chromium
            lighthouse_command = [
                "lighthouse",
                url,
                "--chrome-flags=--headless --no-sandbox --disable-gpu",
                "--output=json",
                "--output-path=" + output_path,
                "--only-categories=performance,accessibility,best-practices,seo",
                "--quiet",
                "--form-factor=desktop",  # Force desktop analysis
                "--throttling.cpuSlowdownMultiplier=2",  # Reduce CPU throttling
                "--max-wait-for-load=30000"  # 30 second page load timeout
            ]

            # Run the command with a timeout
            process = subprocess.run(
                lighthouse_command,
                capture_output=True,
                text=True,
                timeout=60  # 60 second total timeout
            )

            if process.returncode != 0:
                print(f"Lighthouse command failed with error: {process.stderr}")
                return None

            # Check if the output file exists and has content
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                try:
                    # Read and parse the JSON output
                    with open(output_path, "r", encoding='utf-8') as f:
                        lighthouse_data = json.load(f)
                    return lighthouse_data
                except json.JSONDecodeError as e:
                    print(f"Error parsing Lighthouse output: {e}")
                    return None
            else:
                print("Lighthouse didn't generate output")
                return None

        except subprocess.TimeoutExpired:
            print("Lighthouse analysis timed out")
            return None
        except Exception as e:
            print(f"Error running Lighthouse: {e}")
            return None
        finally:
            # Clean up the temporary file
            try:
                if os.path.exists(output_path):
                    os.unlink(output_path)
            except Exception as e:
                print(f"Error cleaning up temporary file: {e}")


    def _process_lighthouse_results(self, lighthouse_data, results):
        """Process Lighthouse results into our format"""
        try:
            # Extract category scores
            categories = lighthouse_data.get("categories", {})

            if "performance" in categories:
                results["performance_score"] = int(
                    categories["performance"]["score"] * 100
                )

            if "accessibility" in categories:
                results["accessibility_score"] = int(
                    categories["accessibility"]["score"] * 100
                )

            if "best-practices" in categories:
                results["best_practices_score"] = int(
                    categories["best-practices"]["score"] * 100
                )

            if "seo" in categories:
                results["seo_score"] = int(categories["seo"]["score"] * 100)

            # Extract important audits and issues
            audits = lighthouse_data.get("audits", {})

            # Performance issues
            if "largest-contentful-paint" in audits:
                lcp = audits["largest-contentful-paint"]
                if lcp.get("score", 1) < 0.5:
                    results["issues"].append(
                        f"Slow content loading (LCP: {lcp.get('displayValue')})"
                    )

            if "total-blocking-time" in audits:
                tbt = audits["total-blocking-time"]
                if tbt.get("score", 1) < 0.5:
                    results["issues"].append(
                        f"Poor interactivity (TBT: {tbt.get('displayValue')})"
                    )

            if "cumulative-layout-shift" in audits:
                cls = audits["cumulative-layout-shift"]
                if cls.get("score", 1) < 0.5:
                    results["issues"].append(
                        f"Layout shifts during loading (CLS: {cls.get('displayValue')})"
                    )

            # SEO issues
            if "meta-description" in audits:
                if audits["meta-description"].get("score", 1) < 0.5:
                    results["issues"].append("Missing meta description")

            if "document-title" in audits:
                if audits["document-title"].get("score", 1) < 0.5:
                    results["issues"].append("Missing or poor document title")

            # Additional SEO audits
            if "link-text" in audits:
                if audits["link-text"].get("score", 1) < 0.5:
                    results["issues"].append("Poor or generic link text")

            if "hreflang" in audits:
                if audits["hreflang"].get("score", 1) < 0.5:
                    results["issues"].append("Incorrect hreflang links")

            if "canonical" in audits:
                if audits["canonical"].get("score", 1) < 0.5:
                    results["issues"].append("Missing canonical link")

            if "robots-txt" in audits:
                if audits["robots-txt"].get("score", 1) < 0.5:
                    results["issues"].append("Problems with robots.txt")

            if "structured-data" in audits and "score" in audits["structured-data"]:
                if audits["structured-data"].get("score", 1) < 0.5:
                    results["issues"].append("Missing structured data")

            # Accessibility issues
            if "color-contrast" in audits:
                if audits["color-contrast"].get("score", 1) < 0.5:
                    results["issues"].append("Poor color contrast for text")

            if "image-alt" in audits:
                if audits["image-alt"].get("score", 1) < 0.5:
                    results["issues"].append("Images missing alt text")

            # Best Practices issues
            if "is-on-https" in audits:
                if audits["is-on-https"].get("score", 1) < 0.5:
                    results["issues"].append("Not using HTTPS")

            if "doctype" in audits:
                if audits["doctype"].get("score", 1) < 0.5:
                    results["issues"].append("Missing doctype")

        except Exception as e:
            results["issues"].append(f"Error processing Lighthouse results: {str(e)}")

    def _perform_basic_analysis(self, url, results):
        """Perform basic analysis as a fallback when Lighthouse is not available"""
        try:
            # Get the webpage
            response = requests.get(url, timeout=10)
            html = response.text.lower()

            # Check response headers
            headers = response.headers

            # Performance checks - Start with a good baseline
            performance_score = 75
            if len(response.content) > 1000000:  # 1MB
                results["issues"].append("Large page size")
                performance_score -= 25
            if results.get("load_time", 0) > 3:
                performance_score -= 15
            if results.get("load_time", 0) > 5:
                performance_score -= 15
            results["performance_score"] = max(30, performance_score)

            # SEO checks - Start with a good baseline
            seo_score = 75

            # Check for title
            if "<title>" not in html or "<title></title>" in html:
                results["issues"].append("Missing page title")
                seo_score -= 25
            
            # Check for meta description
            if 'meta name="description"' not in html and "meta content=" not in html:
                results["issues"].append("Missing meta description")
                seo_score -= 20
            
            # Check for heading structure
            if "<h1" not in html:
                results["issues"].append("Missing H1 heading")
                seo_score -= 15
            
            # Check for image alt text
            img_tags = html.count("<img")
            alt_attributes = html.count("alt=")
            if img_tags > 0 and alt_attributes < img_tags:
                results["issues"].append("Some images missing alt text")
                seo_score -= 10
            
            # Check for robots meta tag that blocks indexing
            if 'meta name="robots" content="noindex' in html:
                results["issues"].append(
                    "Page set to noindex - will not appear in search results"
                )
                seo_score -= 30
            
            # Check for SSL
            if not results.get("has_ssl", False):
                seo_score -= 15
            
            results["seo_score"] = max(25, seo_score)

            # Accessibility checks - Start with a good baseline
            accessibility_score = 70
            
            # Check for alt text on images
            if "<img " in html and (' alt="' not in html or " alt=" not in html):
                results["issues"].append("Images may be missing alt text")
                accessibility_score -= 20
            
            # Check for form labels
            if "<form" in html and "<label" not in html:
                results["issues"].append("Forms may be missing labels")
                accessibility_score -= 15
            
            # Check for proper heading hierarchy
            if "<h1" in html and "<h2" in html:
                accessibility_score += 5  # Bonus for good structure
            
            results["accessibility_score"] = max(30, accessibility_score)

            # Best practices checks - Start with a good baseline
            best_practices_score = 70
            
            # Check for HTTPS
            if results.get("has_ssl", False):
                best_practices_score += 10
            else:
                best_practices_score -= 20
            
            # Check for basic security headers
            security_headers = [
                "Strict-Transport-Security",
                "Content-Security-Policy", 
                "X-Content-Type-Options",
            ]
            missing_headers = [h for h in security_headers if h not in headers]
            
            if missing_headers:
                results["issues"].append(
                    f"Missing security headers: {', '.join(missing_headers)}"
                )
                best_practices_score -= (len(missing_headers) * 8)
            
            # Check for JavaScript libraries with known vulnerabilities
            risky_js_libs = ["jquery-1.", "jquery-2.0", "angular.js@1.", "bootstrap-2"]
            for risky_lib in risky_js_libs:
                if risky_lib in html:
                    results["issues"].append(
                        f"Using potentially outdated library: {risky_lib}"
                    )
                    best_practices_score -= 15
                    break
            
            # Check for proper doctype
            if "<!doctype html>" in html or "<!DOCTYPE html>" in response.text:
                best_practices_score += 5
            
            results["best_practices_score"] = max(25, best_practices_score)

        except Exception as e:
            results["issues"].append(f"Error during basic analysis: {str(e)}")

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
