# Modal Automation Deployment Guide

## Overview

This guide walks you through deploying the daily post inventory maintenance automation to Modal (cloud-hosted, independent of your local Mac).

**What it does:**
- Runs daily at 9 AM UTC
- Maintains 21 posts in Airtable (Draft, Pending Review, Approved - Ready to Schedule, Scheduled)
- Automatically deletes posts that have been "Posted" for 7+ days
- Generates new posts if inventory falls below 21

## Prerequisites

1. **Modal Account**: Already set up ✓
2. **Modal CLI**: Should already be installed
3. **API Keys**: Airtable and Anthropic

## Deployment Steps

### Step 1: Verify Modal Installation

```bash
modal version
```

### Step 2: Create Modal Secrets

You need to create two secrets in Modal for the automation:

#### Secret 1: Airtable Credentials

```bash
modal secret create airtable-credentials \
  AIRTABLE_API_KEY=<your-airtable-api-key> \
  AIRTABLE_BASE_ID=<your-base-id> \
  AIRTABLE_LINKEDIN_TABLE_ID=<your-table-id>
```

Get these from your `.env` file:
```bash
cat /Users/musacomma/Agentic\ Workflow/.env | grep AIRTABLE
```

#### Secret 2: Anthropic Credentials

```bash
modal secret create anthropic-credentials \
  ANTHROPIC_API_KEY=<your-anthropic-api-key>
```

Get this from:
```bash
cat /Users/musacomma/Agentic\ Workflow/.env | grep ANTHROPIC_API_KEY
```

### Step 3: Deploy to Modal

```bash
cd /Users/musacomma/Agentic\ Workflow/execution
modal deploy modal_maintain_inventory.py
```

**Expected output:**
```
✓ Created app 'linkedin-post-inventory'
✓ Deployed function 'maintain_inventory' with schedule: 0 9 * * * (9 AM UTC daily)
```

### Step 4: Verify Deployment

Check that the app is running:

```bash
modal app list
modal logs linkedin-post-inventory
```

## Testing the Automation (Optional)

To test manually without waiting for 9 AM:

```bash
modal run modal_maintain_inventory.py::maintain_inventory
```

## How It Works

### Schedule
- **Frequency**: Daily
- **Time**: 9 AM UTC (approximately 4 AM EDT / 1 AM PDT)
- **Note**: Adjust timezone if needed in the code (line with `Cron("0 9 * * *)`)

### Logic

1. **Count Eligible Posts**
   - Counts posts with status: Draft, Pending Review, Approved - Ready to Schedule, Scheduled
   - Target: 21 posts

2. **Delete Old Posted Posts**
   - Finds all posts with status "Posted"
   - Deletes if Posted At date is 7+ days old
   - Runs every day regardless of inventory level

3. **Generate New Posts**
   - If eligible count < 21, generates new posts
   - Number generated = 21 - current count
   - Posts are created as "Draft" status

4. **Log Results**
   - Logs to Modal for audit trail
   - Shows initial count, deleted, generated, and final count

## Monitoring

View logs for the last run:

```bash
modal logs linkedin-post-inventory --tail 100
```

View all runs:

```bash
modal logs linkedin-post-inventory
```

## Changing the Schedule

To change the daily run time, edit line in `modal_maintain_inventory.py`:

```python
@app.function(
    schedule=modal.Cron("0 9 * * *"),  # Change 9 to desired hour (0-23, UTC)
)
```

Common times:
- `"0 9 * * *"` = 9 AM UTC (current)
- `"0 13 * * *"` = 1 PM UTC (5 AM EDT)
- `"0 14 * * *"` = 2 PM UTC (6 AM EDT)

Then redeploy:
```bash
modal deploy modal_maintain_inventory.py
```

## Changing the Target Inventory

To maintain a different number of posts, edit line in `modal_maintain_inventory.py`:

```python
TARGET_INVENTORY = 21  # Change to desired number
```

Then redeploy.

## Changing Days Before Auto-Delete

To change how long posted posts are kept, edit:

```python
DAYS_TO_KEEP_POSTED = 7  # Change to desired number
```

Then redeploy.

## Troubleshooting

### "Secret not found" error
**Solution**: Re-create the secrets:
```bash
modal secret create airtable-credentials AIRTABLE_API_KEY=<key> ...
modal secret create anthropic-credentials ANTHROPIC_API_KEY=<key>
```

### "API rate limit exceeded"
**Solution**: Modal retries automatically. If persistent, space out deployments or contact Airtable support.

### No posts being generated
**Check**:
1. Is the target inventory already at 21? `modal logs linkedin-post-inventory`
2. Are API keys valid? Run `modal run modal_maintain_inventory.py::maintain_inventory` locally
3. Is Anthropic API working? Check your API key in Modal secrets

### Posts not being deleted
**Check**:
1. Are any posts in "Posted" status?
2. Do they have "Posted At" dates set?
3. Check logs: `modal logs linkedin-post-inventory`

## Verification Checklist

After deployment:

- [ ] `modal app list` shows "linkedin-post-inventory"
- [ ] `modal logs linkedin-post-inventory` shows recent run logs
- [ ] Airtable shows 21 eligible posts (Draft, Pending Review, etc.)
- [ ] Check at 9:01 AM UTC the next day for run logs
- [ ] Verify posts are being generated (check timestamps in Airtable)

## Architecture Diagram

```
Modal Cloud Schedule (9 AM UTC)
         ↓
   maintain_inventory()
         ↓
    ┌────┴────┐
    ↓         ↓
Delete Old   Generate New
Posts (7+)   Posts (if <21)
    ↓         ↓
Airtable API ← Connection
    ↓         ↓
  Success ← Report
```

## Cost

Modal pricing:
- **Free tier**: Up to 1 GB per month (more than enough for daily runs)
- **Paid tier**: $0.50/GB/month after free tier

This automation uses negligible resources (< 1 MB per run).

## Support

For issues:
1. Check logs: `modal logs linkedin-post-inventory`
2. Test locally: `modal run modal_maintain_inventory.py::maintain_inventory`
3. Verify secrets: `modal secret list`
4. Check Modal docs: https://modal.com/docs

---

**Status**: Ready to deploy
**Created**: 2026-01-11
