"""
Modal Cloud Deployment for Upwork Automation
=============================================
Serverless webhooks + cron scheduling for your Upwork job automation.

Deploy: modal deploy cloud/modal_upwork_agent.py
Test:   modal serve cloud/modal_upwork_agent.py

Endpoints:
- GET  /health - Health check
- POST /webhook-proposal - Generate proposal for a job
- POST /webhook-status-check - Check Airtable status changes
- POST /webhook-sync - Sync jobs to Airtable

Cron Jobs:
- Daily 9 AM UTC: Status check
- Every 6 hours: Status check (Under Review → generate, Rejected → delete)
"""

import modal
import os
import json
from datetime import datetime
from typing import Optional

# ============== Modal App Setup ==============

app = modal.App("upwork-automation")

# Image with all dependencies (base for API calls)
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "anthropic",
        "requests", 
        "python-dotenv",
        "aiohttp",
        "fastapi[standard]",
    )
)

# Image with Selenium for scraping
scraper_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install(
        "wget",
        "gnupg",
        "unzip",
        "curl",
        "chromium",
        "chromium-driver",
    )
    .pip_install(
        "selenium",
        "requests",
        "python-dotenv",
        "fastapi[standard]",
    )
    .env({
        "CHROME_BIN": "/usr/bin/chromium",
        "CHROMEDRIVER_PATH": "/usr/bin/chromedriver",
    })
)


# ============== Helper Functions ==============

def log_to_slack(message: str):
    """Send logs to Slack channel for visibility."""
    import requests
    
    slack_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not slack_url:
        print(f"[LOG] {message}")
        return
    
    try:
        requests.post(slack_url, json={
            "text": f"[Upwork Bot] {message}",
            "username": "Upwork Automation",
            "icon_emoji": ":robot_face:"
        }, timeout=5)
    except Exception as e:
        print(f"[LOG] {message} (Slack failed: {e})")


def get_airtable_headers():
    """Get Airtable API headers."""
    return {
        'Authorization': f'Bearer {os.environ.get("AIRTABLE_API_KEY")}',
        'Content-Type': 'application/json'
    }


# ============== Core Functions ==============

