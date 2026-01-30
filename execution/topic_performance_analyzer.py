"""
Topic Performance Analyzer
Self-annealing system that learns from your post approval/denial patterns.
- Tracks approval rates per topic
- Biases randomization toward high-performing topics
- Deprecates topics with 100% rejection rate
"""

import os
import json
import random
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
import requests


class TopicPerformanceAnalyzer:
    """Tracks and analyzes topic performance based on post approvals/denials."""

    def __init__(self, data_file: str = None):
        """Initialize the analyzer with persistent storage."""
        if data_file is None:
            data_file = str(Path(__file__).parent.parent / '.tmp' / 'topic_performance.json')

        self.data_file = data_file
        Path(self.data_file).parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load_data()

    def _load_data(self) -> Dict:
        """Load performance data from file."""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return {
            'topics': {},
            'last_updated': None,
            'total_posts_analyzed': 0,
            'deprecated_topics': []
        }

    def _save_data(self):
        """Save performance data to file."""
        self.data['last_updated'] = datetime.now().isoformat()
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=2)

    def initialize_topic(self, topic_name: str):
        """Initialize tracking for a new topic."""
        if topic_name not in self.data['topics']:
            self.data['topics'][topic_name] = {
                'total_posts': 0,
                'approved_posts': 0,
                'denied_posts': 0,
                'approval_rate': 1.0,  # Start at 100% (neutral bias)
                'deprecated': False,
                'created_at': datetime.now().isoformat()
            }
            self._save_data()

    def record_post_result(self, topic_name: str, approved: bool) -> Dict:
        """
        Record whether a post from a topic was approved or denied.
        Returns updated topic stats and any deprecation notices.
        """
        if topic_name not in self.data['topics']:
            self.initialize_topic(topic_name)

        topic = self.data['topics'][topic_name]
        topic['total_posts'] += 1

        if approved:
            topic['approved_posts'] += 1
        else:
            topic['denied_posts'] += 1

        # Calculate approval rate
        total = topic['total_posts']
        topic['approval_rate'] = topic['approved_posts'] / total if total > 0 else 1.0

        self.data['total_posts_analyzed'] += 1

        # Check for deprecation (100% rejection after at least 3 posts)
        deprecation_notice = None
        if (topic['denied_posts'] > 0 and
            topic['approved_posts'] == 0 and
            topic['total_posts'] >= 3):
            topic['deprecated'] = True
            if topic_name not in self.data['deprecated_topics']:
                self.data['deprecated_topics'].append(topic_name)
            deprecation_notice = {
                'topic': topic_name,
                'reason': 'Topic reached 100% rejection rate',
                'total_posts': topic['total_posts'],
                'approved': topic['approved_posts'],
                'denied': topic['denied_posts']
            }

        self._save_data()

        return {
            'topic': topic_name,
            'approval_rate': topic['approval_rate'],
            'total_posts': topic['total_posts'],
            'approved': topic['approved_posts'],
            'denied': topic['denied_posts'],
            'deprecated': topic.get('deprecated', False),
            'deprecation_notice': deprecation_notice
        }

    def get_active_topics(self) -> List[str]:
        """Get list of non-deprecated topics."""
        return [
            topic for topic, stats in self.data['topics'].items()
            if not stats.get('deprecated', False)
        ]

    def select_weighted_topic(self) -> str:
        """
        Select a topic using weighted randomization based on approval rates.
        Topics with higher approval rates have higher probability of selection.
        """
        active_topics = self.get_active_topics()

        if not active_topics:
            raise ValueError("No active topics available. All topics have been deprecated.")

        # Calculate weights based on approval rates
        # Use a power function to amplify differences: rate^2
        weights = []
        for topic in active_topics:
            rate = self.data['topics'][topic]['approval_rate']
            # Power of 2 to amplify the bias (high performers get much higher weight)
            weight = rate ** 2
            weights.append(weight)

        # Normalize weights
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]

        # Weighted random selection
        selected = random.choices(active_topics, weights=normalized_weights, k=1)[0]
        return selected

    def get_performance_stats(self) -> Dict:
        """Get comprehensive performance statistics."""
        stats = {
            'total_posts_analyzed': self.data['total_posts_analyzed'],
            'total_topics': len(self.data['topics']),
            'active_topics': len(self.get_active_topics()),
            'deprecated_topics': len(self.data['deprecated_topics']),
            'topics': {}
        }

        # Sort by approval rate (descending)
        sorted_topics = sorted(
            self.data['topics'].items(),
            key=lambda x: x[1]['approval_rate'],
            reverse=True
        )

        for topic, data in sorted_topics:
            stats['topics'][topic] = {
                'approval_rate': round(data['approval_rate'] * 100, 1),
                'total_posts': data['total_posts'],
                'approved': data['approved_posts'],
                'denied': data['denied_posts'],
                'deprecated': data.get('deprecated', False),
                'status': '🔴 DEPRECATED' if data.get('deprecated', False) else '✅ ACTIVE'
            }

        return stats

    def print_performance_report(self):
        """Print a formatted performance report."""
        stats = self.get_performance_stats()

        print("\n" + "=" * 100)
        print("📊 TOPIC PERFORMANCE ANALYSIS")
        print("=" * 100)
        print(f"\nTotal Posts Analyzed: {stats['total_posts_analyzed']}")
        print(f"Active Topics: {stats['active_topics']}/{stats['total_topics']}")
        print(f"Deprecated Topics: {stats['deprecated_topics']}")

        print("\n" + "-" * 100)
        print(f"{'Topic':<50} {'Approval Rate':<15} {'Posts':<12} {'Approved':<10} {'Denied':<10} {'Status':<15}")
        print("-" * 100)

        for topic, data in stats['topics'].items():
            approval_pct = data['approval_rate']
            status = data['status']

            # Color-code by status
            if approval_pct >= 75:
                bar = "█" * int(approval_pct / 5) + "░" * (20 - int(approval_pct / 5))
            elif approval_pct >= 50:
                bar = "█" * int(approval_pct / 5) + "░" * (20 - int(approval_pct / 5))
            else:
                bar = "█" * int(approval_pct / 5) + "░" * (20 - int(approval_pct / 5))

            print(
                f"{topic[:50]:<50} {approval_pct:>6.1f}% {bar:<8} "
                f"{data['total_posts']:>4} {data['approved']:>10} {data['denied']:>10} {status:<15}"
            )

        print("-" * 100)
        print()


