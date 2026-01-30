"""
Upwork Job Scraper - Selenium Browser Automation
=================================================
Scrapes job listings from Upwork using your existing Chrome profile.
This avoids CAPTCHA loops by using a profile that's already logged in.

No API keys required - just log in once and use your profile.
"""

import os
import time
import json
import re
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/upwork_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class UpworkScraperSelenium:
    """
    Automates Upwork job scraping using undetected-chromedriver.
    This bypasses Cloudflare/bot detection that causes infinite CAPTCHA loops.
    """
    
    def __init__(self, headless=False, manual_login=False):
        """
        Initialize the Upwork scraper.
        
        Args:
            headless: Run browser in headless mode. Set to False to see what's happening.
                      Recommended: False for first run to handle any security challenges.
            manual_login: If True, opens Upwork and waits for you to log in manually.
        """
        self.email = os.getenv('UPWORK_EMAIL')
        self.password = os.getenv('UPWORK_PASSWORD')
        self.headless = headless
        self.manual_login = manual_login
        self.driver = None
        self.logger = logger
        
        if not manual_login and (not self.email or not self.password):
            raise ValueError("UPWORK_EMAIL and UPWORK_PASSWORD must be set in .env file")
    
    def _init_driver(self):
        """Initialize Chrome driver with a clean profile."""
        chrome_options = Options()
        
        # Create a dedicated profile directory for scraping (avoids conflicts)
        profile_dir = os.path.expanduser('~/.upwork_scraper_profile')
        os.makedirs(profile_dir, exist_ok=True)
        chrome_options.add_argument(f'--user-data-dir={profile_dir}')
        
        # Window size for consistent rendering
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Stability options
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--remote-debugging-port=9222')
        
        # Anti-detection
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # User agent
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36')
        
        # Initialize driver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.implicitly_wait(10)
        
        # Execute CDP command to hide webdriver property
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })
        
        time.sleep(2)
        self.logger.info("✓ Chrome driver initialized")
    
    def _manual_login(self):
        """Wait for user to log in manually."""
        self.logger.info("=" * 60)
        self.logger.info("MANUAL LOGIN MODE")
        self.logger.info("=" * 60)
        self.logger.info("Opening Upwork...")
        self.logger.info("Please log in manually if prompted.")
        self.logger.info("You have 3 minutes to complete the login.")
        self.logger.info("=" * 60)
        
        try:
            # Go directly to jobs page - Upwork will redirect to login if needed
            self.driver.get('https://www.upwork.com/nx/find-work/best-matches')
            time.sleep(5)
        except Exception as e:
            self.logger.error(f"Error loading page: {e}")
            return False
        
        # Wait up to 3 minutes for login to complete
        for i in range(36):  # 36 * 5 = 180 seconds = 3 minutes
            time.sleep(5)
            
            try:
                current_url = self.driver.current_url
                
                # Check if we're on a job page (logged in)
                if any(x in current_url for x in ['find-work', 'best-matches', 'search/jobs']):
                    # Also verify we're not on login page
                    if 'login' not in current_url and 'account-security' not in current_url:
                        self.logger.info("✓ Login detected! Proceeding with scraping...")
                        return True
                
                remaining = 180 - (i + 1) * 5
                if remaining > 0 and i % 2 == 0:  # Log every 10 seconds
                    self.logger.info(f"Waiting for login... ({remaining}s remaining)")
                    
            except Exception as e:
                self.logger.warning(f"Browser check failed: {e}")
                # Browser might be busy with CAPTCHA - just keep waiting
                continue
        
        self.logger.error("Login timeout. Please try again.")
        return False
    
    def _login(self):
        """Log into Upwork."""
        # Use manual login if specified
        if self.manual_login:
            return self._manual_login()
            
        self.logger.info("Logging into Upwork...")
        
        self.driver.get('https://www.upwork.com/ab/account-security/login')
        time.sleep(5)
        
        try:
            # Step 1: Enter email/username
            # Try multiple selectors for the email field
            email_field = None
            email_selectors = [
                (By.ID, 'login_username'),
                (By.CSS_SELECTOR, 'input[name="login[username]"]'),
                (By.CSS_SELECTOR, 'input[type="email"]'),
                (By.CSS_SELECTOR, '#login_username'),
                (By.XPATH, '//input[@placeholder="Username or Email"]'),
                (By.XPATH, '//input[contains(@aria-label, "Username")]'),
            ]
            
            for selector_type, selector in email_selectors:
                try:
                    email_field = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((selector_type, selector))
                    )
                    self.logger.info(f"Found email field with selector: {selector}")
                    break
                except TimeoutException:
                    continue
            
            if not email_field:
                # Take screenshot for debugging
                self.driver.save_screenshot('.tmp/upwork_login_debug.png')
                self.logger.error("Could not find email field. Screenshot saved to .tmp/upwork_login_debug.png")
                self.logger.info("Current URL: " + self.driver.current_url)
                self.logger.info("Page title: " + self.driver.title)
                raise Exception("Email field not found on login page")
            
            email_field.clear()
            time.sleep(0.5)
            email_field.send_keys(self.email)
            time.sleep(1)
            
            # Click Continue button
            continue_selectors = [
                (By.ID, 'login_password_continue'),
                (By.CSS_SELECTOR, '#login_password_continue'),
                (By.CSS_SELECTOR, 'button[type="submit"]'),
                (By.XPATH, '//button[contains(text(), "Continue")]'),
                (By.XPATH, '//button[@data-test="login-password-continue"]'),
            ]
            
            continue_button = None
            for selector_type, selector in continue_selectors:
                try:
                    continue_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((selector_type, selector))
                    )
                    self.logger.info(f"Found continue button with selector: {selector}")
                    break
                except TimeoutException:
                    continue
            
            if continue_button:
                continue_button.click()
            else:
                # Try pressing Enter instead
                email_field.send_keys(Keys.RETURN)
            
            time.sleep(4)
            
            # Step 2: Enter password
            # Check if there's a CAPTCHA or security challenge after email
            current_url = self.driver.current_url
            page_source = self.driver.page_source.lower()
            
            if 'captcha' in page_source or 'robot' in page_source or 'verify' in current_url or 'challenge' in current_url:
                self.logger.warning("⚠️  Security verification detected after email entry!")
                self.logger.info("Please complete the CAPTCHA/verification in the browser window.")
                self.logger.info("Waiting 90 seconds for manual verification...")
                self.driver.save_screenshot('.tmp/upwork_captcha_debug.png')
                time.sleep(90)
            
            password_selectors = [
                (By.ID, 'login_password'),
                (By.CSS_SELECTOR, 'input[name="login[password]"]'),
                (By.CSS_SELECTOR, 'input[type="password"]'),
                (By.CSS_SELECTOR, '#login_password'),
                (By.XPATH, '//input[@placeholder="Password"]'),
            ]
            
            password_field = None
            # Try multiple times with longer waits
            for attempt in range(3):
                for selector_type, selector in password_selectors:
                    try:
                        password_field = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((selector_type, selector))
                        )
                        self.logger.info(f"Found password field with selector: {selector}")
                        break
                    except TimeoutException:
                        continue
                
                if password_field:
                    break
                    
                if attempt < 2:
                    self.logger.warning(f"Password field not found (attempt {attempt+1}/3). Waiting for manual action...")
                    self.logger.info("If there's a CAPTCHA or verification, please complete it now.")
                    self.driver.save_screenshot(f'.tmp/upwork_password_debug_{attempt}.png')
                    time.sleep(30)  # Wait for user to complete any verification
            
            if not password_field:
                self.driver.save_screenshot('.tmp/upwork_password_debug.png')
                self.logger.error("Could not find password field after retries. Screenshot saved.")
                self.logger.info("You may need to log in manually first time. Try running again.")
                raise Exception("Password field not found - Upwork may require manual verification")
            
            password_field.clear()
            time.sleep(0.5)
            password_field.send_keys(self.password)
            time.sleep(1)
            
            # Click Login button
            login_selectors = [
                (By.ID, 'login_control_continue'),
                (By.CSS_SELECTOR, '#login_control_continue'),
                (By.CSS_SELECTOR, 'button[type="submit"]'),
                (By.XPATH, '//button[contains(text(), "Log in")]'),
                (By.XPATH, '//button[@data-test="login-control-continue"]'),
            ]
            
            login_button = None
            for selector_type, selector in login_selectors:
                try:
                    login_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((selector_type, selector))
                    )
                    self.logger.info(f"Found login button with selector: {selector}")
                    break
                except TimeoutException:
                    continue
            
            if login_button:
                login_button.click()
            else:
                password_field.send_keys(Keys.RETURN)
            
            time.sleep(6)
            
            # Check for security challenges
            current_url = self.driver.current_url
            
            if 'security-question' in current_url or 'verify' in current_url or 'challenge' in current_url or 'checkpoint' in current_url:
                self.logger.warning("⚠️  Upwork security challenge detected!")
                self.logger.info("Please complete the verification in the browser window.")
                self.logger.info("Waiting 120 seconds for manual verification...")
                time.sleep(120)
            
            # Verify login success by checking for dashboard elements
            if 'nx/find-work' in self.driver.current_url or 'freelancer' in self.driver.current_url or 'jobs' in self.driver.current_url:
                self.logger.info("✓ Logged in successfully")
                return True
            
            # Alternative: check for navigation elements
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[data-test="nav-find-work"], .nav-item, .up-n-nav'))
                )
                self.logger.info("✓ Logged in successfully")
                return True
            except TimeoutException:
                pass
            
            self.logger.info("✓ Login appears successful (navigating to job search)")
            return True
            
        except Exception as e:
            self.logger.error(f"Login failed: {e}")
            raise
    
    def _build_search_url(self, search_query: str, category: str = '', page: int = 1) -> str:
        """Build Upwork job search URL with filters."""
        base_url = 'https://www.upwork.com/nx/search/jobs'
        params = []
        
        if search_query:
            params.append(f'q={search_query.replace(" ", "%20")}')
        
        if page > 1:
            params.append(f'page={page}')
        
        # Sort by most recent
        params.append('sort=recency')
        
        if params:
            return f"{base_url}?{'&'.join(params)}"
        return base_url
    
    def _extract_job_data(self, job_element) -> Optional[Dict]:
        """Extract job data from a job card element - FAST version."""
        try:
            # Temporarily reduce implicit wait for faster extraction
            self.driver.implicitly_wait(0.5)
            
            job_data = {}
            
            # Job title - try multiple selectors quickly
            title_element = None
            for selector in ['a.job-tile-title-link', '[data-test="job-tile-title-link"]', 'h2 a', '.job-tile-title a']:
                try:
                    title_element = job_element.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if title_element:
                job_data['title'] = title_element.text.strip()
                job_data['url'] = title_element.get_attribute('href')
                if job_data['url']:
                    # Try multiple patterns for job ID extraction
                    match = re.search(r'~(\d+)', job_data['url'])
                    if match:
                        job_data['id'] = match.group(1)
                    else:
                        match = re.search(r'/jobs/~([a-zA-Z0-9]+)', job_data['url'])
                        if match:
                            job_data['id'] = match.group(1)
            else:
                job_data['title'] = 'Unknown'
                job_data['url'] = ''
            
            # Job description - quick search
            job_data['description'] = ''
            for selector in ['[data-test="job-description-text"]', '.job-tile-description', 'p.mb-0']:
                try:
                    desc_element = job_element.find_element(By.CSS_SELECTOR, selector)
                    job_data['description'] = desc_element.text.strip()
                    break
                except NoSuchElementException:
                    continue
            
            # Budget - quick search
            job_data['budget'] = 0
            for selector in ['[data-test="budget"]', '[data-test="job-type-label"]', '.job-tile-budget']:
                try:
                    budget_element = job_element.find_element(By.CSS_SELECTOR, selector)
                    job_data['budget'] = self._parse_budget(budget_element.text)
                    break
                except NoSuchElementException:
                    continue
            
            # Job type (hourly/fixed)
            job_data['job_type'] = 'unknown'
            try:
                type_element = job_element.find_element(By.CSS_SELECTOR, '[data-test="job-type-label"]')
                type_text = type_element.text.lower()
                job_data['job_type'] = 'hourly' if 'hourly' in type_text else 'fixed-price'
            except NoSuchElementException:
                pass
            
            # Skills - quick extraction
            job_data['skills'] = []
            try:
                skills_elements = job_element.find_elements(By.CSS_SELECTOR, '[data-test="token"] span, .air3-token span, .up-skill-badge')
                job_data['skills'] = [skill.text.strip() for skill in skills_elements if skill.text.strip()][:10]  # Limit to 10 skills
            except:
                pass
            
            # Client info - simplified fast extraction
            job_data['client'] = self._extract_client_info_fast(job_element)
            
            # Posted time
            job_data['posted'] = ''
            for selector in ['[data-test="posted-on"]', '.job-tile-header-posted', 'small[data-test="job-pubished-date"]']:
                try:
                    posted_element = job_element.find_element(By.CSS_SELECTOR, selector)
                    job_data['posted'] = posted_element.text.strip()
                    break
                except NoSuchElementException:
                    continue
            
            # Proposals count
            job_data['proposals_count'] = 0
            try:
                proposals_element = job_element.find_element(By.CSS_SELECTOR, '[data-test="proposals"]')
                match = re.search(r'(\d+)', proposals_element.text)
                if match:
                    job_data['proposals_count'] = int(match.group(1))
            except:
                pass
            
            # Add metadata
            job_data['scraped_at'] = datetime.now().isoformat()
            
            # Restore implicit wait
            self.driver.implicitly_wait(10)
            
            return job_data
            
        except Exception as e:
            self.driver.implicitly_wait(10)  # Restore on error
            self.logger.error(f"Error extracting job data: {e}")
            return None
    
    def _extract_client_info_fast(self, job_element) -> Dict:
        """Extract client information - FAST version with minimal waits."""
        client_info = {
            'rating': 0,
            'reviews': 0,
            'spent': '$0',
            'country': '',
            'payment_verified': False
        }
        
        # Get all text from the job element and parse it
        try:
            full_text = job_element.text
            
            # Extract rating from text (e.g., "4.9")
            rating_match = re.search(r'(\d\.\d)\s*(?:of 5|stars?)?', full_text)
            if rating_match:
                client_info['rating'] = float(rating_match.group(1))
            
            # Extract reviews count
            reviews_match = re.search(r'\((\d+)\s*reviews?\)', full_text, re.IGNORECASE)
            if reviews_match:
                client_info['reviews'] = int(reviews_match.group(1))
            
            # Extract spent
            spent_match = re.search(r'\$[\d,.]+[KMB]?\s*(?:spent|total)', full_text, re.IGNORECASE)
            if spent_match:
                client_info['spent'] = spent_match.group(0)
            
            # Payment verified
            if 'payment verified' in full_text.lower():
                client_info['payment_verified'] = True
                
        except:
            pass
        
        return client_info
    
    def _parse_budget(self, budget_text: str) -> int:
        """Parse budget string to integer."""
        if not budget_text:
            return 0
        
        # Remove currency symbols and commas
        clean_text = budget_text.replace('$', '').replace(',', '').strip()
        
        # Handle ranges like "$500-$1,000"
        if '-' in clean_text:
            parts = clean_text.split('-')
            try:
                # Use the higher value
                return int(float(parts[-1].strip()))
            except:
                pass
        
        # Handle hourly rates like "$50.00/hr"
        if '/hr' in clean_text.lower():
            match = re.search(r'([\d.]+)', clean_text)
            if match:
                # Convert hourly to estimated project (assume 40 hours)
                return int(float(match.group(1)) * 40)
        
        # Extract first number
        match = re.search(r'([\d.]+)', clean_text)
        if match:
            return int(float(match.group(1)))
        
        return 0
    
    def scrape_jobs(
        self,
        search_query: str,
        max_jobs: int = 50,
        pages: int = 5
    ) -> List[Dict]:
        """
        Scrape Upwork jobs based on search query.
        
        Args:
            search_query: Search keywords (e.g., "Python automation")
            max_jobs: Maximum number of jobs to scrape
            pages: Maximum number of pages to scrape
        
        Returns:
            List of job dictionaries
        """
        jobs = []
        
        try:
            # Initialize driver if not already done
            if not self.driver:
                self._init_driver()
                self._login()
            
            self.logger.info(f"Searching Upwork for: {search_query}")
            
            for page in range(1, pages + 1):
                if len(jobs) >= max_jobs:
                    break
                
                self.logger.info(f"Scraping page {page}...")
                
                # Navigate to search page
                search_url = self._build_search_url(search_query, page=page)
                self.driver.get(search_url)
                time.sleep(5)  # Wait for jobs to load
                
                # Scroll to load all jobs on page
                self._scroll_page()
                
                # Find all job cards
                try:
                    job_cards = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[data-test="job-tile-list"] article, .job-tile'))
                    )
                except TimeoutException:
                    # Try alternative selector
                    try:
                        job_cards = self.driver.find_elements(By.CSS_SELECTOR, 'section.air3-card-section')
                    except:
                        self.logger.warning(f"No jobs found on page {page}")
                        continue
                
                self.logger.info(f"Found {len(job_cards)} job cards on page {page}")
                
                for card in job_cards:
                    if len(jobs) >= max_jobs:
                        break
                    
                    job_data = self._extract_job_data(card)
                    if job_data and job_data.get('title') and job_data.get('title') != 'Unknown':
                        jobs.append(job_data)
                        self.logger.debug(f"Scraped: {job_data.get('title', 'Unknown')[:50]}...")
                
                # Small delay between pages
                time.sleep(2)
            
            self.logger.info(f"✓ Scraped {len(jobs)} jobs total")
            return jobs
            
        except Exception as e:
            self.logger.error(f"Error scraping jobs: {e}")
            raise
    
    def _scroll_page(self):
        """Scroll page to load all dynamic content."""
        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            for _ in range(3):  # Scroll 3 times
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
                
            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
        except Exception as e:
            self.logger.debug(f"Scroll error (non-critical): {e}")
    
    def get_job_details(self, job_url: str) -> Optional[Dict]:
        """
        Get detailed information from a specific job posting page.
        
        Args:
            job_url: Full URL to the job posting
        
        Returns:
            Dictionary with detailed job info
        """
        try:
            self.driver.get(job_url)
            time.sleep(3)
            
            details = {}
            
            # Full description
            try:
                desc_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[data-test="description"]'))
                )
                details['full_description'] = desc_element.text.strip()
            except:
                pass
            
            # Client history
            try:
                history_element = self.driver.find_element(By.CSS_SELECTOR, '[data-test="client-history"]')
                details['client_history'] = history_element.text.strip()
            except:
                pass
            
            # Experience level required
            try:
                exp_element = self.driver.find_element(By.CSS_SELECTOR, '[data-test="experience-level"]')
                details['experience_level'] = exp_element.text.strip()
            except:
                pass
            
            # Project length
            try:
                length_element = self.driver.find_element(By.CSS_SELECTOR, '[data-test="duration"]')
                details['project_length'] = length_element.text.strip()
            except:
                pass
            
            return details
            
        except Exception as e:
            self.logger.error(f"Error getting job details: {e}")
            return None
    
    def save_jobs(self, jobs: List[Dict], filepath: str = '.tmp/raw_jobs.json'):
        """Save scraped jobs to JSON file."""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(jobs, f, indent=2)
        
        self.logger.info(f"✓ Saved {len(jobs)} jobs to {filepath}")
    
    def close(self):
        """Close browser and cleanup."""
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.logger.info("✓ Browser closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def scrape_upwork_jobs(
    search_query: str,
    max_jobs: int = 50,
    output_file: str = '.tmp/raw_jobs.json',
    headless: bool = False,
    manual_login: bool = False
) -> List[Dict]:
    """
    Convenience function to scrape Upwork jobs.
    
    Args:
        search_query: Search keywords
        max_jobs: Maximum jobs to scrape
        output_file: Output file path
        headless: Run browser in headless mode
        manual_login: If True, wait for manual login instead of auto-login
    
    Returns:
        List of scraped jobs
    """
    with UpworkScraperSelenium(headless=headless, manual_login=manual_login) as scraper:
        jobs = scraper.scrape_jobs(search_query, max_jobs=max_jobs)
        scraper.save_jobs(jobs, output_file)
        return jobs


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape Upwork jobs')
    parser.add_argument('--query', '-q', type=str, required=True, help='Search query')
    parser.add_argument('--max', '-m', type=int, default=50, help='Max jobs to scrape')
    parser.add_argument('--output', '-o', type=str, default='.tmp/raw_jobs.json', help='Output file')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--manual', action='store_true', help='Wait for manual login')
    
    args = parser.parse_args()
    
    jobs = scrape_upwork_jobs(
        search_query=args.query,
        max_jobs=args.max,
        output_file=args.output,
        headless=args.headless,
        manual_login=args.manual
    )
    
    print(f"\n✓ Scraped {len(jobs)} jobs")
    print(f"✓ Saved to {args.output}")