@app.function(
    image=image,
    secrets=[modal.Secret.from_name("upwork-secrets")],
    timeout=120,
)
def generate_proposal(job_title: str, job_description: str, job_skills: str = "", budget: str = "Not specified") -> dict:
    """
    Generate a proposal using Claude Opus 4.5.
    """
    import anthropic
    
    log_to_slack(f"✍️ Generating proposal for: {job_title[:50]}...")
    
    try:
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        
        prompt = f"""You are an expert no-code automation specialist. Your PRIMARY tool is Make.com (formerly Integromat) because of its visual workflow builder and cost-effectiveness. You also use Zapier or n8n when clients specifically request them.

Write a compelling Upwork proposal for this job.

JOB TITLE: {job_title}

JOB DESCRIPTION:
{job_description[:800]}

REQUIRED SKILLS: {job_skills}

BUDGET: {budget}

CRITICAL RULES:
1. Start with a hook that shows you understand their SPECIFIC problem
2. Be conversational, not formal - no generic openings
3. If they mention Zapier/n8n specifically, use that tool. Otherwise, recommend Make.com for flexibility and cost savings
4. Keep it SHORT - under 250 words. Clients don't read long proposals.
5. End with a clear call to action
6. NO generic phrases like "I came across your posting"
7. DO NOT make up fake stats or claim experience you don't have (no "I've built 100+ workflows" or "worked with 50+ clients")
8. Instead of fake social proof, be compelling through: understanding their problem, clear solution approach, specific deliverables, realistic timeline
9. Sound confident through CLARITY and SPECIFICITY, not inflated claims
10. Include a specific timeline estimate

Generate ONLY the proposal text, ready to submit."""

        response = client.messages.create(
            model="claude-opus-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        proposal = response.content[0].text.strip()
        word_count = len(proposal.split())
        
        log_to_slack(f"✅ Proposal generated ({word_count} words)")
        
        return {
            "status": "success",
            "proposal": proposal,
            "word_count": word_count,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        log_to_slack(f"❌ Proposal generation failed: {str(e)}")
        return {"status": "error", "message": str(e)}


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("upwork-secrets")],
    timeout=300,
)
def sync_to_airtable(jobs: list) -> dict:
    """
    Sync jobs to Airtable.
    """
    import requests
    
    api_key = os.environ.get("AIRTABLE_API_KEY")
    base_id = os.environ.get("AIRTABLE_UPWORK_BASE_ID")
    table_name = "Upwork Jobs"
    
    log_to_slack(f"📤 Syncing {len(jobs)} jobs to Airtable...")
    
    url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
    headers = get_airtable_headers()
    
    synced = 0
    failed = 0
    
    try:
        for job in jobs:
            record = {
                "fields": {
                    "Job Title": job.get("title", ""),
                    "Description": job.get("description", "")[:10000],
                    "Budget": str(job.get("budget", "")),
                    "Skills": job.get("skills", ""),
                    "Job URL": job.get("url", ""),
                    "Status": "New",
                    "Scraped At": datetime.now().isoformat()
                }
            }
            
            response = requests.post(url, headers=headers, json=record, timeout=30)
            if response.status_code in [200, 201]:
                synced += 1
            else:
                failed += 1
        
        log_to_slack(f"✅ Sync complete: {synced} synced, {failed} failed")
        
        return {
            "status": "success",
            "synced": synced,
            "failed": failed,
            "airtable_url": f"https://airtable.com/{base_id}",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        log_to_slack(f"❌ Sync failed: {str(e)}")
        return {"status": "error", "message": str(e)}


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("upwork-secrets")],
    timeout=300,
)
def check_airtable_status() -> dict:
    """
    Check Airtable for status changes and process them.
    
    - "Under Review" without proposal → Generate proposal
    - "Rejected" → Delete record
    """
    import requests
    
    api_key = os.environ.get("AIRTABLE_API_KEY")
    base_id = os.environ.get("AIRTABLE_UPWORK_BASE_ID")
    table_name = "Upwork Jobs"
    
    log_to_slack("🔄 Checking Airtable for status changes...")
    
    url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
    headers = get_airtable_headers()
    
    results = {
        "proposals_generated": 0,
        "records_deleted": 0,
        "approved_count": 0
    }
    
    try:
        # 1. Check for "Under Review" jobs needing proposals
        params = {
            'filterByFormula': "AND({Status} = 'Under Review', {Proposal} = '')",
            'maxRecords': 5
        }
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code == 200:
            records = response.json().get('records', [])
            for record in records:
                record_id = record['id']
                fields = record.get('fields', {})
                
                proposal_result = generate_proposal.remote(
                    job_title=fields.get('Job Title', ''),
                    job_description=fields.get('Description', ''),
                    job_skills=fields.get('Skills', ''),
                    budget=fields.get('Budget', 'Not specified')
                )
                
                if proposal_result.get('status') == 'success':
                    update_url = f"{url}/{record_id}"
                    update_data = {
                        "fields": {
                            "Proposal": proposal_result['proposal'],
                            "Notes": f"Proposal auto-generated at {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                        }
                    }
                    requests.patch(update_url, headers=headers, json=update_data, timeout=30)
                    results["proposals_generated"] += 1
                    log_to_slack(f"✍️ Generated proposal for: {fields.get('Job Title', '')[:40]}...")
        
        # 2. Check for "Rejected" jobs to delete
        params = {
            'filterByFormula': "{Status} = 'Rejected'",
            'maxRecords': 50
        }
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code == 200:
            records = response.json().get('records', [])
            for record in records:
                record_id = record['id']
                job_title = record.get('fields', {}).get('Job Title', 'Unknown')
                
                delete_url = f"{url}/{record_id}"
                del_response = requests.delete(delete_url, headers=headers, timeout=30)
                
                if del_response.status_code == 200:
                    results["records_deleted"] += 1
                    log_to_slack(f"🗑️ Deleted rejected: {job_title[:40]}...")
        
        # 3. Count approved jobs
        params = {
            'filterByFormula': "{Status} = 'Approved'",
            'maxRecords': 100
        }
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code == 200:
            results["approved_count"] = len(response.json().get('records', []))
        
        log_to_slack(f"✅ Status check complete: {results['proposals_generated']} proposals, {results['records_deleted']} deleted, {results['approved_count']} approved")
        
        return {
            "status": "success",
            **results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        log_to_slack(f"❌ Status check failed: {str(e)}")
        return {"status": "error", "message": str(e)}


# ============== Cron Scheduled Jobs ==============

@app.function(
    image=image,
    secrets=[modal.Secret.from_name("upwork-secrets")],
    # schedule=modal.Cron("0 9 * * *"),  # Daily at 9 AM UTC [PAUSED - consolidated with periodic check]
    timeout=600,
)
def daily_status_check():
    """Consolidated automated check for Airtable status changes (replaces both daily + periodic checks).

    Paused until needed. To re-enable:
    1. Uncomment the schedule=modal.Cron("0 9 * * *") line above
    2. Redeploy: modal deploy modal_upwork_agent.py
    """
    log_to_slack("⏰ Consolidated status check starting...")
    result = check_airtable_status.remote()
    log_to_slack(f"⏰ Check complete")
    return result


# ============== PAUSED - Consolidated into daily_status_check() ==============
# The following function has been consolidated with daily_status_check() above.
# It ran every 5 minutes (288 times/day), which was redundant.
# All status check logic now consolidated into single daily_status_check() function.
# To re-enable periodic checks (every 5 min), uncomment the schedule on daily_status_check() above.
#
# @app.function(
#     image=image,
#     secrets=[modal.Secret.from_name("upwork-secrets")],
#     schedule=modal.Cron("*/5 * * * *"),  # Every 5 minutes
#     timeout=300,
# )
# def periodic_status_check():
#     """Check Airtable for status changes every 5 minutes."""
#     result = check_airtable_status.remote()
#     return result
# ============================================================================


# ============== Scraper Functions ==============

@app.function(
    image=scraper_image,
    secrets=[modal.Secret.from_name("upwork-secrets"), modal.Secret.from_name("upwork-cookies")],
    timeout=900,  # 15 minutes for scraping
    memory=2048,  # More memory for Chrome
)
def scrape_upwork_jobs(
    search_terms: list = None,
    max_jobs_per_term: int = 15,
    max_pages_per_term: int = 2
) -> dict:
    """
    Scrape Upwork jobs using Selenium with cookie authentication.
    """
    import json
    import time
    import re
    from urllib.parse import quote_plus
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    
    # Default search terms for AI/automation jobs
    DEFAULT_TERMS = [
        "AI automation",
        "Make.com",
        "Zapier integration",
        "n8n workflow",
        "no code automation",
        "workflow automation",
        "AI agent",
        "ChatGPT integration",
    ]
    
    if search_terms is None:
        search_terms = DEFAULT_TERMS
    
    log_to_slack(f"🔍 Starting Upwork scrape for {len(search_terms)} search terms...")
    
    # Load cookies from environment
    cookies_json = os.environ.get("UPWORK_COOKIES", "[]")
    log_to_slack(f"📦 Cookies JSON length: {len(cookies_json)}")
    
    try:
        cookies = json.loads(cookies_json)
        log_to_slack(f"🍪 Parsed {len(cookies)} cookies")
    except Exception as e:
        log_to_slack(f"❌ Failed to parse UPWORK_COOKIES: {str(e)}")
        return {"status": "error", "message": "Invalid cookies"}
    
    if not cookies:
        log_to_slack("❌ No Upwork cookies configured")
        return {"status": "error", "message": "No cookies"}
    
    # Setup Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.binary_location = "/usr/bin/chromium"
    
    driver = None
    all_jobs = []
    seen_ids = set()
    
    try:
        log_to_slack("🚀 Starting Chrome...")
        driver = webdriver.Chrome(options=chrome_options)
        
        # Load cookies
        log_to_slack("🌐 Loading upwork.com...")
        driver.get("https://www.upwork.com")
        time.sleep(2)
        driver.delete_all_cookies()
        
        added_cookies = 0
        for cookie in cookies:
            try:
                cookie_dict = {
                    'name': cookie.get('name'),
                    'value': cookie.get('value'),
                    'domain': cookie.get('domain', '.upwork.com'),
                    'path': cookie.get('path', '/'),
                }
                if cookie.get('secure'):
                    cookie_dict['secure'] = cookie['secure']
                driver.add_cookie(cookie_dict)
                added_cookies += 1
            except:
                pass
        
        log_to_slack(f"🍪 Added {added_cookies} cookies")
        driver.refresh()
        time.sleep(3)
        
        # Check login
        log_to_slack("🔐 Checking login status...")
        driver.get("https://www.upwork.com/nx/find-work/")
        time.sleep(5)
        
        current_url = driver.current_url
        log_to_slack(f"📍 Current URL: {current_url[:80]}...")
        
        if "login" in current_url.lower():
            log_to_slack("❌ Not logged in - cookies expired. Please re-export cookies.")
            return {"status": "error", "message": "Cookies expired - please update"}
        
        log_to_slack("✅ Logged into Upwork successfully!")
        
        # Scrape each search term
        for term in search_terms:
            term_jobs = []
            log_to_slack(f"🔎 Searching: {term}")
            
            for page in range(1, max_pages_per_term + 1):
                if len(term_jobs) >= max_jobs_per_term:
                    break
                
                encoded_term = quote_plus(term)
                url = f"https://www.upwork.com/nx/search/jobs/?q={encoded_term}&sort=recency&payment_verified=1"
                if page > 1:
                    url += f"&page={page}"
                
                try:
                    driver.get(url)
                    time.sleep(4)
                    
                    # Try multiple selectors for job tiles
                    job_tiles = driver.find_elements(By.CSS_SELECTOR, "article[data-test='JobTile']")
                    if not job_tiles:
                        job_tiles = driver.find_elements(By.CSS_SELECTOR, "section.job-tile")
                    if not job_tiles:
                        job_tiles = driver.find_elements(By.CSS_SELECTOR, "[data-test='job-tile-list'] > div")
                    
                    log_to_slack(f"   Found {len(job_tiles)} job tiles on page {page}")
                    
                    if not job_tiles:
                        # Debug: log page source snippet
                        page_text = driver.page_source[:500]
                        log_to_slack(f"   Page snippet: {page_text[:200]}...")
                    
                    for tile in job_tiles:
                        try:
                            # Title and URL - try multiple selectors
                            title_elem = None
                            for selector in ["a[data-test='job-tile-title-link']", "h2 a", "a.job-title", ".job-tile-title a"]:
                                try:
                                    title_elem = tile.find_element(By.CSS_SELECTOR, selector)
                                    if title_elem:
                                        break
                                except:
                                    continue
                            
                            if not title_elem:
                                continue
                                
                            title = title_elem.text.strip()
                            job_url = title_elem.get_attribute("href")
                            
                            # Job ID
                            job_id = None
                            if job_url:
                                match = re.search(r'/jobs/~(\w+)', job_url)
                                if match:
                                    job_id = match.group(1)
                            
                            if job_id and job_id in seen_ids:
                                continue
                            
                            # Description
                            description = ""
                            try:
                                desc_elem = tile.find_element(By.CSS_SELECTOR, "[data-test='job-description-text'], [data-test='UpCLineClamp JobDescription']")
                                description = desc_elem.text.strip()
                            except:
                                pass
                            
                            # Budget
                            budget = ""
                            try:
                                budget_elem = tile.find_element(By.CSS_SELECTOR, "[data-test='is-fixed-price'], [data-test='job-type-label']")
                                budget = budget_elem.text.strip()
                            except:
                                pass
                            
                            # Skills
                            skills = []
                            try:
                                skill_elems = tile.find_elements(By.CSS_SELECTOR, "[data-test='token']")
                                skills = [s.text.strip() for s in skill_elems if s.text.strip()]
                            except:
                                pass
                            
                            if job_id:
                                seen_ids.add(job_id)
                                term_jobs.append({
                                    "id": job_id,
                                    "title": title,
                                    "description": description,
                                    "budget": budget,
                                    "skills": skills,
                                    "url": job_url,
                                    "search_term": term,
                                    "scraped_at": datetime.now().isoformat()
                                })
                        except:
                            continue
                    
                except Exception as e:
                    print(f"Error on page {page}: {e}")
                    break
                
                time.sleep(2)
            
            all_jobs.extend(term_jobs[:max_jobs_per_term])
            time.sleep(2)
        
        log_to_slack(f"✅ Scraped {len(all_jobs)} jobs from Upwork")
        
        return {
            "status": "success",
            "jobs": all_jobs,
            "count": len(all_jobs),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        log_to_slack(f"❌ Scraping error: {str(e)}")
        return {"status": "error", "message": str(e)}
        
    finally:
        if driver:
            driver.quit()


@app.function(
    image=scraper_image,
    secrets=[modal.Secret.from_name("upwork-secrets"), modal.Secret.from_name("upwork-cookies")],
    schedule=modal.Cron("0 14 * * *"),  # Daily at 2 PM UTC (9 AM EST)
    timeout=1200,  # 20 minutes
    memory=2048,
)
def daily_scrape_and_sync():
    """Daily job scraping and sync to Airtable."""
    import requests
    
    log_to_slack("🚀 Starting daily Upwork job scrape...")
    
    # Scrape jobs
    result = scrape_upwork_jobs.remote()
    
    if result.get("status") != "success":
        log_to_slack(f"❌ Scrape failed: {result.get('message')}")
        return result
    
    jobs = result.get("jobs", [])
    
    if not jobs:
        log_to_slack("⚠️ No jobs found")
        return {"status": "success", "message": "No jobs to sync", "count": 0}
    
    # Sync to Airtable
    api_key = os.environ.get("AIRTABLE_API_KEY")
    base_id = os.environ.get("AIRTABLE_UPWORK_BASE_ID")
    table_name = "Upwork Jobs"
    
    url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Get existing job URLs to avoid duplicates
    existing_urls = set()
    try:
        params = {'fields[]': 'Job URL', 'maxRecords': 500}
        response = requests.get(url, headers=headers, params=params, timeout=30)
        if response.status_code == 200:
            for record in response.json().get('records', []):
                job_url = record.get('fields', {}).get('Job URL', '')
                if job_url:
                    existing_urls.add(job_url)
    except:
        pass
    
    # Sync new jobs only
    synced = 0
    skipped = 0
    
    for job in jobs:
        if job.get('url') in existing_urls:
            skipped += 1
            continue
        
        # Format skills as comma-separated string
        skills_str = ", ".join(job.get('skills', [])) if isinstance(job.get('skills'), list) else job.get('skills', '')
        
        record = {
            "fields": {
                "Job Title": job.get("title", "")[:255],
                "Description": job.get("description", "")[:10000],
                "Budget": str(job.get("budget", "")),
                "Skills": skills_str,
                "Job URL": job.get("url", ""),
                "Status": "New",
                "Scraped At": job.get("scraped_at", datetime.now().isoformat())
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=record, timeout=30)
            if response.status_code in [200, 201]:
                synced += 1
            time.sleep(0.2)  # Rate limiting
        except:
            pass
    
    log_to_slack(f"✅ Daily sync complete: {synced} new jobs added, {skipped} duplicates skipped")
    
    return {
        "status": "success",
        "synced": synced,
        "skipped": skipped,
        "total_scraped": len(jobs),
        "timestamp": datetime.now().isoformat()
    }


# ============== Web Endpoints ==============

@app.function(image=image, secrets=[modal.Secret.from_name("upwork-secrets")])
@modal.fastapi_endpoint(method="GET")
def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "upwork-automation",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("upwork-secrets")],
    timeout=120,
)
@modal.fastapi_endpoint(method="POST")
def webhook_proposal(job_title: str, job_description: str, job_skills: str = "", budget: str = "Not specified"):
    """Generate a proposal via webhook."""
    return generate_proposal.remote(
        job_title=job_title,
        job_description=job_description,
        job_skills=job_skills,
        budget=budget
    )


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("upwork-secrets")],
    timeout=300,
)
@modal.fastapi_endpoint(method="POST")
def webhook_status_check(payload: dict = None):
    """
    Handle Airtable automation triggers for status changes.
    
    Can be called in two ways:
    1. From Airtable Automation with record_id and status
    2. As a generic trigger to check all records
    
    Airtable Automation payload format:
    {
        "record_id": "recXXXXXXXXXXXX",
        "status": "Under Review" or "Rejected",
        "job_title": "Optional - for logging"
    }
    """
    import requests
    
    # If no payload or no record_id, do a full scan
    if not payload or not payload.get("record_id"):
        return check_airtable_status.remote()
    
    # Process specific record from Airtable automation
    record_id = payload.get("record_id")
    status = payload.get("status", "").strip()
    job_title = payload.get("job_title", "Unknown Job")[:50]
    
    log_to_slack(f"🔔 Airtable trigger: {job_title} → {status}")
    
    api_key = os.environ.get("AIRTABLE_API_KEY")
    base_id = os.environ.get("AIRTABLE_UPWORK_BASE_ID")
    table_name = "Upwork Jobs"
    
    url = f"https://api.airtable.com/v0/{base_id}/{table_name}/{record_id}"
    headers = get_airtable_headers()
    
    try:
        if status == "Under Review":
            # Fetch record details
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code != 200:
                return {"status": "error", "message": "Record not found"}
            
            record = response.json()
            fields = record.get('fields', {})
            
            # Check if proposal already exists
            if fields.get('Proposal'):
                return {"status": "skipped", "message": "Proposal already exists"}
            
            # Generate proposal
            proposal_result = generate_proposal.remote(
                job_title=fields.get('Job Title', ''),
                job_description=fields.get('Description', ''),
                job_skills=fields.get('Skills', ''),
                budget=fields.get('Budget', 'Not specified')
            )
            
            if proposal_result.get('status') == 'success':
                # Update record with proposal
                update_data = {
                    "fields": {
                        "Proposal": proposal_result['proposal'],
                        "Notes": f"Proposal auto-generated at {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                    }
                }
                requests.patch(url, headers=headers, json=update_data, timeout=30)
                log_to_slack(f"✍️ Generated proposal for: {job_title}")
                return {
                    "status": "success",
                    "action": "proposal_generated",
                    "job_title": job_title,
                    "word_count": proposal_result.get('word_count', 0)
                }
            else:
                return {"status": "error", "message": "Proposal generation failed"}
        
        elif status == "Rejected":
            # Delete the record
            del_response = requests.delete(url, headers=headers, timeout=30)
            if del_response.status_code == 200:
                log_to_slack(f"🗑️ Deleted rejected: {job_title}")
                return {"status": "success", "action": "deleted", "job_title": job_title}
            else:
                return {"status": "error", "message": "Delete failed"}
        
        else:
            return {"status": "ignored", "message": f"No action for status: {status}"}
    
    except Exception as e:
        log_to_slack(f"❌ Webhook error: {str(e)}")
        return {"status": "error", "message": str(e)}


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("upwork-secrets")],
    timeout=300,
)
@modal.fastapi_endpoint(method="POST")  
def webhook_sync(jobs: list):
    """Sync jobs to Airtable via webhook."""
    return sync_to_airtable.remote(jobs=jobs)


@app.function(
    image=scraper_image,
    secrets=[modal.Secret.from_name("upwork-secrets"), modal.Secret.from_name("upwork-cookies")],
    timeout=1200,
    memory=2048,
)
@modal.fastapi_endpoint(method="POST")
def webhook_scrape():
    """Manually trigger job scraping and sync to Airtable."""
    return daily_scrape_and_sync.remote()


# ============== Local Testing ==============

@app.local_entrypoint()
def main():
    """Local testing entrypoint."""
    print("Testing proposal generation...")
    
    result = generate_proposal.remote(
        job_title="Need Make.com Expert for CRM Integration",
        job_description="Connect HubSpot to Mailchimp and Google Sheets. When new lead comes in, add to sequence and notify team on Slack.",
        job_skills="Make.com, HubSpot, API Integration",
        budget="$500-800"
    )
    
    print("\n" + "="*60)
    print("GENERATED PROPOSAL")
    print("="*60)
    print(result.get("proposal", "Error generating proposal"))
    print("="*60)
    print(f"Word count: {result.get('word_count', 'N/A')}")
