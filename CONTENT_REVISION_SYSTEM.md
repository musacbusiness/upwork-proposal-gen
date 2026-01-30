# Content Revision System - How It Currently Works

**Status:** ✓ Implemented and Ready to Use
**Last Updated:** December 30, 2025

---

## Overview

The content revision system allows you to request changes to generated posts directly from Airtable. You simply add a revision instruction in the "Revision Prompt" field, and the system automatically regenerates the content based on your feedback.

---

## Current Architecture

### Two Implementation Options

#### Option 1: Webhook Server (Currently Used)
**Status:** Active but running locally
**Command:** `python3 linkedin_automation/execution/webhook_revise.py`
**Server:** Runs on `localhost:5050`

**How it works:**
```
You click button in Airtable
↓
Button calls webhook at localhost:5050/revise/{record_id}
↓
Webhook server triggers ContentRevisionProcessor
↓
Processor reads "Revision Prompt" field
↓
AI regenerates content based on feedback
↓
New content replaces old content in Airtable
↓
Image prompt regenerated (if needed)
```

#### Option 2: Automation Script (For Batch Processing)
**File:** `linkedin_automation/execution/webhook_revise_automation.py`
**Use Case:** Process multiple revisions at once

---

## The Airtable Fields

### Required Fields for Revision

| Field | Purpose | Example |
|-------|---------|---------|
| **Content** | Current post text | "The one-line prompt..." |
| **Revision Prompt** | Your feedback/instructions | "Make this shorter and punchier" |
| **Status** | Post status | "Draft", "Pending Review", etc. |

### What Happens

When you add text to "Revision Prompt":
1. System detects the field is not empty
2. Reads your revision request
3. Parses what type of revision (content, tone, length, etc.)
4. Regenerates the post using Claude AI
5. Updates the Content field with new version
6. Optionally regenerates image prompt
7. Clears the Revision Prompt field (ready for next revision)

---

## How to Use It

### Step 1: Find Post to Revise
- Open Airtable
- Find the post you want to revise (in Draft or other status)
- Look at the **Content** field

### Step 2: Add Revision Instructions
- Click the **Revision Prompt** field
- Type your feedback/instructions
- Examples:
  ```
  "Make this post shorter"
  "Change the tone to more casual"
  "Focus more on the ROI aspect"
  "Simplify the technical language"
  "Add a specific example"
  "New image - more dramatic"
  "Change image to team working together"
  "Regenerate both post and image"
  ```

### What Can You Revise?

The system detects what you want revised based on keywords:

**Post-Only Changes** (keywords: rewrite, regenerate post, change post, revise post, edit post, etc.)
```
"Make this shorter" → Only regenerates Content
"More casual tone" → Only regenerates Content
"Add an example" → Only regenerates Content
```

**Image-Only Changes** (keywords: new image, different image, photo, picture, graphic, visual, etc.)
```
"New image" → Only regenerates Image + Image Prompt
"Different visual" → Only regenerates Image + Image Prompt
"More dramatic photo" → Only regenerates Image + Image Prompt
```

**Both Post AND Image Changes** (if you mention both)
```
"Rewrite this shorter with a new image" → Regenerates both Content and Image
"Change the post tone and update the visual" → Regenerates both
```

### Step 3: Trigger Revision

**Option A: Via Webhook Button (Single Post)**
```
Airtable has a button that calls:
http://localhost:5050/revise/{record_id}

The server needs to be running:
python3 linkedin_automation/execution/webhook_revise.py
```

**Option B: Manual Command (Single Post)**
```bash
cd "/Users/musacomma/Agentic Workflow"
python3 -c "
from linkedin_automation.execution.content_revisions import ContentRevisionProcessor
processor = ContentRevisionProcessor()
processor.check_for_revisions(record_ids=['rec6Bh4hUVslhhE8J'])
"
```

**Option C: Batch Process (All Posts with Revisions)**
```bash
python3 linkedin_automation/execution/webhook_revise_automation.py
# Processes all posts with non-empty Revision Prompt field
```

### Step 4: Review New Content
- The system regenerates the post
- New content appears in the **Content** field
- **Revision Prompt** field is cleared
- Image prompt is regenerated if needed

---

## Revision Types Detected

The system can understand different types of revision instructions:

### 1. Length Adjustments
```
"Make this shorter"
"Expand this to 3 paragraphs"
"Shorten the intro"
```
→ Regenerates with different length

### 2. Tone Changes
```
"Make this more casual"
"More professional"
"Less salesy, more educational"
```
→ Adjusts voice and tone

### 3. Content Focus
```
"Focus more on the ROI"
"Emphasize the speed benefit"
"Add more examples"
```
→ Refocuses the message

