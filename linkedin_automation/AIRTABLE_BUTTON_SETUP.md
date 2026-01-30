# Airtable Button Setup for One-Click Revisions

Add a button to your Airtable that triggers revisions instantly without running terminal commands.

## Setup Steps

### 1. Install Flask (if not already installed)

```bash
cd "/Users/musacomma/Agentic Workflow/linkedin_automation"
pip3 install flask
```

### 2. Start the Webhook Server

Open a terminal and run:

```bash
cd "/Users/musacomma/Agentic Workflow/linkedin_automation/execution"
python3 webhook_revise.py
```

You should see:
```
============================================================
LinkedIn Revision Webhook Server
============================================================

Starting server on http://localhost:5050

Airtable Button URLs:
  Single record: http://localhost:5050/revise/{record_id}
  All records:   http://localhost:5050/revise-all

Press Ctrl+C to stop
============================================================
```

**Keep this terminal running** while you want the button to work.

---

### 3. Add Button Field to Airtable

1. **Go to your Airtable base** (LinkedIn Posts table)

2. **Add a new field:**
   - Click the `+` button to add a new column
   - Select **"Button"** field type
   - Name it: `Revise Content`

3. **Configure the button:**
   - **Label:** "🔄 Regenerate"
   - **Action:** "Open URL"
   - **URL formula:**
     ```
     CONCATENATE("http://localhost:5050/revise/", RECORD_ID())
     ```

4. **Save the button**

---

### 4. How to Use

**For a single post:**
1. Add revision instructions to the **Notes** column
   - Example: `"Make this more urgent"`
   - Example: `"New image with warmer colors"`
   - Example: `"Regenerate both"`

2. Click the **🔄 Regenerate** button

3. The system will:
   - Read your Notes
   - Regenerate content based on instructions
   - Update the post/image in Airtable
   - Clear the Notes field

---

## Alternative: "Revise All" Button

If you want one button to check ALL records with Notes:

1. Create another Button field: `Revise All Posts`

2. Configure:
   - **Label:** "🔄 Process All Revisions"
   - **Action:** "Open URL"
   - **URL:** `http://localhost:5050/revise-all` (no formula needed)

3. Click this button to process all pending revision requests at once

---

## Running the Server Automatically

### Option A: Keep Terminal Open
Just leave the `webhook_revise.py` terminal running in the background.

### Option B: Background Process (macOS)

Create a launch agent:

```bash
# Create plist file
nano ~/Library/LaunchAgents/com.linkedin.revision.plist
```

Add this content:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.linkedin.revision</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/Users/musacomma/Agentic Workflow/linkedin_automation/execution/webhook_revise.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/musacomma/Agentic Workflow/linkedin_automation/logs/webhook.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/musacomma/Agentic Workflow/linkedin_automation/logs/webhook_error.log</string>
</dict>
</plist>
```

Load the service:
```bash
launchctl load ~/Library/LaunchAgents/com.linkedin.revision.plist
```

Now it runs automatically on startup!

---

## Troubleshooting

**Button doesn't work:**
- ✅ Check webhook server is running (`python3 webhook_revise.py`)
- ✅ Verify URL in button: `http://localhost:5050/revise/{RECORD_ID()}`
- ✅ Make sure Notes field has content

**"Connection refused" error:**
- Server isn't running - start it with `python3 webhook_revise.py`

**Nothing happens when clicking button:**
- Check server logs in the terminal
- Verify Notes field has revision instructions

**Want to stop the server:**
- Press `Ctrl+C` in the terminal running webhook_revise.py

---

## Security Note

This webhook runs on **localhost only** (127.0.0.1), meaning it's only accessible from your computer. This is secure for personal use.

If you need to access it from other devices (iPad, phone), you'd need to:
1. Use your computer's local IP instead of localhost
2. Add authentication to the webhook
3. Consider using a service like ngrok for secure tunneling

---

## Summary

**Before:** Type notes → Open terminal → Run `python3 RUN_linkedin_automation.py --action revise`

**After:** Type notes → Click 🔄 button → Done!

The webhook makes revisions instant and simple.
