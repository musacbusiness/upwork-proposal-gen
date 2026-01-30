# Modal Migration Guide - LinkedIn Automation

Complete migration from local cron to Modal serverless deployment.

---

## Overview of Changes

### Before (Local)
- Flask webhook server running on `localhost:5050`
- Manual button clicks to trigger revisions
- Local cron job for daily generation
- Manual scheduling with terminal commands

### After (Modal)
- Serverless webhooks on Modal infrastructure
- Airtable Automations trigger actions automatically
- Modal cron jobs for daily generation and scheduling
- Automatic post scheduling when status changes
- Automatic deletion scheduling (7 days for Posted, 24 hours for Rejected)

---

## New Workflow

```
┌─────────────────────────────────────────────────────────┐
│                 USER ACTIONS IN AIRTABLE                │
└─────────────────────────────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
    Draft               Pending            Approved
  (Auto-created)      Review             - Ready to
    by Modal           (You click)        Schedule
      cron                               (You click)
         │                 │                 │
         │                 │                 │
    [No action]      Airtable            Airtable
                   Automation #1       Automation #2
                         │                 │
                         ▼                 ▼
                   POST to Modal      POST to Modal
                   /webhook/             /webhook/
                  status-change       status-change
                         │                 │
                         ▼                 ▼
                   Modal Function:   Modal Function:
                Generate Images    Auto-Schedule Post
                         │                 │
                         │                 │
                   Update Airtable   Update Airtable
                   + Image URL       + Scheduled Time
                         │                 │
                         │                 ▼
                         │           Status: Scheduled
                         │                 │
                         │                 ▼
                         │           Modal Cron Job
                         │         (Every 4 hours)
                         │           Check for Posts
                         │           Ready to Post
                         │                 │
                         │                 ▼
                         │           Modal Function:
                         │         Post to LinkedIn
                         │           (Selenium)
                         │                 │
                         │                 ▼
                         │           Update Airtable
                         │           Status: Posted
                         │           + Deletion Date
                         │                 │
                         └──────────────────┘
                                 │
                              [If Rejected]
                                 │
                      Airtable Automation #3
                                 │
                                 ▼
                            POST to Modal
                          /webhook/status-change
                                 │
                                 ▼
                          Modal Function:
                      Handle Rejected Post
                                 │
                                 ▼
                          Update Airtable
                      Scheduled Deletion (24h)
                                 │
                                 ▼
                          Modal Cron Job
                         (Every hour)
                       Check Deletions
                                 │
                                 ▼
                          Delete Records
                         Due for Deletion
```

---

## Step 1: Update Airtable Schema

Add these fields to your **Posts** table:

### New Status Values
Change the "Status" field to include:
- `Draft` (auto-created by Modal cron)
- `Pending Review` (you select this to trigger image generation)
- `Approved - Ready to Schedule` (you select this to trigger scheduling)
- `Scheduled` (auto-set by Modal when scheduling)
- `Posted` (auto-set by Modal when posting)
- `Rejected` (you select this to schedule deletion)

### New Fields to Add
- **Image Generated At** (Date/Time) - When images were generated
- **Scheduled Time** (Date/Time) - When the post will be posted
- **Scheduled At** (Date/Time) - When scheduling was done
- **Posted At** (Date/Time) - When the post went live
- **Scheduled Deletion Date** (Date/Time) - When to delete this record
- **Rejected At** (Date/Time) - When the post was rejected

---

## Step 2: Deploy Modal App

### Prerequisites
```bash
# Install Modal CLI
pip install modal

# Authenticate with Modal
modal token new
```

### Deploy
```bash
cd /Users/musacomma/Agentic\ Workflow/cloud

# Deploy the LinkedIn automation
modal deploy modal_linkedin_automation.py

# You'll see a Modal app URL, save it (something like https://xxx--linkedin-automation.modal.run)
```

### Test Locally (Optional)
```bash
# Test without deploying
modal serve modal_linkedin_automation.py

# This gives you a local URL to test webhooks
```

---

## Step 3: Set Up Modal Secrets

Store your API keys in Modal:

```bash
modal secret create linkedin-secrets \
  AIRTABLE_API_KEY=patXXXXXXXXXXXXXX \
  AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX \
  AIRTABLE_LINKEDIN_TABLE_ID=tblXXXXXXXXXXXXXX \
  ANTHROPIC_API_KEY=sk-ant-xxx \
  REPLICATE_API_TOKEN=r8_XXXXXXXXX \
  LINKEDIN_EMAIL=your_email@gmail.com \
  LINKEDIN_PASSWORD=your_password
```

Or manually in Modal dashboard:
1. Go to https://modal.com/secrets
2. Create secret named `linkedin-secrets`
3. Add all the environment variables above

---

## Step 4: Set Up Airtable Automations

Airtable Automations are **100% free on the free tier**. Here's how to set them up:

### Automation #1: Draft → Pending Review → Trigger Image Generation

1. **In Airtable, go to Automations** (sidebar)
2. **Click "Create Automation"**
3. **Set up trigger:**
   - Select: "When record matches conditions"
   - Field: `Status`
   - Condition: `is` `Pending Review`

4. **Add action:**
   - Select: "Webhook"
   - Method: POST
   - URL: `https://your-modal-url.modal.run/webhook/status-change`
   - Body (JSON):
     ```json
     {
       "record_id": "{record_id}",
       "status": "Pending Review",
       "base_id": "{base_id}",
       "table_id": "{table_id}"
     }
     ```

5. **Name it:** "Generate Images When Pending Review"
6. **Turn ON**

### Automation #2: Approved → Trigger Scheduling

