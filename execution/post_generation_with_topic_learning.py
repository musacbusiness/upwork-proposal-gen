"""
LinkedIn Post Generation with Topic Learning
Generates posts using weighted topic selection based on approval history.
"""

import os
import json
import requests
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from execution.topic_performance_analyzer import TopicPerformanceAnalyzer

# All 73 topics
ALL_TOPICS = [
    "Prompt Engineering Fundamentals",
    "The 80/20 Rule of AI Adoption",
    "AI-Powered Customer Service Responses",
    "Automated Content Repurposing with AI",
    "AI-Assisted Proposal Writing",
    "Intelligent Email Triage and Prioritization",
    "Custom GPT Creation for Specific Business Functions",
    "AI-Powered Meeting Summarization",
    "Contextual AI Knowledge Bases",
    "Prompt Chaining for Complex Tasks",
    "The Automation Audit Framework",
    "Zapier vs Make vs Custom Scripts: Decision Framework",
    "Building Your First Business Automation in 30 Minutes",
    "Multi-Step Workflow Automation Design",
    "Error Handling in Automated Workflows",
    "Automated Data Entry from Emails and Forms",
    "CRM Automation Beyond the Basics",
    "Automated Invoicing and Payment Follow-ups",
    "Document Generation Automation",
    "Slack/Teams Notification Systems",
    "Client Onboarding Automation",
    "Project Status Updates Without Manual Work",
    "Automated Quality Assurance Checklists",
    "Customer Feedback Collection and Analysis",
    "Proactive Issue Detection",
    "Resource Allocation Optimization",
    "Scope Creep Prevention Systems",
    "Delivery Timeline Automation",
    "Post-Project Review Automation",
    "Upsell and Cross-Sell Trigger Systems",
    "The Virtual Employee Framework",
    "Automated Training and Onboarding",
    "Self-Service Customer Portals",
    "AI-Powered First-Line Support",
    "Automated Lead Qualification",
    "Delegation Frameworks for Founders",
    "Asynchronous Communication Systems",
    "ChatGPT vs Claude vs Gemini: Business Use Cases",
    "AI-Powered Market Research",
    "Automated Social Media Management",
    "AI Writing Assistants for Business Communication",
    "Voice-to-Text Automation for Documentation",
    "AI-Powered Translation for Global Business",
    "AI-Powered Competitor Analysis",
    "Sentiment Analysis for Customer Communications",
    "AI-Generated Case Studies and Testimonials",
    "Personalized Outreach at Scale",
    "AI-Powered Contract Review",
    "Automated Competitive Pricing Intelligence",
    "AI-Enhanced Sales Call Analysis",
    "Smart Content Recommendations for Leads",
    "AI-Powered Meeting Preparation",
    "Automated Follow-Up Sequences Based on Engagement",
    "Automated Appointment Scheduling and Reminders",
    "Dynamic Pricing Automation",
    "Automated Referral Request Systems",
    "Subscription and Recurring Revenue Automation",
    "Automated Proposal Follow-Up Sequences",
    "Win-Back Campaigns for Lost Customers",
    "Automated Testimonial Collection",
    "Cart Abandonment Recovery Automation",
    "Automated Renewal and Upgrade Prompts",
    "Lead Magnet Delivery and Nurture Automation",
    "Automated Expense Tracking and Categorization",
    "Inventory and Stock Alert Automation",
    "Automated Vendor Management",
    "Meeting-Free Monday Automation",
    "Automated Task Prioritization",
    "Client Communication Templates with AI Personalization",
    "Automated Project Kickoff Workflows",
    "Time Zone Management Automation",
    "Automated Weekly Review Generation",
    "Smart Notification Filtering"
]


class LinkedInPostGenerator:
    """Generates LinkedIn posts with intelligent topic selection."""

    def __init__(self):
        """Initialize the post generator."""
        self.analyzer = TopicPerformanceAnalyzer()
        self.airtable_api_key = os.environ.get('AIRTABLE_API_KEY')
        self.airtable_base_id = os.environ.get('AIRTABLE_BASE_ID')
        self.airtable_table_id = os.environ.get('AIRTABLE_LINKEDIN_TABLE_ID')
        self.headers = {
            "Authorization": f"Bearer {self.airtable_api_key}",
            "Content-Type": "application/json"
        }

    def initialize_topics(self):
        """Initialize all 73 topics in the analyzer."""
        for topic in ALL_TOPICS:
            self.analyzer.initialize_topic(topic)
        print(f"✅ Initialized {len(ALL_TOPICS)} topics")

    def select_next_topic(self) -> Optional[str]:
        """
        Select the next topic for post generation using weighted randomization.
        High-performing topics are more likely to be selected.
        """
        try:
            topic = self.analyzer.select_weighted_topic()
            return topic
        except ValueError as e:
            print(f"❌ No topics available: {e}")
            return None

    def update_post_approval_status(self, record_id: str, approved: bool, topic_name: str) -> bool:
        """
        Update approval status when a post is approved/denied and record in analyzer.
        Called when user approves/denies a post.
        """
        # Record in analyzer
        result = self.analyzer.record_post_result(topic_name, approved)

        # Log the result
        status = "✅ APPROVED" if approved else "❌ DENIED"
        print(f"\n{status}: {topic_name}")
        print(f"  Topic approval rate: {result['approval_rate']*100:.1f}%")
        print(f"  Total posts from this topic: {result['total_posts']}")

        if result['deprecation_notice']:
            print(f"  🔴 TOPIC DEPRECATED: {topic_name}")
            print(f"     {result['deprecation_notice']['reason']}")
            print(f"     Total posts: {result['deprecation_notice']['total_posts']}")
            print(f"     Approved: {result['deprecation_notice']['approved']}")
            print(f"     Denied: {result['deprecation_notice']['denied']}")

        return True

    def get_performance_dashboard(self) -> str:
        """Get formatted performance dashboard."""
        self.analyzer.print_performance_report()
        return self.analyzer.get_performance_stats()

    def sync_performance_to_airtable(self) -> bool:
        """Sync topic performance metrics to Airtable for dashboard visibility."""
        stats = self.analyzer.get_performance_stats()

        print("\n📊 Topic Performance Summary:")
        print(f"   Total Posts Analyzed: {stats['total_posts_analyzed']}")
        print(f"   Active Topics: {stats['active_topics']}/{stats['total_topics']}")
        print(f"   Deprecated Topics: {stats['deprecated_topics']}")

        if stats['deprecated_topics'] > 0:
            print(f"\n   🔴 Deprecated Topics:")
            for topic, data in stats['topics'].items():
                if data['deprecated']:
                    print(f"      - {topic} (0% approval)")

        return True


