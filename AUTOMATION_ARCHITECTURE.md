# LinkedIn Post Automation Architecture

## System Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         AUTOMATION ORCHESTRATOR                              │
│                    (Runs every 5 minutes, continuously)                      │
└──────┬───────────────────────────────────────────────────┬────────────────────┘
       │                                                    │
       ▼                                                    ▼
┌──────────────────────────┐                  ┌──────────────────────────┐
│  DRAFT POST GENERATOR    │                  │  SMART SCHEDULER         │
│                          │                  │                          │
│ • Counts Draft posts     │                  │ • Finds queue posts      │
│ • If < 21: Generate new  │                  │ • Checks available slots │
│ • Random topic           │                  │ • Assigns time window    │
│ • Random framework       │                  │ • Updates Airtable       │
│ • Random hook            │                  │                          │
│ • Stores as Draft        │                  │ TIME SLOTS:              │
│                          │                  │ • Slot 1: 8-10 AM        │
│ OUTPUT: Draft posts      │                  │ • Slot 2: 12-2 PM        │
│ in Airtable              │                  │ • Slot 3: 5-7 PM         │
└──────────────────────────┘                  │                          │
       ▲                                       │ OUTPUT: Posts with       │
       │                                       │ scheduled times          │
       │                                       └──────────────────────────┘
       │                                              ▲
       │                                              │
       │ (Runs after cleanup & scheduling)           │ (Runs after inventory)
       │                                              │
       └──────────────────────────────────────────────┘

       ▼

┌──────────────────────────┐
│  POST CLEANUP            │
│                          │
│ • Finds Posted posts     │
│ • Checks Posted At date  │
│ • If 7+ days old: DELETE │
│ • Removes from Airtable  │
│                          │
│ OUTPUT: Deleted posts    │
└──────────────────────────┘


                    ▼
        ┌───────────────────────┐
        │  AIRTABLE DATABASE    │
        │  (Posts Table)        │
        ├───────────────────────┤
        │ • Title               │
        │ • Post Content        │
        │ • Status              │
        │ • Scheduled Time      │
        │ • Image Prompt        │
        │ • Notes (metadata)    │
        │ • Posted At           │
        └───────────────────────┘


External Integrations (Waiting):
        │
        ├──► MAKE.COM WEBHOOK
        │    • Detects Pending Review status
        │    • Posts to LinkedIn at scheduled time
        │    • Changes status to Posted
        │
        └──► IMAGE GENERATION API
             • Detects Pending Review status
             • Generates image
             • Adds to Image field
```

---

## Data Flow

### Complete Post Lifecycle

```
[1] AUTO-GENERATED
    ↓
    Automation creates post as Draft
    - Topic: Random from 73 options
    - Framework: Random (PAS, AIDA, BAB, Framework, Contrarian)
    - Hook: Random from 7 templates
    - CTA: Soft (80%) or Direct (20%)
    - Visual Type: Based on post type
    - Status: DRAFT
    - Scheduled Time: EMPTY
    ↓
[2] AWAITING REVIEW (You)
    ↓
    You review post in Airtable
    Edit if needed
    ↓
[3] CHANGE STATUS → "Pending Review"
    ↓
    ┌─ Make.com detects status change
    └─ Calls image generation (future integration)
      └─ Image added to post
    ↓
[4] IMAGE READY (You review)
    ↓
    You review generated image
    Edit if needed
    ↓
[5] CHANGE STATUS → "Approved - Ready to Schedule"
    ↓
    Post enters scheduling queue
    ↓
[6] SMART SCHEDULER PROCESSES
    ↓
    ┌─ Checks available time slots
    ├─ Slot 1 (8-10 AM) for today?
    ├─ Slot 2 (12-2 PM) for today?
    ├─ Slot 3 (5-7 PM) for today?
    ├─ If all today full → check tomorrow
    └─ Assign to next available slot

    Airtable updated:
    - Status: PENDING REVIEW (with scheduled time)
    - Scheduled Time: 2026-01-05T18:47:00
    ↓
[7] WAITING FOR MAKE.COM
    ↓
    Post scheduled, sitting in Airtable
    Make.com monitors for Pending Review + Scheduled Time
    ↓
[8] MAKE.COM POSTS AT SCHEDULED TIME
    ↓
    ┌─ Time reaches scheduled time (e.g., 6:47 PM)
    └─ Make.com webhook triggers
       └─ Posts to LinkedIn via API

    Airtable updated:
    - Status: POSTED
    - Posted At: 2026-01-05T18:47:00
    ↓
[9] LIVE ON LINKEDIN (7 days)
    ↓
    Post collecting engagement
    You can approve/deny (feeds topic learning)
    ↓
[10] AUTO-CLEANUP (After 7 days)
    ↓
    Cleanup script finds Posted posts
    Checks Posted At timestamp
    If 7+ days old → DELETE from Airtable
    ↓
[11] DELETED
    ↓
    Post removed from Airtable
    Space freed for new posts
    Topic learning recorded
    Cycle continues...
```

---

## Time Slot Assignment Logic

### Slot Availability Check

When scheduling a post:

```
Check Date: Today (Jan 5, 2026)
  Slot 1 (8-10 AM):
    ├─ Check Airtable for posts with:
    │  ├─ Status: Pending Review OR Posted
    │  ├─ Scheduled Time between 8:00-10:00 on Jan 5
    │  └─ Found: 1 post → FULL

  Slot 2 (12-2 PM):
    ├─ Check Airtable for posts with:
    │  ├─ Status: Pending Review OR Posted
    │  ├─ Scheduled Time between 12:00-14:00 on Jan 5
    │  └─ Found: 1 post → FULL

  Slot 3 (5-7 PM):
    ├─ Check Airtable for posts with:
    │  ├─ Status: Pending Review OR Posted
    │  ├─ Scheduled Time between 17:00-19:00 on Jan 5
    │  └─ Found: 0 posts → AVAILABLE ✓

