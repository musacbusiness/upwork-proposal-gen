# 🚀 Go Live - Complete Step-by-Step Guide

**Your Configuration:**
- Base ID: `appw88uD6ZM0ckF8f`
- Table ID: `tbljg75KMQWDo2Hgu`

---

## Step 1: Deploy Modal App (5 minutes)

Open your terminal and run:

```bash
cd /Users/musacomma/Agentic\ Workflow/cloud
modal deploy modal_linkedin_automation.py
```

**What to expect:**
- CLI will show deployment progress
- After 2-3 minutes, you'll see: `Deployed! 🎉`
- **IMPORTANT:** Copy the URL that appears (looks like `https://xxx--linkedin-automation.modal.run`)

**Store this URL - you'll need it in Step 4**

---

## Step 2: Create Modal Secrets (3 minutes)

In the same terminal, run:

```bash
modal secret create linkedin-secrets \
  AIRTABLE_API_KEY=patQCCzbAjKw675Bf.a9220198778415662363c84105e67b9c47399f5a01e27688f18f429115574a5c \
  AIRTABLE_BASE_ID=appw88uD6ZM0ckF8f \
  AIRTABLE_LINKEDIN_TABLE_ID=tbljg75KMQWDo2Hgu \
  ANTHROPIC_API_KEY=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 \
  REPLICATE_API_TOKEN=r8_TGbnWs9rFMEoddsvimJlUxRITKIuhio4JXdXF \
  LINKEDIN_EMAIL=Musacbusiness@gmail.com \
  LINKEDIN_PASSWORD=ziqmUn-pyvri7-rijbyg
```

**What to expect:**
- Secret will be created successfully
- ✅ Ready for next step

---

## Step 3: Update Airtable Schema (10 minutes)

### 3A: Update Status Field

1. Go to your Airtable base: https://airtable.com/appw88uD6ZM0ckF8f/tbljg75KMQWDo2Hgu
2. Click on the **Status** column header
3. Click "Edit field"
4. Under "Select options", add these 6 values:
   - [ ] `Draft`
   - [ ] `Pending Review`
   - [ ] `Approved - Ready to Schedule`
   - [ ] `Scheduled`
   - [ ] `Posted`
   - [ ] `Rejected`
5. Click "Save"

### 3B: Add 6 New Date/Time Fields

1. In the same table, click the **+** icon to add a new field
2. Create 6 new fields (all as **Date/Time** type):

| Field Name | Type | Description |
|-----------|------|-------------|
| Image Generated At | Date/Time | When images were generated |
| Scheduled Time | Date/Time | When post will be published |
| Scheduled At | Date/Time | When scheduling occurred |
| Posted At | Date/Time | When post went live |
| Scheduled Deletion Date | Date/Time | When record should be deleted |
| Rejected At | Date/Time | When post was rejected |

3. Click Save for each field

---

## Step 4: Create 3 Airtable Automations (15 minutes)

**Replace `[YOUR-MODAL-URL]` with the URL from Step 1**

### Automation 1: Generate Images

1. Click **Automations** (sidebar)
2. Click **Create automation**
3. **Trigger:**
   - Select: "When record matches conditions"
   - Field: `Status`
   - Condition: `is`
   - Value: `Pending Review`
4. **Action:**
   - Type: "Webhook"
   - Method: `POST`
   - URL: `https://[YOUR-MODAL-URL]/webhook/status-change`
   - Payload type: `JSON`
   - Content:
     ```json
     {
       "record_id": "{record_id}",
       "status": "Pending Review",
       "base_id": "{base_id}",
       "table_id": "{table_id}"
     }
     ```
5. **Name:** "Generate Images When Pending Review"
6. Click **Turn ON** ✓

### Automation 2: Schedule Posts

1. Click **Create automation**
2. **Trigger:**
   - Select: "When record matches conditions"
   - Field: `Status`
   - Condition: `is`
   - Value: `Approved - Ready to Schedule`
3. **Action:**
   - Type: "Webhook"
   - Method: `POST`
   - URL: `https://[YOUR-MODAL-URL]/webhook/status-change`
   - Payload type: `JSON`
   - Content:
     ```json
     {
       "record_id": "{record_id}",
       "status": "Approved - Ready to Schedule",
       "base_id": "{base_id}",
       "table_id": "{table_id}"
     }
     ```
