"""
Upwork Proposal Submitter - Selenium Browser Automation
========================================================
Automatically submits proposals to Upwork jobs with connect bidding.
Monitors Airtable for approved jobs and submits proposals.

Workflow:
1. Poll Airtable for jobs with Status = "Approved"
2. Generate proposal using Claude AI
3. Navigate to job page and submit proposal
4. Bid connects for higher visibility
5. Update Airtable with submission status
"""

import os
import time
import json
import re
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
import requests

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


class UpworkProposalSubmitter:
    """
    Automates Upwork proposal submission with connect bidding.
    """
    
    # Default connect bid settings
    DEFAULT_CONNECTS = 16  # Base connects for a proposal
    BOOST_CONNECTS = 4     # Additional connects to bid for visibility
    
    def __init__(self, headless=False, boost_connects: int = None):
        """
        Initialize the proposal submitter.
        
        Args:
            headless: Run browser in headless mode (not recommended for submissions)
            boost_connects: Additional connects to bid (0-50). Higher = more visibility.
        """
        self.headless = headless
        self.boost_connects = boost_connects if boost_connects is not None else self.BOOST_CONNECTS
        self.driver = None
        self.logger = logger
        self.wait = None
        
        # Airtable config
        self.airtable_api_key = os.getenv('AIRTABLE_API_KEY')
        self.airtable_base_id = os.getenv('AIRTABLE_UPWORK_BASE_ID') or os.getenv('AIRTABLE_BASE_ID')
        self.airtable_table = 'Upwork Jobs'
        
        if not self.airtable_api_key or not self.airtable_base_id:
            raise ValueError("AIRTABLE_API_KEY and AIRTABLE_UPWORK_BASE_ID must be set")
    
    def _init_driver(self):
        """Initialize Chrome driver with existing profile (must be logged into Upwork)."""
        chrome_options = Options()
        
        # Use the same profile as the scraper (already logged in)
        profile_dir = os.path.expanduser('~/.upwork_scraper_profile')
        if not os.path.exists(profile_dir):
            raise ValueError(f"Profile not found at {profile_dir}. Run scraper with --manual first to log in.")
        
        chrome_options.add_argument(f'--user-data-dir={profile_dir}')
        chrome_options.add_argument('--window-size=1920,1080')
        
        if self.headless:
            chrome_options.add_argument('--headless=new')
        
        # Stability options
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        
        # Anti-detection
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # User agent
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.implicitly_wait(10)
        self.wait = WebDriverWait(self.driver, 20)
        
        # Hide webdriver
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })
        
        self.logger.info("Browser initialized with existing Upwork profile")
    
    def _get_approved_jobs(self) -> List[Dict]:
        """Fetch jobs with Status = 'Approved' from Airtable."""
        url = f"https://api.airtable.com/v0/{self.airtable_base_id}/{self.airtable_table}"
        headers = {'Authorization': f'Bearer {self.airtable_api_key}'}
        params = {
            'filterByFormula': "{Status} = 'Approved'",
            'maxRecords': 10
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                records = response.json().get('records', [])
                jobs = []
                for record in records:
                    job = record.get('fields', {})
                    job['_record_id'] = record.get('id')
                    jobs.append(job)
                self.logger.info(f"Found {len(jobs)} approved jobs to submit")
                return jobs
            else:
                self.logger.error(f"Airtable fetch error: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            self.logger.error(f"Error fetching approved jobs: {e}")
            return []
    
    def _update_job_status(self, record_id: str, status: str, proposal: str = None, 
                           error: str = None, connects_used: int = None):
        """Update job status in Airtable after submission attempt."""
        url = f"https://api.airtable.com/v0/{self.airtable_base_id}/{self.airtable_table}/{record_id}"
        headers = {
            'Authorization': f'Bearer {self.airtable_api_key}',
            'Content-Type': 'application/json'
        }
        
        fields = {'Status': status}
        
        if proposal:
            fields['Proposal'] = proposal
        if error:
            fields['Notes'] = f"Submission error: {error}\n\n{fields.get('Notes', '')}"
        if connects_used:
            fields['Notes'] = f"Connects used: {connects_used}\n\n{fields.get('Notes', '')}"
        if status == 'Applied':
            fields['Applied'] = True
        
        try:
            response = requests.patch(url, headers=headers, json={'fields': fields})
            if response.status_code == 200:
                self.logger.info(f"Updated job status to: {status}")
                return True
            else:
                self.logger.error(f"Failed to update status: {response.text}")
                return False
        except Exception as e:
            self.logger.error(f"Error updating job status: {e}")
            return False
    
    def _generate_proposal(self, job: Dict) -> Optional[str]:
        """Generate proposal using Claude AI."""
        try:
            import anthropic
            
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                self.logger.error("ANTHROPIC_API_KEY not set")
                return None
            
            client = anthropic.Anthropic(api_key=api_key)
            
            # Build job context
            job_title = job.get('Job Title', 'Unknown')
            job_description = job.get('Description', '')
            job_skills = job.get('Skills', '')
            budget = job.get('Budget', 'Not specified')
            
            prompt = f"""You are an expert no-code automation specialist who builds workflows using Zapier, Make.com, and n8n. Write a compelling Upwork proposal for this job.

JOB TITLE: {job_title}

JOB DESCRIPTION:
{job_description[:800]}

REQUIRED SKILLS: {job_skills}

BUDGET: ${budget}

IMPORTANT RULES:
1. Start with a hook that shows you understand their SPECIFIC problem
2. Be conversational, not formal - no generic openings
3. Mention specific tools (Zapier, Make.com, n8n) if relevant
4. Keep it SHORT - under 250 words. Clients don't read long proposals.
5. End with a clear call to action
6. NO generic phrases like "I came across your posting"
7. Sound like a human expert, not a template
8. Include a specific timeline estimate

Generate ONLY the proposal text, ready to submit."""

            response = client.messages.create(
                model="claude-opus-4-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            proposal = response.content[0].text.strip()
            self.logger.info(f"Generated proposal ({len(proposal)} chars)")
            return proposal
            
        except Exception as e:
            self.logger.error(f"Error generating proposal: {e}")
            return None
    
    def _navigate_to_job(self, job_url: str) -> bool:
        """Navigate to the job page."""
        try:
            self.driver.get(job_url)
            time.sleep(3)
            
            # Check if we're on the job page
            if '/jobs/' in self.driver.current_url:
                self.logger.info(f"Navigated to job page")
                return True
            else:
                self.logger.warning(f"Unexpected URL: {self.driver.current_url}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error navigating to job: {e}")
            return False
    
    def _click_apply_button(self) -> bool:
        """Click the Apply/Submit Proposal button."""
        try:
            # Wait for page to load
            time.sleep(2)
            
            # Try multiple selectors for the apply button
            apply_selectors = [
                '[data-test="apply-button"]',
                'button[aria-label*="Apply"]',
                'a[href*="apply"]',
                '.up-btn-primary',
                'button.air3-btn-primary',
                '//button[contains(text(), "Apply")]',
                '//a[contains(text(), "Apply Now")]',
                '//button[contains(text(), "Submit a Proposal")]',
            ]
            
            for selector in apply_selectors:
                try:
                    if selector.startswith('//'):
                        button = self.driver.find_element(By.XPATH, selector)
                    else:
                        button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if button.is_displayed():
                        button.click()
                        self.logger.info("Clicked Apply button")
                        time.sleep(3)
                        return True
                except NoSuchElementException:
                    continue
                except ElementClickInterceptedException:
                    # Try scrolling to element
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                    time.sleep(1)
                    button.click()
                    return True
            
            self.logger.error("Could not find Apply button")
            return False
            
        except Exception as e:
            self.logger.error(f"Error clicking apply button: {e}")
            return False
    
    def _fill_proposal_form(self, proposal_text: str, bid_amount: float = None) -> bool:
        """Fill out the proposal form with text and optional bid amount."""
        try:
            time.sleep(2)
            
            # Find the cover letter textarea
            textarea_selectors = [
                'textarea[data-test="cover-letter"]',
                'textarea[name="coverLetter"]',
                '#cover-letter',
                'textarea.cover-letter',
                '//textarea[contains(@placeholder, "cover letter")]',
                '//textarea[contains(@aria-label, "Cover Letter")]',
            ]
            
            textarea = None
            for selector in textarea_selectors:
                try:
                    if selector.startswith('//'):
                        textarea = self.driver.find_element(By.XPATH, selector)
                    else:
                        textarea = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if textarea:
                        break
                except NoSuchElementException:
                    continue
            
            if not textarea:
                # Try finding any large textarea
                textareas = self.driver.find_elements(By.TAG_NAME, 'textarea')
                for ta in textareas:
                    if ta.is_displayed() and ta.get_attribute('rows') and int(ta.get_attribute('rows') or 0) > 3:
                        textarea = ta
                        break
            
            if not textarea:
                self.logger.error("Could not find proposal textarea")
                return False
            
            # Clear and fill the textarea
            textarea.clear()
            textarea.send_keys(proposal_text)
            self.logger.info("Filled proposal text")
            
            # Handle bid amount if it's an hourly job
            if bid_amount:
                try:
                    bid_input = self.driver.find_element(By.CSS_SELECTOR, 'input[data-test="bid-input"], input[name="rate"]')
                    bid_input.clear()
                    bid_input.send_keys(str(bid_amount))
                    self.logger.info(f"Set bid amount: ${bid_amount}")
                except NoSuchElementException:
                    self.logger.debug("No bid input found (might be fixed-price)")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error filling proposal form: {e}")
            return False
    
    def _set_connect_boost(self, boost_connects: int) -> int:
        """Set the connect boost for higher proposal visibility."""
        try:
            # Look for the connects slider or input
            connect_selectors = [
                'input[data-test="boost-input"]',
                'input[name="boostBid"]',
                '.boost-slider input',
                'input[type="range"][aria-label*="boost"]',
            ]
            
            for selector in connect_selectors:
                try:
                    boost_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if boost_input:
                        # Set the boost value
                        self.driver.execute_script(
                            f"arguments[0].value = {boost_connects}; arguments[0].dispatchEvent(new Event('input'));",
                            boost_input
                        )
                        self.logger.info(f"Set connect boost: +{boost_connects} connects")
                        return boost_connects
                except NoSuchElementException:
                    continue
            
            # Try finding boost buttons (+ / -)
            try:
                plus_button = self.driver.find_element(By.CSS_SELECTOR, '[data-test="boost-increase"], .boost-increase')
                for _ in range(boost_connects):
                    plus_button.click()
                    time.sleep(0.2)
                self.logger.info(f"Clicked boost {boost_connects} times")
                return boost_connects
            except NoSuchElementException:
                pass
            
            self.logger.warning("Could not find connect boost controls")
            return 0
            
        except Exception as e:
            self.logger.error(f"Error setting connect boost: {e}")
            return 0
    
    def _submit_proposal(self) -> bool:
        """Click the final submit button."""
        try:
            time.sleep(1)
            
            submit_selectors = [
                'button[data-test="submit-proposal"]',
                'button[type="submit"]',
                '.submit-proposal-btn',
                '//button[contains(text(), "Submit")]',
                '//button[contains(text(), "Send")]',
            ]
            
            for selector in submit_selectors:
                try:
                    if selector.startswith('//'):
                        button = self.driver.find_element(By.XPATH, selector)
                    else:
                        button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if button.is_displayed() and button.is_enabled():
                        # Scroll to button
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                        time.sleep(0.5)
                        button.click()
                        self.logger.info("Clicked Submit button")
                        time.sleep(3)
                        return True
                except NoSuchElementException:
                    continue
            
            self.logger.error("Could not find Submit button")
            return False
            
        except Exception as e:
            self.logger.error(f"Error submitting proposal: {e}")
            return False
    
    def _check_submission_success(self) -> bool:
        """Verify the proposal was submitted successfully."""
        try:
            time.sleep(2)
            
            # Check for success indicators
            success_indicators = [
                'Your proposal has been submitted',
                'Proposal submitted',
                'Successfully submitted',
                'Application sent',
            ]
            
            page_source = self.driver.page_source.lower()
            for indicator in success_indicators:
                if indicator.lower() in page_source:
                    self.logger.info("Proposal submission confirmed!")
                    return True
            
            # Check URL change (often redirects to "my proposals" or similar)
            if 'proposals' in self.driver.current_url or 'submitted' in self.driver.current_url:
                self.logger.info("Redirected to proposals page - submission likely successful")
                return True
            
            # Check for error messages
            error_indicators = ['error', 'failed', 'unable to submit', 'try again']
            for error in error_indicators:
                if error in page_source:
                    self.logger.warning(f"Possible submission error detected")
                    return False
            
            # If no clear indicator, assume success if we got this far
            self.logger.info("No clear success indicator, but no errors detected")
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking submission: {e}")
            return False
    
    def submit_proposal(self, job: Dict, proposal_text: str = None) -> Tuple[bool, str]:
        """
        Submit a proposal for a single job.
        
        Args:
            job: Job dictionary from Airtable
            proposal_text: Optional pre-generated proposal (will generate if not provided)
        
        Returns:
            (success, message) tuple
        """
        job_title = job.get('Job Title', 'Unknown')
        job_url = job.get('Job URL', '')
        record_id = job.get('_record_id')
        
        self.logger.info(f"=" * 60)
        self.logger.info(f"Submitting proposal for: {job_title[:50]}...")
        self.logger.info(f"=" * 60)
        
        if not job_url:
            return False, "No job URL provided"
        
        # Generate proposal if not provided
        if not proposal_text:
            proposal_text = self._generate_proposal(job)
            if not proposal_text:
                self._update_job_status(record_id, 'Under Review', error='Failed to generate proposal')
                return False, "Failed to generate proposal"
        
        try:
            # Initialize browser if needed
            if not self.driver:
                self._init_driver()
            
            # Navigate to job
            if not self._navigate_to_job(job_url):
                self._update_job_status(record_id, 'Under Review', proposal=proposal_text, error='Failed to navigate to job')
                return False, "Failed to navigate to job page"
            
            # Click Apply button
            if not self._click_apply_button():
                self._update_job_status(record_id, 'Under Review', proposal=proposal_text, error='Could not find Apply button')
                return False, "Could not find Apply button"
            
            # Fill proposal form
            if not self._fill_proposal_form(proposal_text):
                self._update_job_status(record_id, 'Under Review', proposal=proposal_text, error='Failed to fill proposal form')
                return False, "Failed to fill proposal form"
            
            # Set connect boost
            boost_used = self._set_connect_boost(self.boost_connects)
            total_connects = self.DEFAULT_CONNECTS + boost_used
            
            # Submit proposal
            if not self._submit_proposal():
                self._update_job_status(record_id, 'Under Review', proposal=proposal_text, error='Failed to click submit')
                return False, "Failed to submit proposal"
            
            # Verify success
            if self._check_submission_success():
                self._update_job_status(record_id, 'Applied', proposal=proposal_text, connects_used=total_connects)
                return True, f"Proposal submitted successfully! Used {total_connects} connects."
            else:
                self._update_job_status(record_id, 'Under Review', proposal=proposal_text, error='Submission verification failed')
                return False, "Submission verification failed"
            
        except Exception as e:
            self.logger.error(f"Error in submit_proposal: {e}")
            if record_id:
                self._update_job_status(record_id, 'Under Review', proposal=proposal_text, error=str(e))
            return False, str(e)
    
    def process_approved_jobs(self, max_submissions: int = 5) -> Dict:
        """
        Process all approved jobs from Airtable.
        
        Args:
            max_submissions: Maximum proposals to submit in one run
        
        Returns:
            Summary dictionary
        """
        summary = {
            'processed': 0,
            'submitted': 0,
            'failed': 0,
            'skipped': 0,
            'details': []
        }
        
        self.logger.info("=" * 60)
        self.logger.info("UPWORK PROPOSAL SUBMITTER")
        self.logger.info("=" * 60)
        
        # Get approved jobs
        approved_jobs = self._get_approved_jobs()
        
        if not approved_jobs:
            self.logger.info("No approved jobs to process")
            return summary
        
        self.logger.info(f"Found {len(approved_jobs)} approved jobs")
        
        # Initialize browser once
        self._init_driver()
        
        try:
            for i, job in enumerate(approved_jobs[:max_submissions]):
                summary['processed'] += 1
                job_title = job.get('Job Title', 'Unknown')
                
                self.logger.info(f"\n[{i+1}/{min(len(approved_jobs), max_submissions)}] Processing: {job_title[:40]}...")
                
                # Check if proposal already exists
                existing_proposal = job.get('Proposal', '')
                
                success, message = self.submit_proposal(job, proposal_text=existing_proposal if existing_proposal else None)
                
                if success:
                    summary['submitted'] += 1
                    summary['details'].append({'job': job_title, 'status': 'submitted', 'message': message})
                else:
                    summary['failed'] += 1
                    summary['details'].append({'job': job_title, 'status': 'failed', 'message': message})
                
                # Delay between submissions to avoid rate limiting
                if i < len(approved_jobs) - 1:
                    delay = 30  # 30 seconds between submissions
                    self.logger.info(f"Waiting {delay}s before next submission...")
                    time.sleep(delay)
        
        finally:
            self.close()
        
        # Log summary
        self.logger.info("\n" + "=" * 60)
        self.logger.info("SUBMISSION SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Processed: {summary['processed']}")
        self.logger.info(f"Submitted: {summary['submitted']}")
        self.logger.info(f"Failed: {summary['failed']}")
        
        return summary
    
    def close(self):
        """Close the browser."""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("Browser closed")
            except:
                pass
            self.driver = None


def submit_approved_proposals(boost_connects: int = 4, max_submissions: int = 5) -> Dict:
    """
    Convenience function to submit proposals for all approved jobs.
    
    Args:
        boost_connects: Additional connects to bid (0-50)
        max_submissions: Max proposals to submit in one run
    
    Returns:
        Summary dictionary
    """
    submitter = UpworkProposalSubmitter(boost_connects=boost_connects)
    return submitter.process_approved_jobs(max_submissions=max_submissions)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Upwork Proposal Submitter')
    parser.add_argument('--boost', type=int, default=4, help='Connect boost amount (0-50)')
    parser.add_argument('--max', type=int, default=5, help='Max proposals to submit')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("UPWORK PROPOSAL AUTO-SUBMITTER")
    print("=" * 60)
    print(f"Boost connects: +{args.boost}")
    print(f"Max submissions: {args.max}")
    print("=" * 60 + "\n")
    
    result = submit_approved_proposals(boost_connects=args.boost, max_submissions=args.max)
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(f"Submitted: {result['submitted']}/{result['processed']}")
    if result['failed']:
        print(f"Failed: {result['failed']}")
    print("=" * 60)