→ ASSIGN POST TO JAN 5, SLOT 3 (random time: 5:47 PM)

If all 3 slots on Jan 5 were full:
Check Date: Tomorrow (Jan 6, 2026)
  Slot 1 (8-10 AM): Available? YES
  → ASSIGN POST TO JAN 6, SLOT 1
```

### Multi-Post Queue Example

```
Queue at 2026-01-05 11:30 AM:
  Post A (approved at 11:30:02)
  Post B (approved at 11:30:03)
  Post C (approved at 11:30:04)

Current occupied slots:
  Jan 5: Slot 1 (filled), Slot 2 (filled), Slot 3 (empty)
  Jan 6: Slot 1 (filled), Slot 2 (empty), Slot 3 (empty)

Assignment (in order):
  Post A → Jan 5, Slot 3 @ 5:47 PM
  Post B → Jan 6, Slot 2 @ 1:15 PM
  Post C → Jan 6, Slot 3 @ 6:03 PM

Result: 3 posts spread across 2 days, filling gaps perfectly
```

---

## Inventory Management

### Auto-Generation Trigger

```
Every 5 minutes:

COUNT Draft posts in Airtable

If count >= 21:
  ✅ Inventory satisfied
  Do nothing
  Wait 5 minutes, repeat

If count < 21:
  NEEDED = 21 - current_count

  For i in 1 to NEEDED:
    1. Pick random topic from 73 topics
    2. Generate post (framework, hook, body, CTA)
    3. Add to Airtable with Status: DRAFT
    4. Record in topic learning system

  Repeat until count = 21
  Wait 5 minutes
```

---

## Topic Learning Integration

### How Approval/Denial Feeds Back

```
Scenario: You approve/deny posts

When you APPROVE a post:
  ↓
  Read "Topic" from Notes field
  ↓
  TopicPerformanceAnalyzer.record_post_result(topic, approved=True)
  ↓
  Update: approved_posts += 1
  Update: approval_rate = approved / total
  ↓
  Next generation: This topic gets higher weight

When you DENY a post:
  ↓
  Read "Topic" from Notes field
  ↓
  TopicPerformanceAnalyzer.record_post_result(topic, approved=False)
  ↓
  Update: denied_posts += 1
  Update: approval_rate = approved / total

  If approval_rate == 0 AND total >= 3:
    → Topic DEPRECATED
    → Removed from future generation
    ↓
  Next generation: This topic never appears again
```

---

## File Structure

```
/Users/musacomma/Agentic Workflow/
├── execution/
│   ├── automation_orchestrator.py       ← Master controller (RUNNING)
│   ├── draft_post_generator.py          ← Inventory manager
│   ├── smart_scheduler.py               ← Time slot assigner
│   ├── post_cleanup.py                  ← Auto-delete manager
│   ├── optimized_post_generator.py      ← Post content generator
│   ├── topic_performance_analyzer.py    ← Topic learning
│   └── [other utilities]
│
├── .tmp/
│   ├── automation.log                   ← Live automation logs
│   ├── automation.pid                   ← Process ID
│   └── topic_performance.json           ← Topic learning data
│
├── AUTOMATION_WORKFLOW_GUIDE.md         ← Full workflow docs
├── AUTOMATION_LIVE_STATUS.md            ← Current status
├── AUTOMATION_ARCHITECTURE.md           ← This file
├── LINKEDIN_POST_OPTIMIZATION_FRAMEWORK.md
├── LINKEDIN_VISUAL_CONTENT_GUIDE.md
└── POST_GENERATION_SPEC.json
```

---

## Continuous Execution Model

### Process Tree

```
automation_orchestrator.py (PID: 7442)
└── Master loop (every 5 minutes)
    ├── Call draft_post_generator.maintain_inventory()
    ├── Call smart_scheduler.process_queue()
    └── Call post_cleanup.run_cleanup()

    └── Sleep 300 seconds
    └── Loop back to start

The process:
- Runs forever (unless killed)
- Uses minimal CPU between cycles (sleeping)
- Logs all activity to .tmp/automation.log
- Persists on system restart (can add to launchd/systemd)
```

---

## Status Summary

### Scripts
- ✅ `automation_orchestrator.py` - **RUNNING** (PID: 7442)
- ✅ `draft_post_generator.py` - Ready to use
- ✅ `smart_scheduler.py` - Ready to use
- ✅ `post_cleanup.py` - Ready to use
- ✅ `optimized_post_generator.py` - Supporting role

### Data
- ✅ Airtable connected - Posts synchronized
- ✅ 21 Draft posts generated - Ready for review
- ✅ Topic performance tracking - Learning from decisions

### Integrations Pending
- ⏳ Make.com webhooks - For posting & image generation
- ⏳ Image generation API - For automatic visuals
- ⏳ LinkedIn API - For posting

### Ready to Use
✅ **Automation is LIVE and fully operational**

You can start immediately:
1. Review Draft posts in Airtable
2. Change status to "Pending Review" when ready
3. Change status to "Approved - Ready to Schedule"
4. Let automation handle the rest
