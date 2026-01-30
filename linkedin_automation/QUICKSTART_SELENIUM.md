# LinkedIn Automation - Quick Start (Selenium)

## 🚀 Setup (One-Time)

```bash
# 1. Install dependencies
cd "/Users/musacomma/Agentic Workflow/linkedin_automation"
pip3 install selenium webdriver-manager

# 2. Add credentials to .env
nano ../.env
```

Add these lines to `.env`:
```env
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_password
ANTHROPIC_API_KEY=sk-ant-...your_key
```

---

## ✅ Test It Works

```bash
# Test Selenium login and posting (visible browser)
python3 execution/linkedin_poster_selenium.py
```

This opens Chrome and posts a test message. Watch it work!

---

## 📝 Daily Workflow

```bash
# 1. Generate 3 posts with AI images
python3 RUN_linkedin_automation.py --action generate-posts

# 2. Review posts in Airtable
open https://airtable.com/appw88uD6ZM0ckF8f

# 3. Change status to "Approved - Ready to Schedule"

# 4. Post immediately
python3 RUN_linkedin_automation.py --action post-now
```

---

## 🔄 Automate with Cron (Optional)

Post automatically at 9 AM, 2 PM, 8 PM:

```bash
crontab -e
```

Add:
```cron
0 9,14,20 * * * cd "/Users/musacomma/Agentic Workflow/linkedin_automation" && python3 RUN_linkedin_automation.py --action post-now
```

---

## 📊 Check Status

```bash
python3 RUN_linkedin_automation.py --action status
```

Shows:
- ✓ Credentials configured
- ✓ Posts pending/approved in Airtable
- ✓ Next posting times

---

## 🎯 Commands Reference

| Command | What It Does |
|---------|-------------|
| `--action research` | Research content ideas |
| `--action generate-posts` | Generate 3 posts + images |
| `--action post-now` | Post next approved post |
| `--action status` | Show automation status |
| `--action daily` | Full workflow (research → generate → schedule) |

---

## ⚙️ How It Works

1. **Selenium opens Chrome** (invisible by default)
2. **Logs into LinkedIn** with your credentials
3. **Creates and publishes post** (~15 seconds)
4. **Closes browser**

No API keys needed! Just your regular LinkedIn login.

---

## 🔧 Troubleshooting

**Can't login?**
- Check credentials in `.env`
- LinkedIn may ask for 2FA on first login (script waits 60s)

**ChromeDriver error?**
```bash
pip3 install --upgrade webdriver-manager
```

**Want to watch it work?**
Edit `execution/linkedin_scheduler.py` line 231:
```python
with LinkedInPosterSelenium(headless=False) as poster:
```

---

## 📖 Full Documentation

See `SELENIUM_SETUP.md` for complete guide.
