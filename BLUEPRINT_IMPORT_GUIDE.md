# Make.com Blueprint Import Guide - LinkedIn Auto-Posting Scenario

**Blueprint File**: `linkedin_posting_blueprint.json`
**Scenario Goal**: Receive posts from Modal → Post to LinkedIn → Update Airtable → Send iPhone notification
**Setup Time**: ~15-20 minutes

---

## What is a Blueprint?

A **blueprint** in Make.com is a pre-configured automation template that you can import into your account. It contains:
- All modules (components) needed for the workflow
- How modules are connected together
- Module settings and configurations
- Data mappings between modules

Instead of building from scratch, you import the blueprint and just connect your accounts (Airtable, LinkedIn, etc.).

---

## Step 1: Download the Blueprint

The blueprint file is: **`linkedin_posting_blueprint.json`**

Location: `/Users/musacomma/Agentic Workflow/linkedin_posting_blueprint.json`

---

## Step 2: Import Blueprint into Make.com

### 2.1 Go to Make.com
1. Log in to [make.com](https://make.com)
2. Click your organization (top left)
3. Click "Blueprints"

### 2.2 Import the Blueprint
1. Click **"New Blueprint"** (or **"Import"**)
2. Click **"Select JSON file"**
3. Choose `linkedin_posting_blueprint.json` from your computer
4. Click **"Save"** or **"Import"**

### 2.3 Create Scenario from Blueprint
1. The blueprint appears in your blueprints list
2. Click the blueprint
3. Click **"Create Scenario"** or **"Use this Blueprint"**
4. Name it: `LinkedIn Auto-Posting with Airtable Sync`
5. Click **"Create"**

---

## Step 3: Configure the 4 Modules

### Module 1: Webhook Trigger ✓ (No config needed)
**Purpose**: Receives POST request from Modal with post data

**What it receives**:
```json
{
  "record_id": "recABC123...",
  "content": "Your post text here...",
  "image_url": "https://airtable-cdn.com/image.jpg",
  "base_id": "appXXXX...",
  "table_id": "tblXXXX...",
  "scheduled_deletion_date": "2025-12-31T00:00:00"
}
```

**To get the webhook URL**:
1. Click Module 1 (Webhook Trigger)
2. Copy the **Webhook URL** shown
3. Save this - you'll need it for Modal secret

---

### Module 2: LinkedIn Create Post ⚙️ (NEEDS CONFIG)
**Purpose**: Posts content and image to LinkedIn

#### 2.1 Connect LinkedIn Account
1. Click Module 2 (LinkedIn Create Post)
2. Under "Connection", click the dropdown
3. Click **"Create a new connection"** or **"Add"**
4. Make.com will:
   - Open LinkedIn login
   - Ask for permission to post
   - Authorize Make.com
5. Once authorized, the connection is saved

#### 2.2 Verify Module Settings
The blueprint already has:
- **Post Text**: `{{1.content}}` (pulls from webhook)
- **Image URL**: `{{1.image_url}}` (pulls from webhook)
- **Image Upload**: Automatically enabled if image_url exists

**Test it**: Click the play button (▶️) to test this module alone
- Should show: "Post created successfully"

---

### Module 3: Airtable Update Record ⚙️ (NEEDS CONFIG)
**Purpose**: Updates Airtable record with Status="Posted" and LinkedIn URL

#### 3.1 Connect Airtable Account
1. Click Module 3 (Airtable Update Record)
2. Under "Connection", click the dropdown
3. Click **"Create a new connection"** or **"Add"**
4. Make.com will ask for your Airtable API key
5. Get your API key:
   - Go to [airtable.com](https://airtable.com) → Account settings
   - Create new personal access token with these scopes:
     - `data.records:write`
     - `schema.bases:read`
   - Copy the token
6. Paste token in Make.com connection dialog
7. Click "Save"

#### 3.2 Verify Fields
The blueprint already maps these fields:
- **Base ID**: `{{1.base_id}}` (from webhook)
- **Table ID**: `{{1.table_id}}` (from webhook)
- **Record ID**: `{{1.record_id}}` (from webhook)
- **Status**: "Posted" (hardcoded)
- **Posted At**: Current timestamp
- **LinkedIn Post URL**: `{{2.postUrl}}` (from LinkedIn module)

**Test it**: Click the play button to verify Airtable update works

---

### Module 4: iPhone Push Notification ✓ (Auto-configured)
**Purpose**: Sends push notification to your iPhone

#### 4.1 Install Make.com Mobile App (if not already)
1. Go to Apple App Store
2. Search: "Make"
3. Install the official **Make** app
4. Log in with your Make.com account
5. Enable notifications on your iPhone:
   - Settings → Notifications → Make
   - Allow notifications: ON

#### 4.2 Module Already Configured
The blueprint already has:
- **Notification Title**: "📱 LinkedIn Post Published"
- **Message**: Shows first 50 characters of your post
- **Target**: iPhone (via Make.com app)

**Test it**: Click the play button
- Should show: "Notification sent successfully"
- Check your iPhone for a test notification

---

## Step 4: Get the Webhook URL and Update Modal Secret

### 4.1 Copy Webhook URL from Module 1
1. Go back to Module 1 (Webhook Trigger)
2. Look for the **Webhook URL** field
3. Click the copy button (📋)
4. Save it - example: `https://hook.us1.make.com/abc123def456...`

### 4.2 Update Modal Secret
Run this in terminal:
```bash
modal secret update linkedin-makecom-webhook \
  MAKE_LINKEDIN_WEBHOOK_URL="https://hook.us1.make.com/YOUR_WEBHOOK_ID"
```

Replace `YOUR_WEBHOOK_ID` with your actual webhook URL from step 4.1.

---

## Step 5: Enable the Scenario

1. Go back to your scenario (should be on the main canvas)
2. Click **"ON"** button (top right) to enable the scenario
3. You should see: "Scenario is active ✓"

**The scenario is now waiting for webhooks from Modal!**

---

## Step 6: Test the Complete Scenario

### 6.1 Prepare Test Post in Airtable
1. Go to your Airtable LinkedIn table
2. Create a new record:
   - **Status**: "Scheduled"
   - **Scheduled Time**: [current time - 1 minute]
   - **Post Content**: "🧪 Test post - please ignore"
   - **Image**: (leave empty for first test)

### 6.2 Wait for Scheduler
1. Wait 5-10 seconds
2. Modal scheduler should detect it and send webhook to Make.com

### 6.3 Check Results

**Check Make.com Logs**:
1. Go to your scenario
2. Click **"View execution history"** (bottom left)
3. You should see:
   - ✅ Module 1: Webhook received
   - ✅ Module 2: Post created on LinkedIn
   - ✅ Module 3: Airtable record updated
   - ✅ Module 4: Notification sent

**Check your iPhone**:
- You should get a push notification from Make.com
- Check Airtable:
  - Status should be "Posted"
  - "Posted At" should have timestamp
  - "LinkedIn Post URL" should have URL

**Check LinkedIn**:
- Your test post should appear on your LinkedIn profile

---

## Troubleshooting

### Issue: Webhook Not Received
**Problem**: Module 1 never activates
**Solutions**:
1. Check webhook URL was copied correctly
2. Verify Modal secret was updated
3. Check Modal logs for webhook call
4. Redeploy Modal: `modal deploy cloud/modal_linkedin_automation.py`

### Issue: LinkedIn Post Fails
**Problem**: Module 2 shows error
**Solutions**:
1. Check LinkedIn connection is valid (refresh it)
2. Verify your LinkedIn account can post (not restricted)
3. Check post content length (LinkedIn has limits)
4. Try manual test: click Module 2 play button

### Issue: Airtable Not Updating
**Problem**: Module 3 shows error
**Solutions**:
1. Verify Airtable connection (refresh it)
2. Check that record_id, base_id, table_id are being passed correctly
3. Ensure Airtable token has write permissions
4. Check field names match exactly (case-sensitive)

### Issue: iPhone Not Getting Notification
**Problem**: Module 4 shows error or success but you don't receive it
**Solutions**:
1. Verify Make.com app is installed on iPhone
2. Check iPhone notification settings (Settings → Notifications → Make)
3. Check you're logged into Make.com app with same account
4. Try a manual test: click Module 4 play button

### Issue: "Connection" Error When Testing
**Problem**: Can't test modules because connections aren't configured
**Solutions**:
1. Make sure Airtable connection is created (Module 3)
2. Make sure LinkedIn connection is created (Module 2)
3. Both need to be authorized first

---

## What Happens When Post Goes Live

```
1. Airtable record with Status="Scheduled" (scheduled time in past)
                    ↓ (5 seconds later)
2. Modal scheduler detects it
                    ↓
3. Modal sends webhook POST to Make.com with post data
                    ↓
4. Make.com Module 1 receives webhook
                    ↓
5. Make.com Module 2 posts to LinkedIn
                    ↓
6. LinkedIn returns post URL
                    ↓
7. Make.com Module 3 updates Airtable:
   - Status: "Posted"
   - Posted At: [timestamp]
   - LinkedIn Post URL: [link to post]
                    ↓
8. Make.com Module 4 sends iPhone notification
                    ↓
9. You get notification: "📱 LinkedIn Post Published - Your post text here..."
                    ↓
✅ COMPLETE - Post is live, Airtable is updated, you're notified!
```

---

## File Structure in Blueprint

```json
{
  "name": "LinkedIn Auto-Posting with Airtable Sync & iPhone Notification",
  "flow": [
    {
      "id": 1,
      "module": "builtin:WebhookTrigger",
      "parameters": {
        "name": "Receive Post Data from Modal"
      }
    },
    {
      "id": 2,
      "module": "linkedin:createPost",
      "parameters": {
        "postText": "{{1.content}}",
        "imageUrl": "{{1.image_url}}"
      }
    },
    {
      "id": 3,
      "module": "airtable:updateRecord",
      "parameters": {
        "baseId": "{{1.base_id}}",
        "recordId": "{{1.record_id}}",
        "fields": {
          "Status": "Posted",
          "LinkedIn Post URL": "{{2.postUrl}}"
        }
      }
    },
    {
      "id": 4,
      "module": "make:sendNotification",
      "parameters": {
        "title": "📱 LinkedIn Post Published",
        "message": "Your post just went live!"
      }
    }
  ],
  "connections": [
    {"source": 1, "target": 2},
    {"source": 2, "target": 3},
    {"source": 3, "target": 4}
  ]
}
```

---

## Next Steps Checklist

- [ ] Download blueprint JSON file
- [ ] Import into Make.com
- [ ] Create scenario from blueprint
- [ ] Configure LinkedIn connection (Module 2)
- [ ] Configure Airtable connection (Module 3)
- [ ] Verify iPhone notifications enabled (Module 4)
- [ ] Copy webhook URL from Module 1
- [ ] Update Modal secret with webhook URL
- [ ] Enable the scenario
- [ ] Test with one post
- [ ] Monitor Make.com logs for first week

---

## Support

**If you need help**:

1. **Check Make.com execution logs**: Your scenario → "View execution history"
2. **Check Modal logs**: https://modal.com/apps/musacbusiness/main/deployed/linkedin-automation
3. **Blueprint file**: `linkedin_posting_blueprint.json` in your Agentic Workflow folder

---

**You're all set!** Once enabled, the scenario will automatically:
- ✅ Receive posts from Modal
- ✅ Post to LinkedIn
- ✅ Update Airtable
- ✅ Notify your iPhone

Everything is fully automated. Set it and forget it! 🚀
