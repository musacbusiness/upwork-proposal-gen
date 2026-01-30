# Scheduling Issue Detection & Correction Directive

**Objective:** Automatically detect and correct scheduling mistakes in the LinkedIn automation system.

**Last Updated:** December 30, 2025
**Status:** ✓ Active and Integrated

---

## What This Does

The detection and correction system monitors Airtable records for scheduling issues and automatically fixes them:

1. **Detects Multiple Posts in Same Window**
   - Identifies when 2+ posts are scheduled for the same posting window on the same day
   - Example: All 3 posts scheduled for 9:00 AM on Dec 30 (the bug we just fixed)

2. **Detects Posts Scheduled in the Past**
   - Finds posts with scheduled times that have already passed
   - Example: Post scheduled for 2 PM yesterday, but it's now 8 PM today

3. **Detects Invalid Scheduled Times**
   - Identifies posts with unparseable or malformed scheduled times
   - Handles multiple date formats (ISO, UTC Z format, alternative formats)

4. **Auto-Corrects Issues**
   - Redistributes posts to available windows on the same day
   - Moves posts to future days if needed
   - Resets posts to "Draft" status if they can't be fixed automatically

---

## Key Concepts

### Posting Windows
- **9 AM ET** (±15 minutes) - First window
- **2 PM ET** (±15 minutes) - Second window
- **8 PM ET** (±15 minutes) - Third window

Posts within 30 minutes of a window time are considered part of that window.

### Distribution Algorithm
1. Find posts scheduled for same window/date
2. Keep first post in original window
3. Reassign others to available windows on same day
4. If no slots on same day, move to next available day
5. If next day full, try day-after-tomorrow

### Detection Rules
- A window is "used" if ANY post is scheduled within 30 minutes of that hour
- Multiple posts = issue (should be 1 per window per day)
- Past scheduled time = issue (should reschedule to future)
- Unparseable time = issue (reset to Draft for manual review)

---

## How to Run

### Manual Execution
```bash
cd "/Users/musacomma/Agentic Workflow"
python3 execution/detect_and_fix_scheduling_issues.py
```

### Automated (Modal)
The system runs automatically:
- **Every 4 hours** via cron task in Modal
- **On-demand** via webhook when posts are scheduled

### Schedule Check
Check `/Users/musacomma/Agentic Workflow/cloud/modal_linkedin_automation.py` for:
- Line ~700: `@app.scheduled` decorator for periodic checks
- Function: `auto_schedule_and_post_scheduler()`

---

## Script Location & Structure

**Main Script:** `execution/detect_and_fix_scheduling_issues.py`

### Core Functions

**Detection Functions:**
- `fetch_all_records()` - Get all posts from Airtable
- `detect_issues()` - Scan for all 3 issue types, returns categorized results
- `parse_scheduled_time()` - Parse multiple date formats (ISO, UTC Z, alternatives)
- `determine_posting_window()` - Identify which window a post belongs to

**Correction Functions:**
- `correct_window_conflicts()` - Fix multiple posts in same window
- `correct_past_scheduled()` - Reschedule posts in the past
- `correct_invalid_times()` - Fix or reset unparseable times

**Utilities:**
- `get_headers()` - Airtable API auth headers
- `update_record()` - Update single record with retry logic
- `main()` - Orchestrate detection and correction, return summary

---

## Detection Examples

### Example 1: Window Conflict
```
DETECTED:
✗ Multiple posts in 2025-12-30 at 9:00 window:
  - rec6Bh4hUVslhhE8J (Why specificity matters...)
  - recERjcFKzukvmYWk (How automation is transforming...)
  - recdpAVxLCOglOciz (How real estate agents...)

CORRECTION:
✓ Keeping rec6Bh4hUVslhhE8J in 9:00 window
✓ Reassigned recERjcFKzukvmYWk to 14:00 window
✓ Reassigned recdpAVxLCOglOciz to 20:00 window
```

### Example 2: Past Scheduled
```
DETECTED:
⚠ Post scheduled in past (3.2 hours ago):
  - recXXXXXXXXXXXXXX (Title...)

CORRECTION:
✓ Rescheduled to 2025-12-31 at 09:15 AM
```

