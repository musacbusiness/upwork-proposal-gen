# Modal LinkedIn Automation - Architecture

Complete system architecture for serverless LinkedIn content automation.

---

## System Overview

```
                        INTERNET
                            │
                            ▼
                    ┌───────────────┐
                    │  You + Browser│
                    │   (Airtable)  │
                    └───────┬───────┘
                            │
                   ┌────────┴────────┐
                   │                 │
          Change:Status          Read Results
                   │                 │
                   ▼                 ▼
            ┌──────────────┐  ┌──────────────┐
            │  Airtable    │  │  Airtable    │
            │  Automations │  │  Posts Table │
            │  (Free tier) │  │              │
            └──────┬───────┘  └──────────────┘
                   │
      ┌────────────┼────────────┐
      │            │            │
      ▼            ▼            ▼
 Auto #1      Auto #2       Auto #3
 Pending→      Approved→     Rejected→
 Review        Schedule      Delete
      │            │            │
      │ POST       │ POST       │ POST
      │            │            │
      └────────────┼────────────┘
                   │
                   ▼
        ┌──────────────────────────┐
        │  MODAL CLOUD             │
        │  (Serverless Functions)  │
        │                          │
        │  ┌────────────────────┐  │
        │  │ Web Endpoints      │  │
        │  │ /webhook/          │  │
        │  │  status-change     │  │
        │  └────────────────────┘  │
        │           │              │
        │           ▼              │
        │  ┌────────────────────┐  │
        │  │ Route by Status:   │  │
        │  │                    │  │
        │  │ Pending Review?    │  │
        │  │ → Call Function 1  │  │
        │  │                    │  │
        │  │ Approved?          │  │
        │  │ → Call Function 2  │  │
        │  │                    │  │
        │  │ Rejected?          │  │
        │  │ → Call Function 3  │  │
        │  └────────────────────┘  │
        └──────────────────────────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
        ▼          ▼          ▼
   Function1  Function2   Function3
   Generate   Schedule    Handle
   Images     Post        Rejected
        │          │          │
        ▼          ▼          ▼
    Replicate   Update    Update
    API         Airtable  Airtable
        │          │          │
        └──────────┼──────────┘
                   │
                   ▼
        ┌──────────────────────────┐
        │  MODAL CRON JOBS         │
        │  (Background Timers)     │
        │                          │
        │  Every 4 Hours:          │
        │  Check for posts ready   │
        │  to post                 │
        │           │              │
        │           ▼              │
        │  Post to LinkedIn        │
        │  (Selenium)              │
        │           │              │
        │  Every Hour:             │
        │  Check for records due   │
        │  for deletion            │
        │           │              │
        │           ▼              │
        │  Delete old records      │
        │           │              │
        │  Daily 6 AM UTC:         │
        │  Generate new posts      │
        │  (Claude + Images)       │
        └──────────────────────────┘
                   │
                   ▼
        ┌──────────────────────────┐
        │ External APIs            │
        │ (via Modal)              │
        │                          │
        │ ├─ Airtable API          │
        │ ├─ Anthropic (Claude)    │
        │ ├─ Replicate (Images)    │
        │ └─ LinkedIn API/Selenium │
        └──────────────────────────┘
```

---

## Data Flow

### Flow 1: Image Generation (Pending Review → Generated Image)

```
┌─────────┐
│ Airtable│  You change Status
│  Post   │  to "Pending Review"
└────┬────┘
     │
     ▼
┌────────────────────────┐
│ Airtable Automation #1 │  Watches for
│ (Watch Records)        │  status change
└────┬───────────────────┘
     │
     ▼
┌────────────────────────┐
│ HTTP POST Webhook      │  Sends record_id
│ to Modal               │  and status
└────┬───────────────────┘
     │
     ▼
┌────────────────────────┐
│ Modal Endpoint         │  Receives webhook
│ /webhook/status-change │
└────┬───────────────────┘
     │
     ▼
┌────────────────────────┐
│ Detect "Pending Review"│  Routes to correct
│ Status                 │  function
└────┬───────────────────┘
     │
     ▼
┌──────────────────────────┐
│ generate_images_for_post │  Modal function
│ (async)                  │  (non-blocking)
└────┬─────────────────────┘
     │
     ├─→ Fetch post record from Airtable
     │
     ├─→ Call Claude to generate image prompt
     │
     ├─→ POST to Replicate API
     │   "Generate image with prompt..."
     │
     ├─→ Poll Replicate API (every 2 sec)
     │   "Is image ready?"
     │
     ├─→ Get image URL when done (30-60s)
     │
     └─→ PATCH Airtable
         Update record:
         - Image URL
         - Image Generated At (timestamp)

     Returns immediately
     │
     ▼
┌────────────────────────────────────┐
│ User sees in Airtable:             │
│ - Image URL populated              │
│ - Image Generated At: [timestamp]  │
│ (30-60 seconds after status change)│
└────────────────────────────────────┘
```