### 4. Audience Adjustment
```
"Make this for beginners"
"This is for experienced users"
"Simplify for a general audience"
```
→ Adjusts complexity level

### 5. Format Changes
```
"Turn this into 3 key points"
"Make it a story format"
"Use bullet points"
```
→ Restructures the content

---

## The ContentRevisionProcessor

**File:** `linkedin_automation/execution/content_revisions.py` (450+ lines)

### Main Methods

```python
class ContentRevisionProcessor:
    def check_for_revisions(self, record_ids=None) -> int:
        """
        Check Airtable for posts with revision instructions
        Returns: Number of posts revised
        """

    def _parse_revision_type(self, prompt: str) -> str:
        """
        Determine what type of revision is needed
        Returns: 'post', 'image', or 'both'
        """

    def _process_revision(self, record_id, fields, revision_prompt, revision_type) -> bool:
        """
        Actually perform the revision (post, image, or both)
        """

    def _regenerate_post(self, current_fields, instructions) -> str:
        """
        Regenerate post content based on instructions
        Uses Claude API
        """

    def _regenerate_image(self, current_fields, instructions) -> Dict:
        """
        Regenerate image based on instructions
        1. Revises the image prompt using Claude
        2. Generates new image from revised prompt
        3. Returns image URL + new prompt
        """

    def _update_post_content(self, record_id, new_content) -> bool:
        """Update Content field in Airtable"""

    def _update_image(self, record_id, image_data) -> bool:
        """Update Image + Image URL + Image Prompt fields"""

    def _generate_change_summary(self, ...) -> str:
        """
        Generate human-readable summary of what changed
        Uses Claude to compare old vs new
        """
```

### How It Works

1. **Detection:**
   ```
   Looks for: {Revision Prompt} != '' AND {Status} != 'Posted'
   Skips: Posted posts (don't revise what's already live)
   ```

2. **Parsing Revision Type:**
   ```
   Reads revision prompt keywords:

   'post' keywords: rewrite, regenerate post, change post, edit post, etc.
   'image' keywords: new image, different image, photo, picture, graphic, visual, etc.

   Returns: 'post', 'image', or 'both'
   ```

3. **Post Regeneration** (if needed):
   ```
   Calls Claude with:
   - Current post content
   - User's revision instruction
   - Your voice profile for consistency

   Returns: New post text
   ```

4. **Image Regeneration** (if needed):
   ```
   Step A: Revise the image prompt
   ├─ Call Claude with:
   │  - Current image prompt
   │  - Post content (for context)
   │  - User's image revision instruction
   │  └─ Returns: New image prompt

   Step B: Generate new image
   ├─ Call Replicate with new prompt
   └─ Returns: Image URL + prompt
   ```

5. **Update Airtable:**
   ```
   If post revised:
   ├─ Update Content field with new post
   ├─ Update Image Prompt field (auto-revision)
   └─ Generate new image from revised prompt

   If image revised:
   ├─ Update Image field with new image
   ├─ Update Image URL field
   └─ Update Image Prompt field

   Always:
   ├─ Clear Revision Prompt field
   ├─ Log changes in Notes field
   └─ Generate change summary (what changed)
   ```

### Image Revision Details

**How Image Revision Works:**

When you ask for image changes, the system:

1. **Parses Your Request**
   - Detects image-related keywords: "new image", "change photo", "different visual", etc.
   - Or combined with post changes: "rewrite and new image"

2. **Revises the Image Prompt**
   - Calls Claude with current prompt + your instruction
   - Claude generates new image description
   - Example:
     ```
     Current: "Professional workspace, laptop, modern desk setup"
     Your request: "More dynamic, people collaborating"
     New: "Team of professionals collaborating at modern workspace,
            high energy, engaged discussion, natural lighting"
     ```

3. **Generates New Image**
   - Calls image generator (Replicate) with new prompt
   - Image generator creates new image
   - Retrieves image URL

4. **Updates Everything**
   - Replaces Image field with new image
   - Updates Image URL field
   - Updates Image Prompt field with new description
   - Logs the change in Notes

---

## Current Setup in Modal

The new Modal system (`cloud/modal_linkedin_automation.py`) doesn't yet include revision handling, but it's possible to add it.

### What's Available Now:
- ✓ Initial post generation
- ✓ Image generation
- ✓ Scheduling
- ✓ Posting to LinkedIn
- ✓ Deletion management

### What's Not Yet in Modal:
- ❌ Revision via Modal webhooks
- ❌ Revision via Airtable automation
- ❌ Real-time revision detection

---

## How to Migrate Revisions to Modal

If you want revisions to run in Modal instead of locally:

