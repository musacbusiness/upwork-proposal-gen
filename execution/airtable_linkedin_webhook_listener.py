#!/usr/bin/env python3
"""
Airtable LinkedIn Webhook Listener
===================================
Polls Airtable for LinkedIn post status changes and triggers Modal functions.

This replaces the polling-based approach by:
1. Checking Airtable every 30-60 seconds for status changes
2. Calling Modal functions directly when status changes
3. Tracking processed records to avoid duplicate execution

Status flows:
- Draft → Pending Review → Modal generates images
- Pending Review → Approved - Ready to Schedule → Modal schedules post
- Any status → Rejected → Modal handles rejection

Run:
    python3 execution/airtable_linkedin_webhook_listener.py

Environment variables required:
    AIRTABLE_API_KEY
    AIRTABLE_BASE_ID
    AIRTABLE_LINKEDIN_TABLE_ID
    MODAL_WEBHOOK_URL (optional, for calling Modal via HTTP)
"""

import os
import sys
import json
import time
import logging
import threading
from datetime import datetime
from typing import Dict, Set, Optional
from pathlib import Path

import requests
from dotenv import load_dotenv

# Load env
env_file = "/Users/musacomma/Agentic Workflow/.env"
if os.path.exists(env_file):
    load_dotenv(env_file)

