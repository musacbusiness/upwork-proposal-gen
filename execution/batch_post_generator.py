"""
Batch post generator - Creates multiple posts for automated scheduling.
Generates posts and adds them to Airtable with scheduled times starting tomorrow.
"""

import os
import sys
import random
from pathlib import Path
from datetime import datetime, timedelta
import requests

# Add execution directory to path
sys.path.insert(0, str(Path(__file__).parent))
from optimized_post_generator import OptimizedPostGenerator

def generate_batch_posts(num_posts: int = 21, start_tomorrow: bool = True):
    """Generate and schedule a batch of posts."""

    print("="*80)
    print(f"🚀 BATCH POST GENERATION - {num_posts} POSTS")
    print("="*80 + "\n")

    generator = OptimizedPostGenerator()

    # All 73 topics
    topics = [
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

    generated_posts = []

    # Generate posts
    print(f"📝 Generating {num_posts} posts...\n")

    for i in range(num_posts):
        topic = random.choice(topics)
        post = generator.generate_complete_post(topic)
        generated_posts.append(post)

        # Calculate scheduled time if requested
        if start_tomorrow:
            tomorrow = datetime.now() + timedelta(days=1)
            # Spread across 30 days starting tomorrow
            days_offset = random.randint(0, 29)
            scheduled_time = (tomorrow + timedelta(days=days_offset)).replace(hour=9, minute=0)
            post['scheduled_time'] = scheduled_time.isoformat()
            post['status'] = 'Pending Review'  # Set to Pending Review when scheduling

        print(f"  {i+1}/{num_posts} ✓ {post['title'][:60]}...")

    print(f"\n✅ Generated {num_posts} posts\n")

    # Add to Airtable
    print("="*80)
    print(f"📤 ADDING POSTS TO AIRTABLE")
    print("="*80 + "\n")

    added_count = 0
    for i, post in enumerate(generated_posts, 1):
        if generator.add_post_to_airtable(post):
            added_count += 1
            scheduled_date = ""
            if post.get('scheduled_time'):
                scheduled_obj = datetime.fromisoformat(post['scheduled_time'])
                scheduled_date = f" | Scheduled: {scheduled_obj.strftime('%b %d, %Y @ 9 AM')}"
            print(f"  {i}/{num_posts} Added: {post['title'][:50]}...{scheduled_date}")
        else:
            print(f"  {i}/{num_posts} ❌ Failed: {post['title'][:50]}...")

    print("\n" + "="*80)
    print(f"✅ BATCH COMPLETE")
    print("="*80)
    print(f"\nSuccessfully added {added_count}/{num_posts} posts to Airtable")

    if start_tomorrow:
        print("\nScheduling Details:")
        print(f"  • Status: Pending Review (ready to post)")
        print(f"  • Start Date: Tomorrow at 9:00 AM")
        print(f"  • Spread: Next 30 days")
        print(f"  • Posting: Automatic via Make.com webhook")
    else:
        print("\nScheduling Details:")
        print(f"  • Status: Draft (awaiting review)")
        print(f"  • Next Step: Review posts and change status to 'Pending Review'")
        print(f"  • Then run: python3 execution/schedule_pending_posts.py")

    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate batch of LinkedIn posts")
    parser.add_argument("--count", type=int, default=21, help="Number of posts to generate (default: 21)")
    parser.add_argument("--draft", action="store_true", help="Create as Draft (no scheduling)")

    args = parser.parse_args()

    generate_batch_posts(num_posts=args.count, start_tomorrow=not args.draft)
