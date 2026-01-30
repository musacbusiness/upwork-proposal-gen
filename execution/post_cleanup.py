"""
Post Cleanup Automation
Deletes posts that have been in "Posted" status for 7+ days.
"""

import os
import requests
from datetime import datetime, timedelta

class PostCleanup:
    """Manages post cleanup and deletion."""

    def __init__(self):
        """Initialize cleanup manager."""
        env_file = "/Users/musacomma/Agentic Workflow/.env"
        if os.path.exists(env_file):
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip().strip('"\'')

        self.airtable_api_key = os.environ.get('AIRTABLE_API_KEY')
        self.airtable_base_id = os.environ.get('AIRTABLE_BASE_ID')
        self.airtable_table_id = os.environ.get('AIRTABLE_LINKEDIN_TABLE_ID')
        self.headers = {
            "Authorization": f"Bearer {self.airtable_api_key}",
            "Content-Type": "application/json"
        }

    def fetch_all_posts(self) -> list:
        """Fetch all posts from Airtable."""
        url = f"https://api.airtable.com/v0/{self.airtable_base_id}/{self.airtable_table_id}"
        response = requests.get(url, headers=self.headers)

        if response.status_code != 200:
            return []

        return response.json().get('records', [])

    def get_posts_to_delete(self) -> list:
        """Get posts that have been Posted for 7+ days."""
        posts = self.fetch_all_posts()
        deletion_candidates = []
        now = datetime.now()
        seven_days_ago = now - timedelta(days=7)

        for post in posts:
            fields = post.get('fields', {})
            status = fields.get('Status', '')

            # Only check "Posted" posts
            if status != 'Posted':
                continue

            # Check Posted At timestamp
            posted_at = fields.get('Posted At')

            if posted_at:
                try:
                    posted_dt = datetime.fromisoformat(posted_at)

                    # If posted more than 7 days ago, mark for deletion
                    if posted_dt <= seven_days_ago:
                        deletion_candidates.append({
                            'id': post['id'],
                            'title': fields.get('Title', 'Unknown'),
                            'posted_at': posted_dt
                        })
                except ValueError:
                    continue

        return deletion_candidates

    def delete_post(self, record_id: str) -> bool:
        """Delete a post from Airtable."""
        url = f"https://api.airtable.com/v0/{self.airtable_base_id}/{self.airtable_table_id}/{record_id}"
        response = requests.delete(url, headers=self.headers)
        return response.status_code == 200

    def run_cleanup(self):
        """Run the cleanup process."""
        print("="*80)
        print("🗑️  POST CLEANUP - DELETING EXPIRED POSTS")
        print("="*80 + "\n")

        posts_to_delete = self.get_posts_to_delete()

        if not posts_to_delete:
            print("✅ No posts eligible for deletion (posts Posted less than 7 days ago)")
            print("="*80 + "\n")
            return

        print(f"Found {len(posts_to_delete)} post(s) ready for deletion:\n")

        deleted_count = 0
        for post in posts_to_delete:
            if self.delete_post(post['id']):
                days_posted = (datetime.now() - post['posted_at']).days
                print(f"  ✅ Deleted: {post['title'][:60]}...")
                print(f"     Posted {days_posted} days ago\n")
                deleted_count += 1
            else:
                print(f"  ❌ Failed: {post['title'][:60]}...\n")

        print("="*80)
        print(f"✅ CLEANUP COMPLETE - Deleted {deleted_count}/{len(posts_to_delete)} posts")
        print("="*80 + "\n")

def main():
    """Main execution."""
    cleanup = PostCleanup()
    cleanup.run_cleanup()

if __name__ == "__main__":
    main()
