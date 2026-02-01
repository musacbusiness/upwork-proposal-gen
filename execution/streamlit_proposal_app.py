#!/usr/bin/env python3
"""
Streamlit web app for Upwork Proposal Generator
Accessible from anywhere - phone, tablet, desktop
Optimized for Streamlit Cloud (no web scraping)
"""

import streamlit as st
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment (for local testing)
load_dotenv()

# For Streamlit Cloud: set environment variable from secrets
if "ANTHROPIC_API_KEY" in st.secrets:
    os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]

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
    height=300,
    placeholder="Paste the full job description from Upwork here...",
    label_visibility="collapsed"
)

# Session state for proposal storage
if "proposal" not in st.session_state:
    st.session_state.proposal = None

if "job_data" not in st.session_state:
    st.session_state.job_data = None

if "proposal_score" not in st.session_state:
    st.session_state.proposal_score = None

if "show_regen_dialog" not in st.session_state:
    st.session_state.show_regen_dialog = False

if "regen_prompt" not in st.session_state:
    st.session_state.regen_prompt = ""

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
                    'title': 'Upwork Job',
                    'description': job_description.strip(),
                    'budget': 'Not specified',
                    'skills': [],
                    'level': 'Not specified',
                }

                st.write("Calling Claude API...")
                # Generate proposal (returns tuple of proposal text and score dict)
                result = generator.generate_proposal(job_data)

                if isinstance(result, tuple):
                    proposal, score = result
                else:
                    proposal = result
                    score = None

                st.write(f"✓ API returned: {len(proposal) if proposal else 0} chars")

                if proposal:
                    st.session_state.proposal = proposal
                    st.session_state.job_data = job_data
                    st.session_state.proposal_score = score
                    st.success("✓ Proposal generated successfully!")
                else:
                    st.error("❌ Proposal generation returned empty.")

                    # Try to read and display logs
                    try:
                        from pathlib import Path
                        log_file = Path(".tmp/upwork_proposal_log.txt")
                        if log_file.exists():
                            with open(log_file, 'r') as f:
                                logs = f.read()
                            st.warning("Debug logs:")
                            st.code(logs[-2000:])  # Show last 2000 chars of log
                    except Exception as log_err:
                        st.write(f"Could not read logs: {log_err}")

            except Exception as e:
                st.error(f"❌ ERROR: {type(e).__name__}")
                st.error(f"Details: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

# Display proposal if generated
if st.session_state.proposal:
    st.markdown("---")
    st.markdown("### ✅ Your Proposal")

    # Display proposal in a read-only text area for easy copying
    st.text_area(
        "Proposal",
        value=st.session_state.proposal,
        height=400,
        disabled=True,
        label_visibility="collapsed"
    )

    # Action buttons
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("**How to copy:**\n1. Triple-click the text above\n2. Cmd+C (Mac) or Ctrl+C (Windows/Linux)\n3. Paste into Upwork")

    with col2:
        col_sub1, col_sub2 = st.columns([1, 1])
        with col_sub1:
            if st.button("🔄 Generate New", use_container_width=True):
                st.session_state.show_regen_dialog = True
                st.rerun()
        with col_sub2:
            st.download_button(
                label="📥 Download",
                data=st.session_state.proposal,
                file_name=f"proposal.txt",
                mime="text/plain",
                use_container_width=True
            )

    # Regeneration dialog
    if st.session_state.show_regen_dialog:
        st.markdown("---")
        st.markdown("### ✏️ Regenerate Proposal")
        st.markdown("*Optionally add instructions for regeneration (e.g., 'make it more enthusiastic', 'focus on timeline')*")

        regen_prompt = st.text_area(
            "Regeneration Instructions",
            height=80,
            placeholder="Leave empty to generate fresh, or add specific guidance...",
            label_visibility="collapsed"
        )

        col_regen1, col_regen2 = st.columns(2)

        with col_regen1:
            if st.button("Generate", use_container_width=True, key="regen_with_prompt"):
                st.session_state.show_regen_dialog = False

                with st.spinner("🤖 Regenerating proposal..."):
                    try:
                        api_key = os.getenv("ANTHROPIC_API_KEY")
                        if not api_key:
                            st.error("❌ API key not found. Please add ANTHROPIC_API_KEY to Streamlit Secrets.")
                            st.stop()

                        generator = ProposalGenerator()

                        # Get job data and add regeneration instructions if provided
                        job_data = st.session_state.job_data.copy()
                        if regen_prompt.strip():
                            job_data['regen_instructions'] = regen_prompt.strip()

                        result = generator.generate_proposal(job_data)

                        if isinstance(result, tuple):
                            proposal, score = result
                        else:
                            proposal = result
                            score = None

                        if proposal:
                            st.session_state.proposal = proposal
                            st.session_state.proposal_score = score
                            st.success("✓ Proposal regenerated successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to regenerate proposal.")

                    except Exception as e:
                        st.error(f"❌ ERROR: {type(e).__name__}")
                        st.error(f"Details: {str(e)}")

        with col_regen2:
            if st.button("Cancel", use_container_width=True, key="cancel_regen"):
                st.session_state.show_regen_dialog = False
                st.rerun()

    # Quick stats and quality score
    st.markdown("---")

    # Display PQS score if available
    if st.session_state.proposal_score:
        score = st.session_state.proposal_score
        total_score = score.get('total_score', 0)
        max_score = 20

        # Quality indicator
        if total_score >= 18:
            quality_color = "green"
            quality_text = "Excellent"
        elif total_score >= 15:
            quality_color = "blue"
            quality_text = "Good"
        elif total_score >= 12:
            quality_color = "orange"
            quality_text = "Fair"
        else:
            quality_color = "red"
            quality_text = "Needs Improvement"

        st.markdown(f"### Quality Score: {total_score}/{max_score} - {quality_text}")

        # Show individual component scores
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Hook", f"{score.get('hook', 0)}/5")
        with col2:
            st.metric("Plan", f"{score.get('plan', 0)}/5")
        with col3:
            st.metric("Proof", f"{score.get('proof', 0)}/5")
        with col4:
            st.metric("Fit", f"{score.get('fit', 0)}/5")

        st.markdown("---")

    # Stats
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
