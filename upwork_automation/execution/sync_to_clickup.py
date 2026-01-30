import json
import logging
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../logs/upwork_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class ClickUpIntegration:
    """Manage ClickUp integration for job task creation"""
    
    def __init__(self, api_key: str, workspace_id: str, list_id: str):
        """
        Initialize ClickUp integration
        
        Args:
            api_key: ClickUp API key
            workspace_id: ClickUp workspace ID
            list_id: ClickUp list ID for Upwork jobs
        """
        self.api_key = api_key
        self.workspace_id = workspace_id
        self.list_id = list_id
        self.base_url = "https://api.clickup.com/api/v2"
        self.headers = {
            "Authorization": api_key,
            "Content-Type": "application/json"
        }
        self.logger = logger
    
    def check_duplicate_job(self, job_id: str) -> bool:
        """Check if job already exists in ClickUp"""
        try:
            url = f"{self.base_url}/list/{self.list_id}/task"
            params = {
                "query": f"upwork_{job_id}",
                "include_closed": True
            }
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                tasks = response.json().get('tasks', [])
                return len(tasks) > 0
            else:
                self.logger.warning(f"Error checking duplicate: {response.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"Error checking duplicate job: {e}")
            return False
    
    def create_task(self, job: Dict) -> Optional[Dict]:
        """
        Create a task in ClickUp for a job
        
        Args:
            job: Job dictionary with details
        
        Returns:
            Task data if successful, None otherwise
        """
        if self.check_duplicate_job(job.get('id', '')):
            self.logger.warning(f"Job {job.get('id')} already exists in ClickUp")
            return None
        
        try:
            # Format job description
            description = self._format_job_description(job)
            
            # Prepare task data
            task_data = {
                "name": job.get('title', 'Upwork Job')[:100],
                "description": description,
                "status": "AWAITING APPROVAL",
                "priority": self._calculate_priority(job),
                "custom_fields": [
                    {
                        "id": "job_id",
                        "value": job.get('id', '')
                    },
                    {
                        "id": "budget",
                        "value": str(job.get('budget', ''))
                    },
                    {
                        "id": "client_rating",
                        "value": str(job.get('client', {}).get('rating', ''))
                    },
                    {
                        "id": "job_url",
                        "value": job.get('url', '')
                    },
                    {
                        "id": "filter_score",
                        "value": str(job.get('filter_score', 0))
                    },
                    {
                        "id": "scraped_at",
                        "value": job.get('filtered_at', '')
                    }
                ]
            }
            
            # Create task
            url = f"{self.base_url}/list/{self.list_id}/task"
            response = requests.post(url, headers=self.headers, json=task_data)
            
            if response.status_code in [200, 201]:
                task = response.json().get('task', {})
                self.logger.info(f"✓ Created task in ClickUp for job {job.get('id')} - Task ID: {task.get('id')}")
                return task
            else:
                self.logger.error(f"Error creating task: {response.status_code} - {response.text}")
                return None
        
        except Exception as e:
            self.logger.error(f"Error creating ClickUp task: {e}")
            return None
    
    def _format_job_description(self, job: Dict) -> str:
        """Format job details into ClickUp description"""
        description = f"""
**Job Title:** {job.get('title', 'N/A')}

**Client:** {job.get('client', {}).get('name', 'N/A')}
- Rating: {job.get('client', {}).get('rating', 'N/A')}/5
- Reviews: {job.get('client', {}).get('reviews', 'N/A')}
- Hire Rate: {job.get('client', {}).get('hire_rate', 'N/A')}

**Budget:** ${job.get('budget', 'N/A')}
**Type:** {job.get('type', 'N/A')}
**Level:** {job.get('level', 'N/A')}

**Required Skills:** {', '.join(job.get('skills', []))}

**Job Description:**
{job.get('description', 'N/A')[:1000]}...

**Job URL:** {job.get('url', 'N/A')}

**Filter Score:** {job.get('filter_score', 0):.1f}/100

**Scraped At:** {job.get('filtered_at', 'N/A')}
"""
        return description.strip()
    
    def _calculate_priority(self, job: Dict) -> int:
        """
        Calculate priority level based on job score
        
        ClickUp priority: 1=urgent, 2=high, 3=normal, 4=low
        """
        score = job.get('filter_score', 50)
        
        if score >= 80:
            return 1  # Urgent
        elif score >= 70:
            return 2  # High
        elif score >= 50:
            return 3  # Normal
        else:
            return 4  # Low
    
    def sync_jobs_to_clickup(self, jobs: List[Dict]) -> Dict:
        """
        Sync filtered jobs to ClickUp
        
        Returns:
            Summary dict with created/failed counts
        """
        created = 0
        failed = 0
        duplicates = 0
        tasks = []
        
        for job in jobs:
            task = self.create_task(job)
            if task:
                created += 1
                tasks.append(task)
            elif self.check_duplicate_job(job.get('id', '')):
                duplicates += 1
            else:
                failed += 1
        
        summary = {
            "total": len(jobs),
            "created": created,
            "duplicates": duplicates,
            "failed": failed,
            "tasks": tasks,
            "synced_at": datetime.now().isoformat()
        }
        
        self.logger.info(f"ClickUp sync complete: {created} created, {duplicates} duplicates, {failed} failed")
        return summary
    
    def register_webhook(self, webhook_url: str, event: str = "taskStatusUpdated") -> Optional[Dict]:
        """
        Register a webhook for task status changes
        
        Args:
            webhook_url: URL to receive webhook events
            event: Event type to listen for
        
        Returns:
            Webhook data if successful
        """
        try:
            url = f"{self.base_url}/team/{self.workspace_id}/webhook"
            webhook_data = {
                "endpoint": webhook_url,
                "events": [event],
                "list_ids": [self.list_id]
            }
            
            response = requests.post(url, headers=self.headers, json=webhook_data)
            
            if response.status_code in [200, 201]:
                webhook = response.json()
                self.logger.info(f"✓ Registered webhook: {webhook.get('id')}")
                return webhook
            else:
                self.logger.error(f"Error registering webhook: {response.status_code}")
                return None
        except Exception as e:
            self.logger.error(f"Error registering webhook: {e}")
            return None


def load_filtered_jobs(filepath: str = '.tmp/filtered_jobs_accepted.json') -> List[Dict]:
    """Load filtered jobs from JSON file"""
    try:
        with open(filepath, 'r') as f:
            jobs = json.load(f)
        logger.info(f"Loaded {len(jobs)} jobs from {filepath}")
        return jobs
    except FileNotFoundError:
        logger.error(f"Filtered jobs file not found: {filepath}")
        return []


def save_sync_summary(summary: Dict, output_path: str = '.tmp/clickup_sync_summary.json'):
    """Save ClickUp sync summary to file"""
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Saved sync summary to {output_path}")


if __name__ == "__main__":
    # Load credentials from environment
    api_key = os.getenv('CLICKUP_API_KEY')
    workspace_id = os.getenv('CLICKUP_WORKSPACE_ID')
    list_id = os.getenv('CLICKUP_LIST_ID')
    
    if not all([api_key, workspace_id, list_id]):
        logger.error("Missing ClickUp credentials in .env file")
        exit(1)
    
    # Initialize ClickUp integration
    clickup = ClickUpIntegration(api_key, workspace_id, list_id)
    
    # Load filtered jobs
    jobs = load_filtered_jobs()
    
    if jobs:
        # Sync jobs to ClickUp
        summary = clickup.sync_jobs_to_clickup(jobs)
        
        # Save summary
        save_sync_summary(summary)
    else:
        logger.warning("No jobs to sync")