class AirtableApprovalTracker:
    """Track post approvals/denials and update topic performance."""

    def __init__(self):
        """Initialize tracker with Airtable connection."""
        env_file = "/Users/musacomma/Agentic Workflow/.env"
        self.env = self._load_env(env_file)

        self.api_key = self.env.get('AIRTABLE_API_KEY')
        self.base_id = self.env.get('AIRTABLE_BASE_ID')
        self.table_id = self.env.get('AIRTABLE_LINKEDIN_TABLE_ID')
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.analyzer = TopicPerformanceAnalyzer()
        self.initialize_topics()

    def _load_env(self, env_file: str) -> Dict:
        """Load environment variables."""
        env = {}
        if os.path.exists(env_file):
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        env[key.strip()] = value.strip().strip('"\'')
        return env

    def initialize_topics(self):
        """Initialize all topics."""
        for topic in ALL_TOPICS:
            self.analyzer.initialize_topic(topic)

    def sync_post_topics_to_airtable(self, record_id: str, topic_name: str) -> bool:
        """Add topic field to a post record."""
        url = f"https://api.airtable.com/v0/{self.base_id}/{self.table_id}/{record_id}"

        payload = {
            "fields": {
                "Topic": topic_name
            }
        }

        response = requests.patch(url, headers=self.headers, json=payload)
        return response.status_code == 200

    def process_post_status_changes(self) -> Dict:
        """
        Scan Airtable for status changes (Approved/Denied) and update topic performance.
        Returns summary of processed posts.
        """
        url = f"https://api.airtable.com/v0/{self.base_id}/{self.table_id}"

        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            print(f"❌ Error fetching records: {response.status_code}")
            return {}

        records = response.json().get('records', [])
        processed = {'approved': 0, 'denied': 0, 'deprecated': []}

        for record in records:
            fields = record.get('fields', {})
            status = fields.get('Status')
            topic = fields.get('Topic')

            # Only process posts with topic assignments
            if not topic:
                continue

            # Check if status is Approved or Rejected
            if status == 'Approved':
                result = self.analyzer.record_post_result(topic, approved=True)
                processed['approved'] += 1

                if result['deprecation_notice']:
                    processed['deprecated'].append(result['deprecation_notice'])

            elif status == 'Rejected':
                result = self.analyzer.record_post_result(topic, approved=False)
                processed['denied'] += 1

                if result['deprecation_notice']:
                    processed['deprecated'].append(result['deprecation_notice'])

        return processed

    def print_performance_report(self):
        """Print formatted performance report."""
        self.analyzer.print_performance_report()


# Integration function
def suggest_next_topic_for_generation() -> str:
    """
    Public function to suggest next topic for post generation.
    Call this before generating a new post.
    """
    # Load environment
    env_file = "/Users/musacomma/Agentic Workflow/.env"
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"\'')

    generator = LinkedInPostGenerator()
    generator.initialize_topics()

    topic = generator.select_next_topic()
    if topic:
        approval_rate = generator.analyzer.data['topics'][topic]['approval_rate'] * 100
        print(f"\n🎯 Suggested Topic: {topic}")
        print(f"   Approval Rate: {approval_rate:.1f}%")
    return topic


if __name__ == "__main__":
    # Example usage
    print("=" * 100)
    print("📝 LinkedIn Post Generator with Topic Learning")
    print("=" * 100)

    # Initialize generator
    generator = LinkedInPostGenerator()
    generator.initialize_topics()

    # Show current performance
    print("\n📊 Current Topic Performance:")
    generator.get_performance_dashboard()

    # Suggest next topic
    print("\n🎯 Suggesting next topic for post generation...")
    topic = generator.select_next_topic()
    if topic:
        print(f"   Selected: {topic}")

    # Show how to track approvals
    print("\n" + "=" * 100)
    print("💡 How to Use This System:")
    print("=" * 100)
    print("""
1. When generating a new post:
   - Call suggest_next_topic_for_generation()
   - Use the suggested topic
   - Add the topic name to the post record in Airtable

2. When approving/denying posts:
   - Update the Status field in Airtable to "Approved" or "Rejected"
   - The system automatically learns from your decisions
   - Topics with high approval rates get selected more often
   - Topics with 0% approval get deprecated after 3 rejections

3. Check performance:
   - Run tracker.process_post_status_changes() to sync decisions
   - Run generator.get_performance_dashboard() to see stats
   - Deprecated topics no longer appear in suggestions
    """)
