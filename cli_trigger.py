#!/usr/bin/env python3
"""
CLI trigger for LinkedIn automation using subprocess to properly invoke Modal functions.

Usage:
    python3 cli_trigger.py --record-id "rec123" --status "Pending Review"
"""

import subprocess
import argparse
import json
import os
import sys


def main():
    parser = argparse.ArgumentParser(description="Trigger LinkedIn automation via Modal")
    parser.add_argument("--record-id", required=True, help="Airtable record ID")
    parser.add_argument("--status", required=True, help="New status")
    parser.add_argument("--base-id", help="Airtable base ID")
    parser.add_argument("--table-id", help="Airtable table ID")

    args = parser.parse_args()

    base_id = args.base_id or os.environ.get('AIRTABLE_BASE_ID')
    table_id = args.table_id or os.environ.get('AIRTABLE_LINKEDIN_TABLE_ID')

    print(f"🔄 Triggering: {args.record_id} → {args.status}")

    # Create a temporary Python script to run in Modal context
    script = f"""
import sys
sys.path.insert(0, '/Users/musacomma/Agentic Workflow/cloud')

from modal_linkedin_automation import handle_webhook
import json

result = handle_webhook('{args.record_id}', '{args.status}', '{base_id}', '{table_id}')
print(json.dumps(result))
"""

    try:
        # Run via Python subprocess which should maintain Modal context
        result = subprocess.run(
            [sys.executable, '-c', script],
            cwd='/Users/musacomma/Agentic Workflow/cloud',
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            output = result.stdout.strip()
            try:
                result_json = json.loads(output)
                print(f"✅ Success!")
                print(f"📋 Result: {result_json}")
                return 0
            except json.JSONDecodeError:
                print(f"⚠️  Output: {output}")
                if result.stderr:
                    print(f"Stderr: {result.stderr}")
                return 0
        else:
            print(f"❌ Error: {result.stderr}")
            return 1

    except Exception as e:
        print(f"❌ Failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
