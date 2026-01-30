#!/usr/bin/env python3
"""
Simplified automation showcase generation - direct enricher + post building.
Bypasses framework complexity that's causing hangs.
"""

import os
import sys
import json
import random
from pathlib import Path
from datetime import datetime
import requests

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

from educational_content_enricher import EducationalContentEnricher
from post_quality_checker import PostQualityChecker

class SimpleAutomationPostGenerator:
    """Generate automation showcase posts without framework overhead."""

    def __init__(self):
        self.enricher = EducationalContentEnricher()
        self.checker = PostQualityChecker()
        self.airtable_api_key = os.environ.get('AIRTABLE_API_KEY')
        self.airtable_base_id = os.environ.get('AIRTABLE_BASE_ID')
        self.airtable_table_id = os.environ.get('AIRTABLE_LINKEDIN_TABLE_ID')
        self.headers = {
            "Authorization": f"Bearer {self.airtable_api_key}",
            "Content-Type": "application/json"
        }

    def generate_post(self, automation_name, context):
        """Generate a simple automation showcase post."""
        print(f"  Generating enricher content...", flush=True)

        # Get automation showcase content from enricher
        showcase = self.enricher.generate_automation_showcase(automation_name, context)

        # Build hook
        hook = f"Most business owners still do {automation_name.lower()} manually.\n\nIt doesn't have to be that way."

        # Build body from showcase sections
        body_parts = []
        if showcase.get('how_it_works'):
            body_parts.append(f"Here's how it works:\n{showcase['how_it_works']}")
        if showcase.get('problems_solved'):
            body_parts.append(f"\nWhat it solves:\n{showcase['problems_solved']}")
        if showcase.get('workflow_improvement'):
            body_parts.append(f"\nThe impact:\n{showcase['workflow_improvement']}")
        if showcase.get('example'):
            body_parts.append(f"\nExample:\n{showcase['example']}")

        body = "\n".join(body_parts)

        # Build CTA
        cta = "What's your biggest bottleneck? Drop a comment and let me know how I can help."

        # Build hashtags
        hashtags = "#Automation #Business #Efficiency #AI"

        # Combine everything
        full_content = f"{hook}\n\n{body}\n\n{cta}\n\n{hashtags}"

        # Sanitize (remove asterisks)
        full_content = full_content.replace('**', '').replace('*', '')

        # Build post dict
        post = {
            'title': f"How {automation_name} Saves Business Owners Hours Per Week",
            'post_topic': context,
            'full_content': full_content,
            'framework': 'Direct-Automation-Showcase',
            'hook_type': 'Direct',
            'cta_type': 'Question',
            'post_type': 'expertise_posts',
            'visual_type': 'personal_photo',
            'visual_spec': {'type': 'personal_photo'},
            'hashtags': hashtags,
            'generated_at': datetime.now().isoformat(),
            'scheduled_time': None,
            'status': 'Draft',
            'educational_mode': False,
            'automation_showcase_mode': True,
            'automation_name': automation_name,
            'content_length': len(full_content)
        }

        return post

    def upload_to_airtable(self, post):
        """Upload post to Airtable."""
        url = f"https://api.airtable.com/v0/{self.airtable_base_id}/{self.airtable_table_id}"

        metadata = f"""Framework: Direct-Automation-Showcase
Automation: {post['automation_name']}
Topic: {post['post_topic']}"""

        fields = {
            "Title": post['title'],
            "Post Content": post['full_content'],
            "Status": post['status'],
            "Image Prompt": "Professional business automation illustration",
            "Notes": metadata
        }

        payload = {"records": [{"fields": fields}]}

        response = requests.post(url, headers=self.headers, json=payload)

        if response.status_code == 200:
            record_id = response.json()['records'][0]['id']
            print(f"     ✅ Uploaded: {record_id}", flush=True)
            return True
        else:
            print(f"     ❌ Upload failed: {response.status_code}", flush=True)
            return False

# Main execution
if __name__ == "__main__":
    print("\n" + "="*80)
    print("  🤖 GENERATING 3 AUTOMATION SHOWCASE POSTS (SIMPLIFIED)")
    print("="*80 + "\n", flush=True)

    generator = SimpleAutomationPostGenerator()
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
            post = generator.generate_post(automation_name, context)
            length = post['content_length']

            print(f"      Length: {length} chars", flush=True)
            print(f"      Running QC...", flush=True)

            qc_result = checker.validate_post(post, check_duplicates=False)

            if qc_result['passes_qc']:
                print(f"      Uploading...", flush=True)
                if generator.upload_to_airtable(post):
                    uploaded += 1
                    print(f"      ✅ SUCCESS\n", flush=True)
                else:
                    print(f"      ❌ Upload failed\n", flush=True)
            else:
                print(f"      ❌ QC Failed:")
                for issue in qc_result['issues'][:1]:
                    print(f"         {issue[:70]}\n", flush=True)

        except Exception as e:
            print(f"      ❌ Error: {str(e)[:70]}\n", flush=True)

    print("="*80)
    print(f"✅ COMPLETE: {uploaded}/3 posts uploaded")
    print("="*80 + "\n", flush=True)

    sys.exit(0 if uploaded >= 2 else 1)
