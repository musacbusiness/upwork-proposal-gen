# Airtable LinkedIn Webhook Listener Setup

## Overview

The local webhook listener polls Airtable every 30 seconds for status changes and triggers Modal functions directly. This replaces the polling-based approach previously used.

**Architecture**:
```
Your Mac (Local)
    ↓
Airtable LinkedIn Posts Table
    ↓
Webhook Listener (polling every 30s)
    ↓
Modal Functions (image generation, scheduling)
```

---

## Installation & Running

### 1. Install Dependencies

The listener requires `requests` and `python-dotenv` (already installed):

```bash
pip3 install requests python-dotenv
```

### 2. Start the Listener

**Option A: Run in foreground (for testing)**

```bash
cd "/Users/musacomma/Agentic Workflow"
python3 execution/airtable_linkedin_webhook_listener.py
```

You'll see output like:
```
================================================================================
🚀 AIRTABLE LINKEDIN WEBHOOK LISTENER STARTED
================================================================================
Polling every 30 seconds
API Key: patQCC...
Base ID: appw88uD6ZM0ckF8f
Table ID: tbljg75KMQWDo2Hgu
================================================================================
```

**Option B: Run in background (for production)**

```bash
cd "/Users/musacomma/Agentic Workflow"
nohup python3 execution/airtable_linkedin_webhook_listener.py > /tmp/webhook_listener.log 2>&1 &
echo $! > /tmp/webhook_listener.pid
```

**Option C: Run as macOS Launch Agent (permanent, auto-restart)**

Create `~/Library/LaunchAgents/com.musacomma.webhook-listener.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.musacomma.webhook-listener</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/musacomma/Agentic Workflow/execution/airtable_linkedin_webhook_listener.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/musacomma/Agentic Workflow/logs/webhook_listener_out.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/musacomma/Agentic Workflow/logs/webhook_listener_err.log</string>
    <key>WorkingDirectory</key>
    <string>/Users/musacomma/Agentic Workflow</string>
</dict>
</plist>
```

Then:
```bash
launchctl load ~/Library/LaunchAgents/com.musacomma.webhook-listener.plist
```

### 3. Verify It's Running

```bash
# Check if process is running
pgrep -f airtable_linkedin_webhook_listener

# View logs (if using background/launch agent)
tail -f "/Users/musacomma/Agentic Workflow/logs/airtable_linkedin_listener.log"

# Check for recent status changes
tail -f "/Users/musacomma/Agentic Workflow/logs/airtable_linkedin_listener.log" | grep "STATUS CHANGE"
```

---

## How It Works

### Status Triggers

When you change a post's status in Airtable:

1. **Draft → Pending Review**
   - Listener detects change (within 30 seconds)
   - Calls Modal `generate_images_for_post()` function
   - Images generated and saved to Airtable

2. **Pending Review → Approved - Ready to Schedule**
   - Listener detects change
   - Calls Modal `schedule_approved_post()` function
   - Also runs `check_and_fix_scheduling_issues()`
   - Post scheduled for LinkedIn publishing

3. **Any Status → Rejected**
   - Listener detects change
   - Calls Modal `handle_rejected_post()` function
   - Record cleaned up

### Cooldown System

To prevent duplicate processing, the listener has a **5-minute cooldown** per record/status combination. If you change a status and Modal doesn't respond:

- Wait 5 minutes before trying again
- OR manually delete the log entry for that record (stored in-memory)

---

## Stopping the Listener

**If running in foreground:**
- Press `Ctrl+C`

**If running in background (nohup):**
```bash
kill $(cat /tmp/webhook_listener.pid)
```

**If running as Launch Agent:**
```bash
launchctl unload ~/Library/LaunchAgents/com.musacomma.webhook-listener.plist
```

---

## Logs

Logs are stored in:
```
/Users/musacomma/Agentic Workflow/logs/airtable_linkedin_listener.log
```

