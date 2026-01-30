# Upwork Job Automation System

A fully automated system to find, filter, and apply to Upwork jobs. This system replicates and enhances your Make.com workflow.

## Features

✅ **Job Scraping** - Collect Upwork jobs matching your criteria  
✅ **Intelligent Filtering** - Filter jobs by budget, rating, skills, and custom criteria  
✅ **ClickUp Integration** - Auto-populate tasks with job details  
✅ **Proposal Generation** - AI-powered personalized proposals using Claude  
✅ **Webhook Support** - Trigger proposals from ClickUp status changes  
✅ **Logging & Analytics** - Track all operations and results  
✅ **Error Recovery** - Self-annealing with detailed error handling  

## Architecture

```
Raw Jobs (Apify/Scraper)
    ↓
Filter Engine (filter_jobs.py)
    ↓
ClickUp Integration (sync_to_clickup.py)
    ↓
Proposal Generator (generate_proposal.py)
    ↓
Ready for Submission
```

## Quick Start

### 1. Set Up Environment

```bash
# Copy example .env (if you haven't already)
cp .env.example .env

# Add your credentials to .env
CLICKUP_API_KEY=your_api_key
CLICKUP_WORKSPACE_ID=your_workspace_id
CLICKUP_LIST_ID=your_list_id
ANTHROPIC_API_KEY=your_claude_api_key
```

### 2. Customize Filter Rules

Edit `config/filter_rules.json` to match your preferences:

```json
{
  "budget": {"min": 500, "max": 10000},
  "client_rating": {"min": 4.5},
  "client_reviews": {"min": 50},
  "job_category": ["Web Development", "Automation"],
  "skills_required": ["Python"],
  "exclude_keywords": ["blockchain", "ai training"]
}
```

### 3. Get Raw Jobs

You need to scrape Upwork jobs first. Two options:

**Option A: Use Apify** (Recommended)
- Use an Apify Upwork Jobs scraper actor
- Export results to `.tmp/raw_jobs.json`

**Option B: Manual Scraping**
- Use Selenium/Playwright to scrape jobs
- See `directives/upwork_job_automation.md` for details

### 4. Run the Pipeline

```bash
# Filter jobs
python orchestrate.py --action filter

# Check ClickUp and approve jobs manually (change status to "APPROVED")

# Sync to ClickUp
python orchestrate.py --action sync

# Generate proposals for approved jobs
python orchestrate.py --action proposals

# Or run everything at once
python orchestrate.py --action full
```

### 5. Review & Submit

- Check `proposals/` folder for generated proposals
- Copy/paste into Upwork
- Submit proposals on Upwork
- Track responses in ClickUp

## File Structure

```
.
├── directives/
│   └── upwork_job_automation.md    # System documentation
├── execution/
│   ├── filter_jobs.py              # Filter engine
│   ├── sync_to_clickup.py          # ClickUp integration
│   ├── generate_proposal.py        # Proposal generator
│   └── scrape_upwork_jobs.py       # Job scraper (optional)
├── config/
│   └── filter_rules.json           # Filtering criteria
├── templates/
│   └── proposal_template.md        # Proposal template
├── logs/
│   └── upwork_automation.log       # Detailed logs
├── .tmp/
│   ├── raw_jobs.json               # Raw scraped jobs
│   ├── filtered_jobs_accepted.json # Filtered & accepted
│   ├── filtered_jobs_rejected.json # Filtered & rejected
│   ├── proposals/                  # Generated proposals
│   └── *.json                      # Summary files
├── .env                            # Credentials (gitignored)
├── .gitignore                      # Git ignore rules
└── orchestrate.py                  # Main orchestration script
```

## Commands

```bash
# Filter raw jobs based on config
python orchestrate.py --action filter

# Sync filtered jobs to ClickUp
python orchestrate.py --action sync

# Generate proposals for approved jobs
python orchestrate.py --action proposals

# Run full pipeline
python orchestrate.py --action full

# Check system status
python orchestrate.py --action status
```

## Configuration

### Environment Variables (.env)

Required:
```
CLICKUP_API_KEY=your_clickup_api_key
CLICKUP_WORKSPACE_ID=your_workspace_id
CLICKUP_LIST_ID=your_list_id
ANTHROPIC_API_KEY=your_claude_api_key
```

Optional:
```
UPWORK_EMAIL=your@email.com
UPWORK_PASSWORD=password
LOG_LEVEL=INFO
```

### Filter Rules (config/filter_rules.json)

