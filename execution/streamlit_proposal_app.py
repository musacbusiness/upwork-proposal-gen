#!/usr/bin/env python3
"""
Streamlit web app for Upwork Proposal Generator
Accessible from anywhere - phone, tablet, desktop
Run: streamlit run execution/streamlit_proposal_app.py
"""

import streamlit as st
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from generate_upwork_proposal import (
    UpworkScraper,
    ProposalGenerator,
    ClipboardManager,
)

# Page config
st.set_page_config(
    page_title="Upwork Proposal Generator",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        max-width: 900px;
        margin: 0 auto;
    }
    .stButton > button {
        width: 100%;
        padding: 12px;
        font-size: 16px;
        border-radius: 8px;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 16px;
        margin: 16px 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 8px;
        padding: 16px;
        margin: 16px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.title("📝 Upwork Proposal Generator")
st.markdown("Generate personalized proposals in seconds. Works on desktop, tablet, or phone.")

# Sidebar info
with st.sidebar:
    st.markdown("### How It Works")
    st.markdown("""
    1. **Paste** an Upwork job link
    2. **Generate** a personalized proposal
    3. **Copy** to clipboard
    4. **Paste** into Upwork

    Your proposals are written in your voice - direct, analytical, numbers-focused.
    """)

    st.markdown("---")
    st.markdown("### Your Voice")
    st.markdown("""
    - ✓ Analytical
    - ✓ Numbers-driven
    - ✓ Direct, no fluff
    - ✓ Client-centric
    - ✓ Authentic
    """)

# Main interface
col1, col2 = st.columns([3, 1], gap="large")

with col1:
    st.markdown("### Paste Your Job Link")
    job_url = st.text_input(
        "Upwork Job URL",
        placeholder="https://www.upwork.com/jobs/...",
        label_visibility="collapsed"
    )

# Session state for proposal storage
if "proposal" not in st.session_state:
    st.session_state.proposal = None

if "job_data" not in st.session_state:
    st.session_state.job_data = None

if "generating" not in st.session_state:
    st.session_state.generating = False

# Generate button
col1, col2 = st.columns([3, 1])

with col1:
    generate_btn = st.button(
        "🚀 Generate Proposal",
        use_container_width=True,
        key="generate_btn"
    )

# Generate proposal on button click
if generate_btn and job_url:
    if "upwork.com/jobs/" not in job_url:
        st.error("⚠️ Please provide a valid Upwork job URL")
    else:
        with st.spinner("🔄 Generating proposal..."):
            try:
                # Initialize scraper and generator
                scraper = UpworkScraper()
                generator = ProposalGenerator()

                # Try to scrape job
                st.info("📥 Fetching job details...")
                job_data = scraper.scrape_job(job_url)

                # Store job data in session
                st.session_state.job_data = job_data

                if not job_data or not job_data.get('description'):
                    st.warning("⚠️ Could not scrape job page (may need manual entry)")
                    st.markdown("**Fallback:** Copy the job description from Upwork and paste it below:")

                    manual_description = st.text_area(
                        "Job Description",
                        height=200,
                        placeholder="Paste the full job description here...",
                        label_visibility="collapsed"
                    )

                    if manual_description:
                        job_data = job_data or {}
                        job_data['description'] = manual_description
                        job_data['title'] = job_data.get('title', 'Upwork Job')
                        st.session_state.job_data = job_data

                        with st.spinner("🤖 Generating proposal..."):
                            proposal = generator.generate_proposal(job_data)
                            st.session_state.proposal = proposal
                else:
                    # Generate proposal
                    st.info(f"📋 Job: {job_data.get('title', 'Unknown')}")
                    st.info(f"💰 Budget: {job_data.get('budget', 'Not specified')}")

                    with st.spinner("🤖 Generating proposal..."):
                        proposal = generator.generate_proposal(job_data)
                        st.session_state.proposal = proposal

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# Display proposal if generated
if st.session_state.proposal:
    st.markdown("---")
    st.markdown("### ✅ Your Proposal")

    # Display proposal in expandable box
    with st.container():
        st.markdown("""
        <div style="background-color: #f0f2f6; padding: 20px; border-radius: 8px; border-left: 4px solid #1f77b4;">
        """, unsafe_allow_html=True)

        st.markdown(st.session_state.proposal)

        st.markdown("</div>", unsafe_allow_html=True)

    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("📋 Copy to Clipboard", use_container_width=True):
            ClipboardManager.copy_to_clipboard(st.session_state.proposal)
            st.success("✓ Copied to clipboard!")

    with col2:
        if st.button("💾 Save as Text", use_container_width=True):
            proposals_dir = Path(".tmp/proposals")
            proposals_dir.mkdir(parents=True, exist_ok=True)

            job_id = st.session_state.job_data.get('job_id', 'proposal')
            proposal_file = proposals_dir / f"{job_id}_proposal.txt"

            with open(proposal_file, 'w') as f:
                f.write(st.session_state.proposal)

            st.success(f"✓ Saved to {proposal_file}")

    with col3:
        if st.button("🔄 Generate New", use_container_width=True):
            st.session_state.proposal = None
            st.session_state.job_data = None
            st.rerun()

    # Quick stats
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        word_count = len(st.session_state.proposal.split())
        st.metric("Word Count", word_count)

    with col2:
        read_time = max(1, word_count // 200)
        st.metric("Read Time", f"{read_time} min")

    with col3:
        st.metric("Status", "Ready to submit")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 12px; margin-top: 20px;">
    Proposals are generated in your voice - direct, analytical, client-focused.
    <br>
    Built with Claude AI + your voice profile.
    </div>
    """, unsafe_allow_html=True)
