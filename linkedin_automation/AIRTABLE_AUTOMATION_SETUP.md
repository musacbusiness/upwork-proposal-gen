# Airtable Automation Setup - Zero-Click Revisions

Set up Airtable to automatically trigger revisions when you check a box - no button clicking needed!

---

## Option 1: Checkbox Trigger (Recommended - Easiest)

### Step 1: Add Checkbox Field

1. Go to your LinkedIn Posts table
2. Add new field → **Checkbox** type
3. Name: `Process Revision`

### Step 2: Create Airtable Automation

1. **Click "Automations"** at the top of Airtable
2. **Create custom automation**
3. **Trigger:** "When record matches conditions"
   - **Table:** LinkedIn Posts
   - **Condition:** `Process Revision` is `checked`
   - **AND** `Revision Prompt` is not empty

4. **Action:** "Run script"
5. **Paste this script:**

```javascript
let config = input.config();
let recordId = config.recordId;

// Call the webhook
let response = await fetch('http://localhost:5050/automation/revise', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        record_id: recordId
    })
});

let result = await response.json();
console.log('Revision result:', result);

// Uncheck the box after processing
let table = base.getTable('LinkedIn Posts');
await table.updateRecordAsync(recordId, {
    'Process Revision': false
});

output.set('result', result);
```

6. **Configure input variables:**
   - Click "Add" next to Input variables
   - Variable name: `recordId`
   - Value: Select "Record ID" from the trigger

7. **Save & Turn on** the automation

### How It Works:

**You:**
1. Type in `Revision Prompt`: "Make this more urgent"
2. Check the `Process Revision` box

**System automatically:**
1. ✅ Triggers webhook
2. ✅ Regenerates content
3. ✅ Updates post/image
4. ✅ Clears Revision Prompt
5. ✅ Logs to Notes
6. ✅ Unchecks the box

**You never click anything else!**

---

## Option 2: Watch for Revision Prompt Changes

Even more automatic - triggers whenever you add text to Revision Prompt:

### Automation Setup:

1. **Trigger:** "When record updated"
   - **Table:** LinkedIn Posts
   - **Field:** `Revision Prompt`
   - **Condition:** When field is not empty

2. **Action:** Same script as Option 1

### How It Works:

**You:**
- Just type in `Revision Prompt`: "Make this shorter"
- Press Enter or tab away

**System automatically:**
- ✅ Detects the change
- ✅ Triggers revision
- ✅ Processes everything
- ✅ Clears prompt and logs to Notes

**Zero extra clicks!**

---

## Option 3: Scheduled Batch Processing

Process all pending revisions at once every 15 minutes:

### Automation Setup:

1. **Trigger:** "At scheduled time"
   - **Interval:** Every 15 minutes

2. **Action:** "Find records"
   - **Table:** LinkedIn Posts
   - **Condition:** `Revision Prompt` is not empty
   - **AND** `Status` is not "Posted"

3. **Action:** "Run script"

```javascript
let recordIds = input.config().recordIds;

// Process all records at once
let response = await fetch('http://localhost:5050/revise-all', {
    method: 'POST'
});

let result = await response.json();
console.log('Batch revision result:', result);
output.set('result', result);
```

### How It Works:

**You:**
- Add revision prompts whenever you want
- Do other work

**Every 15 minutes:**
- ✅ System checks for pending revisions
- ✅ Processes all of them
- ✅ Updates everything

---

## Option 4: Advanced - Webhook with Ngrok (Access from Anywhere)

If you want to use Airtable from iPad/phone or outside your network:

### Step 1: Install Ngrok

```bash
brew install ngrok
```

### Step 2: Start Ngrok Tunnel

```bash
ngrok http 5050
```

You'll see:
```
Forwarding    https://abc123.ngrok.io -> http://localhost:5050
```

### Step 3: Update Button/Automation URLs

Replace `http://localhost:5050` with your ngrok URL:
```
Button: CONCATENATE("https://abc123.ngrok.io/revise/", RECORD_ID())
Automation: https://abc123.ngrok.io/automation/revise
```

**Now it works from anywhere!** (Phone, tablet, other computer)

---

## Comparison Table

| Method | Setup Difficulty | Speed | Use Case |
|--------|-----------------|-------|----------|
| **Button** | Easy | Instant | Manual control, one-at-a-time |
| **Checkbox** | Medium | Instant | Visual confirmation, checkbox to trigger |
| **Auto on Change** | Medium | Instant | Fully automatic, type and forget |
| **Scheduled Batch** | Medium | Every 15min | Batch processing, set it and forget it |
| **Ngrok** | Advanced | Instant | Mobile/remote access |

---

## My Recommendation:

**Start with Option 1 (Checkbox)** because:
- ✅ Easy visual confirmation (check the box when ready)
- ✅ Won't accidentally trigger on typos
- ✅ You control exactly when it processes
- ✅ Simple to understand and debug

**Later upgrade to Option 2** (Auto on change) once you're comfortable with the system.

---

## Testing Your Automation

### 1. Start enhanced webhook server:

```bash
cd "/Users/musacomma/Agentic Workflow/linkedin_automation/execution"
python3 webhook_revise_automation.py
```

### 2. In Airtable:
- Add revision prompt: "Make this test post shorter"
- Check the "Process Revision" box (if using Option 1)
- Or just press Enter (if using Option 2)

### 3. Watch it work:
- Checkbox unchecks automatically
- Revision Prompt clears
- Notes shows log
- Post updates

---

## Troubleshooting

**Automation doesn't trigger:**
- ✅ Make sure automation is turned ON (toggle at top)
- ✅ Check webhook server is running
- ✅ Verify field names match exactly
- ✅ Check Airtable automation run history for errors

**"localhost refused connection":**
- ✅ Webhook server isn't running - start it
- ✅ Use ngrok if accessing from different device

**Script fails:**
- ✅ Check run history in Airtable automations
- ✅ Verify input variable `recordId` is configured
- ✅ Look at webhook server logs

---

## Summary

**Without automation:** Type prompt → Click button → Done

**With checkbox automation:** Type prompt → Check box → Done (box unchecks itself)

**With auto-trigger:** Type prompt → [Press Enter] → Done (completely automatic)

Choose what feels most comfortable for your workflow! 🚀
