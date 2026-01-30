#!/usr/bin/env python3
"""
RUN_linkedin_automation.py - ENTRY POINT FOR LINKEDIN CONTENT AUTOMATION

Main interaction point for LinkedIn lead generation automation.
Coordinates: content research → image generation → Airtable storage → scheduling → posting

Usage:
    python RUN_linkedin_automation.py --action research       # Research & generate content ideas
    python RUN_linkedin_automation.py --action generate-posts # Generate full posts with images
    python RUN_linkedin_automation.py --action schedule       # Schedule approved posts
    python RUN_linkedin_automation.py --action post-now       # Post immediately
    python RUN_linkedin_automation.py --action daily          # Run complete daily workflow
    python RUN_linkedin_automation.py --action status         # Check automation status
"""

import json
import logging
import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add execution directory to path
sys.path.insert(0, str(Path(__file__).parent / 'execution'))

from execution.research_content import ContentResearcher
from execution.generate_images import ImageGenerator
from execution.airtable_integration import AirtableIntegration
from execution.linkedin_scheduler import LinkedInScheduler
from execution.content_revisions import ContentRevisionProcessor
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/linkedin_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()


class LinkedInContentOrchestrator:
    """Orchestrate complete LinkedIn content automation workflow"""
    
    def __init__(self):
        self.logger = logger
        self.ensure_directories()
        self.load_config()
    
    def ensure_directories(self):
        """Create necessary directories"""
        dirs = [
            'logs',
            'config',
            '.tmp',
            '../.tmp/linkedin_images',
            '../.tmp/linkedin_posts'
        ]
        for d in dirs:
            Path(d).mkdir(parents=True, exist_ok=True)
    
    def load_config(self):
        """Load LinkedIn automation configuration"""
        try:
            with open('config/linkedin_config.json', 'r') as f:
                self.config = json.load(f)
        except Exception as e:
            self.logger.warning(f"Could not load config: {e}")
            self.config = {}
    
    def action_research(self):
        """Research and generate content ideas"""
        self.logger.info("=" * 60)
        self.logger.info("ACTION: Research Content Ideas")
        self.logger.info("=" * 60)
        
        try:
            # Initialize researcher
            researcher = ContentResearcher()
            
            # Get topics from config
            topics = self.config.get('content_research', {}).get('topics', [
                'AI automation for business',
                'Workflow optimization',
                'Business process automation'
            ])
            
            # Research topics
            ideas = researcher.research_topics(topics, count=2)
            
            if not ideas:
                self.logger.error("No ideas generated")
                return False
            
            # Save ideas
            researcher.save_content_ideas(ideas, '../.tmp/linkedin_content_ideas.json')
            
            self.logger.info(f"✓ Research complete: {len(ideas)} ideas generated")
            return True
            
        except Exception as e:
            self.logger.error(f"Error in research action: {e}")
            return False
    
    def action_generate_posts(self):
        """Generate full post content with images for 7 days ahead"""
        self.logger.info("=" * 60)
        self.logger.info("ACTION: Generate Posts & Images (7 Days)")
        self.logger.info("=" * 60)
        
        try:
            researcher = ContentResearcher()
            image_gen = ImageGenerator()
            airtable = AirtableIntegration()
            scheduler = LinkedInScheduler()
            
            # Get topics from config
            topics = self.config.get('content_research', {}).get('topics', [])
            posts_per_day = 3  # Always 3 posts per day
            days_to_schedule = 7  # Generate 7 days worth
            
            if not topics:
                self.logger.error("No topics configured")
                return False
            
            # Clean up old posted records first
            deleted_count = airtable.cleanup_old_posts(days_to_keep=7)
            self.logger.info(f"Cleaned up {deleted_count} old posted records")
            
            # Get randomized schedule times for 7 days
            scheduled_times = scheduler.get_schedule_times(days_ahead=days_to_schedule)
            total_posts = posts_per_day * days_to_schedule  # 21 posts
            
            # Generate daily content with day-aware context
            posts = researcher.generate_daily_content(
                topics, 
                posts_per_day=total_posts,
                scheduled_dates=scheduled_times
            )
            
            if not posts:
                self.logger.error("No posts generated")
                return False
            
            # Generate images for each post
            posts_with_images = image_gen.generate_batch_images(posts, save_locally=True)
            
            # Add to Airtable with scheduled times
            airtable_ids = []
            for idx, post in enumerate(posts_with_images):
                if idx < len(scheduled_times):
                    post['scheduled_time'] = scheduled_times[idx].isoformat()
                
                record_id = airtable.add_post(post)
                if record_id:
                    airtable_ids.append(record_id)
                    self.logger.info(f"Added post to Airtable: {record_id} (scheduled: {post.get('scheduled_time', 'N/A')})")
            
            self.logger.info(f"✓ Generated {len(posts_with_images)} posts with images for {days_to_schedule} days")
            self.logger.info(f"✓ Added {len(airtable_ids)} posts to Airtable (Awaiting Approval)")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in generate posts action: {e}")
            return False
    
    def action_schedule(self):
        """Schedule approved posts"""
        self.logger.info("=" * 60)
        self.logger.info("ACTION: Schedule Approved Posts")
        self.logger.info("=" * 60)
        
        try:
            airtable = AirtableIntegration()
            scheduler = LinkedInScheduler()
            
            # Get approved posts from Airtable
            approved_posts = airtable.get_approved_posts()
            
            if not approved_posts:
                self.logger.warning("No approved posts to schedule")
                return False
            
            # Get scheduling times
            scheduled_times = scheduler.get_schedule_times()
            scheduled_count = 0
            
            for i, post_record in enumerate(approved_posts[:len(scheduled_times)]):
                post_data = post_record.get('fields', {})
                
                # Schedule the post
                scheduled = scheduler.schedule_post(post_data, scheduled_times[i])
                
                if scheduled:
                    # Add to scheduling queue in Airtable
                    queue_id = airtable.add_to_scheduling_queue(
                        post_record.get('id'),
                        scheduled_times[i].isoformat()
                    )
                    
                    if queue_id:
                        scheduled_count += 1
            
            self.logger.info(f"✓ Scheduled {scheduled_count} posts")
            return True
            
        except Exception as e:
            self.logger.error(f"Error in schedule action: {e}")
            return False
    
    def action_post_now(self):
        """Post immediately (posts first approved post)"""
        self.logger.info("=" * 60)
        self.logger.info("ACTION: Post Now")
        self.logger.info("=" * 60)
        
        try:
            airtable = AirtableIntegration()
            scheduler = LinkedInScheduler()
            
            # Get approved posts ready to post
            approved_posts = airtable.get_approved_posts_for_scheduling()
            
            if not approved_posts:
                self.logger.warning("No approved posts ready to post")
                return False
            
            post_record = approved_posts[0]
            post_data = post_record.get('fields', {})
            record_id = post_record.get('id')
            
            self.logger.info(f"Posting: {post_data.get('Title', 'Untitled')}")
            
            # Publish immediately
            published = scheduler.publish_post(post_data)
            
            if published:
                # Update status to "Posted"
                airtable.update_post_status(record_id, "Posted")
                self.logger.info(f"✓ Posted successfully and updated status to 'Posted'")
                return True
            else:
                self.logger.error("Failed to publish post")
                return False
            
        except Exception as e:
            self.logger.error(f"Error in post now action: {e}")
            return False
    
    def action_revise(self):
        """Process content revision requests from Airtable Notes column"""
        self.logger.info("=" * 60)
        self.logger.info("ACTION: Process Content Revisions")
        self.logger.info("=" * 60)
        
        try:
            processor = ContentRevisionProcessor()
            revised_count = processor.check_for_revisions()
            
            if revised_count > 0:
                self.logger.info(f"✓ Processed {revised_count} revision request(s)")
                return True
            else:
                self.logger.info("No revision requests found in Notes column")
                return True
                
        except Exception as e:
            self.logger.error(f"Error in revise action: {e}")
            return False
    
    def action_daily(self):
        """Run complete daily workflow"""
        self.logger.info("=" * 60)
        self.logger.info("ACTION: Daily Workflow")
        self.logger.info("=" * 60)
        
        steps = [
            ("research", self.action_research),
            ("generate-posts", self.action_generate_posts),
            ("schedule", self.action_schedule)
        ]
        
        results = {}
        for step_name, step_func in steps:
            self.logger.info(f"\n>>> Running step: {step_name}")
            try:
                results[step_name] = step_func()
            except Exception as e:
                self.logger.error(f"Error in {step_name}: {e}")
                results[step_name] = False
        
        # Summary
        self.logger.info("\n" + "=" * 60)
        self.logger.info("DAILY WORKFLOW SUMMARY")
        self.logger.info("=" * 60)
        for step_name, success in results.items():
            status = "✓ PASS" if success else "✗ FAIL"
            self.logger.info(f"{status} - {step_name}")
        
        return all(results.values())
    
    def action_status(self):
        """Show automation status"""
        self.logger.info("=" * 60)
        self.logger.info("LINKEDIN AUTOMATION STATUS")
        self.logger.info("=" * 60)
        
        airtable = AirtableIntegration()
        scheduler = LinkedInScheduler()
        
        # Check Airtable connection
        try:
            pending = airtable.get_pending_posts()
            approved = airtable.get_approved_posts()
            
            self.logger.info(f"\nAirtable Status:")
            self.logger.info(f"  Pending Approval: {len(pending)}")
            self.logger.info(f"  Approved: {len(approved)}")
        except Exception as e:
            self.logger.warning(f"Could not get Airtable status: {e}")
        
        # Check credentials
        self.logger.info(f"\nCredentials Status:")
        
        creds = {
            'ANTHROPIC_API_KEY': 'Claude API',
            'AIRTABLE_API_KEY': 'Airtable API',
            'REPLICATE_API_TOKEN': 'Replicate API (Images)',
            'LINKEDIN_EMAIL': 'LinkedIn Email',
            'LINKEDIN_PASSWORD': 'LinkedIn Password'
        }
        
        for env_var, description in creds.items():
            value = os.getenv(env_var)
            status = "✓" if value else "✗"
            masked = value[:10] + "..." if value else "NOT SET"
            self.logger.info(f"  {status} {description}: {masked}")
        
        # Show next posting times
        self.logger.info(f"\nNext Posting Times:")
        next_times = scheduler.calculate_next_posting_times(hours_ahead=24)
        for t in next_times[:5]:
            self.logger.info(f"  {t.strftime('%Y-%m-%d %H:%M %Z')}")


def main():
    parser = argparse.ArgumentParser(
        description='LinkedIn Content Automation - Lead Generation System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python RUN_linkedin_automation.py --action research       # Research topics
  python RUN_linkedin_automation.py --action generate-posts # Generate posts + images
  python RUN_linkedin_automation.py --action schedule       # Schedule approved posts
  python RUN_linkedin_automation.py --action post-now       # Post immediately
  python RUN_linkedin_automation.py --action daily          # Full daily workflow
  python RUN_linkedin_automation.py --action status         # Check status
        """
    )
    
    parser.add_argument(
        '--action',
        choices=['research', 'generate-posts', 'schedule', 'post-now', 'daily', 'status', 'revise'],
        required=True,
        help='Action to perform'
    )
    
    args = parser.parse_args()
    
    orchestrator = LinkedInContentOrchestrator()
    
    action_map = {
        'research': orchestrator.action_research,
        'generate-posts': orchestrator.action_generate_posts,
        'schedule': orchestrator.action_schedule,
        'post-now': orchestrator.action_post_now,
        'daily': orchestrator.action_daily,
        'status': orchestrator.action_status,
        'revise': orchestrator.action_revise,
    }
    
    success = action_map[args.action]()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
