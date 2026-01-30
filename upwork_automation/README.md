# Upwork Automation System

This folder contains a complete, automated system for finding, filtering, and applying to Upwork jobs.

## Quick Start

```bash
# From the upwork_automation directory:

# Run the complete pipeline
python RUN_upwork_automation.py --action full

# Or run individual steps:
python RUN_upwork_automation.py --action filter      # Filter raw jobs
python RUN_upwork_automation.py --action sync        # Sync to ClickUp
python RUN_upwork_automation.py --action proposals   # Generate proposals
python RUN_upwork_automation.py --action status      # Check system status
```

## How It Works

```
Raw Jobs (from Apify or manual scrape)
    ↓
Filter Jobs (based on config/filter_rules.json)
    ↓
Sync to ClickUp (creates tasks with job details)
    ↓
Generate Proposals (AI-powered using Claude)
    ↓
Ready for Submission
```

## Setup

### 1. Install Dependencies

```bash
# From parent directory
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create or update `.env` in the **parent directory** with:

```
# Claude AI (Required for proposals)
ANTHROPIC_API_KEY=sk-ant-xxx

# ClickUp (Required for job tracking)
CLICKUP_API_KEY=pk_xxx
CLICKUP_WORKSPACE_ID=123456
CLICKUP_LIST_ID=789456

# Apify (Optional, for automated scraping)
APIFY_API_TOKEN=apk_xxx

# Upwork (Optional)
UPWORK_EMAIL=your@email.com
```

### 3. Customize Filter Rules

Edit `config/filter_rules.json` to set your preferences:

- **Budget Range**: Min and max budget you accept
- **Client Rating**: Minimum client rating (4.5+ recommended)
- **Client Reviews**: Minimum number of reviews (50+ recommended)
- **Job Category**: Types of jobs you're interested in
- **Skills Required**: Skills that must match
- **Exclude Keywords**: Keywords that disqualify a job
- **Proposals Required**: Maximum number of proposals you'll accept
- **Job Type**: Fixed-price, hourly, or both

## Folder Structure

```
upwork_automation/
├── RUN_upwork_automation.py          ← ENTRY POINT - Use this to run automation
├── execution/                         ← Internal modules
│   ├── filter_jobs.py                # Job filtering engine
│   ├── generate_proposal.py           # AI proposal generation
│   └── sync_to_clickup.py            # ClickUp integration
├── config/
│   └── filter_rules.json             # Your filtering preferences
├── templates/
│   └── proposal_template.md          # Proposal template
├── logs/
│   └── upwork_automation.log         # Application logs
└── README.md                          # This file
```

## Workflow

### Step 1: Scrape Jobs (Manual or Automated)

Get raw Upwork job listings and save to `.tmp/raw_jobs.json` in the parent directory.

### Step 2: Filter Jobs

```bash
python RUN_upwork_automation.py --action filter
```

Jobs are filtered based on your criteria and scored 0-100 for fit. Results saved to:
- `.tmp/filtered_jobs_accepted.json` - Jobs that passed filters
- `.tmp/filtered_jobs_rejected.json` - Jobs that were rejected

### Step 3: Sync to ClickUp

```bash
python RUN_upwork_automation.py --action sync
```

Creates ClickUp tasks for each filtered job with:
- Job details and description
- Budget and client rating
- Filter score and application link
- Status: "AWAITING APPROVAL" (for you to review)

### Step 4: Generate Proposals

```bash
python RUN_upwork_automation.py --action proposals
```

Once you approve jobs in ClickUp, Claude AI generates personalized proposals:
- Analyzes job description for pain points
- Creates custom proposals highlighting your expertise
- Saves proposals to `.tmp/proposals/` directory

## Running the Complete Pipeline

```bash
python RUN_upwork_automation.py --action full
```

This runs all steps in sequence: filter → sync → proposals

## Checking System Status

```bash
python RUN_upwork_automation.py --action status
```

Shows:
- Which files exist and their sizes
- API credentials status (masked for security)
- Overall system health

## Advanced Features

### Webhook Integration (Optional)

ClickUp can trigger proposal generation when you change a job status to "APPROVED". This is handled by the webhook registration in the ClickUp integration.

### Custom Scoring

Jobs are scored based on:
- Budget alignment
- Client rating
- Number of proposals
- Skills match
- Review count

Higher scores = better fit.

### Error Handling

The system includes:
- Duplicate job detection (won't re-sync same job)
- Comprehensive logging to `logs/upwork_automation.log`
- Graceful fallbacks for API failures
- Detailed error messages for troubleshooting

## Troubleshooting

### "Raw jobs file not found"

You need to scrape Upwork jobs first. Options:
1. Use Apify with the Upwork scraper actor
2. Manually export jobs and save to `.tmp/raw_jobs.json`
3. Use the scraper in the parent directory's `execution/scrape_upwork_jobs.py`

### "Missing ClickUp credentials"

Make sure `.env` file in parent directory has:
- `CLICKUP_API_KEY`
- `CLICKUP_WORKSPACE_ID`
- `CLICKUP_LIST_ID`

### "Missing ANTHROPIC_API_KEY"

Get Claude API key from https://console.anthropic.com and add to `.env`

### Proposals not generating

1. Check that you have approved jobs in ClickUp
2. Export approved jobs from ClickUp list
3. Save to `.tmp/approved_jobs.json` in parent directory
4. Run proposals action again

## Customization

### Modify Filter Criteria

Edit `config/filter_rules.json` and restart the automation. Changes apply to the next filtering run.

### Custom Proposal Template

Edit `templates/proposal_template.md` to match your style. The system uses this as a reference for Claude.

### Adjust Scoring

Edit the `calculate_job_score()` method in `execution/filter_jobs.py` to change how jobs are rated.

## API Quotas & Costs

- **Claude API**: Charges per 1M input/output tokens (~$3-$15 per 1K proposals depending on job complexity)
- **ClickUp API**: Free tier has limits; paid plans available
- **Apify**: Free tier includes job scraping credits; paid plans for higher volumes

Monitor usage in the respective dashboards.

## Support

For issues:
1. Check logs: `logs/upwork_automation.log`
2. Run status check: `python RUN_upwork_automation.py --action status`
3. Review the main project README in parent directory

## License

This automation is for personal use. Ensure you comply with Upwork's terms of service.