Key settings:
- **budget.min/max** - Budget range to accept
- **client_rating.min** - Minimum client rating
- **client_reviews.min** - Minimum number of reviews
- **job_category** - Allowed job categories (empty = all)
- **skills_required** - Must match at least one
- **exclude_keywords** - Any job with these words is rejected
- **proposals_required.max** - Maximum proposals already submitted
- **job_type** - fixed-price, hourly, or leave empty for all

## Workflow

### Step 1: Scrape Jobs
Get raw job data from Upwork using Apify or custom scraper.

**Output:** `.tmp/raw_jobs.json`

### Step 2: Filter Jobs
Apply intelligent filters based on your criteria.

**Input:** `.tmp/raw_jobs.json` + `config/filter_rules.json`  
**Output:** `.tmp/filtered_jobs_accepted.json` (sorted by score)

### Step 3: Sync to ClickUp
Create ClickUp tasks for filtered jobs with status "AWAITING APPROVAL".

**Input:** `.tmp/filtered_jobs_accepted.json`  
**Output:** Tasks in ClickUp, summary in `.tmp/clickup_sync_summary.json`

### Step 4: Manual Approval (You)
Review jobs in ClickUp and change status to "APPROVED" for jobs you want to apply to.

### Step 5: Generate Proposals
For each approved job, generate a personalized proposal using Claude AI.

**Input:** Approved jobs from ClickUp  
**Output:** Proposal text files in `.tmp/proposals/`

### Step 6: Submit Proposals
Copy/paste proposals into Upwork and submit.

## Key Features Explained

### Smart Filtering

Jobs are scored 0-100 based on:
- Budget alignment (±20 points)
- Client rating (±15 points)
- Client review count (±10 points)
- Proposal count (±15 points)
- Skills match (±10 points)

Higher score = better fit.

### Proposal Generation

The AI proposal generator:
1. Analyzes job description to extract pain points
2. Identifies key requirements and opportunities
3. Generates personalized, professional proposal
4. Tailored to your service offering

Proposals are concise (under 400 words) and ready to copy/paste.

### Error Handling

The system:
- Logs all operations and errors
- Continues on non-fatal errors
- Provides clear error messages
- Can be re-run without duplicates

## Advanced Usage

### Custom Scraper

To create a custom Upwork scraper, see `directives/upwork_job_automation.md` for requirements and expected JSON format.

### Webhook Integration

To auto-generate proposals when status changes in ClickUp:

1. Set up ClickUp webhook for `taskStatusUpdated` event
2. Create a Flask/FastAPI endpoint to receive webhooks
3. Call `generate_proposal.py` when status → APPROVED

Example webhook payload handler:
```python
@app.post('/webhook/clickup')
def handle_clickup_webhook(payload: dict):
    task = payload.get('task')
    if task.get('status', {}).get('status') == 'APPROVED':
        generator = ProposalGenerator()
        proposal = generator.generate_proposal_from_clickup_task(task)
        # Save proposal...
```

### Batch Operations

You can batch process multiple jobs:

```python
from execution.filter_jobs import JobFilter
from execution.generate_proposal import ProposalGenerator

# Load jobs
jobs = load_filtered_jobs()

# Generate proposals for all
generator = ProposalGenerator()
summary = generator.generate_proposals_batch(jobs)
```

## Troubleshooting

### "No raw jobs found"
- First, you need to scrape jobs and save to `.tmp/raw_jobs.json`
- Use Apify or custom scraper (see directives)

### "Missing ClickUp credentials"
- Add CLICKUP_API_KEY, CLICKUP_WORKSPACE_ID, CLICKUP_LIST_ID to .env

### "API rate limit exceeded"
- The system implements delays between API calls
- Check logs for timing info

### "Proposals not generating"
- Check ANTHROPIC_API_KEY in .env
- Ensure approved jobs exist in `.tmp/approved_jobs.json`
- Check logs for detailed error messages

## Success Metrics

Track these to measure effectiveness:
- Jobs scraped per run
- % passing filters
- Time from scrape to ClickUp task
- Time from approval to proposal
- Interview rate from proposals

See `logs/upwork_automation.log` for detailed analytics.

## Next Steps

1. ✅ Set up `.env` with credentials
2. ✅ Customize `config/filter_rules.json`
3. ✅ Get raw jobs via Apify or scraper
4. ✅ Run `python orchestrate.py --action filter`
5. ✅ Review in ClickUp and approve jobs
6. ✅ Run `python orchestrate.py --action proposals`
7. ✅ Copy proposals and submit on Upwork

## Support

- Check `directives/upwork_job_automation.md` for detailed system documentation
- Review logs in `logs/upwork_automation.log` for debugging
- Update `config/filter_rules.json` based on what works

## License

Proprietary - Your Automated Systems Business
