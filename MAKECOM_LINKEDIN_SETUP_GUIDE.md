# Make.com Scenario Setup Guide - LinkedIn Auto-Posting

**Goal**: Create a Make.com scenario that receives posts from Modal, posts them to LinkedIn via Linkup API, sends you an SMS, and notifies Modal when complete.

---

## Part 1: Prerequisites

### 1.1 Get Linkup API Key
- Go to [Linkup.so](https://linkup.so)
- Sign up for account
- Connect your LinkedIn profile through Linkup
- Get your API key from settings
- Save it securely

### 1.2 Get SMS Service (Twilio)
- Go to [Twilio.com](https://twilio.com)
- Create free account (includes $20 credits)
- Get your phone number
- Get Account SID and Auth Token
- In Make.com, connect Twilio module

### 1.3 Know Your Phone Number
- Your phone number in format: `+1234567890` (with country code)

---

## Part 2: Create Make.com Scenario

### Step 1: Create New Scenario
1. Log in to Make.com
2. Click "Create a new scenario"
3. Name it: `LinkedIn Auto-Posting with SMS & Modal Sync`
4. Click Create

### Step 2: Add Webhook Trigger Module
1. Click the empty module area
2. Search: `Webhooks`
3. Select: `Webhooks → Custom Webhook`
4. Click "Add"
5. Name it: "Receive Post from Modal"
6. Click "Save"
7. A webhook URL appears. **Copy this URL** - you'll need it later

**Example webhook URL:**
```
https://hook.us1.make.com/abc123def456ghi789jkl
```

### Step 3: Add Linkup API Module (Post to LinkedIn)
1. Click the right arrow from the Webhook module
2. Search: `Linkup`
3. Select: `Linkup API → Create a Post`
4. Click "Add"
5. Name it: "Post to LinkedIn"
6. **Connect your Linkup account** (or add API key)
7. Configure:
   - **Post text**: Click the input field, select `content` from the webhook data
   - **Image URL**: Click the input field, select `image_url` from webhook data
   - **Include image**: Leave empty (Linkup auto-detects)
8. Click "Save"

**To map the fields properly:**
- When you click in a field, you'll see `{{1.content}}` and `{{1.image_url}}` options
- Select those to auto-populate

### Step 4: Add SMS Notification Module
1. Click the right arrow from Linkup module
2. Search: `SMS` or `Twilio`
3. Select: `SMS → Send an SMS` (or Twilio module)
4. Click "Add"
5. Name it: "Send SMS Notification"
6. **Connect Twilio account** (or your SMS service)
7. Configure:
   - **To**: Your phone number (e.g., `+14155552671`)
   - **Message**:
   ```
   Your LinkedIn post just went live! 🎉 Check it out at {{2.post_url}}
   ```
8. Click "Save"

### Step 5: Add HTTP Module (Notify Modal)
1. Click the right arrow from SMS module
2. Search: `HTTP`
3. Select: `HTTP → Make a Request`
4. Click "Add"
5. Name it: "Update Modal That Post Is Live"
6. Configure:
   - **Method**: POST
   - **URL**: (you'll fill this in after deploying Modal)
   - **Headers**:
     - Key: `Content-Type`
     - Value: `application/json`
   - **Body** (Raw JSON):
   ```json
   {
     "record_id": "{{1.record_id}}",
     "base_id": "{{1.base_id}}",
     "table_id": "{{1.table_id}}",
     "post_url": "{{2.post_url}}",
     "posted_at": "{{now}}",
     "action": "mark_as_posted"
   }
   ```
7. Click "Save"

**Note**: You'll add the Modal webhook URL after deploying the updated Modal code

---

## Part 3: Set Environment Variables in Make.com

Environment variables let you store secrets securely.

1. In Make.com, go to Organization Settings (top left)
2. Click "Variables" or "Secrets"
3. Add these variables:

| Variable Name | Value | Example |
|---------------|-------|---------|
| `LINKUP_API_KEY` | Your Linkup API key | `sk_live_abc123...` |
| `RECIPIENT_PHONE` | Your phone number | `+14155552671` |
| `MODAL_WEBHOOK_URL` | Modal webhook (add after deploying) | `https://musacbusiness--linkedin-automation.modal.run/mark-post-as-posted` |

Then in each module, reference them with `{{env(VARIABLE_NAME)}}`

---

## Part 4: Test the Scenario

1. **Enable** the scenario (toggle at top right)
2. Wait for the trigger to be ready
3. Go back to the webhook module and copy the webhook URL
4. Send a test POST request:

```bash
curl -X POST https://hook.us1.make.com/abc123... \
  -H "Content-Type: application/json" \
  -d '{
    "record_id": "recTEST123",
    "content": "🧪 Test post - please ignore",
    "image_url": "",
    "base_id": "appw88uD6ZM0ckF8f",
    "table_id": "tbljg75KMQWDo2Hgu",
    "scheduled_deletion_date": "2025-12-31T00:00:00"
  }'
```

5. Check:
   - ✅ Module 2: Did Linkup receive the request?
   - ✅ Module 3: Did you get an SMS?
   - ✅ Module 4: Can you see the HTTP request was sent?

---

## Part 5: Configure Modal to Call Make.com

### Step 5a: Get Your Webhook URL
1. In Make.com, go to your scenario
2. Click on the Webhook module (Module 1)
3. Copy the Webhook URL
4. Example: `https://hook.us1.make.com/abc123def456ghi789jkl`

### Step 5b: Create Modal Secret

Run this command in terminal:

```bash
modal secret create linkedin-makecom-webhook \
  MAKE_LINKEDIN_WEBHOOK_URL="https://hook.us1.make.com/YOUR_WEBHOOK_ID"
```

Replace `YOUR_WEBHOOK_ID` with your actual webhook URL from Step 5a.

### Step 5c: Deploy Updated Modal Code

Run:
```bash
cd "/Users/musacomma/Agentic Workflow"
modal deploy cloud/modal_linkedin_automation.py
```

---

## Part 6: Create Modal Webhook for Make.com to Call Back

Now Make.com needs a way to tell Modal that the post is live. We need to add a webhook endpoint in Modal.

**The code below adds a new endpoint that Make.com will call:**

Add this to your `cloud/modal_linkedin_automation.py` file:

```python
@app.function(image=image, secrets=[modal.Secret.from_name("linkedin-secrets")], timeout=60)
@fastapi_endpoint()
def mark_post_as_posted(request: dict) -> dict:
    """
    Webhook endpoint for Make.com to call when post goes live.
    Make.com calls this after successfully posting to LinkedIn.
    """
    import requests

    logger = logging.getLogger(__name__)
    logger.info(f"Received post-live notification from Make.com for record {request.get('record_id')}")

    try:
        record_id = request.get('record_id')
        base_id = request.get('base_id')
        table_id = request.get('table_id')
        post_url = request.get('post_url')

        if not all([record_id, base_id, table_id]):
            return {"success": False, "error": "Missing required fields"}

        # Update Airtable with LinkedIn post URL if available
        update_fields = {
            "LinkedIn Post URL": post_url
        }

        # Note: Status should already be "Posted" from Modal's post_to_linkedin_via_makecom()
        # This just adds the LinkedIn URL for reference

        success = update_airtable_record(base_id, table_id, record_id, update_fields)

        if success:
            logger.info(f"Updated record {record_id} with LinkedIn post URL")
            return {"success": True, "message": "Post marked as live"}
        else:
            logger.error(f"Failed to update record {record_id}")
            return {"success": False, "error": "Airtable update failed"}

    except Exception as e:
        logger.error(f"Error processing post-live notification: {e}")
        return {"success": False, "error": str(e)}
```

Then get the endpoint URL and add it to Make.com:
- After deploying, your endpoint is: `https://musacbusiness--linkedin-automation.modal.run/mark-post-as-posted`
- Add this to the HTTP module in Make.com (Module 4)

---

## Part 7: End-to-End Test

1. **Add a test post to Airtable**:
   - Status: "Scheduled"
   - Scheduled Time: [current time - 1 minute]
   - Post Content: "🧪 Test post - please ignore"
   - Image: (optional)

2. **Wait 5-10 seconds** for the scheduler to trigger

3. **Check:**
   - ✅ Modal logs show: "Sending post to Make.com webhook"
   - ✅ Make.com scenario ran successfully
   - ✅ You got an SMS notification
   - ✅ Post appears on LinkedIn
   - ✅ Airtable shows Status = "Posted"

4. **Monitor logs:**
   - Modal: `https://modal.com/apps/musacbusiness/main/deployed/linkedin-automation`
   - Make.com: Execution history in your scenario

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Make.com webhook not receiving data | Check Modal logs - is webhook URL correct? Check firewall/network |
| Linkup API failing | Verify API key is correct. Check Linkup account is connected to LinkedIn |
| SMS not sending | Check phone number format (+country_code). Verify Twilio account is active |
| Modal webhook not called | Check HTTP module URL is correct. Check JSON body syntax |
| LinkedIn post blocked | Linkup may have rate limits. Try waiting 1 minute between posts |

---

## Summary

Your flow now works like this:

```
Post scheduled in Airtable
    ↓ (5 sec scheduler)
Modal auto_schedule_and_post_scheduler() detects "Scheduled" status
    ↓
post_to_linkedin_via_makecom() calls Make.com webhook
    ↓ (Make.com receives JSON)
[1] Webhook module: extracts post data
    ↓
[2] Linkup API: posts to LinkedIn (avoids checkpoint)
    ↓
[3] SMS module: sends you notification
    ↓
[4] HTTP module: calls Modal to confirm
    ↓
Modal updates Airtable: Status="Posted", LinkedIn Post URL added
    ↓
Post appears on your LinkedIn profile!
```

---

## Files Modified

- `cloud/modal_linkedin_automation.py`:
  - Renamed `post_to_linkedin()` → `post_to_linkedin_via_makecom()`
  - Replaced Selenium with webhook call
  - Added `mark_post_as_posted()` endpoint for Make.com callback
  - Fixed image URL extraction from Airtable attachment array

- New Modal secret:
  - `linkedin-makecom-webhook` with `MAKE_LINKEDIN_WEBHOOK_URL`

- New Make.com scenario:
  - 4 modules (Webhook, Linkup, SMS, HTTP callback)
  - Fully automated LinkedIn posting

---

## Cost

- **Modal**: Free (within limits)
- **Make.com**: ~$0-50/month depending on usage
- **Linkup**: ~$50-200/month for LinkedIn posting
- **Twilio SMS**: ~$0.01/SMS after free credits

**Total**: ~$50-250/month, but posts 24/7 without checkpoints!

---

## Next Steps

1. ✅ Deploy updated Modal code
2. ✅ Create Make.com scenario
3. ✅ Test end-to-end with test post
4. ✅ Monitor logs for first week
5. ✅ Document any issues

Done! You now have enterprise-grade LinkedIn automation that works around security checkpoints.
