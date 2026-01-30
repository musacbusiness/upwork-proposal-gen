# Upwork Proposal Generator - Quick Start Guide

## What It Does
Paste an Upwork job link → Get a personalized proposal → Copy to clipboard in **30 seconds**

The system automatically:
1. **Scrapes** the Upwork job details
2. **Generates** a proposal using Claude API, written in your voice
3. **Copies** the proposal to your clipboard

Your voice is built in: Direct, numbers-focused, no fluff, client-centric.

---

## Usage

### Option 1: Web Scraping (Automated)
```bash
python execution/generate_upwork_proposal.py "https://www.upwork.com/jobs/..."
```

The script will:
- Extract job title, description, budget, skills, level
- Generate a personalized proposal matching your voice
- Copy it to clipboard automatically

Output example:
```
✓ SUCCESS! Proposal is ready to paste into Upwork.
✓ Proposal copied to clipboard - paste it into Upwork now!
```

### Option 2: Manual Fallback (If Scraping Fails)
If web scraping doesn't work:
```bash
python execution/generate_upwork_proposal.py "https://www.upwork.com/jobs/..."
```

It will prompt you to paste the job description. Just:
1. Copy the job description from Upwork
2. Paste it when prompted
3. Press `Ctrl+D` (or `Cmd+D` on Mac) when done
4. The proposal will be generated and copied to clipboard

---

## What The Proposal Includes

Your proposals automatically include:

✓ **Opening** - Shows you understand their specific problem (not generic)
✓ **Why you fit** - Your relevant experience (automation, AI, business optimization)
✓ **Your approach** - Concrete steps, not just promises
✓ **ROI/Outcome** - What they actually get (time saved, money made, scale achieved)
✓ **Call to action** - Next steps

### Your Voice in Proposals
- **Analytical**: Show you think strategically about their business
- **Numbers-focused**: Reference concrete metrics, ROI, opportunity cost
- **Direct**: No "I'm excited to help you" fluff
- **Authentic**: Sound like a peer, not a guru
- **Client-centric**: Frame everything in terms of what THEY gain

---

## Where Files Are Stored

```
.tmp/proposals/
  └─ {job_id}_proposal.txt        # Your generated proposals (saved for reference)

.tmp/upwork_proposal_log.txt       # Logs of all generation attempts
```

---

## Troubleshooting

### Problem: "Chrome WebDriver not found"
**Solution 1 (Quick)**: Install webdriver-manager
```bash
pip install webdriver-manager
```

**Solution 2 (Fallback)**: Use manual mode - paste the job description instead

### Problem: "Proposal copied to clipboard failed"
**Solution**: The proposal will still be printed to terminal. Just manually copy it from there.

### Problem: "API rate limit"
**Solution**: Wait a few minutes and try again. Claude API has rate limits. You can queue multiple jobs and come back to them.

### Problem: "Job page took too long to load"
**Solution**:
- Check your internet connection
- Try again in a few seconds
- Or use manual mode (paste job description)

---

## Configuration

### Change the Model
Open `execution/generate_upwork_proposal.py` and change the `model` parameter:

```python
message = self.client.messages.create(
    model="claude-opus-4-5-20251101",  # Change this
    max_tokens=1024,
    ...
)
```

Models available:
- `claude-opus-4-5-20251101` (recommended - best quality)
- `claude-sonnet-4-5` (faster, good quality)
- `claude-haiku-4-5` (cheapest, basic quality)

### Adjust Proposal Length
In the `_build_prompt` method, change the word count:
```python
- Length: 150-250 words (should read in under 2 minutes)
```

Smaller = faster, more impact
Larger = more detail, more persuasive

---

## What's Your Voice Profile?

Your proposals are written with YOUR authentic voice, extracted from [VOICE_DISCOVERY_CONVERSATION.md](VOICE_DISCOVERY_CONVERSATION.md):

- **Who you are**: 23-year-old founder, self-taught builder, automation expert
- **How you think**: Analytical + willing to take calculated risks
- **What you believe**: Real software > Platform constraints; client transformation = winning
- **How you talk**: Direct, concrete, strategic, no bullshit
- **Why you do it**: Not for billion-dollar status, but for clients scaling and saving time

Every proposal reflects this. You won't get generic "I'm a certified expert" language. You'll get authentic communication that shows you understand the business problem.

---

## Example Workflow

**You:**
```bash
python execution/generate_upwork_proposal.py "https://www.upwork.com/jobs/12345"
```

**System:**
```
UPWORK PROPOSAL GENERATOR
============================================================

[1/3] SCRAPING JOB DETAILS...
→ Navigating to: https://www.upwork.com/jobs/12345
✓ Successfully scraped job: Build AI chatbot integration

📋 Job: Build AI chatbot integration for union contract database
💰 Budget: $2,500 - $5,000
📊 Skills: Python, AI, API Integration

[2/3] GENERATING PROPOSAL...
→ Generating proposal with Claude API...
✓ Proposal generated successfully

[3/3] SAVING & COPYING TO CLIPBOARD...
✓ Proposal saved to: .tmp/proposals/12345_proposal.txt
✓ Proposal copied to clipboard

============================================================
✓ SUCCESS! Proposal is ready to paste into Upwork.
============================================================

[Proposal text displays here]

============================================================
✓ Proposal copied to clipboard - paste it into Upwork now!
============================================================
```

**You:** Go to Upwork, paste (Cmd+V), and submit.

---

## Data & Privacy

- **Local only**: Job details are stored in `.tmp/proposals/` on your machine
- **Claude API**: Only the job description and your voice profile are sent to Claude
- **No tracking**: No analytics, no profiling beyond what you configure
- **Clean up**: Delete `.tmp/proposals/` anytime to remove history

---

## Next Steps (Future)

As you build more work, we can:
1. **Add case studies**: Once you have completed projects, add them to proposals
2. **A/B test proposals**: Track which angles convert best (interviews vs rejections)
3. **Batch mode**: Apply to 10+ jobs in one go
4. **Analytics**: See which proposal angles work best for different job types

---

## Questions?

Check the directive: [directives/upwork_job_automation.md](directives/upwork_job_automation.md)

Or review your voice profile: [VOICE_DISCOVERY_CONVERSATION.md](VOICE_DISCOVERY_CONVERSATION.md)

---

**Last updated**: January 30, 2025
