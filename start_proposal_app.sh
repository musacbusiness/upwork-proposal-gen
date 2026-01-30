#!/bin/bash
# Quick launcher for Upwork Proposal Generator web app

cd "/Users/musacomma/Agentic Workflow"

echo "🚀 Starting Upwork Proposal Generator..."
echo ""
echo "📱 Open in browser: http://localhost:8501"
echo "📱 On phone (same WiFi): http://YOUR_MAC_IP:8501"
echo ""
echo "To find your Mac IP:"
echo "  System Settings → Network → copy IP address"
echo ""
echo "Press Ctrl+C to stop the app"
echo ""

streamlit run execution/streamlit_proposal_app.py
