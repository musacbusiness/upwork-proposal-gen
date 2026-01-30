#!/usr/bin/env python3
"""
Client Success Story - Automation Case Study Post Generator
===========================================================

CRITICAL CHANGE: Posts written from CLIENT PERSPECTIVE, not self-promotion

Structure:
1. Hook: "I helped [client type] implement [automation]. Here's what happened."
2. What we set up: The automation solution we implemented for them
3. Their problems: What they were struggling with BEFORE
4. Their results: Specific metrics/outcomes they achieved
5. Real example: Their specific scenario and transformation
6. CTA: "Want similar results for your [problem]? Let's talk."
7. Hashtags

This positions you as an implementer/consultant who delivers results for clients.
Social proof is more powerful than claiming benefits for yourself.
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

class ClientSuccessStoryGenerator:
    """Generate client success story posts showing automation results for their businesses."""

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

        # Client success stories - hooks written from "I helped a client" perspective
        self.automations = {
            "Proposal Generation Automation": {
                "topic": "Sales Process Automation",
                "client_type": "sales team",
                "what_we_did": "implemented a Proposal Generation Automation that creates professional proposals in minutes instead of hours",
                "problem_context": "proposal delays",
                "hooks": [
                    "I helped a sales team that was spending 45 minutes per proposal writing them manually.\n\nAfter we set up a Proposal Generation Automation, here's what changed.",
                    "I worked with a sales director whose team was losing deals because proposal delays killed momentum.\n\nWe implemented a Proposal Generation Automation. The difference was immediate.",
                    "I noticed a sales organization wasting 200+ hours per year on proposal busywork.\n\nWe built them a Proposal Generation Automation. That freed up their best rep to close more deals.",
                    "I watched a sales manager struggle: their best rep was actually their best admin (spending 30% of time on proposals).\n\nWe set up a Proposal Generation Automation for them. That changed everything.",
                ],
            },
            "Client Onboarding Automation": {
                "topic": "Client Management Automation",
                "client_type": "service business",
                "what_we_did": "implemented a Client Onboarding Automation that handles the entire workflow automatically, turning chaos into seamless first impressions",
                "problem_context": "client onboarding experience",
                "hooks": [
                    "I helped a service business that was blowing their first week with clients—manual onboarding was chaos.\n\nAfter we set up a Client Onboarding Automation, their client retention completely changed.",
                    "I worked with a team sending the same 7 emails, collecting the same 5 documents, updating the same 3 spreadsheets for every client.\n\nWe implemented a Client Onboarding Automation to replace all that. Here's what happened.",
                    "I watched a business owner realize: clients who had a smooth first week stayed 3 years. Clients who didn't stayed 18 months.\n\nWe set up a Client Onboarding Automation. Their retention numbers proved the impact.",
                    "I saw a client management team drowning in manual onboarding tasks that took 4-6 hours per client.\n\nWe built them a Client Onboarding Automation. They recovered all that time in week one.",
                ],
            },
            "Automated Invoice and Payment Processing": {
                "topic": "Financial Automation",
                "client_type": "finance team",
                "what_we_did": "implemented an Automated Invoice and Payment Processing system that handles the entire workflow automatically, recovering cash and time",
                "problem_context": "invoice and payment management",
                "hooks": [
                    "I helped a finance person spending 6 hours per day on invoicing and payment chasing.\n\nWe set up an Automated Invoice and Payment Processing system. Within days, their workload dropped to 15 minutes.",
                    "I worked with a business losing money because payment tracking was a nightmare and late payments were killing cash flow.\n\nWe implemented an Automated Invoice and Payment Processing system. They recovered $50K in overdue payments within a month.",
                    "I watched a finance manager chase payment emails like it was her full-time job.\n\nWe set up an Automated Invoice and Payment Processing system for her team. Her stress level dropped immediately.",
                    "I saw a small business getting killed by late payments because they had no system to track or follow up.\n\nWe built them an Automated Invoice and Payment Processing automation. Their cash flow stabilized in 3 weeks.",
                ],
            },
            "Email Automation and Lead Nurturing": {
                "topic": "Marketing Automation",
                "client_type": "sales organization",
                "what_we_did": "implemented Email Automation and Lead Nurturing sequences that keep prospects engaged automatically and increase conversion rates",
                "problem_context": "lead nurturing workflows",
                "hooks": [
                    "I helped a sales team losing 40% of qualified leads because follow-up wasn't consistent.\n\nWe set up Email Automation and Lead Nurturing sequences. Here's what their pipeline looked like after.",
                    "I worked with a team whose best leads were falling through the cracks because nobody had capacity for consistent follow-up.\n\nWe implemented Email Automation and Lead Nurturing. Their lead-to-close rate jumped significantly.",
                    "I saw a business losing $50K per month in revenue because prospects disappeared between touchpoints.\n\nWe built Email Automation and Lead Nurturing sequences. That revenue came back.",
                    "I noticed a sales organization with a real problem: 3 weeks of silence after first contact with a prospect.\n\nWe set up Email Automation and Lead Nurturing for them. Engagement metrics improved instantly.",
                ],
            },
            "Task Assignment and Workflow Distribution": {
                "topic": "Operations Automation",
                "client_type": "growing team",
                "what_we_did": "implemented a Task Assignment and Workflow Distribution system that automatically assigns work and removes bottlenecks",
                "problem_context": "workflow bottlenecks",
                "hooks": [
                    "I worked with a team where the manager had become the bottleneck—every task needed approval before anyone could work.\n\nWe set up a Task Assignment and Workflow Distribution system. Their throughput doubled.",
                    "I helped a team wasting 20% of their time asking 'who should do this?' for every single task.\n\nWe implemented a Task Assignment and Workflow Distribution system. Clarity solved the problem.",
                    "I saw an operation where unclear ownership meant 15 emails asking for clarification on every task.\n\nWe built them a Task Assignment and Workflow Distribution automation. Communication chaos turned into smooth workflows.",
                    "I worked with a 15-person team going from 3-day delays on task completion to same-day turnarounds.\n\nWe set up Task Assignment and Workflow Distribution for them. Here's what changed.",
                ],
            },
        }

    def get_random_automation(self):
        """Randomly select an automation instead of using the same 3."""
        automation_name = random.choice(list(self.automations.keys()))
        automation_config = self.automations[automation_name]
        return automation_name, automation_config

    def build_case_study_post(self, automation_name, automation_config, showcase):
        """
        Build a client success story post with proper case study structure:
        1. Hook (I helped a [client type], here's what happened)
        2. What we set up (the automation we implemented)
        3. Their problems (what they were struggling with)
        4. Their results (specific metrics/improvements)
        5. Real example (their specific scenario)
        6. CTA (want similar results)
        7. Hashtags
        """
        sections = []

        # Get hook that positions this as client success story
        hook = random.choice(automation_config['hooks'])
        sections.append(hook)

        # Add what we set up (implementation description)
        what_we_did = automation_config['what_we_did']
        sections.append(f"\nHere's what we set up: {what_we_did}.")

        # Add their problems (what they were struggling with - trim to 250 chars)
        if showcase.get('problems_solved'):
            problems = showcase['problems_solved']
            if len(problems) > 250:
                problems = problems[:250].rsplit(' ', 1)[0] + "..."
            sections.append(f"\nTheir problems before:\n{problems}")

        # Add their results (specific improvements - trim to 200 chars)
        if showcase.get('workflow_improvement'):
            results = showcase['workflow_improvement']
            if len(results) > 200:
                results = results[:200].rsplit(' ', 1)[0] + "..."
            sections.append(f"\nTheir results:\n{results}")

        # Add real example (their specific scenario - trim to 300 chars)
        if showcase.get('example'):
            example = showcase['example']
            if len(example) > 300:
                example = example[:300].rsplit(' ', 1)[0] + "..."
            sections.append(f"\nTheir real example:\n{example}")

        # Build full post
        full_content = "\n".join(sections)

        # Add CTA (invitation to work together on similar results)
        ctas = [
            f"Is your {automation_config['client_type']} dealing with similar {automation_config['problem_context']}? Reply below—I want to understand your situation.",
            f"Want to see similar results for your {automation_config['problem_context']}? Let's talk about what's possible for your business.",
            f"Curious if this automation could solve your {automation_config['problem_context']} challenges? Drop a comment—I'd love to help.",
            f"Think your team could benefit from something like this? Tell me what your biggest bottleneck is with {automation_config['problem_context']}.",
            f"How much time could you save if you had this automated? Let me know in the comments—I love talking about efficiency wins.",
        ]
        cta = random.choice(ctas)
        full_content += f"\n\n{cta}"

        # Add hashtags
        hashtags_options = [
            "#Automation #ClientSuccess #Business",
            "#CaseStudy #Automation #Operations",
            "#BusinessAutomation #Efficiency #Results",
            "#Entrepreneurship #Automation #Growth",
            "#SystemsThinking #Automation #ROI",
        ]
        hashtags = random.choice(hashtags_options)
        full_content += f"\n\n{hashtags}"

        # Remove asterisks
        full_content = full_content.replace('**', '').replace('*', '')

        return full_content

    def generate_post(self):
        """Generate a single client success story post with random automation."""
        print(f"  Selecting random automation...", flush=True)
        automation_name, automation_config = self.get_random_automation()

        print(f"  Automation: {automation_name}", flush=True)
        print(f"  Client type: {automation_config['client_type']}", flush=True)
        print(f"  Generating showcase content...", flush=True)

        # Generate showcase content
        showcase = self.enricher.generate_automation_showcase(
            automation_name,
            automation_config['topic']
        )

        print(f"  Building client success story...", flush=True)

        # Build case study post
        full_content = self.build_case_study_post(automation_name, automation_config, showcase)

        # Build post dict
        post = {
            'title': f"Client Success: {automation_name} Results",
            'post_topic': automation_config['topic'],
            'full_content': full_content,
            'framework': 'Client-Success-Story',
            'hook_type': 'Client-Perspective',
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

        metadata = f"""Framework: Client-Success-Story
Automation: {post['automation_name']}
Topic: {post['post_topic']}
Style: Case Study, Client-Focused, Results-Driven"""

        fields = {
            "Title": post['title'],
            "Post Content": post['full_content'],
            "Status": post['status'],
            "Image Prompt": "Professional achievement moment, client success",
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
    print("  🚀 GENERATING CLIENT SUCCESS STORY POSTS")
    print("="*80 + "\n", flush=True)

    generator = ClientSuccessStoryGenerator()
    checker = PostQualityChecker()

    uploaded = 0

    for idx in range(1, 4):
        print(f"[{idx}/3] Generating success story...", flush=True)

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
    print(f"✅ COMPLETE: {uploaded}/3 client success stories uploaded")
    print("="*80 + "\n", flush=True)

    sys.exit(0 if uploaded >= 2 else 1)
