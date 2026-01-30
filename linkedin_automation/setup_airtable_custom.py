#!/usr/bin/env python3
"""
Airtable Base Setup Script - Custom LinkedIn Automation Tables
"""

import requests
import json

# Configuration
API_KEY = "patQCCzbAjKw675Bf.a9220198778415662363c84105e67b9c47399f5a01e27688f18f429115574a5c"
BASE_ID = "appw88uD6ZM0ckF8f"

BASE_URL = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

print(f"\n🚀 Setting up LinkedIn Content Automation in base: {BASE_ID}\n")

# Delete existing table if any
print("Checking for existing tables...")
get_response = requests.get(f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables", headers=headers)
if get_response.status_code == 200:
    existing_tables = get_response.json().get('tables', [])
    print(f"Found {len(existing_tables)} existing tables")

# Table 1: LinkedIn Posts
print("\nCreating 'LinkedIn Posts' table...")
posts_table = {
    "name": "LinkedIn Posts",
    "description": "LinkedIn content with research sources, frameworks, and approval status",
    "fields": [
        {
            "name": "Title",
            "type": "singleLineText",
            "description": "Title/headline of the LinkedIn post"
        },
        {
            "name": "Post Content",
            "type": "multilineText",
            "description": "Full text content of the LinkedIn post"
        },
        {
            "name": "Research Source(s)",
            "type": "multilineText",
            "description": "Sources where the content/research came from"
        },
        {
            "name": "Writing Framework",
            "type": "singleSelect",
            "description": "Framework used to structure the post",
            "options": {
                "choices": [
                    {"name": "PAS (Problem-Agitate-Solution)", "color": "blueBright"},
                    {"name": "AIDA (Attention-Interest-Desire-Action)", "color": "greenBright"},
                    {"name": "BAB (Before-After-Bridge)", "color": "purpleBright"},
                    {"name": "Storytelling", "color": "orangeBright"},
                    {"name": "How-To Guide", "color": "cyanBright"},
                    {"name": "Listicle", "color": "pinkBright"},
                    {"name": "Case Study", "color": "yellowBright"},
                    {"name": "Question-Answer", "color": "tealBright"}
                ]
            }
        },
        {
            "name": "Image",
            "type": "multipleAttachments",
            "description": "Generated image for the post"
        },
        {
            "name": "Image URL",
            "type": "url",
            "description": "URL to the generated image (if hosted externally)"
        },
        {
            "name": "Status",
            "type": "singleSelect",
            "description": "Approval and scheduling status",
            "options": {
                "choices": [
                    {"name": "Draft", "color": "grayBright"},
                    {"name": "Pending Review", "color": "yellowBright"},
                    {"name": "Approved - Ready to Schedule", "color": "greenBright"},
                    {"name": "Scheduled", "color": "blueBright"},
                    {"name": "Posted", "color": "purpleBright"},
                    {"name": "Rejected", "color": "redBright"}
                ]
            }
        },
        {
            "name": "Created Date",
            "type": "dateTime",
            "description": "When the post was generated",
            "options": {
                "dateFormat": {
                    "name": "iso"
                },
                "timeFormat": {
                    "name": "24hour"
                },
                "timeZone": "America/New_York"
            }
        },
        {
            "name": "Scheduled Time",
            "type": "dateTime",
            "description": "When the post is scheduled to go live",
            "options": {
                "dateFormat": {
                    "name": "iso"
                },
                "timeFormat": {
                    "name": "24hour"
                },
                "timeZone": "America/New_York"
            }
        },
        {
            "name": "Posted Time",
            "type": "dateTime",
            "description": "When the post was actually published",
            "options": {
                "dateFormat": {
                    "name": "iso"
                },
                "timeFormat": {
                    "name": "24hour"
                },
                "timeZone": "America/New_York"
            }
        },
        {
            "name": "LinkedIn Post URL",
            "type": "url",
            "description": "URL of the live LinkedIn post"
        },
        {
            "name": "Image Prompt",
            "type": "multilineText",
            "description": "Prompt used to generate the image"
        },
        {
            "name": "Notes",
            "type": "multilineText",
            "description": "Additional notes or feedback"
        }
    ]
}

response = requests.post(BASE_URL, headers=headers, json=posts_table)

if response.status_code in [200, 201]:
    posts_table_id = response.json().get('id')
    print(f"✅ 'LinkedIn Posts' table created successfully!")
    print(f"   Table ID: {posts_table_id}")
else:
    print(f"❌ Error creating 'LinkedIn Posts' table: {response.status_code}")
    print(response.text)
    exit(1)

# Table 2: Scheduling Queue
print("\nCreating 'Scheduling Queue' table...")
queue_table = {
    "name": "Scheduling Queue",
    "description": "Tracks scheduled posts and their publishing status",
    "fields": [
        {
            "name": "Scheduled Time",
            "type": "dateTime",
            "description": "When to publish this post",
            "options": {
                "dateFormat": {
                    "name": "iso"
                },
                "timeFormat": {
                    "name": "24hour"
                },
                "timeZone": "America/New_York"
            }
        },
        {
            "name": "Status",
            "type": "singleSelect",
            "options": {
                "choices": [
                    {"name": "Queued", "color": "yellowBright"},
                    {"name": "Publishing", "color": "blueBright"},
                    {"name": "Published", "color": "greenBright"},
                    {"name": "Failed", "color": "redBright"},
                    {"name": "Cancelled", "color": "grayBright"}
                ]
            }
        },
        {
            "name": "Platform",
            "type": "singleLineText",
            "description": "Publishing platform (LinkedIn)"
        },
        {
            "name": "Error Message",
            "type": "multilineText",
            "description": "Error details if publishing failed"
        }
    ]
}

response = requests.post(BASE_URL, headers=headers, json=queue_table)

if response.status_code in [200, 201]:
    queue_table_id = response.json().get('id')
    print(f"✅ 'Scheduling Queue' table created successfully!")
    print(f"   Table ID: {queue_table_id}")
    
    # Add link field from Queue to Posts
    print("\n   Adding link to LinkedIn Posts...")
    link_field = {
        "name": "Post",
        "type": "multipleRecordLinks",
        "options": {
            "linkedTableId": posts_table_id
        }
    }
    
    link_url = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables/{queue_table_id}/fields"
    link_response = requests.post(link_url, headers=headers, json=link_field)
    
    if link_response.status_code in [200, 201]:
        print("   ✅ Link field created successfully")
    else:
        print(f"   ⚠️  Could not create link field: {link_response.status_code}")
else:
    print(f"❌ Error creating 'Scheduling Queue' table: {response.status_code}")
    print(response.text)

print("\n" + "="*70)
print("🎉 Airtable base setup complete!")
print("="*70)
print(f"\nBase ID: {BASE_ID}")
print(f"View at: https://airtable.com/{BASE_ID}")
print("\nTables created:")
print("  1. LinkedIn Posts - Main content table")
print("  2. Scheduling Queue - Publishing schedule tracker")
print("\nNext steps:")
print("  1. Base ID is already in your link")
print("  2. Update .env with: AIRTABLE_BASE_ID=appw88uD6ZM0ckF8f")
print("  3. You can add custom writing frameworks later")
print("  4. Run: python RUN_linkedin_automation.py --action status")