### Flow 2: Auto-Scheduling (Approved → Scheduled)

```
┌─────────┐
│ Airtable│  You change Status
│  Post   │  to "Approved - Ready
└────┬────┘   to Schedule"
     │
     ▼
┌────────────────────────┐
│ Airtable Automation #2 │  Watches for
│ (Watch Records)        │  status change
└────┬───────────────────┘
     │
     ▼
┌────────────────────────┐
│ HTTP POST Webhook      │
│ to Modal               │
└────┬───────────────────┘
     │
     ▼
┌──────────────────────────┐
│ schedule_approved_post() │  Modal function
│ (async)                  │  (non-blocking)
└────┬─────────────────────┘
     │
     ├─→ Fetch post record
     │
     ├─→ Check Status is "Approved"
     │
     ├─→ Calculate next posting time:
     │   - Check current time (America/New_York)
     │   - Next slot: 9 AM, 2 PM, or 8 PM
     │   - Add random ±15 min offset
     │   - Make it future time
     │
     ├─→ If no slot today → use tomorrow 9 AM
     │
     └─→ PATCH Airtable
         Update record:
         - Status: "Scheduled"
         - Scheduled Time: [calculated time]
         - Scheduled At: [now]

     Returns immediately
     │
     ▼
┌────────────────────────────────────┐
│ User sees in Airtable:             │
│ - Status changed to "Scheduled"    │
│ - Scheduled Time populated         │
│ - Scheduled At: [timestamp]        │
│ (Within seconds)                   │
└────────────────────────────────────┘
```

### Flow 3: Auto-Posting (Scheduled → Posted)

```
Modal Cron Job
(Every 4 hours)
│
▼
┌──────────────────────────┐
│ Check Airtable           │  Query for
│ for "Scheduled" posts    │  Status = "Scheduled"
│ with past times          │
└────┬─────────────────────┘
     │
     ├─→ Find posts where
     │   Scheduled Time < now
     │
     ▼
┌──────────────────────────┐
│ For each post ready:     │
│ post_to_linkedin()       │  Modal function
└────┬─────────────────────┘
     │
     ├─→ Fetch post content & image
     │
     ├─→ Open Selenium browser
     │   to LinkedIn
     │
     ├─→ Log in with credentials
     │
     ├─→ Click "Start a post"
     │
     ├─→ Paste content
     │
     ├─→ Upload image
     │
     ├─→ Click "Post"
     │
     ├─→ Calculate deletion date (now + 7 days)
     │
     └─→ PATCH Airtable
         Update record:
         - Status: "Posted"
         - Posted At: [now]
         - Scheduled Deletion Date: [now + 7d]

         Spawn deletion timer task
     │
     ▼
┌────────────────────────────────────┐
│ User sees in Airtable:             │
│ - Status: "Posted"                 │
│ - Posted At: [timestamp]           │
│ - Scheduled Deletion Date: [+7d]   │
│ (Within 4-hour check window)       │
└────────────────────────────────────┘
```

### Flow 4: Auto-Deletion (Posted/Rejected → Deleted)

```
Modal Cron Job
(Every 1 hour)
│
▼
┌────────────────────────────┐
│ cleanup_scheduled_deletions │  Modal function
│ (Every hour)               │
└────┬──────────────────────┘
     │
     ├─→ Query Airtable for all records
     │   with Scheduled Deletion Date < now
     │
     ▼
┌────────────────────────────┐
│ For each record due:       │
└────┬──────────────────────┘
     │
     ├─→ DELETE /v0/BASE_ID/TABLE_ID/REC_ID
     │   (Airtable API)
     │
     ▼
┌────────────────────────────┐
│ Record deleted             │  Removed from
│ from Airtable              │  Airtable
└────────────────────────────┘

EITHER:
- 7 days after posting
- 24 hours after rejection
```

