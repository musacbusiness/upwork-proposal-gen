"""
Airtable Integration Module - Sync LinkedIn posts with Airtable

Manages reading/writing post data to Airtable, including:
- Storing generated posts in Draft status
- Tracking approved posts
- Managing scheduling queue
- Recording posted content and engagement
"""

import json
import logging
from typing import List, Dict, Optional
import os
from datetime import datetime
from dotenv import load_dotenv
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../logs/linkedin_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()


class AirtableIntegration:
    """Manage Airtable integration for LinkedIn content management"""
    
    def __init__(self, api_key: str = None, config_path: str = None):
        """
        Initialize Airtable integration
        
        Args:
            api_key: Airtable API key (defaults to AIRTABLE_API_KEY env var)
            config_path: Path to Airtable configuration
        """
        self.api_key = api_key or os.getenv('AIRTABLE_API_KEY')
        self.base_id = os.getenv('AIRTABLE_BASE_ID', 'appw88uD6ZM0ckF8f')
        self.table_id = 'tbljg75KMQWDo2Hgu'  # LinkedIn Posts table
        self.base_url = "https://api.airtable.com/v0"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Table name to ID mapping
        self.tables = {
            "posts": self.table_id,
            "linkedin_posts": self.table_id
        }
        
        self.logger = logger
    
    def create_record(self, table_name: str, fields: Dict) -> Optional[Dict]:
        """
        Create a new record in Airtable
        
        Args:
            table_name: Name of the table (will look up in config)
            fields: Dictionary of field names and values
        
        Returns:
            Created record data or None if failed
        """
        if not self.base_id:
            self.logger.error("AIRTABLE_BASE_ID not configured")
            return None
        
        try:
            url = f"{self.base_url}/{self.base_id}/{self.table_id}"
            
            payload = {
                "records": [
                    {
                        "fields": fields
                    }
                ]
            }
            
            response = requests.post(url, json=payload, headers=self.headers, timeout=30)
            
            if response.status_code in [200, 201]:
                result = response.json()
                record = result.get('records', [{}])[0]
                self.logger.info(f"Created record in {table_name}: {record.get('id')}")
                return record
            else:
                self.logger.error(f"Error creating record: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error creating Airtable record: {e}")
            return None
    
    def update_record(self, table_name: str, record_id: str, fields: Dict) -> Optional[Dict]:
        """
        Update an existing record in Airtable
        
        Args:
            table_name: Name of the table
            record_id: ID of the record to update
            fields: Dictionary of fields to update
        
        Returns:
            Updated record data or None if failed
        """
        if not self.base_id:
            self.logger.error("AIRTABLE_BASE_ID not configured")
            return None
        
        table_id = self.tables.get(table_name)
        if not table_id:
            self.logger.error(f"Table {table_name} not found")
            return None
        
        try:
            url = f"{self.base_url}/{self.base_id}/{table_id}/{record_id}"
            
            payload = {
                "fields": fields
            }
            
            response = requests.patch(url, json=payload, headers=self.headers, timeout=30)
            
            if response.status_code in [200, 201]:
                result = response.json()
                self.logger.info(f"Updated record in {table_name}: {record_id}")
                return result
            else:
                self.logger.error(f"Error updating record: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error updating Airtable record: {e}")
            return None
    
    def get_records(self, table_name: str, filter_formula: str = None) -> List[Dict]:
        """
        Get records from Airtable
        
        Args:
            table_name: Name of the table
            filter_formula: Optional Airtable filter formula
        
        Returns:
            List of records
        """
        if not self.base_id:
            self.logger.error("AIRTABLE_BASE_ID not configured")
            return []
        
        table_id = self.tables.get(table_name)
        if not table_id:
            self.logger.error(f"Table {table_name} not found")
            return []
        
        try:
            url = f"{self.base_url}/{self.base_id}/{table_id}"
            
            params = {}
            if filter_formula:
                params['filterByFormula'] = filter_formula
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                records = result.get('records', [])
                self.logger.info(f"Retrieved {len(records)} records from {table_name}")
                return records
            else:
                self.logger.error(f"Error getting records: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting Airtable records: {e}")
            return []
    
    def add_post(self, post: Dict) -> Optional[str]:
        """
        Add a generated post to Airtable Posts table
        
        Args:
            post: Post object with all details
        
        Returns:
            Airtable record ID or None if failed
        """
        try:
            fields = {
                "Title": post.get('title', ''),
                "Post Content": post.get('content', ''),
                "Image Prompt": post.get('image_prompt', ''),
                "Created Date": datetime.now().isoformat(),
                "Writing Framework": post.get('framework', 'Listicle')
            }
            
            # Try to set Status - may fail if option doesn't exist in dropdown
            # Use existing Status dropdown options:
            # Draft, Pending Review, Approved - Ready to Schedule, Scheduled, Posted, Rejected
            status_to_set = post.get('status', 'Draft')
            
            # Add image URL if available
            if post.get('image_url'):
                fields["Image URL"] = post.get('image_url')
                # Also attach image file
                fields["Image"] = [{"url": post.get('image_url')}]
            
            # Try with Status first
            fields["Status"] = status_to_set
            record = self.create_record("posts", fields)
            
            # If failed due to Status field, retry without it
            if record is None:
                self.logger.warning("Retrying without Status field (may need to add dropdown option in Airtable)")
                del fields["Status"]
                record = self.create_record("posts", fields)
            
            if record:
                return record.get('id')
            return None
            
        except Exception as e:
            self.logger.error(f"Error adding post to Airtable: {e}")
            return None
    
    def get_approved_posts(self) -> List[Dict]:
        """
        Get all approved posts from Airtable
        
        Returns:
            List of approved post records
        """
        try:
            formula = "{Status}='APPROVED'"
            records = self.get_records("posts", filter_formula=formula)
            
            self.logger.info(f"Retrieved {len(records)} approved posts")
            return records
            
        except Exception as e:
            self.logger.error(f"Error getting approved posts: {e}")
            return []
    
    def get_pending_posts(self) -> List[Dict]:
        """
        Get posts pending approval
        
        Returns:
            List of pending post records
        """
        try:
            formula = "{Status}='Draft'"
            records = self.get_records("posts", filter_formula=formula)
            
            self.logger.info(f"Retrieved {len(records)} pending posts")
            return records
            
        except Exception as e:
            self.logger.error(f"Error getting pending posts: {e}")
            return []
    
    def approve_post(self, record_id: str, approved_by: str = "Automation") -> bool:
        """
        Mark a post as approved
        
        Args:
            record_id: Airtable record ID
            approved_by: User approving the post
        
        Returns:
            Success status
        """
        try:
            fields = {
                "Status": "APPROVED",
                "Approved By": approved_by,
                "Approval Date": datetime.now().isoformat()
            }
            
            result = self.update_record("posts", record_id, fields)
            return result is not None
            
        except Exception as e:
            self.logger.error(f"Error approving post: {e}")
            return False
    
    def mark_posted(self, record_id: str, posted_url: str = None) -> bool:
        """
        Mark a post as successfully posted
        
        Args:
            record_id: Airtable record ID
            posted_url: URL of the posted LinkedIn post
        
        Returns:
            Success status
        """
        try:
            fields = {
                "Status": "POSTED",
                "Posted At": datetime.now().isoformat()
            }
            
            if posted_url:
                fields["Posted URL"] = posted_url
            
            result = self.update_record("posts", record_id, fields)
            return result is not None
            
        except Exception as e:
            self.logger.error(f"Error marking post as posted: {e}")
            return False
    
    def add_to_scheduling_queue(self, post_record_id: str, scheduled_time: str) -> Optional[str]:
        """
        Add a post to the scheduling queue
        
        Args:
            post_record_id: Airtable record ID of the post
            scheduled_time: ISO format datetime for scheduling
        
        Returns:
            Queue record ID or None if failed
        """
        try:
            fields = {
                "Post ID": [post_record_id],
                "Scheduled Time": scheduled_time,
                "Status": "PENDING",
                "Platform": "LinkedIn"
            }
            
            record = self.create_record("scheduling_queue", fields)
            
            if record:
                self.logger.info(f"Added post to scheduling queue: {record.get('id')}")
                return record.get('id')
            return None
            
        except Exception as e:
            self.logger.error(f"Error adding to scheduling queue: {e}")
            return None
    
    def get_posts_ready_to_schedule(self) -> List[Dict]:
        """
        Get posts that are approved and ready to be scheduled
        
        Returns:
            List of approved posts ready for scheduling
        """
        try:
            formula = "AND({Status}='APPROVED', {Scheduled Times}=BLANK())"
            records = self.get_records("posts", filter_formula=formula)
            
            self.logger.info(f"Retrieved {len(records)} posts ready to schedule")
            return records
            
        except Exception as e:
            self.logger.error(f"Error getting posts to schedule: {e}")
            return []
    
    def save_posts_locally(self, posts: List[Dict], output_path: str = '../.tmp/linkedin_posts_airtable.json'):
        """Save posts to local JSON for backup and reference"""
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(posts, f, indent=2)
        
        self.logger.info(f"Saved {len(posts)} posts to {output_path}")
        return output_path
    
    def update_post_status(self, record_id: str, status: str) -> bool:
        """
        Update post status in Airtable
        
        Args:
            record_id: Airtable record ID
            status: New status ('Awaiting Approval', 'Approved - Ready to Schedule', 'Posted')
        
        Returns:
            True if successful
        """
        try:
            import requests
            
            url = f"{self.base_url}/{self.base_id}/{self.table_id}/{record_id}"
            
            payload = {
                "fields": {
                    "Status": status
                }
            }
            
            if status == "Posted":
                payload["fields"]["Posted Time"] = datetime.now().isoformat()
            
            response = requests.patch(url, json=payload, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                self.logger.info(f"Updated post {record_id} status to: {status}")
                return True
            else:
                self.logger.error(f"Failed to update status: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error updating post status: {e}")
            return False
    
    def cleanup_old_posts(self, days_to_keep: int = 7) -> int:
        """
        Delete posted records older than specified days
        
        Args:
            days_to_keep: Number of days to keep posted records
        
        Returns:
            Number of records deleted
        """
        try:
            import requests
            from datetime import timedelta
            
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            cutoff_str = cutoff_date.strftime('%Y-%m-%d')
            
            # Get all posted records older than cutoff
            formula = f"AND({{Status}}='Posted', IS_BEFORE({{Posted Time}}, '{cutoff_str}'))"
            
            url = f"{self.base_url}/{self.base_id}/{self.table_id}"
            params = {"filterByFormula": formula}
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code != 200:
                self.logger.error(f"Failed to fetch old posts: {response.status_code}")
                return 0
            
            records = response.json().get('records', [])
            deleted_count = 0
            
            for record in records:
                record_id = record.get('id')
                delete_url = f"{url}/{record_id}"
                
                del_response = requests.delete(delete_url, headers=self.headers, timeout=30)
                
                if del_response.status_code == 200:
                    deleted_count += 1
                    self.logger.info(f"Deleted old post: {record_id}")
            
            self.logger.info(f"Cleaned up {deleted_count} old posted records")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old posts: {e}")
            return 0
    
    def get_approved_posts_for_scheduling(self) -> List[Dict]:
        """
        Get approved posts that haven't been scheduled yet
        
        Returns:
            List of approved posts without scheduled times
        """
        try:
            import requests
            
            # Posts with "Approved - Ready to Schedule" status
            formula = "{Status}='Approved - Ready to Schedule'"
            
            url = f"{self.base_url}/{self.base_id}/{self.table_id}"
            params = {"filterByFormula": formula}
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 200:
                records = response.json().get('records', [])
                self.logger.info(f"Found {len(records)} approved posts ready for scheduling")
                return records
            else:
                self.logger.error(f"Failed to get approved posts: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting approved posts for scheduling: {e}")
            return []


if __name__ == "__main__":
    # Test Airtable connection
    airtable = AirtableIntegration()
    
    # Get pending posts
    pending = airtable.get_pending_posts()
    print(f"Found {len(pending)} pending posts")
