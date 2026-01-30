"""
Draft Post Generator - Generates post content only (no images, no scheduling).
Posts created with Draft status, waiting for user review.
Maintains inventory of 21+ Draft posts.
"""

import os
import sys
import json
import random
from pathlib import Path
from datetime import datetime
from typing import List
import requests

sys.path.insert(0, str(Path(__file__).parent))
from optimized_post_generator import OptimizedPostGenerator
from post_quality_checker import PostQualityChecker

class DraftPostGenerator:
    """Generates draft posts and maintains inventory."""

    def __init__(self):
        """Initialize generator."""
        env_file = "/Users/musacomma/Agentic Workflow/.env"
        if os.path.exists(env_file):
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip().strip('"\'')

        self.generator = OptimizedPostGenerator()
        self.quality_checker = PostQualityChecker()
        self.airtable_api_key = os.environ.get('AIRTABLE_API_KEY')
        self.airtable_base_id = os.environ.get('AIRTABLE_BASE_ID')
        self.airtable_table_id = os.environ.get('AIRTABLE_LINKEDIN_TABLE_ID')
        self.headers = {
            "Authorization": f"Bearer {self.airtable_api_key}",
            "Content-Type": "application/json"
        }

        self.topics = [
            # Successful Prompting Techniques
            "Chain-of-Thought Prompting for Better AI Responses",
            "Few-Shot Learning Techniques for Precise AI Outputs",
            "How to Give AI Permission to Express Uncertainty",
            "Structured Output Formats for Consistent AI Results",
            "Semantic Clarity in AI Prompts: Getting What You Actually Want",
            "Role-Based Prompting: Making AI Think Like Your Expert",

            # Processes That Can Be Automated
            "Streamlining Client Onboarding with Automation",
            "Automated Invoicing and Payment Management Systems",
            "Proposal Generation and Delivery Automation",
            "Automating Repetitive Email and Data Entry Tasks",
            "Task Assignment and Workflow Distribution Automation",
            "Automating Follow-Up Sequences and Reminders",
            "Employee Onboarding and Training Automation",
            "Service Delivery Automation Without Losing Quality",

            # Healthy Relationship with AI and Automation
            "Human Oversight in AI Systems: Why It Matters",
            "Avoiding Over-Reliance on Automation and AI",
            "Building Automation with Escalation to Humans",
            "Maintaining Critical Thinking in an Automated Business",
            "Decision-Making Control: Where Humans Must Remain in Charge",
            "Audit Practices for AI and Automation Systems",
            "The Hidden Costs of Over-Automating Your Business",

            # AI and Automation Tools and Their Applications
            "ChatGPT vs Claude vs Gemini: Choosing the Right AI for Your Business",
            "Zapier for Business Automation: What It Can Actually Do",
            "Make.com Workflow Automation: Beyond the Basics",
            "n8n vs Zapier vs Make: Open-Source Automation Platforms",
            "No-Code Automation Platforms for Non-Technical Teams",
            "AI Integration: Connecting Tools Into Your Workflow",
            "Selecting the Right Automation Platform for Your Business",

            # === NEW TOPICS - PHASE 3 EXPANSION ===

            # Category: AI Implementation & Integration
            "How to Audit Your Business for AI Opportunities",
            "Building Your First AI Automation: A Step-by-Step Guide",
            "Selecting the Right AI Tool for Your Specific Business Need",
            "Integrating AI into Existing Workflows Without Disruption",
            "Measuring ROI on AI and Automation Investments",

            # Category: Practical AI Techniques
            "Prompt Engineering for Consistent Brand Voice",
            "Using AI for Customer Research and Insights",
            "AI-Assisted Content Repurposing: One Post to 10 Formats",
            "Automating Client Communication Without Losing Personal Touch",
            "AI for Competitive Analysis and Market Research",

            # Category: Business Process Automation
            "Creating SOPs That Enable Automation",
            "Automating Sales Pipeline Management",
            "Client Reporting Automation That Impresses",
            "Email Sequence Automation for Lead Nurturing",
            "Automated Quality Control for Service Businesses",

            # Category: AI Strategy & Planning
            "Building an AI Adoption Roadmap for Your Business",
            "Training Your Team to Use AI Effectively",
            "Data Preparation for AI: What You Need Before Starting",
            "Privacy and Security Considerations for AI in Business",
            "When NOT to Automate: Critical Human Touchpoints",

            # Businesses Using AI and Automation for Competitive Advantage
            "How Healthcare Providers Use AI to Outpace Competition",
            "Financial Services Automation: 85% Efficiency Gains Real",
            "E-Commerce Brands Scaling with AI-Powered Personalization",
            "Logistics Companies Ahead of Competition Through Automation",
            "Customer Service Excellence via AI-First Support Systems",
            "Marketing Automation for 544% ROI and Faster Campaigns",
            "How Startups Beat Established Companies with Smart Automation",

            # Using AI While Maintaining Authenticity
            "Building Your Brand Voice in an AI-Saturated World",
            "Keeping Your Personal Touch While Using AI Tools",
            "Emotional Authenticity: Sharing Real Stories Over AI Content",
            "Teaching AI Your Writing Style for Authentic Content",
            "When to Use AI Behind the Scenes (and When to Show It)",
            "Why 1 in 4 Business Owners Lost Clients to Inauthentic AI",
            "The Balance: AI Efficiency Without Losing Human Connection"
        ]

    def count_draft_posts(self) -> int:
        """Count existing Draft posts in Airtable."""
        url = f"https://api.airtable.com/v0/{self.airtable_base_id}/{self.airtable_table_id}"
        response = requests.get(url, headers=self.headers)

        if response.status_code != 200:
            return 0

        posts = response.json().get('records', [])
        draft_count = sum(1 for p in posts if p.get('fields', {}).get('Status') == 'Draft')
        return draft_count

    def generate_draft_post(self, topic: str = None, educational_mode: bool = False, automation_showcase_mode: bool = False, automation_name: str = None) -> dict:
        """Generate a single draft post (content only, no images/scheduling).

        Args:
            topic: Optional specific topic to use. If None, random selection.
            educational_mode: If True, generate instructional content with examples/steps
            automation_showcase_mode: If True, generate automation showcase content
            automation_name: Name of the automation to showcase (used in automation_showcase_mode)
        """
        if topic is None:
            topic = random.choice(self.topics)

        post = self.generator.generate_complete_post(
            topic,
            educational_mode=educational_mode,
            automation_showcase_mode=automation_showcase_mode,
            automation_name=automation_name
        )

        # Remove scheduling-related fields
        post['scheduled_time'] = None
        post['status'] = 'Draft'
        # Store the topic that was used to generate this post
        post['post_topic'] = topic

        return post

    def get_diverse_topics(self, count: int = 21) -> List[str]:
        """Get a diverse set of topics (sampling without replacement).

        Args:
            count: Number of topics to return (max 42)

        Returns:
            List of unique topics, shuffled for randomness
        """
        # Sample unique topics without replacement
        count = min(count, len(self.topics))  # Can't sample more than available
        selected_topics = random.sample(self.topics, count)
        return selected_topics

    def map_framework_to_airtable(self, framework: str) -> str:
        """Map internal framework names to Airtable select options."""
        framework_mapping = {
            "PAS": "PAS (Problem-Agitate-Solution)",
            "AIDA": "AIDA (Attention-Interest-Desire-Action)",
            "BAB": "BAB (Before-After-Bridge)",
            "Framework": "How-To Guide",
            "Contrarian": "Listicle"
        }
        return framework_mapping.get(framework, framework)

    def add_post_to_airtable(self, post: dict) -> tuple:
        """Add draft post to Airtable with QC validation.

        Returns: (success: bool, qc_result: dict or None)
        """
        # Step 1: Run quality checks
        qc_result = self.quality_checker.validate_post(post, check_duplicates=True)

        if not qc_result['passes_qc']:
            # QC failed - return failure with issues
            return False, qc_result

        # Step 2: If QC passes, upload to Airtable
        url = f"https://api.airtable.com/v0/{self.airtable_base_id}/{self.airtable_table_id}"

        metadata = f"""Writing Framework: {post['framework']}
Hook Type: {post['hook_type']}
CTA Type: {post['cta_type']}
Post Type: {post['post_type']}
Visual Type: {post['visual_type']}
Visual Spec: {json.dumps(post['visual_spec'])}
QC Status: PASSED"""

        fields = {
            "Title": post['title'],
            "Post Content": post['full_content'],
            "Status": post['status'],
            "Post Topic": post.get('post_topic', 'N/A'),  # Track the topic used to generate this post
            "Writing Framework": self.map_framework_to_airtable(post['framework']),
            "Image Prompt": f"Visual Type: {post['visual_type']} | Dimensions: {post['visual_spec'].get('dimensions', 'N/A')}",
            "Notes": metadata
        }

        payload = {
            "records": [
                {
                    "fields": fields
                }
            ]
        }

        response = requests.post(url, headers=self.headers, json=payload)
        success = response.status_code == 200

        if success:
            return True, qc_result
        else:
            # Upload failed
            return False, {'error': f'Airtable upload failed: {response.status_code}'}

    def maintain_inventory(self, target: int = 21, max_retries: int = 5):
        """Generate posts to maintain minimum inventory with quality control.

        Uses diverse topic selection to ensure variety across posts.

        Args:
            target: Target number of Draft posts
            max_retries: Max attempts to generate a valid post before giving up
        """
        current = self.count_draft_posts()
        needed = max(0, target - current)

        if needed == 0:
            print(f"✅ Inventory satisfied: {current} Draft posts (target: {target})")
            return

        print(f"📝 Generating {needed} posts (current: {current}, target: {target})")
        print(f"🎯 Using topic diversity: sampling {needed} unique topics\n")

        # Get diverse topics upfront - ensures no topic is repeated in this batch
        diverse_topics = self.get_diverse_topics(needed)
        print(f"📋 Topics selected for this batch:")
        for i, topic in enumerate(diverse_topics, 1):
            print(f"   {i}. {topic}")
        print()

        added_count = 0
        failed_posts = []
        topic_index = 0  # Track which topic in the diverse set we're using

        for i in range(needed):
            attempts = 0
            success = False
            current_topic = diverse_topics[i]  # Use the pre-selected diverse topic

            while attempts < max_retries and not success:
                attempts += 1
                # Try with the assigned topic, or a fallback if retrying
                topic_to_use = current_topic if attempts == 1 else random.choice(diverse_topics)
                post = self.generate_draft_post(topic=topic_to_use)

                upload_success, qc_result = self.add_post_to_airtable(post)

                if upload_success:
                    added_count += 1
                    print(f"  {i+1}/{needed} ✓ {post['title'][:60]}... (attempt {attempts})")
                    print(f"            Topic: {post['post_topic']}")
                    success = True
                else:
                    if attempts < max_retries:
                        print(f"  {i+1}/{needed} ⚠️  Attempt {attempts}/{max_retries} failed - retrying with different topic...")
                        if qc_result and qc_result.get('issues'):
                            for issue in qc_result['issues'][:1]:
                                print(f"             Issue: {issue[:70]}...")
                    else:
                        print(f"  {i+1}/{needed} ❌ Failed after {max_retries} attempts")
                        failed_posts.append({
                            'title': post['title'],
                            'issues': qc_result.get('issues', []) if qc_result else ['Unknown error']
                        })

        print(f"\n{'='*80}")
        print(f"✅ Added {added_count} Draft posts to inventory (target: {needed})")
        print(f"📊 Topic Variety: {added_count}/{needed} posts use unique topics")

        if failed_posts:
            print(f"\n⚠️  {len(failed_posts)} posts failed QC after {max_retries} attempts:")
            for failed in failed_posts:
                print(f"\n  Title: {failed['title'][:70]}...")
                print(f"  Issues:")
                for issue in failed['issues']:
                    print(f"    • {issue[:80]}")

def main():
    """Main execution."""
    print("="*80)
    print("📋 DRAFT POST GENERATOR - INVENTORY MAINTENANCE")
    print("="*80 + "\n")

    generator = DraftPostGenerator()
    generator.maintain_inventory(target=21)

    print("\n" + "="*80)
    print("✅ INVENTORY MANAGEMENT COMPLETE")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
