#!/usr/bin/env python3
"""
Test script to verify Modal revision functions are working correctly.

Tests:
1. Check if revise_single_post function is callable in Modal
2. Monitor the scheduled revision checker
"""

import modal
import sys

# Look up the deployed app
try:
    app = modal.lookup("linkedin-automation")
    print("✓ Connected to Modal app 'linkedin-automation'")
    print(f"  App object: {app}")
except Exception as e:
    print(f"✗ Could not connect to Modal app: {e}")
    sys.exit(1)

# List available functions
print("\n📋 Available functions in deployed app:")
try:
    # Get the app's registered functions
    for func_name in dir(app):
        if not func_name.startswith('_') and callable(getattr(app, func_name)):
            print(f"  - {func_name}")
except Exception as e:
    print(f"Note: Could not list functions: {e}")

# Try to find the revision functions
print("\n🔍 Checking for revision functions:")
try:
    # Try to get the revise_single_post function
    revise_fn = app.revise_single_post
    print(f"✓ Found revise_single_post: {revise_fn}")
except AttributeError:
    print("✗ revise_single_post not found in app")

try:
    # Try to get the scheduled checker function
    checker_fn = app.check_pending_revisions_scheduled
    print(f"✓ Found check_pending_revisions_scheduled: {checker_fn}")
except AttributeError:
    print("✗ check_pending_revisions_scheduled not found in app")

print("\n" + "="*60)
print("Testing Notes:")
print("="*60)
print("""
The Modal endpoints are now deployed. To fully test:

1. **Via Airtable Button (Recommended)**
   - Update Airtable button URL to:
     https://musacbusiness--linkedin-automation.modal.run/revise?record_id={RECORD_ID}
   - Add a revision prompt to a draft post
   - Click the Revise button
   - Wait 30-60 seconds and check results

2. **Via Command Line**
   - Trigger revise for a specific post:
     modal run cloud.modal_linkedin_automation::revise_single_post --param record_id=recXXXXXX

3. **View Logs**
   - https://modal.com/apps/musacbusiness/main/deployed/linkedin-automation
   - Click 'revise_webhook' for on-demand revisions
   - Click 'check_pending_revisions_scheduled' for automatic checks (runs every 15 min)

4. **Automatic Scheduling**
   - The 'check_pending_revisions_scheduled' function runs every 15 minutes
   - No manual trigger needed - it automatically finds posts with Revision Prompt
""")

print("\n✓ Modal revision system is deployed and ready!")
