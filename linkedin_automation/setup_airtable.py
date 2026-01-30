#!/usr/bin/env python3
"""
Airtable Base Setup Script
Automatically creates all required tables and fields for LinkedIn automation
"""

import requests
import json
import sys

# Configuration
API_KEY = "patQCCzbAjKw675Bf.a9220198778415662363c84105e67b9c47399f5a01e27688f18f429115574a5c"
BASE_ID = input("Enter your Airtable Base ID (starts with 'app'): ").strip()

BASE_URL = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

print(f"\n🚀 Setting up LinkedIn Content Automation in base: {BASE_ID}\n")

# Table 1: Posts
print("Creating 'Posts' table...")
posts_table = {
    "name": "Posts",
    "description": "LinkedIn posts with content, images, and approval status",
    "fields": [
        {
            "name": "Title",
            "type": "singleLineText"
        },
        {
            "name": "Content",
            "type": "multilineText"
        },
        {
            "name": "Status",
            "type": "singleSelect",
            "options": {
                "choices": [
                    {"name": "PENDING_APPROVAL", "color": "yellowBright"},
                    {"name": "APPROVED", "color": "greenBright"},
                    {"name": "SCHEDULED", "color": "blueBright"},
                    {"name": "POSTED", "color": "purpleBright"},
                    {"name": "FAILED", "color": "redBright"}
                ]
            }
        },
        {
            "name": "Image URL",
            "type": "url"
        },
        {
            "name": "Image Prompt",
            "type": "multilineText"
        },
        {
            "name": "Content Type",
            "type": "singleSelect",
            "options": {
                "choices": [
                    {"name": "AI Workflow Prompt"},
                    {"name": "Automation Case Study"},
                    {"name": "AI Implementation Guide"},
                    {"name": "Business Tip"},
                    {"name": "Industry Insight"}
                ]
            }
        },
        {
            "name": "Created Date",
            "type": "dateTime",
            "options": {
                "dateFormat": {
                    "name": "iso"
                }
            }
        },
        {
            "name": "Approved By",
            "type": "singleLineText"
        },
        {
            "name": "Approval Date",
            "type": "dateTime"
        },
        {
            "name": "Scheduled Times",
            "type": "multilineText"
        },
        {
            "name": "Posted URL",
            "type": "url"
        },
        {
            "name": "Posted At",
            "type": "dateTime"
        },
        {
            "name": "Approval Notes",
            "type": "multilineText"
        }
    ]
}

response = requests.post(BASE_URL, headers=headers, json=posts_table)

if response.status_code in [200, 201]:
    posts_table_id = response.json().get('id')
    print(f"✅ 'Posts' table created successfully (ID: {posts_table_id})")
else:
    print(f"❌ Error creating 'Posts' table: {response.status_code}")
    print(response.text)
    sys.exit(1)

# Table 2: Scheduling Queue
print("\nCreating 'Scheduling Queue' table...")
queue_table = {
    "name": "Scheduling Queue",
    "description": "Queue of posts scheduled for publishing",
    "fields": [
        {
            "name": "Scheduled Time",
            "type": "dateTime",
            "options": {
                "dateFormat": {
                    "name": "iso"
                }
            }
        },
        {
            "name": "Status",
            "type": "singleSelect",
            "options": {
                "choices": [
                    {"name": "PENDING", "color": "yellowBright"},
                    {"name": "SCHEDULED", "color": "blueBright"},
                    {"name": "POSTED", "color": "greenBright"},
                    {"name": "FAILED", "color": "redBright"}
                ]
            }
        },
        {
            "name": "Platform",
            "type": "singleLineText"
        },
        {
            "name": "Posted URL",
            "type": "url"
        },
        {
            "name": "Error Message",
            "type": "multilineText"
        }
    ]
}

response = requests.post(BASE_URL, headers=headers, json=queue_table)

if response.status_code in [200, 201]:
    queue_table_id = response.json().get('id')
    print(f"✅ 'Scheduling Queue' table created successfully (ID: {queue_table_id})")
    
    # Now add the link field to connect Posts to Scheduling Queue
    print("\nAdding link between Posts and Scheduling Queue...")
    
    link_field = {
        "name": "Post ID",
        "type": "multipleRecordLinks",
        "options": {
            "linkedTableId": posts_table_id
        }
    }
    
    link_url = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables/{queue_table_id}/fields"
    link_response = requests.post(link_url, headers=headers, json=link_field)
    
    if link_response.status_code in [200, 201]:
        print("✅ Link field created successfully")
    else:
        print(f"⚠️  Could not create link field: {link_response.status_code}")
else:
    print(f"❌ Error creating 'Scheduling Queue' table: {response.status_code}")
    print(response.text)
    sys.exit(1)

# Table 3: Content Ideas (optional tracking)
print("\nCreating 'Content Ideas' table (optional)...")
ideas_table = {
    "name": "Content Ideas",
    "description": "Research and content idea tracking",
    "fields": [
        {
            "name": "Topic",
            "type": "singleLineText"
        },
        {
            "name": "Description",
            "type": "multilineText"
        },
        {
            "name": "Content Type",
            "type": "singleSelect",
            "options": {
                "choices": [
                    {"name": "AI Workflow Prompt"},
                    {"name": "Automation Case Study"},
                    {"name": "AI Implementation Guide"},
                    {"name": "Business Tip"},
                    {"name": "Industry Insight"}
                ]
            }
        },
        {
            "name": "Research Date",
            "type": "dateTime"
        },
        {
            "name": "Sources",
            "type": "multilineText"
        },
        {
            "name": "Used",
            "type": "checkbox"
        }
    ]
}

response = requests.post(BASE_URL, headers=headers, json=ideas_table)

if response.status_code in [200, 201]:
    print(f"✅ 'Content Ideas' table created successfully")
else:
    print(f"⚠️  Could not create 'Content Ideas' table (optional): {response.status_code}")

print("\n" + "="*60)
print("🎉 Airtable base setup complete!")
print("="*60)
print(f"\nYour Base ID: {BASE_ID}")
print("\nNext steps:")
print("1. Update your .env file with:")
print(f"   AIRTABLE_BASE_ID={BASE_ID}")
print("2. Update linkedin_automation/config/linkedin_config.json")
print("3. Run: python RUN_linkedin_automation.py --action status")
print("\nView your base at: https://airtable.com/{BASE_ID}")
