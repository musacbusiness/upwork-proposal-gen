# Quick Start: Polling Trigger (5 Minutes)

## The Goal

Whenever you change a post's status in Airtable, automatically trigger Modal functions **without manually running commands**.

## Prerequisites

✅ Modal app deployed
✅ Airtable schema configured
✅ Flask server script ready
✅ Polling script ready

All done! Just need to run them.

---

## Step 1: Start Flask Server (2 minutes)

Open a terminal and run:

```bash
cd /Users/musacomma/Agentic\ Workflow
python3 airtable_webhook_server.py
```

You should see:
```
============================================================
🚀 Airtable Webhook Server Starting
============================================================

✅ Server will run on: http://localhost:8000
📋 Configure Airtable Automations:
   ...
```

**Leave this running.** Keep the terminal window open.

---

## Step 2: Start Polling Trigger (1 minute)

Open a **NEW terminal window** and run:

```bash
cd /Users/musacomma/Agentic\ Workflow
python3 polling_trigger.py
```

You should see:
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

**Leave this running too.** Keep both terminal windows open.

---

## Step 3: Test It (2 minutes)

### 3A: Open Your Airtable Table

Go to your table: [https://airtable.com/appw88uD6ZM0ckF8f/tbljg75KMQWDo2Hgu](https://airtable.com/appw88uD6ZM0ckF8f/tbljg75KMQWDo2Hgu)

### 3B: Change a Post's Status

Pick any post and change its status to:
- `Pending Review` (triggers image generation)
- `Approved - Ready to Schedule` (triggers scheduling)
- `Rejected` (triggers rejection handling)

Example: Change "Your Team Is Already Using AI" from `Draft` to `Pending Review`

### 3C: Watch the Magic Happen

Look at the **polling terminal window**. You should see:

```
📢 DETECTED 1 CHANGE(S):

  Record: rec036I0Bjg8HT2Cu
  Title: Your Team Is Already Using AI...
  Status: Draft → Pending Review
  ✅ Triggered!
```

Then look at the **Flask terminal window**. You should see:

```
127.0.0.1 - - [25/Dec/2025 14:15:30] "POST /webhook HTTP/1.1" 200 -
```

Then **check your Airtable**. Wait 30-60 seconds and refresh:
- `Image URL` field should be populated
- `Image Generated At` timestamp should appear

**🎉 It worked!**

---

## What's Happening Behind the Scenes

```
Airtable (Status changed)
    ↓
Polling Script (Checks every 30 seconds)
    ↓
Detects change
    ↓
Calls Flask Webhook
    ↓
Flask calls Modal
    ↓
Modal generates image
    ↓
Airtable updated with image URL
```

---

## Verify Everything is Working

Check the log file to confirm:

```bash
tail -f /Users/musacomma/Agentic\ Workflow/polling_trigger.log
```

You should see entries like:
```
2025-12-25 14:12:04,936 - __main__ - INFO - Triggering: rec036I0Bjg8HT2Cu → Pending Review
2025-12-25 14:12:04,936 - __main__ - INFO - Triggering Modal function: rec036I0Bjg8HT2Cu → Pending Review
```

---

## Test All Three Workflows

### Test 1: Image Generation ✅

1. Change any post to `Pending Review`
2. Wait 30-60 seconds
3. Check Airtable - image URL appears

### Test 2: Post Scheduling ✅

1. Change the same post to `Approved - Ready to Schedule`
2. Wait 5 seconds
3. Check Airtable:
   - Status changes to `Scheduled`
   - `Scheduled Time` gets a value
   - `Scheduled At` gets a timestamp

### Test 3: Rejection Handling ✅

1. Create a new test post or change another one
2. Set status to `Rejected`
3. Wait 5 seconds
4. Check Airtable - `Scheduled Deletion Date` is 24 hours from now

---

## Common Questions

### Q: Do I have to keep both terminals open?
**A:** Yes, for now. Both processes need to run continuously.
- Flask server: Receives webhook calls
- Polling script: Detects changes

### Q: How often does it check?
**A:** Every 30 seconds (default). You can change it:
```bash
python3 polling_trigger.py --interval 10  # Every 10 seconds
python3 polling_trigger.py --interval 60  # Every 60 seconds
```

### Q: What if my Mac sleeps?
**A:** Polling stops. Keep your Mac awake or set up auto-start (see POLLING_SETUP_GUIDE.md)

### Q: Does it work remotely?
**A:** Only if your Mac is on and polling is running. For 24/7 triggering, deploy to a server.

### Q: Is the 30-second delay a problem?
**A:** No! LinkedIn posts don't care. You approve a post, 30 seconds later it's scheduled. Perfect.

### Q: Can I make it faster?
**A:** Yes, use shorter intervals:
```bash
python3 polling_trigger.py --interval 5  # Every 5 seconds (more aggressive)
```

### Q: What if I want instant triggering?
**A:** Use Zapier/Make.com instead ($29/month). Or use Airtable Scripts (if you have Pro+).

---

## Next Steps

### Right Now
1. ✅ Keep both terminals running
2. ✅ Test the three workflows above
3. ✅ Verify everything works

### Next (Optional - For 24/7 Automation)

If you want this to run automatically even when you're not looking:

```bash
# Option A: Use tmux (keeps it running in background)
tmux new-session -d -s polling "python3 polling_trigger.py"

# Option B: Use launchctl (auto-starts on Mac reboot)
# See POLLING_SETUP_GUIDE.md for details
```

### Tomorrow
- Change post statuses in Airtable normally
- Polling will detect and trigger automatically
- Images generate, posts schedule, cleanup happens automatically

---

## Troubleshooting

### "Could not connect to webhook server"
**Solution:** Make sure Flask server is running in the other terminal

### "No changes detected"
**Solution:** Make sure status value exactly matches:
- `Pending Review` (not "pending review")
- `Approved - Ready to Schedule` (with hyphens)
- `Rejected`

### "Nothing happens when I change status"
1. Check polling terminal - does it say "DETECTED CHANGE"?
2. Check Flask terminal - does it show POST request?
3. Check Airtable - did the status actually change?

---

## Success Criteria ✅

You're done when:
- [ ] Flask server is running and accepting requests
- [ ] Polling script is running and checking Airtable
- [ ] You can change a post's status in Airtable
- [ ] Polling detects the change within 30 seconds
- [ ] Modal function is triggered automatically
- [ ] Airtable is updated with results (image URL, scheduled time, etc.)

---

## That's It! 🎉

You now have **fully automatic triggering** without any manual commands.

Every time you change a post's status in Airtable, the system automatically:
1. Generates images (if Pending Review)
2. Schedules posts (if Approved)
3. Handles rejections (if Rejected)
4. Cleans up old posts (automatically)

All without you lifting a finger. ✅

---

## One More Thing

Want it to run 24/7 even when your Mac is off?

Deploy to a server:
- **Heroku** (easiest, free tier ending)
- **Railway** ($5/month)
- **Render** ($7/month)
- **AWS** (essentially free)

Or keep it local on your Mac using launchctl (see POLLING_SETUP_GUIDE.md).

---

**You're all set! Go change some post statuses and watch the magic happen.** ✨
