# LinkedIn Content Automation - Lead Generation System

Automated system for researching, creating, and scheduling valuable LinkedIn content that generates leads for your business. Posts 2-3 times daily with AI-generated images.

## Quick Start

```bash
# From the linkedin_automation directory:

# Run the complete daily workflow
python RUN_linkedin_automation.py --action daily

# Or run individual steps:
python RUN_linkedin_automation.py --action research       # Research & generate ideas
python RUN_linkedin_automation.py --action generate-posts # Create posts + images
python RUN_linkedin_automation.py --action schedule       # Schedule approved posts
python RUN_linkedin_automation.py --action post-now       # Post immediately
python RUN_linkedin_automation.py --action status         # Check system status
```

## How It Works

```
Daily Research (6:00 AM)
    ↓
Generate Content Ideas using Claude
    ↓
Format into LinkedIn Posts with Image Prompts
    ↓
Generate Professional Images (Banana.dev)
    ↓
Store in Airtable (PENDING_APPROVAL)
    ↓
[You Review & Approve in Airtable]
    ↓
Auto-Schedule Posts (9:00 AM, 2:00 PM, 8:00 PM)
    ↓
Publish to LinkedIn
    ↓
Track Analytics
```

## Setup

### 1. Install Dependencies

```bash
# From parent directory
pip install -r requirements.txt
```

### 2. Configure API Keys

Add these to your `.env` file in the **parent directory**:

```
# Claude AI (Required for content generation)
ANTHROPIC_API_KEY=sk-ant-xxx

# Airtable (Required for post management)
AIRTABLE_API_KEY=patXXXXXXXXXXXXXX
AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX

# Banana.dev (Required for image generation)
BANANA_API_KEY=xxx-xxx-xxx

# LinkedIn (Required for posting)
LINKEDIN_ACCESS_TOKEN=AQExxxxxxxxxxxxxx
LINKEDIN_ORGANIZATION_ID=123456789

# Optional: Custom tracking
GOOGLE_ANALYTICS_ID=UA-XXXXXXXXX-X
```

### 3. Set Up Airtable Base

Create an Airtable base with these tables:

#### Table: Posts
Fields:
- **Title** (Single line text) - Post title/headline
- **Content** (Long text) - Full post content
- **Status** (Single select) - PENDING_APPROVAL, APPROVED, SCHEDULED, POSTED, FAILED
- **Image URL** (URL) - Link to generated image
- **Image Prompt** (Long text) - Prompt used for image generation
- **Content Type** (Single select) - AI Workflow Prompt, Automation Case Study, etc.
- **Created Date** (Date) - When post was generated
- **Approved By** (Single line text) - Who approved it
- **Scheduled Times** (Long text) - ISO datetimes for scheduling
- **Posted URL** (URL) - LinkedIn post URL after publishing

#### Table: Scheduling Queue
Fields:
- **Post ID** (Link to Posts) - Reference to post
- **Scheduled Time** (Date) - When to post
- **Status** (Single select) - PENDING, SCHEDULED, POSTED, FAILED
- **Platform** (Single line text) - "LinkedIn"
- **Posted URL** (URL) - URL of posted content

### 4. Configure Posting Schedule

Edit `config/linkedin_config.json`:

```json
{
  "linkedin": {
    "posting_times": ["09:00", "14:00", "20:00"],
    "posts_per_day": 3,
    "timezone": "America/New_York"
  },
  "content_research": {
    "topics": [
      "AI automation for business",
      "Workflow optimization",
      "Business process automation",
      ...
    ]
  }
}
```

## Folder Structure

```
linkedin_automation/
├── RUN_linkedin_automation.py          ← ENTRY POINT
├── execution/                           ← Core modules
│   ├── research_content.py             # Claude-powered research
│   ├── generate_images.py              # Banana.dev image generation
│   ├── airtable_integration.py         # Airtable sync
│   └── linkedin_scheduler.py           # LinkedIn posting
├── config/
│   └── linkedin_config.json            # Settings
├── logs/
│   └── linkedin_automation.log         # Activity logs
└── README.md                            ← This file
```

## Workflow Stages

### Stage 1: Content Research

```bash
python RUN_linkedin_automation.py --action research
```