### Example 3: Invalid Time Format
```
DETECTED:
✗ Invalid time format: "12/30/2025 2:30pm"

CORRECTION:
✓ Fixed to ISO format: 2025-12-30T14:30:00-05:00
OR
✓ Reset to Draft (if unparseable)
```

---

## Integration with Modal

The system is integrated into Modal in two ways:

### 1. Periodic Scheduled Check (Every 4 Hours)
```python
@app.scheduled(schedule=modal.Period(hours=4))
def auto_schedule_and_post_scheduler():
    # ... posts scheduled posts to LinkedIn ...
    # ... at end, calls detect_and_fix_scheduling_issues ...
```

### 2. On-Demand via Webhook
When posts are approved and scheduled, the Modal scheduling function runs detection to catch issues immediately.

---

## Logging & Monitoring

All corrections are logged with:
- Record ID being corrected
- Original value
- New value
- Reason for change

Example log output:
```
2025-12-30 00:07:13,879 - INFO - ✓ Updated record recERjcFKzukvmYWk: {"Scheduled Time": "2025-12-30T14:15:00-04:56"}
2025-12-30 00:07:14,333 - INFO - Redistributed from 9:00 to 14:00 window on 2025-12-30
```

---

## Airtable Fields Used

- **Scheduled Time** (Date field) - When post should be published
- **Status** (Select field) - Post status (Draft, Scheduled, Posted, etc.)
- **Title** (Text field) - Used for logging and identification

---

## Error Handling

### API Errors
- If Airtable API fails to fetch records: Logs warning, skips detection round
- If API fails to update: Logs error, does not retry (manual intervention needed)

### Date Parsing Errors
- Supports multiple formats: ISO, UTC Z, common date/time formats
- Falls back to resetting to Draft if unparseable
- Logs all failures for investigation

### Edge Cases
- Posts with no scheduled time are skipped
- Posts with non-"Scheduled" status but with scheduled times are logged as warnings
- Empty windows set (all 3 windows full) falls back to day-after-tomorrow

---

## Testing & Validation

### How to Test
1. Create 3 posts in Airtable
2. Manually set all 3 to "Scheduled" status
3. Set all 3 to same Scheduled Time (e.g., tomorrow 9:15 AM)
4. Run: `python3 execution/detect_and_fix_scheduling_issues.py`
5. Verify:
   - Detection identifies 1 conflict
   - Corrections reassign to 14:00 and 20:00 windows
   - Check Airtable - times should be updated

### Expected Output
```
Issues detected: 1
Corrections applied: 2
```

---

## Maintenance & Improvements

### Known Limitations
- Manual Airtable edits (changing times directly) won't trigger correction until next 4-hour check
- Posts more than 3 days in past cannot be rescheduled (system limits)

### Future Enhancements
1. Add real-time webhook trigger (correct immediately on status change)
2. Add Slack notifications for corrections
3. Add correction history tracking in Airtable
4. Add configuration for custom window times
5. Add smarter distribution (minimize gaps, prefer earlier windows)

---

## Integration Steps (If Re-deploying)

1. **Update Modal:** Add call to detection script before posting
   ```python
   detect_and_fix_scheduling_issues()  # Call before posting
   ```

2. **Environment Variables:** Already set in Modal secrets
   - `AIRTABLE_API_KEY`
   - `AIRTABLE_BASE_ID`
   - `AIRTABLE_LINKEDIN_TABLE_ID`

3. **Install Dependencies:** Already in Modal image
   - `requests`, `pytz`, `python-dotenv`

4. **Deploy:** `modal deploy cloud/modal_linkedin_automation.py`

---

## Related Files

- **Main Script:** `execution/detect_and_fix_scheduling_issues.py`
- **Modal Integration:** `cloud/modal_linkedin_automation.py` (lines ~700, ~324-500)
- **Related Directives:**
  - `scheduling_window_logic.md` - How posting windows work
  - `airtable_record_structure.md` - Airtable field definitions

---

## Summary

**What it solves:** Automatic detection and correction of scheduling mistakes
**How it works:** Periodic scans + immediate correction + logging
**Status:** ✓ Active, integrated with Modal, tested
**Last issue fixed:** Dec 30, 2025 - All 3 posts reassigned from 9 AM to 9/2 PM/8 PM windows
