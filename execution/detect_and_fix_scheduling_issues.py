"""
Scheduling Issue Detection & Correction System
==============================================

This script periodically checks for scheduling mistakes in Airtable and corrects them:
1. Detects multiple posts assigned to the same posting window on the same day
2. Identifies posts scheduled in the past
3. Finds posts with invalid scheduled times
4. Auto-corrects distribution issues by reassigning posts to available windows
5. Logs all corrections with reasoning

Run manually:
    python3 execution/detect_and_fix_scheduling_issues.py

Can be integrated into Modal as a periodic task.
"""

import os
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Set
import logging
import pytz
import random
from dotenv import load_dotenv

# ============== Setup ==============

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get credentials from environment
AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID")
AIRTABLE_LINKEDIN_TABLE_ID = os.environ.get("AIRTABLE_LINKEDIN_TABLE_ID")

if not all([AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_LINKEDIN_TABLE_ID]):
    raise ValueError("Missing required Airtable credentials")

POSTING_WINDOWS = [9, 14, 20]  # 9 AM, 2 PM, 8 PM ET
WINDOW_BUFFER_MINUTES = 30  # Posts within 30 min of window belong to that window
TZ = pytz.timezone('America/New_York')

# ============== Airtable API Helpers ==============

def get_headers():
    """Get Airtable API headers"""
    return {
        'Authorization': f'Bearer {AIRTABLE_API_KEY}',
        'Content-Type': 'application/json'
    }


def fetch_all_records() -> List[Dict]:
    """Fetch all records from the LinkedIn table"""
    try:
        url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_LINKEDIN_TABLE_ID}"
        response = requests.get(url, headers=get_headers(), timeout=30)

        if response.status_code == 200:
            return response.json().get('records', [])
        else:
            logger.error(f"Failed to fetch records: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        logger.error(f"Error fetching records: {e}")
        return []


def update_record(record_id: str, fields: Dict) -> bool:
    """Update a single Airtable record"""
    try:
        url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_LINKEDIN_TABLE_ID}/{record_id}"
        payload = {"fields": fields}

        response = requests.patch(url, json=payload, headers=get_headers(), timeout=30)

        if response.status_code == 200:
            logger.info(f"✓ Updated record {record_id}: {json.dumps(fields)}")
            return True
        else:
            logger.error(f"Failed to update {record_id}: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error updating record {record_id}: {e}")
        return False


# ============== Detection Logic ==============

def parse_scheduled_time(time_str: str) -> Tuple[datetime, bool]:
    """
    Parse scheduled time string.
    Handles both ISO format with timezone and UTC Z format.
    Returns (datetime, is_valid)
    """
    if not time_str:
        return None, False

    try:
        # Try standard ISO format first
        dt = datetime.fromisoformat(time_str).astimezone(TZ)
        return dt, True
    except:
        pass

    try:
        # Handle UTC Z format (e.g., 2025-12-30T13:48:00.000Z)
        if time_str.endswith('Z'):
            # Replace Z with +00:00 for UTC
            utc_str = time_str.replace('Z', '+00:00')
            dt = datetime.fromisoformat(utc_str).astimezone(TZ)
            return dt, True
    except:
        pass

    logger.warning(f"Invalid scheduled time format: {time_str}")
    return None, False


def determine_posting_window(scheduled_dt: datetime) -> int:
    """
    Determine which posting window a scheduled time belongs to.
    Returns the window hour (9, 14, or 20) or None if not in any window.
    """
    for window_hour in POSTING_WINDOWS:
        window_time = scheduled_dt.replace(hour=window_hour, minute=0, second=0, microsecond=0)
        time_diff = abs((scheduled_dt - window_time).total_seconds() / 60)

        if time_diff <= WINDOW_BUFFER_MINUTES:
            return window_hour

    return None


def get_window_key(scheduled_dt: datetime) -> Tuple[str, int]:
    """
    Get a unique key for a scheduled time (date_str, window_hour).
    Used to group posts by day and window.
    """
    date_key = scheduled_dt.strftime('%Y-%m-%d')
    window_hour = determine_posting_window(scheduled_dt)
    return (date_key, window_hour)