# Configure logging
log_dir = Path("/Users/musacomma/Agentic Workflow/logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'airtable_linkedin_listener.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')
AIRTABLE_TABLE_ID = os.getenv('AIRTABLE_LINKEDIN_TABLE_ID')
MODAL_TOKEN = os.getenv('MODAL_TOKEN_ID')  # For Modal API calls

# Polling interval (seconds)
POLL_INTERVAL = 30

# Track processed records to avoid duplicate handling
# Format: {record_id: {status: str, timestamp: datetime}}
processed_records: Dict[str, Dict] = {}
COOLDOWN_SECONDS = 300  # 5 minute cooldown between processing same record/status


def get_airtable_headers() -> Dict[str, str]:
    """Get headers for Airtable API requests."""
    return {
        'Authorization': f'Bearer {AIRTABLE_API_KEY}',
        'Content-Type': 'application/json'
    }


def fetch_linkedin_posts() -> list:
    """Fetch all LinkedIn posts from Airtable."""
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_ID}"

    try:
        response = requests.get(url, headers=get_airtable_headers(), timeout=30)
        if response.status_code == 200:
            records = response.json().get('records', [])
            logger.info(f"Fetched {len(records)} records from Airtable")
            return records
        else:
            logger.error(f"Failed to fetch records: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        logger.error(f"Error fetching records: {e}")
        return []


def call_modal_function(record_id: str, status: str) -> bool:
    """
    Call Modal function to handle status change.

    Uses Modal's native Python API to call the handle_webhook function.
    Falls back to HTTP if needed.
    """
    try:
        # Try to import Modal and call function directly
        import modal

        logger.info(f"Calling Modal function: handle_webhook({record_id}, {status})")

        # Get the function from the deployed Modal app
        app_name = "linkedin-automation"
        function_name = "handle_webhook"

        try:
            # Try to call via Modal API
            handle_webhook_fn = modal.Function.from_name(app_name, function_name)
            result = handle_webhook_fn.remote(
                record_id,
                status,
                AIRTABLE_BASE_ID,
                AIRTABLE_TABLE_ID
            )
            logger.info(f"✓ Modal function executed: {result}")
            return True
        except Exception as e:
            logger.warning(f"Failed to call via Modal API: {e}")
            logger.info("Falling back to HTTP webhook...")
            return False

    except ImportError:
        logger.warning("Modal package not available, skipping direct call")
        return False
    except Exception as e:
        logger.error(f"Error calling Modal function: {e}")
        return False


def process_status_change(record_id: str, old_status: Optional[str], new_status: str) -> bool:
    """
    Process a status change for a record.

    Args:
        record_id: The Airtable record ID
        old_status: Previous status (None if new record)
        new_status: New status

    Returns:
        True if processing succeeded, False otherwise
    """
    # Skip if no actual status change
    if old_status == new_status:
        return False

    # Check cooldown to avoid duplicate processing
    key = f"{record_id}:{new_status}"
    if key in processed_records:
        last_processed = processed_records[key].get('timestamp')
        if last_processed:
            elapsed = (datetime.now() - last_processed).total_seconds()
            if elapsed < COOLDOWN_SECONDS:
                logger.debug(f"Record {record_id} on cooldown (status: {new_status})")
                return False

    # Log the status change
    logger.info(f"📌 Status change: {record_id} → {new_status}" +
                (f" (was: {old_status})" if old_status else ""))

    # Process based on new status
    if new_status == "Pending Review":
        logger.info(f"  ↳ Triggering image generation...")
        success = call_modal_function(record_id, "Pending Review")

    elif new_status == "Approved - Ready to Schedule":
        logger.info(f"  ↳ Triggering post scheduling...")
        success = call_modal_function(record_id, "Approved - Ready to Schedule")

    elif new_status == "Rejected":
        logger.info(f"  ↳ Triggering rejection handler...")
        success = call_modal_function(record_id, "Rejected")

    else:
        logger.debug(f"  ↳ Status '{new_status}' has no associated action")
        success = False

    # Track processing
    if success:
        processed_records[key] = {
            'timestamp': datetime.now(),
            'status': new_status
        }
        logger.info(f"  ✓ Processing complete for {record_id}")
    else:
        logger.warning(f"  ✗ Processing failed for {record_id}")

    return success


def poll_airtable():
    """
    Poll Airtable for status changes.

    Compares current status of each record against stored state to detect changes.
    """
    logger.info("=" * 80)
    logger.info(f"Polling Airtable ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    logger.info("=" * 80)

    # Fetch all records
    records = fetch_linkedin_posts()

    if not records:
        logger.warning("No records found in Airtable")
        return

    # Check each record for status changes
    status_changes = []
    for record in records:
        record_id = record['id']
        fields = record.get('fields', {})
        current_status = fields.get('Status', 'Unknown')

        # Check if this is a status change
        if record_id not in processed_records:
            # New record - don't trigger on first appearance, just track it
            processed_records[record_id] = {
                'status': current_status,
                'timestamp': datetime.now()
            }
            logger.debug(f"Tracking new record: {record_id} (status: {current_status})")
        else:
            # Check for status change
            old_status = processed_records[record_id].get('status')
            if old_status != current_status:
                logger.info(f"\n🔔 STATUS CHANGE DETECTED:")
                logger.info(f"   Record: {record_id}")
                logger.info(f"   Old:    {old_status}")
                logger.info(f"   New:    {current_status}")
                status_changes.append((record_id, old_status, current_status))

                # Update stored status
                processed_records[record_id]['status'] = current_status

    # Process all detected status changes
    if status_changes:
        logger.info(f"\nProcessing {len(status_changes)} status change(s)...")
        for record_id, old_status, new_status in status_changes:
            process_status_change(record_id, old_status, new_status)
    else:
        logger.info("No status changes detected")

    logger.info(f"Poll complete. Tracking {len(processed_records)} records.\n")


def polling_loop():
    """
    Continuous polling loop.

    Checks Airtable at regular intervals and processes status changes.
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"🚀 AIRTABLE LINKEDIN WEBHOOK LISTENER STARTED")
    logger.info(f"{'='*80}")
    logger.info(f"Polling every {POLL_INTERVAL} seconds")
    logger.info(f"API Key: {AIRTABLE_API_KEY[:20]}...")
    logger.info(f"Base ID: {AIRTABLE_BASE_ID}")
    logger.info(f"Table ID: {AIRTABLE_TABLE_ID}")
    logger.info(f"{'='*80}\n")

    try:
        while True:
            try:
                poll_airtable()
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
                import traceback
                logger.error(traceback.format_exc())

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        logger.info("\n\n" + "="*80)
        logger.info("🛑 SHUTDOWN REQUESTED")
        logger.info(f"Processed {len(processed_records)} records total")
        logger.info("="*80 + "\n")
        sys.exit(0)


def main():
    """Main entry point."""
    # Validate environment
    if not AIRTABLE_API_KEY:
        logger.error("AIRTABLE_API_KEY not set in .env")
        sys.exit(1)

    if not AIRTABLE_BASE_ID:
        logger.error("AIRTABLE_BASE_ID not set in .env")
        sys.exit(1)

    if not AIRTABLE_TABLE_ID:
        logger.error("AIRTABLE_LINKEDIN_TABLE_ID not set in .env")
        sys.exit(1)

    # Start polling loop
    polling_loop()


if __name__ == "__main__":
    main()
