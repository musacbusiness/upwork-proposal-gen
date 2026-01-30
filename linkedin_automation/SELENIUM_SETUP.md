# LinkedIn Selenium Setup Guide

## Overview
Your LinkedIn automation now uses **browser automation (Selenium)** instead of the LinkedIn API. This means:
- ✅ No API key required
- ✅ No app creation/approval needed
- ✅ Just use your regular LinkedIn login
- ✅ Works with personal accounts

---

## Installation

### 1. Install Selenium Dependencies

Due to network timeouts, you'll need to install these when your connection is stable:

```bash
cd /Users/musacomma/Agentic\ Workflow/linkedin_automation
pip3 install selenium webdriver-manager
```

**What these do:**
- `selenium` - Browser automation framework
- `webdriver-manager` - Automatically downloads and manages ChromeDriver

---

## Configuration

### 2. Add Your LinkedIn Credentials

Edit your `.env` file and add your LinkedIn login:

```bash
# Open .env file
nano ../.env
```

Update these lines:
```env
LINKEDIN_EMAIL=your_actual_email@example.com
LINKEDIN_PASSWORD=your_actual_password
```

**Security Note:** 
- Your `.env` file is in `.gitignore` - it won't be committed to git
- Credentials are only stored locally on your machine
- The automation logs into LinkedIn just like you would manually

---

## How It Works

### Browser Automation Flow:

1. **Launch Chrome** (headless by default - invisible)
2. **Navigate to LinkedIn login** (linkedin.com/login)
3. **Enter your email & password** 
4. **Click login button**
5. **Navigate to feed**
6. **Click "Start a post"**
7. **Enter text content**
8. **Upload image** (if provided)
9. **Click "Post" button**
10. **Verify success & close browser**

Takes about 10-15 seconds per post.

---

## Testing

### Test the Selenium Module Directly

```bash
cd /Users/musacomma/Agentic\ Workflow/linkedin_automation/execution

# First, update your credentials in ../.env, then run:
python3 linkedin_poster_selenium.py
```

This will:
- Open a **visible** Chrome window (headless=False in test mode)
- Log into your LinkedIn
- Post a test message
- You can watch it happen in real-time!

### Test with the Full Automation

```bash
cd /Users/musacomma/Agentic\ Workflow/linkedin_automation

# Generate a post (requires ANTHROPIC_API_KEY)
python3 RUN_linkedin_automation.py --action generate-posts

# Post immediately
python3 RUN_linkedin_automation.py --action post-now
```

---

## Headless vs Visible Mode

### Headless (Default - Invisible)
```python
with LinkedInPosterSelenium(headless=True) as poster:
    poster.post_content(text, image_path)
```

### Visible (For Testing/Debugging)
```python
with LinkedInPosterSelenium(headless=False) as poster:
    poster.post_content(text, image_path)
```

To change the default in the scheduler, edit:
`execution/linkedin_scheduler.py` line 231:
```python
with LinkedInPosterSelenium(headless=True) as poster:  # Change to False to watch
```

---

## Handling 2FA / Security Challenges

If LinkedIn detects unusual login activity, it may ask for verification:

1. **Manual Verification**: 
   - The script will pause for 60 seconds
   - Complete the challenge in the browser window
   - Script continues automatically

2. **Email/SMS Code**:
   - Check your email or phone
   - Enter code in browser
   - Script will wait

3. **Future Logins**:
   - After first successful login, LinkedIn usually recognizes your machine
   - Subsequent logins are faster and don't require verification

**Tip**: Run the first test in **visible mode** (`headless=False`) so you can handle any challenges.

---

## Scheduling

### Important Note About Scheduling

LinkedIn's web interface doesn't support scheduled posting (that's an API-only feature). With Selenium, we have two options:

1. **Store posts in Airtable and run automation at scheduled times**
   ```bash
   # Add this to your crontab to run at 9 AM, 2 PM, and 8 PM
   0 9,14,20 * * * cd /Users/musacomma/Agentic\ Workflow/linkedin_automation && python3 RUN_linkedin_automation.py --action post-now
   ```

2. **Use the built-in scheduler** (posts are queued, you trigger publishing)
   ```bash
   python3 RUN_linkedin_automation.py --action schedule  # Queue posts
   python3 RUN_linkedin_automation.py --action post-now  # Publish next queued post
   ```

---

## Troubleshooting

### ChromeDriver Issues
```bash
# If you see "chromedriver not found"
pip3 install --upgrade webdriver-manager

# Or manually download ChromeDriver
# https://chromedriver.chromium.org/downloads
```

### Element Not Found
- LinkedIn may have changed their UI
- Open an issue and I'll update the selectors
- Or run in visible mode to see what's happening

### Login Fails
- Check credentials in `.env`
- Try logging in manually first to handle any account issues
- LinkedIn may require verification on first login from new location

### Post Button Not Clickable
- Wait a few more seconds (increase `time.sleep()` values)
- LinkedIn may be loading slowly
- Check your internet connection

---

## Advanced: Running Scheduled Posts with Cron

To fully automate posting at specific times:

```bash
# Edit your crontab
crontab -e

# Add these lines (adjust times as needed):
# Post at 9 AM Eastern
0 9 * * * cd /Users/musacomma/Agentic\ Workflow/linkedin_automation && /usr/local/bin/python3 RUN_linkedin_automation.py --action post-now >> logs/cron.log 2>&1

# Post at 2 PM Eastern
0 14 * * * cd /Users/musacomma/Agentic\ Workflow/linkedin_automation && /usr/local/bin/python3 RUN_linkedin_automation.py --action post-now >> logs/cron.log 2>&1

# Post at 8 PM Eastern
0 20 * * * cd /Users/musacomma/Agentic\ Workflow/linkedin_automation && /usr/local/bin/python3 RUN_linkedin_automation.py --action post-now >> logs/cron.log 2>&1
```

---

## Files Created

- `execution/linkedin_poster_selenium.py` - Main Selenium automation module
- `execution/linkedin_scheduler.py` - Updated to use Selenium
- `SELENIUM_SETUP.md` - This guide

---

## Next Steps

1. ✅ Install Selenium: `pip3 install selenium webdriver-manager`
2. ✅ Add credentials to `.env`
3. ✅ Test: `python3 execution/linkedin_poster_selenium.py`
4. ✅ Generate content: `python3 RUN_linkedin_automation.py --action generate-posts`
5. ✅ Post to LinkedIn: `python3 RUN_linkedin_automation.py --action post-now`

---

## Questions?

The Selenium approach is much simpler than LinkedIn's API but has some trade-offs:
- **Slower** (~15s per post vs instant API)
- **Requires Chrome** installed on your system
- **No native scheduling** (must use cron or run manually)
- **More reliable** (no API rate limits or approval process)

For your use case (2-3 posts per day), Selenium is perfect! 🚀