def detect_issues() -> Dict:
    """
    Detect all scheduling issues in Airtable.
    Returns dict with issue types and affected records.
    """
    records = fetch_all_records()
    issues = {
        'multiple_in_window': [],      # Multiple posts in same window/day
        'scheduled_in_past': [],        # Posts scheduled in the past
        'invalid_times': [],            # Posts with invalid scheduled times
        'all_records': records          # For reference
    }

    now = datetime.now(TZ)
    window_occupancy = {}  # Key: (date, window_hour), Value: [record_ids]

    logger.info(f"\n{'='*70}")
    logger.info(f"SCHEDULING ISSUE DETECTION - {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    logger.info(f"{'='*70}\n")

    for record in records:
        record_id = record.get('id')
        fields = record.get('fields', {})
        title = fields.get('Title', 'Untitled')
        status = fields.get('Status', 'Unknown')
        scheduled_time_str = fields.get('Scheduled Time')

        # Skip if not scheduled
        if not scheduled_time_str:
            continue

        # Skip if not in "Scheduled" status
        if status != 'Scheduled':
            logger.warning(f"⚠ Record {record_id} has Scheduled Time but status is '{status}' (not 'Scheduled')")
            continue

        # Parse scheduled time
        scheduled_dt, is_valid = parse_scheduled_time(scheduled_time_str)

        if not is_valid:
            issues['invalid_times'].append({
                'record_id': record_id,
                'title': title,
                'scheduled_time_str': scheduled_time_str,
                'error': 'Invalid date format'
            })
            logger.error(f"✗ {record_id}: Invalid scheduled time format: {scheduled_time_str}")
            continue

        # Check if scheduled in past
        if scheduled_dt < now:
            issues['scheduled_in_past'].append({
                'record_id': record_id,
                'title': title,
                'scheduled_time': scheduled_dt.isoformat(),
                'current_time': now.isoformat(),
                'hours_past': (now - scheduled_dt).total_seconds() / 3600
            })
            logger.warning(f"⚠ {record_id}: Scheduled in past ({(now - scheduled_dt).total_seconds() / 3600:.1f} hours ago)")
            continue

        # Track window occupancy
        window_key = get_window_key(scheduled_dt)
        date_key, window_hour = window_key

        if window_key not in window_occupancy:
            window_occupancy[window_key] = []

        window_occupancy[window_key].append({
            'record_id': record_id,
            'title': title,
            'scheduled_time': scheduled_dt.isoformat()
        })

    # Detect multiple posts in same window
    for (date_key, window_hour), posts in window_occupancy.items():
        if len(posts) > 1:
            issues['multiple_in_window'].append({
                'date': date_key,
                'window_hour': window_hour,
                'count': len(posts),
                'posts': posts
            })

            posts_str = ', '.join([f"{p['record_id']} ({p['title']})" for p in posts])
            logger.error(f"✗ Multiple posts in {date_key} at {window_hour}:00 window: {posts_str}")

    # Summary
    logger.info(f"\nDETECTION SUMMARY:")
    logger.info(f"  - Total records: {len(records)}")
    logger.info(f"  - Scheduled posts: {sum(len(p) for p in window_occupancy.values())}")
    logger.info(f"  - Multiple in window: {len(issues['multiple_in_window'])}")
    logger.info(f"  - Scheduled in past: {len(issues['scheduled_in_past'])}")
    logger.info(f"  - Invalid times: {len(issues['invalid_times'])}")

    return issues


# ============== Correction Logic ==============

def correct_window_conflicts(issues: Dict) -> List[Dict]:
    """
    Correct cases where multiple posts are scheduled for the same window.
    Redistributes posts to available windows on that day or subsequent days.

    Returns list of corrections applied.
    """
    corrections = []

    if not issues['multiple_in_window']:
        logger.info("\nNo window conflicts to correct.")
        return corrections

    logger.info(f"\n{'='*70}")
    logger.info("CORRECTING WINDOW CONFLICTS")
    logger.info(f"{'='*70}\n")

    now = datetime.now(TZ)

    for conflict in issues['multiple_in_window']:
        date_key = conflict['date']
        window_hour = conflict['window_hour']
        posts = conflict['posts']

        logger.info(f"\nConflict: {date_key} at {window_hour}:00 - {len(posts)} posts")

        # Parse the date
        conflict_date = datetime.strptime(date_key, '%Y-%m-%d').replace(tzinfo=TZ)

        # Get all posts on that date to see what windows are used
        day_windows_used = set()

        for record in issues['all_records']:
            fields = record.get('fields', {})
            if fields.get('Status') == 'Scheduled':
                scheduled_str = fields.get('Scheduled Time')
                if scheduled_str:
                    scheduled_dt, is_valid = parse_scheduled_time(scheduled_str)
                    if is_valid and scheduled_dt.strftime('%Y-%m-%d') == date_key:
                        w = determine_posting_window(scheduled_dt)
                        if w:
                            day_windows_used.add(w)

        logger.info(f"  Windows already used on {date_key}: {sorted(day_windows_used)}")

        # Find available windows on the same day
        available_windows = [w for w in POSTING_WINDOWS if w not in day_windows_used]

        logger.info(f"  Available windows on {date_key}: {available_windows}")

        # Reassign posts
        kept_in_original = posts[0]  # Keep first post in original window
        posts_to_reassign = posts[1:]  # Reassign the rest

        logger.info(f"  ✓ Keeping {kept_in_original['record_id']} in {window_hour}:00 window")

        for post_idx, post in enumerate(posts_to_reassign):
            if available_windows:
                # Assign to next available window on same day
                new_window = available_windows.pop(0)
                new_scheduled_dt = conflict_date.replace(hour=new_window, minute=0, second=0, microsecond=0)
                offset_minutes = random.randint(-15, 15)
                new_scheduled_dt = new_scheduled_dt + timedelta(minutes=offset_minutes)

                update_result = update_record(post['record_id'], {
                    'Scheduled Time': new_scheduled_dt.isoformat()
                })

                if update_result:
                    corrections.append({
                        'record_id': post['record_id'],
                        'title': post['title'],
                        'old_time': post['scheduled_time'],
                        'new_time': new_scheduled_dt.isoformat(),
                        'reason': f'Redistributed from {window_hour}:00 to {new_window}:00 window on {date_key}'
                    })
                    logger.info(f"  ✓ Reassigned {post['record_id']} to {new_window}:00 window ({offset_minutes:+d} min offset)")
            else:
                # No available windows on same day - move to next day
                next_day = conflict_date + timedelta(days=1)
                new_window = 9  # Start with 9 AM on next day
                new_scheduled_dt = next_day.replace(hour=new_window, minute=0, second=0, microsecond=0)
                offset_minutes = random.randint(-15, 15)
                new_scheduled_dt = new_scheduled_dt + timedelta(minutes=offset_minutes)

                update_result = update_record(post['record_id'], {
                    'Scheduled Time': new_scheduled_dt.isoformat()
                })

                if update_result:
                    corrections.append({
                        'record_id': post['record_id'],
                        'title': post['title'],
                        'old_time': post['scheduled_time'],
                        'new_time': new_scheduled_dt.isoformat(),
                        'reason': f'Moved to next day ({next_day.strftime("%Y-%m-%d")}) at {new_window}:00 - no available windows on {date_key}'
                    })
                    logger.info(f"  ✓ Moved {post['record_id']} to {next_day.strftime('%Y-%m-%d')} at {new_window}:00 (no available slots on {date_key})")

    return corrections


def correct_past_scheduled(issues: Dict) -> List[Dict]:
    """
    Correct posts scheduled in the past.
    Reschedules them to the nearest future available window.
    """
    corrections = []

    if not issues['scheduled_in_past']:
        logger.info("\nNo past-scheduled posts to correct.")
        return corrections

    logger.info(f"\n{'='*70}")
    logger.info("CORRECTING PAST-SCHEDULED POSTS")
    logger.info(f"{'='*70}\n")

    now = datetime.now(TZ)

    for past_post in issues['scheduled_in_past']:
        record_id = past_post['record_id']
        title = past_post['title']
        hours_past = past_post['hours_past']

        logger.info(f"\nPost {record_id}: Scheduled {hours_past:.1f} hours in past")

        # Find next available window
        for days_ahead in range(0, 7):  # Check next 7 days
            check_date = (now + timedelta(days=days_ahead)).replace(hour=0, minute=0, second=0, microsecond=0)
            date_key = check_date.strftime('%Y-%m-%d')

            # Get windows used on this date
            used_windows = set()
            for record in issues['all_records']:
                fields = record.get('fields', {})
                if fields.get('Status') == 'Scheduled' and record.get('id') != record_id:
                    scheduled_str = fields.get('Scheduled Time')
                    if scheduled_str:
                        scheduled_dt, is_valid = parse_scheduled_time(scheduled_str)
                        if is_valid and scheduled_dt.strftime('%Y-%m-%d') == date_key:
                            w = determine_posting_window(scheduled_dt)
                            if w:
                                used_windows.add(w)

            available = [w for w in POSTING_WINDOWS if w not in used_windows]

            if available:
                new_window = available[0]
                new_scheduled_dt = check_date.replace(hour=new_window, minute=0, second=0, microsecond=0)
                offset_minutes = random.randint(-15, 15)
                new_scheduled_dt = new_scheduled_dt + timedelta(minutes=offset_minutes)

                update_result = update_record(record_id, {
                    'Scheduled Time': new_scheduled_dt.isoformat()
                })

                if update_result:
                    corrections.append({
                        'record_id': record_id,
                        'title': title,
                        'old_time': past_post['scheduled_time'],
                        'new_time': new_scheduled_dt.isoformat(),
                        'reason': f'Rescheduled from past to {new_scheduled_dt.strftime("%Y-%m-%d at %I:%M %p %Z")}'
                    })
                    logger.info(f"  ✓ Rescheduled to {date_key} at {new_window}:00 ({offset_minutes:+d} min offset)")

                break

    return corrections


def correct_invalid_times(issues: Dict) -> List[Dict]:
    """
    Attempt to fix posts with invalid scheduled times.
    For posts with clear patterns, auto-correct. Otherwise, reset to Draft.
    """
    corrections = []

    if not issues['invalid_times']:
        logger.info("\nNo invalid times to correct.")
        return corrections

    logger.info(f"\n{'='*70}")
    logger.info("CORRECTING INVALID TIMES")
    logger.info(f"{'='*70}\n")

    for invalid_post in issues['invalid_times']:
        record_id = invalid_post['record_id']
        title = invalid_post['title']
        bad_time = invalid_post['scheduled_time_str']

        logger.info(f"\nInvalid time in {record_id}: {bad_time}")

        # Try to parse with alternative formats
        alternative_formats = [
            '%Y-%m-%d %H:%M:%S',
            '%m/%d/%Y %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
        ]

        parsed_dt = None
        for fmt in alternative_formats:
            try:
                naive_dt = datetime.strptime(bad_time.split('+')[0], fmt)
                parsed_dt = TZ.localize(naive_dt)
                break
            except:
                continue

        if parsed_dt:
            # Successfully parsed with alternative format
            now = datetime.now(TZ)

            if parsed_dt < now:
                # Already in past - reset to Draft (don't clear the date field yet)
                update_result = update_record(record_id, {
                    'Status': 'Draft'
                })

                if update_result:
                    corrections.append({
                        'record_id': record_id,
                        'title': title,
                        'action': 'Reset to Draft',
                        'reason': 'Invalid time format was in the past - reset for re-scheduling'
                    })
                    logger.info(f"  ✓ Reset to Draft (parsed time was in past)")
            else:
                # Valid future time - update with properly formatted ISO
                update_result = update_record(record_id, {
                    'Scheduled Time': parsed_dt.isoformat()
                })

                if update_result:
                    corrections.append({
                        'record_id': record_id,
                        'title': title,
                        'old_format': bad_time,
                        'new_time': parsed_dt.isoformat(),
                        'reason': 'Fixed date format'
                    })
                    logger.info(f"  ✓ Fixed format: {parsed_dt.isoformat()}")
        else:
            # Can't parse - reset to Draft for manual review
            update_result = update_record(record_id, {
                'Status': 'Draft'
            })

            if update_result:
                corrections.append({
                    'record_id': record_id,
                    'title': title,
                    'action': 'Reset to Draft',
                    'reason': f'Could not parse time format: {bad_time}'
                })
                logger.info(f"  ✓ Reset to Draft (unparseable format)")

    return corrections


# ============== Main Execution ==============

def main():
    """Run detection and correction"""
    logger.info("\n" + "="*70)
    logger.info("LINKEDIN SCHEDULING ISSUE DETECTION & CORRECTION SYSTEM")
    logger.info("="*70 + "\n")

    # Step 1: Detect issues
    issues = detect_issues()

    total_issues = (
        len(issues['multiple_in_window']) +
        len(issues['scheduled_in_past']) +
        len(issues['invalid_times'])
    )

    if total_issues == 0:
        logger.info("\n✓ NO ISSUES DETECTED - Scheduling system is healthy!\n")
        return {
            'status': 'healthy',
            'issues_found': 0,
            'corrections_applied': 0
        }

    logger.info(f"\n⚠ FOUND {total_issues} ISSUES - Beginning corrections...\n")

    # Step 2: Apply corrections
    all_corrections = []

    all_corrections.extend(correct_window_conflicts(issues))
    all_corrections.extend(correct_past_scheduled(issues))
    all_corrections.extend(correct_invalid_times(issues))

    # Step 3: Summary
    logger.info(f"\n{'='*70}")
    logger.info("CORRECTION SUMMARY")
    logger.info(f"{'='*70}\n")

    logger.info(f"Issues detected: {total_issues}")
    logger.info(f"Corrections applied: {len(all_corrections)}\n")

    for correction in all_corrections:
        logger.info(f"  • {correction['record_id']}: {correction.get('reason', correction.get('action', 'Updated'))}")

    logger.info(f"\n{'='*70}\n")

    return {
        'status': 'corrected',
        'issues_found': total_issues,
        'corrections_applied': len(all_corrections),
        'corrections': all_corrections
    }


if __name__ == '__main__':
    result = main()
    print(f"\n\nFINAL STATUS: {result['status'].upper()}")
    print(f"Issues found: {result['issues_found']}")
    print(f"Corrections applied: {result['corrections_applied']}")
