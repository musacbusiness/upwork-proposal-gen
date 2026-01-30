# Scheduling System - Monitoring Quick Reference

**Purpose:** How to monitor the scheduling detection & correction system

---

## Daily Monitoring

### Check Modal Logs
```
https://modal.com/apps/musacbusiness/main/deployed/linkedin-automation
→ Click on "check_and_fix_scheduling_issues" function
→ View logs for recent executions
```

**What to look for:**
```
✓ "No scheduling issues detected" - Everything healthy
✓ "Issues found: 0" - Clean system
⚠ "Window conflict detected" - System caught and fixed an issue
✗ "Failed to update" - Issue detected but not auto-fixed (manual review needed)
```

---

## Run Manual Check Anytime

```bash
cd "/Users/musacomma/Agentic Workflow"
python3 execution/detect_and_fix_scheduling_issues.py
```

**Output meanings:**
```
Issues detected: 0
Corrections applied: 0
→ System is healthy ✓

Issues detected: 1
Corrections applied: 2
→ System caught and fixed a conflict ✓

Issues detected: 3
Corrections applied: 1
→ Some issues fixed, some need manual review ⚠
```

---

## What Healthy Looks Like

### In Airtable
```
Post 1: Status = Scheduled, Time = 2025-12-31T09:15:00-05:00
Post 2: Status = Scheduled, Time = 2025-12-31T14:30:00-05:00
Post 3: Status = Scheduled, Time = 2025-12-31T20:45:00-05:00
        ↑ Each in different window ✓
```

### In Modal Logs
```
2025-12-30 12:00:00 - INFO - Checking for scheduling issues...
2025-12-30 12:00:01 - INFO - No scheduling issues detected
2025-12-30 12:00:01 - DEBUG - No changes detected. Tracking 3 records.
```

---

## What Unhealthy Looks Like

### In Airtable
```
Post 1: Status = Scheduled, Time = 2025-12-31T09:15:00-05:00
Post 2: Status = Scheduled, Time = 2025-12-31T09:30:00-05:00  ← SAME WINDOW
Post 3: Status = Scheduled, Time = 2025-12-31T09:45:00-05:00  ← SAME WINDOW
```

### In Modal Logs (Before Fix)
```
⚠ Window conflict on 2025-12-31 at 9:00 - 3 posts
```

### In Modal Logs (After Auto-Fix)
```
✓ Moved rec... to 14:00 window
✓ Moved rec... to 20:00 window
✓ Scheduling issue detection complete: 1 conflicts, 2 fixed
```

---

## Common Scenarios

### Scenario 1: Multiple Posts Approved at Once
```
You approve 3 posts within 10 seconds
↓
All might schedule for same window initially
↓
Auto-detection catches this
↓
Redistributes to 9/2/8 PM
↓
You don't see the issue (system fixed it)
✓ Expected behavior
```

### Scenario 2: Airtable Time Edited Manually
```
You manually change Scheduled Time to malformed format
↓
Detection catches it on next check
↓
Script tries to parse with multiple formats
↓
If parseable: Updates with correct format
↓
If not: Resets to Draft for you to re-approve
✓ Expected behavior
```

### Scenario 3: Scheduled Post in Past
```
System is down for 6 hours
You come back and see a post scheduled for 8 hours ago
↓
Detection catches "scheduled_in_past"
↓
Reschedules to next available window
↓
You get log notification
✓ Expected behavior
```

---

## Troubleshooting

### "Issues detected: 3, Corrections applied: 0"
**Problem:** Detection found issues but couldn't fix them
**Action:** Check Airtable API logs, may need manual intervention
**Check:**
```bash
# Verify Airtable connectivity
curl -H "Authorization: Bearer $AIRTABLE_API_KEY" \
  https://api.airtable.com/v0/meta/bases
```

### "Error in scheduling issue detection"
**Problem:** Script crashed unexpectedly
**Action:** Check error message in logs
**Common causes:**
- Invalid environment variables
- Airtable API down
- Network connectivity issue

**Fix:**
```bash
# Verify .env is set correctly
cat .env | grep AIRTABLE
# Should show 3 variables:
# AIRTABLE_API_KEY=...
# AIRTABLE_BASE_ID=...
# AIRTABLE_LINKEDIN_TABLE_ID=...
```

### Posts Not Being Redistributed
**Problem:** Multiple posts in same window persist
**Check:**
1. Are posts in "Scheduled" status? (only checks those)
2. Are times actually conflicting? (within 30 min of window)
3. Check API logs for update errors

**Manual Fix:**
```bash
# See which posts are problematic
python3 execution/detect_and_fix_scheduling_issues.py

# If detection finds them but doesn't fix:
# Check error messages in output
# May need to manually edit Airtable

# Then re-run to verify fix:
python3 execution/detect_and_fix_scheduling_issues.py
```

---

## Metrics to Track

**Healthy System:**
- Issues detected per week: 0-2 (rare, caught immediately)
- Corrections applied: 100% of issues detected
- False positives: 0 (confidence in detection)

**Unhealthy System:**
- Issues detected increasing over time
- Corrections applied < 50% of issues (API problems)
- Errors in logs frequently

---

## When to Investigate Further

```
✓ See 1 issue detected and corrected
  → Normal, system working

⚠ See 3+ issues per day
  → Check scheduling logic, may need adjustment

✗ See issues but corrections fail
  → Check Airtable API, modal logs, network

✗ See past-scheduled posts
  → System was down, manually fix oldest first
```

---

## System Health Dashboard (Manual Check)

Run this weekly:

```bash
# 1. Check total posts
curl -s -H "Authorization: Bearer $AIRTABLE_API_KEY" \
  https://api.airtable.com/v0/$AIRTABLE_BASE_ID/$AIRTABLE_LINKEDIN_TABLE_ID \
  | jq '.records | length'

# 2. Check scheduled posts
python3 execution/detect_and_fix_scheduling_issues.py

# 3. View Modal logs for last 24 hours
# → https://modal.com/apps/musacbusiness/main/deployed/linkedin-automation
```

---

## Quick Commands

### Run detection manually
```bash
cd "/Users/musacomma/Agentic Workflow"
python3 execution/detect_and_fix_scheduling_issues.py
```

### See full logs
```bash
cd "/Users/musacomma/Agentic Workflow"
python3 execution/detect_and_fix_scheduling_issues.py 2>&1 | tee detection.log
```

### Schedule with cron (every 4 hours)
```bash
# Edit crontab
crontab -e

# Add line:
0 */4 * * * cd "/Users/musacomma/Agentic Workflow" && python3 execution/detect_and_fix_scheduling_issues.py >> /tmp/scheduling_check.log 2>&1
```

### Check cron logs
```bash
tail -f /tmp/scheduling_check.log
```

---

## When Everything Works

You should see:
- Posts automatically distributed across 3 windows
- No manual fixes needed
- Modal logs showing "No issues detected"
- Clean Airtable with balanced scheduling

**System is healthy and protecting your posts! ✓**

---

## Reference

- **Directive:** `directives/scheduling_issue_detection.md`
- **Main Script:** `execution/detect_and_fix_scheduling_issues.py`
- **Modal Code:** `cloud/modal_linkedin_automation.py` lines 1416-1545
- **Summary:** `SCHEDULING_DETECTION_SYSTEM.md`
- **This Guide:** `MONITORING_QUICK_REFERENCE.md`
