"""
Modal Cloud Deployment for LinkedIn Content Automation
=======================================================

Serverless webhooks + cron scheduling for LinkedIn content generation,
image generation, scheduling, and posting.

Deploy:
    modal deploy cloud/modal_linkedin_automation.py

Test locally:
    modal serve cloud/modal_linkedin_automation.py

Endpoints:
- POST /webhook/status-change - Handle Airtable status changes (Draft→Pending, Pending→Approved, Rejected)
- POST /webhook/schedule-check - Check for posts ready to schedule and post
- GET  /health - Health check

Scheduled Tasks (Cron):
- Every 4 hours: Check for posts ready to schedule and auto-post them
- Daily 6 AM UTC: Generate new content posts

Workflow:
1. Content generated → Status: Draft
2. User changes to Pending Review → Webhook triggers image generation
3. User changes to Approved → Webhook triggers auto-scheduling
4. Auto-scheduler posts → Status: Posted (system updates)
5. 7-day timer starts for deletion
6. If Rejected → 24-hour timer starts for deletion
"""

import modal
from modal import fastapi_endpoint, Period
import os
import json
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import logging

# ============== Modal App Setup ==============

app = modal.App("linkedin-automation")

# Base image with all dependencies
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "anthropic>=0.39",
        "requests>=2.32",
        "python-dotenv>=1.0",
        "aiohttp>=3.9",
        "pillow>=10.0",
        "pytz>=2024.1",
        "fastapi>=0.104",
    )
)


# ============== Helper Functions ==============

def get_airtable_headers():
    """Get Airtable API headers"""
    return {
        'Authorization': f'Bearer {os.environ.get("AIRTABLE_API_KEY")}',
        'Content-Type': 'application/json'
    }


def get_airtable_record(base_id: str, table_id: str, record_id: str) -> dict:
    """Fetch a single Airtable record"""
    url = f"https://api.airtable.com/v0/{base_id}/{table_id}/{record_id}"
    response = requests.get(url, headers=get_airtable_headers(), timeout=30)

    if response.status_code == 200:
        return response.json()
    else:
        logging.error(f"Failed to fetch record: {response.status_code} - {response.text}")
        return None