**What happens:**
- Claude AI researches configured topics
- Generates 5+ content ideas per topic
- Creates post headlines and descriptions
- Generates image concepts
- Stores in `.tmp/linkedin_content_ideas.json`

**Output:** Ideas ready for post generation

### Stage 2: Post Generation

```bash
python RUN_linkedin_automation.py --action generate-posts
```

**What happens:**
- Takes content ideas from research
- Claude formats into full LinkedIn posts (150-300 words)
- Generates image prompts for each post
- Banana.dev generates professional images
- Posts stored in Airtable as PENDING_APPROVAL
- Images saved locally and referenced in posts

**Output:** Posts with images in Airtable awaiting approval

**Key Features:**
- Posts include call-to-action encouraging engagement
- Images are 1200x1200px (perfect for LinkedIn)
- Hashtags included automatically
- Professional, conversational tone

### Stage 3: Approval & Scheduling

In Airtable:
1. Review posts in "Posts" table (PENDING_APPROVAL status)
2. Change status to "APPROVED" when ready
3. Add approval notes if needed

```bash
python RUN_linkedin_automation.py --action schedule
```

**What happens:**
- Finds all APPROVED posts in Airtable
- Automatically schedules at: 9:00 AM, 2:00 PM, 8:00 PM (configurable)
- Adds to Scheduling Queue table
- Posts queued for LinkedIn API publishing

**Output:** Posts scheduled and ready to go live

### Stage 4: Publishing

Posts publish automatically at scheduled times via LinkedIn API.

**To post immediately (testing):**
```bash
python RUN_linkedin_automation.py --action post-now
```

## Content Types

The system automatically generates these types of posts:

### 1. **AI Workflow Prompt**
Share specific LLM prompts that business owners can use
- Example: "Here's the prompt I use to generate marketing strategies..."
- Includes the actual prompt formatted for copy-paste
- Engagement: High (people love ready-to-use templates)

### 2. **Automation Case Study**
Real (or realistic) examples of automation implementations
- Before/after metrics
- Specific tools and process changes
- Time/cost savings achieved
- Engagement: Very High

### 3. **AI Implementation Guide**
Step-by-step guidance for implementing AI/automation
- Practical, actionable advice
- Common pitfalls to avoid
- Implementation timeline
- Engagement: High

### 4. **Business Tip**
Quick, actionable business optimization tips
- Single powerful idea per post
- Immediately applicable
- Engagement: Medium-High

### 5. **Industry Insight**
Trends, predictions, and observations
- Industry news analysis
- What it means for business owners
- Engagement: Medium

## Scheduling Logic

Posts are scheduled in 3 batches per day:

- **Morning (9:00 AM)** - Energy-focused content, motivation
- **Afternoon (2:00 PM)** - Actionable tips, case studies
- **Evening (8:00 PM)** - Insights, thought leadership

You can adjust times in `config/linkedin_config.json`.

## Image Generation

Images are generated using Banana.dev with professional styling:

- **Format:** 1200x1200px (LinkedIn square)
- **Style:** Modern, professional business aesthetic
- **Elements:** Include brand colors, typography, relevant visuals
- **Quality:** 4K resolution, high quality
- **Saved:** Locally in `.tmp/linkedin_images/` and referenced in posts

Image prompts are automatically generated based on post content to ensure visual relevance.

## API Keys & Credentials

### LinkedIn
1. Go to https://www.linkedin.com/developers/apps
2. Create a new app or use existing
3. Generate access token with `w_member_social` scope
4. Token has 60-day expiration, rotate before expiry

### Airtable
1. Go to https://airtable.com/account/tokens
2. Create personal access token
3. Add to `.env` as `AIRTABLE_API_KEY`
4. Get base ID from URL: `airtable.com/appXXXXXXXXXXXXXX`

### Banana.dev
1. Sign up at https://www.banana.dev
2. Create API key in dashboard
3. Add to `.env` as `BANANA_API_KEY`
4. Keep track of usage (has quotas)

### Claude (Anthropic)
1. Get key from https://console.anthropic.com
2. Add as `ANTHROPIC_API_KEY` in `.env`
3. Monitor usage for cost management

## Running on Schedule

### MacOS (Cron)