Example log output:
```
2026-01-10 22:22:24 - INFO - 🚀 AIRTABLE LINKEDIN WEBHOOK LISTENER STARTED
2026-01-10 22:22:24 - INFO - Polling every 30 seconds
2026-01-10 22:22:24 - INFO - Fetched 6 records from Airtable
2026-01-10 22:22:24 - INFO - No status changes detected

2026-01-10 22:22:54 - INFO - 🔔 STATUS CHANGE DETECTED:
2026-01-10 22:22:54 - INFO -    Record: recXXXXXXXX
2026-01-10 22:22:54 - INFO -    Old:    Draft
2026-01-10 22:22:54 - INFO -    New:    Pending Review
2026-01-10 22:22:54 - INFO - 📌 Status change: recXXXXXXXX → Pending Review
2026-01-10 22:22:54 - INFO -   ↳ Triggering image generation...
2026-01-10 22:22:54 - INFO - Calling Modal function: handle_webhook(recXXXXXXXX, Pending Review)
2026-01-10 22:22:54 - INFO - ✓ Modal function executed: {'success': True, ...}
```

---

## Limitations & Notes

### Current Limitations

1. **Polling-based, not event-driven** (30-second latency)
   - Changes in Airtable take up to 30 seconds to trigger Modal
   - This is acceptable for LinkedIn post generation (typically async process anyway)

2. **Mac must stay running**
   - The polling server runs on your local machine
   - If your Mac sleeps/shuts down, polling stops
   - **Solution**: Use Launch Agent to auto-restart on reboot

3. **No mobile triggering**
   - Can't trigger from your phone (would need to deploy server to cloud)
   - As user mentioned, this is acceptable for now

### Future Improvements

- Deploy to Heroku/Railway to eliminate Mac requirement (~$10-15/month)
- Upgrade Airtable to paid tier for true native webhooks ($20+/month)
- Use AWS Lambda + API Gateway for serverless solution

---

## Troubleshooting

### Listener not detecting changes

1. **Check if it's running:**
   ```bash
   pgrep -f airtable_linkedin_webhook_listener
   ```

2. **Check logs for errors:**
   ```bash
   tail -f "/Users/musacomma/Agentic Workflow/logs/airtable_linkedin_listener.log"
   ```

3. **Verify Airtable API key is valid:**
   ```bash
   curl -H "Authorization: Bearer $AIRTABLE_API_KEY" \
     https://api.airtable.com/v0/appw88uD6ZM0ckF8f/tbljg75KMQWDo2Hgu?maxRecords=1
   ```

### Modal not receiving call

- Check that Modal is deployed: `modal app list`
- Verify function name in listener matches Modal (should be "handle_webhook")
- Check Modal logs: `modal logs linkedin-automation --tail 50`

### Cooldown preventing retry

The listener has a 5-minute cooldown to prevent duplicate processing. If you want to retry immediately:

1. Stop the listener
2. Restart it (clears in-memory state)
3. Change status again

---

## Next Steps

1. **Test the listener:**
   ```bash
   cd "/Users/musacomma/Agentic Workflow"
   python3 execution/airtable_linkedin_webhook_listener.py
   ```

2. **In Airtable, change a post status to test** (e.g., Draft → Pending Review)

3. **Watch the logs** to confirm it triggers Modal

4. **Set up Launch Agent** for permanent auto-starting

---

## Architecture Summary

**Old Setup** (Removed):
```
Modal Scheduled Task (every 5 seconds) → Polls Airtable → Triggers functions
```

**New Setup**:
```
Local Listener (every 30 seconds) → Polls Airtable → Calls Modal Functions
```

**Advantages**:
- ✅ No Modal compute time wasted on polling
- ✅ Clear separation: Modal = execution, Local = monitoring
- ✅ Cheaper Modal usage (no continuous scheduled tasks)
- ✅ Can restart listener without affecting Modal deployment

**Tradeoffs**:
- ⏱️ 30-second latency (vs 5 seconds in old setup)
- 💻 Mac must be running (deployment can fix this)