---

## Component Relationships

### Modal Functions (Async)
```
Modal App
│
├─ Web Endpoints
│  └─ /webhook/status-change
│     └─ Routes to functions based on status
│
├─ Async Functions (Spawned, non-blocking)
│  ├─ generate_images_for_post()
│  ├─ schedule_approved_post()
│  ├─ post_to_linkedin()
│  ├─ handle_rejected_post()
│  └─ schedule_deletion_task()
│
└─ Cron Jobs (Scheduled)
   ├─ auto_schedule_and_post_scheduler() - Every 4h
   ├─ cleanup_scheduled_deletions() - Every 1h
   └─ generate_daily_content() - Daily 6 AM UTC
```

### External APIs Used
```
Modal Functions
│
├─→ Airtable API
│   ├─ GET /v0/{base}/{table}/{record} (Fetch)
│   ├─ PATCH /v0/{base}/{table}/{record} (Update)
│   └─ DELETE /v0/{base}/{table}/{record} (Delete)
│
├─→ Anthropic API (Claude)
│   └─ POST /v1/messages (Generate text)
│
├─→ Replicate API
│   ├─ POST /v1/predictions (Create image)
│   └─ GET /v1/predictions/{id} (Poll status)
│
└─→ LinkedIn
    └─ Selenium browser automation
        (Login → Create post → Upload image → Publish)
```

---

## Data Models

### Airtable Post Record
```json
{
  "id": "recXXXXXXXXXXXXXX",
  "fields": {
    "Title": "string",
    "Content": "string (150-300 chars)",
    "Status": "Draft|Pending Review|Approved - Ready to Schedule|Scheduled|Posted|Rejected",
    "Image URL": "https://...",
    "Image Prompt": "string (detailed image description)",
    "Content Type": "AI Workflow Prompt|Case Study|...",
    "Created Date": "2025-12-25T10:30:00Z",
    "Approved By": "string",
    "Image Generated At": "2025-12-25T10:35:00Z",
    "Scheduled Time": "2025-12-25T14:00:00Z",
    "Scheduled At": "2025-12-25T09:30:00Z",
    "Posted At": "2025-12-25T14:00:00Z",
    "Posted URL": "https://linkedin.com/feed/update/xxx",
    "Scheduled Deletion Date": "2026-01-01T14:00:00Z",
    "Rejected At": "2025-12-25T09:50:00Z"
  }
}
```

### Webhook Payload
```json
{
  "record_id": "recXXXXXXXXXXXXXX",
  "status": "Pending Review|Approved - Ready to Schedule|Rejected",
  "base_id": "appXXXXXXXXXXXXXX",
  "table_id": "tblXXXXXXXXXXXXXX"
}
```

---

## State Machine

```
┌──────────────┐
│    DRAFT     │  Initial state
│ (Auto-created│  by daily cron
│ by Modal)    │
└────┬─────────┘
     │
     │ (User action)
     ▼
┌──────────────────┐
│ PENDING REVIEW   │  (User selects)
│                  │  Modal: Generate images
│ Image Generated? │
└────┬─────────────┘
     │ No: User modifies
     │    (Edit & try again)
     │
     │ Yes: Approved?
     ├──────────┐
     │          │
     │ No       │ Yes
     ▼          ▼
  (Stays)    ┌──────────────────────┐
  Pending    │ APPROVED -READY TO   │
  Review     │ SCHEDULE             │
             │                      │
             │ Modal: Auto-schedule │
             └────┬─────────────────┘
                  │
                  ▼
             ┌──────────────┐
             │  SCHEDULED   │  (Auto-set by Modal)
             │              │  Waiting for time
             │  Time: 9am   │
             │  2pm, 8pm    │
             └────┬─────────┘
                  │
                  │ (Time passes)
                  │ Modal cron checks every 4h
                  │
                  ▼
             ┌──────────────┐
             │   POSTED     │  (Auto-set by Modal)
             │              │  Posted to LinkedIn
             │ Timer: 7 days│
             └────┬─────────┘
                  │
                  │ (7 days pass)
                  │ Modal cron checks every 1h
                  │
                  ▼
             ┌──────────────┐
             │   DELETED    │  Record removed
             │              │  from Airtable
             └──────────────┘

ALTERNATIVE PATH (Rejection):

From PENDING REVIEW or APPROVED:
     │
     │ (User action: Click "Reject")
     ▼
  ┌──────────────┐
  │  REJECTED    │  (User selects)
  │              │  Modal: Schedule deletion
  │  Timer: 24h  │
  └────┬─────────┘
       │
       │ (24 hours pass)
       │ Modal cron checks every 1h
       │
       ▼
    ┌──────────────┐
    │   DELETED    │  Record removed
    │              │  from Airtable
    └──────────────┘
```

