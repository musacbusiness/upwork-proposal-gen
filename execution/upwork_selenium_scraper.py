"""
Upwork Job Scraper - Selenium with Cookie Authentication
=========================================================
Scrapes Upwork job listings using Selenium with pre-authenticated cookies.
Designed to run on Modal cloud with daily scheduling.

Usage:
1. Export your Upwork cookies using browser extension (Cookie-Editor)
2. Save cookies to Modal secrets
3. Deploy to Modal for daily scraping
"""

import json
import logging
import os
import re
import time
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import quote_plus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UpworkSeleniumScraper:
    """Scrape Upwork jobs using Selenium with cookie authentication"""
    
    # Search terms for AI/automation jobs
    SEARCH_TERMS = [
        "AI automation",
        "Make.com",
        "Zapier integration", 
        "n8n workflow",
        "no code automation",
        "workflow automation",
        "AI agent",
        "ChatGPT integration",
        "automation specialist",
        "API integration"
    ]
    
    def __init__(self, cookies: Optional[List[Dict]] = None, headless: bool = True):
        """
        Initialize scraper
        
        Args:
            cookies: List of cookie dictionaries from browser export
            headless: Run browser in headless mode
        """
        self.cookies = cookies or []
        self.headless = headless
        self.driver = None
        self.logger = logger
        
    def _init_driver(self):
        """Initialize Selenium WebDriver"""
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless=new")
        
        # Anti-detection settings
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Disable automation flags
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        
        # Remove webdriver property
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })
        
        self.logger.info("WebDriver initialized")
        
    def _load_cookies(self):
        """Load cookies into browser session"""
        if not self.cookies:
            self.logger.warning("No cookies provided")
            return False
            
        # First navigate to Upwork to set domain
        self.driver.get("https://www.upwork.com")
        time.sleep(2)
        
        # Clear existing cookies
        self.driver.delete_all_cookies()
        
        # Add cookies
        for cookie in self.cookies:
            try:
                # Ensure cookie has required fields
                cookie_dict = {
                    'name': cookie.get('name'),
                    'value': cookie.get('value'),
                    'domain': cookie.get('domain', '.upwork.com'),
                    'path': cookie.get('path', '/'),
                }
                
                # Add optional fields if present
                if cookie.get('secure'):
                    cookie_dict['secure'] = cookie['secure']
                if cookie.get('httpOnly'):
                    cookie_dict['httpOnly'] = cookie['httpOnly']
                    
                self.driver.add_cookie(cookie_dict)
            except Exception as e:
                self.logger.debug(f"Could not add cookie {cookie.get('name')}: {e}")
        
        self.logger.info(f"Loaded {len(self.cookies)} cookies")
        
        # Refresh to apply cookies
        self.driver.refresh()
        time.sleep(3)
        
        return True
        
    def _is_logged_in(self) -> bool:
        """Check if we're logged into Upwork"""
        try:
            # Navigate to a page that requires auth
            self.driver.get("https://www.upwork.com/nx/find-work/")
            time.sleep(3)
            
            # Check if we're on login page
            current_url = self.driver.current_url
            if "login" in current_url or "signup" in current_url:
                self.logger.warning("Not logged in - redirected to login page")
                return False
            
            # Check for job feed content
            page_source = self.driver.page_source
            if "Best Matches" in page_source or "Most Recent" in page_source or "job-tile" in page_source:
                self.logger.info("Successfully logged in")
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking login status: {e}")
            return False
    
    def _build_search_url(self, search_term: str, page: int = 1) -> str:
        """Build Upwork search URL"""
        encoded_term = quote_plus(search_term)
        base_url = f"https://www.upwork.com/nx/search/jobs/?q={encoded_term}"
        
        # Add filters for better results
        filters = [
            "sort=recency",  # Most recent first
            "contractor_tier=1,2,3",  # All experience levels
            "payment_verified=1",  # Payment verified clients
        ]
        
        if page > 1:
            filters.append(f"page={page}")
            
        return f"{base_url}&{'&'.join(filters)}"
    
    def _extract_jobs_from_page(self) -> List[Dict]:
        """Extract job listings from current page"""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        jobs = []
        
        try:
            # Wait for job tiles to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-test='job-tile-list']"))
            )
            time.sleep(2)  # Extra wait for dynamic content
            
            # Find all job tiles
            job_tiles = self.driver.find_elements(By.CSS_SELECTOR, "article[data-test='JobTile']")
            
            if not job_tiles:
                # Try alternative selector
                job_tiles = self.driver.find_elements(By.CSS_SELECTOR, "[data-ev-label='job_tile']")
            
            self.logger.info(f"Found {len(job_tiles)} job tiles on page")
            
            for tile in job_tiles:
                try:
                    job = self._parse_job_tile(tile)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    self.logger.debug(f"Error parsing job tile: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error extracting jobs: {e}")
            
        return jobs
    
    def _parse_job_tile(self, tile) -> Optional[Dict]:
        """Parse a single job tile element"""
        from selenium.webdriver.common.by import By
        
        try:
            # Extract job title and URL
            title_elem = tile.find_element(By.CSS_SELECTOR, "a[data-test='job-tile-title-link'], h2 a, .job-tile-title a")
            title = title_elem.text.strip()
            job_url = title_elem.get_attribute("href")
            
            # Extract job ID from URL
            job_id = None
            if job_url:
                match = re.search(r'/jobs/~(\w+)', job_url)
                if match:
                    job_id = match.group(1)
            
            # Extract description
            description = ""
            try:
                desc_elem = tile.find_element(By.CSS_SELECTOR, "[data-test='job-description-text'], .job-description, [data-test='UpCLineClamp JobDescription']")
                description = desc_elem.text.strip()
            except:
                pass
            
            # Extract budget
            budget = ""
            try:
                budget_elem = tile.find_element(By.CSS_SELECTOR, "[data-test='budget'], .budget, [data-test='is-fixed-price'], [data-test='job-type-label']")
                budget = budget_elem.text.strip()
            except:
                pass
            
            # Extract hourly rate if present
            try:
                hourly_elem = tile.find_element(By.CSS_SELECTOR, "[data-test='hourly-rate']")
                if hourly_elem:
                    budget = hourly_elem.text.strip()
            except:
                pass
            
            # Extract skills
            skills = []
            try:
                skill_elems = tile.find_elements(By.CSS_SELECTOR, "[data-test='token'], .skill-badge, [data-test='Skill']")
                skills = [s.text.strip() for s in skill_elems if s.text.strip()]
            except:
                pass
            
            # Extract posted time
            posted_at = ""
            try:
                time_elem = tile.find_element(By.CSS_SELECTOR, "[data-test='posted-on'], .posted-on, time")
                posted_at = time_elem.text.strip()
            except:
                pass
            
            # Extract client info
            client_info = {}
            try:
                # Payment verified
                verified_elems = tile.find_elements(By.CSS_SELECTOR, "[data-test='payment-verified'], .payment-verified")
                client_info['payment_verified'] = len(verified_elems) > 0
                
                # Client rating
                rating_elem = tile.find_elements(By.CSS_SELECTOR, "[data-test='client-rating'], .rating")
                if rating_elem:
                    client_info['rating'] = rating_elem[0].text.strip()
                    
                # Client spend
                spend_elem = tile.find_elements(By.CSS_SELECTOR, "[data-test='total-spent'], .total-spent")
                if spend_elem:
                    client_info['total_spent'] = spend_elem[0].text.strip()
                    
            except:
                pass
            
            # Extract proposals count
            proposals = ""
            try:
                proposals_elem = tile.find_element(By.CSS_SELECTOR, "[data-test='proposals'], .proposals")
                proposals = proposals_elem.text.strip()
            except:
                pass
            
            # Extract connects required
            connects = ""
            try:
                connects_elem = tile.find_element(By.CSS_SELECTOR, "[data-test='connects-required']")
                connects = connects_elem.text.strip()
            except:
                pass
            
            job = {
                "id": job_id,
                "title": title,
                "description": description,
                "budget": budget,
                "skills": skills,
                "url": job_url,
                "posted_at": posted_at,
                "proposals": proposals,
                "connects_required": connects,
                "client": client_info,
                "scraped_at": datetime.now().isoformat()
            }
            
            return job
            
        except Exception as e:
            self.logger.debug(f"Error parsing job tile: {e}")
            return None
    
    def scrape_jobs(
        self,
        search_terms: Optional[List[str]] = None,
        max_jobs_per_term: int = 20,
        max_pages_per_term: int = 3
    ) -> List[Dict]:
        """
        Scrape jobs for all search terms
        
        Args:
            search_terms: List of search terms (defaults to AI/automation terms)
            max_jobs_per_term: Max jobs to collect per search term
            max_pages_per_term: Max pages to scrape per term
            
        Returns:
            List of job dictionaries
        """
        if search_terms is None:
            search_terms = self.SEARCH_TERMS
            
        all_jobs = []
        seen_ids = set()
        
        try:
            # Initialize driver
            self._init_driver()
            
            # Load cookies and verify login
            if not self._load_cookies():
                self.logger.error("Failed to load cookies")
                return []
                
            if not self._is_logged_in():
                self.logger.error("Not logged in to Upwork - please update cookies")
                return []
            
            # Scrape each search term
            for term in search_terms:
                self.logger.info(f"Searching for: {term}")
                term_jobs = []
                
                for page in range(1, max_pages_per_term + 1):
                    if len(term_jobs) >= max_jobs_per_term:
                        break
                        
                    url = self._build_search_url(term, page)
                    self.logger.info(f"  Page {page}: {url}")
                    
                    try:
                        self.driver.get(url)
                        time.sleep(3)  # Wait for page load
                        
                        page_jobs = self._extract_jobs_from_page()
                        
                        # Deduplicate by job ID
                        for job in page_jobs:
                            if job['id'] and job['id'] not in seen_ids:
                                seen_ids.add(job['id'])
                                job['search_term'] = term
                                term_jobs.append(job)
                                
                        if not page_jobs:
                            self.logger.info(f"  No more jobs found on page {page}")
                            break
                            
                    except Exception as e:
                        self.logger.error(f"  Error on page {page}: {e}")
                        break
                    
                    # Rate limiting
                    time.sleep(2)
                
                all_jobs.extend(term_jobs[:max_jobs_per_term])
                self.logger.info(f"  Collected {len(term_jobs)} jobs for '{term}'")
                
                # Delay between search terms
                time.sleep(3)
            
            self.logger.info(f"Total jobs scraped: {len(all_jobs)}")
            return all_jobs
            
        except Exception as e:
            self.logger.error(f"Scraping error: {e}")
            return all_jobs
            
        finally:
            self.close()
    
    def close(self):
        """Close browser"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("Browser closed")
            except:
                pass


def export_cookies_instructions():
    """Print instructions for exporting Upwork cookies"""
    instructions = """
    ╔══════════════════════════════════════════════════════════════════╗
    ║          HOW TO EXPORT YOUR UPWORK COOKIES                       ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║                                                                  ║
    ║  1. Install "Cookie-Editor" browser extension                    ║
    ║     - Chrome: Search "Cookie-Editor" in Chrome Web Store         ║
    ║     - Firefox: Search "Cookie-Editor" in Add-ons                 ║
    ║                                                                  ║
    ║  2. Log into Upwork in your browser                              ║
    ║     - Make sure you're fully authenticated                       ║
    ║     - Navigate to https://www.upwork.com/nx/find-work/           ║
    ║                                                                  ║
    ║  3. Click Cookie-Editor extension icon                           ║
    ║                                                                  ║
    ║  4. Click "Export" button (bottom of popup)                      ║
    ║     - Choose "Export as JSON"                                    ║
    ║     - This copies cookies to clipboard                           ║
    ║                                                                  ║
    ║  5. Save to file:                                                ║
    ║     - Create file: ~/.upwork_cookies.json                        ║
    ║     - Paste the JSON content                                     ║
    ║                                                                  ║
    ║  6. Add to Modal secrets (for cloud deployment):                 ║
    ║     modal secret create upwork-cookies \\                         ║
    ║       UPWORK_COOKIES="$(cat ~/.upwork_cookies.json)"             ║
    ║                                                                  ║
    ║  IMPORTANT: Re-export cookies if scraping stops working          ║
    ║  (sessions expire after ~30 days)                                ║
    ║                                                                  ║
    ╚══════════════════════════════════════════════════════════════════╝
    """
    print(instructions)


def load_cookies_from_file(filepath: str = None) -> List[Dict]:
    """Load cookies from JSON file"""
    if filepath is None:
        filepath = os.path.expanduser("~/.upwork_cookies.json")
    
    try:
        with open(filepath, 'r') as f:
            cookies = json.load(f)
            logger.info(f"Loaded {len(cookies)} cookies from {filepath}")
            return cookies
    except FileNotFoundError:
        logger.error(f"Cookie file not found: {filepath}")
        export_cookies_instructions()
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in cookie file: {e}")
        return []


def load_cookies_from_env() -> List[Dict]:
    """Load cookies from environment variable (for Modal)"""
    cookies_json = os.environ.get("UPWORK_COOKIES")
    
    if not cookies_json:
        logger.error("UPWORK_COOKIES environment variable not set")
        return []
    
    try:
        cookies = json.loads(cookies_json)
        logger.info(f"Loaded {len(cookies)} cookies from environment")
        return cookies
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in UPWORK_COOKIES: {e}")
        return []


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Scrape Upwork jobs")
    parser.add_argument("--export-instructions", action="store_true", help="Show cookie export instructions")
    parser.add_argument("--cookies-file", type=str, help="Path to cookies JSON file")
    parser.add_argument("--headless", action="store_true", default=True, help="Run in headless mode")
    parser.add_argument("--max-jobs", type=int, default=20, help="Max jobs per search term")
    parser.add_argument("--output", type=str, default=".tmp/scraped_jobs.json", help="Output file path")
    
    args = parser.parse_args()
    
    if args.export_instructions:
        export_cookies_instructions()
        exit(0)
    
    # Load cookies
    if args.cookies_file:
        cookies = load_cookies_from_file(args.cookies_file)
    else:
        cookies = load_cookies_from_file()
    
    if not cookies:
        logger.error("No cookies available. Run with --export-instructions for help.")
        exit(1)
    
    # Initialize scraper
    scraper = UpworkSeleniumScraper(cookies=cookies, headless=args.headless)
    
    # Scrape jobs
    jobs = scraper.scrape_jobs(max_jobs_per_term=args.max_jobs)
    
    if jobs:
        # Save to file
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, 'w') as f:
            json.dump(jobs, f, indent=2)
        
        logger.info(f"✅ Saved {len(jobs)} jobs to {args.output}")
        
        # Print summary
        print("\n" + "="*60)
        print(f"SCRAPED {len(jobs)} JOBS")
        print("="*60)
        for job in jobs[:5]:
            print(f"\n📋 {job['title'][:60]}...")
            print(f"   💰 {job['budget']}")
            print(f"   🔗 {job['url']}")
    else:
        logger.error("No jobs scraped")
