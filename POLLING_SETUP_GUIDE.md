# Polling Trigger Setup Guide

## What is Polling?

Instead of waiting for webhooks to fire, the polling trigger **continuously scans your Airtable** for status changes and automatically triggers Modal functions.

**How it works:**
1. Checks your Airtable records every 30 seconds (configurable)
2. Compares current status to previous status
3. If status changed to a trigger value → automatically calls Modal function
4. Records the new state so it doesn't trigger twice

---

## Advantages Over Webhooks

| Feature | Polling | Webhooks |
|---------|---------|----------|
| Setup complexity | Easy | Complex |
| Reliability | Very high | Depends on webhook config |
| Cost | Free | Free or $29-99/mo |
| Local server required | Yes (Flask) | No (with Zapier) |
| Guaranteed firing | Yes (polls continuously) | Sometimes missed |
| Latency | 30+ seconds | Instant |
| Can run on Mac | Yes | No (needs server) |

---

## Quick Start (5 minutes)

### Step 1: Make Sure Flask Server is Running

```bash
# In one terminal window
python3 airtable_webhook_server.py
```

Output should show:
```
✅ Server will run on: http://localhost:8000
```

### Step 2: Start the Polling Trigger

```bash
# In another terminal window
cd /Users/musacomma/Agentic\ Workflow
python3 polling_trigger.py
```

Output:
```
======================================================================
🚀 LinkedIn Automation Polling Trigger Started
======================================================================
Polling every 30 seconds
Webhook URL: http://localhost:8000/webhook
Base ID: appw88uD6ZM0ckF8f
Table ID: tbljg75KMQWDo2Hgu
======================================================================
```

### Step 3: Test It

Change a post's status in Airtable to one of:
- `Pending Review`
- `Approved - Ready to Schedule`
- `Rejected`

**The polling trigger will:**
1. Detect the change within 30 seconds
2. Automatically trigger the Modal function
3. Log the action

Check the terminal to see:
```
📢 DETECTED 1 CHANGE(S):

  Record: rec036I0Bjg8HT2Cu
  Title: Your Team Is Already Using AI...
  Status: Draft → Pending Review
  ✅ Triggered!
```

---

## Configuration Options

### Change Polling Interval

Poll every 10 seconds (faster response):
```bash
python3 polling_trigger.py --interval 10
```

Poll every 5 minutes (less frequent):
```bash
python3 polling_trigger.py --interval 300
```

Poll every 1 minute (balanced):
```bash
python3 polling_trigger.py --interval 60
```

### Verbose Output

See detailed logs:
```bash
python3 polling_trigger.py --verbose
```

### Use Custom Webhook URL

If you deployed Flask to a server:
```bash
python3 polling_trigger.py --webhook-url "https://your-server.com/webhook"
```

### Run Once (For Cron Jobs)

Check once and exit (useful for scheduling):
```bash
python3 polling_trigger.py --once
```

---

## Running 24/7 on Your Mac

### Option 1: Keep Terminal Open
Simple but requires keeping a terminal window open.

```bash
python3 polling_trigger.py
```

### Option 2: Run in Background with tmux

```bash
# Start in background
tmux new-session -d -s polling "python3 polling_trigger.py"

# View logs
tmux attach-session -s polling

# Stop when done
tmux kill-session -s polling
```

### Option 3: macOS Launch Agent (Recommended)

Create a plist file to auto-start on boot:

**Step 1: Create launch agent**
```bash
mkdir -p ~/Library/LaunchAgents

cat > ~/Library/LaunchAgents/com.linkedin-automation.polling.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.linkedin-automation.polling</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/Users/musacomma/Agentic Workflow/polling_trigger.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/musacomma/Agentic Workflow/polling_trigger.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/musacomma/Agentic Workflow/polling_trigger_error.log</string>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF
```

**Step 2: Load it**
```bash
launchctl load ~/Library/LaunchAgents/com.linkedin-automation.polling.plist
```

**Step 3: Verify it's running**
```bash
launchctl list | grep linkedin
```

**Step 4: View logs**
```bash
tail -f /Users/musacomma/Agentic\ Workflow/polling_trigger.log
```

**To stop:**
```bash
launchctl unload ~/Library/LaunchAgents/com.linkedin-automation.polling.plist
```

### Option 4: Cron Job (Scheduled Polling)

Edit crontab:
```bash
crontab -e
```

