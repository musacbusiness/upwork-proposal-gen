#!/bin/bash
# Automated deployment script for Modal + Streamlit

set -e

echo "🚀 Upwork Proposal Generator - Deployment Script"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check dependencies
echo -e "${BLUE}[1/5]${NC} Checking dependencies..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found"
    exit 1
fi

if ! command -v git &> /dev/null; then
    echo "❌ Git not found"
    exit 1
fi

echo -e "${GREEN}✓${NC} Python and Git found"

# Step 2: Install Modal
echo ""
echo -e "${BLUE}[2/5]${NC} Installing Modal..."
pip install modal --quiet > /dev/null
echo -e "${GREEN}✓${NC} Modal installed"

# Step 3: Setup Modal authentication
echo ""
echo -e "${BLUE}[3/5]${NC} Setting up Modal authentication..."
echo "📍 A browser window will open to authenticate with Modal"
echo "   After authentication, paste the token back here"
echo ""

if modal token new; then
    echo -e "${GREEN}✓${NC} Modal authenticated"
else
    echo -e "${YELLOW}⚠${NC} Modal authentication may have issues - continue anyway? (y/n)"
    read -r response
    if [[ ! $response =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 4: Create Modal secret
echo ""
echo -e "${BLUE}[4/5]${NC} Setting up Modal secret..."
echo "📍 Enter your Claude API key (from .env file):"
read -s -r ANTHROPIC_API_KEY

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ API key cannot be empty"
    exit 1
fi

if modal secret create upwork-proposal-secrets ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Modal secret created"
else
    echo -e "${YELLOW}⚠${NC} Secret may already exist (that's OK)"
fi

# Step 5: Deploy to Modal
echo ""
echo -e "${BLUE}[5/5]${NC} Deploying to Modal..."
cd "/Users/musacomma/Agentic Workflow"

if modal deploy execution/generate_upwork_proposal.py; then
    echo -e "${GREEN}✓${NC} Modal deployment successful"
else
    echo -e "${YELLOW}⚠${NC} Modal deployment may have issues - continue? (y/n)"
    read -r response
    if [[ ! $response =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 6: GitHub setup
echo ""
echo -e "${BLUE}BONUS: GitHub Setup (Optional)${NC}"
echo "To deploy Streamlit Cloud as well:"
echo ""
echo "  1. Create GitHub repo:"
echo "     git init"
echo "     git remote add origin https://github.com/YOUR_USERNAME/upwork-proposal-gen"
echo "     git add ."
echo "     git commit -m 'Initial commit'"
echo "     git push -u origin main"
echo ""
echo "  2. Go to https://share.streamlit.io"
echo "  3. Click 'New app' → Select your repo"
echo "  4. Main file: execution/streamlit_proposal_app.py"
echo "  5. Deploy"
echo ""

# Done
echo ""
echo -e "${GREEN}════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ DEPLOYMENT COMPLETE!${NC}"
echo -e "${GREEN}════════════════════════════════════════════${NC}"
echo ""
echo "Your Modal backend is now 24/7 running."
echo ""
echo "Next steps:"
echo "1. Deploy to Streamlit Cloud (see instructions above)"
echo "2. Or run locally: streamlit run execution/streamlit_proposal_app.py"
echo ""
echo "📖 Full guide: DEPLOY_MODAL_STREAMLIT.md"
