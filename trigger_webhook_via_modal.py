#!/usr/bin/env python3
"""
Trigger Modal functions via modal run command.
This script should be called via: modal run trigger_webhook_via_modal.py --record-id X --status Y
"""

import argparse
import os

# This script will be run by Modal, so it has access to the app
def main():
    parser = argparse.ArgumentParser(description="Trigger webhook via Modal")
    parser.add_argument("--record-id", required=True, help="Airtable record ID")
    parser.add_argument("--status", required=True, help="New status value")
    parser.add_argument("--base-id", help="Airtable base ID (optional)")
    parser.add_argument("--table-id", help="Airtable table ID (optional)")

    args = parser.parse_args()

    # Get credentials from environment or args
    base_id = args.base_id or os.environ.get('AIRTABLE_BASE_ID')
    table_id = args.table_id or os.environ.get('AIRTABLE_LINKEDIN_TABLE_ID')

    # Import here so it runs in Modal context
    from cloud.modal_linkedin_automation import handle_webhook

    # Call the function
    result = handle_webhook(args.record_id, args.status, base_id, table_id)

    print(f"Result: {result}")
    return result


if __name__ == "__main__":
    main()
