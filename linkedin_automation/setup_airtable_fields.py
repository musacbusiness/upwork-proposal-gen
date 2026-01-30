#!/usr/bin/env python3
"""
setup_airtable_fields.py - Add Revision Prompt field and Button to Airtable

This script adds the required fields to your LinkedIn Posts table:
1. Revision Prompt (Long text field)
2. Revise Content (Button field)

Usage:
    python3 setup_airtable_fields.py
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

# Airtable configuration
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
BASE_ID = 'appw88uD6ZM0ckF8f'
TABLE_ID = 'tbljg75KMQWDo2Hgu'

def add_revision_prompt_field():
    """Add Revision Prompt long text field"""
    
    url = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables/{TABLE_ID}/fields"
    
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "name": "Revision Prompt",
        "type": "multilineText"
    }
    
    print("Adding 'Revision Prompt' field...")
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        print("✅ Successfully added 'Revision Prompt' field!")
        return True
    else:
        print(f"❌ Failed to add field: {response.status_code}")
        print(f"Response: {response.text}")
        return False


def add_button_field():
    """Add Revise Content button field"""
    
    url = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables/{TABLE_ID}/fields"
    
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Button field with URL formula
    payload = {
        "name": "Revise Content",
        "type": "button",
        "options": {
            "label": "🔄 Regenerate",
            "url": "CONCATENATE('http://localhost:5050/revise/', RECORD_ID())"
        }
    }
    
    print("Adding 'Revise Content' button field...")
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        print("✅ Successfully added 'Revise Content' button!")
        return True
    else:
        print(f"❌ Failed to add button: {response.status_code}")
        print(f"Response: {response.text}")
        return False


def check_existing_fields():
    """Check what fields already exist"""
    
    url = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables/{TABLE_ID}"
    
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}"
    }
    
    print("Checking existing fields...")
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        fields = data.get('fields', [])
        field_names = [f['name'] for f in fields]
        
        print("\nExisting fields:")
        for name in field_names:
            print(f"  - {name}")
        
        return field_names
    else:
        print(f"❌ Failed to fetch fields: {response.status_code}")
        return []


def main():
    print("=" * 60)
    print("Airtable Field Setup - LinkedIn Automation")
    print("=" * 60)
    print()
    
    if not AIRTABLE_API_KEY:
        print("❌ Error: AIRTABLE_API_KEY not found in .env file")
        return
    
    # Check existing fields
    existing_fields = check_existing_fields()
    print()
    
    # Add Revision Prompt if it doesn't exist
    if "Revision Prompt" in existing_fields:
        print("ℹ️  'Revision Prompt' field already exists, skipping...")
    else:
        add_revision_prompt_field()
    
    print()
    
    # Add Button if it doesn't exist
    if "Revise Content" in existing_fields:
        print("ℹ️  'Revise Content' button already exists, skipping...")
    else:
        add_button_field()
    
    print()
    print("=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Go to your Airtable table")
    print("2. You should see:")
    print("   - 'Revision Prompt' column (for typing revision instructions)")
    print("   - 'Revise Content' column with 🔄 Regenerate button")
    print("3. Test it:")
    print("   - Type in Revision Prompt: 'Make this shorter'")
    print("   - Click the 🔄 Regenerate button")
    print("   - Watch it update!")
    print()


if __name__ == "__main__":
    main()
