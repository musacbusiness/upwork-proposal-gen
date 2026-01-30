# Airtable Automations Setup Guide

**Status: Ready to Configure**
**Last Updated: December 25, 2025**

---

## Overview

Your Airtable table is now fully configured with:
- ✅ All 6 status options (Draft, Pending Review, Approved - Ready to Schedule, Scheduled, Posted, Rejected)
- ✅ All 6 date/time fields (Image Generated At, Scheduled Time, Scheduled At, Posted At, Scheduled Deletion Date, Rejected At)

Now you can trigger the Modal workflows in two ways:

---

## Option 1: Manual Python Trigger (Recommended for Testing)

Use this command whenever you want to trigger a workflow:

```bash
# Test image generation
python3 trigger_modal_webhook.py --record-id "recXXXXXXX" --status "Pending Review"

# Test post scheduling
python3 trigger_modal_webhook.py --record-id "recXXXXXXX" --status "Approved - Ready to Schedule"

# Test rejection handling
python3 trigger_modal_webhook.py --record-id "recXXXXXXX" --status "Rejected"
```

**Replace `recXXXXXXX` with your actual record ID from Airtable.**

### How to Get Record ID:
1. Open your Airtable table
2. Right-click on any record
3. Click "Copy record ID" or see it in the URL bar

---

## Option 2: Airtable Automations (For Full Automation)

If you want Airtable status changes to automatically trigger the Modal workflows, you can set up automations. However, this is complex because Airtable Automations require HTTP endpoints, and Modal's HTTP webhooks need additional configuration.

### Setup Steps:

**Automation 1: When Status changes to "Pending Review"**

1. In Airtable, go to **Automations** (top menu)
2. Click **Create automation**
3. **Trigger:**
   - Select: "When record matches conditions"
   - Field: `Status`
   - Condition: `is`
   - Value: `Pending Review`
4. **Action:**
   - Type: "Scripting - Run script"
   - Paste this script:

```javascript
// Trigger image generation in Modal
const recordId = input.config().recordId;
const baseId = input.config().baseId;
const tableId = input.config().tableId;

console.log(`Triggering image generation for ${recordId}`);
// Note: You'll need to configure Modal webhook URL here

// For now, log the action
console.log("Status changed to: Pending Review");
console.log("Image generation should be triggered");
```

5. **Name:** "Generate Images When Pending Review"
6. Click **Turn ON** ✓

---

## Current Workflow (Without Automations)

Until you set up the Airtable Automations, here's how to use the system:

### Step 1: Create a Post in Airtable
- Title: Your post title
- Content: Your post content
- Status: Leave as **Draft**
- Image URL: Link to image (or leave blank for generation)

### Step 2: Trigger Image Generation
When you want images generated, run:
```bash
python3 trigger_modal_webhook.py --record-id "YOUR_RECORD_ID" --status "Pending Review"
```

The system will:
- Generate an image via Replicate
- Store the image URL in the "Image URL" field
- Update "Image Generated At" timestamp

### Step 3: Approve for Scheduling
When you're happy with the post, run:
```bash
python3 trigger_modal_webhook.py --record-id "YOUR_RECORD_ID" --status "Approved - Ready to Schedule"
```

The system will:
- Calculate optimal posting time (9am, 2pm, or 8pm ±15 min)
- Set "Scheduled Time" with the time
- Change Status to **Scheduled**
- Store "Scheduled At" timestamp

### Step 4: Auto-Post at Scheduled Time
At the scheduled time, the system will:
- Post to LinkedIn automatically
- Change Status to **Posted**
- Set "Posted At" timestamp
- Schedule deletion for 7 days later

### Step 5: Automatic Cleanup
After 7 days (or 24 hours if rejected):
- The record is automatically deleted from Airtable
- Cleanup job runs hourly

---

## Testing the System

### Test Everything Works

```bash
#!/bin/bash
# Test script - run these commands in order

# Get a record ID from your Airtable table and replace REC_ID below
REC_ID="recXXXXXXX"

echo "Testing workflow..."

# Test 1: Image generation
echo "✓ Triggering image generation..."
python3 trigger_modal_webhook.py --record-id "$REC_ID" --status "Pending Review"

# Wait 30-60 seconds for processing
sleep 45

# Test 2: Post scheduling
echo "✓ Triggering post scheduling..."
python3 trigger_modal_webhook.py --record-id "$REC_ID" --status "Approved - Ready to Schedule"

# Check the record in Airtable to see the updates!
echo "✓ Done! Check your Airtable record to see the updates."
```

---

## Troubleshooting

### Issue: "Function has not been hydrated"
**Solution:** Make sure you're in the correct directory and Modal is authenticated:
```bash
python3 -m modal token validate
cd /Users/musacomma/Agentic\ Workflow
```

### Issue: "Record ID not found"
**Solution:** Copy the correct record ID from Airtable:
1. Open your table in Airtable
2. Click on a record
3. The URL shows: `...?recXXXXXXX...` - that's your record ID

### Issue: "Status doesn't match"
**Solution:** Make sure you're using the exact status names:
- `Draft`
- `Pending Review` (not "pending review" or "pending_review")
- `Approved - Ready to Schedule` (with exact spacing)
- `Scheduled`
- `Posted`
- `Rejected`

---

## Advanced: Full Airtable Automations

If you want to skip the manual triggering and have Airtable automations do it automatically, you need to:

1. Create a local webhook server that listens for Airtable webhooks
2. Configure Airtable to send webhooks to your server
3. Your server calls the Modal trigger script

OR

1. Use Airtable's "Script" action to directly call Modal functions
2. Requires Complex Modal authentication in Airtable

For now, **the Python trigger method is simpler and more reliable.**

---

## Next Steps

1. **Get a test record ID** from your Airtable table
2. **Run:** `python3 trigger_modal_webhook.py --record-id "YOUR_ID" --status "Pending Review"`
3. **Check your Airtable** to see if the fields were updated
4. **Verify it works**, then expand to more posts

---

## Files Reference

| File | Purpose |
|------|---------|
| `trigger_modal_webhook.py` | Manually trigger Modal functions |
| `AIRTABLE_AUTOMATIONS_SETUP.md` | This guide |
| `DEPLOYMENT_COMPLETE.md` | Full deployment overview |

---

## Timeline

- **First test:** 5 minutes (run trigger command)
- **Full testing:** 15 minutes (test all 3 workflows)
- **Production ready:** After successful testing

---

**Ready to test? Start with:**
```bash
python3 trigger_modal_webhook.py --record-id "YOUR_RECORD_ID" --status "Pending Review"
```

Let me know if you hit any issues! 🚀
