#!/usr/bin/env python3
"""
Modal Automation: Daily Post Inventory Maintenance (9 AM UTC)

This function runs on Modal (cloud-hosted, not local machine).
- Maintains 21 posts in Airtable with eligible statuses
- Deletes posts that have been posted for 7+ days
- Runs daily at 9 AM UTC

Deployment:
    modal deploy modal_maintain_inventory.py
"""

import os
import json
import requests
from datetime import datetime, timedelta, timezone
import sys
from pathlib import Path

# Import our local modules
sys.path.insert(0, str(Path(__file__).parent))

from draft_post_generator import DraftPostGenerator
from post_quality_checker import PostQualityChecker

# Modal imports
try:
    import modal
except ImportError:
    print("Installing modal...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "modal"])
    import modal


# Initialize Modal app
app = modal.App(name="linkedin-post-inventory")

# Environment variables for Modal
AIRTABLE_API_KEY = os.environ.get('AIRTABLE_API_KEY')
AIRTABLE_BASE_ID = os.environ.get('AIRTABLE_BASE_ID')
AIRTABLE_TABLE_ID = os.environ.get('AIRTABLE_LINKEDIN_TABLE_ID')
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')

# Target inventory size
TARGET_INVENTORY = 21

# Eligible statuses for counting
ELIGIBLE_STATUSES = ['Draft', 'Pending Review', 'Approved - Ready to Schedule', 'Scheduled']

# Time to keep posted posts before deletion (days)
DAYS_TO_KEEP_POSTED = 7


def get_airtable_headers():
    """Get headers for Airtable API requests."""
    return {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }


def get_eligible_posts_count():
    """Count posts with eligible statuses in Airtable.

    Returns:
        (count, records) - tuple of count and list of record objects
    """
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_ID}"
    headers = get_airtable_headers()

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            records = response.json().get('records', [])

            # Filter by eligible statuses
            eligible = [
                r for r in records
                if r.get('fields', {}).get('Status') in ELIGIBLE_STATUSES
            ]

            return len(eligible), records
        else:
            print(f"Error fetching records: {response.status_code}")
            return 0, []
    except Exception as e:
        print(f"Error getting posts count: {e}")
        return 0, []


def delete_old_posted_posts(all_records):
    """Delete posts that have been in 'Posted' status for 7+ days.

    Args:
        all_records: List of all Airtable records
    """
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_ID}"
    headers = get_airtable_headers()

    deleted_count = 0

    for record in all_records:
        fields = record.get('fields', {})
        status = fields.get('Status')

        # Check if post is in Posted status
        if status == 'Posted':
            # Get the posted date
            posted_at = fields.get('Posted At')

            if posted_at:
                try:
                    # Parse the posted date
                    posted_time = datetime.fromisoformat(posted_at.replace('Z', '+00:00'))

                    # Calculate days since posting
                    now = datetime.now(timezone.utc)
                    days_since_posted = (now - posted_time).days

                    # Delete if 7+ days have passed
                    if days_since_posted >= DAYS_TO_KEEP_POSTED:
                        record_id = record['id']
                        delete_url = f"{url}/{record_id}"

                        try:
                            del_response = requests.delete(
                                delete_url,
                                headers=headers,
                                timeout=10
                            )
                            if del_response.status_code == 200:
                                deleted_count += 1
                                print(f"✓ Deleted old posted post: {record_id}")
                            else:
                                print(f"✗ Failed to delete {record_id}: {del_response.status_code}")
                        except Exception as e:
                            print(f"✗ Error deleting record: {e}")

                except Exception as e:
                    print(f"Error parsing posted date: {e}")

    return deleted_count


