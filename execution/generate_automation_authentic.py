#!/usr/bin/env python3
"""
Authentic Automation Showcase Generator - Using winning LinkedIn post structures.

Posts now have:
- Unique, specific hooks (no repetition)
- Scannable format with clear sections
- Focus on business impact, not technical details
- Conversational, authentic tone
- Specific numbers and real results
- Clear CTAs that invite dialogue
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

class AuthenticAutomationPostGenerator:
    """Generate authentic automation showcase posts with winning LinkedIn structures."""

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

        # Winning hook templates by automation (specific, not generic)
        self.hooks = {
            "Proposal Generation Automation": [
                "I watched our sales team spend 45 minutes on each proposal.\n\nThen we automated it. Now it's 2 minutes.",
                "Here's what kills deal momentum: sales reps get buried in proposal logistics instead of talking to prospects.\n\nWe've fixed it.",
                "Our team discovered we're wasting 200+ hours per year on proposal busywork. Nobody talks about it, but it's killing deal momentum.",
                "I realized our best sales rep was actually our best admin. She'd spend 30% of her time on proposals.\n\nThat stopped this month.",
            ],
            "Client Onboarding Automation": [
                "We've watched your first week with a client set the tone for the entire relationship.\n\nWe were blowing it with manual onboarding.",
                "I saw our onboarding team send the same 7 emails, collect the same 5 documents, and update the same 3 spreadsheets for every client.\n\nThen I asked: why are humans doing this?",
                "Our clients expect a smooth first experience. We were giving them chaos.\n\nNow? It's seamless.",
                "I've seen the difference: clients who stick around 18 months vs those who stay 3 years. It often comes down to that first week.",
            ],
            "Automated Invoice and Payment Processing": [
                "Our finance team's spending 6 hours per day on invoicing.\n\nThen we automated it. Now? 15 minutes.",
                "Here's the dirty secret: most companies lose money because payment tracking's a nightmare.\n\nWe solved it in 3 weeks.",
                "I watched our finance person chase payment emails like it was her job.\n\nTurns out, it didn't need to be.",
                "We're watching small businesses get killed by late payments.\n\nMost aren't automating follow-ups. We decided to change that.",
            ],
        }

    def get_hook(self, automation_name):
        """Get a specific, authentic hook for the automation."""
        if automation_name in self.hooks:
            return random.choice(self.hooks[automation_name])
        return f"We automated {automation_name.lower()}.\n\nHere's what changed."

    def build_scannable_body(self, showcase):
        """Build scannable, punchy body focused on impact."""
        sections = []

        # Add problems solved first (emotional connection)
        if showcase.get('problems_solved'):
            problems = showcase['problems_solved']
            # Trim to 300 chars max for conciseness
            if len(problems) > 300:
                problems = problems[:300].rsplit(' ', 1)[0] + "..."
            sections.append("What this solves:\n" + problems)

        # Add workflow improvement with focus on time/money saved
        if showcase.get('workflow_improvement'):
            impact = showcase['workflow_improvement']
            # Trim to 250 chars max - focus on business impact, not technical details
            if len(impact) > 250:
                impact = impact[:250].rsplit(' ', 1)[0] + "..."
            sections.append("The impact:\n" + impact)

        # Add real example (proof)
        if showcase.get('example'):
            example = showcase['example']
            # Trim to 300 chars max for concrete scenarios
            if len(example) > 300:
                example = example[:300].rsplit(' ', 1)[0] + "..."
            sections.append("Real example:\n" + example)

        # Only add technical details if truly necessary
        # if showcase.get('how_it_works'):
        #     sections.append("How it works:\n" + showcase['how_it_works'][:200] + "...")

        return "\n\n".join(sections)

    def generate_post(self, automation_name, context):
        """Generate an authentic automation showcase post."""
        print(f"  Generating enricher content...", flush=True)

        # Get automation showcase content from enricher
        showcase = self.enricher.generate_automation_showcase(automation_name, context)

        # Get specific, varied hook
        hook = self.get_hook(automation_name)

        # Build scannable body
        body = self.build_scannable_body(showcase)

        # Authentic CTA (invites dialogue, not forced)
        ctas = [
            "What's your biggest bottleneck? Reply below—I want to understand your situation.",
            "Is your team still manually handling this? Drop a comment—I'm curious how much time you're losing.",
            "What would you do with 10 extra hours per week? Let's talk about it.",
            "Tell me: what's stopping you from automating this in your business?",
            "How much time is this costing you right now? Let me know in the comments.",
        ]
        cta = random.choice(ctas)

        # Relevant hashtags (not overdone)
        hashtags_options = [
            "#Automation #Operations #Business",
            "#Sales #Automation #Efficiency",
            "#Finance #Automation #SmallBusiness",
            "#BusinessAutomation #Productivity #AI",
            "#Entrepreneurship #Automation #Growth",
        ]
        hashtags = random.choice(hashtags_options)

        # Build post (scannable format)
        full_content = f"{hook}\n\n{body}\n\n{cta}\n\n{hashtags}"

        # Sanitize (remove asterisks)
        full_content = full_content.replace('**', '').replace('*', '')

        # Build post dict
        post = {
            'title': f"{automation_name}: The Numbers Nobody Talks About",
            'post_topic': context,
            'full_content': full_content,
            'framework': 'Authentic-Automation-Showcase',
            'hook_type': 'Specific-Story',
            'cta_type': 'Dialogue-Invitation',
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

        metadata = f"""Framework: Authentic-Automation-Showcase
Automation: {post['automation_name']}
Topic: {post['post_topic']}
Style: Story-Driven, Impact-Focused"""

        fields = {
            "Title": post['title'],
            "Post Content": post['full_content'],
            "Status": post['status'],
            "Image Prompt": "Professional at work, authentic moment",
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
    print("  🚀 GENERATING AUTHENTIC AUTOMATION SHOWCASE POSTS")
    print("="*80 + "\n", flush=True)

    generator = AuthenticAutomationPostGenerator()
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
    print(f"✅ COMPLETE: {uploaded}/3 authentic posts uploaded")
    print("="*80 + "\n", flush=True)

    sys.exit(0 if uploaded >= 2 else 1)