class AirtableTopicSync:
    """Sync topic performance data with Airtable for persistence and dashboard visibility."""

    def __init__(self):
        """Initialize with Airtable credentials."""
        env_file = "/Users/musacomma/Agentic Workflow/.env"
        self.env = self._load_env(env_file)

        self.api_key = self.env.get('AIRTABLE_API_KEY')
        self.base_id = self.env.get('AIRTABLE_BASE_ID')
        self.table_name = 'Topic Performance'
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

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

    def ensure_table_exists(self) -> str:
        """Check if Topic Performance table exists, create if not. Returns table ID."""
        url = f"https://api.airtable.com/v0/meta/bases/{self.base_id}/tables"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            tables = response.json().get('tables', [])
            for table in tables:
                if table['name'] == self.table_name:
                    return table['id']

        # Table doesn't exist - would need to create it via API
        # For now, return None and handle in sync methods
        return None

    def sync_topic_performance(self, analyzer: TopicPerformanceAnalyzer) -> bool:
        """Sync topic performance data to Airtable."""
        table_id = self.ensure_table_exists()

        if not table_id:
            print("⚠️  Topic Performance table not found in Airtable")
            print("    Manual setup required: Create a 'Topic Performance' table with fields:")
            print("    - Topic Name (text)")
            print("    - Total Posts (number)")
            print("    - Approved Posts (number)")
            print("    - Denied Posts (number)")
            print("    - Approval Rate (percent)")
            print("    - Deprecated (checkbox)")
            print("    - Last Updated (date)")
            return False

        # Sync each topic
        url = f"https://api.airtable.com/v0/{self.base_id}/{table_id}"

        for topic, stats in analyzer.data['topics'].items():
            payload = {
                "fields": {
                    "Topic Name": topic,
                    "Total Posts": stats['total_posts'],
                    "Approved Posts": stats['approved_posts'],
                    "Denied Posts": stats['denied_posts'],
                    "Approval Rate": round(stats['approval_rate'] * 100, 1),
                    "Deprecated": stats.get('deprecated', False),
                    "Last Updated": datetime.now().isoformat()
                }
            }

            # Try to update existing record or create new one
            # This would need proper lookup logic in production
            response = requests.post(url, headers=self.headers, json={"records": [{"fields": payload['fields']}]})

        return True


def integrate_with_post_generator(analyzer: TopicPerformanceAnalyzer, all_topics: List[str]) -> str:
    """
    Select a topic for post generation using weighted randomization.
    Called when generating new LinkedIn posts.
    """
    # Initialize all topics in analyzer if not already done
    for topic in all_topics:
        if topic not in analyzer.data['topics']:
            analyzer.initialize_topic(topic)

    # Select topic using weighted randomization
    try:
        selected_topic = analyzer.select_weighted_topic()
        return selected_topic
    except ValueError as e:
        print(f"❌ Error selecting topic: {e}")
        return None


# Example usage and testing
if __name__ == "__main__":
    # Initialize analyzer
    analyzer = TopicPerformanceAnalyzer()

    # List of all 73 topics
    all_topics = [
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

    # Initialize all topics
    for topic in all_topics:
        analyzer.initialize_topic(topic)

    # Simulate some approvals/denials for testing
    test_results = {
        "Prompt Engineering Fundamentals": [True, True, True, True],  # 100% approval
        "Dynamic Pricing Automation": [False, False, False],  # 0% approval (will deprecate)
        "Personalized Outreach at Scale": [True, True, False],  # 67% approval
        "AI-Powered Meeting Summarization": [True, False, True, False],  # 50% approval
    }

    print("Recording test results...")
    for topic, results in test_results.items():
        for result in results:
            analyzer.record_post_result(topic, result)

    # Show performance report
    analyzer.print_performance_report()

    # Test weighted selection
    print("\n📝 Testing weighted topic selection...")
    print("Selecting 10 random topics (should favor high-approval topics):\n")
    selection_counts = {}
    for i in range(10):
        topic = analyzer.select_weighted_topic()
        selection_counts[topic] = selection_counts.get(topic, 0) + 1
        approval_rate = analyzer.data['topics'][topic]['approval_rate'] * 100
        print(f"{i+1}. {topic} ({approval_rate:.1f}% approval)")

    print(f"\nSelection distribution: {selection_counts}")
