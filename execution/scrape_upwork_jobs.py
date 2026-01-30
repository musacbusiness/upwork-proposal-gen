"""
Upwork Job Scraper

This module scrapes Upwork job listings. Two approaches:

1. Apify Integration (Recommended)
   - Use Apify's pre-built Upwork scraper actor
   - Reliable, well-maintained, respects rate limits
   - Requires Apify account and API token

2. Selenium/Playwright (Custom)
   - Direct scraping via headless browser
   - More control but higher risk of rate limiting
   - Requires Upwork login credentials

See directives/upwork_job_automation.md for full documentation.
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

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

load_dotenv()


class ApifyUpworkScraper:
    """Scrape Upwork jobs using Apify actor"""
    
    def __init__(self, api_key: str):
        """
        Initialize Apify scraper
        
        Args:
            api_key: Apify API token
        """
        try:
            from apify_client import ApifyClient
        except ImportError:
            logger.error("apify-client not installed. Install with: pip install apify-client")
            raise
        
        self.client = ApifyClient(api_key)
        self.logger = logger
    
    def scrape_upwork_jobs(
        self,
        search_query: str,
        category: str = '',
        min_budget: int = 0,
        max_results: int = 100
    ) -> List[Dict]:
        """
        Scrape Upwork jobs using Apify actor
        
        Args:
            search_query: Search keywords (e.g., "Python automation")
            category: Job category filter
            min_budget: Minimum budget filter
            max_results: Maximum results to scrape
        
        Returns:
            List of job dictionaries
        """
        try:
            self.logger.info(f"Scraping Upwork jobs for: {search_query}")
            
            # Run Apify actor for Upwork scraping
            # Note: This assumes you have an Apify actor already set up
            # You'll need to adjust actor_id based on your actual Apify actor
            
            run_input = {
                "searchQuery": search_query,
                "maxResults": max_results,
                "proxy": {
                    "useApifyProxy": True,
                    "apifyProxyGroups": ["RESIDENTIAL"]
                }
            }
            
            if category:
                run_input["category"] = category
            if min_budget:
                run_input["minBudget"] = min_budget
            
            # Run actor
            actor_call = self.client.actor("undefined/upwork-jobs-scraper").call(run_input)
            
            # Get results
            jobs = list(self.client.dataset(actor_call["defaultDatasetId"]).iterate_items())
            
            self.logger.info(f"Scraped {len(jobs)} jobs from Upwork")
            return self._normalize_jobs(jobs)
            
        except Exception as e:
            self.logger.error(f"Error scraping Upwork: {e}")
            return []
    
    def _normalize_jobs(self, raw_jobs: List[Dict]) -> List[Dict]:
        """Normalize Apify output to standard job format"""
        normalized = []
        
        for job in raw_jobs:
            normalized_job = {
                "id": job.get("jobId") or job.get("id"),
                "title": job.get("jobTitle") or job.get("title"),
                "description": job.get("jobDescription") or job.get("description", ""),
                "budget": self._extract_budget(job),
                "type": job.get("jobType") or "unknown",
                "category": job.get("jobCategory") or job.get("category"),
                "level": job.get("requiredLevel") or job.get("level"),
                "skills": job.get("requiredSkills") or [],
                "proposals_required": int(job.get("proposalsCount") or 0),
                "client": {
                    "name": job.get("clientName") or job.get("client", {}).get("name"),
                    "rating": float(job.get("clientRating") or 0),
                    "reviews": int(job.get("clientReviewCount") or 0),
                    "hire_rate": job.get("clientHireRate")
                },
                "url": job.get("jobUrl") or job.get("url"),
                "posted_at": job.get("postedTime") or job.get("posted_at"),
                "raw_data": job
            }
            normalized.append(normalized_job)
        
        return normalized
    
    def _extract_budget(self, job: Dict) -> float:
        """Extract budget amount from job"""
        # Handle different budget formats
        if isinstance(job.get("budget"), dict):
            return float(job.get("budget", {}).get("amount", 0))
        elif isinstance(job.get("budget"), (int, float)):
            return float(job.get("budget", 0))
        
        # Try alternative field names
        budget_str = job.get("budgetRange") or job.get("budgetMin") or "0"
        try:
            # Extract first number from string like "$500 - $1000"
            import re
            match = re.search(r'\$?([\d,]+)', str(budget_str))
            if match:
                return float(match.group(1).replace(',', ''))
        except:
            pass
        
        return 0


class ManualUpworkScraper:
    """Manual scraping approach using Selenium (as fallback/alternative)"""
    
    def __init__(self, email: str, password: str):
        """
        Initialize manual scraper with credentials
        
        Args:
            email: Upwork email
            password: Upwork password
        """
        self.email = email
        self.password = password
        self.logger = logger
        self.driver = None
    
    def scrape_upwork_jobs(self, search_query: str, max_pages: int = 5) -> List[Dict]:
        """
        Scrape jobs using Selenium (BETA - not fully implemented)
        
        Note: This requires careful handling of Upwork's anti-scraping measures.
        Recommended to use Apify instead.
        """
        self.logger.warning("Manual scraping is not recommended due to Upwork anti-scraping measures")
        self.logger.info("Please use Apify actor instead (see README)")
        
        # This would require implementing login, navigation, and extraction
        # Not included in this version - use Apify for reliability
        
        return []
    
    def close(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()


def save_raw_jobs(jobs: List[Dict], output_path: str = '.tmp/raw_jobs.json'):
    """Save raw scraped jobs to JSON"""
    with open(output_path, 'w') as f:
        json.dump(jobs, f, indent=2)
    logger.info(f"Saved {len(jobs)} raw jobs to {output_path}")


def load_raw_jobs(input_path: str = '.tmp/raw_jobs.json') -> List[Dict]:
    """Load raw jobs from JSON"""
    try:
        with open(input_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Raw jobs file not found: {input_path}")
        return []


if __name__ == "__main__":
    # Example usage with Apify
    
    api_token = os.getenv('APIFY_API_TOKEN')
    if not api_token:
        logger.error("APIFY_API_TOKEN not found in .env")
        logger.info("To use Apify scraper:")
        logger.info("1. Create account at apify.com")
        logger.info("2. Set up Upwork jobs scraper actor")
        logger.info("3. Add APIFY_API_TOKEN to .env")
        exit(1)
    
    # Initialize Apify scraper
    scraper = ApifyUpworkScraper(api_token)
    
    # Scrape jobs
    jobs = scraper.scrape_upwork_jobs(
        search_query="Python automation",
        max_results=100
    )
    
    if jobs:
        # Save raw jobs
        save_raw_jobs(jobs)
        logger.info(f"✓ Successfully scraped {len(jobs)} jobs")
    else:
        logger.error("No jobs scraped")