---

## Timing & SLAs

### Real-Time (< 1 second)
- Webhook delivery from Airtable → Modal
- Status change acknowledgment
- Function spawn (async return)

### Fast (< 5 seconds)
- Scheduling calculation
- Airtable status update
- User sees "Scheduled" in Airtable

### Medium (30-60 seconds)
- Image generation via Replicate
- User sees image URL in Airtable

### Background (Up to 4 hours)
- Post to LinkedIn (waits for scheduled time)
- May take up to 4 hours for posting (cron runs every 4h)

### Cleanup (Up to 1 hour)
- Record deletion (cron runs every 1 hour)
- Deleted within 1 hour of deletion date

### Daily
- New content generation (6 AM UTC)
- Creates 21 posts daily

---

## Failure Handling

```
If Replicate fails:
├─ Log error to Modal logs
├─ Airtable record unchanged
├─ User can retry by changing status again
└─ No data loss

If Airtable API fails:
├─ Modal function logs error
├─ User can manually update Airtable
├─ No image/schedule loss
└─ Retry-safe

If LinkedIn posting fails:
├─ Log error
├─ Status stays "Scheduled"
├─ Cron retries every 4 hours
├─ Manual fallback: Post via LinkedIn UI
└─ User can investigate logs

If deletion fails:
├─ Log error
├─ Record stays in Airtable
├─ Cron retries every hour
├─ User can manually delete
└─ No data corruption
```

---

## Security & Secrets

```
Modal Secrets (Encrypted in Modal Dashboard)
│
├─ AIRTABLE_API_KEY (Airtable read/write access)
├─ AIRTABLE_BASE_ID (Base identifier)
├─ AIRTABLE_LINKEDIN_TABLE_ID (Table identifier)
├─ ANTHROPIC_API_KEY (Claude AI access)
├─ REPLICATE_API_TOKEN (Image generation access)
├─ LINKEDIN_EMAIL (LinkedIn account)
└─ LINKEDIN_PASSWORD (LinkedIn password)

Accessed by Modal Functions at runtime
├─ Never logged or exposed
├─ Deleted after function execution
├─ Encrypted in transit
└─ Encrypted at rest in Modal storage
```

---

## Scaling

### Current Scale (Per Day)
```
- 21 posts generated (3 × 7 days)
- 21 images generated (via Replicate)
- 3 scheduled
- 1-3 posted (depending on schedule)
- Records deleted as they age
```

### Estimated Load
```
Modal Functions Executions:
├─ Image generation: ~21/day × 60sec = 21 min compute
├─ Scheduling: ~21/day × 5sec = 2 min compute
├─ Posting: ~3/day × 120sec = 6 min compute
├─ Deletion checks: 24/day × 10sec = 4 min compute
└─ Content generation: 1/day × 300sec = 5 min compute

Total: ~40 minutes compute per day
Cost: ~$0.01-0.05/day = $0.30-1.50/month
```

### If Scaling 10x (210 posts/day)
```
- Image generation: ~210 min compute
- All other tasks proportionally scale
- Total: ~400 min compute per day
- Cost: ~$3-15/month

Still very affordable!
```

---

## Summary Table

| Aspect | Local | Modal |
|--------|-------|-------|
| **Uptime** | Depends on Mac | 99.9% SLA |
| **Compute Cost** | $0 (your Mac) | $1-5/month |
| **Setup** | Already done | 1 hour |
| **Maintenance** | Manual | Automatic |
| **Scaling** | Limited | Unlimited |
| **Triggering** | Manual buttons | Automatic webhooks |
| **Scheduling** | Manual commands | Automatic crons |
| **Deletion** | Manual | Automatic crons |
| **Reliability** | Variable | Enterprise-grade |

---

**Architecture:** Modal serverless + Airtable Automations + Replicate API

**Deployment:** ~1 hour setup, then fully automatic

**Cost:** ~$10-35/month (highly reliable)

**Maintenance:** Check logs occasionally, everything else automatic
