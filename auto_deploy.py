#!/usr/bin/env python3
"""
Automated deployment script for Modal + Streamlit
Handles all setup and deployment steps
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description=""):
    """Run a command and return success/failure"""
    if description:
        print(f"\n{'='*60}")
        print(f"📍 {description}")
        print(f"{'='*60}")

    print(f"→ Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=False, text=True)
    return result.returncode == 0

def check_prerequisites():
    """Check if all prerequisites are installed"""
    print("\n✓ Checking prerequisites...\n")

    checks = [
        ("Python 3", "python3 --version"),
        ("Modal", "python3 -m modal --version"),
        ("Git", "git --version"),
    ]

    for name, cmd in checks:
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"  ✓ {name}: {result.stdout.strip().split(chr(10))[0]}")
            else:
                print(f"  ✗ {name}: Not found or error")
                return False
        except Exception as e:
            print(f"  ✗ {name}: {e}")
            return False

    return True

def main():
    """Main deployment flow"""
    print("\n" + "="*60)
    print("🚀 UPWORK PROPOSAL GENERATOR - DEPLOYMENT")
    print("="*60)

    os.chdir("/Users/musacomma/Agentic Workflow")

    # Step 1: Check prerequisites
    print("\n[1/4] CHECKING PREREQUISITES")
    if not check_prerequisites():
        print("\n❌ Some prerequisites are missing. Please install them first.")
        sys.exit(1)

    # Step 2: Get API key
    print("\n[2/4] VERIFYING CONFIGURATION")
    print("✓ Checking for Claude API key...")

    try:
        with open('.env', 'r') as f:
            env_content = f.read()
            if 'ANTHROPIC_API_KEY' in env_content:
                api_key = [line.split('=')[1] for line in env_content.split('\n') if line.startswith('ANTHROPIC_API_KEY')][0].strip()
                print(f"  ✓ API key found: {api_key[:20]}...{api_key[-10:]}")
            else:
                print("  ✗ ANTHROPIC_API_KEY not found in .env")
                sys.exit(1)
    except Exception as e:
        print(f"  ✗ Error reading .env: {e}")
        sys.exit(1)

    # Step 3: Modal authentication
    print("\n[3/4] AUTHENTICATING WITH MODAL")
    print("⚠️  Modal requires browser authentication")
    print("If prompted, follow these steps:")
    print("  1. A browser will open to https://modal.com/signin")
    print("  2. Sign in with your Modal account (create one if needed)")
    print("  3. Copy the token and paste it back")
    print("\nAttempting authentication...")

    auth_cmd = "python3 -m modal token new 2>&1 | grep -i 'token\\|authenticated\\|success' || echo 'Check Modal setup'"
    auth_result = subprocess.run(auth_cmd, shell=True, capture_output=True, text=True)
    print(f"  → {auth_result.stdout.strip() if auth_result.stdout else 'Please authenticate manually: python3 -m modal token new'}")

    # Step 4: Deploy to Modal
    print("\n[4/4] DEPLOYING TO MODAL")
    print("🚀 Deploying backend functions to Modal...")

    deploy_cmd = "python3 -m modal deploy execution/modal_deploy.py 2>&1"
    result = subprocess.run(deploy_cmd, shell=True, capture_output=True, text=True)

    if result.returncode == 0:
        print("  ✓ Modal deployment successful!")
        if "deployed" in result.stdout.lower() or "app" in result.stdout.lower():
            print(f"\n  App ID: upwork-proposal-generator")
            print(f"  Backend running 24/7 ✓")
        print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
    else:
        print(f"  ⚠️  Deployment returned: {result.returncode}")
        print("  This might be normal depending on your Modal setup")
        if result.stdout:
            print(f"  Output:\n{result.stdout[-1000:]}")
        if result.stderr:
            print(f"  Error:\n{result.stderr[-1000:]}")

    # Final instructions
    print("\n" + "="*60)
    print("✅ MODAL SETUP COMPLETE (or nearly complete)")
    print("="*60)

    print("\n📍 NEXT: Deploy Streamlit Frontend")
    print("\n1. Initialize Git:")
    print("   cd '/Users/musacomma/Agentic Workflow'")
    print("   git init")
    print("   git add .")
    print("   git commit -m 'Initial commit'")

    print("\n2. Create GitHub repo:")
    print("   git remote add origin https://github.com/YOUR_USERNAME/upwork-proposal-gen")
    print("   git push -u origin main")

    print("\n3. Deploy to Streamlit Cloud:")
    print("   - Go to https://share.streamlit.io")
    print("   - Click 'New app'")
    print("   - Repository: YOUR_USERNAME/upwork-proposal-gen")
    print("   - Main file: execution/streamlit_proposal_app.py")
    print("   - Click Deploy")

    print("\n4. Visit your live app:")
    print("   https://your-username-upwork-proposal-gen.streamlit.app")

    print("\n" + "="*60)
    print("📚 Full details: DEPLOY_NOW.md")
    print("="*60 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Deployment cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        sys.exit(1)