4. **Name:** "Schedule Post When Approved"
5. Click **Turn ON** ✓

### Automation 3: Handle Rejections

1. Click **Create automation**
2. **Trigger:**
   - Select: "When record matches conditions"
   - Field: `Status`
   - Condition: `is`
   - Value: `Rejected`
3. **Action:**
   - Type: "Webhook"
   - Method: `POST`
   - URL: `https://[YOUR-MODAL-URL]/webhook/status-change`
   - Payload type: `JSON`
   - Content:
     ```json
     {
       "record_id": "{record_id}",
       "status": "Rejected",
       "base_id": "{base_id}",
       "table_id": "{table_id}"
     }
     ```
4. **Name:** "Schedule Deletion When Rejected"
5. Click **Turn ON** ✓

---

## Step 5: Test All 3 Workflows (10 minutes)

### Test 1: Image Generation ✅

1. In Airtable, create a new row with:
   - Title: "Test Post 1"
   - Content: "This is a test post"
   - Status: Draft
2. Change Status to **Pending Review**
3. Wait 30-60 seconds
4. **Check:** Image URL should appear in the "Image URL" field
5. Check logs: `modal logs --app linkedin-automation`

### Test 2: Auto-Scheduling ✅

1. Same test post, change Status to **Approved - Ready to Schedule**
2. Wait 5 seconds
3. **Check:**
   - Status should change to **Scheduled**
   - "Scheduled Time" field should be populated with a future time
4. Check logs: `modal logs --app linkedin-automation generate_images_for_post`

### Test 3: Rejection Handling ✅

1. Create another test row with:
   - Title: "Test Post 2"
   - Content: "Another test"
   - Status: Draft
2. Change Status to **Rejected**
3. **Check:** "Scheduled Deletion Date" should appear (24 hours from now)
4. Check logs: `modal logs --app linkedin-automation handle_rejected_post`

---

## 🎉 You're Live! What Happens Next

### Daily Automatic Actions

**Every day at 6 AM UTC:**
- Modal generates 21 new posts (Draft status)
- Ready for you to review and approve

**When you change Status → Pending Review:**
- Modal generates images (30-60 seconds)
- Updates Airtable with image URL

**When you change Status → Approved - Ready to Schedule:**
- Modal calculates posting time
- Sets Status to "Scheduled"
- Stores scheduled time in Airtable

**Every 4 hours:**
- Modal checks for posts ready to post
- Posts to LinkedIn when time arrives
- Updates Status to "Posted"
- Schedules 7-day deletion

**Every hour:**
- Modal checks for records due for deletion
- Automatically deletes from Airtable

---

## 📊 Monitoring & Troubleshooting

### View Logs
```bash
# Real-time logs
modal logs --app linkedin-automation

# Specific function
modal logs --app linkedin-automation generate_daily_content
```

### Health Check
```bash
curl https://[YOUR-MODAL-URL]/health
```

### Common Issues

**Images not generating?**
- Check Modal logs
- Verify Automation is ON
- Check Replicate API balance

**Automations not triggering?**
- Verify Status field values match exactly
- Ensure Automations are ON
- Check webhook URL (no trailing slash)

**Posts not scheduling?**
- Check if Status is exactly "Approved - Ready to Schedule"
- Verify Airtable Automation is ON
- Check Modal logs for errors

---

## ✅ Go-Live Checklist

- [ ] Step 1: Deploy Modal app
- [ ] Step 2: Create Modal secrets
- [ ] Step 3: Update Airtable schema (6 status values + 6 date fields)
- [ ] Step 4: Create 3 Airtable Automations
- [ ] Step 5: Test all 3 workflows

**Once all complete: You're LIVE! 🚀**

---

**Need help?** Check the comprehensive guides:
- [QUICK_START_MODAL.md](./QUICK_START_MODAL.md) - Quick reference
- [MODAL_MIGRATION_GUIDE.md](./linkedin_automation/MODAL_MIGRATION_GUIDE.md) - Detailed guide
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Technical details

---

Generated: December 25, 2025
Status: Ready to Deploy