```bash
crontab -e
```

Add:
```
# Daily research at 6 AM
0 6 * * * cd /Users/username/Agentic\ Workflow/linkedin_automation && python RUN_linkedin_automation.py --action research

# Post scheduling at 8 AM (after review)
0 8 * * * cd /Users/username/Agentic\ Workflow/linkedin_automation && python RUN_linkedin_automation.py --action schedule
```

### Linux/Server (Systemd Timer)

Create `/etc/systemd/system/linkedin-automation.service`:

```ini
[Unit]
Description=LinkedIn Automation Service
After=network.target

[Service]
Type=oneshot
User=your_user
WorkingDirectory=/path/to/linkedin_automation
ExecStart=/usr/bin/python3 RUN_linkedin_automation.py --action daily
```

Create `/etc/systemd/system/linkedin-automation.timer`:

```ini
[Unit]
Description=LinkedIn Automation Daily Timer
Requires=linkedin-automation.service

[Timer]
OnCalendar=*-*-* 06:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable:
```bash
sudo systemctl enable linkedin-automation.timer
sudo systemctl start linkedin-automation.timer
```

## Monitoring & Troubleshooting

### Check Status

```bash
python RUN_linkedin_automation.py --action status
```

Shows:
- Number of pending posts
- Number of approved posts
- Credentials status
- Next 5 posting times

### View Logs

```bash
tail -f logs/linkedin_automation.log
```

Or view historical logs in the logs directory.

### Common Issues

**"AIRTABLE_BASE_ID not configured"**
- Add `AIRTABLE_BASE_ID` to `.env`
- Base ID is the `appXXXXXXX` part of Airtable URL

**"No approved posts to schedule"**
- Make sure posts are marked as "APPROVED" in Airtable
- Check that Status field shows "APPROVED" exactly

**"Image generation failed"**
- Check Banana.dev API key validity
- Check remaining quota/credits
- Verify internet connection

**"LinkedIn post failed"**
- Verify access token is current (expires every 60 days)
- Check LinkedIn API permissions
- Verify organization ID if posting to company page

## Cost Estimates

**Monthly costs (approx):**
- Claude API: $10-30 (depending on traffic)
- Banana.dev: $10-50 (image generation)
- Airtable: $0-12 (free tier sufficient, $12/month for pro)
- LinkedIn API: $0 (free for native developers)
- **Total:** $20-92/month

## Advanced Customization

### Change Content Topics

Edit `config/linkedin_config.json`:
```json
"topics": [
  "Your custom topic 1",
  "Your custom topic 2",
  ...
]
```

### Adjust Posting Frequency

```json
"posts_per_day": 5,  // Post 5 times daily instead of 3
"posting_times": ["07:00", "10:00", "13:00", "16:00", "19:00"]
```

### Modify Image Style

Edit `generate_images.py` in the `_enhance_prompt()` method to adjust image generation style.

### Custom Tone/Voice

Edit `research_content.py` in the `generate_post_content()` method to adjust Claude's instructions for your voice.

## Support & Troubleshooting

For issues:
1. Check `logs/linkedin_automation.log` for detailed errors
2. Run `python RUN_linkedin_automation.py --action status`
3. Verify all API keys are valid and current
4. Check Airtable structure matches expected schema

## Next Steps

1. Set up all API keys in `.env`
2. Create Airtable base with tables and fields
3. Configure topics in `config/linkedin_config.json`
4. Run: `python RUN_linkedin_automation.py --action daily`
5. Review posts in Airtable and approve
6. Set up cron/scheduler for daily runs

## Best Practices

- **Review posts before approval** - Customize if needed for your voice
- **Monitor engagement** - Track which post types get best response
- **Rotate topics** - Update topics quarterly for freshness
- **Test images** - Run a test post to verify image quality
- **Track ROI** - Note leads generated from specific posts
- **Maintain token expiry** - LinkedIn tokens expire every 60 days

## Support

For detailed instructions and troubleshooting, see:
- Main project README in parent directory
- Individual module docstrings in `execution/`
- Airtable API docs: https://airtable.com/api
- LinkedIn Developer docs: https://learn.microsoft.com/en-us/linkedin/

---

**Last Updated:** December 2025
**Version:** 1.0
