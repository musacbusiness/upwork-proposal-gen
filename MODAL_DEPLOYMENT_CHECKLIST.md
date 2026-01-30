# Modal Deployment Checklist - LinkedIn Automation

Quick reference for deploying LinkedIn automation to Modal.

---

## Pre-Deployment (5 minutes)

- [ ] Have Modal CLI installed: `which modal`
- [ ] Authenticated with Modal: `modal token new` (if first time)
- [ ] Have Airtable API key from `.env`
- [ ] Have Airtable Base ID from `.env`
- [ ] Have Airtable Table ID (see guide: step 5)
- [ ] Have Anthropic API key
- [ ] Have Replicate API token
- [ ] Have LinkedIn credentials

---

## Deploy Modal App (10 minutes)

```bash
cd /Users/musacomma/Agentic\ Workflow/cloud
modal deploy modal_linkedin_automation.py
```

- [ ] Deployment completes successfully
- [ ] Save the Modal URL from output (looks like `https://xxx--linkedin-automation.modal.run`)
- [ ] Verify: `modal apps list` shows `linkedin-automation`

---

## Create Modal Secrets (5 minutes)

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

- [ ] Secret created: `modal secret list` shows `linkedin-secrets`
- [ ] All 8 variables present

---

## Update Airtable Schema (10 minutes)

### Status Field Values
Add to existing "Status" field:
- [ ] `Draft`
- [ ] `Pending Review`
- [ ] `Approved - Ready to Schedule`
- [ ] `Scheduled`
- [ ] `Posted`
- [ ] `Rejected`

### New Fields
Add these as new columns to Posts table:
- [ ] `Image Generated At` (Date/Time)
- [ ] `Scheduled Time` (Date/Time)
- [ ] `Scheduled At` (Date/Time)
- [ ] `Posted At` (Date/Time)
- [ ] `Scheduled Deletion Date` (Date/Time)
- [ ] `Rejected At` (Date/Time)

---

## Set Up Airtable Automations (15 minutes)

### Automation #1: Pending Review → Generate Images
- [ ] Created automation
- [ ] Trigger: Status `is` `Pending Review`
- [ ] Action: Webhook POST to `https://[YOUR-MODAL-URL]/webhook/status-change`
- [ ] Body:
  ```json
  {
    "record_id": "{record_id}",
    "status": "Pending Review",
    "base_id": "{base_id}",
    "table_id": "{table_id}"
  }
  ```
- [ ] Named: "Generate Images When Pending Review"
- [ ] Status: ON ✓

### Automation #2: Approved → Schedule Post
- [ ] Created automation
- [ ] Trigger: Status `is` `Approved - Ready to Schedule`
- [ ] Action: Webhook POST to `https://[YOUR-MODAL-URL]/webhook/status-change`
- [ ] Body:
  ```json
  {
    "record_id": "{record_id}",
    "status": "Approved - Ready to Schedule",
    "base_id": "{base_id}",
    "table_id": "{table_id}"
  }
  ```
- [ ] Named: "Schedule Post When Approved"
- [ ] Status: ON ✓

### Automation #3: Rejected → Schedule Deletion
- [ ] Created automation
- [ ] Trigger: Status `is` `Rejected`
- [ ] Action: Webhook POST to `https://[YOUR-MODAL-URL]/webhook/status-change`
- [ ] Body:
  ```json
  {
    "record_id": "{record_id}",
    "status": "Rejected",
    "base_id": "{base_id}",
    "table_id": "{table_id}"
  }
  ```
- [ ] Named: "Schedule Deletion When Rejected"
- [ ] Status: ON ✓

---

## Test Workflows (15 minutes)

### Test 1: Image Generation (Pending Review)
1. [ ] Create test post in Airtable with Draft status
2. [ ] Change status to `Pending Review`
3. [ ] Check Modal logs: `modal logs --app linkedin-automation`
4. [ ] Verify image URL appears in Airtable (30-60 seconds)
5. [ ] Check "Image Generated At" timestamp

### Test 2: Auto-Scheduling (Approved)
1. [ ] Change post status to `Approved - Ready to Schedule`
2. [ ] Check Modal logs
3. [ ] Verify status changes to `Scheduled`
4. [ ] Verify "Scheduled Time" is populated (future time)
5. [ ] Check "Scheduled At" timestamp

### Test 3: Rejection Handling (Rejected)
1. [ ] Change post status to `Rejected`
2. [ ] Check Modal logs
3. [ ] Verify "Scheduled Deletion Date" is 24 hours from now
4. [ ] Check "Rejected At" timestamp

---

## Verify Deployment (5 minutes)

- [ ] Health check passes: `curl https://[YOUR-MODAL-URL]/health`
- [ ] Response shows: `"status": "healthy"`
- [ ] Modal logs show no errors: `modal logs --app linkedin-automation`
- [ ] Airtable connection working (test in Airtable)

---

## Post-Deployment (Optional)

- [ ] Update daily content generation function (implement logic)
- [ ] Implement LinkedIn posting via Selenium
- [ ] Set up backup/monitoring
- [ ] Remove local webhook server (no longer needed)
- [ ] Document Modal URL in team notes
- [ ] Monitor costs (should be <$5/month)

---

## Rollback Plan

If something goes wrong:
1. [ ] Keep local setup running until Modal is stable for 7 days
2. [ ] If Modal issues, revert to local by restarting webhook server
3. [ ] `python linkedin_automation/execution/webhook_revise_automation.py`

---

## Costs

| Service | Estimate |
|---------|----------|
| Modal (compute) | $1-5/month |
| Airtable | $0 (free tier) |
| Replicate (images) | $2-10/month |
| Anthropic (Claude) | $5-20/month |
| **Total** | **~$10-35/month** |

---

## Useful Commands

```bash
# View all Modal apps
modal app list

# View logs
modal logs --app linkedin-automation

# View specific function logs
modal logs --app linkedin-automation generate_images_for_post

# Check secrets
modal secret list

# Update a secret
modal secret update linkedin-secrets REPLICATE_API_TOKEN=new_token

# Redeploy after code changes
modal deploy cloud/modal_linkedin_automation.py

# Serve locally for testing (without deploying)
modal serve cloud/modal_linkedin_automation.py
```

---

## Completion

- [ ] All checks passed
- [ ] Workflows tested successfully
- [ ] Ready for production use
- [ ] Documented Modal URL and secret names

**Date Deployed:** ___________

**Deployed By:** ___________

**Notes:**

---

**Next Steps:**
1. Monitor for 7 days
2. Once stable, remove local webhook server
3. Update daily generation function
4. Implement LinkedIn Selenium posting
