"""
Delete all posts from Airtable to start fresh.
"""

import os
import requests

def delete_all_posts():
    """Delete all posts from Airtable."""

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
    print("🗑️  DELETING ALL POSTS FROM AIRTABLE")
    print("="*80 + "\n")

    deleted_count = 0

    for post in posts:
        record_id = post['id']
        fields = post.get('fields', {})
        title = fields.get('Title', 'Unknown')

        delete_url = f"{url}/{record_id}"
        delete_response = requests.delete(delete_url, headers=headers)

        if delete_response.status_code == 200:
            print(f"✅ Deleted: {title[:60]}")
            deleted_count += 1
        else:
            print(f"❌ Error: {delete_response.status_code} - {title[:60]}")

    print("\n" + "="*80)
    print(f"✅ COMPLETE - Deleted {deleted_count} posts from Airtable")
    print("="*80 + "\n")

if __name__ == "__main__":
    delete_all_posts()
