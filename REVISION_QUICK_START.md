# Content Revision - Quick Start Guide

**In 60 seconds:** How to revise a post

---

## 1. Start the Revision Server (First Time Only)

```bash
cd "/Users/musacomma/Agentic Workflow"
python3 linkedin_automation/execution/webhook_revise.py
```

**You should see:**
```
Starting server on http://localhost:5050
```

**Leave this running** - it processes revisions automatically.

---

## 2. Go to Airtable

Open your LinkedIn automation Airtable:
- Find the post you want to revise
- Look at the **Content** field (the post text)

---

## 3. Add Your Feedback

Click the **Revision Prompt** field and type what you want changed:

### Examples - Post Changes:
```
"Make this shorter"
"More casual tone"
"Add a specific example"
"Focus on the time saved"
"Simplify the technical language"
"Make it punchier"
```

### Examples - Image Changes:
```
"New image"
"Different visual - more people collaboration"
"Change the image to show a team"
"Update image to be more dynamic"
"Regenerate image with different style"
```

### Examples - Both:
```
"Rewrite shorter and new image"
"Change tone to casual and update visual"
"Simplify text and change image to show team working"
```

---

## 4. Click the Revise Button

In Airtable, there's a **Revise** button that looks like it says "http://localhost:5050/revise/..."

Click it. That's it.

---

## 5. Check Back in 30-60 Seconds

The system will:
- ✓ Read your feedback
- ✓ Detect if you want post changes, image changes, or both
- ✓ Regenerate post (if requested) using Claude
- ✓ Regenerate image prompt (if requested) using Claude
- ✓ Generate new image from revised prompt (if requested)
- ✓ Replace old content/image with new versions
- ✓ Clear the Revision Prompt field
- ✓ Log what changed in the Notes field

**New content appears in the Content field. New image appears in the Image field.**

---

## What You Can Ask For

✓ Length changes ("shorter", "expand this")
✓ Tone changes ("more casual", "professional")
✓ Focus changes ("emphasize ROI", "add examples")
✓ Format changes ("bullet points", "storytelling")
✓ Audience changes ("for beginners", "for experts")

---

## What NOT to Do

❌ Change the post while it's being revised
❌ Click the button multiple times rapidly
❌ Edit the Content field manually (revision will overwrite it)

---

## Multiple Revisions in a Row

Want to make multiple changes?

**Option 1: One at a time**
1. Add Revision Prompt: "Make it shorter"
2. Click Revise button
3. When done, add next Revision Prompt: "More casual"
4. Click Revise button again

**Option 2: All at once**
1. Add Revision Prompt: "Make it shorter, more casual, add an example"
2. Click Revise button
3. Done

---

## If Server Stops

If revisions stop working:

```bash
# Kill the old server
pkill -f webhook_revise.py

# Start a new one
python3 linkedin_automation/execution/webhook_revise.py
```

---

## Batch Process Multiple Posts

To revise all posts with feedback at once:

```bash
python3 linkedin_automation/execution/webhook_revise_automation.py
```

This processes every post that has a Revision Prompt filled in.

---

## That's It!

```
Revision Prompt → Click Button → 30 seconds → New Content
```

Done.

---

**More details:** Read `CONTENT_REVISION_SYSTEM.md`
**Having issues?** Check server is running on `localhost:5050`
