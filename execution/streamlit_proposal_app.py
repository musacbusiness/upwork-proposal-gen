#!/usr/bin/env python3
"""
Streamlit web app for Upwork Proposal Generator
Accessible from anywhere - phone, tablet, desktop
Optimized for Streamlit Cloud (no web scraping)
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
    </style>
""", unsafe_allow_html=True)

# Title
st.title("📝 Upwork Proposal Generator")
st.markdown("Generate personalized proposals in seconds. Works on desktop, tablet, or phone.")

# Sidebar info
with st.sidebar:
    st.markdown("### How It Works")
    st.markdown("""
    1. **Paste** the job description from Upwork
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
st.markdown("### Paste Job Description")
st.markdown("*Copy the full job description from Upwork and paste it below*")

job_description = st.text_area(
    "Job Description",
    height=250,
    placeholder="Paste the full job description from Upwork here...",
    label_visibility="collapsed"
)

job_title = st.text_input(
    "Job Title (optional)",
    placeholder="e.g., 'Build AI chatbot integration'",
    label_visibility="collapsed"
)

# Session state for proposal storage
if "proposal" not in st.session_state:
    st.session_state.proposal = None

if "job_data" not in st.session_state:
    st.session_state.job_data = None

# Generate button
generate_btn = st.button(
    "🚀 Generate Proposal",
    use_container_width=True,
    key="generate_btn"
)

# Generate proposal on button click
if generate_btn:
    if not job_description or len(job_description.strip()) < 50:
        st.error("⚠️ Please paste a full job description (at least 50 characters)")
    else:
        with st.spinner("🤖 Generating proposal..."):
            try:
                # Check if API key is set
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    st.error("❌ API key not found. Please add ANTHROPIC_API_KEY to Streamlit Secrets.")
                    st.stop()

                st.info(f"✓ API key found ({len(api_key)} chars)")

                # Initialize generator
                st.write("Initializing proposal generator...")
                generator = ProposalGenerator()
                st.write("✓ Generator initialized")

                # Prepare job data
                job_data = {
                    'job_id': 'upwork_job',
                    'title': job_title or 'Upwork Job',
                    'description': job_description.strip(),
                    'budget': 'Not specified',
                    'skills': [],
                    'level': 'Not specified'
                }

                st.write("Calling Claude API...")
                # Generate proposal
                proposal = generator.generate_proposal(job_data)
                st.write(f"✓ API returned: {len(proposal) if proposal else 0} chars")

                if proposal:
                    st.session_state.proposal = proposal
                    st.session_state.job_data = job_data
                    st.success("✓ Proposal generated successfully!")
                else:
                    st.error("❌ Proposal generation returned empty.")

            except Exception as e:
                st.error(f"❌ ERROR: {type(e).__name__}")
                st.error(f"Details: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

# Display proposal if generated
if st.session_state.proposal:
    st.markdown("---")
    st.markdown("### ✅ Your Proposal")

    # Display proposal in box
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

            proposal_file = proposals_dir / f"proposal_{st.session_state.job_data.get('job_id', 'proposal')}.txt"

            with open(proposal_file, 'w') as f:
                f.write(st.session_state.proposal)

            st.success(f"✓ Saved locally")

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
        st.metric("Status", "✓ Ready to submit")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 12px; margin-top: 20px;">
    Proposals are generated in your voice - direct, analytical, client-focused.
    <br>
    Built with Claude AI + your voice profile.
    </div>
    """, unsafe_allow_html=True)
