#!/usr/bin/env python3
"""
Coherent Automation Showcase Post Generator - Improved Logic
============================================================

CRITICAL IMPROVEMENTS:
1. Hooks explicitly mention the automation being showcased
2. Posts have clear structure: Hook → What the automation is → What it solves → Impact → Example
3. Automation name appears multiple times throughout post
4. Randomized topic selection (not always same 3)
5. Content is cohesive and flows naturally
6. Each section ties back to the specific automation
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

class CoherentAutomationPostGenerator:
    """Generate coherent automation showcase posts with explicit automation mentions."""

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

        # Automation showcase library with context
        # Each automation has hooks, what it does, and topic
        self.automations = {
            "Proposal Generation Automation": {
                "topic": "Sales Process Automation",
                "what_it_does": "automatically generates professional proposals in minutes instead of hours",
                "problem_context": "sales proposals",
                "hooks": [
                    "I watched our sales team spend 45 minutes writing each proposal.\n\nThen we built a Proposal Generation Automation.",
                    "Here's what kills deal momentum: sales reps get buried in proposal logistics.\n\nOur Proposal Generation Automation fixed it.",
                    "Our team discovered we're wasting 200+ hours per year on proposal busywork.\n\nSo we built a Proposal Generation Automation.",
                    "I realized our best sales rep was actually our best admin—spending 30% of her time on proposals.\n\nWe built a Proposal Generation Automation. That stopped.",
                ],
            },
            "Client Onboarding Automation": {
                "topic": "Client Management Automation",
                "what_it_does": "automatically handles the entire client onboarding workflow in minutes",
                "problem_context": "client onboarding experience",
                "hooks": [
                    "I've watched: a client's first week with us sets the tone for their entire relationship with us.\n\nWe were blowing it with manual onboarding. So we built a Client Onboarding Automation.",
                    "I watched our onboarding team send the same 7 emails, collect the same 5 documents, and update the same 3 spreadsheets for every client.\n\nWe decided that's insane. We built a Client Onboarding Automation to replace it.",
                    "Our clients expect a smooth first impression when they sign with us.\n\nManual onboarding wasn't delivering that. Our Client Onboarding Automation changed everything.",
                    "I've seen the difference: clients who've got a smooth first experience stay 3 years. Clients who don't stay 18 months.\n\nThat's why we built a Client Onboarding Automation.",
                ],
            },
            "Automated Invoice and Payment Processing": {
                "topic": "Financial Automation",
                "what_it_does": "automatically handles invoice generation, tracking, and payment follow-ups",
                "problem_context": "invoice and payment management",
                "hooks": [
                    "I watched: our finance person spends 6 hours per day chasing invoices and payment confirmations.\n\nSo we built an Automated Invoice and Payment Processing system. Now? 15 minutes.",
                    "Here's what I realized: we're losing money because payment tracking's a nightmare and late payments are killing our cash flow.\n\nOur Automated Invoice and Payment Processing system solved it in 3 weeks.",
                    "I noticed our finance person was chasing payment emails like it was her full-time job—but it wasn't.\n\nWe built an Automated Invoice and Payment Processing system. That's over.",
                    "Late payments were killing our cash flow and destroying relationships.\n\nMost businesses aren't using Automated Invoice and Payment Processing. We decided to change that.",
                ],
            },
            "Email Automation and Lead Nurturing": {
                "topic": "Marketing Automation",
                "what_it_does": "automatically sends targeted emails to nurture leads through the sales funnel",
                "problem_context": "lead nurturing workflows",
                "hooks": [
                    "I realized we were losing 40% of qualified leads because follow-up wasn't consistent.\n\nWe built Email Automation and Lead Nurturing sequences to fix it.",
                    "Our team's best leads were falling through the cracks—nobody had capacity for consistent follow-up.\n\nEmail Automation and Lead Nurturing changed that.",
                    "Here's what kills conversions: 3 weeks of silence after first contact with a prospect.\n\nOur Email Automation and Lead Nurturing system ensures touchpoints happen automatically.",
                    "We were losing $50K in monthly revenue because prospects got forgotten between touchpoints.\n\nEmail Automation and Lead Nurturing sequences recovered that.",
                ],
            },
            "Task Assignment and Workflow Distribution": {
                "topic": "Operations Automation",
                "what_it_does": "automatically assigns tasks to team members and distributes work based on capacity",
                "problem_context": "workflow bottlenecks",
                "hooks": [
                    "I became a bottleneck—every task needed my approval before anyone could work.\n\nWe built a Task Assignment and Workflow Distribution system that changed everything.",
                    "Our team was wasting 20% of time asking 'who should do this?' for every single task.\n\nA Task Assignment and Workflow Distribution system solved it.",
                    "Here's what slows down teams: unclear ownership means 15 emails asking for clarification on every task.\n\nOur Task Assignment and Workflow Distribution automation eliminated that.",
                    "Our 15-person team went from 3-day delays to same-day task completion when we implemented Task Assignment and Workflow Distribution automation.",
                ],
            },
        }

    def get_random_automation(self):
        """Randomly select an automation instead of using the same 3."""
        automation_name = random.choice(list(self.automations.keys()))
        automation_config = self.automations[automation_name]
        return automation_name, automation_config

    def build_coherent_post(self, automation_name, automation_config, showcase):
        """
        Build a coherent post with proper structure:
        1. Hook (mentions automation explicitly)
        2. What this automation does (brief description)
        3. Problems it solves
        4. The impact (time/money saved)
        5. Real example
        6. CTA
        7. Hashtags
        """
        sections = []

        # Get hook that already mentions automation
        hook = random.choice(automation_config['hooks'])
        sections.append(hook)

        # Add what the automation does (explicit explanation)
        what_it_does = automation_config['what_it_does']
        sections.append(f"\n{automation_name} {what_it_does}.")

        # Add problems solved (trim to 250 chars)
        if showcase.get('problems_solved'):
            problems = showcase['problems_solved']
            if len(problems) > 250:
                problems = problems[:250].rsplit(' ', 1)[0] + "..."
            sections.append(f"\nProblems it solved:\n{problems}")

        # Add impact (trim to 200 chars, focus on business results)
        if showcase.get('workflow_improvement'):
            impact = showcase['workflow_improvement']
            if len(impact) > 200:
                impact = impact[:200].rsplit(' ', 1)[0] + "..."
            sections.append(f"\nThe impact:\n{impact}")

        # Add real example (trim to 300 chars, show concrete scenario)
        if showcase.get('example'):
            example = showcase['example']
            if len(example) > 300:
                example = example[:300].rsplit(' ', 1)[0] + "..."
            sections.append(f"\nReal example:\n{example}")

        # Build full post
        full_content = "\n".join(sections)

        # Add CTA (dialogue-inviting, specific to the automation topic)
        ctas = [
            "What's your biggest bottleneck with this? Reply below—I want to understand your situation.",
            f"Is your team still manually handling {automation_config['problem_context']}? Drop a comment—I'm curious how much time you're losing.",
            "What would you do with the extra time this automation would give you? Let's talk about it.",
            f"Tell me: what's stopping you from automating {automation_config['problem_context']} in your business?",
            f"How much time is {automation_config['problem_context']} costing you right now? Let me know in the comments.",
        ]
        cta = random.choice(ctas)
        full_content += f"\n\n{cta}"

        # Add hashtags
        hashtags_options = [
            "#Automation #Operations #Business",
            "#Sales #Automation #Efficiency",
            "#Finance #Automation #SmallBusiness",
            "#BusinessAutomation #Productivity #AI",
            "#Entrepreneurship #Automation #Growth",
        ]
        hashtags = random.choice(hashtags_options)
        full_content += f"\n\n{hashtags}"

        # Remove asterisks
        full_content = full_content.replace('**', '').replace('*', '')

        return full_content

    def generate_post(self):
        """Generate a single coherent automation showcase post with random topic."""
        print(f"  Selecting random automation...", flush=True)
        automation_name, automation_config = self.get_random_automation()

        print(f"  Automation: {automation_name}", flush=True)
        print(f"  Generating enricher content...", flush=True)

        # Generate showcase content
        showcase = self.enricher.generate_automation_showcase(
            automation_name,
            automation_config['topic']
        )

        print(f"  Building coherent post structure...", flush=True)

        # Build coherent post
        full_content = self.build_coherent_post(automation_name, automation_config, showcase)

        # Build post dict
        post = {
            'title': f"{automation_name}: The Numbers Nobody Talks About",
            'post_topic': automation_config['topic'],
            'full_content': full_content,
            'framework': 'Coherent-Automation-Showcase',
            'hook_type': 'Automation-Specific',
            'cta_type': 'Dialogue-Invitation',
            'post_type': 'expertise_posts',
            'visual_type': 'personal_photo',
            'visual_spec': {'type': 'personal_photo'},
            'generated_at': datetime.now().isoformat(),
            'scheduled_time': None,
            'status': 'Draft',
            'automation_showcase_mode': True,
            'automation_name': automation_name,
            'content_length': len(full_content)
        }

        return post

    def upload_to_airtable(self, post):
        """Upload post to Airtable."""
        url = f"https://api.airtable.com/v0/{self.airtable_base_id}/{self.airtable_table_id}"

        metadata = f"""Framework: Coherent-Automation-Showcase
Automation: {post['automation_name']}
Topic: {post['post_topic']}
Style: Coherent, Automation-Focused, Impact-Driven"""

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
    print("  🚀 GENERATING COHERENT AUTOMATION SHOWCASE POSTS")
    print("="*80 + "\n", flush=True)

    generator = CoherentAutomationPostGenerator()
    checker = PostQualityChecker()

    uploaded = 0

    for idx in range(1, 4):
        print(f"[{idx}/3] Generating post...", flush=True)

        try:
            post = generator.generate_post()
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
                for issue in qc_result['issues'][:2]:
                    print(f"         {issue[:70]}\n", flush=True)

        except Exception as e:
            print(f"      ❌ Error: {str(e)[:70]}\n", flush=True)

    print("="*80)
    print(f"✅ COMPLETE: {uploaded}/3 coherent posts uploaded")
    print("="*80 + "\n", flush=True)

    sys.exit(0 if uploaded >= 2 else 1)
