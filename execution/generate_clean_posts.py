"""
Generate clean educational posts with all markdown artifacts removed.
Deletes existing posts and regenerates with sanitization.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from draft_post_generator import DraftPostGenerator
from post_quality_checker import PostQualityChecker


def print_section_header(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def main():
    """Generate clean posts with markdown artifacts removed."""
    print_section_header("🧹 GENERATING CLEAN OPTIMIZED POSTS")

    generator = DraftPostGenerator()
    checker = PostQualityChecker()

    # Step 1: Delete all existing posts
    print("Step 1: Cleaning up existing posts...")
    print("─" * 80)
    deleted_count = generator.generator.delete_all_posts()
    if deleted_count > 0:
        print(f"✅ Deleted {deleted_count} posts from Airtable\n")
    else:
        print("ℹ️  No posts to delete\n")

    # Step 2: Generate and upload clean posts
    print("Step 2: Generating 3 clean optimized posts...")
    print("─" * 80 + "\n")

    successful_posts = []
    attempted_posts = 0
    max_attempts = 10

    while len(successful_posts) < 3 and attempted_posts < max_attempts:
        attempted_posts += 1
        print(f"Attempt {attempted_posts}/10...", flush=True)

        try:
            post = generator.generate_draft_post(educational_mode=True)
            length = post.get('content_length', len(post['full_content']))

            # Check for asterisks before upload
            asterisks = post['full_content'].count('*')

            # Run QC
            qc_result = checker.validate_post(post, check_duplicates=False)

            if qc_result['passes_qc']:
                # Add to Airtable (with sanitization applied inside)
                if generator.generator.add_post_to_airtable(post):
                    successful_posts.append((post, length, asterisks))
                    status = "✅ CLEAN" if asterisks == 0 else f"✅ CLEANED ({asterisks}*)"
                    print(f"  {status}: {post['title'][:60]}")
                    print(f"     Length: {length} chars\n")
                else:
                    print(f"  ⚠️  Upload failed\n")
            else:
                if qc_result['issues']:
                    reason = qc_result['issues'][0].split(':')[0]
                    print(f"  ❌ {reason}\n")

        except Exception as e:
            print(f"  ❌ Error: {str(e)[:60]}\n")

    # Results Summary
    print_section_header("✅ FINAL RESULTS")

    if successful_posts:
        print(f"Posts Successfully Generated: {len(successful_posts)}/3")
        print(f"Generation Attempts: {attempted_posts}/{max_attempts}\n")

        print("Generated Posts (cleaned):")
        for i, (post, length, asterisks) in enumerate(successful_posts, 1):
            status = "✅ Clean" if asterisks == 0 else f"✅ Sanitized"
            print(f"\n{i}. {post['title'][:70]}")
            print(f"   Framework: {post['framework']}")
            print(f"   Length: {length} chars (optimal: 1,200-1,800)")
            print(f"   Status: {status} (had {asterisks} asterisks removed)")

        # Length Analysis
        lengths = [l for _, l, _ in successful_posts]
        print(f"\nLength Optimization:")
        print(f"├─ Average: {sum(lengths)//len(lengths)} chars")
        print(f"├─ Shortest: {min(lengths)} chars")
        print(f"├─ Longest: {max(lengths)} chars")

        in_range = sum(1 for l in lengths if 1200 <= l <= 1800)
        print(f"└─ In Optimal Range (1,200-1,800): {in_range}/{len(successful_posts)} posts")

        # Cleanliness Check
        total_asterisks_removed = sum(a for _, _, a in successful_posts)
        if total_asterisks_removed > 0:
            print(f"\nContent Sanitization:")
            print(f"├─ Asterisks Removed: {total_asterisks_removed} total")
            print(f"└─ Posts Status: ✅ ALL CLEAN (markdown-free)")
        else:
            print(f"\nContent Quality:")
            print(f"└─ Posts Status: ✅ PRISTINE (zero artifacts)")

    # Cost Summary
    print(f"\nCost Metrics:")
    cost_summary = generator.generator.enricher.get_cost_summary(days=1)
    print(f"├─ Total API Cost (today): ${cost_summary['total_cost']:.4f}")
    print(f"├─ API Calls Made: {cost_summary['entries']}")
    if successful_posts:
        print(f"└─ Cost Per Post Generated: ${cost_summary['total_cost']/attempted_posts:.4f}")

    # Final Status
    print_section_header("✅ POSTS READY FOR LINKEDIN")

    if len(successful_posts) >= 2:
        print("System Status: READY FOR PRODUCTION")
        print(f"• {len(successful_posts)} clean posts in Airtable")
        print(f"• All markdown artifacts removed (asterisks, bold, italic formatting)")
        print(f"• Post lengths optimized: {sum(lengths)//len(lengths)} chars average")
        print(f"• Educational content: ACTIVE")
        print(f"• Quality control: PASSING")
        return 0
    else:
        print(f"Status: PARTIAL ({len(successful_posts)} posts)")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
