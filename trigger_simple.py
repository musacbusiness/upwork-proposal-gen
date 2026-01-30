#!/usr/bin/env python3
"""
Simple trigger for LinkedIn automation webhook.
Works by importing and running the function directly through Modal's deployed app.

Usage:
    python3 trigger_simple.py --record-id "rec123abc" --status "Pending Review"
"""

import argparse
import os
import sys

# Add cloud directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'cloud'))

def main():
    parser = argparse.ArgumentParser(description="Trigger LinkedIn automation webhook")
    parser.add_argument("--record-id", required=True, help="Airtable record ID")
    parser.add_argument("--status", required=True, help="New status (Pending Review, Approved - Ready to Schedule, Rejected)")
    parser.add_argument("--base-id", help="Airtable base ID (optional, uses env var if not provided)")
    parser.add_argument("--table-id", help="Airtable table ID (optional, uses env var if not provided)")

    args = parser.parse_args()

    base_id = args.base_id or os.environ.get('AIRTABLE_BASE_ID')
    table_id = args.table_id or os.environ.get('AIRTABLE_LINKEDIN_TABLE_ID')

    print(f"🔄 Triggering webhook: {args.record_id} → {args.status}")

    try:
        # Import Modal and the app
        import modal
        from modal_linkedin_automation import app, handle_webhook

        print(f"✅ App loaded: {app.name}")
        print(f"✅ Function loaded: handle_webhook")

        # The function needs to be called in a Modal context
        # Use app.run to ensure proper Modal context
        print(f"📤 Calling Modal function...")

        result = app.run(
            handle_webhook,
            args.record_id,
            args.status,
            base_id,
            table_id
        )

        print(f"✅ Success!")
        print(f"📋 Result: {result}")
        return result

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
