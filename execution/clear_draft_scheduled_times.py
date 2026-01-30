"""
Clear scheduled times from posts in Draft status.
Posts should only be scheduled when moved to Pending Review.
"""

import os
import requests

def clear_draft_scheduled_times():
    """Remove scheduled times from Draft posts."""

    # Load environment
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

    # Fetch all posts
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Error fetching posts: {response.status_code}")
        return

    posts = response.json().get('records', [])

    print("="*80)
    print("🧹 CLEARING SCHEDULED TIMES FROM DRAFT POSTS")
    print("="*80 + "\n")

    cleared_count = 0

    for post in posts:
        record_id = post['id']
        fields = post.get('fields', {})
        status = fields.get('Status', '')
        scheduled_time = fields.get('Scheduled Time')
        title = fields.get('Title', 'Unknown')

        # Check if post is in Draft status and has a scheduled time
        if status == 'Draft' and scheduled_time:
            # Clear the scheduled time
            update_url = f"{url}/{record_id}"
            update_payload = {
                "fields": {
                    "Scheduled Time": None
                }
            }

            update_response = requests.patch(update_url, headers=headers, json=update_payload)

            if update_response.status_code == 200:
                print(f"✅ Cleared: {title}")
                print(f"   Status: Draft (will schedule when moved to Pending Review)\n")
                cleared_count += 1
            else:
                print(f"❌ Error clearing {title}: {update_response.status_code}\n")

    print("="*80)
    if cleared_count > 0:
        print(f"✅ Cleared scheduled times from {cleared_count} Draft post(s)")
        print("\nWorkflow:")
        print("  1. ✅ Posts created as Draft (no scheduled time)")
        print("  2. 📝 You review and edit posts")
        print("  3. 🔄 Change status to 'Pending Review'")
        print("  4. 🔧 Run: python3 execution/schedule_pending_posts.py")
        print("  5. 📅 Posts get random scheduled times (1-30 days @ 9 AM)")
    else:
        print("ℹ️  No Draft posts with scheduled times to clear")
    print("="*80)

if __name__ == "__main__":
    clear_draft_scheduled_times()
