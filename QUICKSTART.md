# Quick Start Guide - Upwork Automation System

Get your automated Upwork job application system running in 30 minutes.

## Prerequisites

- Python 3.8+
- Upwork account
- ClickUp account
- Claude API key (Anthropic)
- Optional: Apify account for scraping

## Installation (5 minutes)

### 1. Install Dependencies

```bash
cd "/Users/musacomma/Agentic Workflow"
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Edit `.env` file and add:

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

**How to get these:**

- **ANTHROPIC_API_KEY**: Get from [console.anthropic.com](https://console.anthropic.com)
- **CLICKUP_API_KEY**: ClickUp Settings → Integrations → API
- **CLICKUP_WORKSPACE_ID**: ClickUp → Your Team → Copy workspace ID from URL
- **CLICKUP_LIST_ID**: Create a list called "Upwork Applications", copy ID from URL
- **APIFY_API_TOKEN**: Get from [apify.com](https://apify.com)

## Configuration (5 minutes)

### Edit `config/filter_rules.json`

Set your job filtering preferences:

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

### Customize Proposal Template

Edit `templates/proposal_template.md` with your service description.

## Run Your First Automation (10 minutes)

### Step 1: Get Raw Jobs

You need jobs to filter. Use Apify:

1. Go to [apify.com](https://apify.com)
2. Find "Upwork Jobs Scraper" actor
3. Configure search query: `"Python automation"`
4. Run and export results
5. Save to `.tmp/raw_jobs.json`

**Or** use this command to test with example data:

```bash
# Creates sample jobs in .tmp/raw_jobs.json
python -c "
import json
from execution.filter_jobs import JobFilter

# Create example jobs
sample_jobs = [
    {
        'id': '1', 'title': 'Build Python Automation System',
        'description': 'Need help with Python automation scripts',
        'budget': 2000, 'type': 'fixed-price',
        'skills': ['Python', 'Automation', 'API'],
        'client': {'name': 'Tech Co', 'rating': 4.8, 'reviews': 150},
        'url': 'https://upwork.com/jobs/123'
    }
]

with open('.tmp/raw_jobs.json', 'w') as f:
    json.dump(sample_jobs, f, indent=2)

print('✓ Created sample jobs')
"
```

### Step 2: Filter Jobs

```bash
python orchestrate.py --action filter
```

**Output:**
- ✓ Filtered jobs saved to `.tmp/filtered_jobs_accepted.json`
- See accepted jobs in CLI output

### Step 3: Sync to ClickUp

```bash
python orchestrate.py --action sync
```

**Output:**
- ✓ Tasks created in your ClickUp list with status "AWAITING APPROVAL"
- Each task shows job details, budget, client info

### Step 4: Approve Jobs in ClickUp

1. Go to your ClickUp list
2. Review jobs (already sorted by quality score)
3. Change status from "AWAITING APPROVAL" → "APPROVED" for jobs you want to apply to
4. Optional: Add notes or assign to yourself

### Step 5: Generate Proposals

First, export approved jobs from ClickUp:

1. ClickUp → Filter list to status="APPROVED"
2. Select all tasks
3. Export as JSON with custom fields
4. Save to `.tmp/approved_jobs.json`

Then generate proposals:

```bash
python orchestrate.py --action proposals
```

**Output:**
- ✓ Proposals generated in `.tmp/proposals/` folder
- Each file is ready to copy/paste into Upwork

### Step 6: Submit on Upwork

1. Go to Upwork
2. Open a job
3. Click "Send Proposal"
4. Copy/paste proposal from `.tmp/proposals/{job_id}_proposal.txt`
5. Add your name and submit

## Check Your Progress

```bash
# See system status
python orchestrate.py --action status

# View logs
tail -f logs/upwork_automation.log
```

## Full Pipeline (One Command)

After the first run, you can run the complete pipeline:

```bash
python orchestrate.py --action full
```

This runs:
1. Filter jobs ✓
2. Sync to ClickUp ✓
3. Generate proposals ✓

## Daily Workflow

1. **Morning**: Scrape new jobs via Apify (manual or scheduled)
2. **Filter & Sync**: `python orchestrate.py --action filter && python orchestrate.py --action sync`
3. **Review**: Check ClickUp, approve jobs you like
4. **Generate**: `python orchestrate.py --action proposals`
5. **Submit**: Copy proposals and submit on Upwork
6. **Track**: Monitor responses in ClickUp

## Common Issues

**"Missing ClickUp credentials"**
→ Add CLICKUP_API_KEY, CLICKUP_WORKSPACE_ID, CLICKUP_LIST_ID to .env

**"No raw jobs found"**
→ First scrape jobs to .tmp/raw_jobs.json (use Apify)

**"Proposals not generating"**
→ Ensure ANTHROPIC_API_KEY is in .env with valid Claude API key

**"ClickUp sync failed"**
→ Check API key, workspace ID, and list ID in .env

## Next Level: Automation

### Schedule Daily Scraping

Use cron or GitHub Actions to run daily:

```bash
# Run at 6 AM every day
0 6 * * * cd "/Users/musacomma/Agentic Workflow" && python orchestrate.py --action full
```

### Auto-submit Proposals (Advanced)

Set up a ClickUp webhook to auto-generate proposals when status changes to APPROVED.

See `execution/generate_proposal.py` for webhook handler example.

### Monitor Success

Track metrics in ClickUp:
- Response rate (interviews / proposals sent)
- Average job score accepted
- Time from approval to submission
- Budget range of successful jobs

## Customization Ideas

1. **Fine-tune filters** - Adjust `config/filter_rules.json` based on what works
2. **Improve proposals** - Edit `templates/proposal_template.md` to match your style
3. **Add more criteria** - Modify filter logic in `execution/filter_jobs.py`
4. **Schedule runs** - Use OS scheduler or GitHub Actions for daily scraping

## Support & Debugging

1. **Check logs**: `tail -f logs/upwork_automation.log`
2. **Check status**: `python orchestrate.py --action status`
3. **Read directives**: `directives/upwork_job_automation.md` has full technical details
4. **Review code comments**: Each script is well-documented

## Success Tips

✅ Start with a small budget range to test  
✅ Approve and submit your first 5 proposals manually  
✅ Track which proposals get interviews  
✅ Adjust filters based on what works  
✅ Keep proposal templates updated with recent work  
✅ Monitor client feedback and improve accordingly  

## You're Ready!

You now have a fully automated system to apply to Upwork jobs. Start with manual testing, then automate as you gain confidence in the filters and proposals.

Good luck! 🚀
