#!/bin/bash
# Simple trigger script to invoke Modal functions
# Usage: ./trigger.sh --record-id "rec123" --status "Pending Review"

set -e

# Parse arguments
RECORD_ID=""
STATUS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --record-id)
            RECORD_ID="$2"
            shift 2
            ;;
        --status)
            STATUS="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

if [ -z "$RECORD_ID" ] || [ -z "$STATUS" ]; then
    echo "Usage: $0 --record-id <id> --status <status>"
    echo "Example: $0 --record-id 'rec123abc' --status 'Pending Review'"
    exit 1
fi

# Change to the app directory
cd "$(dirname "$0")/cloud"

# Use Python to call the modal function directly
python3 << EOF
import sys
sys.path.insert(0, '.')

# Import Modal
import modal
import os

# Set up environment for Modal to find the app
os.environ['MODAL_APP_NAME'] = 'linkedin-automation'

# Import and call the function
from modal_linkedin_automation import handle_webhook

print(f"Triggering: {sys.argv[1]} -> {sys.argv[2]}")

result = handle_webhook.remote("$RECORD_ID", "$STATUS", None, None)
print(f"Result: {result}")
EOF
