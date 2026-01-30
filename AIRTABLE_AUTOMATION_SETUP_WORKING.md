# Setting Up Working Airtable Automations

## The Problem

You changed the status to "Pending Review" but nothing happened because there's no trigger configured.

**Why?** The Modal system is deployed in the cloud, but Airtable Automations can't directly call Modal functions without HTTP webhooks (which are complex to set up).

## The Solution: Hybrid Approach

Use a combination of:
1. **Airtable Automations** (free, built-in)
2. **Python script** (runs on your Mac or a server)
3. **Modal functions** (already deployed)

---

## Setup Option 1: Simple Python Trigger (Recommended for Testing)

### Step 1: Make the Script Executable

```bash
cd /Users/musacomma/Agentic\ Workflow
chmod +x cli_trigger.py
```

### Step 2: Test It Works

```bash
# Test with your actual record ID
python3 cli_trigger.py --record-id "rec036I0Bjg8HT2Cu" --status "Pending Review"
```

### Step 3: Set Up Airtable Automation to Call It

**Note:** This requires Airtable Scripts (available on some plans) or an external automation tool.

For now, **manually run** the trigger:

```bash
# Whenever you change a status in Airtable, run:
python3 cli_trigger.py --record-id "YOUR_RECORD_ID" --status "Pending Review"
python3 cli_trigger.py --record-id "YOUR_RECORD_ID" --status "Approved - Ready to Schedule"
python3 cli_trigger.py --record-id "YOUR_RECORD_ID" --status "Rejected"
```

---

## Setup Option 2: Flask Webhook Server (For True Automation)

This approach runs a local server on your Mac that Airtable can call.

### Step 1: Install Flask

```bash
pip3 install flask
```

### Step 2: Start the Webhook Server

```bash
cd /Users/musacomma/Agentic\ Workflow
python3 airtable_webhook_server.py
```

**Output:**
```
============================================================
🚀 Airtable Webhook Server Starting
============================================================

✅ Server will run on: http://localhost:8000
...
```

### Step 3: Keep Server Running

The server must stay running 24/7 for webhooks to work. You can:
- Keep terminal window open
- Use `screen` or `tmux` to keep it running in background
- Set up a systemd service (advanced)

### Step 4: Configure Airtable Automations

**Automation 1: Trigger on "Pending Review" Status**

1. In Airtable, go to **Automations**
2. Click **Create automation**
3. **Trigger:**
   - "When record matches conditions"
   - Field: `Status`
   - Condition: `is`
   - Value: `Pending Review`

4. **Action:**
   - "Send HTTP request" (or "Script")
   - Method: `POST`
   - URL: `http://localhost:8000/webhook`
   - Body (JSON):
     ```json
     {
       "record_id": "{record_id}",
       "status": "Pending Review",
       "base_id": "appw88uD6ZM0ckF8f",
       "table_id": "tbljg75KMQWDo2Hgu"
     }
     ```

5. Turn **ON**

**Automation 2: Trigger on "Approved - Ready to Schedule" Status**

Repeat above with:
- Status: `Approved - Ready to Schedule`
- JSON body: `"status": "Approved - Ready to Schedule"`

**Automation 3: Trigger on "Rejected" Status**

Repeat above with:
- Status: `Rejected`
- JSON body: `"status": "Rejected"`

---

## Right Now: Test with Your Records

You have 3 records in "Pending Review" status. Test them manually:

```bash
# First record
python3 cli_trigger.py --record-id "rec036I0Bjg8HT2Cu" --status "Pending Review"

# Wait 30-60 seconds, check Airtable for image generation

# Second record
python3 cli_trigger.py --record-id "rec0JRXCnqGg1PkAc" --status "Pending Review"

# Third record
python3 cli_trigger.py --record-id "recN6hXK3HVN9Yo7s" --status "Pending Review"
```

---

## Troubleshooting

### Issue: "Function object is not callable"
**Status:** Known issue with modal function calling from subprocess
**Workaround:** Use the Flask server approach instead

### Issue: Webhook server won't stay running
**Solution:** Use tmux or screen:
```bash
# Run in background with tmux
tmux new-session -d -s webhook "python3 airtable_webhook_server.py"

# View logs
tmux attach-session -t webhook

# Kill when done
tmux kill-session -t webhook
```

### Issue: Airtable automation "Send HTTP request" not available
**Solution:**
- Check your Airtable plan (Pro+ required for some features)
- Or upgrade the automations to use the built-in webhook action
- Or contact Airtable support

---

## Current Status

✅ Modal app deployed
✅ All functions ready
✅ Airtable schema configured
❌ Trigger system needs setup

**Next step:** Choose Option 1 (manual) or Option 2 (automated webhook server) and set it up.

---

## Long-Term Solution

Once you verify everything works, you can:

1. Move the webhook server to a permanent host (Heroku, AWS, Modal itself)
2. Set up cron jobs to call the trigger on schedules
3. Enable Modal's built-in cron jobs for automatic daily posting

---

**Questions?** Start with Option 1 (manual trigger) to test the system, then move to Option 2 once you're confident it works.
