"""
Modal deployment for Upwork Proposal Generator
This file defines the Modal functions that run in the cloud

Deploy with:
  modal deploy execution/modal_deploy.py

Or run locally with:
  modal run execution/modal_deploy.py
"""

import os
import modal
from pathlib import Path

# Create Modal app
app = modal.App("upwork-proposal-generator")

# Define image with all dependencies
image = (
    modal.Image.debian_slim()
    .pip_install(
        "selenium>=4.10.0",
        "anthropic>=0.7.0",
        "webdriver-manager>=4.0.1",
        "python-dotenv>=1.0.0",
        "requests>=2.31.0",
    )
)


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("upwork-proposal-secrets")],
    timeout=600,
)
def generate_proposal(job_url: str = None, job_description: str = None) -> dict:
    """
    Generate a proposal from either a job URL or manual description

    Args:
        job_url: Upwork job URL (will try to scrape)
        job_description: Full job description text (fallback/manual)

    Returns:
        {
            "success": bool,
            "proposal": str (if successful),
            "error": str (if failed),
            "job_data": dict
        }
    """
    import anthropic
    from datetime import datetime

    try:
        # If we have a description, use it directly
        if job_description:
            job_data = {
                'job_id': 'manual_' + datetime.now().strftime('%Y%m%d_%H%M%S'),
                'title': 'Upwork Job (Manual)',
                'description': job_description,
                'budget': 'Not specified',
                'skills': [],
                'level': 'Not specified'
            }
        elif job_url:
            # Try to scrape the URL
            try:
                from selenium import webdriver
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                from selenium.webdriver.chrome.options import Options
                from selenium.webdriver.chrome.service import Service
                from webdriver_manager.chrome import ChromeDriverManager

                chrome_options = Options()
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-blink-features=AutomationControlled")
                chrome_options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36")

                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)

                driver.get(job_url)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "job-details"))
                )

                job_data = {
                    'job_id': job_url.split('/')[-1].split('~')[0] if '~' in job_url else 'unknown',
                    'title': 'Upwork Job',
                    'description': '',
                    'budget': 'Not specified',
                    'skills': [],
                    'level': 'Not specified'
                }

                # Extract title
                try:
                    title = driver.find_element(By.CSS_SELECTOR, 'h1[class*="title"]')
                    job_data['title'] = title.text.strip()
                except:
                    pass

                # Extract description
                try:
                    desc = driver.find_element(By.CSS_SELECTOR, '[class*="description"]')
                    job_data['description'] = desc.text.strip()
                except:
                    pass

                driver.quit()

            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to scrape job: {str(e)}. Please provide job description manually.",
                    "job_data": None
                }
        else:
            return {
                "success": False,
                "error": "Please provide either job_url or job_description",
                "job_data": None
            }

        # Check we have a description
        if not job_data.get('description'):
            return {
                "success": False,
                "error": "No job description found",
                "job_data": job_data
            }

        # Generate proposal using Claude
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        voice_profile = """
        You are Musa Comma, a 23-year-old founder and automation expert.

        CORE TRAITS:
        - Analytical + willing to take leaps of faith when worst case is survivable
        - Direct, no fluff - calls out BS clearly
        - Truth-focused - authenticity over polish
        - Client-centric - success = clients winning (scaling, saving time, more money)
        - Numbers-driven - use concrete examples and metrics

        YOUR EXPERIENCE:
        - Founded MC Marketing Solutions (2019-2023): Learned businesses need structure & automation
        - Founder of ScaleAxis (2024-present): Building AI-powered automation platform
        - Skills: Business automation, AI integration, market analysis, strategic thinking

        HOW YOU TALK:
        1. Open with their pain point (show you understand)
        2. Make it concrete - use numbers and real scenarios
        3. Explain opportunity cost of NOT acting
        4. Show ROI/speed-to-payback
        5. Paint the potential
        6. Direct and honest - no hype, no exaggeration
        """

        prompt = f"""Write a proposal for this Upwork job.

JOB TITLE: {job_data.get('title', 'Unknown')}
BUDGET: {job_data.get('budget', 'Not specified')}
JOB DESCRIPTION: {job_data.get('description', '')}

REQUIREMENTS:
- Length: 150-250 words
- Structure: Open with their pain point → Why you're a fit → Your approach → Outcome/ROI → Call to action
- Include: At least one concrete metric or ROI calculation
- Tone: Direct, professional, authentic
- Be specific: Reference details from their job description
- No fluff: No "I'm excited to help you"

Write ONLY the proposal text. No intro, no closing, no notes. Just the proposal."""

        message = client.messages.create(
            model="claude-opus-4-5-20251101",
            max_tokens=1024,
            temperature=0.7,
            system=voice_profile,
            messages=[{"role": "user", "content": prompt}]
        )

        proposal = message.content[0].text.strip()

        return {
            "success": True,
            "proposal": proposal,
            "job_data": job_data
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Error: {str(e)}",
            "job_data": None
        }


@app.local_entrypoint()
def main(job_url: str = None, job_description: str = None):
    """Local entrypoint for testing"""
    print("Testing proposal generation...")
    result = generate_proposal.remote(job_url, job_description)

    if result["success"]:
        print("\n✅ SUCCESS!")
        print("\nProposal:")
        print("=" * 60)
        print(result["proposal"])
        print("=" * 60)
    else:
        print(f"\n❌ Error: {result['error']}")
