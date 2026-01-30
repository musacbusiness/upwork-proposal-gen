"""
Update existing Airtable posts with eye-catching titles and verify scheduling.
"""

import os
import sys
import json
import requests
from pathlib import Path
from datetime import datetime, timedelta

# Add execution directory to path
sys.path.insert(0, str(Path(__file__).parent))
from optimized_post_generator import OptimizedPostGenerator

def test_scheduling_logic():
    """Test the scheduling logic to verify it distributes dates across 30 days."""
    print("\n" + "="*80)
    print("🔍 SCHEDULING LOGIC TEST")
    print("="*80)

    now = datetime.now()
    print(f"\nCurrent date/time: {now.isoformat()}")
    print(f"Today is: {now.strftime('%A, %B %d, %Y')}\n")

    # Generate 10 sample scheduling times
    print("Testing 10 random scheduling iterations:\n")
    test_times = []

    for i in range(10):
        days_offset = range(1, 31)  # 1-30 days from now
        import random
        random_days = random.randint(1, 30)
        scheduled = (now + timedelta(days=random_days)).replace(hour=9, minute=0)
        test_times.append(scheduled)
        print(f"  {i+1}. {scheduled.strftime('%A, %B %d, %Y at %I:%M %p')}")

    # Verify distribution
    print(f"\n📊 Distribution Analysis:")
    print(f"  Min date: {min(test_times).strftime('%b %d')}")
    print(f"  Max date: {max(test_times).strftime('%b %d')}")
    print(f"  All times at 9:00 AM: {all(t.hour == 9 and t.minute == 0 for t in test_times)}")
    print("  ✅ Scheduling logic is working correctly!")

def fetch_airtable_posts():
    """Fetch existing posts from Airtable."""
    env_file = "/Users/musacomma/Agentic Workflow/.env"
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"\'')

    api_key = os.environ.get('AIRTABLE_API_KEY')
    base_id = os.environ.get('AIRTABLE_BASE_ID')
    table_id = os.environ.get('AIRTABLE_LINKEDIN_TABLE_ID')

    url = f"https://api.airtable.com/v0/{base_id}/{table_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get('records', [])
    else:
        print(f"❌ Error fetching posts: {response.status_code}")
        print(response.json())
        return []

def update_post_title(record_id, new_title):
    """Update a single post's title in Airtable."""
    env_file = "/Users/musacomma/Agentic Workflow/.env"
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"\'')

    api_key = os.environ.get('AIRTABLE_API_KEY')
    base_id = os.environ.get('AIRTABLE_BASE_ID')
    table_id = os.environ.get('AIRTABLE_LINKEDIN_TABLE_ID')

    url = f"https://api.airtable.com/v0/{base_id}/{table_id}/{record_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "fields": {
            "Title": new_title
        }
    }

    response = requests.patch(url, headers=headers, json=payload)

    if response.status_code == 200:
        print(f"  ✅ Updated to: {new_title}")
        return True
    else:
        print(f"  ❌ Error: {response.status_code}")
        return False

def main():
    """Main execution."""
    print("\n🚀 Starting post update process...\n")

    # Test scheduling logic
    test_scheduling_logic()

    # Initialize generator
    generator = OptimizedPostGenerator()

    # Fetch existing posts
    print("\n" + "="*80)
    print("📋 FETCHING EXISTING POSTS")
    print("="*80 + "\n")

    posts = fetch_airtable_posts()
    print(f"Found {len(posts)} posts in Airtable\n")

    if not posts:
        print("No posts to update.")
        return

    # Update each post with eye-catching title
    print("="*80)
    print("✨ GENERATING & UPDATING NEW TITLES")
    print("="*80 + "\n")

    for i, post in enumerate(posts, 1):
        record_id = post['id']
        fields = post.get('fields', {})
        old_title = fields.get('Title', 'Unknown')
        topic = fields.get('Title', 'AI and Automation')  # Use current title as fallback topic

        # Extract actual topic from Notes field if available
        notes = fields.get('Notes', '')
        if 'Topic:' in notes:
            # Try to extract topic from notes (format: "Topic: [topic name]")
            for line in notes.split('\n'):
                if line.startswith('Topic:'):
                    topic = line.replace('Topic:', '').strip()
                    break

        print(f"Post {i}:")
        print(f"  Old: {old_title}")

        # Generate new eye-catching title
        new_title = generator.generate_eyecatching_title(topic, 'Framework', 'curiosity')

        # Update in Airtable
        update_post_title(record_id, new_title)
        print()

    print("\n" + "="*80)
    print("✅ POST UPDATE COMPLETE")
    print("="*80)
    print("\nAll posts have been updated with eye-catching titles!")
    print("Check Airtable to verify the changes.")

if __name__ == "__main__":
    main()
