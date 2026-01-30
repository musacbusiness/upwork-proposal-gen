"""
LinkedIn Scheduling Module - Schedule and post content to LinkedIn

Manages scheduling LinkedIn posts at specified times and tracking posts.
Uses Selenium browser automation for posting (no API required).
"""

import json
import logging
from typing import List, Dict, Optional
import os
from datetime import datetime, timedelta
import random
from dotenv import load_dotenv
from pytz import timezone as tz
from linkedin_poster_selenium import LinkedInPosterSelenium

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


class LinkedInScheduler:
    """Manage LinkedIn post scheduling and publishing using Selenium"""
    
    def __init__(self, config_path: str = '../config/linkedin_config.json'):
        """
        Initialize LinkedIn scheduler with randomized time windows
        
        Args:
            config_path: Path to LinkedIn configuration
        """
        # Time windows for 3 posts per day (in 24-hour format)
        self.time_windows = [
            (8, 30, 10, 0),   # Morning: 8:30 AM - 10:00 AM
            (12, 0, 14, 0),   # Midday: 12:00 PM - 2:00 PM
            (17, 0, 20, 0)    # Evening: 5:00 PM - 8:00 PM
        ]
        self.posts_per_day = 3
        self.timezone_str = 'America/New_York'
        self.logger = logger
        self.timezone = tz(self.timezone_str)
    
    def get_random_time_in_window(self, start_hour: int, start_min: int, 
                                   end_hour: int, end_min: int, base_date: datetime) -> datetime:
        """
        Generate a random time within a specified window
        
        Args:
            start_hour: Window start hour (24-hour)
            start_min: Window start minute
            end_hour: Window end hour (24-hour)
            end_min: Window end minute
            base_date: Base date to apply time to
        
        Returns:
            Random datetime within the window
        """
        # Convert times to minutes since midnight
        start_minutes = start_hour * 60 + start_min
        end_minutes = end_hour * 60 + end_min
        
        # Generate random minute within range
        random_minutes = random.randint(start_minutes, end_minutes)
        
        # Convert back to hours and minutes
        hour = random_minutes // 60
        minute = random_minutes % 60
        
        return base_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    def get_schedule_times(self, base_date: datetime = None, days_ahead: int = 7) -> List[datetime]:
        """
        Get randomized posting times for the next N days
        
        Args:
            base_date: Starting date (defaults to tomorrow)
            days_ahead: Number of days to schedule (default 7)
        
        Returns:
            List of datetime objects with randomized times in specified windows
        """
        if not base_date:
            # Start from tomorrow
            base_date = datetime.now(self.timezone).replace(hour=0, minute=0, second=0, microsecond=0)
            base_date += timedelta(days=1)
        
        scheduled_times = []
        
        for day_offset in range(days_ahead):
            current_day = base_date + timedelta(days=day_offset)
            
            # Generate 3 random times for this day (one in each window)
            for window in self.time_windows:
                random_time = self.get_random_time_in_window(
                    window[0], window[1], window[2], window[3], current_day
                )
                scheduled_times.append(random_time)
        
        self.logger.info(f"Generated {len(scheduled_times)} randomized posting times over {days_ahead} days")
        return sorted(scheduled_times)
    
    def schedule_post(self, post_content: Dict, scheduled_time: datetime) -> Optional[Dict]:
        """
        Schedule a post to be published at a specific time
        
        Note: With Selenium, scheduling is simulated - posts are stored for later publishing.
        Actual posting happens when the orchestrator runs at the scheduled time.
        
        Args:
            post_content: Post object with content and media
            scheduled_time: When to publish the post
        
        Returns:
            Scheduled post metadata or None if failed
        """
        try:
            self.logger.info(f"Post queued for scheduling at {scheduled_time}")
            
            return {
                "post_id": f"scheduled_{int(scheduled_time.timestamp())}",
                "scheduled_time": scheduled_time.isoformat(),
                "status": "SCHEDULED",
                "content": post_content.get('Content') or post_content.get('content', ''),
                "method": "selenium_scheduled"
            }
                
        except Exception as e:
            self.logger.error(f"Error scheduling post: {e}")
            return None
    
    def _get_user_urn(self) -> Optional[str]:
        """Get LinkedIn user URN from API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            url = f"{self.base_url}/me"
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                urn = result.get('id')
                self.logger.debug(f"Retrieved user URN: {urn}")
                return urn
            else:
                self.logger.error(f"Error getting user URN: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting user URN: {e}")
            return None
    
    def _prepare_post_payload(self, post_content: Dict, actor_urn: str, 
                             scheduled_time: datetime) -> Dict:
        """
        Prepare LinkedIn API payload for scheduling a post
        
        Args:
            post_content: Post object with content
            actor_urn: LinkedIn user URN
            scheduled_time: When to publish
        
        Returns:
            Formatted payload for LinkedIn API
        """
        payload = {
            "author": f"urn:li:person:{actor_urn}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.Share": {
                    "shareCommentary": {
                        "text": post_content.get('content', '')
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        # Add image if available
        if post_content.get('image_url'):
            payload["specificContent"]["com.linkedin.ugc.Share"]["shareMediaCategory"] = "IMAGE"
            # Image handling would require additional asset registration
            # For now, we'll note this in the payload
            payload["_image_url"] = post_content.get('image_url')
        
        return payload
    
    def schedule_batch(self, posts: List[Dict]) -> List[Dict]:
        """
        Schedule multiple posts for the day
        
        Args:
            posts: List of post objects to schedule
        
        Returns:
            List of scheduled post metadata
        """
        scheduled_times = self.get_schedule_times()
        scheduled_posts = []
        
        for i, post in enumerate(posts[:self.posts_per_day]):
            if i < len(scheduled_times):
                scheduled = self.schedule_post(post, scheduled_times[i])
                if scheduled:
                    scheduled_posts.append(scheduled)
        
        self.logger.info(f"Scheduled {len(scheduled_posts)} posts")
        return scheduled_posts
    
    def publish_post(self, post_content: Dict) -> Optional[Dict]:
        """
        Publish a post immediately using Selenium browser automation
        
        Args:
            post_content: Post object to publish
        
        Returns:
            Published post data or None if failed
        """
        try:
            # Initialize Selenium poster
            with LinkedInPosterSelenium(headless=True) as poster:
                # Extract content and image path
                text = post_content.get('Content') or post_content.get('content', '')
                image_path = post_content.get('Image Local Path') or post_content.get('image_local_path')
                
                # Post to LinkedIn
                result = poster.post_content(text, image_path)
                
                if result.get('success'):
                    self.logger.info(f"✓ Post published successfully via Selenium")
                    return {
                        "post_id": f"selenium_{int(datetime.now().timestamp())}",
                        "published_time": datetime.now(self.timezone).isoformat(),
                        "status": "PUBLISHED",
                        "content": text,
                        "method": "selenium"
                    }
                else:
                    self.logger.error(f"Failed to publish post: {result.get('message')}")
                    return None
                
        except Exception as e:
            self.logger.error(f"Error publishing post: {e}")
            return None
    
    def get_post_analytics(self, post_id: str) -> Optional[Dict]:
        """
        Get analytics for a published post
        
        Args:
            post_id: LinkedIn post ID
        
        Returns:
            Post analytics data or None if failed
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            url = f"{self.base_url}/posts/{post_id}?projection=(ugcPost(shares,likes,comments))"
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                analytics = {
                    "post_id": post_id,
                    "likes": len(result.get('ugcPost', {}).get('likes', [])),
                    "comments": len(result.get('ugcPost', {}).get('comments', [])),
                    "shares": len(result.get('ugcPost', {}).get('shares', [])),
                    "retrieved_at": datetime.now().isoformat()
                }
                
                self.logger.info(f"Retrieved analytics for post {post_id}: {analytics}")
                return analytics
            else:
                self.logger.error(f"Error getting analytics: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting post analytics: {e}")
            return None
    
    def calculate_next_posting_times(self, hours_ahead: int = 24) -> List[datetime]:
        """
        Calculate next posting times in advance
        
        Args:
            hours_ahead: How many hours ahead to calculate
        
        Returns:
            List of upcoming posting datetimes
        """
        upcoming_times = []
        current_time = datetime.now(self.timezone)
        
        for hours in range(hours_ahead):
            check_date = current_time + timedelta(hours=hours)
            scheduled_times = self.get_schedule_times(check_date)
            
            for scheduled_time in scheduled_times:
                if scheduled_time > current_time:
                    upcoming_times.append(scheduled_time)
        
        self.logger.info(f"Calculated {len(upcoming_times)} upcoming posting times")
        return upcoming_times
    
    def save_schedule(self, posts: List[Dict], schedule_file: str = '../.tmp/linkedin_schedule.json'):
        """Save posting schedule to file for reference"""
        os.makedirs(os.path.dirname(schedule_file) or '.', exist_ok=True)
        
        schedule = {
            "posts": posts,
            "generated_at": datetime.now().isoformat(),
            "total_scheduled": len(posts),
            "timezone": self.timezone_str
        }
        
        with open(schedule_file, 'w') as f:
            json.dump(schedule, f, indent=2)
        
        self.logger.info(f"Saved schedule to {schedule_file}")
        return schedule_file


if __name__ == "__main__":
    scheduler = LinkedInScheduler()
    
    # Get next posting times
    times = scheduler.get_schedule_times()
    for t in times:
        print(f"Scheduled posting time: {t}")
