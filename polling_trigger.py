#!/usr/bin/env python3
"""
Polling trigger for LinkedIn automation.
Scans Airtable records every N seconds for status changes and triggers Modal functions.

Usage:
    python3 polling_trigger.py [--interval 30] [--verbose]

Features:
    - Polls Airtable every 30 seconds (configurable)
    - Detects status changes automatically
    - Triggers Modal functions when status changes
    - Keeps track of processed records (doesn't duplicate triggers)
    - Runs 24/7 in background
    - Can be run via cron for scheduled checks
"""

import requests
import json
import time
import argparse
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('polling_trigger.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Airtable config
AIRTABLE_API_KEY = os.environ.get('AIRTABLE_API_KEY', 'patQCCzbAjKw675Bf.a9220198778415662363c84105e67b9c47399f5a01e27688f18f429115574a5c')
BASE_ID = os.environ.get('AIRTABLE_BASE_ID', 'appw88uD6ZM0ckF8f')
TABLE_ID = os.environ.get('AIRTABLE_LINKEDIN_TABLE_ID', 'tbljg75KMQWDo2Hgu')

# State file to track which records we've already processed
STATE_FILE = Path(__file__).parent / 'polling_state.json'

# Status values that should trigger actions
TRIGGER_STATUSES = {
    'Pending Review': 'image_generation',
    'Approved - Ready to Schedule': 'scheduling',
    'Rejected': 'rejection_handling'
}


def get_airtable_headers():
    """Get Airtable API headers"""
    return {
        'Authorization': f'Bearer {AIRTABLE_API_KEY}',
        'Content-Type': 'application/json'
    }


def load_state():
    """Load the previous state of records from file"""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load state file: {e}")
    return {}


def save_state(state):
    """Save the current state of records to file"""
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logger.error(f"Could not save state file: {e}")


def fetch_records():
    """Fetch all records from Airtable (with pagination)"""
    try:
        url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}"
        all_records = []
        offset = None

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
                logger.error(f"Airtable API error: {response.status_code} - {response.text}")
                return all_records if all_records else []

        return all_records
    except Exception as e:
        logger.error(f"Error fetching records: {e}")
        return []


