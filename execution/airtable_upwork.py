"""
Airtable Integration for Upwork Job Automation
===============================================
Stores and manages Upwork job listings in Airtable.
"""

import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
import requests
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AirtableUpworkIntegration:
    """Manage Upwork jobs in Airtable"""
    
    def __init__(self):
        self.api_key = os.getenv('AIRTABLE_API_KEY')
        self.base_id = os.getenv('AIRTABLE_UPWORK_BASE_ID') or os.getenv('AIRTABLE_BASE_ID')
        
        if not self.api_key:
            raise ValueError("AIRTABLE_API_KEY not found in .env")
        
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        self.base_url = 'https://api.airtable.com/v0'
        self.logger = logger
        
        # Table name for Upwork jobs
        self.table_name = 'Upwork Jobs'
    
    def create_base(self, workspace_id: str = None) -> Optional[str]:
        """
        Create a new Airtable base for Upwork jobs.
        
        Note: Airtable API doesn't support creating bases programmatically.
        User needs to create the base manually and provide the base ID.
        
        Returns:
            Base ID if successful
        """
        self.logger.info("=" * 60)
        self.logger.info("AIRTABLE BASE SETUP")
        self.logger.info("=" * 60)
        self.logger.info("")
        self.logger.info("Please create a new Airtable base manually:")
        self.logger.info("1. Go to https://airtable.com")
        self.logger.info("2. Click '+ Create a base' or 'Add a base'")
        self.logger.info("3. Name it 'Upwork Job Automation'")
        self.logger.info("4. Create a table named 'Upwork Jobs'")
        self.logger.info("")
        self.logger.info("Then run: python setup_airtable_upwork.py")
        self.logger.info("=" * 60)
        return None
    
    def setup_table_fields(self) -> bool:
        """
        Set up the required fields in the Upwork Jobs table.
        Creates records to establish field structure.
        """
        self.logger.info("Setting up Airtable fields for Upwork Jobs...")
        
        # Create a sample record to establish fields
        # Airtable will auto-create fields based on the data
        sample_record = {
            "fields": {
                "Job Title": "Sample Job - Delete Me",
                "Job ID": "sample_delete_me",
                "Job URL": "https://upwork.com/jobs/~sample",
                "Description": "This is a sample record to set up the table structure. Delete this after setup.",
                "Budget": 0,
                "Job Type": "fixed-price",
                "Skills": "Python, Automation",
                "Client Rating": 0.0,
                "Client Reviews": 0,
                "Client Spent": "$0",
                "Client Country": "Unknown",
                "Payment Verified": False,
                "Posted": "Just now",
                "Proposals Count": 0,
                "Status": "New",
                "Score": 0,
                "Scraped At": datetime.now().isoformat(),
                "Notes": "",
                "Proposal": "",
                "Applied": False
            }
        }
        
        url = f"{self.base_url}/{self.base_id}/{self.table_name}"
        
        try:
            response = requests.post(url, headers=self.headers, json=sample_record)
            
            if response.status_code == 200:
                record_id = response.json().get('id')
                self.logger.info("✓ Table fields created successfully")
                
                # Delete the sample record
                delete_url = f"{url}/{record_id}"
                requests.delete(delete_url, headers=self.headers)
                self.logger.info("✓ Sample record cleaned up")
                return True
            else:
                self.logger.error(f"Failed to set up fields: {response.status_code}")
                self.logger.error(response.text)
                return False
                
        except Exception as e:
            self.logger.error(f"Error setting up fields: {e}")
            return False
    
    def sync_jobs(self, jobs: List[Dict]) -> Dict:
        """
        Sync scraped jobs to Airtable.
        
        Args:
            jobs: List of job dictionaries from scraper
        
        Returns:
            Summary dict with created, updated, skipped counts
        """
        summary = {
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'failed': 0,
            'jobs': []
        }
        
        self.logger.info(f"Syncing {len(jobs)} jobs to Airtable...")
        
        # Get existing jobs to check for duplicates
        existing_jobs = self._get_existing_job_ids()
        
        for job in jobs:
            job_id = job.get('id', '')
            
            if not job_id:
                self.logger.warning(f"Job has no ID, skipping: {job.get('title', 'Unknown')}")
                summary['skipped'] += 1
                continue
            
            if job_id in existing_jobs:
                self.logger.debug(f"Job already exists: {job_id}")
                summary['skipped'] += 1
                continue
            
            # Create new job record
            result = self._create_job_record(job)
            
            if result:
                summary['created'] += 1
                summary['jobs'].append({
                    'id': job_id,
                    'title': job.get('title', 'Unknown'),
                    'record_id': result
                })
            else:
                summary['failed'] += 1
        
        self.logger.info(f"✓ Sync complete: {summary['created']} created, {summary['skipped']} skipped, {summary['failed']} failed")
        return summary
    
    def _get_existing_job_ids(self) -> set:
        """Get set of existing job IDs in Airtable"""
        job_ids = set()
        
        url = f"{self.base_url}/{self.base_id}/{self.table_name}"
        params = {
            'fields[]': 'Job ID',
            'pageSize': 100
        }
        
        try:
            offset = None
            while True:
                if offset:
                    params['offset'] = offset
                
                response = requests.get(url, headers=self.headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    for record in data.get('records', []):
                        job_id = record.get('fields', {}).get('Job ID')
                        if job_id:
                            job_ids.add(job_id)
                    
                    offset = data.get('offset')
                    if not offset:
                        break
                else:
                    self.logger.warning(f"Error fetching existing jobs: {response.status_code}")
                    break
                    
        except Exception as e:
            self.logger.error(f"Error getting existing job IDs: {e}")
        
        return job_ids
    
    def _create_job_record(self, job: Dict) -> Optional[str]:
        """Create a single job record in Airtable"""
        
        # Extract client info
        client = job.get('client', {})
        
        # Calculate a simple score based on available data
        score = self._calculate_job_score(job)
        
        record = {
            "fields": {
                "Job Title": job.get('title', 'Unknown')[:100],  # Airtable has field limits
                "Job ID": job.get('id', ''),
                "Job URL": job.get('url', ''),
                "Description": job.get('description', '')[:5000],  # Long text limit
                "Budget": job.get('budget', 0),
                "Job Type": job.get('job_type', 'unknown'),
                "Skills": ', '.join(job.get('skills', [])),
                "Client Rating": client.get('rating', 0),
                "Client Reviews": client.get('reviews', 0),
                "Client Spent": client.get('spent', '$0'),
                "Client Country": client.get('country', ''),
                "Payment Verified": client.get('payment_verified', False),
                "Posted": job.get('posted', ''),
                "Proposals Count": job.get('proposals_count', 0),
                "Status": "New",
                "Score": score,
                "Scraped At": job.get('scraped_at', datetime.now().isoformat()),
                "Notes": "",
                "Proposal": "",
                "Applied": False
            }
        }
        
        url = f"{self.base_url}/{self.base_id}/{self.table_name}"
        
        try:
            response = requests.post(url, headers=self.headers, json=record)
            
            if response.status_code == 200:
                record_id = response.json().get('id')
                self.logger.debug(f"Created job: {job.get('title', 'Unknown')[:40]}...")
                return record_id
            else:
                self.logger.error(f"Failed to create job: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error creating job record: {e}")
            return None
    
    def _calculate_job_score(self, job: Dict) -> int:
        """
        Calculate a score for the job based on various factors.
        Score ranges from 0-100.
        """
        score = 50  # Base score
        
        client = job.get('client', {})
        
        # Client rating bonus (0-20 points)
        rating = client.get('rating', 0)
        if rating >= 4.8:
            score += 20
        elif rating >= 4.5:
            score += 15
        elif rating >= 4.0:
            score += 10
        elif rating > 0:
            score += 5
        
        # Client reviews bonus (0-15 points)
        reviews = client.get('reviews', 0)
        if reviews >= 100:
            score += 15
        elif reviews >= 50:
            score += 10
        elif reviews >= 10:
            score += 5
        
        # Payment verified bonus (10 points)
        if client.get('payment_verified', False):
            score += 10
        
        # Budget bonus (0-10 points)
        budget = job.get('budget', 0)
        if budget >= 1000:
            score += 10
        elif budget >= 500:
            score += 7
        elif budget >= 100:
            score += 5
        
        # Low competition bonus (0-10 points)
        proposals = job.get('proposals_count', 0)
        if proposals <= 5:
            score += 10
        elif proposals <= 15:
            score += 5
        elif proposals >= 50:
            score -= 10  # Penalty for high competition
        
        return max(0, min(100, score))  # Clamp to 0-100
    
    def get_jobs_by_status(self, status: str) -> List[Dict]:
        """Get jobs filtered by status"""
        url = f"{self.base_url}/{self.base_id}/{self.table_name}"
        params = {
            'filterByFormula': f"{{Status}} = '{status}'",
            'pageSize': 100
        }
        
        jobs = []
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                for record in data.get('records', []):
                    job = record.get('fields', {})
                    job['record_id'] = record.get('id')
                    jobs.append(job)
                    
        except Exception as e:
            self.logger.error(f"Error getting jobs by status: {e}")
        
        return jobs
    
    def update_job_status(self, record_id: str, status: str, notes: str = None) -> bool:
        """Update job status and optionally add notes"""
        url = f"{self.base_url}/{self.base_id}/{self.table_name}/{record_id}"
        
        fields = {"Status": status}
        if notes:
            fields["Notes"] = notes
        
        try:
            response = requests.patch(url, headers=self.headers, json={"fields": fields})
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Error updating job status: {e}")
            return False
    
    def save_proposal(self, record_id: str, proposal: str) -> bool:
        """Save generated proposal to job record"""
        url = f"{self.base_url}/{self.base_id}/{self.table_name}/{record_id}"
        
        try:
            response = requests.patch(url, headers=self.headers, json={
                "fields": {
                    "Proposal": proposal,
                    "Status": "Proposal Ready"
                }
            })
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Error saving proposal: {e}")
            return False
    
    def mark_as_applied(self, record_id: str) -> bool:
        """Mark job as applied"""
        url = f"{self.base_url}/{self.base_id}/{self.table_name}/{record_id}"
        
        try:
            response = requests.patch(url, headers=self.headers, json={
                "fields": {
                    "Applied": True,
                    "Status": "Applied"
                }
            })
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Error marking as applied: {e}")
            return False


def load_jobs_from_file(filepath: str = '.tmp/raw_jobs.json') -> List[Dict]:
    """Load jobs from JSON file"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Jobs file not found: {filepath}")
        return []


def sync_jobs_to_airtable(jobs: List[Dict] = None, filepath: str = '.tmp/raw_jobs.json') -> Dict:
    """
    Convenience function to sync jobs to Airtable.
    
    Args:
        jobs: List of job dicts, or None to load from file
        filepath: Path to jobs JSON file
    
    Returns:
        Sync summary dict
    """
    if jobs is None:
        jobs = load_jobs_from_file(filepath)
    
    if not jobs:
        logger.error("No jobs to sync")
        return {'created': 0, 'skipped': 0, 'failed': 0}
    
    airtable = AirtableUpworkIntegration()
    return airtable.sync_jobs(jobs)


# Alias for convenience
UpworkAirtable = AirtableUpworkIntegration


if __name__ == "__main__":
    # Test the integration
    import argparse
    
    parser = argparse.ArgumentParser(description='Airtable Upwork Integration')
    parser.add_argument('--setup', action='store_true', help='Set up table fields')
    parser.add_argument('--sync', action='store_true', help='Sync jobs from file')
    parser.add_argument('--file', type=str, default='.tmp/raw_jobs.json', help='Jobs file path')
    
    args = parser.parse_args()
    
    airtable = AirtableUpworkIntegration()
    
    if args.setup:
        airtable.setup_table_fields()
    elif args.sync:
        result = sync_jobs_to_airtable(filepath=args.file)
        print(f"\nSync complete: {result}")
    else:
        parser.print_help()
