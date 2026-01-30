#!/usr/bin/env python3
"""
Bridge script to trigger Modal functions from Airtable automations.
This script listens for webhook calls from Airtable and triggers the appropriate Modal functions.

Usage:
    python trigger_modal_webhook.py --run-server
"""

import argparse
import json
import os
import sys
import logging
from datetime import datetime

import modal

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def trigger_webhook(record_id: str, status: str, base_id: str = None, table_id: str = None):
    """
    Trigger a Modal function based on the status change.

    Args:
        record_id: The Airtable record ID
        status: The new status value
        base_id: Airtable base ID (optional, uses env var if not provided)
        table_id: Airtable table ID (optional, uses env var if not provided)
    """
    try:
        logger.info(f"Triggering webhook: {record_id} → {status}")

        # Use modal.Function.lookup to get the deployed function
        try:
            handle_webhook_fn = modal.Function.lookup("linkedin-automation", "handle_webhook")
            logger.info("Found handle_webhook function via lookup")
        except Exception as e:
            logger.warning(f"Function lookup failed: {e}, trying alternative method...")
            # Fallback: Call via the cloud module
            import sys
            sys.path.insert(0, '/Users/musacomma/Agentic Workflow/cloud')
            from modal_linkedin_automation import handle_webhook
            handle_webhook_fn = handle_webhook

        # Call the function
        logger.info(f"Calling function with: record_id={record_id}, status={status}, base_id={base_id}, table_id={table_id}")
        result = handle_webhook_fn.remote(record_id, status, base_id, table_id)

        logger.info(f"Webhook result: {result}")
        return result

    except Exception as e:
        logger.error(f"Error triggering webhook: {str(e)}", exc_info=True)
        raise


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Trigger Modal functions from Airtable webhooks")
    parser.add_argument("--record-id", required=True, help="Airtable record ID")
    parser.add_argument("--status", required=True, help="New status value")
    parser.add_argument("--base-id", help="Airtable base ID (optional)")
    parser.add_argument("--table-id", help="Airtable table ID (optional)")

    args = parser.parse_args()

    result = trigger_webhook(
        record_id=args.record_id,
        status=args.status,
        base_id=args.base_id,
        table_id=args.table_id
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
