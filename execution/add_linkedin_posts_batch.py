#!/usr/bin/env python3
"""
Add LinkedIn Posts Batch to Airtable
=====================================

Adds 30 LinkedIn posts to Airtable with:
- Status: Draft
- Scheduled Post Time: Distributed across next 30 days (one per day)
- Post Content: The post text
- Topic: The topic name

Usage:
    python3 add_linkedin_posts_batch.py
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('linkedin_batch_upload.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()


class LinkedInBatchUploader:
    """Handles batch upload of LinkedIn posts to Airtable"""

    def __init__(self):
        """Initialize Airtable connection"""
        self.api_key = os.getenv('AIRTABLE_API_KEY')
        self.base_id = os.getenv('AIRTABLE_BASE_ID')
        self.table_id = os.getenv('AIRTABLE_LINKEDIN_TABLE_ID')

        if not all([self.api_key, self.base_id, self.table_id]):
            raise ValueError("Missing required environment variables: AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_LINKEDIN_TABLE_ID")

        self.base_url = f"https://api.airtable.com/v0/{self.base_id}/{self.table_id}"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        self.successful_uploads = []
        self.failed_uploads = []

    def generate_batch_3_posts(self) -> List[Dict]:
        """Generate the 10 posts for Batch 3"""
        posts = [
            {
                "title": "Cloud-Based Operations",
                "content": "Going paperless saved us 20+ hours monthly and $3k in storage costs. 📁\n\nOur rule: if it touches paper, automate it. Contracts → DocuSign, Invoices → Cloud, Files → Drive.\n\nResult: Access anywhere, searchable everything, zero filing cabinets.\n\nPaper is a single point of failure. Cloud is not.",
                "topic": "Cloud-Based Operations and Going Paperless"
            },
            {
                "title": "Automated Reporting Systems",
                "content": "This saved our leadership team 15 hours per month: automated reporting. 📊\n\nWe built dashboards that pull from:\n→ CRM (pipeline)\n→ Finance (cash flow)\n→ Support (tickets)\n→ Marketing (conversions)\n\nNo more manual data compilation. Just live insights when you need them.",
                "topic": "Automated Reporting Systems"
            },
            {
                "title": "API Integration Fundamentals",
                "content": "The difference between businesses that scale and those that plateau? API integrations. 🔌\n\nEvery tool you use has an API. Connect them = no manual data transfer.\n\nWe linked CRM → invoicing → project management. Data flows automatically.\n\nManual data entry is a choice, not a requirement.",
                "topic": "API Integration Fundamentals"
            },
            {
                "title": "Client Onboarding Automation",
                "content": "Here's how we cut client onboarding time from 4 days to 4 hours: 🚀\n\nDay 1: Contract signed → triggers welcome sequence\nDay 1: Payment received → access granted automatically\nDay 1: Onboarding checklist → sent with progress tracking\nDay 2: Kickoff call → pre-scheduled via calendar link\n\nFirst impressions are automated now.",
                "topic": "Client Onboarding Automation"
            },
            {
                "title": "Proactive Issue Detection",
                "content": "The best problems are ones you catch before customers notice. 🔍\n\nWe built alerts for:\n- Server response times >2s\n- Error rates >1%\n- Payment failures\n- Integration disconnects\n\nBy the time a customer reaches out, we're already fixing it. That's service excellence.",
                "topic": "Proactive Issue Detection"
            },
            {
                "title": "Strategic Payment Automation",
                "content": "This increased our collection rate from 73% to 94%: strategic payment reminders. 💳\n\nDay 0: Invoice + payment link\nDay 1: Auto-charge if card on file\nDay 5: Gentle reminder (\"Just checking...\")\nDay 10: Firmer reminder (\"We need this to continue...\")\nDay 15: Escalation (\"Service will pause...\")\n\nNo anger, no awkwardness. Just systems.",
                "topic": "Automated Invoicing and Payment Follow-ups"
            },
            {
                "title": "Scope Creep Prevention",
                "content": "Scope creep killed our margins until we automated boundaries. 🛡️\n\nNow every project has:\n- Auto-tracked hours per phase\n- Alerts at 80% capacity\n- Change request forms (not verbal asks)\n- Approval workflows\n\nResult: 40% fewer overruns, healthier client relationships. Clear systems = clear expectations.",
                "topic": "Scope Creep Prevention Systems"
            },
            {
                "title": "Hybrid Human-AI Workflows",
                "content": "The future isn't AI replacing humans—it's AI amplifying them. 🤖👤\n\nOur best workflows:\n- AI drafts → human edits\n- AI analyzes → human decides\n- AI flags → human resolves\n\nWe're 3x faster while maintaining quality. The magic is in the handoff, not the replacement.",
                "topic": "Hybrid Human-AI Workflows"
            },
            {
                "title": "Predictive Churn Detection",
                "content": "We cut customer churn by 35% with one automation: predictive alerts. ⚠️\n\nSignals we track:\n- Login frequency drops\n- Feature usage declines\n- Support tickets increase\n- Engagement score falls\n\nWhen 3+ signals fire, account manager gets alerted. Intervention happens before cancellation. Prevention > recovery.",
                "topic": "Predictive Churn Detection"
            },
            {
                "title": "A/B Testing Automation",
                "content": "This ended our endless debates about copy/design: automated A/B testing. 🧪\n\nNow:\n- Tests run automatically\n- Statistical significance calculated\n- Winners promoted\n- Losers archived with learnings\n\nNo more opinions. Just data-driven decisions at scale. We test 10x more than we used to.",
                "topic": "A/B Testing Automation"
            }
        ]
        return posts

    def get_all_posts(self) -> List[Dict]:
        """Combine all batches into one list"""

        # Batch 1 (provided)
        batch_1 = [
            {"title": "Prompt Engineering Fundamentals", "content": "Most businesses are doing AI prompts wrong. They ask vague questions and get vague answers.\n\nThe fix? Three simple rules:\n1. Give context (\"You're a sales expert...\")\n2. Be specific (\"Write 3 subject lines...\")\n3. Show examples (\"Like this: ...\")\n\nYour AI is only as good as your instructions. Treat it like briefing a junior employee—clear, structured, actionable. 🎯", "topic": "Prompt Engineering Fundamentals"},
            {"title": "AI-Powered Customer Service", "content": "Here's how AI-powered responses save you 15+ hours per week:\n\nStop writing the same customer emails manually. Build a response library with AI that:\n- Matches your brand voice\n- Addresses common questions\n- Personalizes based on context\n\nYour team reviews and sends. You save time without losing the human touch. Win-win. 💡", "topic": "AI-Powered Customer Service Responses"},
            {"title": "Automated Content Repurposing", "content": "This one automation saved us 12 hours weekly: content repurposing.\n\nOne long-form piece becomes:\n→ 5 LinkedIn posts\n→ 10 tweets\n→ 3 email newsletters\n→ 1 carousel\n\nThe system extracts key points, reformats, and queues everything. You create once, distribute everywhere. That's leverage. 📊", "topic": "Automated Content Repurposing with AI"},
            {"title": "80/20 Rule of AI Adoption", "content": "The difference between AI adoption winners and losers? The 80/20 rule.\n\n80% of value comes from automating:\n- Data entry\n- Email responses\n- Report generation\n- Meeting summaries\n\nStart there. Nail the basics before chasing complex AI projects. Small wins compound into massive efficiency gains. 🚀", "topic": "The 80/20 Rule of AI Adoption"},
            {"title": "Standard Operating Procedures", "content": "Most businesses are doing SOPs wrong—they write them once and never update them.\n\nHere's the truth: SOPs should be living documents that:\n- Capture what actually works\n- Get updated after every iteration\n- Feed into your automation stack\n\nYour SOPs are your automation blueprint. Treat them accordingly. 📋", "topic": "Standard Operating Procedures That Don't Suck"},
            {"title": "Building Feedback Loops", "content": "Here's how feedback loops save you from operational chaos:\n\nEvery automated process needs:\n1. Success metrics\n2. Error alerts\n3. Weekly reviews\n\nWithout feedback, automation becomes a black box. With it, you catch problems early and improve continuously. Automation without monitoring is just delegation with extra steps. 🔄", "topic": "Feedback Loops for Continuous Improvement"},
            {"title": "Automated Invoicing and Payment Follow-ups", "content": "This one automation improved our cash flow by 40%: automated payment follow-ups.\n\nDay 0: Invoice sent\nDay 3: Friendly reminder\nDay 7: Second notice\nDay 14: Escalation alert\n\nNo manual tracking. No awkward conversations. Just systematic follow-through that protects your revenue. Your future self will thank you. 💰", "topic": "Automated Invoicing and Payment Follow-ups"},
            {"title": "Tasks vs Workflows vs Systems", "content": "The difference between tasks, workflows, and systems will change how you think about your business.\n\nTask: Send invoice\nWorkflow: Invoice → reminder → payment\nSystem: Automated invoicing + cash flow dashboard + alerts\n\nMost people optimize tasks. Winners build systems. 🎯", "topic": "The Difference Between Tasks, Workflows, and Systems"},
            {"title": "Real-Time Dashboard Creation", "content": "Here's how real-time dashboards save you 10+ hours of reporting monthly:\n\nConnect your tools once. Get instant visibility into:\n- Revenue\n- Pipeline\n- Customer health\n- Team capacity\n\nStop compiling reports manually. Start making decisions from live data. That's how you scale without losing control. 📈", "topic": "Real-Time Dashboard Creation"},
            {"title": "Automated Quality Assurance", "content": "Most businesses are doing quality control wrong—they check after problems happen.\n\nSmart approach? Automated QA checklists that:\n- Run before delivery\n- Flag inconsistencies\n- Enforce standards\n- Document everything\n\nCatch issues before customers do. That's how you build a reputation for excellence. ✅", "topic": "Automated Quality Assurance Checklists"}
        ]

        # Batch 2 (provided)
        batch_2 = [
            {"title": "Custom GPT Creation", "content": "Most businesses waste $5k/month on generic AI tools when a custom GPT costs $20. 🎯\n\nWe built a proposal generator that knows our pricing, tone, and past wins. Now proposals take 8 minutes instead of 3 hours.\n\nThe difference? Training data you already have.", "topic": "Custom GPT Creation for Specific Business Functions"},
            {"title": "AI-Assisted Proposal Writing", "content": "Here's how we cut proposal time by 87%: 📝\n\n1. Feed AI your best 10 proposals\n2. Create templates with dynamic sections\n3. Let AI draft, humans refine\n\nResult: 3 hours → 20 minutes. Same win rate. Zero burnout.\n\nStop writing from scratch every time.", "topic": "AI-Assisted Proposal Writing"},
            {"title": "Intelligent Email Triage", "content": "The average executive gets 121 emails/day. Only 12 need their attention. 📧\n\nWe built an AI filter that scores urgency, extracts action items, and auto-routes 90% of messages.\n\nYour inbox shouldn't be your job. Triage should be automated.", "topic": "Intelligent Email Triage and Prioritization"},
            {"title": "Automation Audit Framework", "content": "This saved us 40 hours last month: 🔍\n\nMap every task your team does weekly → Score by frequency + time cost → Automate anything scoring 15+\n\nWe found 23 tasks eating 6 hours/week each. Automated 19 of them.\n\nMost businesses automate randomly. Winners audit first.", "topic": "The Automation Audit Framework"},
            {"title": "CRM Automation Beyond Basics", "content": "Your CRM can do more than send email sequences. 💡\n\nReal power: Auto-qualify leads from behavior, trigger custom workflows per deal stage, predict churn before it happens.\n\nWe doubled sales velocity by automating what happens *between* touchpoints.", "topic": "CRM Automation Beyond the Basics"},
            {"title": "Zapier vs Make vs Custom Scripts", "content": "The difference between Zapier, Make, and custom scripts? 🛠️\n\nZapier: Fast setup, expensive at scale\nMake: Complex logic, better pricing\nCustom: Total control, requires dev\n\nWe use all three. The key is knowing when to graduate from one to the next.", "topic": "Zapier vs Make vs Custom Scripts: Decision Framework"},
            {"title": "Self-Annealing Systems", "content": "Here's how systems fix themselves: 🔧\n\nWhen an automation breaks, it logs the error → AI reads the log → suggests a fix → tests it → updates documentation.\n\nWe went from 8 hours/week maintaining automations to 45 minutes.\n\nYour systems should get stronger when they fail.", "topic": "Building Self-Annealing Systems"},
            {"title": "Dependency Mapping", "content": "Most automation projects fail because of hidden dependencies. 🕸️\n\nBefore building, we map: What data feeds this? What breaks if this fails? What depends on this output?\n\nOne client saved 3 weeks of rework by spending 2 hours mapping dependencies first.", "topic": "Dependency Mapping in Complex Workflows"},
            {"title": "Modular System Design", "content": "The difference between fragile and antifragile automation? Modules. 🧩\n\nBuild each component to work independently. Swap pieces without breaking the whole.\n\nWe rebuilt a client's system in 3 days (not 3 weeks) because everything was modular. Change became easy.", "topic": "Modular System Design"},
            {"title": "Documentation-Driven Operations", "content": "This changed everything for us: Write the documentation first. 📋\n\nBefore building automation, document how it should work. Forces clear thinking, reveals gaps, becomes training material.\n\nTeams with docs-first culture scale 3x faster. Knowledge doesn't live in someone's head.", "topic": "Documentation-Driven Operations"}
        ]

        # Batch 3 (generated)
        batch_3 = self.generate_batch_3_posts()

        return batch_1 + batch_2 + batch_3

    def create_record(self, fields: Dict) -> Optional[Dict]:
        """
        Create a single record in Airtable

        Args:
            fields: Dictionary of field names and values

        Returns:
            Created record data or None if failed
        """
        try:
            payload = {
                "records": [
                    {
                        "fields": fields
                    }
                ]
            }

            response = requests.post(
                self.base_url,
                json=payload,
                headers=self.headers,
                timeout=30
            )

            if response.status_code in [200, 201]:
                result = response.json()
                record = result.get('records', [{}])[0]
                logger.info(f"Created record: {record.get('id')} - {fields.get('Title', 'Untitled')}")
                return record
            else:
                logger.error(f"Error creating record: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Exception creating record: {e}")
            return None

    def create_scheduled_time(self, day_offset: int) -> str:
        """
        Create a scheduled time for a post

        Args:
            day_offset: Number of days from tomorrow (0 = tomorrow)

        Returns:
            ISO format datetime string
        """
        # Start from tomorrow
        base_date = datetime.now() + timedelta(days=1)

        # Add day offset
        scheduled_date = base_date + timedelta(days=day_offset)

        # Set time to 9:00 AM
        scheduled_time = scheduled_date.replace(hour=9, minute=0, second=0, microsecond=0)

        # Return ISO format with timezone
        return scheduled_time.isoformat()

    def upload_posts(self, posts: List[Dict]) -> Dict:
        """
        Upload all posts to Airtable

        Args:
            posts: List of post dictionaries

        Returns:
            Summary dictionary with success/failure counts
        """
        logger.info(f"Starting upload of {len(posts)} posts to Airtable")

        for idx, post in enumerate(posts):
            try:
                # Prepare fields for Airtable
                fields = {
                    "Title": post.get('title', f"Post {idx+1}"),
                    "Post Content": post.get('content', ''),
                    "Status": "Draft",
                    "Scheduled Time": self.create_scheduled_time(idx)
                }

                # Create record
                record = self.create_record(fields)

                if record:
                    self.successful_uploads.append({
                        'record_id': record.get('id'),
                        'title': fields['Title'],
                        'scheduled_time': fields['Scheduled Time']
                    })
                else:
                    self.failed_uploads.append({
                        'title': fields['Title'],
                        'error': 'Failed to create record'
                    })

            except Exception as e:
                logger.error(f"Error processing post {idx+1}: {e}")
                self.failed_uploads.append({
                    'title': post.get('title', f"Post {idx+1}"),
                    'error': str(e)
                })

        # Prepare summary
        summary = {
            'total_posts': len(posts),
            'successful': len(self.successful_uploads),
            'failed': len(self.failed_uploads),
            'success_rate': (len(self.successful_uploads) / len(posts) * 100) if posts else 0,
            'successful_uploads': self.successful_uploads,
            'failed_uploads': self.failed_uploads
        }

        return summary

    def print_summary(self, summary: Dict):
        """Print a formatted summary of the upload"""
        print("\n" + "="*80)
        print("LINKEDIN POSTS BATCH UPLOAD SUMMARY")
        print("="*80)
        print(f"\nTotal Posts: {summary['total_posts']}")
        print(f"Successful: {summary['successful']} ({summary['success_rate']:.1f}%)")
        print(f"Failed: {summary['failed']}")

        if summary['successful_uploads']:
            print("\n" + "-"*80)
            print("SUCCESSFULLY UPLOADED POSTS:")
            print("-"*80)
            for idx, upload in enumerate(summary['successful_uploads'], 1):
                scheduled_dt = datetime.fromisoformat(upload['scheduled_time'])
                print(f"\n{idx}. {upload['title']}")
                print(f"   Record ID: {upload['record_id']}")
                print(f"   Scheduled: {scheduled_dt.strftime('%Y-%m-%d at %I:%M %p')}")

        if summary['failed_uploads']:
            print("\n" + "-"*80)
            print("FAILED UPLOADS:")
            print("-"*80)
            for idx, failure in enumerate(summary['failed_uploads'], 1):
                print(f"\n{idx}. {failure['title']}")
                print(f"   Error: {failure['error']}")

        print("\n" + "="*80)
        print(f"Upload completed at {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}")
        print("="*80 + "\n")


def main():
    """Main execution function"""
    try:
        # Initialize uploader
        uploader = LinkedInBatchUploader()

        # Get all posts
        posts = uploader.get_all_posts()

        logger.info(f"Loaded {len(posts)} posts for upload")

        # Upload posts
        summary = uploader.upload_posts(posts)

        # Print summary
        uploader.print_summary(summary)

        # Save summary to log file
        import json
        summary_file = f'upload_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Summary saved to {summary_file}")

        # Return exit code based on success
        if summary['failed'] > 0:
            logger.warning(f"Upload completed with {summary['failed']} failures")
            return 1
        else:
            logger.info("All posts uploaded successfully!")
            return 0

    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