def update_airtable_record(base_id: str, table_id: str, record_id: str, fields: dict) -> bool:
    """Update an Airtable record with retry logic for reliability"""
    import time
    url = f"https://api.airtable.com/v0/{base_id}/{table_id}/{record_id}"
    payload = {"fields": fields}

    max_retries = 3
    retry_delay = 1  # seconds

    for attempt in range(max_retries):
        try:
            response = requests.patch(url, json=payload, headers=get_airtable_headers(), timeout=30)

            if response.status_code == 200:
                logging.info(f"Updated record {record_id} (attempt {attempt + 1}/{max_retries})")
                return True
            elif response.status_code == 429:  # Rate limit
                logging.warning(f"Rate limited. Retrying in {retry_delay}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                continue
            else:
                logging.error(f"Failed to update record: {response.status_code} - {response.text}")
                if attempt < max_retries - 1:
                    logging.info(f"Retrying... (attempt {attempt + 2}/{max_retries})")
                    time.sleep(retry_delay)
                continue
        except requests.exceptions.Timeout:
            logging.warning(f"Timeout updating record. Retrying... (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            continue
        except Exception as e:
            logging.error(f"Error updating record: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            continue

    logging.error(f"Failed to update record {record_id} after {max_retries} attempts")
    return False


def add_airtable_record(base_id: str, table_id: str, fields: dict) -> Optional[str]:
    """Add a new Airtable record and return the record ID"""
    url = f"https://api.airtable.com/v0/{base_id}/{table_id}"
    payload = {"records": [{"fields": fields}]}

    response = requests.post(url, json=payload, headers=get_airtable_headers(), timeout=30)

    if response.status_code == 201:
        records = response.json().get('records', [])
        if records:
            return records[0]['id']
    else:
        logging.error(f"Failed to add record: {response.status_code} - {response.text}")

    return None


def delete_airtable_record(base_id: str, table_id: str, record_id: str) -> bool:
    """Delete an Airtable record"""
    url = f"https://api.airtable.com/v0/{base_id}/{table_id}/{record_id}"

    response = requests.delete(url, headers=get_airtable_headers(), timeout=30)

    if response.status_code == 200:
        logging.info(f"Deleted record {record_id}")
        return True
    else:
        logging.error(f"Failed to delete record: {response.status_code} - {response.text}")
        return False


# ============== Core Automation Functions ==============

@app.function(image=image, secrets=[modal.Secret.from_name("linkedin-secrets")], timeout=300)
def generate_images_for_post(record_id: str, base_id: str, table_id: str) -> bool:
    """
    Generate AI images for a post that's in Pending Review status.

    This is triggered when a post status changes to "Pending Review".
    """
    import time
    from pathlib import Path

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Starting image generation for record {record_id}")

        # Fetch the record
        record = get_airtable_record(base_id, table_id, record_id)
        if not record:
            logger.error(f"Could not fetch record {record_id}")
            return False

        fields = record.get('fields', {})
        post_content = fields.get('Post Content', '')
        image_prompt_base = fields.get('Image Prompt', '')

        if not post_content and not image_prompt_base:
            logger.error("No content or image prompt found")
            return False

        # Generate image prompt if not exists
        if not image_prompt_base:
            from anthropic import Anthropic
            client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

            response = client.messages.create(
                model="claude-opus-4-20250514",
                max_tokens=300,
                messages=[{
                    "role": "user",
                    "content": f"""Based on this LinkedIn post, generate a detailed image prompt for a professional business graphic (1200x1200px):

Post: {post_content[:500]}

Generate a prompt that would create a professional, visually engaging image that complements this post. Be specific about style, colors, and elements."""
                }]
            )

            image_prompt = response.content[0].text.strip()
        else:
            image_prompt = image_prompt_base

        # Generate image using Replicate
        import subprocess

        logger.info(f"Generating image with prompt: {image_prompt[:100]}...")

        # Call Replicate API
        replicate_token = os.environ.get("REPLICATE_API_TOKEN")
        headers = {
            "Authorization": f"Token {replicate_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "version": "google/nano-banana-pro",  # High-quality model
            "input": {
                "prompt": image_prompt + ", professional photography, photorealistic, candid moment, natural lighting, 4K, sharp focus, documentary style, editorial photography, authentic business scenario, high detail",
                "width": 1200,
                "height": 1200,
                "num_inference_steps": 50,  # Higher steps for better quality
                "guidance_scale": 8.5,  # Slightly higher guidance for consistency with prompt
                "negative_prompt": "cartoon, illustration, abstract, stock photo, generic, blurry, distorted, ugly, text, watermark, AI art, synthetic, unrealistic, painting, drawing, anime"
            }
        }

        # Create prediction
        response = requests.post(
            "https://api.replicate.com/v1/predictions",
            json=payload,
            headers=headers,
            timeout=30
        )

        if response.status_code != 201:
            logger.error(f"Failed to create prediction: {response.status_code} - {response.text}")
            return False

        prediction = response.json()
        prediction_id = prediction.get('id')

        logger.info(f"Prediction created: {prediction_id}, waiting for completion...")

        # Poll for completion (max 5 minutes)
        max_wait = 300
        start_time = datetime.now()
        image_url = None

        while (datetime.now() - start_time).total_seconds() < max_wait:
            response = requests.get(
                f"https://api.replicate.com/v1/predictions/{prediction_id}",
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                status = result.get('status')

                if status == 'succeeded':
                    output = result.get('output')
                    if output:
                        image_url = output[0] if isinstance(output, list) else output
                        break
                elif status == 'failed':
                    logger.error(f"Prediction failed: {result.get('error')}")
                    return False

                time.sleep(2)
            else:
                logger.error(f"Error polling prediction: {response.status_code}")
                return False

        if not image_url:
            logger.error("Image generation timed out")
            return False

        logger.info(f"Image generated: {image_url}")

        # Download the image
        try:
            logger.info("Downloading generated image...")
            img_response = requests.get(image_url, timeout=30)
            if img_response.status_code != 200:
                logger.error(f"Failed to download image: {img_response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error downloading image: {e}")
            return False

        # Upload to Airtable as attachment
        try:
            logger.info("Uploading image to Airtable...")
            # Airtable attachment format
            update_fields = {
                "Image": [
                    {
                        "url": image_url
                    }
                ],
                "Image Prompt": image_prompt
            }

            success = update_airtable_record(base_id, table_id, record_id, update_fields)

            if success:
                logger.info(f"Record updated with generated image")
                return True
            else:
                logger.error("Failed to update record with image")
                return False
        except Exception as e:
            logger.error(f"Error uploading image to Airtable: {e}")
            return False

    except Exception as e:
        logging.error(f"Error in image generation: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return False


@app.function(image=image, secrets=[modal.Secret.from_name("linkedin-secrets")], timeout=300)
def schedule_approved_post(record_id: str, base_id: str, table_id: str) -> bool:
    """
    Schedule an approved post for publishing.

    This is triggered when status changes to "Approved - Ready to Schedule".

    Distributes posts across all 3 daily posting windows:
    - 9 AM (±15 min)
    - 2 PM (±15 min)
    - 8 PM (±15 min)

    Includes retry logic and race condition detection.
    """
    import pytz
    from datetime import datetime, timedelta
    import random
    import time

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Scheduling approved post {record_id}")

        # Fetch the record
        record = get_airtable_record(base_id, table_id, record_id)
        if not record:
            logger.error(f"Could not fetch record {record_id}")
            return False

        fields = record.get('fields', {})

        # Check if post is approved (or already scheduled - race condition protection)
        status = fields.get('Status', '')
        if status not in ['Approved - Ready to Schedule', 'Scheduled']:
            logger.warning(f"Post status is {status}, not 'Approved - Ready to Schedule'")
            return False

        # If already scheduled and has a Scheduled Time, it was already processed
        if status == 'Scheduled' and fields.get('Scheduled Time'):
            logger.info(f"Post already scheduled (race condition detected). Skipping.")
            return True

        logger.info(f"Post status: {status}")

        # Get next available posting time
        tz = pytz.timezone('America/New_York')
        now = datetime.now(tz)

        # Posting times: 9 AM, 2 PM, 8 PM with random offset (±15 min)
        posting_times = [9, 14, 20]

        # Get all records to see which posting windows are already used today
        # Track which posting window (9 AM, 2 PM, 8 PM) is used, not just the hour
        try:
            headers = {
                'Authorization': f'Bearer {os.environ.get("AIRTABLE_API_KEY")}',
                'Content-Type': 'application/json'
            }
            url = f"https://api.airtable.com/v0/{base_id}/{table_id}"
            response = requests.get(url, headers=headers)

            used_posting_windows = set()  # Will contain 9, 14, or 20
            if response.status_code == 200:
                records = response.json().get('records', [])
                for record in records:
                    scheduled_time_str = record.get('fields', {}).get('Scheduled Time')
                    if scheduled_time_str:
                        try:
                            scheduled = datetime.fromisoformat(scheduled_time_str).astimezone(tz)
                            # Check if scheduled for today
                            if scheduled.date() == now.date():
                                # Determine which posting window this is closest to
                                for window_hour in posting_times:
                                    # Window is used if scheduled time is within 30 min of that window
                                    window_time = scheduled.replace(hour=window_hour, minute=0, second=0, microsecond=0)
                                    time_diff = abs((scheduled - window_time).total_seconds() / 60)
                                    if time_diff <= 30:  # Within 30 minutes of the window
                                        used_posting_windows.add(window_hour)
                                        logger.info(f"Posting window {window_hour}:00 already has a post scheduled today")
                                        break
                        except:
                            pass
            logger.info(f"Used posting windows today: {sorted(used_posting_windows)}")
        except Exception as e:
            logger.warning(f"Could not check used posting times: {e}")
            used_posting_windows = set()

        # Find next available slot today (excluding already-used windows)
        scheduled_time = None
        for hour in posting_times:
            # Skip if this posting window is already used today
            if hour in used_posting_windows:
                logger.info(f"Posting window {hour}:00 already used, skipping to next window")
                continue

            test_time = now.replace(hour=hour, minute=0, second=0, microsecond=0)

            # Add random offset (±15 min)
            offset_minutes = random.randint(-15, 15)
            test_time = test_time + timedelta(minutes=offset_minutes)

            # Only schedule if the time is in the future
            if test_time > now:
                scheduled_time = test_time
                logger.info(f"Found available window at {hour}:00 (scheduled for {test_time.strftime('%I:%M %p %Z')} with {offset_minutes:+d} min offset)")
                break

        # If no time today, check tomorrow's windows
        if not scheduled_time:
            tomorrow = now + timedelta(days=1)

            # Check which windows are already used TOMORROW
            used_windows_tomorrow = set()
            try:
                headers = {
                    'Authorization': f'Bearer {os.environ.get("AIRTABLE_API_KEY")}',
                    'Content-Type': 'application/json'
                }
                url = f"https://api.airtable.com/v0/{base_id}/{table_id}"
                response = requests.get(url, headers=headers)

                if response.status_code == 200:
                    all_records = response.json().get('records', [])
                    for record in all_records:
                        scheduled_time_str = record.get('fields', {}).get('Scheduled Time')
                        if scheduled_time_str:
                            try:
                                scheduled = datetime.fromisoformat(scheduled_time_str).astimezone(tz)
                                # Check if scheduled for tomorrow
                                if scheduled.date() == tomorrow.date():
                                    # Determine which posting window this is closest to
                                    for window_hour in posting_times:
                                        window_time = scheduled.replace(hour=window_hour, minute=0, second=0, microsecond=0)
                                        time_diff = abs((scheduled - window_time).total_seconds() / 60)
                                        if time_diff <= 30:
                                            used_windows_tomorrow.add(window_hour)
                                            logger.info(f"Tomorrow's posting window {window_hour}:00 already has a post scheduled")
                                            break
                            except:
                                pass
            except Exception as e:
                logger.warning(f"Could not check tomorrow's used windows: {e}")

            logger.info(f"Tomorrow's used windows: {sorted(used_windows_tomorrow)}")

            # Find first available window tomorrow
            scheduled_time = None
            for hour in posting_times:
                if hour not in used_windows_tomorrow:
                    test_time = tomorrow.replace(hour=hour, minute=0, second=0, microsecond=0)
                    offset_minutes = random.randint(-15, 15)
                    test_time = test_time + timedelta(minutes=offset_minutes)
                    scheduled_time = test_time
                    logger.info(f"No slots available today. Scheduled for tomorrow at {hour}:00 (offset: {offset_minutes} min)")
                    break

            # If all tomorrow windows are full, use 9 AM day after tomorrow
            if not scheduled_time:
                day_after = now + timedelta(days=2)
                scheduled_time = day_after.replace(hour=9, minute=0, second=0, microsecond=0)
                offset_minutes = random.randint(-15, 15)
                scheduled_time = scheduled_time + timedelta(minutes=offset_minutes)
                logger.info(f"All windows full for next 2 days. Scheduled for {day_after.date()} at 9:00 AM (offset: {offset_minutes} min)")

        logger.info(f"Scheduled post for: {scheduled_time} ({scheduled_time.strftime('%I:%M %p %Z')})")

        # Update record with scheduled time and status
        update_fields = {
            "Status": "Scheduled",
            "Scheduled Time": scheduled_time.isoformat(),
            "Scheduled At": datetime.now().isoformat()
        }

        success = update_airtable_record(base_id, table_id, record_id, update_fields)

        if success:
            logger.info(f"Post scheduled for {scheduled_time}")
            return True
        else:
            logger.error("Failed to update record with scheduled time")
            return False

    except Exception as e:
        logging.error(f"Error scheduling post: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return False


@app.function(image=image, secrets=[modal.Secret.from_name("linkedin-secrets"), modal.Secret.from_name("linkedin-makecom-webhook")], timeout=180)
def post_to_linkedin_via_makecom(record_id: str, base_id: str, table_id: str) -> bool:
    """
    Post content to LinkedIn using Make.com webhook with Linkup API.
    Avoids LinkedIn security checkpoints by using Make.com's enterprise integration.
    Updates record status to "Posted" and schedules deletion.
    """
    import requests

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Posting to LinkedIn via Make.com webhook for record {record_id}")

        # Fetch the record
        record = get_airtable_record(base_id, table_id, record_id)
        if not record:
            logger.error(f"Could not fetch record {record_id}")
            return False

        fields = record.get('fields', {})
        content = fields.get('Post Content', '') or fields.get('Content', '')

        # Handle Airtable attachment array properly
        image_field = fields.get('Image', [])
        if isinstance(image_field, list) and len(image_field) > 0:
            image_url = image_field[0].get('url', '')
        else:
            image_url = fields.get('Image URL', '')  # Fallback

        if not content:
            logger.error("No content to post")
            return False

        # Get Make.com webhook URL from environment
        webhook_url = os.environ.get('MAKE_LINKEDIN_WEBHOOK_URL')
        if not webhook_url:
            logger.error("MAKE_LINKEDIN_WEBHOOK_URL not configured")
            return False

        # Prepare webhook payload
        payload = {
            "record_id": record_id,
            "content": content,
            "image_url": image_url,
            "base_id": base_id,
            "table_id": table_id,
            "scheduled_deletion_date": (datetime.now() + timedelta(days=7)).isoformat()
        }

        # Call Make.com webhook
        logger.info(f"Sending post to Make.com webhook for record {record_id}")
        response = requests.post(webhook_url, json=payload, timeout=120)

        if response.status_code == 200:
            logger.info(f"Make.com webhook accepted post for {record_id}")

            # Update Airtable status (Make.com will post to LinkedIn)
            deletion_date = (datetime.now() + timedelta(days=7)).isoformat()
            update_fields = {
                "Status": "Posted",
                "Posted At": datetime.now().isoformat(),
                "Scheduled Deletion Date": deletion_date
            }

            success = update_airtable_record(base_id, table_id, record_id, update_fields)

            if success:
                logger.info(f"Updated Airtable for record {record_id}")
                schedule_deletion_task.spawn(record_id, base_id, table_id, deletion_date)
                return True
            else:
                logger.error(f"Failed to update Airtable for {record_id}")
                return False
        else:
            logger.error(f"Make.com webhook failed with status {response.status_code}: {response.text}")
            return False

    except Exception as e:
        logger.error(f"Error posting via Make.com webhook: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


@app.function(image=image, secrets=[modal.Secret.from_name("linkedin-secrets")], timeout=60)
def schedule_deletion_task(record_id: str, base_id: str, table_id: str, deletion_date: str) -> None:
    """
    Schedule a record for deletion on a specific date.
    This would be called by post_to_linkedin (7 days) or handle_rejected (24 hours).

    Note: Modal doesn't have persistent scheduled tasks, so this uses a workaround.
    In production, you'd use a proper job queue (e.g., Celery + Redis).
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info(f"Deletion scheduled for record {record_id} on {deletion_date}")

    # Store deletion task in Airtable
    # In a real system, you'd push this to a job queue or database
    # The cron job will periodically check for records ready to delete

    logger.info(f"Record {record_id} scheduled for deletion at {deletion_date}")


@app.function(image=image, secrets=[modal.Secret.from_name("linkedin-secrets")], timeout=300)
def handle_rejected_post(record_id: str, base_id: str, table_id: str) -> bool:
    """
    Handle a rejected post.
    Schedule it for deletion 24 hours from now.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Handling rejected post {record_id}")

        # Calculate deletion date (24 hours from now)
        deletion_date = (datetime.now() + timedelta(hours=24)).isoformat()

        # Update record with scheduled deletion
        update_fields = {
            "Status": "Rejected",
            "Rejected At": datetime.now().isoformat(),
            "Scheduled Deletion Date": deletion_date
        }

        success = update_airtable_record(base_id, table_id, record_id, update_fields)

        if success:
            logger.info(f"Rejected post scheduled for deletion in 24 hours")

            # Schedule deletion
            schedule_deletion_task.spawn(record_id, base_id, table_id, deletion_date)

            return True
        else:
            logger.error("Failed to update rejected record")
            return False

    except Exception as e:
        logging.error(f"Error handling rejected post: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return False


# ============== Cron Jobs ==============

def proofread_post(post_text: str, client) -> str:
    """
    Proofread and fix grammar/spelling errors in LinkedIn post.
    Returns corrected post text.
    """
    try:
        response = client.messages.create(
            model="claude-opus-4-5-20251101",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": f"""Proofread this LinkedIn post for grammar, spelling, and punctuation errors.
Fix any issues while maintaining the authentic voice and tone.
If there are no errors, return the post exactly as-is.

IMPORTANT: Return ONLY the corrected post text. No explanations or comments.

Post:
{post_text}"""
            }]
        )

        corrected_text = response.content[0].text.strip()
        return corrected_text
    except Exception as e:
        logging.warning(f"Error during proofreading: {e}")
        # Return original if proofreading fails
        return post_text


@app.function(image=image, secrets=[modal.Secret.from_name("linkedin-secrets")], timeout=3600)
def generate_daily_content():
    """
    Generate new content posts daily.
    Creates 21 posts (7 days × 3 posts/day) with Draft status.
    """
    from anthropic import Anthropic
    import json
    import random
    import pytz

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        logger.info("Running daily content generation")

        base_id = os.environ.get('AIRTABLE_BASE_ID')
        table_id = os.environ.get('AIRTABLE_LINKEDIN_TABLE_ID')
        anthropic_key = os.environ.get('ANTHROPIC_API_KEY')

        if not all([base_id, table_id, anthropic_key]):
            logger.error("Missing required environment variables")
            return False

        client = Anthropic(api_key=anthropic_key)

        # Configuration - Diverse topics across personal experience, industry trends, and tactics
        # See MUSA_VOICE_PROFILE.md for complete context on tone and approach
        # Mix of: personal stories, automation insights, AI trends, niche-specific strategies
        topics = [
            # Personal Experience (Musa's Journey)
            'Why my first business (MC Marketing) failed and what I learned',
            'The real cost of manual processes your business ignores',
            'How 5 people can scale like 50 with the right automation',
            'Small businesses winning against enterprises through automation',
            'Why marketing services failed before I tried automation',

            # AI & Automation Trends & Benefits
            'How AI is reshaping business operations in 2025',
            'The difference between AI hype and AI reality for small teams',
            'Why most businesses are underutilizing their AI investments',
            'How automation platforms free up time for what actually matters',
            'How AI chatbots are transforming customer service workflows',
            'The 3 AI breakthroughs that will define 2025 for your business',
            'Why AI adoption is accelerating faster than you think',
            'The automation ROI that nobody talks about',
            'How businesses are quietly doubling productivity with AI',
            'The hidden cost of staying manual in an AI-powered world',

            # Practical Examples: Automation Helping Businesses Thrive
            'How a plumbing company cut scheduling time by 90%',
            'The e-commerce team that reduced customer service response time from 6 hours to 2 minutes',
            'How a 2-person consulting firm handles 50+ client workflows automatically',
            'The fitness studio that grew 200% without hiring more staff (automation did the work)',
            'How a digital marketing agency cut project delivery time in half',
            'The accounting firm that eliminated data entry errors entirely with automation',
            'How a SaaS company reduced onboarding time from weeks to hours',
            'The real estate team that closes 40% more deals with AI lead qualification',
            'How a course creator automates everything except teaching',
            'The recruitment agency that screens candidates 10x faster',

            # Real Estate Agent Niche
            'How real estate agents are using AI to close 30% more deals',
            'The automation strategy real estate agents need right now',
            'AI lead scoring: How agents qualify 10x faster',
            'Real estate follow-up automation that converts',

            # Social Media Marketing Agency Niche
            'How social media agencies are scaling without hiring',
            'AI content calendars: The competitive advantage agencies are using',
            'How agencies are automating client reporting and saving 10+ hours/week',

            # Prompting & AI Tactics (20 Topics - Practical, Action-Oriented)
            'The one-line prompt that unlocked 60% better AI outputs',
            'How to talk to AI like you talk to a contractor (and get 10x better results)',
            'The prompt template I use for every business automation',
            'Why your AI outputs are mediocre (and how to fix it in 30 seconds)',
            'The 5-part prompt framework that transforms generic to genius',
            'How context beats complexity in AI prompts',
            'The constraint that made my AI outputs 100x more useful',
            'Why you should never ask AI yes-or-no questions (and what to ask instead)',
            'The prompt pattern that keeps AI focused on what actually matters',
            'How to debug a broken prompt (before you blame the AI)',
            'The system prompt hack that changed my AI game',
            'Why "be more detailed" is the worst prompt advice (and what actually works)',
            'The role-play prompt that makes AI think like your ideal employee',
            'How to use examples in prompts to get exactly what you want',
            'The iterative prompt technique that fixes 80% of bad outputs',
            'Why specificity matters more than length in prompts',
            'The output format trick that eliminates AI hallucinations',
            'How to chain prompts to solve problems AI cannot solve alone',
            'The prompt that turned my AI from assistant to strategist',
            'Why you should debate with your AI (and how to do it right)'
        ]

        posts_per_day = 3
        days_ahead = 7
        total_posts = posts_per_day * days_ahead  # 21 posts
        max_posts_threshold = 21  # Stop generation when this many posts exist

        logger.info(f"Generating {total_posts} posts for {days_ahead} days")

        # Check current post count - suspend if we're at threshold
        try:
            headers = {
                'Authorization': f'Bearer {os.environ.get("AIRTABLE_API_KEY")}',
                'Content-Type': 'application/json'
            }
            url = f"https://api.airtable.com/v0/{base_id}/{table_id}"
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                records = response.json().get('records', [])
                current_post_count = len(records)
                logger.info(f"Current post count: {current_post_count}")

                if current_post_count >= max_posts_threshold:
                    logger.info(f"Post threshold reached ({current_post_count}/{max_posts_threshold}). Suspending generation.")
                    return True  # Return success without generating - suspension is normal
            else:
                logger.warning(f"Could not check post count: {response.status_code}")
        except Exception as e:
            logger.warning(f"Error checking post count: {e}")
            # Continue with generation if check fails

        # Research topics and generate ideas
        logger.info("Researching topics and generating ideas...")

        # Randomize topic selection to avoid monotone content
        import random
        topics_shuffled = random.sample(topics, min(len(topics), max(3, len(topics)//2)))
        logger.info(f"Selected {len(topics_shuffled)} randomized topics for generation")

        all_ideas = []

        for topic in topics_shuffled:
            logger.info(f"Researching topic: {topic}")

            try:
                message = client.messages.create(
                    model="claude-opus-4-5-20251101",
                    max_tokens=4000,
                    messages=[{
                        "role": "user",
                        "content": f"""Generate 3 LinkedIn post ideas from Musa Comma's perspective about: {topic}

Context from MUSA_VOICE_PROFILE.md:
- 23-year-old self-taught founder of ScaleAxis
- Previously ran MC Marketing Solutions (learned it failed due to wrong market segment)
- Believes real software beats platform constraints
- Decision framework: opportunity cost + speed-to-payback + potential
- Communication style: direct, blunt, no corporate speak, authentic
- Avoids: fake credentials, false accomplishments, hype without substance
- Values: truth, authenticity, real client transformation over valuations

For each idea, provide:
1. Content Type (Personal Story, Founder Insight, Real Case Study, Lesson Learned, ROI Breakdown)
2. Post Title (compelling, in Musa's direct voice)
3. Post Description (1-2 sentences - the core insight)
4. Key Points (3 concrete actionable points)
5. Image Concept (realistic, professional business scenario - not abstract)

Requirements:
- Based on REAL experience (MC Marketing, ScaleAxis, automation insights)
- Reflect his three-angle thinking (opportunity cost, payback, potential)
- Grounded in actual business problems
- No fake company names, metrics, or team members
- Tone: direct, problem-focused, conversational

IMPORTANT: Respond ONLY with valid JSON array.
[{{"type": "Personal Story", "title": "Title", "description": "Desc", "key_points": ["P1", "P2", "P3"], "image_concept": "Concept"}}]"""
                    }]
                )

                response_text = message.content[0].text.strip()

                # Clean up markdown if present
                if response_text.startswith('```'):
                    response_text = response_text.split('```')[1]
                    if response_text.startswith('json'):
                        response_text = response_text[4:]

                ideas = json.loads(response_text.strip())
                for idea in ideas:
                    idea['topic'] = topic
                all_ideas.extend(ideas)

                logger.info(f"Generated {len(ideas)} ideas for {topic}")

            except Exception as e:
                logger.warning(f"Error researching topic {topic}: {e}")
                continue

        if not all_ideas:
            logger.error("No ideas generated")
            return False

        logger.info(f"Total ideas generated: {len(all_ideas)}")

        # Generate full posts from ideas
        logger.info("Generating full post content...")

        tz = pytz.timezone('America/New_York')
        posts_created = 0

        for i in range(total_posts):
            try:
                # Select idea (cycle through available ideas)
                idea = all_ideas[i % len(all_ideas)]

                # Determine what day this post is for
                day_num = i // posts_per_day
                post_date = datetime.now(tz) + timedelta(days=day_num)

                # Add day context
                day_name = post_date.strftime('%A')
                idea_with_context = {**idea, 'day_context': day_name}

                # Generate post content
                prompt = f"""Create an authentic LinkedIn post written from Musa Comma's perspective.

VOICE PROFILE REFERENCE: See MUSA_VOICE_PROFILE.md
- 23-year-old founder of ScaleAxis, self-taught
- MC Marketing Solutions background (learned lesson about wrong market)
- Philosophy: Analyze → Leap of Faith → Learn from outcome
- No fear approach: "Can I survive worst case? Will I learn? Yes to both → fear eliminated"
- Three-angle thinking: opportunity cost + speed-to-payback + potential
- Communication: direct, blunt, conversational, calls out BS
- Avoids: hype, fake credentials, false accomplishments
- Values: truth over polish, authentic over generic
- Actual WHY: client transformation (not billion-dollar valuation)

Post Topic: {idea.get('title', '')}
Type: {idea.get('type', '')}
Context: {idea.get('description', '')}
Key Points: {', '.join(idea.get('key_points', []))}

Requirements:
1. First-person, sound like Musa wrote it naturally
2. 150-300 words, conversational
3. Ground in REAL experience (MC Marketing, ScaleAxis, automation insights)
4. Show why he cares (client transformation, not validation)
5. Use his decision framework (opportunity cost, payback, potential)
6. Be direct and blunt where appropriate
7. NO: fake names, false metrics, CFOs that don't exist, hype
8. YES: practical insight, real experience, honest assessment
9. Subtle CTA (not pushy), 2-3 hashtags, natural line breaks
10. Include specific number/real data if contextually relevant

Generate ONLY the post text itself."""

                message = client.messages.create(
                    model="claude-opus-4-5-20251101",
                    max_tokens=800,
                    messages=[{"role": "user", "content": prompt}]
                )

                post_text = message.content[0].text.strip()

                # Proofread post for grammar and spelling errors
                post_text = proofread_post(post_text, client)
                logger.info(f"Proofread post completed")

                # Generate image prompt - RELEVANCE-FOCUSED FOR LINKEDIN ENGAGEMENT
                image_prompt_msg = client.messages.create(
                    model="claude-opus-4-5-20251101",
                    max_tokens=400,
                    messages=[{
                        "role": "user",
                        "content": f"""Generate a precise, LinkedIn-optimized image prompt (1200x1200px square).

Post Topic: {idea.get('title', '')}
Post Type: {idea.get('type', '')}
Post Content (first 200 chars): {post_text[:200]}

CRITICAL: Image must directly relate to and reinforce the post topic. NO generic business photos.

Visual Strategy Based on Post Type:

IF Tactical/Prompting Content:
→ Data visualization, before/after transformation, or chart showing improvement
→ Example: Graph with dramatic improvement curve, checklist being completed, problem being solved visually

IF Business Success Story/Practical Example:
→ Authentic workplace scenario showing the result (not the problem)
→ Real people working, genuine reactions, specific to the industry mentioned
→ Example: Scheduling app on screen with calendar full, happy team member, actual workspace

IF AI Trend Content:
→ Data visualization, trend chart, or conceptual diagram
→ Modern, clean aesthetic showing the concept clearly
→ Example: 2025 timeline with growth trajectory, feature comparison chart, industry insight visualization

IF Prompting/Skills Teaching:
→ Visual breakdown of the concept - contrast between wrong and right approach
→ Infographic-style showing the framework or pattern
→ Example: Split screen (messy vs. organized), framework diagram, step-by-step visual

IF Personal/Authentic Story:
→ Real team member, genuine workspace moment, not posed
→ Candid moment showing authenticity over polish
→ Example: Team member actually working, office environment, authentic expression

Design Requirements:
- Clean composition with ONE clear focal point (where eye lands first)
- High contrast to stop scrollers
- Minimal white space (breathing room, not cluttered)
- 1200x1200px square format
- Sharp, professional quality
- Readable at feed size (mobile-first design)
- No text overlays unless data visualization
- If text: 18pt+ sans-serif, high contrast (dark on light or light on dark)
- Color psychology: bold but professional (blues, greens, modern tones)

Authenticity Requirements:
- Real people over models
- Genuine scenarios over staged
- Specific to topic (not generic)
- Relatable but professional
- Emotionally resonant (builds 3-day recall)

Absolute Requirements:
- MUST directly support and reinforce the post message
- MUST be immediately understandable without text
- MUST add credibility, authority, or proof
- MUST trigger professional FOMO (fear of missing industry insight)
- NO stock photos of generic "professional at desk"
- NO images disconnected from post topic
- NO abstract or vague business imagery
- NO cartoon, illustration, or overly stylized content

Generate ONLY the detailed image prompt (500-800 characters) that will produce this exact image in image generation. Make it specific and actionable."""
                    }]
                )

                image_prompt = image_prompt_msg.content[0].text.strip()

                # Create Airtable record
                fields = {
                    "Title": idea.get('title', 'Untitled'),
                    "Content": post_text,
                    "Status": "Draft",
                    "Image Prompt": image_prompt,
                    "Image Concept": idea.get('image_concept', ''),
                    "Content Type": idea.get('type', 'General'),
                    "Created Date": datetime.now().isoformat(),
                }

                record_id = add_airtable_record(base_id, table_id, fields)

                if record_id:
                    posts_created += 1
                    logger.info(f"Created post {posts_created}/{total_posts}: {idea.get('title')}")
                else:
                    logger.warning(f"Failed to create post for idea: {idea.get('title')}")

            except Exception as e:
                logger.warning(f"Error generating post {i}: {e}")
                continue

        logger.info(f"Daily content generation complete: {posts_created}/{total_posts} posts created")
        return posts_created > 0

    except Exception as e:
        logger.error(f"Error in daily content generation: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


@app.function(image=image, secrets=[modal.Secret.from_name("linkedin-secrets")], timeout=300)
def cleanup_scheduled_deletions():
    """
    Periodically check for records scheduled for deletion.
    If deletion date has passed, delete the record from Airtable.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        logger.info("Running scheduled deletion cleanup")

        base_id = os.environ.get('AIRTABLE_BASE_ID')
        table_id = os.environ.get('AIRTABLE_LINKEDIN_TABLE_ID')

        if not base_id or not table_id:
            logger.error("Missing Airtable configuration")
            return False

        # Query for records with Scheduled Deletion Date in the past
        now = datetime.now()
        formatted_now = now.strftime('%Y-%m-%d')

        # Use Airtable filter formula to find records due for deletion
        formula = f"IS_BEFORE({{Scheduled Deletion Date}}, '{formatted_now}')"

        url = f"https://api.airtable.com/v0/{base_id}/{table_id}"
        params = {"filterByFormula": formula}

        response = requests.get(url, headers=get_airtable_headers(), params=params, timeout=30)

        if response.status_code != 200:
            logger.error(f"Failed to query records: {response.status_code} - {response.text}")
            return False

        records = response.json().get('records', [])
        logger.info(f"Found {len(records)} records due for deletion")

        deleted_count = 0

        for record in records:
            record_id = record.get('id')
            fields = record.get('fields', {})
            status = fields.get('Status', '')
            deletion_date = fields.get('Scheduled Deletion Date', '')

            logger.info(f"Deleting record {record_id} (Status: {status}, Deletion Date: {deletion_date})")

            # Delete the record
            if delete_airtable_record(base_id, table_id, record_id):
                deleted_count += 1
                logger.info(f"Successfully deleted record {record_id}")
            else:
                logger.warning(f"Failed to delete record {record_id}")

        logger.info(f"Deletion cleanup complete: {deleted_count}/{len(records)} records deleted")
        return True

    except Exception as e:
        logger.error(f"Error in deletion cleanup: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


# ============== Webhook Handler Functions ==============
# These functions can be called directly via Modal

# ============== Cloud-Native Polling (replaces Mac LaunchAgent) ==============

def fetch_all_airtable_records(base_id: str, table_id: str) -> List[dict]:
    """Fetch all records from Airtable with pagination"""
    try:
        all_records = []
        offset = None
        url = f"https://api.airtable.com/v0/{base_id}/{table_id}"

        while True:
            params = {}
            if offset:
                params['offset'] = offset

            response = requests.get(url, headers=get_airtable_headers(), timeout=10, params=params)

            if response.status_code == 200:
                data = response.json()
                all_records.extend(data.get('records', []))

                # Check if there are more records
                offset = data.get('offset')
                if not offset:
                    break
            else:
                logging.error(f"Airtable API error: {response.status_code} - {response.text}")
                break

        return all_records
    except Exception as e:
        logging.error(f"Error fetching records: {e}")
        return []


def build_polling_state(records: List[dict]) -> dict:
    """Build state dict from current Airtable records"""
    state = {}
    for record in records:
        record_id = record['id']
        fields = record.get('fields', {})
        state[record_id] = {
            'title': fields.get('Title', 'Untitled'),
            'status': fields.get('Status', 'Draft'),
            'last_seen': datetime.now().isoformat()
        }
    return state


def detect_status_changes(old_state: dict, new_state: dict) -> List[dict]:
    """Compare old and new states, return list of changes"""
    trigger_statuses = {
        'Pending Review': 'image_generation',
        'Approved - Ready to Schedule': 'scheduling',
        'Rejected': 'rejection_handling'
    }

    changes = []

    for record_id, new_data in new_state.items():
        if record_id not in old_state:
            # New record
            if new_data['status'] in trigger_statuses:
                changes.append({
                    'record_id': record_id,
                    'title': new_data['title'],
                    'old_status': None,
                    'new_status': new_data['status'],
                    'reason': 'new_record'
                })
        else:
            old_data = old_state[record_id]
            # Status changed
            if old_data['status'] != new_data['status']:
                if new_data['status'] in trigger_statuses:
                    changes.append({
                        'record_id': record_id,
                        'title': new_data['title'],
                        'old_status': old_data['status'],
                        'new_status': new_data['status'],
                        'reason': 'status_change'
                    })

    return changes


# Use Modal's KV store for polling state persistence
polling_state_kv = modal.Dict.from_name("polling-state", create_if_missing=True)


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("linkedin-secrets")],
    # schedule=modal.Period(seconds=5)  # DISABLED: See post_scheduler_exact_minute() in modal_maintain_inventory.py
)
def poll_airtable_for_changes():
    """
    Cloud-hosted polling function (replaces Mac LaunchAgent).
    NOW MANUAL ONLY - for handling status changes when explicitly called.

    Note: Posting is now handled by post_scheduler_exact_minute() in modal_maintain_inventory.py
    which runs once per minute (1,440 checks/day) for 92% cost savings vs 5-second polling.

    This consolidation allows us to stay within Modal's 5 cron job limit.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        base_id = os.environ.get('AIRTABLE_BASE_ID')
        table_id = os.environ.get('AIRTABLE_LINKEDIN_TABLE_ID')

        if not base_id or not table_id:
            logger.error("Missing Airtable configuration")
            return {"success": False, "error": "Missing Airtable config"}

        logger.info("Cloud polling: Checking Airtable for status changes...")

        # Fetch current records from Airtable
        records = fetch_all_airtable_records(base_id, table_id)
        if not records:
            logger.warning("No records found or API error")
            return {"success": False, "error": "No records found"}

        # Build new state
        new_state = build_polling_state(records)

        # Load old state from Modal KV store
        old_state = dict(polling_state_kv) if polling_state_kv else {}

        # Detect changes
        changes = detect_status_changes(old_state, new_state)

        if changes:
            logger.info(f"Detected {len(changes)} status change(s)")

            for change in changes:
                record_id = change['record_id']
                title = change['title']
                new_status = change['new_status']

                logger.info(f"  📝 {record_id}: {change.get('old_status', 'N/A')} → {new_status}")
                logger.info(f"     {title}")

                # Call handler directly (no webhook server needed!)
                try:
                    result = handle_webhook.remote(record_id, new_status, base_id, table_id)
                    logger.info(f"  ✅ Handler triggered: {result}")
                except Exception as e:
                    logger.error(f"  ❌ Failed to trigger handler: {e}")

        else:
            logger.debug(f"No changes detected. Tracking {len(new_state)} records.")

        # Update state in Modal KV store
        for record_id, data in new_state.items():
            polling_state_kv[record_id] = data

        return {
            "success": True,
            "records_checked": len(new_state),
            "changes_detected": len(changes)
        }

    except Exception as e:
        logger.error(f"Error in cloud polling: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e)}


@app.function(image=image, secrets=[modal.Secret.from_name("linkedin-secrets")], timeout=300)
def check_and_fix_scheduling_issues(base_id: str, table_id: str):
    """
    Detect and automatically correct scheduling issues in Airtable.
    Called after posts are scheduled to catch conflicts.

    Issues detected:
    1. Multiple posts in same posting window on same day
    2. Posts scheduled in the past
    3. Invalid scheduled times

    Auto-corrects by redistributing posts to available windows.
    """
    import pytz
    from datetime import datetime, timedelta
    import random

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        logger.info("Checking for scheduling issues...")

        tz = pytz.timezone('America/New_York')
        now = datetime.now(tz)
        posting_times = [9, 14, 20]
        window_buffer = 30  # minutes

        # Fetch all records
        headers = {
            'Authorization': f'Bearer {os.environ.get("AIRTABLE_API_KEY")}',
            'Content-Type': 'application/json'
        }
        url = f"https://api.airtable.com/v0/{base_id}/{table_id}"
        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code != 200:
            logger.warning(f"Could not fetch records: {response.status_code}")
            return {"success": False, "error": "API fetch failed"}

        records = response.json().get('records', [])
        window_occupancy = {}  # Key: (date, window_hour), Value: [record_ids]

        # Build window occupancy map for scheduled posts
        for record in records:
            record_id = record.get('id')
            fields = record.get('fields', {})
            status = fields.get('Status', '')
            scheduled_time_str = fields.get('Scheduled Time')

            if status != 'Scheduled' or not scheduled_time_str:
                continue

            try:
                # Parse scheduled time - handle both ISO and UTC Z formats
                if scheduled_time_str.endswith('Z'):
                    scheduled_time_str = scheduled_time_str.replace('Z', '+00:00')

                scheduled = datetime.fromisoformat(scheduled_time_str).astimezone(tz)

                # Determine which window this post belongs to
                for window_hour in posting_times:
                    window_time = scheduled.replace(hour=window_hour, minute=0, second=0, microsecond=0)
                    time_diff = abs((scheduled - window_time).total_seconds() / 60)

                    if time_diff <= window_buffer:
                        date_key = scheduled.strftime('%Y-%m-%d')
                        window_key = (date_key, window_hour)

                        if window_key not in window_occupancy:
                            window_occupancy[window_key] = []

                        window_occupancy[window_key].append({
                            'record_id': record_id,
                            'title': fields.get('Title', 'Untitled'),
                            'scheduled_time': scheduled.isoformat()
                        })
                        break
            except Exception as e:
                logger.warning(f"Could not parse scheduled time for {record_id}: {e}")
                continue

        # Find and fix window conflicts
        issues_found = 0
        issues_fixed = 0

        for (date_key, window_hour), posts in window_occupancy.items():
            if len(posts) > 1:
                issues_found += 1
                logger.warning(f"⚠ Window conflict on {date_key} at {window_hour}:00 - {len(posts)} posts")

                # Keep first post, redistribute others
                kept_post = posts[0]
                posts_to_move = posts[1:]

                # Get available windows on this date
                available_windows = [w for w in posting_times if (date_key, w) not in window_occupancy or (date_key, w) == (date_key, window_hour)]

                for post in posts_to_move:
                    if available_windows and available_windows[0] != window_hour:
                        new_window = available_windows.pop(0)
                        target_date = datetime.strptime(date_key, '%Y-%m-%d').replace(tzinfo=tz)
                        new_time = target_date.replace(hour=new_window, minute=0, second=0, microsecond=0)
                        offset_minutes = random.randint(-15, 15)
                        new_time = new_time + timedelta(minutes=offset_minutes)

                        # Update record
                        update_url = f"https://api.airtable.com/v0/{base_id}/{table_id}/{post['record_id']}"
                        update_payload = {"fields": {"Scheduled Time": new_time.isoformat()}}

                        update_response = requests.patch(update_url, json=update_payload, headers=headers, timeout=30)

                        if update_response.status_code == 200:
                            issues_fixed += 1
                            logger.info(f"✓ Moved {post['record_id']} to {new_window}:00 window")
                        else:
                            logger.error(f"✗ Failed to update {post['record_id']}")

        if issues_found > 0:
            logger.info(f"Scheduling issue detection complete: {issues_found} conflicts, {issues_fixed} fixed")
            return {"success": True, "issues_found": issues_found, "issues_fixed": issues_fixed}
        else:
            logger.debug("No scheduling issues detected")
            return {"success": True, "issues_found": 0, "issues_fixed": 0}

    except Exception as e:
        logger.error(f"Error in scheduling issue detection: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e)}


@app.function(image=image, secrets=[modal.Secret.from_name("linkedin-secrets")])
def handle_webhook(record_id: str, status: str, base_id: str = None, table_id: str = None):
    """
    Main webhook handler that can be called directly.
    Handles status changes from Airtable.
    Can be called from cloud polling or external webhooks.
    """
    if not base_id:
        base_id = os.environ.get('AIRTABLE_BASE_ID')
    if not table_id:
        table_id = os.environ.get('AIRTABLE_LINKEDIN_TABLE_ID')

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info(f"Webhook handler called: {record_id} → {status}")

    if status == "Pending Review":
        logger.info("Spawning image generation...")
        generate_images_for_post.spawn(record_id, base_id, table_id)
        return {"success": True, "action": "image_generation_triggered"}

    elif status == "Approved - Ready to Schedule":
        logger.info("Spawning post scheduling...")
        schedule_approved_post.spawn(record_id, base_id, table_id)

        # After scheduling, check for any scheduling issues and auto-correct them
        # This catches cases where multiple posts end up in the same window
        logger.info("Running scheduling issue detection...")
        check_and_fix_scheduling_issues.spawn(base_id, table_id)

        return {"success": True, "action": "scheduling_triggered"}

    elif status == "Rejected":
        logger.info("Spawning rejection handler...")
        handle_rejected_post.spawn(record_id, base_id, table_id)
        return {"success": True, "action": "rejection_handled"}

    else:
        logger.warning(f"Unknown status: {status}")
        return {"success": False, "error": f"Unknown status: {status}"}


# ============== Content Revision Functions ==============

@app.function(image=image, secrets=[modal.Secret.from_name("linkedin-secrets")], timeout=300)
def revise_single_post(record_id: str, base_id: str = None, table_id: str = None):
    """
    Revise a single post based on Revision Prompt field.
    Called from Airtable button or API.

    Args:
        record_id: The Airtable record ID to revise
        base_id: Airtable base ID (uses env var if not provided)
        table_id: Airtable table ID (uses env var if not provided)

    Returns:
        Dict with success status and revision details
    """
    import sys
    from pathlib import Path

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        # Get base/table from env if not provided
        if not base_id:
            base_id = os.environ.get('AIRTABLE_BASE_ID')
        if not table_id:
            table_id = os.environ.get('AIRTABLE_LINKEDIN_TABLE_ID')

        logger.info(f"Starting revision for record {record_id}")

        # Import here to avoid dependency issues at module load time
        sys.path.insert(0, '/root/linkedin_automation/execution')
        from content_revisions import ContentRevisionProcessor

        processor = ContentRevisionProcessor()
        result = processor.check_for_revisions(record_ids=[record_id])

        return {
            "success": True,
            "record_id": record_id,
            "revisions_processed": result,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error revising post: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e),
            "record_id": record_id
        }


@fastapi_endpoint()
def revise_web_app():
    """Create FastAPI app for revision webhook"""
    from fastapi import FastAPI, Query

    app_revision = FastAPI()

    @app_revision.get("/revise")
    async def handle_revision(record_id: str = Query(None)):
        """Handle revision request from Airtable button"""
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        if not record_id:
            return {"error": "record_id required"}

        try:
            logger.info(f"Webhook called for revision: {record_id}")

            result = revise_single_post.remote(
                record_id,
                os.environ.get('AIRTABLE_BASE_ID'),
                os.environ.get('AIRTABLE_LINKEDIN_TABLE_ID')
            )

            return result

        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return {"error": str(e)}

    return app_revision


@app.function(image=image, secrets=[modal.Secret.from_name("linkedin-secrets")])  # schedule=Period(minutes=15) [PAUSED]
def check_pending_revisions_scheduled():
    """
    Periodically check for posts with Revision Prompt field populated.
    Runs every 15 minutes automatically.

    Returns:
        Dict with number of revisions processed
    """
    import sys
    from pathlib import Path

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        logger.info("Checking for pending revisions...")

        # Try multiple paths to find the content_revisions module
        possible_paths = [
            '/root/linkedin_automation/execution',
            '/root/Agentic Workflow/linkedin_automation/execution',
            'linkedin_automation/execution',
            './linkedin_automation/execution'
        ]

        imported = False
        for path in possible_paths:
            if path not in sys.path:
                sys.path.insert(0, path)
            logger.info(f"[DEBUG] Trying to import from: {path}")

        try:
            from content_revisions import ContentRevisionProcessor
            imported = True
            logger.info("[DEBUG] Successfully imported ContentRevisionProcessor")
        except ImportError as ie:
            logger.warning(f"[DEBUG] Import from default paths failed: {ie}")
            # Try importing with full path
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location("content_revisions", "/root/linkedin_automation/execution/content_revisions.py")
                if spec and spec.loader:
                    content_revisions = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(content_revisions)
                    ContentRevisionProcessor = content_revisions.ContentRevisionProcessor
                    imported = True
                    logger.info("[DEBUG] Successfully imported ContentRevisionProcessor via importlib")
            except Exception as e2:
                logger.error(f"[DEBUG] Importlib approach also failed: {e2}")

        if not imported:
            logger.error("Could not import ContentRevisionProcessor from any location")
            return {"error": "Could not import ContentRevisionProcessor"}

        processor = ContentRevisionProcessor()
        revised_count = processor.check_for_revisions()

        logger.info(f"Revision check complete: {revised_count} posts revised")
        return {"revised_count": revised_count}

    except Exception as e:
        logger.error(f"Error in scheduled revision check: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"error": str(e)}


@app.function(image=image, secrets=[modal.Secret.from_name("linkedin-secrets")])
@fastapi_endpoint()
def mark_post_as_posted(request_dict: dict) -> dict:
    """
    Webhook endpoint for Make.com to call when post goes live.
    Make.com calls this after successfully posting to LinkedIn.
    Updates Airtable with the LinkedIn post URL.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Received post-live notification from Make.com")

        record_id = request_dict.get('record_id')
        base_id = request_dict.get('base_id')
        table_id = request_dict.get('table_id')
        post_url = request_dict.get('post_url')

        if not all([record_id, base_id, table_id]):
            logger.error(f"Missing required fields in Make.com callback")
            return {"success": False, "error": "Missing required fields"}

        logger.info(f"Updating record {record_id} with LinkedIn post URL: {post_url}")

        # Update Airtable with LinkedIn post URL if available
        update_fields = {}
        if post_url:
            update_fields["LinkedIn Post URL"] = post_url

        if update_fields:
            success = update_airtable_record(base_id, table_id, record_id, update_fields)

            if success:
                logger.info(f"✓ Updated record {record_id} with LinkedIn post URL")
                return {"success": True, "message": "Post URL recorded"}
            else:
                logger.error(f"✗ Failed to update record {record_id}")
                return {"success": False, "error": "Airtable update failed"}
        else:
            logger.info(f"No post URL provided, but notification received successfully")
            return {"success": True, "message": "Notification received (no URL to record)"}

    except Exception as e:
        logger.error(f"Error processing post-live notification: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e)}


@app.function(image=image, secrets=[modal.Secret.from_name("linkedin-secrets")])
@fastapi_endpoint()
def airtable_webhook_listener():
    """
    Listen for Airtable Automation events (FREE tier feature).

    Uses Airtable's free Automations feature to trigger HTTP webhooks instead of polling.

    How it works:
    1. User marks post status as "Approved - Ready to Schedule"
    2. Airtable Automation detects the status change
    3. Automation sends HTTP request to this webhook
    4. Modal receives the webhook and triggers scheduling/image generation

    Benefits:
    - No polling = no wasted API calls
    - Instant triggering (under 1 second)
    - Works with Airtable free tier
    - Same cost as before (zero)

    Endpoint: /webhook/airtable-publish
    Method: POST
    """
    from fastapi import FastAPI, Request, Header
    import hmac
    import hashlib
    import base64

    app_webhook = FastAPI()

    def verify_airtable_signature(request_body: bytes, signature_header: str) -> bool:
        """Verify that webhook came from Airtable using HMAC-SHA256"""
        # Get the webhook token from environment
        webhook_token = os.environ.get('AIRTABLE_WEBHOOK_TOKEN')
        if not webhook_token:
            logging.warning("No AIRTABLE_WEBHOOK_TOKEN set - skipping signature verification")
            return True  # Allow if not configured

        # Compute expected signature
        computed_signature = base64.b64encode(
            hmac.new(
                webhook_token.encode(),
                request_body,
                hashlib.sha256
            ).digest()
        ).decode()

        # Compare signatures
        return hmac.compare_digest(computed_signature, signature_header)

    @app_webhook.post("/webhook/airtable-publish")
    async def handle_airtable_webhook(request: Request):
        """
        Handle webhook from Airtable Automations (free tier feature).

        This replaces polling with event-driven architecture using Airtable's free
        Automations that trigger when a record's Status changes.

        Triggers:
        - When Status changes to "Approved - Ready to Schedule" → Schedule post
        - When Status changes to "Pending Review" → Generate image

        Expected payload (from Airtable Automation HTTP action):
        {
            "changedTablesById": {
                "tblXXXXXXXXXXXXXX": {
                    "changedRecordsById": {
                        "recXXXXXXXXXXXXXX": {
                            "current": {
                                "fields": {
                                    "Status": "Approved - Ready to Schedule",
                                    "Title": "Post title",
                                    "Post Content": "Full post content..."
                                }
                            }
                        }
                    }
                }
            }
        }

        Setup Instructions (Airtable Automations - Free):
        1. Open your Airtable base → Automations tab
        2. Create new automation
        3. Trigger: "When a record matches conditions"
        4. Condition: Status = "Approved - Ready to Schedule"
        5. Action: "Webhook (Send HTTP request)"
        6. URL: https://musacbusiness--linkedin-automation-airtable-webhook-listener.modal.run/webhook/airtable-publish
        7. Method: POST
        8. Headers: Content-Type: application/json
        9. Body: Use Airtable variables to insert record data
        """
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        try:
            payload = await request.json()
            logger.info(f"Received Airtable Automation webhook")

            # Extract changed records
            changed_tables = payload.get('changedTablesById', {})
            base_id = os.environ.get('AIRTABLE_BASE_ID')
            table_id = os.environ.get('AIRTABLE_LINKEDIN_TABLE_ID')

            processed_count = 0

            for tbl_id, table_data in changed_tables.items():
                # Only process our LinkedIn posts table
                if tbl_id != table_id:
                    continue

                changed_records = table_data.get('changedRecordsById', {})

                for record_id, record_data in changed_records.items():
                    try:
                        current = record_data.get('current', {})
                        fields = current.get('fields', {})
                        status = fields.get('Status', '')

                        logger.info(f"Processing record {record_id}: status={status}")

                        # Trigger scheduling if status is "Approved - Ready to Schedule"
                        if status == 'Approved - Ready to Schedule':
                            logger.info(f"Triggering schedule for approved post: {record_id}")

                            # Call the scheduling function
                            result = schedule_approved_post.remote(
                                record_id,
                                base_id,
                                table_id
                            )

                            logger.info(f"Schedule result: {result}")
                            processed_count += 1

                        # Trigger image generation if status is "Pending Review"
                        elif status == 'Pending Review':
                            logger.info(f"Triggering image generation for: {record_id}")

                            result = generate_images_for_post.remote(
                                record_id,
                                base_id,
                                table_id
                            )

                            logger.info(f"Image generation result: {result}")
                            processed_count += 1

                    except Exception as e:
                        logger.error(f"Error processing record {record_id}: {e}")
                        import traceback
                        logger.error(traceback.format_exc())

            return {
                "success": True,
                "message": f"Processed {processed_count} records",
                "processed_count": processed_count
            }

        except Exception as e:
            logger.error(f"Webhook error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"success": False, "error": str(e)}, 500

    return app_webhook


if __name__ == "__main__":
    print("Modal LinkedIn Automation App")
    print("Deploy: modal deploy cloud/modal_linkedin_automation.py")
    print("Test: modal serve cloud/modal_linkedin_automation.py")