def trigger_modal_function(record_id, status, base_id, table_id):
    """Trigger the Modal function via webhook server"""
    try:
        logger.info(f"Triggering Modal function: {record_id} → {status}")

        # Try to call via the Flask webhook server (if running locally)
        webhook_url = os.environ.get('WEBHOOK_URL', 'http://localhost:8000/webhook')

        payload = {
            'record_id': record_id,
            'status': status,
            'base_id': base_id,
            'table_id': table_id
        }

        response = requests.post(webhook_url, json=payload, timeout=10)

        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Modal function triggered successfully: {result}")
            return True
        else:
            logger.error(f"Webhook error: {response.status_code} - {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        logger.error(f"❌ Could not connect to webhook server at {webhook_url}")
        logger.info("Make sure the Flask server is running: python3 airtable_webhook_server.py")
        return False
    except Exception as e:
        logger.error(f"Error triggering Modal function: {e}")
        return False


def check_for_changes(current_state, new_state):
    """Compare states and find status changes"""
    changes = []

    for record_id, new_data in new_state.items():
        if record_id not in current_state:
            # New record
            if new_data['status'] in TRIGGER_STATUSES:
                changes.append({
                    'record_id': record_id,
                    'title': new_data['title'],
                    'old_status': None,
                    'new_status': new_data['status'],
                    'reason': 'new_record'
                })
        else:
            old_data = current_state[record_id]
            # Status changed
            if old_data['status'] != new_data['status']:
                if new_data['status'] in TRIGGER_STATUSES:
                    changes.append({
                        'record_id': record_id,
                        'title': new_data['title'],
                        'old_status': old_data['status'],
                        'new_status': new_data['status'],
                        'reason': 'status_change'
                    })
                    logger.info(f"📝 Status change detected: {record_id} ({new_data['title']})")
                    logger.info(f"   {old_data['status']} → {new_data['status']}")

    return changes


def poll_airtable(interval, verbose=False):
    """Main polling loop"""
    logger.info("=" * 70)
    logger.info("🚀 LinkedIn Automation Polling Trigger Started")
    logger.info("=" * 70)
    logger.info(f"Polling every {interval} seconds")
    logger.info(f"Webhook URL: {os.environ.get('WEBHOOK_URL', 'http://localhost:8000/webhook')}")
    logger.info(f"Base ID: {BASE_ID}")
    logger.info(f"Table ID: {TABLE_ID}")
    logger.info("=" * 70)
    logger.info("")

    current_state = load_state()
    poll_count = 0

    try:
        while True:
            poll_count += 1
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            if verbose:
                logger.info(f"[Poll #{poll_count}] {timestamp} - Checking Airtable...")

            # Fetch current records
            records = fetch_records()

            if not records:
                logger.warning("No records found or API error")
                time.sleep(interval)
                continue

            # Build new state
            new_state = {}
            for record in records:
                record_id = record['id']
                fields = record.get('fields', {})
                new_state[record_id] = {
                    'title': fields.get('Title', 'Untitled'),
                    'status': fields.get('Status', 'N/A'),
                    'last_seen': datetime.now().isoformat()
                }

            # Check for changes
            changes = check_for_changes(current_state, new_state)

            if changes:
                logger.info(f"\n📢 DETECTED {len(changes)} CHANGE(S):")
                for change in changes:
                    logger.info(f"\n  Record: {change['record_id']}")
                    logger.info(f"  Title: {change['title']}")
                    logger.info(f"  Status: {change['old_status']} → {change['new_status']}")

                    # Trigger Modal function
                    success = trigger_modal_function(
                        change['record_id'],
                        change['new_status'],
                        BASE_ID,
                        TABLE_ID
                    )

                    if success:
                        logger.info(f"  ✅ Triggered!")
                    else:
                        logger.error(f"  ❌ Failed to trigger (webhook server not responding?)")

                logger.info("")

            # Update state
            current_state = new_state
            save_state(current_state)

            # Log summary
            total_records = len(new_state)
            triggered_records = sum(1 for _, data in new_state.items() if data['status'] in TRIGGER_STATUSES)

            if verbose:
                logger.info(f"  Total records: {total_records}")
                logger.info(f"  Awaiting trigger: {triggered_records}")

            # Wait before next poll
            time.sleep(interval)

    except KeyboardInterrupt:
        logger.info("\n\n⏹️  Polling stopped by user")
        logger.info("=" * 70)
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        logger.info("Retrying in 60 seconds...")
        time.sleep(60)


def main():
    parser = argparse.ArgumentParser(
        description='Polling trigger for LinkedIn automation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Poll every 30 seconds (default)
  python3 polling_trigger.py

  # Poll every 10 seconds with verbose output
  python3 polling_trigger.py --interval 10 --verbose

  # Poll every 5 minutes (300 seconds)
  python3 polling_trigger.py --interval 300

  # Run as a cron job (polls once and exits)
  python3 polling_trigger.py --once
        """
    )

    parser.add_argument(
        '--interval',
        type=int,
        default=30,
        help='Polling interval in seconds (default: 30)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose logging output'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run once and exit (useful for cron jobs)'
    )
    parser.add_argument(
        '--webhook-url',
        help='Webhook URL to call (default: http://localhost:8000/webhook)'
    )

    args = parser.parse_args()

    # Set webhook URL if provided
    if args.webhook_url:
        os.environ['WEBHOOK_URL'] = args.webhook_url

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.once:
        # Run once for cron jobs
        logger.info("Running once (cron mode)...")
        current_state = load_state()
        records = fetch_records()

        new_state = {}
        for record in records:
            record_id = record['id']
            fields = record.get('fields', {})
            new_state[record_id] = {
                'title': fields.get('Title', 'Untitled'),
                'status': fields.get('Status', 'N/A'),
            }

        changes = check_for_changes(current_state, new_state)

        for change in changes:
            logger.info(f"Triggering: {change['record_id']} → {change['new_status']}")
            trigger_modal_function(change['record_id'], change['new_status'], BASE_ID, TABLE_ID)

        save_state(new_state)
        logger.info(f"Done. Found {len(changes)} changes.")
    else:
        # Continuous polling
        poll_airtable(args.interval, args.verbose)


if __name__ == '__main__':
    main()
