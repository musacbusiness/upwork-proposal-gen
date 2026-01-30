# Cloud Deployment Guide for Upwork Automation

## Overview

This guide shows you how to deploy your Upwork automation to the cloud using **Modal** (recommended) or run it locally with **Cloudflare Tunnels**.

## Option 1: Modal (Recommended)

### Why Modal?
- **Fast cold starts**: 2-3 seconds (vs 20-30s on other platforms)
- **Cheap**: ~$0.01 per 100 requests, $5 free credits
- **Serverless**: No ongoing costs when idle
- **Built-in cron**: Schedule jobs to run automatically

### Setup Steps

#### 1. Install Modal
```bash
pip install modal
```

#### 2. Create Modal Account & Token
```bash
modal token new
```
This opens a browser to authenticate.

#### 3. Set Up Secrets in Modal Dashboard

Go to [modal.com/secrets](https://modal.com/secrets) and create a secret called `upwork-secrets` with:

```
ANTHROPIC_API_KEY=your_key_here
AIRTABLE_API_KEY=your_key_here
AIRTABLE_UPWORK_BASE_ID=your_base_id
SLACK_WEBHOOK_URL=your_slack_webhook (optional)
```

#### 4. Deploy to Modal
```bash
cd "/Users/musacomma/Agentic Workflow"
modal deploy cloud/modal_upwork_agent.py
```

#### 5. Get Your Webhook URLs

After deployment, Modal gives you URLs like:
```
https://your-username--upwork-automation-webhook-scrape.modal.run
https://your-username--upwork-automation-webhook-proposal.modal.run
https://your-username--upwork-automation-webhook-full-pipeline.modal.run
```

### Using the Webhooks

#### From Make.com
1. Add HTTP module
2. URL: `https://your-username--upwork-automation-webhook-full-pipeline.modal.run`
3. Method: POST
4. Query params: `query=zapier automation&limit=100`

#### From n8n
1. Add HTTP Request node
2. Same URL and params as above

#### From cURL
```bash
curl -X POST "https://your-username--upwork-automation-webhook-full-pipeline.modal.run?query=Make.com%20automation&limit=100"
```

### Scheduled Jobs (Cron)

The deployment includes automatic scheduling:

| Schedule | What it does |
|----------|--------------|
| Daily 9 AM UTC | Scrapes 100 jobs for each automation keyword |
| Every 6 hours | Checks Airtable for status changes |

To modify schedules, edit `cloud/modal_upwork_agent.py`:
```python
@app.function(schedule=modal.Cron("0 9 * * *"))  # Daily at 9 AM
@app.function(schedule=modal.Cron("0 */6 * * *"))  # Every 6 hours
```

---

## Option 2: Local Server + Cloudflare Tunnel

### Why Local?
- **Free**: No cloud costs
- **Full control**: Runs on your machine
- **Testing**: Great for development

### Requirements
- Computer running 24/7
- Cloudflare account (free)

### Setup Steps

#### 1. Install Cloudflare Tunnel
```bash
brew install cloudflared
# or download from https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/
```

#### 2. Start Your Local Server
```bash
cd "/Users/musacomma/Agentic Workflow"
python orchestrate.py --action auto
```

#### 3. Expose via Cloudflare
```bash
cloudflared tunnel --url http://localhost:5051
```

This gives you a URL like: `https://random-words.trycloudflare.com`

#### 4. Use the Webhook
Your endpoints are now available at:
- `https://random-words.trycloudflare.com/health`
- `https://random-words.trycloudflare.com/webhook/status-change`

---

## Option 3: Hybrid with Make.com

### Trigger Agent from Make.com

1. **In Make.com**: Create a scenario with a webhook trigger
2. **Add HTTP Module**: Call your Modal webhook
3. **Process Response**: Use the returned data in Make.com

### Trigger Make.com from Agent

Store Make.com webhook info in your directives:

```markdown
# My Make.com Workflow

## Webhook URL
https://hook.us1.make.com/abc123xyz

## How to Call
Send a POST request with JSON body:
{
  "action": "process_leads",
  "data": {...}
}
```

Then your agent can call Make.com webhooks directly!

---

## Slack Chain-of-Thought Logging

To see what your agent is thinking in real-time:

1. Create a Slack app with incoming webhooks
2. Add `SLACK_WEBHOOK_URL` to your Modal secrets
3. Watch the `#cloud-logs` channel for updates like:
   - "🔍 Starting Upwork scrape: query='zapier', limit=100"
   - "✅ Scrape complete: 87 jobs found"
   - "📤 Syncing to Airtable..."

---

## Quick Reference

### Modal Commands
```bash
modal deploy cloud/modal_upwork_agent.py  # Deploy
modal serve cloud/modal_upwork_agent.py   # Local testing with hot reload
modal app logs upwork-automation          # View logs
modal app stop upwork-automation          # Stop all running functions
```

### Webhook Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/webhook-scrape` | POST | Scrape Upwork jobs |
| `/webhook-proposal` | POST | Generate proposal |
| `/webhook-full-pipeline` | POST | Run complete pipeline |

### Query Parameters
| Param | Default | Description |
|-------|---------|-------------|
| `query` | "automation" | Search query |
| `limit` | 100 | Max jobs to scrape |

---

## Cost Comparison

| Method | Monthly Cost | Reliability |
|--------|-------------|-------------|
| Modal | ~$1-5 | ⭐⭐⭐⭐⭐ |
| Local + Cloudflare | $0 | ⭐⭐⭐ (depends on uptime) |
| AWS Lambda | ~$5-20 | ⭐⭐⭐⭐ |
| Heroku | ~$7+ | ⭐⭐⭐⭐ |

**Recommendation**: Start with Modal. It's the best balance of cost, reliability, and ease of setup.
