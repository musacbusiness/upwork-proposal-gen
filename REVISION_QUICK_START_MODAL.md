# Content Revision - Quick Start (Modal Edition)

**Status:** ✅ Live and ready
**Last Updated:** December 30, 2025

---

## 1. One-Time Setup (5 minutes)

### Update Airtable Button

1. Open your LinkedIn automation table in Airtable
2. Click the "Revise" button field
3. Edit the button configuration
4. Replace the URL formula with:

```
CONCATENATE("https://musacbusiness--linkedin-automation.modal.run/revise?record_id=", RECORD_ID())
```

5. Save
6. Done! ✓

---

## 2. How to Revise a Post

### In 3 Steps:

**Step 1:** Find a post you want to revise in Airtable

**Step 2:** Add text to the **Revision Prompt** field
- Example: "Make this shorter"
- Example: "More casual tone"
- Example: "New image"

**Step 3:** Click the **Revise** button

**Wait 30-60 seconds** → Content updates automatically ✓

---

## 3. What You Can Ask For

### Post Changes
- "Make this shorter"
- "More casual tone"
- "Add an example"
- "Focus on ROI"
- "Simplify language"

### Image Changes
- "New image"
- "Different visual"
- "More dramatic photo"
- "Show people collaborating"

### Both Post & Image
- "Rewrite shorter with new image"
- "Change tone and update visual"

---

## 4. What Happens Behind the Scenes

```
Click Revise Button
    ↓
Modal webhook receives request
    ↓
Calls ContentRevisionProcessor
    ↓
Claude regenerates content (based on your feedback)
    ↓
Updates Airtable
    ↓
Revision Prompt field cleared
    ↓
Done! (~30-60 seconds)
```

---

## 5. Monitor Progress

### View Real-Time Logs
- **URL:** https://modal.com/apps/musacbusiness/main/deployed/linkedin-automation
- **Click:** `revise_webhook` for on-demand revisions
- **Look for:** "Starting revision for record..." message

### What You'll See
- ✓ "Revision completed for record..." = Success
- ✗ "Error revising post: ..." = Something went wrong

---

## 6. Automatic Background Checks

The system also checks for pending revisions **automatically every 15 minutes**.

- No Airtable button click needed
- Just add Revision Prompt and wait
- System finds it on the next automatic run

**To view automatic check logs:**
- https://modal.com/apps/musacbusiness/main/deployed/linkedin-automation
- Click `check_pending_revisions_scheduled`

---

## 7. Troubleshooting

### Issue: Button doesn't work
**Solution:**
1. Check URL formula is correct in Airtable
2. Check Modal logs for errors
3. Refresh Airtable page

### Issue: Revision not happening
**Solution:**
1. Is Revision Prompt field filled?
2. Is post Status "Draft"? (won't revise "Posted")
3. Check logs - maybe it's running
4. Wait until next 15-minute automatic check runs

### Issue: Want old system back?
**Solution:**
1. Revert Airtable button URL to: `CONCATENATE("http://localhost:5050/revise/", RECORD_ID())`
2. Start local server: `python3 linkedin_automation/execution/webhook_revise.py`
3. Done

---

## 8. Key Differences from Old System

### OLD (Local)
- ❌ Had to run webhook server: `python3 webhook_revise.py`
- ❌ Mac had to stay online
- ❌ Manual terminal startup
- ❌ Limited logging
- ❌ Called `localhost:5050`

### NEW (Modal)
- ✓ No server to run
- ✓ Works 24/7 (Mac can be offline)
- ✓ Automatic setup
- ✓ Full logging in dashboard
- ✓ Calls Modal cloud: `modal.run`

---

## 9. Cost

**FREE** - Within Modal's generous free tier

No additional cost for revisions.

---

## 10. That's It!

```
Revision Prompt → Click Button → ~30 seconds → Updated Content
```

---

## Need More Details?

- **Full Migration Report:** `MODAL_REVISION_MIGRATION_COMPLETE.md`
- **Setup Instructions:** `MIGRATION_INSTRUCTIONS.md`
- **System Architecture:** `CONTENT_REVISION_SYSTEM.md`
- **Modal Dashboard:** https://modal.com/apps/musacbusiness/main/deployed/linkedin-automation

---

**Status:** ✅ Ready to use
**No Setup Needed:** Just update Airtable button URL

Done!
