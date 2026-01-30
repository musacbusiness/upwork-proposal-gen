# Scheduling Quick Reference

**Posting Windows:** 9 AM, 2 PM (14:00), 8 PM (20:00) ET

---

## How Scheduling Works (Fixed)

### Daily Window Availability
```
9 AM   → Post 1
2 PM   → Post 2
8 PM   → Post 3

(Next day - windows reset)
9 AM   → Post 4
2 PM   → Post 5
8 PM   → Post 6
```

### How to Trigger Scheduling
1. Post must be in status: **"Approved - Ready to Schedule"**
2. Polling detects status change (every 5 seconds)
3. Post automatically assigned to next available window
4. **Scheduled Time** field populates with exact time (±15 min random offset)
5. Status remains "Scheduled"

### Queue Behavior
When you approve multiple posts rapidly:
```
Approve Post 1 → automatically assigned to 9 AM
Approve Post 2 → automatically assigned to 2 PM
Approve Post 3 → automatically assigned to 8 PM
```

Each post checks the CURRENT state before assigning, so no conflicts.

---

## Workflow

### Step 1: Posts Generated (Daily 6 AM UTC)
- Status: **Draft**
- Image Prompt: Ready
- Scheduled Time: Empty

### Step 2: You Review Posts in Airtable
- Read content
- Check image prompt looks relevant
- When satisfied, proceed to Step 3

### Step 3: Request Image Generation
- Change Status: **Draft** → **"Pending Review"**
- Wait 5-10 seconds
- Image auto-generates
- Image URL populates

### Step 4: Approve for Scheduling
- Review generated image
- If happy, change Status: **"Pending Review"** → **"Approved - Ready to Schedule"**
- Wait 5 seconds
- Scheduling logic runs
- Scheduled Time populates automatically

### Step 5: Auto-Post
- At scheduled time, post auto-publishes to LinkedIn
- Status updates to: **"Posted"**
- 7-day timer starts for auto-deletion

---

## Window Assignment Logic

When you approve a post, the system checks:

1. **What posts are already scheduled today?**
   - Look at all posts with Scheduled Time for today

2. **Which windows are taken?**
   - If a post is scheduled between 8:45 AM - 9:15 AM → 9 AM window is used
   - If a post is scheduled between 1:45 PM - 2:15 PM → 2 PM window is used
   - If a post is scheduled between 7:45 PM - 8:15 PM → 8 PM window is used

3. **Assign to next available window**
   - If 9 AM used, try 2 PM
   - If 9 AM + 2 PM used, try 8 PM
   - If all used, schedule for tomorrow 9 AM

---

## Example Scenarios

### Scenario 1: Approve All 3 at Once
**Action:** Change 3 posts from Draft → Approved rapidly

**What happens:**
- 5-second polling detects all 3 changes
- Post 1 scheduled: 9:05 AM ✓
- Post 2 scheduled: 2:09 PM ✓
- Post 3 scheduled: 8:03 PM ✓

**Result:** All 3 windows utilized ✓

---

### Scenario 2: Approve 1, Then Later Approve 2 More

**Action 1 (10 AM):** Approve Post 1
- Polling detects change
- Checks current posts: none scheduled today
- Assigns Post 1 → 9 AM (but it's past 9 AM, so actually 2 PM since 9 AM is now)
- Status: Scheduled, Time: 2:07 PM

**Action 2 (11 AM):** Approve Post 2
- Polling detects change
- Checks current posts: Post 1 at 2:07 PM (2 PM window used)
- Skips 9 AM and 2 PM
- Assigns Post 2 → 8 PM
- Status: Scheduled, Time: 8:11 PM

**Action 3 (12 PM):** Approve Post 3
- Polling detects change
- Checks current posts: Post 1 at 2:07 PM (2 PM used), Post 2 at 8:11 PM (8 PM used)
- Only 9 AM available in current schedule, but it's past 9 AM
- Skips to tomorrow
- Assigns Post 3 → tomorrow 9 AM
- Status: Scheduled, Time: 9:04 AM (tomorrow)

**Result:** Posts spread across available windows, queue handled automatically ✓

---

### Scenario 3: Reject a Post, Then Approve Again

**Action 1:** Approve Post 1
- Assigned to 9 AM
- Status: Scheduled, Time: 9:03 AM

**Action 2:** Change to "Rejected"
- Scheduling canceled (not posted yet)
- Post stays in Airtable
- Can be revised later

**Action 3:** Approve same post again
- Polling detects status change from Rejected → Approved
- Checks current scheduled posts: none (9 AM is now past)
- Still no posts scheduled for today at this point
- Assigns to 2 PM (next available window after 9 AM passed)
- Status: Scheduled, Time: 2:05 PM

**Result:** Post rescheduled automatically ✓

---

## Status Transitions

```
Draft
  ↓ (you approve for image)
Pending Review
  ↓ (image generates automatically)
Pending Review (with image)
  ↓ (you approve for scheduling)
Approved - Ready to Schedule
  ↓ (scheduling runs automatically)
Scheduled
  ↓ (scheduled time arrives)
Posted
  ↓ (7 days later)
Deleted
```

---

## Key Points

✓ **Automatic window assignment** - No manual coordination needed
✓ **Queue handling** - Rapid approvals go to different windows
✓ **Day rollover** - Windows reset each day at midnight ET
✓ **No window conflicts** - System checks before assigning
✓ **Flexible timing** - Approve posts anytime, they auto-assign
✓ **Random jitter** - Each post gets ±15 min offset for natural look

---

## Testing the Fix

To verify scheduling works correctly:

1. Go to Airtable
2. Select the 3 existing posts
3. Change all from "Scheduled" back to "Draft"
4. Change all 3 to "Approved - Ready to Schedule" within 10 seconds
5. Watch Scheduled Time field populate:
   - Post 1: ~9:00 AM
   - Post 2: ~2:00 PM (14:00)
   - Post 3: ~8:00 PM (20:00)

If you see this, the fix is working! ✓

---

## Troubleshooting

**Q: All posts still scheduling for 9 AM**
A: You might have the old version. Verify:
- Modal deployment is current (check last deployment time)
- Try changing status to Draft and back to Approved
- Clear Modal cache if needed

**Q: Posts scheduling way in the future**
A: Expected if you approve all 3 after 8 PM. System reserves windows only for posts not yet passed:
- After 8 PM, all windows for today are "past"
- Next available is tomorrow 9 AM
- This is correct behavior

**Q: Scheduled Time not updating**
A: Give it 5-10 seconds after status change:
- Polling runs every 5 seconds
- Scheduling takes 2-5 seconds
- Total: ~5-15 seconds to see Scheduled Time populate

---

## Summary

✅ Posts now distribute across all 3 posting windows
✅ Queue automatically processes when approving multiple posts
✅ System intelligently assigns available windows
✅ No manual coordination needed
✅ Same logic repeats daily

Just approve posts, rest is automatic! 🎯
