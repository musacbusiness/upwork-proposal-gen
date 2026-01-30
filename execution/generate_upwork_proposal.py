#!/usr/bin/env python3
"""
Upwork Proposal Generator
Takes an Upwork job URL, extracts job details, and generates a personalized proposal
using Claude API with your authentic voice and experience profile.

Usage:
    python generate_upwork_proposal.py "https://www.upwork.com/jobs/..."

Output:
    Proposal copied to clipboard, ready to paste into Upwork
"""

import sys
import os
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
import subprocess

# Third-party imports
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import anthropic

# Try to import webdriver-manager for automatic driver management
try:
    from webdriver_manager.chrome import ChromeDriverManager
    HAS_WEBDRIVER_MANAGER = True
except ImportError:
    HAS_WEBDRIVER_MANAGER = False

# Setup logging
log_dir = Path(".tmp")
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "upwork_proposal_log.txt"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class UpworkScraper:
    """Scrapes Upwork job details from a job URL"""

    def __init__(self):
        self.driver = None
        self.wait = None

    def setup_driver(self):
        """Initialize Selenium WebDriver with Chrome"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")

        try:
            # Try using webdriver-manager if available
            if HAS_WEBDRIVER_MANAGER:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                # Fallback to default chromedriver search
                self.driver = webdriver.Chrome(options=chrome_options)

            self.wait = WebDriverWait(self.driver, 10)
            logger.info("✓ Selenium WebDriver initialized")
        except Exception as e:
            logger.error(f"✗ Failed to initialize WebDriver: {e}")
            logger.error("ℹ Install chromedriver or webdriver-manager to enable web scraping")
            raise

    def scrape_job(self, url: str) -> Optional[Dict]:
        """
        Scrape job details from Upwork job URL

        Args:
            url: Upwork job URL

        Returns:
            Dict with job details or None if scraping fails
        """
        if not self.driver:
            self.setup_driver()

        try:
            logger.info(f"→ Navigating to: {url}")
            self.driver.get(url)

            # Wait for main job content to load
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "job-details")))
            time.sleep(2)  # Extra wait for dynamic content

            job_data = self._extract_job_details()
            logger.info(f"✓ Successfully scraped job: {job_data.get('title', 'Unknown')}")
            return job_data

        except TimeoutException:
            logger.error("✗ Timeout: Job page took too long to load")
            return None
        except Exception as e:
            logger.error(f"✗ Scraping failed: {e}")
            return None
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None

    def _extract_job_details(self) -> Dict:
        """Extract job details from the loaded page"""
        details = {}

        try:
            # Extract job title
            try:
                title = self.driver.find_element(By.CSS_SELECTOR, 'h1[class*="title"]').text
                details['title'] = title.strip()
            except NoSuchElementException:
                details['title'] = "Unknown Job Title"

            # Extract job description
            try:
                description_elem = self.driver.find_element(By.CSS_SELECTOR, '[class*="description"]')
                details['description'] = description_elem.text.strip()
            except NoSuchElementException:
                details['description'] = ""

            # Extract budget
            try:
                budget_elem = self.driver.find_element(By.CSS_SELECTOR, '[class*="budget"]')
                details['budget'] = budget_elem.text.strip()
            except NoSuchElementException:
                details['budget'] = "Not specified"

            # Extract level/experience
            try:
                level_elem = self.driver.find_element(By.CSS_SELECTOR, '[class*="level"]')
                details['level'] = level_elem.text.strip()
            except NoSuchElementException:
                details['level'] = "Not specified"

            # Extract required skills
            try:
                skills_elements = self.driver.find_elements(By.CSS_SELECTOR, '[class*="skill"]')
                details['skills'] = [skill.text.strip() for skill in skills_elements[:10]]
            except NoSuchElementException:
                details['skills'] = []

            # Extract job category
            try:
                category_elem = self.driver.find_element(By.CSS_SELECTOR, '[class*="category"]')
                details['category'] = category_elem.text.strip()
            except NoSuchElementException:
                details['category'] = "Not specified"

            # Extract client info
            try:
                client_name = self.driver.find_element(By.CSS_SELECTOR, '[class*="client-name"]').text
                details['client_name'] = client_name.strip()
            except NoSuchElementException:
                details['client_name'] = "Not available"

            # Extract number of proposals
            try:
                proposals_elem = self.driver.find_element(By.CSS_SELECTOR, '[class*="proposals"]')
                details['num_proposals'] = proposals_elem.text.strip()
            except NoSuchElementException:
                details['num_proposals'] = "Not available"

            # Extract job ID from URL
            details['job_id'] = self.driver.current_url.split('/')[-1].split('~')[0]

            return details

        except Exception as e:
            logger.warning(f"⚠ Error extracting some job details: {e}")
            return details


class ProposalGenerator:
    """Generates personalized proposals using Claude API with your voice profile"""

    # Your voice profile and experience - from VOICE_DISCOVERY_CONVERSATION.md
    VOICE_PROFILE = """
    You are Musa Comma, a 23-year-old founder and automation expert. Your communication style:

    CORE TRAITS:
    - Analytical + willing to take leaps of faith when worst case is survivable
    - Direct, no fluff - calls out BS clearly
    - Truth-focused - authenticity over polish
    - Client-centric - success = clients winning (scaling, saving time, more money)
    - Numbers-driven - use concrete examples and metrics

    YOUR EXPERIENCE:
    - Founded MC Marketing Solutions (2019-2023): Learned that low-budget clients can't see ROI. Businesses need structure & automation.
    - Founder of ScaleAxis (2024-present): Building AI-powered automation platform focusing on business optimization, time savings, team amplification, operational scaling.
    - Background: Business automation, AI integration, market analysis, strategic thinking. Marketing communication skills (still developing).

    YOUR WORLDVIEW:
    - Real software > Platform constraints (vs. no-code tools that limit you)
    - Opportunity cost + speed-to-payback + potential = how you frame decisions
    - Fear is eliminated through reframing: if worst case is survivable AND you learn from it, fear has nowhere to land

    HOW YOU TALK:
    1. Open with their pain point (show you understand the problem)
    2. Make it concrete - use numbers and real scenarios
    3. Explain the opportunity cost of NOT acting
    4. Show ROI/speed-to-payback (how fast does this pay for itself?)
    5. Paint the potential (what becomes possible?)
    6. Keep it direct and honest - no hype, no exaggeration
    7. Show your relevant experience (don't oversell, just state facts)

    PROPOSAL TONE:
    - Professional but direct (like talking to a peer, not a guru)
    - Blunt when necessary (call out the real issue, not the symptom)
    - Strategic (shows you think beyond the immediate task)
    - Concrete (numbers, specific examples, realistic timelines)
    - Confident but not arrogant (you know your approach works, but you're not god)
    """

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def generate_proposal(self, job_data: Dict) -> Optional[str]:
        """
        Generate a personalized proposal using Claude API

        Args:
            job_data: Dict with job details from scraper

        Returns:
            Generated proposal text or None if generation fails
        """
        try:
            # Build the prompt
            prompt = self._build_prompt(job_data)

            logger.info("→ Generating proposal with Claude API...")

            message = self.client.messages.create(
                model="claude-opus-4-5-20251101",  # Using the most capable model for best quality
                max_tokens=1024,
                temperature=0.7,  # Slight variation to sound natural, not robotic
                system=self.VOICE_PROFILE,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            proposal = message.content[0].text.strip()
            logger.info("✓ Proposal generated successfully")
            return proposal

        except Exception as e:
            logger.error(f"✗ Proposal generation failed: {e}")
            return None

    def _build_prompt(self, job_data: Dict) -> str:
        """Build the prompt for Claude to generate a proposal"""

        job_title = job_data.get('title', 'Unknown')
        job_desc = job_data.get('description', '')
        budget = job_data.get('budget', 'Not specified')
        skills = ', '.join(job_data.get('skills', [])[:5]) if job_data.get('skills') else 'Not specified'
        level = job_data.get('level', 'Not specified')

        prompt = f"""You are writing a proposal for an Upwork job.

JOB DETAILS:
Title: {job_title}
Budget: {budget}
Experience Level Needed: {level}
Skills Required: {skills}
Full Description: {job_desc}

WRITE A PROPOSAL:
- Length: 150-250 words (should read in under 2 minutes)
- Structure: Opening (their pain point) → Why you're a fit → Your approach → Outcome → Next steps
- Tone: Direct, professional, numbers-focused. Show you understand their problem.
- Include: At least one concrete number/metric/ROI calculation
- Be authentic: No fluff, no "excited to help" clichés. Show you think this way.
- Personalize: Reference something specific from their job description that shows you read it

The proposal will be copied directly into Upwork, so write it as if you're speaking to them directly.
Start with the proposal text only - no intro, no closing, just the proposal."""

        return prompt


class ClipboardManager:
    """Handles copying text to system clipboard"""

    @staticmethod
    def copy_to_clipboard(text: str) -> bool:
        """
        Copy text to system clipboard

        Args:
            text: Text to copy

        Returns:
            True if successful, False otherwise
        """
        try:
            # Try pbcopy (macOS)
            process = subprocess.Popen(
                ['pbcopy'],
                stdin=subprocess.PIPE,
                env={'LANG': 'en_US.UTF-8'}
            )
            process.communicate(text.encode('utf-8'))
            process.wait()
            logger.info("✓ Proposal copied to clipboard (macOS)")
            return True
        except Exception as e:
            try:
                # Fallback: Try xclip (Linux)
                process = subprocess.Popen(
                    ['xclip', '-selection', 'clipboard'],
                    stdin=subprocess.PIPE
                )
                process.communicate(text.encode('utf-8'))
                process.wait()
                logger.info("✓ Proposal copied to clipboard (Linux)")
                return True
            except Exception as e2:
                logger.warning(f"⚠ Could not copy to clipboard: {e}, {e2}")
                return False


class UpworkProposalGenerator:
    """Main orchestrator for the entire flow"""

    def __init__(self):
        self.scraper = UpworkScraper()
        self.generator = ProposalGenerator()
        self.proposals_dir = Path(".tmp/proposals")
        self.proposals_dir.mkdir(parents=True, exist_ok=True)

    def run(self, url: str) -> bool:
        """
        Main execution flow: Scrape → Generate → Copy

        Args:
            url: Upwork job URL

        Returns:
            True if successful, False otherwise
        """
        logger.info("=" * 60)
        logger.info("UPWORK PROPOSAL GENERATOR")
        logger.info("=" * 60)

        # Step 1: Scrape job details
        logger.info("\n[1/3] SCRAPING JOB DETAILS...")
        job_data = self.scraper.scrape_job(url)

        # If scraping fails, offer fallback
        if not job_data or not job_data.get('description'):
            logger.warning("\n⚠ Web scraping didn't work (may need authentication or chromedriver).")
            logger.warning("→ Fallback: Paste the job description below and press Ctrl+D (Mac: Cmd+D) when done:\n")

            try:
                description = sys.stdin.read().strip()
                if not description:
                    logger.error("✗ No job description provided.")
                    return False

                job_data = job_data or {}
                job_data['description'] = description
                job_data['title'] = job_data.get('title', 'Upwork Job')
                job_data['job_id'] = job_data.get('job_id', 'manual_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
                logger.info("✓ Job description received")
            except (EOFError, KeyboardInterrupt):
                logger.error("✗ No description provided. Exiting.")
                return False

        print(f"\n📋 Job: {job_data.get('title', 'Unknown')}")
        print(f"💰 Budget: {job_data.get('budget', 'Not specified')}")
        print(f"📊 Skills: {', '.join(job_data.get('skills', ['Not specified'])[:3])}")

        # Step 2: Generate proposal
        logger.info("\n[2/3] GENERATING PROPOSAL...")
        proposal = self.generator.generate_proposal(job_data)

        if not proposal:
            logger.error("\n✗ Failed to generate proposal. Check API key and try again.")
            return False

        # Step 3: Save and copy to clipboard
        logger.info("\n[3/3] SAVING & COPYING TO CLIPBOARD...")

        job_id = job_data.get('job_id', 'unknown')
        proposal_file = self.proposals_dir / f"{job_id}_proposal.txt"

        # Save to file
        try:
            with open(proposal_file, 'w') as f:
                f.write(proposal)
            logger.info(f"✓ Proposal saved to: {proposal_file}")
        except Exception as e:
            logger.warning(f"⚠ Could not save proposal file: {e}")

        # Copy to clipboard
        if ClipboardManager.copy_to_clipboard(proposal):
            logger.info("\n" + "=" * 60)
            logger.info("✓ SUCCESS! Proposal is ready to paste into Upwork.")
            logger.info("=" * 60)
            print("\n" + proposal)
            print("\n" + "=" * 60)
            print("✓ Proposal copied to clipboard - paste it into Upwork now!")
            print("=" * 60)
            return True
        else:
            logger.info("\n" + "=" * 60)
            logger.info("✓ Proposal generated (clipboard copy failed):")
            logger.info("=" * 60)
            print("\n" + proposal)
            print("\n" + "=" * 60)
            print("⚠ Copy the proposal above and paste it into Upwork")
            print("=" * 60)
            return True


def validate_url(url: str) -> bool:
    """Validate that URL is an Upwork job URL"""
    return "upwork.com/jobs/" in url


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python generate_upwork_proposal.py <upwork_job_url>")
        print("Example: python generate_upwork_proposal.py 'https://www.upwork.com/jobs/...'")
        sys.exit(1)

    url = sys.argv[1].strip()

    if not validate_url(url):
        print("✗ Invalid URL. Must be an Upwork job URL (upwork.com/jobs/...)")
        sys.exit(1)

    generator = UpworkProposalGenerator()
    success = generator.run(url)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
