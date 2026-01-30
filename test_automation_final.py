#!/usr/bin/env python3
"""
Test the complete LinkedIn automation - verify image generation
"""
import requests
import json
import os
import sys
import time
from datetime import datetime

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

def get_record(record_id):
    """Get a specific record"""
    headers = {
        'Authorization': f'Bearer {AIRTABLE_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    url = f"{AIRTABLE_API_URL}/{record_id}"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error fetching record: {response.text}")
        return None
    
    return response.json()

def main():
    print("\n" + "="*70)
    print("✨ LinkedIn Automation End-to-End Test")
    print("="*70)
    
    # Get Draft records
    print("\n📋 Step 1: Fetching Draft records from Airtable...")
    draft_records = get_draft_records()
    
    if not draft_records:
        print("❌ No Draft records found")
        return
    
    # Pick the first Draft record
    test_record = draft_records[0]
    record_id = test_record['id']
    record_title = test_record['fields'].get('Name', 'Unknown')
    
    print(f"✅ Selected: {record_title} ({record_id})")
    
    # Check initial state
    print("\n📸 Step 2: Checking initial state...")
    initial_record = get_record(record_id)
    initial_image_url = initial_record['fields'].get('Image URL', None)
    print(f"   Initial status: {initial_record['fields'].get('Status', 'N/A')}")
    print(f"   Initial image URL: {initial_image_url if initial_image_url else '❌ None'}")
    
    # Change status to trigger automation
    print(f"\n⚙️  Step 3: Triggering automation...")
    print(f"   Changing status to 'Pending Review'...")
    if not update_record_status(record_id, 'Pending Review'):
        print("❌ Failed to update status")
        return
    print("✅ Status updated")
    
    # Wait for processing
    print("\n⏳ Step 4: Waiting for image generation (30 seconds)...")
    print("   ", end='', flush=True)
    for i in range(30, 0, -1):
        if i % 10 == 0 or i <= 3:
            print(f"{i}s ", end='', flush=True)
        time.sleep(1)
    print("✅")
    
    # Check final state
    print("\n✅ Step 5: Checking final state...")
    final_record = get_record(record_id)
    final_status = final_record['fields'].get('Status', 'N/A')
    final_image_url = final_record['fields'].get('Image URL', None)
    
    print(f"   Final status: {final_status}")
    print(f"   Final image URL: {final_image_url if final_image_url else '❌ None'}")
    
    # Summary
    print("\n" + "="*70)
    if final_image_url and final_image_url != initial_image_url:
        print("🎉 SUCCESS! Automation completed successfully!")
        print(f"\n📷 Generated image URL:")
        print(f"   {final_image_url}")
        print("\n✅ Complete workflow verified:")
        print("   1. ✅ Status change detected (polling worked)")
        print("   2. ✅ Webhook triggered (webhook server working)")
        print("   3. ✅ Modal function executed (image generation started)")
        print("   4. ✅ Image generated and saved to Airtable (automation complete)")
    else:
        print("❌ Automation did not complete successfully")
        print(f"   Image URL unchanged or still processing")
    
    print("="*70 + "\n")

if __name__ == '__main__':
    main()
