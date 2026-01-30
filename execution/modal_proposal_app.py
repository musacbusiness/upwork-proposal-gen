#!/usr/bin/env python3
"""
Modal deployment for Upwork Proposal Generator
Deploy to Modal Cloud - runs 24/7, accessible anywhere

Deploy: modal deploy execution/modal_proposal_app.py

Access: https://your-username--proposal-generator.modal.run
"""

import os
import sys
from pathlib import Path
from datetime import datetime

import modal
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Modal app
app = modal.App("upwork-proposal-generator")

# Define Modal image with all dependencies
image = (
    modal.Image.debian_slim()
    .pip_install(
        "streamlit>=1.28",
        "selenium>=4.0",
        "anthropic>=0.7",
        "webdriver-manager>=4.0",
        "python-dotenv>=1.0",
        "requests>=2.31",
    )
)

# Modal function to generate proposals (can be called from Streamlit or standalone)
@app.function(image=image, secrets=[modal.Secret.from_name("upwork-proposal-secrets")])
def generate_proposal_modal(job_url: str, manual_description: str = None) -> dict:
    """
    Generate a proposal from a job URL or manual description

    Returns: {
        "success": bool,
        "proposal": str,
        "job_data": dict,
        "error": str (if failed)
    }
    """
    try:
        import anthropic
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.common.exceptions import TimeoutException, NoSuchElementException
        from webdriver_manager.chrome import ChromeDriverManager

        # Job scraping
        job_data = {}

        if manual_description:
            job_data['description'] = manual_description
            job_data['title'] = 'Upwork Job (Manual)'
            job_data['job_id'] = 'manual_' + datetime.now().strftime('%Y%m%d_%H%M%S')
        else:
            # Try to scrape
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36")

            try:
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
                wait = WebDriverWait(driver, 10)

                driver.get(job_url)
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "job-details")))

                # Extract job details
                job_data = {
                    'job_id': job_url.split('/')[-1].split('~')[0],
                    'title': 'Upwork Job',
                    'description': '',
                    'budget': 'Not specified',
                    'skills': [],
                    'level': 'Not specified'
                }

                try:
                    title = driver.find_element(By.CSS_SELECTOR, 'h1[class*="title"]')
                    job_data['title'] = title.text.strip()
                except:
                    pass

                try:
                    desc = driver.find_element(By.CSS_SELECTOR, '[class*="description"]')
                    job_data['description'] = desc.text.strip()
                except:
                    pass

                driver.quit()

            except Exception as e:
                return {
                    "success": False,
                    "error": f"Scraping failed: {str(e)}. Please provide job description manually."
                }

        if not job_data.get('description'):
            return {
                "success": False,
                "error": "No job description found. Please provide it manually."
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

        HOW YOU TALK:
        1. Open with their pain point (show you understand)
        2. Make it concrete - use numbers and real scenarios
        3. Explain opportunity cost of NOT acting
        4. Show ROI/speed-to-payback
        5. Paint the potential
        6. Direct and honest - no hype
        """

        prompt = f"""Write a proposal for this Upwork job.

JOB:
Title: {job_data.get('title', 'Unknown')}
Budget: {job_data.get('budget', 'Not specified')}
Description: {job_data.get('description', '')}

WRITE:
- Length: 150-250 words
- Structure: Pain point → Why you fit → Approach → Outcome → CTA
- Include: At least one concrete metric/ROI
- Tone: Direct, professional, authentic
- No intro/closing - just the proposal

Start with the proposal text only."""

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
            "error": f"Generation failed: {str(e)}"
        }


# Streamlit app (runs as Modal web endpoint)
@app.function(
    image=image.run_function(lambda: __import__("streamlit.web.cli").web.cli.main),
    secrets=[modal.Secret.from_name("upwork-proposal-secrets")],
    timeout=3600,
)
@modal.web_endpoint()
def streamlit_app(request):
    """Streamlit app endpoint on Modal"""
    # This is a simplified approach - for full Streamlit on Modal,
    # we'd use the streamlit_from_path approach
    pass


# Local Streamlit app (for testing/development)
def main_streamlit():
    """Local Streamlit interface for development"""
    st.set_page_config(
        page_title="Upwork Proposal Generator",
        page_icon="📝",
        layout="wide"
    )

    st.title("📝 Upwork Proposal Generator (Modal Cloud)")
    st.markdown("Generate proposals 24/7, your Mac stays off.")

    with st.sidebar:
        st.markdown("### Running on Modal")
        st.markdown("This app runs in the cloud 24/7")

    job_url = st.text_input(
        "Upwork Job URL",
        placeholder="https://www.upwork.com/jobs/...",
        label_visibility="collapsed"
    )

    manual_desc = st.text_area(
        "Or paste job description",
        placeholder="Paste full job description here...",
        height=150,
        label_visibility="collapsed"
    )

    if st.button("🚀 Generate Proposal", use_container_width=True):
        if not job_url and not manual_desc:
            st.error("Provide either a URL or job description")
        else:
            with st.spinner("Generating..."):
                result = generate_proposal_modal.remote(job_url if job_url else "", manual_desc)

                if result["success"]:
                    st.success("✓ Proposal generated!")
                    st.markdown("### Proposal")
                    st.markdown(result["proposal"])

                    # Copy button
                    if st.button("📋 Copy to Clipboard"):
                        st.write(result["proposal"])
                        st.info("Copy the proposal above manually")
                else:
                    st.error(f"Failed: {result['error']}")


if __name__ == "__main__":
    main_streamlit()
