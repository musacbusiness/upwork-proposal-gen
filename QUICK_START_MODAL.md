# Quick Start - Modal LinkedIn Automation

**TL;DR**: 3 steps to go from local to serverless.

---

## 1️⃣ Deploy Modal App (5 min)

```bash
cd /Users/musacomma/Agentic\ Workflow/cloud
modal deploy modal_linkedin_automation.py
```

✅ Copy the URL from the output (you'll need it)

---

## 2️⃣ Create Secrets (3 min)

```bash
modal secret create linkedin-secrets \
  AIRTABLE_API_KEY=patQCCzbAjKw675Bf... \
  AIRTABLE_BASE_ID=appw88uD6ZM0ckF8f \
  AIRTABLE_LINKEDIN_TABLE_ID=tblXXXXXXXXXXXXXX \
  ANTHROPIC_API_KEY=sk-ant-api03-... \
  REPLICATE_API_TOKEN=r8_TGbnWs9rFMEoddsvimJlUxRITKIuhio4... \
  LINKEDIN_EMAIL=Musacbusiness@gmail.com \
  LINKEDIN_PASSWORD=ziqmUn-pyvri7-rijbyg
```

✅ Replace values from your `.env` file

---

## 3️⃣ Set Up Airtable Automations (10 min)

In Airtable, create 3 automations:

### Automation 1: Generate Images
- **Trigger:** Status `is` `Pending Review`
- **Action:** Webhook POST
- **URL:** `https://[YOUR-MODAL-URL]/webhook/status-change`
- **Body:**
```json
{"record_id": "{record_id}", "status": "Pending Review", "base_id": "{base_id}", "table_id": "{table_id}"}
```

### Automation 2: Schedule Posts
- **Trigger:** Status `is` `Approved - Ready to Schedule`
- **Action:** Webhook POST
- **URL:** `https://[YOUR-MODAL-URL]/webhook/status-change`
- **Body:**
```json
{"record_id": "{record_id}", "status": "Approved - Ready to Schedule", "base_id": "{base_id}", "table_id": "{table_id}"}
```

### Automation 3: Handle Rejections
- **Trigger:** Status `is` `Rejected`
- **Action:** Webhook POST
- **URL:** `https://[YOUR-MODAL-URL]/webhook/status-change`
- **Body:**
```json
{"record_id": "{record_id}", "status": "Rejected", "base_id": "{base_id}", "table_id": "{table_id}"}
```

✅ Turn all 3 ON

---

## 4️⃣ Update Airtable Schema (5 min)

### New Status Values
Add to "Status" field:
- Draft
- Pending Review
- Approved - Ready to Schedule
- Scheduled
- Posted
- Rejected

### New Fields (as Date/Time)
- Image Generated At
- Scheduled Time
- Scheduled At
- Posted At
- Scheduled Deletion Date
- Rejected At

---

## 5️⃣ Test It (5 min)

1. Create a post in Airtable (Draft)
2. Change status to `Pending Review`
3. Wait 30-60 seconds
4. ✅ Image URL appears?

5. Change status to `Approved - Ready to Schedule`
6. Wait 5 seconds
7. ✅ Status changes to `Scheduled`?
8. ✅ Scheduled Time is populated?

---

## Your New Workflow

```
┌──────────────────┐
│  You Create Post │
│  Status: Draft   │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────┐
│ You: Change to           │
│ "Pending Review"         │
└────────┬─────────────────┘
         │
    [Automatic]
         │
         ▼
┌──────────────────────────┐
│ Modal: Generate Images   │
│ (30-60 seconds)          │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ You: Review Image        │
│ Change to "Approved -    │
│ Ready to Schedule"       │
└────────┬─────────────────┘
         │
    [Automatic]
         │
         ▼
┌──────────────────────────┐
│ Modal: Schedule Post     │
│ Set random time (9am,    │
│ 2pm, or 8pm ±15min)      │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ Status: Scheduled        │
│ Ready for publishing     │
└────────┬─────────────────┘
         │
    [Modal Cron - Every 4h]
         │
         ▼
┌──────────────────────────┐
│ Modal: Post to LinkedIn  │
│ (When scheduled time     │
│ passes)                  │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ Status: Posted           │
│ 7-day deletion timer     │
│ started                  │
└──────────────────────────┘
```

---

## Monitoring

```bash
# Real-time logs
modal logs --app linkedin-automation

# Specific function
modal logs --app linkedin-automation generate_images_for_post

# Health check
curl https://[YOUR-MODAL-URL]/health
```

---

## Costs

| Item | Cost |
|------|------|
| Modal compute | $1-5/month |
| Image generation | $2-10/month |
| Claude API | $5-20/month |
| **Total** | **~$10-35/month** |

Much cheaper than local compute + hosting!

---

## Troubleshooting

**Images not generating?**
- Check Modal logs: `modal logs --app linkedin-automation`
- Verify Automation webhook URL (no trailing slash)
- Check Replicate balance

**Status not changing?**
- Verify Airtable Automation is ON
- Check webhook URL matches your Modal deployment
- Test manually: `curl -X POST [WEBHOOK-URL] -H "Content-Type: application/json" -d '{"record_id":"rec123","status":"Pending Review","base_id":"appXXX","table_id":"tblXXX"}'`

**Webhook 404?**
- Modal URL is incorrect
- App may not have deployed successfully
- Try redeploying: `modal deploy cloud/modal_linkedin_automation.py`

---

## Full Documentation

For detailed setup and troubleshooting:
- 📖 [Full Migration Guide](./linkedin_automation/MODAL_MIGRATION_GUIDE.md)
- ✅ [Deployment Checklist](./MODAL_DEPLOYMENT_CHECKLIST.md)
- 🔧 [Modal App Code](./cloud/modal_linkedin_automation.py)

---

## Next Steps

1. ✅ Deploy Modal app
2. ✅ Create secrets
3. ✅ Update Airtable schema
4. ✅ Set up 3 automations
5. ✅ Test workflows
6. 🔄 Implement LinkedIn posting (Selenium)
7. 🔄 Implement daily content generation
8. 🔄 Monitor for 7 days before removing local setup

---

**Questions?** Check the full guide or Modal logs for details.

**Ready?** Start with Step 1 above! 🚀