1. **Click "Create Automation"**
2. **Set up trigger:**
   - Select: "When record matches conditions"
   - Field: `Status`
   - Condition: `is` `Approved - Ready to Schedule`

3. **Add action:**
   - Select: "Webhook"
   - Method: POST
   - URL: `https://your-modal-url.modal.run/webhook/status-change`
   - Body (JSON):
     ```json
     {
       "record_id": "{record_id}",
       "status": "Approved - Ready to Schedule",
       "base_id": "{base_id}",
       "table_id": "{table_id}"
     }
     ```

4. **Name it:** "Schedule Post When Approved"
5. **Turn ON**

### Automation #3: Rejected → Trigger Deletion Scheduling

1. **Click "Create Automation"**
2. **Set up trigger:**
   - Select: "When record matches conditions"
   - Field: `Status`
   - Condition: `is` `Rejected`

3. **Add action:**
   - Select: "Webhook"
   - Method: POST
   - URL: `https://your-modal-url.modal.run/webhook/status-change`
   - Body (JSON):
     ```json
     {
       "record_id": "{record_id}",
       "status": "Rejected",
       "base_id": "{base_id}",
       "table_id": "{table_id}"
     }
     ```

4. **Name it:** "Schedule Deletion When Rejected"
5. **Turn ON**

---

## Step 5: Update Modal App with Real Airtable Table ID

Get your table ID from Airtable:

1. Open Airtable and find your Posts table
2. Click **Share** button → **Copy a link to this table**
3. The URL will be: `airtable.com/appXXXXX/tblYYYYY/...`
4. Copy the `tblYYYYY` part (that's your table ID)

Update your Modal secret:
```bash
modal secret update linkedin-secrets \
  AIRTABLE_LINKEDIN_TABLE_ID=tblYYYYY
```

---

## Step 6: Test the Workflow

### Test Image Generation
1. Create a new post in Airtable (Draft status)
2. Change status to `Pending Review`
3. Check Modal logs: `modal logs modal_linkedin_automation`
4. Image URL should appear in Airtable (takes 30-60 seconds)

### Test Scheduling
1. Ensure the post has an image
2. Change status to `Approved - Ready to Schedule`
3. Check Modal logs
4. Within seconds, "Scheduled Time" field should be populated
5. Status should change to `Scheduled`

### Test Deletion Scheduling
1. Change any post's status to `Rejected`
2. Check Modal logs
3. The `Scheduled Deletion Date` field should show 24 hours from now

---

## Step 7: Monitor and Debug

### View Modal Logs
```bash
# Real-time logs
modal logs --app linkedin-automation

# Specific function
modal logs --app linkedin-automation generate_images_for_post
```

### Check Webhook Failures
1. In Airtable, click Automations
2. Click on an automation
3. Check recent runs - see which ones failed
4. Click on a failed run to see the error

### Common Issues

**Issue: Webhook returns 404**
- The Modal URL is wrong
- Check that you deployed the app: `modal deploy cloud/modal_linkedin_automation.py`
- Copy the correct URL from deployment output

**Issue: "AIRTABLE_API_KEY not configured"**
- Secret not created or wrong name
- Verify: `modal secret list`
- Recreate with: `modal secret create linkedin-secrets ...`

**Issue: Image generation times out**
- Replicate API might be slow
- Timeout is set to 5 minutes - should be enough
- Check Replicate balance/quota

**Issue: Automation doesn't trigger**
- Make sure status change is "is" not "changes to"
- Webhook URL has no trailing slash
- Try testing the webhook manually with curl

---

## Step 8: Daily Content Generation (Optional)

The Modal app includes a cron job that runs daily at 6 AM UTC to generate new posts.

To customize:
1. Edit `cloud/modal_linkedin_automation.py`
2. Find the `generate_daily_content()` function
3. Implement the content generation logic (copy from local version)
4. Redeploy: `modal deploy cloud/modal_linkedin_automation.py`

---

## Step 9: Cleanup - Remove Local Webhook Server

Once Modal is working:

```bash
# No longer needed - remove or stop
rm linkedin_automation/execution/webhook_revise.py
rm linkedin_automation/execution/webhook_revise_automation.py

# Also remove from any cron jobs
crontab -e  # Remove the webhook server startup line
```

---

## Architecture Summary

| Component | Old (Local) | New (Modal) |
|-----------|------------|-----------|
| Webhook Server | Flask on localhost:5050 | Modal web endpoint |
| Image Generation | Local or Replicate | Modal function + Replicate |
| Scheduling | Manual terminal commands | Modal function (auto) |
| Posting | Local Selenium | Modal function (Selenium container) |
| Daily Generation | Cron job on Mac | Modal cron job |
| Post Deletion | Manual | Modal cron job (auto) |
| Cost | $0 (local compute) | ~$1-5/month (Modal) |
| Uptime | Dependent on your Mac | 99.9% SLA |
| Scalability | Limited to local | Unlimited |

---

## Next Steps

1. ✅ Deploy Modal app
2. ✅ Create Modal secrets
3. ✅ Update Airtable schema
4. ✅ Set up 3 Airtable Automations
5. ✅ Test each workflow
6. ✅ Update daily generation function
7. ✅ Implement LinkedIn posting (Selenium)
8. ✅ Monitor for 7 days before removing local setup

---

## Support

If you encounter issues:
1. Check Modal logs: `modal logs --app linkedin-automation`
2. Check Airtable Automation run history
3. Verify secrets: `modal secret list`
4. Test webhook URL manually with curl
5. Check Replicate API balance
6. Verify LinkedIn credentials are current

---

**Status:** Ready for deployment
**Last Updated:** December 2025
