# Make.com Integration Directive

## Overview
This directive enables bidirectional communication between your Upwork automation and Make.com workflows.

## 1. Calling Make.com FROM Your Agent

### Store Webhook URLs
When you have Make.com workflows, store their webhook URLs here for your agent to call.

### Example Make.com Webhooks

#### Lead Enrichment Workflow
```
URL: https://hook.us1.make.com/YOUR_WEBHOOK_ID
Method: POST
Body: {
  "action": "enrich_lead",
  "email": "lead@example.com",
  "company": "Acme Inc"
}
Response: {
  "linkedin_url": "...",
  "company_size": "...",
  "enriched": true
}
```

#### Notification Workflow
```
URL: https://hook.us1.make.com/YOUR_NOTIFICATION_WEBHOOK
Method: POST
Body: {
  "message": "New job found: {{job_title}}",
  "channel": "slack",
  "priority": "high"
}
```

## 2. Calling Your Agent FROM Make.com

### Modal Webhook Endpoints

After deploying to Modal, use these URLs in Make.com:

#### Full Pipeline (Scrape + Filter + Sync)
```
URL: https://YOUR_USERNAME--upwork-automation-webhook-full-pipeline.modal.run
Method: POST
Query String: query=zapier%20automation&limit=100
```

#### Generate Proposal
```
URL: https://YOUR_USERNAME--upwork-automation-webhook-proposal.modal.run
Method: POST
Headers: Content-Type: application/json
Body: {
  "job_title": "{{job_title}}",
  "job_description": "{{job_description}}",
  "budget": "{{budget}}"
}
```

## 3. Sample Make.com Scenarios

### Scenario A: Daily Job Scraping
```
Trigger: Schedule (Daily at 9 AM)
    ↓
HTTP Request: POST to Modal /webhook-full-pipeline
    ↓
Parse JSON Response
    ↓
Slack: Send summary "Found {{jobs_count}} new Upwork jobs"
```

### Scenario B: Auto-Generate Proposal on Airtable Update
```
Trigger: Airtable - Watch Records (Status = "Under Review")
    ↓
HTTP Request: POST to Modal /webhook-proposal
    Body: job details from Airtable
    ↓
Airtable: Update Record with generated proposal
    ↓
Slack: Notify "Proposal ready for review: {{job_title}}"
```

### Scenario C: Lead Enrichment Pipeline
```
Trigger: Webhook (from your agent)
    ↓
Clearbit: Enrich Company
    ↓
Hunter.io: Find Email
    ↓
LinkedIn: Get Profile
    ↓
Respond to Webhook: Return enriched data
```

## 4. Error Handling

### In Make.com
- Set timeout to 120 seconds (agent tasks can take time)
- Add error handler module
- Use "Resume" to continue on non-critical errors

### In Your Agent
- Check response status codes
- Log failures to Slack
- Implement retry logic for transient errors

## 5. Authentication

### Securing Your Webhooks
For production, add authentication:

```python
# In your Modal function
@modal.web_endpoint(method="POST")
def webhook_scrape(request):
    # Check API key
    api_key = request.headers.get("X-API-Key")
    if api_key != os.environ.get("WEBHOOK_API_KEY"):
        return {"error": "Unauthorized"}, 401
    
    # Process request...
```

Then in Make.com, add header:
```
X-API-Key: your_secret_key
```

## 6. Data Flow Examples

### Agent → Make.com → External Services
```
Your Agent (needs enrichment)
    ↓ POST to Make.com webhook
Make.com Scenario
    ↓ Calls Clearbit, Hunter.io, etc.
    ↓ Returns enriched data
Your Agent (continues with enriched data)
```

### Make.com → Agent → Airtable
```
Make.com (scheduled trigger)
    ↓ POST to Modal webhook
Your Agent (scrapes Upwork)
    ↓ Filters jobs
    ↓ Syncs to Airtable
    ↓ Returns summary
Make.com (receives response)
    ↓ Sends Slack notification
```

## 7. Testing

### Test Make.com Webhook Locally
```bash
curl -X POST "https://hook.us1.make.com/YOUR_WEBHOOK" \
  -H "Content-Type: application/json" \
  -d '{"test": true, "message": "Hello from agent"}'
```

### Test Modal Webhook
```bash
curl -X POST "https://YOUR--upwork-automation-webhook-proposal.modal.run" \
  -H "Content-Type: application/json" \
  -d '{"job_title": "Test Job", "job_description": "Test description", "budget": "$500"}'
```
