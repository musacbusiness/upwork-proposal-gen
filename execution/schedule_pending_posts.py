"""
Schedule posts when status changes to "Pending Review".
This script:
1. Fetches posts with status "Pending Review" that don't have a scheduled time
2. Generates random scheduled times (1-30 days from now at 9 AM)
3. Updates those posts with the scheduled time
"""

import os
import sys
import random
from pathlib import Path
from datetime import datetime, timedelta
import requests

def schedule_pending_posts():
    """Schedule posts that are in Pending Review status but not yet scheduled."""

    # Load environment
    env_file = "/Users/musacomma/Agentic Workflow/.env"
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"\'')

    api_key = os.environ.get('AIRTABLE_API_KEY')
    base_id = os.environ.get('AIRTABLE_BASE_ID')
    table_id = os.environ.get('AIRTABLE_LINKEDIN_TABLE_ID')

    url = f"https://api.airtable.com/v0/{base_id}/{table_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Fetch all posts
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Error fetching posts: {response.status_code}")
        return

    posts = response.json().get('records', [])

    print("="*80)
    print("📅 SCHEDULING PENDING POSTS")
    print("="*80 + "\n")

    scheduled_count = 0

    for post in posts:
        record_id = post['id']
        fields = post.get('fields', {})
        status = fields.get('Status', '')
        scheduled_time = fields.get('Scheduled Time')
        title = fields.get('Title', 'Unknown')

        # Check if post is in Pending Review and not yet scheduled
        if status == 'Pending Review' and not scheduled_time:
            # Generate random scheduled time
            days_offset = random.randint(1, 30)
            new_scheduled_time = (datetime.now() + timedelta(days=days_offset)).replace(hour=9, minute=0).isoformat()

            # Update the post
            update_url = f"{url}/{record_id}"
            update_payload = {
                "fields": {
                    "Scheduled Time": new_scheduled_time
                }
            }

            update_response = requests.patch(update_url, headers=headers, json=update_payload)

            if update_response.status_code == 200:
                scheduled_date = datetime.fromisoformat(new_scheduled_time).strftime('%A, %B %d, %Y at %I:%M %p')
                print(f"✅ Scheduled: {title}")
                print(f"   📅 {scheduled_date}\n")
                scheduled_count += 1
            else:
                print(f"❌ Error scheduling {title}: {update_response.status_code}\n")

    print("="*80)
    if scheduled_count > 0:
        print(f"✅ Scheduled {scheduled_count} post(s)")
    else:
        print("ℹ️  No posts to schedule (all pending posts already have scheduled times)")
    print("="*80)

if __name__ == "__main__":
    schedule_pending_posts()
