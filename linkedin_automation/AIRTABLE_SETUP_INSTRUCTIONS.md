# Airtable Column & Button Setup Instructions

## Required Columns in Your LinkedIn Posts Table

Your Airtable table needs these columns configured:

### 1. **Revision Prompt** (Long text field)
- **Type:** Long text
- **Purpose:** Where you type revision instructions
- **Example:** "Make this more professional and add a CTA"

### 2. **Notes** (Long text field)  
- **Type:** Long text
- **Purpose:** Auto-populated log of what was changed
- **Example:** "✅ Revised post on 2025-12-05 2:30 PM\nPrompt: Make this more professional"

### 3. **Other existing columns:**
- Post (Long text)
- Image URL (URL)
- Image Prompt (Long text)
- Status (Single select)
- Scheduled Date (Date)
- etc.

---

## How to Add the Revision Prompt Column

1. **Go to your LinkedIn Posts table in Airtable**

2. **Click the `+` button** at the top right to add a new field

3. **Select "Long text"** as the field type

4. **Name it:** `Revision Prompt`

5. **Click "Create field"**

---

## How to Configure the Regenerate Button

### Step 1: Add Button Field

1. **Click the `+` button** again to add another field

2. **Select "Button"** as the field type

3. **Configure the button:**
   - **Field name:** `Revise Content`
   - **Button label:** `🔄 Regenerate`
   - **Action:** Select **"Open URL"**

### Step 2: Set the URL Formula

In the URL field, paste this exact formula:

```
CONCATENATE("http://localhost:5050/revise/", RECORD_ID())
```

**Important:** Make sure you use `RECORD_ID()` not `record_id()`

### Step 3: Save

Click **"Create field"** or **"Save"**

---

## Final Table Structure

Your table should look like this:

```
| Post | Image URL | Status | Revision Prompt | Notes | Revise Content |
|------|-----------|--------|-----------------|-------|----------------|
| "AI automation..." | img.jpg | Awaiting Approval | Make more urgent | | [🔄 Regenerate] |
```

---

## How the Workflow Works

### Before Revision:
```
Revision Prompt: "Make this more professional and add statistics"
Notes: [empty]
```

### Click 🔄 Regenerate Button

### After Revision:
```
Revision Prompt: [cleared - empty]
Notes: "✅ Revised post on 2025-12-05 2:30 PM
        Prompt: Make this more professional and add statistics"
```

The system:
1. ✅ Reads your **Revision Prompt**
2. ✅ Regenerates content with Claude Opus 4.5
3. ✅ Updates the **Post** and/or **Image URL**
4. ✅ Clears the **Revision Prompt**
5. ✅ Logs what changed in **Notes**

---

## Testing Your Setup

### 1. Start the webhook server (if not already running):
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
```

### 2. In Airtable:
- Find any existing post record
- Type in **Revision Prompt:** `"Make this test post shorter"`
- Click the **🔄 Regenerate** button

### 3. Check results:
- The button should open a URL briefly (showing success message)
- **Revision Prompt** field should be cleared
- **Notes** field should show: "✅ Revised post on [timestamp]..."
- **Post** field should have new content

---

## Troubleshooting

**Button doesn't work:**
- ✅ Verify webhook server is running
- ✅ Check the URL formula is exactly: `CONCATENATE("http://localhost:5050/revise/", RECORD_ID())`
- ✅ Make sure there's content in **Revision Prompt**

**Nothing happens when clicking:**
- ✅ Look at the webhook server terminal for errors
- ✅ Verify the **Revision Prompt** column exists and has content
- ✅ Check Status isn't "Posted" (posted records are skipped)

**Notes field doesn't update:**
- ✅ Make sure you have a "Notes" column (not "Note" or "notes")
- ✅ Check the column type is Long text

---

## Column Name Requirements

The webhook code expects these **exact** column names:
- `Revision Prompt` (not "RevisionPrompt" or "Revision_Prompt")
- `Notes` (not "Note" or "notes")
- `Post` 
- `Image URL`
- `Status`

If your columns have different names, let me know and I'll update the code.

---

## Summary

**What you need to do in Airtable:**
1. ✅ Add "Revision Prompt" column (Long text)
2. ✅ Verify "Notes" column exists (Long text)
3. ✅ Add "Revise Content" button with URL formula
4. ✅ Test it!

**What the system does automatically:**
1. ✅ Reads Revision Prompt
2. ✅ Regenerates content
3. ✅ Clears Revision Prompt
4. ✅ Logs changes in Notes

You're ready to go! 🚀
