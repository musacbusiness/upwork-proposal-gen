#!/usr/bin/env python3
"""
Quick generation of 3 automation showcase posts with timeout handling.
"""

import sys
import os
from pathlib import Path

# Add execution directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Load env
env_file = "/Users/musacomma/Agentic Workflow/.env"
if os.path.exists(env_file):
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip().strip('"\'')

from draft_post_generator import DraftPostGenerator
from post_quality_checker import PostQualityChecker

print("\n" + "="*80)
print("  🤖 GENERATING 3 AUTOMATION SHOWCASE POSTS")
print("="*80 + "\n", flush=True)

generator = DraftPostGenerator()
checker = PostQualityChecker()

automations = [
    ("Proposal Generation Automation", "Sales Process Automation"),
    ("Client Onboarding Automation", "Client Management Automation"),
    ("Automated Invoice and Payment Processing", "Financial Automation"),
]

uploaded = 0

for idx, (automation_name, context) in enumerate(automations, 1):
    print(f"[{idx}/3] {automation_name}", flush=True)
    print(f"      Context: {context}", flush=True)

    try:
        print(f"      Generating...", flush=True)
        post = generator.generate_draft_post(
            topic=context,
            automation_showcase_mode=True,
            automation_name=automation_name
        )

        length = post.get('content_length', len(post['full_content']))
        print(f"      Length: {length} chars", flush=True)

        print(f"      Running QC...", flush=True)
        qc_result = checker.validate_post(post, check_duplicates=False)

        if qc_result['passes_qc']:
            print(f"      Uploading...", flush=True)
            if generator.generator.add_post_to_airtable(post):
                uploaded += 1
                print(f"      ✅ UPLOADED")
                print(f"         Title: {post['title'][:55]}")
                print(f"         Framework: {post['framework']}\n", flush=True)
            else:
                print(f"      ❌ Upload failed\n", flush=True)
        else:
            print(f"      ❌ QC Failed\n", flush=True)

    except Exception as e:
        print(f"      ❌ Error: {str(e)[:70]}\n", flush=True)

print("="*80)
print(f"✅ COMPLETE: {uploaded}/3 posts uploaded")
print("="*80 + "\n", flush=True)

sys.exit(0 if uploaded >= 2 else 1)