Add this line to poll every 5 minutes:
```bash
*/5 * * * * cd /Users/musacomma/Agentic\ Workflow && python3 polling_trigger.py --once >> polling_cron.log 2>&1
```

Or every minute:
```bash
* * * * * cd /Users/musacomma/Agentic\ Workflow && python3 polling_trigger.py --once >> polling_cron.log 2>&1
```

---

## How It Works Internally

### 1. State Tracking

The trigger keeps a file `polling_state.json` that remembers the status of each record:

```json
{
  "rec036I0Bjg8HT2Cu": {
    "title": "Your Team Is Already Using AI...",
    "status": "Pending Review",
    "last_seen": "2025-12-25T08:50:00.123456"
  }
}
```

### 2. Change Detection

When it polls:
1. Fetches current records from Airtable
2. Compares with saved state
3. If status changed AND it's a trigger status → calls webhook

### 3. Avoiding Duplicates

The state file ensures you don't trigger the same status change twice:
- Changes status to "Pending Review" → triggers once ✅
- Status stays "Pending Review" → doesn't trigger again ✅
- Changes to "Approved" → triggers again ✅

---

## Monitoring

### View Live Logs

```bash
# Watch logs in real-time
tail -f /Users/musacomma/Agentic\ Workflow/polling_trigger.log
```

### Check State File

```bash
cat /Users/musacomma/Agentic\ Workflow/polling_state.json | python3 -m json.tool
```

### Restart the Trigger

```bash
# Stop it
# Press Ctrl+C in the terminal

# Start it again
python3 polling_trigger.py
```

---

## Troubleshooting

### Issue: "Could not connect to webhook server"

**Solution:** Make sure Flask server is running:
```bash
# Terminal 1: Start Flask server
python3 airtable_webhook_server.py

# Terminal 2: Start polling (in different window)
python3 polling_trigger.py
```

### Issue: Changes not being detected

**Solution:**
1. Check the status field exactly matches one of:
   - `Pending Review` (not "pending review")
   - `Approved - Ready to Schedule` (with exact spacing)
   - `Rejected`

2. Check logs for errors:
```bash
tail -f polling_trigger.log
```

### Issue: Too many logs, want less verbose

**Remove `--verbose` flag:**
```bash
python3 polling_trigger.py  # (no --verbose)
```

### Issue: Latency is too high (30+ seconds delay)

**Use shorter polling interval:**
```bash
python3 polling_trigger.py --interval 5  # Poll every 5 seconds
```

---

## Comparison: Polling vs. Alternatives

### Polling (This Solution)
✅ Free
✅ Simple to set up
✅ Very reliable
✅ Runs on your Mac
⚠️ 30-second latency
⚠️ Mac must stay on

### Zapier/Make.com
✅ Instant triggering
✅ No local setup
✅ Professional
❌ $29-99/month cost

### Airtable Scripts
✅ Free
✅ Native to Airtable
⚠️ Requires Pro+ plan
⚠️ Complex setup

### AWS Lambda
✅ Free (essentially)
✅ Runs 24/7
❌ Complex setup
❌ More expensive long-term

---

## Why This is Actually Better for You

1. **No subscription cost** - polling is free forever
2. **No external service dependency** - everything runs locally
3. **Guaranteed reliability** - checks continuously
4. **Easy to debug** - see logs in real-time
5. **Easy to pause** - just close the terminal
6. **Can run on any schedule** - via cron or background service

---

## Next Steps

1. **Start the Flask server:**
   ```bash
   python3 airtable_webhook_server.py
   ```

2. **Start the polling trigger:**
   ```bash
   python3 polling_trigger.py
   ```

3. **Change a post's status in Airtable** and watch it trigger automatically!

4. **(Optional) Set up to run 24/7** using tmux, launchctl, or cron

---

## Test Right Now

```bash
# Terminal 1: Start Flask server
python3 airtable_webhook_server.py

# (Open new terminal)

# Terminal 2: Start polling
python3 polling_trigger.py

# (Open Airtable in browser)

# Step 3: Change a post's status to "Pending Review"

# Watch the polling trigger automatically call Modal! 🚀
```

---

**That's it! You now have fully automatic triggering.**

Every time you change a post's status in Airtable, the polling trigger will detect it within seconds and automatically trigger the Modal functions.

No webhooks. No subscriptions. No complexity. Just polling. ✅
