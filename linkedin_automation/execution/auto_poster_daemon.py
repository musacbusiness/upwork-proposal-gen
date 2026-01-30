"""
Auto-Poster Daemon - Automatically posts approved LinkedIn content at scheduled times

This daemon runs continuously and:
1. Monitors Airtable for posts with Status = "Approved - Ready to Schedule"
2. Posts content at the scheduled time
3. Updates status to "Posted" after successful posting
"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv
from pytz import timezone as tz

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from execution.airtable_integration import AirtableIntegration
from execution.linkedin_poster_selenium import LinkedInPosterSelenium

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), '../logs/auto_poster.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AutoPosterDaemon:
    """
    Daemon that automatically posts approved content at scheduled times
    """
    
    def __init__(self):
        self.airtable = AirtableIntegration()
        self.poster = None  # Initialize lazily to avoid browser opening unnecessarily
        self.timezone = tz('America/New_York')
        self.check_interval = 60  # Check every 60 seconds
        self.logger = logger
        
    def get_approved_posts_due(self) -> List[Dict]:
        """
        Get all approved posts that are due to be posted
        
        Returns:
            List of posts ready to be published
        """
        try:
            # Get posts with status "Approved - Ready to Schedule"
            formula = "{Status}='Approved - Ready to Schedule'"
            records = self.airtable.get_records("posts", filter_formula=formula)
            
            now = datetime.now(self.timezone)
            due_posts = []
            
            for record in records:
                fields = record.get('fields', {})
                scheduled_time_str = fields.get('Scheduled Time')
                
                if scheduled_time_str:
                    try:
                        # Parse the scheduled time
                        scheduled_time = datetime.fromisoformat(scheduled_time_str.replace('Z', '+00:00'))
                        
                        # If scheduled time has passed, it's due
                        if scheduled_time <= now:
                            due_posts.append({
                                'record_id': record.get('id'),
                                'fields': fields,
                                'scheduled_time': scheduled_time
                            })
                    except (ValueError, TypeError) as e:
                        self.logger.warning(f"Invalid scheduled time for record {record.get('id')}: {e}")
                else:
                    # No scheduled time = post immediately when approved
                    due_posts.append({
                        'record_id': record.get('id'),
                        'fields': fields,
                        'scheduled_time': now
                    })
            
            return due_posts
            
        except Exception as e:
            self.logger.error(f"Error getting approved posts: {e}")
            return []
    
    def post_to_linkedin(self, post_data: Dict) -> bool:
        """
        Post content to LinkedIn
        
        Args:
            post_data: Post data including content and image
            
        Returns:
            True if posted successfully
        """
        try:
            # Initialize poster if not already done
            if self.poster is None:
                self.poster = LinkedInPosterSelenium()
            
            fields = post_data.get('fields', {})
            content = fields.get('Post Content', '')
            image_url = fields.get('Image URL')
            title = fields.get('Title', 'Untitled')
            
            self.logger.info(f"Posting to LinkedIn: {title}")
            
            # Post to LinkedIn
            result = self.poster.post_to_linkedin(content, image_url)
            
            if result and result.get('success'):
                self.logger.info(f"Successfully posted: {title}")
                return True
            else:
                self.logger.error(f"Failed to post: {title} - {result}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error posting to LinkedIn: {e}")
            return False
    
    def update_post_status(self, record_id: str, status: str, notes: str = None):
        """
        Update post status in Airtable
        
        Args:
            record_id: Airtable record ID
            status: New status value
            notes: Optional notes to append
        """
        try:
            update_fields = {"Status": status}
            
            if notes:
                # Get existing notes and append
                record = self.airtable.get_record("posts", record_id)
                existing_notes = record.get('fields', {}).get('Notes', '') if record else ''
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
                new_notes = f"{existing_notes}\n[{timestamp}] {notes}" if existing_notes else f"[{timestamp}] {notes}"
                update_fields["Notes"] = new_notes.strip()
            
            self.airtable.update_record("posts", record_id, update_fields)
            self.logger.info(f"Updated record {record_id} to status: {status}")
            
        except Exception as e:
            self.logger.error(f"Error updating post status: {e}")
    
    def process_due_posts(self):
        """Process all posts that are due to be published"""
        due_posts = self.get_approved_posts_due()
        
        if not due_posts:
            return
        
        self.logger.info(f"Found {len(due_posts)} posts ready to publish")
        
        for post in due_posts:
            record_id = post['record_id']
            title = post['fields'].get('Title', 'Untitled')
            
            self.logger.info(f"Processing: {title}")
            
            # Post to LinkedIn
            success = self.post_to_linkedin(post)
            
            if success:
                self.update_post_status(
                    record_id, 
                    "Posted",
                    f"Auto-posted successfully"
                )
            else:
                self.update_post_status(
                    record_id,
                    "Approved - Ready to Schedule",  # Keep approved for retry
                    f"Auto-post failed - will retry"
                )
            
            # Small delay between posts
            time.sleep(5)
    
    def run(self):
        """
        Main daemon loop - continuously checks for and processes approved posts
        """
        self.logger.info("=" * 60)
        self.logger.info("Auto-Poster Daemon Started")
        self.logger.info(f"Checking every {self.check_interval} seconds")
        self.logger.info("=" * 60)
        
        while True:
            try:
                self.process_due_posts()
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
            
            # Wait before next check
            time.sleep(self.check_interval)
    
    def cleanup(self):
        """Clean up resources"""
        if self.poster:
            try:
                self.poster.close()
            except:
                pass


def main():
    """Entry point for the auto-poster daemon"""
    daemon = AutoPosterDaemon()
    
    try:
        daemon.run()
    except KeyboardInterrupt:
        logger.info("Shutting down Auto-Poster Daemon...")
    finally:
        daemon.cleanup()


if __name__ == "__main__":
    main()