def generate_and_upload_posts(count):
    """Generate and upload specified number of posts.

    Args:
        count: Number of posts to generate

    Returns:
        Number of successfully uploaded posts
    """
    gen = DraftPostGenerator()
    checker = PostQualityChecker()

    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_ID}"
    headers = get_airtable_headers()

    uploaded = 0

    for i in range(count):
        try:
            # Generate post
            post = gen.generate_draft_post(educational_mode=False)

            # Validate
            validation = checker.validate_post(post, check_duplicates=False)

            # Get framework mapping
            framework_airtable = gen.map_framework_to_airtable(post['framework'])

            # Upload to Airtable
            fields = {
                "Title": post['title'],
                "Post Content": post['full_content'],
                "Status": "Draft",
                "Writing Framework": framework_airtable,
                "Image Prompt": f"Visual: {post['visual_type']}",
                "Notes": f"Framework: {post['framework']}\nHook: {post['hook_type']}\nTopic: {post['post_topic']}"
            }

            payload = {"records": [{"fields": fields}]}

            response = requests.post(url, headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                uploaded += 1
            else:
                print(f"Upload failed for post {i+1}: {response.status_code}")

        except Exception as e:
            print(f"Error generating post {i+1}: {e}")

    return uploaded


def maintain_inventory_daily():
    """Daily task to maintain post inventory.

    - Checks current eligible posts count
    - Deletes old posted posts (7+ days old)
    - Generates new posts if needed to reach TARGET_INVENTORY
    """
    print("\n" + "="*80)
    print("📋 LINKEDIN POST INVENTORY MAINTENANCE (Modal)")
    print("="*80)
    print(f"Target inventory: {TARGET_INVENTORY} posts")
    print(f"Eligible statuses: {', '.join(ELIGIBLE_STATUSES)}")
    print(f"Auto-delete posted posts after: {DAYS_TO_KEEP_POSTED} days")

    # Step 1: Delete old posted posts
    print(f"\n1️⃣  DELETING OLD POSTED POSTS (7+ days old)...")
    eligible_count, all_records = get_eligible_posts_count()
    deleted = delete_old_posted_posts(all_records)
    print(f"   Deleted: {deleted} old posts")

    # Step 2: Check current eligible posts count
    print(f"\n2️⃣  CHECKING CURRENT INVENTORY...")
    eligible_count, _ = get_eligible_posts_count()
    print(f"   Current eligible posts: {eligible_count}/{TARGET_INVENTORY}")

    # Step 3: Generate new posts if needed
    posts_needed = TARGET_INVENTORY - eligible_count

    if posts_needed > 0:
        print(f"\n3️⃣  GENERATING NEW POSTS ({posts_needed} needed)...")
        uploaded = generate_and_upload_posts(posts_needed)
        print(f"   Generated and uploaded: {uploaded}/{posts_needed} posts")
    else:
        print(f"\n3️⃣  NO NEW POSTS NEEDED")
        print(f"   Inventory is at target ({eligible_count}/{TARGET_INVENTORY})")

    # Final count
    final_count, _ = get_eligible_posts_count()

    print(f"\n{'='*80}")
    print(f"✅ MAINTENANCE COMPLETE")
    print(f"   Final inventory: {final_count}/{TARGET_INVENTORY} eligible posts")
    print(f"   Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"{'='*80}\n")

    return {
        "success": True,
        "initial_count": eligible_count - posts_needed if posts_needed > 0 else eligible_count,
        "deleted": deleted,
        "generated": posts_needed,
        "final_count": final_count,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.function(
    secrets=[modal.Secret.from_name("linkedin-makecom-webhook")]
)
def post_scheduler_exact_minute():
    """
    Efficient post scheduler - runs once per minute at the top of the minute.
    Posts scheduled posts that match the current minute to Make.com webhook.

    Cost: 1,440 checks/day (once per minute) vs 17,280 with 5-second polling = 92% savings.

    Flow:
    1. Fetch all "Scheduled" posts with Scheduled Time populated
    2. Check if Scheduled Time falls within current minute (±0-60 seconds)
    3. For each match, call Make.com webhook with post content
    4. Make.com posts to LinkedIn and updates Airtable status to "Posted"
    """
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        base_id = AIRTABLE_BASE_ID
        table_id = AIRTABLE_TABLE_ID
        api_key = AIRTABLE_API_KEY
        make_webhook_url = os.environ.get('MAKE_LINKEDIN_WEBHOOK_URL')

        if not all([base_id, table_id, api_key, make_webhook_url]):
            logger.error("Missing Airtable or Make.com configuration")
            return {"success": False, "posted": 0}

        # Get current time (rounded to start of minute)
        now = datetime.now(timezone.utc)
        minute_start = now.replace(second=0, microsecond=0)
        minute_end = minute_start + timedelta(minutes=1)

        logger.info(f"Post scheduler check: {minute_start.isoformat()} to {minute_end.isoformat()}")

        # Fetch all records
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        url = f"https://api.airtable.com/v0/{base_id}/{table_id}"
        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code != 200:
            logger.error(f"Failed to fetch Airtable records: {response.status_code}")
            return {"success": False, "posted": 0}

        records = response.json().get('records', [])
        posted_count = 0

        # Find posts scheduled for this minute
        for record in records:
            fields = record.get('fields', {})
            status = fields.get('Status', '')
            record_id = record.get('id')
            scheduled_time_str = fields.get('Scheduled Time')

            if status == "Scheduled" and scheduled_time_str:
                try:
                    # Parse scheduled time
                    scheduled_time = datetime.fromisoformat(scheduled_time_str.replace('Z', '+00:00'))

                    # Check if scheduled time falls within current minute
                    if minute_start <= scheduled_time < minute_end:
                        logger.info(f"🎯 Posting {record_id} (scheduled for {scheduled_time_str})")

                        # Extract post content for Make.com
                        content = fields.get('Post Content', '') or fields.get('Content', '')
                        image_field = fields.get('Image', [])
                        image_url = ''

                        if isinstance(image_field, list) and len(image_field) > 0:
                            image_url = image_field[0].get('url', '')
                        else:
                            image_url = fields.get('Image URL', '')

                        if not content:
                            logger.warning(f"No content for post {record_id}")
                            continue

                        # Call Make.com webhook
                        payload = {
                            "record_id": record_id,
                            "content": content,
                            "base_id": base_id,
                            "table_id": table_id,
                            "scheduled_deletion_date": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
                        }

                        # Only include image_url if it's not empty (Make.com LinkedIn module may fail with empty string)
                        if image_url:
                            payload["image_url"] = image_url

                        try:
                            webhook_response = requests.post(make_webhook_url, json=payload, timeout=120)

                            if webhook_response.status_code == 200:
                                posted_count += 1
                                logger.info(f"✓ Posted {record_id} to LinkedIn via Make.com")
                            else:
                                logger.error(f"Make.com webhook failed for {record_id}: {webhook_response.status_code}")
                        except Exception as e:
                            logger.error(f"Error calling Make.com webhook for {record_id}: {e}")

                except ValueError as e:
                    logger.warning(f"Could not parse time for {record_id}: {scheduled_time_str}")

        logger.info(f"Post scheduler check complete. Posted {posted_count} posts.")
        return {"success": True, "posted": posted_count}

    except Exception as e:
        logger.error(f"Post scheduler error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "posted": 0}


@app.function(
    schedule=modal.Cron("* * * * *"),  # Run every minute
    secrets=[
        modal.Secret.from_name("linkedin-makecom-webhook"),
        modal.Secret.from_name("airtable-credentials"),
        modal.Secret.from_name("anthropic-credentials")
    ]
)
def unified_scheduler():
    """
    Unified scheduler running every minute - handles both:
    1. Posting: Checks every minute for posts scheduled in this minute
    2. Inventory: At 9:00 AM UTC, maintains 21-post inventory

    This single cron job keeps us within Modal's 5-job limit while handling
    all LinkedIn post automation needs.
    """
    now = datetime.now(timezone.utc)
    hour = now.hour
    minute = now.minute

    results = {"minute_check": None, "inventory_check": None}

    # Check for posts to post every minute
    results["minute_check"] = post_scheduler_exact_minute.remote()

    # At 9:00 AM UTC, also run inventory maintenance
    if hour == 9 and minute == 0:
        results["inventory_check"] = maintain_inventory_daily()

    return results


if __name__ == "__main__":
    # For local testing only
    print("This script is designed to run on Modal.")
    print("To deploy: modal deploy modal_maintain_inventory.py")
    print("To test locally: python -m modal run modal_maintain_inventory.py::maintain_inventory")