### Option 1: Add Revision Function to Modal
```python
@app.function(image=image, secrets=[modal.Secret.from_name("linkedin-secrets")], timeout=300)
def revise_post(record_id: str, base_id: str, table_id: str, revision_prompt: str):
    """
    Process a revision request for a post
    """
    # Read post from Airtable
    # Regenerate content based on revision_prompt
    # Update Airtable
    # Regenerate image
    pass
```

### Option 2: Add Periodic Revision Check
```python
@app.function(image=image, secrets=[modal.Secret.from_name("linkedin-secrets")])
def check_for_pending_revisions():
    """
    Check for all posts with Revision Prompt field populated
    Process them automatically
    """
    pass
```

---

## Local Webhook Setup (Current)

### Start the Server
```bash
cd "/Users/musacomma/Agentic Workflow"
python3 linkedin_automation/execution/webhook_revise.py
```

**Output:**
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

### Airtable Button Configuration

**Button URL Formula:**
```
CONCATENATE("http://localhost:5050/revise/", RECORD_ID())
```

### Endpoints Available

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/revise/{record_id}` | GET/POST | Revise single post |
| `/revise-all` | GET/POST | Check all posts for revisions |
| `/health` | GET | Health check |

---

## Example Workflow

### Scenario: Post Is Too Long

**Current post:**
```
"The one-line prompt that unlocked 60% better AI outputs

Real story about adding one clarifying question line to prompts,
resulting in 60% better outputs. Grounds the technique in actual
testing (6 weeks of tracking). Direct, practical tone with specific
examples (marketing, job description, sales email).

Key Message: 'Treat AI like a smart colleague who needs context,
not a vending machine'"
```

**Your feedback:**
```
Revision Prompt: "Make this post 50% shorter and more punchy"
```

**System does:**
1. Detects non-empty Revision Prompt
2. Parses "shorter and more punchy"
3. Calls Claude:
   ```
   Current post: [above]
   Revision: Make this 50% shorter and more punchy
   Voice: Direct, blunt, no corporate speak

   Generate revised post
   ```
4. Receives new version:
   ```
   "The one-line prompt that unlocked 60% better outputs

   I spent 6 weeks testing this: one clarifying line in your
   prompt = 60% better results.

   Treat AI like a contractor. Give it context, not commands."
   ```
5. Updates Airtable Content field
6. Clears Revision Prompt field
7. Regenerates image prompt

**Result:** Post is shorter, punchier, ready to review

---

## Files Involved

### Legacy System (Currently Active)
```
linkedin_automation/execution/
├── content_revisions.py          ← Core revision logic
├── webhook_revise.py             ← Webhook server
└── webhook_revise_automation.py  ← Batch processing
```

### Documentation
```
linkedin_automation/
├── AIRTABLE_AUTOMATION_SETUP.md  ← Setup guide
├── FREE_TIER_AUTOMATION.md       ← Free tier options
└── MODAL_MIGRATION_GUIDE.md      ← Migration notes
```

---

## Limitations

### Current
- Server must be running locally on port 5050
- Mac must be online for webhook to work
- No Modal integration yet
- Manual endpoint triggering

### Potential Issues
- If server crashes, no revisions until restarted
- Webhook blocks if Anthropic API is slow
- No queue system for multiple simultaneous revisions
- No revision history tracking

---

## Cost Optimization

Each revision costs:
- 1 Claude API call (content regeneration)
- 1 Image generation API call (optional, if image regenerated)

**Estimate:** ~$0.02 per revision for content only

---

## Next Steps (Recommendations)

### To Keep Using Current System:
```bash
# 1. Start webhook server
python3 linkedin_automation/execution/webhook_revise.py

# 2. In Airtable, add Revision Prompt and click the button
# 3. Server processes revision automatically
```

### To Migrate to Modal:
```bash
# Option A: Add revision function to cloud/modal_linkedin_automation.py
# Option B: Create new Modal app just for revisions
# Option C: Keep local for revisions, Modal for generation/posting
```

### To Add Monitoring:
```bash
# Create dashboard showing:
# - Revisions processed
# - Average revision time
# - Success rate
# - API costs per revision
```

---

## Summary

**Current Status:** Fully implemented and functional
**How to Use:** Add feedback to Revision Prompt field → Click button → Done
**Cost:** ~$0.02 per revision
**Latency:** 30-60 seconds per revision
**Quality:** Uses your voice profile for consistency

The system is ready to use. Just start the webhook server and begin revising!

---

**Location:** `linkedin_automation/execution/content_revisions.py`
**Server:** `linkedin_automation/execution/webhook_revise.py`
**Status:** ✓ READY TO USE
