#!/usr/bin/env python3
"""
Setup script for Upwork Automation Airtable Base
=================================================
Creates the Airtable base and configures fields for Upwork job tracking.

Since Airtable doesn't allow programmatic base creation,
this script will:
1. Check if AIRTABLE_UPWORK_BASE_ID is set
2. If not, guide you through manual creation
3. Set up the table structure
"""

import os
import sys
import requests
from dotenv import load_dotenv, set_key

load_dotenv()


def check_airtable_credentials():
    """Check if Airtable credentials are configured"""
    api_key = os.getenv('AIRTABLE_API_KEY')
    
    if not api_key:
        print("❌ AIRTABLE_API_KEY not found in .env file")
        print("   Please add your Airtable Personal Access Token")
        print("   Get it from: https://airtable.com/create/tokens")
        return False
    
    print(f"✓ Airtable API Key found: {api_key[:20]}...")
    return True


def check_upwork_base():
    """Check if Upwork base is configured"""
    base_id = os.getenv('AIRTABLE_UPWORK_BASE_ID')
    
    if base_id:
        print(f"✓ Upwork Base ID found: {base_id}")
        return base_id
    
    # Fall back to generic base ID
    base_id = os.getenv('AIRTABLE_BASE_ID')
    if base_id:
        print(f"⚠️  Using generic AIRTABLE_BASE_ID: {base_id}")
        print("   Consider setting AIRTABLE_UPWORK_BASE_ID for a dedicated base")
        return base_id
    
    return None


def create_base_instructions():
    """Print instructions for creating the Airtable base"""
    print("\n" + "=" * 60)
    print("CREATE AIRTABLE BASE FOR UPWORK AUTOMATION")
    print("=" * 60)
    print("""
Steps to create your Airtable base:

1. Go to https://airtable.com
2. Click '+ Create a base' (or '+ Add a base' on your workspace)
3. Choose 'Start from scratch'
4. Name it: 'Upwork Job Automation'
5. You'll see a default table - rename it to: 'Upwork Jobs'

6. Get the Base ID:
   - Look at the URL: https://airtable.com/appXXXXXXXXXXXXXX/...
   - The 'appXXXXXXXXXXXXXX' part is your Base ID
   - It starts with 'app' followed by random characters

7. Add to your .env file:
   AIRTABLE_UPWORK_BASE_ID=appXXXXXXXXXXXXXX
   
8. Run this script again to set up the table fields

""")
    print("=" * 60)


def setup_table_fields(base_id: str, api_key: str):
    """Set up the required fields in Airtable"""
    print("\nSetting up Airtable table fields...")
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    table_name = 'Upwork Jobs'
    url = f'https://api.airtable.com/v0/{base_id}/{table_name}'
    
    # Create a sample record to establish fields
    sample_record = {
        "fields": {
            "Job Title": "🔧 SETUP - Delete this row",
            "Job ID": "_setup_record_",
            "Job URL": "https://upwork.com",
            "Description": "This record was created to set up the table structure. You can delete it.",
            "Budget": 0,
            "Job Type": "fixed-price",
            "Skills": "Python, Automation, API",
            "Client Rating": 5.0,
            "Client Reviews": 100,
            "Client Spent": "$10K+",
            "Client Country": "United States",
            "Payment Verified": True,
            "Posted": "Just now",
            "Proposals Count": 0,
            "Status": "New",
            "Score": 85,
            "Scraped At": "2025-01-01T00:00:00",
            "Notes": "Delete this setup record",
            "Proposal": "",
            "Applied": False
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=sample_record)
        
        if response.status_code == 200:
            print("✓ Table fields created successfully!")
            print("\nFields created:")
            for field in sample_record['fields'].keys():
                print(f"   • {field}")
            
            # Note: We're NOT deleting the sample record so user can see the structure
            print("\n⚠️  A sample record was created in your table.")
            print("   You can delete it after reviewing the field structure.")
            return True
            
        elif response.status_code == 404:
            print(f"❌ Table '{table_name}' not found!")
            print("   Please create a table named 'Upwork Jobs' in your base")
            return False
            
        elif response.status_code == 422:
            print("⚠️  Some fields may already exist (this is OK)")
            print(f"   Response: {response.text}")
            return True
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error setting up fields: {e}")
        return False


def verify_setup(base_id: str, api_key: str):
    """Verify the Airtable setup is working"""
    print("\nVerifying Airtable setup...")
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    url = f'https://api.airtable.com/v0/{base_id}/Upwork Jobs'
    params = {'maxRecords': 1}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            records = response.json().get('records', [])
            print(f"✓ Successfully connected to Airtable!")
            print(f"   Records in table: {len(records)}+")
            return True
        else:
            print(f"❌ Failed to verify: {response.status_code}")
            print(f"   {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False


def update_env_file(base_id: str):
    """Update .env file with the base ID"""
    env_path = '.env'
    
    try:
        set_key(env_path, 'AIRTABLE_UPWORK_BASE_ID', base_id)
        print(f"✓ Updated .env with AIRTABLE_UPWORK_BASE_ID={base_id}")
        return True
    except Exception as e:
        print(f"⚠️  Could not update .env file: {e}")
        print(f"   Please manually add: AIRTABLE_UPWORK_BASE_ID={base_id}")
        return False


def main():
    print("\n" + "=" * 60)
    print("UPWORK AIRTABLE SETUP")
    print("=" * 60 + "\n")
    
    # Step 1: Check credentials
    if not check_airtable_credentials():
        return False
    
    api_key = os.getenv('AIRTABLE_API_KEY')
    
    # Step 2: Check if base is configured
    base_id = check_upwork_base()
    
    if not base_id:
        create_base_instructions()
        
        # Ask for base ID
        print("\nEnter your Airtable Base ID (starts with 'app'):")
        base_id = input("> ").strip()
        
        if not base_id or not base_id.startswith('app'):
            print("❌ Invalid Base ID. Please run setup again.")
            return False
        
        # Save to .env
        update_env_file(base_id)
    
    # Step 3: Set up table fields
    if not setup_table_fields(base_id, api_key):
        print("\n⚠️  Field setup had issues. Please check your Airtable base.")
        return False
    
    # Step 4: Verify
    if verify_setup(base_id, api_key):
        print("\n" + "=" * 60)
        print("✅ SETUP COMPLETE!")
        print("=" * 60)
        print("""
Your Airtable is ready for Upwork job tracking!

Next steps:
1. Run the scraper: python orchestrate.py --action scrape --manual --query "Python"
2. Sync to Airtable: python orchestrate.py --action sync
3. View jobs in Airtable and update statuses
4. Generate proposals: python orchestrate.py --action proposals

Airtable Status workflow:
• New → Review → Approved → Proposal Ready → Applied → Hired/Rejected
""")
        return True
    
    return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
