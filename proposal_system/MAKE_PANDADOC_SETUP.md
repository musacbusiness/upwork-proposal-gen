# Make.com + PandaDoc Proposal System Setup

## Overview

This guide walks you through setting up the Make.com scenario that connects:
1. **Zoom AI Companion** → Transcript to webhook
2. **Your Proposal Webhook** → Analyzes & generates proposal content
3. **PandaDoc** → Creates professional, signable proposal
4. **Airtable** → Tracks all proposals

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     PROPOSAL AUTOMATION FLOW                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  TRIGGER OPTIONS:                                                   │
│  ┌──────────────────┐    ┌──────────────────┐                      │
│  │ Scenario 1:      │    │ Scenario 2:      │                      │
│  │ Zoom Transcript  │    │ Manual Input     │                      │
│  │ (via webhook)    │    │ (Airtable form)  │                      │
│  └────────┬─────────┘    └────────┬─────────┘                      │
│           │                       │                                 │
│           └───────────┬───────────┘                                 │
│                       ▼                                             │
│           ┌──────────────────────┐                                  │
│           │ Make.com Scenario    │                                  │
│           └──────────┬───────────┘                                  │
│                      ▼                                              │
│           ┌──────────────────────┐                                  │
│           │ Your Webhook         │                                  │
│           │ /analyze-transcript  │                                  │
│           │ or /manual-input     │                                  │
│           └──────────┬───────────┘                                  │
│                      ▼                                              │
│           ┌──────────────────────┐                                  │
│           │ /generate-proposal   │                                  │
│           │ Claude AI generates  │                                  │
│           │ full proposal text   │                                  │
│           └──────────┬───────────┘                                  │
│                      ▼                                              │
│           ┌──────────────────────┐                                  │
│           │ PandaDoc             │                                  │
│           │ Create Document      │                                  │
│           │ from Template        │                                  │
│           └──────────┬───────────┘                                  │
│                      ▼                                              │
│           ┌──────────────────────┐                                  │
│           │ Airtable             │                                  │
│           │ Update record with   │                                  │
│           │ PandaDoc link        │                                  │
│           └──────────────────────┘                                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Create PandaDoc Template

In PandaDoc, create a proposal template with these **tokens** (merge fields):

### Template Sections:

1. **Header**
   - `{{Company.Name}}` - Your company (ScaleAxis)
   - `{{Client.Name}}` - Client company name
   - `{{Document.Date}}` - Proposal date

2. **Executive Summary**
   - `{{ExecutiveSummary}}` - Auto-generated from webhook

3. **Current Challenges**
   - `{{Challenges}}` - Pain points section

4. **Proposed Solution**
   - `{{Solution}}` - What you'll build

5. **Scope of Work**
   - `{{ScopeOfWork}}` - Deliverables list

6. **Timeline**
   - `{{Timeline}}` - Project timeline

7. **Investment**
   - `{{ProjectPrice}}` - One-time project fee
   - `{{MaintenanceFee}}` - Monthly maintenance (optional)
   - `{{ROIExplanation}}` - Value justification

8. **Terms & Conditions**
   - Standard terms (hardcoded in template)

9. **Signature Block**
   - PandaDoc signature field

### How to Create Template:
1. Go to PandaDoc → Templates → Create Template
2. Design your proposal layout
3. Add text fields with the token names above (use `{{TokenName}}` format)
4. Add a signature field at the bottom
5. Save as "ScaleAxis Service Proposal"
6. Note the **Template ID** (found in URL or settings)

---

## Step 2: Set Up Airtable Base

Create a base called "Proposals" with this structure:

### Table: Prospects

| Field Name | Type | Notes |
|------------|------|-------|
| Client Name | Single line text | Required |
| Client Email | Email | For PandaDoc recipient |
| Status | Single select | New, Analyzing, Proposal Sent, Signed, Lost |
| Source | Single select | Zoom Call, In-Person, Referral |
| Pain Points | Long text | JSON or bullet list |
| Transcript | Long text | Full Zoom transcript (if applicable) |
| Hours Saved/Week | Number | For pricing calculation |
| Employees Affected | Number | For pricing calculation |
| Hourly Rate | Currency | Default $45 |
| Proposal Content | Long text | Generated proposal markdown |
| Project Price | Currency | Calculated price |
| Maintenance Fee | Currency | Monthly fee |
| PandaDoc URL | URL | Link to the generated proposal |
| PandaDoc ID | Single line text | Document ID for tracking |
| Created At | Date | Auto-set |
| Notes | Long text | Additional context |

---

## Step 3: Create Make.com Scenario

### Scenario A: Zoom Transcript → Proposal

**Modules:**

1. **Webhook (Custom)** - Receives transcript from Zoom
   - Create a custom webhook in Make.com
   - URL: `https://hook.us1.make.com/xxxxx` (copy this)

2. **HTTP - Make a Request** - Send to your analysis endpoint
   ```
   URL: http://YOUR_SERVER:5052/analyze-transcript
   Method: POST
   Body: {"transcript": "{{1.transcript}}"}
   ```

3. **HTTP - Make a Request** - Generate proposal
   ```
   URL: http://YOUR_SERVER:5052/generate-proposal
   Method: POST
   Body: {
     "client_name": "{{2.client_name}}",
     "pain_points": {{2.pain_points}},
     "solutions": {{2.proposed_solutions}},
     "pricing": {{2.calculated_pricing}},
     "source": "transcript"
   }
   ```

