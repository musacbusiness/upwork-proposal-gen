"""
Smart Queue-Based Scheduler
Detects posts with "Approved - Ready to Schedule" status, queues them,
and assigns to available time slots (8-10am, 12-2pm, 5-7pm).
"""

import os
import requests
from datetime import datetime, timedelta
import random
import json
from pathlib import Path

class TimeSlot:
    """Represents a time slot."""
    def __init__(self, date: datetime, slot_number: int):
        self.date = date
        self.slot = slot_number  # 1, 2, or 3

    @property
    def start_hour(self) -> int:
        """Start hour for this slot."""
        return {1: 8, 2: 12, 3: 17}[self.slot]

    @property
    def end_hour(self) -> int:
        """End hour for this slot."""
        return {1: 10, 2: 14, 3: 19}[self.slot]

    @property
    def slot_name(self) -> str:
        """Human-readable slot name."""
        return {1: "8-10 AM", 2: "12-2 PM", 3: "5-7 PM"}[self.slot]

    def get_scheduled_time(self) -> str:
        """Get random time within this slot in ISO format."""
        minute = random.randint(0, 59)
        scheduled = self.date.replace(hour=self.start_hour, minute=minute, second=0)
        return scheduled.isoformat()


class SmartScheduler:
    """Intelligent scheduler for LinkedIn posts."""

    def __init__(self):
        """Initialize scheduler."""
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

    def get_posts_to_schedule(self) -> list:
        """Get posts with 'Approved - Ready to Schedule' status, sorted by created date."""
        posts = self.fetch_all_posts()

        approved = [p for p in posts if p.get('fields', {}).get('Status') == 'Approved - Ready to Schedule']

        # Sort by created date (oldest first)
        approved.sort(key=lambda x: x.get('createdTime', ''))

        return approved

    def get_occupied_slots(self) -> dict:
        """Get occupied time slots. Returns: {date_str: {slot_num: True/False}}"""
        posts = self.fetch_all_posts()
        occupied = {}

        for post in posts:
            fields = post.get('fields', {})
            status = fields.get('Status', '')
            scheduled_time = fields.get('Scheduled Time')

            # Only count scheduled posts (Pending Review, Posted)
            if scheduled_time and status in ['Pending Review', 'Posted']:
                try:
                    dt = datetime.fromisoformat(scheduled_time)
                    date_key = dt.date().isoformat()

                    if date_key not in occupied:
                        occupied[date_key] = {1: False, 2: False, 3: False}

                    # Determine which slot this post occupies
                    hour = dt.hour
                    if 8 <= hour < 10:
                        slot = 1
                    elif 12 <= hour < 14:
                        slot = 2
                    elif 17 <= hour < 19:
                        slot = 3
                    else:
                        continue

                    occupied[date_key][slot] = True

                except ValueError:
                    continue

        return occupied

    def find_available_slot(self, start_date: datetime = None) -> TimeSlot:
        """Find next available time slot starting from start_date."""
        if start_date is None:
            start_date = datetime.now()

        occupied = self.get_occupied_slots()

        # Search forward up to 60 days
        for days_offset in range(60):
            check_date = start_date + timedelta(days=days_offset)
            date_key = check_date.date().isoformat()

            occupied_today = occupied.get(date_key, {1: False, 2: False, 3: False})

            # Try slots in order
            for slot_num in [1, 2, 3]:
                if not occupied_today[slot_num]:
                    return TimeSlot(check_date, slot_num)

        # Fallback (should never reach here)
        return TimeSlot(start_date, 1)

    def update_post_scheduled_time(self, record_id: str, scheduled_time: str) -> bool:
        """Update a post's scheduled time in Airtable."""
        url = f"https://api.airtable.com/v0/{self.airtable_base_id}/{self.airtable_table_id}/{record_id}"

        payload = {
            "fields": {
                "Scheduled Time": scheduled_time,
                "Status": "Pending Review"  # Change status to Pending Review when scheduled
            }
        }

        response = requests.patch(url, headers=self.headers, json=payload)
        return response.status_code == 200

    def process_queue(self):
        """Process queue of posts awaiting scheduling."""
        posts_to_schedule = self.get_posts_to_schedule()

        if not posts_to_schedule:
            print("✅ No posts in scheduling queue")
            return

        print("="*80)
        print(f"📅 PROCESSING SCHEDULING QUEUE ({len(posts_to_schedule)} posts)")
        print("="*80 + "\n")

        start_date = datetime.now()

        for i, post in enumerate(posts_to_schedule, 1):
            record_id = post['id']
            fields = post.get('fields', {})
            title = fields.get('Title', 'Unknown')

            # Find next available slot
            slot = self.find_available_slot(start_date)
            scheduled_time = slot.get_scheduled_time()

            # Update post
            if self.update_post_scheduled_time(record_id, scheduled_time):
                scheduled_dt = datetime.fromisoformat(scheduled_time)
                print(f"  {i}/{len(posts_to_schedule)} ✅ Scheduled: {title[:50]}...")
                print(f"     📍 {scheduled_dt.strftime('%a, %b %d')} @ {slot.slot_name}\n")
            else:
                print(f"  {i}/{len(posts_to_schedule)} ❌ Failed: {title[:50]}...\n")

        print("="*80)
        print(f"✅ SCHEDULING COMPLETE - {len(posts_to_schedule)} posts queued")
        print("="*80 + "\n")

def main():
    """Main execution."""
    scheduler = SmartScheduler()
    scheduler.process_queue()

if __name__ == "__main__":
    main()
