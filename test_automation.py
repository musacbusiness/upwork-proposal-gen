#!/usr/bin/env python3
"""
Test the complete automation: change a record status and monitor the results
"""
import requests
import json
import os
import sys
import time
from datetime import datetime

# Add cloud directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'cloud'))

# Airtable API setup
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
BASE_ID = os.getenv('AIRTABLE_BASE_ID', 'appw88uD6ZM0ckF8f')
TABLE_ID = os.getenv('AIRTABLE_LINKEDIN_TABLE_ID', 'tbljg75KMQWDo2Hgu')

AIRTABLE_API_URL = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}"

def get_draft_records():
    """Get all Draft records"""
    headers = {
        'Authorization': f'Bearer {AIRTABLE_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Filter for Draft status
    url = f"{AIRTABLE_API_URL}?filterByFormula={{Status}}='Draft'"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error fetching records: {response.text}")
        return []
    
    return response.json().get('records', [])

def update_record_status(record_id, new_status):
    """Update a record's status"""
    headers = {
        'Authorization': f'Bearer {AIRTABLE_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'fields': {
            'Status': new_status
        }
    }
    
    url = f"{AIRTABLE_API_URL}/{record_id}"
    response = requests.patch(url, json=data, headers=headers)
    
    if response.status_code not in [200, 201]:
        print(f"Error updating record: {response.text}")
        return False
    
    return True

def check_attachments(record_id):
    """Check if a record has attachments"""
    headers = {
        'Authorization': f'Bearer {AIRTABLE_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    url = f"{AIRTABLE_API_URL}/{record_id}"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error fetching record: {response.text}")
        return None
    
    record = response.json()
    attachments = record.get('fields', {}).get('Attachments', [])
    return attachments

def main():
    print("\n" + "="*60)
    print("🚀 Testing Complete LinkedIn Automation")
    print("="*60)
    
    # Get Draft records
    print("\n📋 Fetching Draft records...")
    draft_records = get_draft_records()
    
    if not draft_records:
        print("❌ No Draft records found")
        return
    
    # Pick the first Draft record
    test_record = draft_records[0]
    record_id = test_record['id']
    record_title = test_record['fields'].get('Name', 'Unknown')
    
    print(f"✅ Selected record: {record_title} ({record_id})")
    
    # Check attachments before
    print("\n📸 Checking attachments before automation...")
    attachments_before = check_attachments(record_id)
    print(f"   Attachments before: {len(attachments_before or [])} files")
    
    # Change status to trigger automation
    print(f"\n⏱️  Changing status to 'Pending Review' to trigger automation...")
    if update_record_status(record_id, 'Pending Review'):
        print("✅ Status updated successfully")
    else:
        print("❌ Failed to update status")
        return
    
    # Wait for automation to process
    print("\n⏳ Waiting 5 seconds for automation to process...")
    for i in range(5, 0, -1):
        print(f"   {i}...", end='', flush=True)
        time.sleep(1)
    print(" ✅")
    
    # Check attachments after
    print("\n📸 Checking attachments after automation...")
    attachments_after = check_attachments(record_id)
    print(f"   Attachments after: {len(attachments_after or [])} files")
    
    if attachments_after and len(attachments_after) > len(attachments_before or []):
        print("\n🎉 SUCCESS! Image was generated and uploaded!")
        print(f"   New attachments: {[a.get('filename') for a in attachments_after[-1:]]}")
    else:
        print("\n⚠️  No new attachments detected")
        print("   The automation may still be processing, or there was an error")
    
    print("\n" + "="*60)
    print("Test complete")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