4. **PandaDoc - Create a Document**
   - Template: Select your "ScaleAxis Service Proposal"
   - Name: "Proposal - {{2.client_name}} - {{formatDate(now; "YYYY-MM-DD")}}"
   - Recipient Email: `{{2.client_email}}` (or leave blank for manual)
   - Tokens:
     - `Client.Name` = `{{2.client_name}}`
     - `ExecutiveSummary` = Parse from `{{3.proposal_content}}`
     - `ProjectPrice` = `{{3.pricing.suggested_project_price}}`
     - etc.

5. **Airtable - Create Record**
   - Base: Proposals
   - Table: Prospects
   - Fields: Map all the data from previous modules

### Scenario B: Manual Input (Airtable Trigger)

**Modules:**

1. **Airtable - Watch Records**
   - Base: Proposals
   - Table: Prospects
   - Trigger: When Status = "New"

2. **HTTP - Make a Request** - Process pain points
   ```
   URL: http://YOUR_SERVER:5052/manual-input
   Method: POST
   Body: {
     "client_name": "{{1.Client Name}}",
     "client_email": "{{1.Client Email}}",
     "pain_points": ["{{1.Pain Points}}"],
     "hours_saved_per_week": {{1.Hours Saved/Week}},
     "num_employees": {{1.Employees Affected}}
   }
   ```

3. **HTTP - Make a Request** - Generate proposal
   ```
   URL: http://YOUR_SERVER:5052/generate-proposal
   Method: POST
   Body: {
     "client_name": "{{2.client_name}}",
     "pain_points": {{2.pain_points}},
     "pricing": {{2.calculated_pricing}},
     "source": "manual"
   }
   ```

4. **PandaDoc - Create a Document**
   - Same as Scenario A

5. **Airtable - Update Record**
   - Update the original record with:
     - Status = "Proposal Generated"
     - Proposal Content = `{{3.proposal_content}}`
     - Project Price = `{{3.pricing.suggested_project_price}}`
     - PandaDoc URL = `{{4.document_link}}`
     - PandaDoc ID = `{{4.id}}`

---

## Step 4: Connect Zoom AI Companion

### Option A: Zoom Webhook (Requires Zoom Developer Account)

1. Create a Zoom App at marketplace.zoom.us
2. Enable "Meeting Ended" webhook
3. Point webhook to your Make.com scenario URL
4. When meeting ends, Zoom sends transcript to Make.com

### Option B: Manual Upload (Simpler)

1. After Zoom call, download transcript from Zoom
2. Upload to a Google Drive folder
3. Make.com watches the folder, triggers when new file added
4. Reads file content and sends to webhook

### Option C: Zapier Bridge (If Zoom integration easier there)

1. Zapier: Zoom → New Recording with Transcript
2. Zapier: Send webhook to Make.com
3. Make.com handles the rest

---

## Step 5: Test the System

### Test 1: Manual Input
```bash
curl -X POST http://localhost:5052/manual-input \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Test Company",
    "client_email": "test@example.com",
    "pain_points": [
      "Spending 10 hours/week on manual data entry",
      "No visibility into sales pipeline"
    ],
    "hours_saved_per_week": 10,
    "num_employees": 2
  }'
```

### Test 2: Generate Full Proposal
```bash
curl -X POST http://localhost:5052/generate-proposal \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Test Company",
    "pain_points": [
      {"problem": "Manual data entry", "time_spent_hours": 5},
      {"problem": "No pipeline visibility", "time_spent_hours": 3}
    ],
    "pricing": {
      "suggested_project_price": 3500,
      "monthly_maintenance_fee": 525,
      "roi_explanation": "Saves $18,720/year"
    }
  }'
```

---

## Step 6: Deploy to Cloud (Optional)

For 24/7 availability, deploy the webhook to Modal:

1. Add to your existing Modal deployment
2. Or run on a VPS/cloud server
3. Update Make.com URLs to point to cloud endpoint

---

## Pricing Logic Reference

From the value-based pricing framework:

| Client Saves | You Charge (10% of annual) | Monthly Maintenance |
|--------------|---------------------------|---------------------|
| $12,000/year | $1,200 | $180/month |
| $25,000/year | $2,500 | $375/month |
| $50,000/year | $5,000 | $750/month |
| $100,000/year | $10,000 | $1,500/month |

**Formula:**
1. Hours saved/week × Hourly rate × 52 weeks × Employees = Annual Savings
2. Project Price = Annual Savings ÷ 10 (10x ROI rule)
3. Maintenance = 10-25% of Project Price per month

---

## Files Reference

| File | Purpose |
|------|---------|
| `proposal_system/webhook_proposal_generator.py` | Main webhook server |
| `proposal_system/MAKE_PANDADOC_SETUP.md` | This guide |

---

## Troubleshooting

**PandaDoc not creating document:**
- Check OAuth connection in Make.com
- Ensure template exists and has correct token names
- Business plan should work with Make.com's OAuth integration

**Pricing seems off:**
- Adjust `PRICING_CONFIG` in webhook_proposal_generator.py
- Default hourly rate is $45, minimum project is $1,500

**Transcript analysis incomplete:**
- Ensure transcript is long enough (>100 characters)
- Check Claude API key is valid

---

## Next Steps

1. ✅ Create PandaDoc template with tokens
2. ✅ Set up Airtable base
3. ✅ Build Make.com scenario
4. ✅ Test with sample data
5. ⏳ Connect Zoom (when ready)
6. ⏳ Enable auto-send (when confident in output)
