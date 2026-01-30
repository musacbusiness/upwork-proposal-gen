"""
Generate automation showcase posts featuring real business automations.

Creates engaging posts that show business owners:
- How specific automations work operationally
- What problems they solve
- Workflow improvements and time savings
- Real examples of automation in action
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from draft_post_generator import DraftPostGenerator
from post_quality_checker import PostQualityChecker


# Featured automations to showcase
FEATURED_AUTOMATIONS = [
    ("Proposal Generation Automation", "Sales Process Automation"),
    ("Client Onboarding Automation", "Client Management Automation"),
    ("Automated Invoice and Payment Processing", "Financial Automation"),
    ("Email Automation and Lead Nurturing Sequences", "Marketing Automation"),
    ("Task Assignment and Workflow Distribution", "Operations Automation"),
    ("Automated Meeting Scheduling and Follow-ups", "Calendar and Communication Automation"),
    ("Document Generation and Templating", "Admin Automation"),
    ("Client Reporting Automation", "Reporting and Analytics Automation"),
]


def print_section_header(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def main():
    """Generate automation showcase posts."""
    print_section_header("🤖 GENERATING AUTOMATION SHOWCASE POSTS")

    generator = DraftPostGenerator()
    checker = PostQualityChecker()

    successful_posts = []
    attempted = 0
    max_attempts = 20

    print(f"Generating {len(FEATURED_AUTOMATIONS)} automation showcase posts...")
    print(f"Featured automations: {', '.join([a[0] for a in FEATURED_AUTOMATIONS[:3]])}...\n")

    for automation_name, context in FEATURED_AUTOMATIONS:
        if len(successful_posts) >= len(FEATURED_AUTOMATIONS):
            break

        print(f"Generating post for: {automation_name}")
        print(f"  Context: {context}")

        attempt_count = 0
        while attempt_count < 3:  # 3 attempts per automation
            attempted += 1
            attempt_count += 1

            try:
                # Generate automation showcase post
                post = generator.generate_draft_post(
                    topic=context,
                    automation_showcase_mode=True,
                    automation_name=automation_name
                )

                length = post.get('content_length', len(post['full_content']))
                in_range = 1200 <= length <= 1800

                print(f"    Attempt {attempt_count}: Generated {length} chars", end="")

                # Check if within optimal range
                if not in_range:
                    print(f" (out of range)")
                    continue

                print(f" (in range)")

                # Run QC
                qc_result = checker.validate_post(post, check_duplicates=False)

                if qc_result['passes_qc']:
                    # Add to Airtable
                    if generator.generator.add_post_to_airtable(post):
                        successful_posts.append((post, automation_name, length))
                        print(f"    ✅ UPLOADED to Airtable\n")
                        break
                    else:
                        print(f"    ⚠️  Upload failed\n")
                else:
                    if qc_result['issues']:
                        reason = qc_result['issues'][0].split(':')[0]
                        print(f"    ❌ QC Failed: {reason}")

            except Exception as e:
                print(f"    ❌ Error: {str(e)[:60]}")

    # Results Summary
    print_section_header("📊 AUTOMATION SHOWCASE GENERATION COMPLETE")

    print(f"Posts Successfully Generated: {len(successful_posts)}/{len(FEATURED_AUTOMATIONS)}")
    print(f"Total Attempts: {attempted}/{max_attempts}\n")

    if successful_posts:
        print("Generated Automation Posts:")
        for i, (post, automation, length) in enumerate(successful_posts, 1):
            print(f"\n{i}. {automation}")
            print(f"   Title: {post['title'][:70]}")
            print(f"   Length: {length} chars")
            print(f"   Framework: {post['framework']}")

        # Length analysis
        lengths = [l for _, _, l in successful_posts]
        print(f"\n\nLength Optimization:")
        print(f"├─ Average: {sum(lengths)//len(lengths)} chars")
        print(f"├─ Shortest: {min(lengths)} chars")
        print(f"├─ Longest: {max(lengths)} chars")

        in_range_count = sum(1 for l in lengths if 1200 <= l <= 1800)
        print(f"└─ In Optimal Range (1,200-1,800): {in_range_count}/{len(successful_posts)} posts")

    # Cost summary
    print(f"\n\nCost Metrics:")
    cost_summary = generator.generator.enricher.get_cost_summary(days=1)
    print(f"├─ Total API Cost (today): ${cost_summary['total_cost']:.4f}")
    print(f"├─ API Calls Made: {cost_summary['entries']}")
    if successful_posts:
        print(f"└─ Cost Per Post Generated: ${cost_summary['total_cost']/attempted:.4f}")

    # Final status
    print_section_header("✅ AUTOMATION SHOWCASE SYSTEM ACTIVE")

    if len(successful_posts) >= 5:
        print("System Status: READY FOR PRODUCTION")
        print(f"• {len(successful_posts)} automation showcase posts uploaded")
        print(f"• Real operational benefits highlighted")
        print(f"• Business owner-focused messaging")
        print(f"• Clean, markdown-free content")
        return 0
    else:
        print(f"Status: IN PROGRESS ({len(successful_posts)} posts generated)")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
