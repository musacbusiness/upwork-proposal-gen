#!/bin/bash
# Complete deployment setup and deployment for Modal + Streamlit

set -e

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  🚀 UPWORK PROPOSAL GENERATOR - CLOUD DEPLOYMENT SETUP         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get API key from .env
API_KEY=$(grep "ANTHROPIC_API_KEY" .env | cut -d'=' -f2)

if [ -z "$API_KEY" ]; then
    echo -e "${RED}❌ Error: ANTHROPIC_API_KEY not found in .env${NC}"
    exit 1
fi

echo -e "${BLUE}[1/4]${NC} Checking dependencies..."
python3 -m pip install modal --quiet 2>/dev/null
echo -e "${GREEN}✓${NC} Modal installed"

echo ""
echo -e "${BLUE}[2/4]${NC} Setting up Modal authentication..."
echo ""
echo "We need to authenticate with Modal."
echo "Your browser will open - follow the prompts and paste the token below."
echo ""

# Try to open browser and authenticate
python3 -c "
import modal
import sys

try:
    # This will open browser if no token exists
    token = modal.config.get_token_path()
    print('Token path:', token)
except Exception as e:
    print(f'Please visit: https://modal.com/signin')
"

# Create the secret
echo ""
echo -e "${BLUE}[3/4]${NC} Creating Modal secret with your Claude API key..."

python3 << 'PYTHON_SCRIPT'
import modal
import sys

try:
    # Try to create the secret
    secret = modal.Secret.from_dict({
        "ANTHROPIC_API_KEY": __import__('os').getenv('ANTHROPIC_API_KEY') or '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'
    })
    print("✓ Modal secret created/verified")
except Exception as e:
    print(f"Note: Secret creation requires Modal authentication")
    print(f"Error: {e}")
PYTHON_SCRIPT

echo ""
echo -e "${BLUE}[4/4]${NC} Deploying to Modal..."
echo ""

cd "/Users/musacomma/Agentic Workflow"

# Deploy the Modal app
if python3 -m modal deploy execution/modal_deploy.py 2>&1 | tee /tmp/modal_deploy.log; then
    echo ""
    echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✅ MODAL DEPLOYMENT SUCCESSFUL!${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Your Modal backend is now running 24/7 in the cloud."
    echo ""
    echo "Modal functions deployed:"
    echo "  - generate_proposal() → Generates proposals"
    echo ""
else
    echo ""
    echo -e "${YELLOW}⚠️  Modal deployment encountered issues.${NC}"
    echo "This might be due to authentication. Check the log above."
    echo ""
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  NEXT: Deploy Streamlit Frontend                              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "1. Initialize Git (if not already):"
echo "   git init"
echo "   git add ."
echo "   git commit -m 'Initial commit'"
echo ""
echo "2. Create GitHub repo and push:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/upwork-proposal-gen"
echo "   git push -u origin main"
echo ""
echo "3. Deploy Streamlit:"
echo "   - Go to https://share.streamlit.io"
echo "   - Click 'New app'"
echo "   - Select your GitHub repo"
echo "   - Main file: execution/streamlit_proposal_app.py"
echo "   - Click Deploy"
echo ""
echo "4. Your app will be live at:"
echo "   https://your-username-upwork-proposal-gen.streamlit.app"
echo ""
echo -e "${GREEN}Then you're done! 🎉${NC}"
echo ""
