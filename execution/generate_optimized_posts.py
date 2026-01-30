"""
Generate optimized educational posts with LinkedIn length constraints.

This script:
1. Deletes all existing posts from Airtable
2. Generates 3 new educational posts with optimized length (1,200-1,800 chars)
3. Validates posts with QC before uploading
4. Tracks cost and metrics
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


def print_post_details(post: dict, qc_result: dict = None):
    """Print detailed post information."""
    print(f"  📝 Title: {post['title'][:70]}")
    print(f"  📋 Framework: {post['framework']}")
    print(f"  🎓 Educational: {post.get('educational_mode', False)}")
    print(f"  📏 Length: {post.get('content_length', len(post['full_content']))} chars (optimal: 1,200-1,800)")

    if qc_result:
        status = "✅ PASSED" if qc_result['passes_qc'] else "❌ FAILED"
        print(f"  🔍 QC Status: {status}")
        if not qc_result['passes_qc'] and qc_result['issues']:
            for issue in qc_result['issues'][:2]:
                print(f"     • {issue[:70]}")


def main():
    """Run the optimized post generation."""
    print_section_header("🚀 GENERATING OPTIMIZED EDUCATIONAL POSTS")

    generator = DraftPostGenerator()
    checker = PostQualityChecker()

    # Step 1: Delete existing posts
    print("Step 1: Cleaning up existing posts...")
    print("─" * 80)
    deleted_count = generator.generator.delete_all_posts()
    if deleted_count > 0:
        print(f"✅ Deleted {deleted_count} existing posts\n")
    else:
        print("ℹ️  No posts to delete\n")

    # Step 2: Generate new posts
    print("Step 2: Generating 3 new optimized educational posts...")
    print("─" * 80 + "\n")

    successful_posts = []
    failed_posts = []

    # Generate 3 posts
    for i in range(3):
        print(f"Generating Post {i+1}/3...")

        try:
            # Generate educational post
            post = generator.generate_draft_post(educational_mode=True)

            # Validate with QC
            qc_result = checker.validate_post(post, check_duplicates=False)

            # Print post details
            print_post_details(post, qc_result)

            if qc_result['passes_qc']:
                print(f"  ✅ QC PASSED - Adding to Airtable\n")

                # Add to Airtable
                if generator.generator.add_post_to_airtable(post):
                    successful_posts.append((post, qc_result))
                else:
                    print(f"  ❌ Failed to upload to Airtable\n")
                    failed_posts.append((post, qc_result))
            else:
                print(f"  ❌ QC FAILED - Not uploading\n")
                failed_posts.append((post, qc_result))

        except Exception as e:
            print(f"  ❌ ERROR: {str(e)}\n")
            failed_posts.append((None, None))

    # Step 3: Summary Report
    print_section_header("📊 OPTIMIZATION RESULTS")

    print(f"Generation Summary:")
    print(f"├─ Total Posts Generated: 3")
    print(f"├─ ✅ QC Passed: {len(successful_posts)}")
    print(f"├─ ❌ QC Failed: {len(failed_posts)}")
    print(f"└─ Success Rate: {(len(successful_posts)/3)*100:.0f}%")

    # Length statistics
    if successful_posts:
        lengths = [p[0]['content_length'] for p in successful_posts]
        print(f"\nLength Optimization:")
        print(f"├─ Avg Length: {sum(lengths)//len(lengths)} chars")
        print(f"├─ Min Length: {min(lengths)} chars")
        print(f"├─ Max Length: {max(lengths)} chars")

        # Check if all are in optimal range
        in_range = sum(1 for l in lengths if 1200 <= l <= 1800)
        print(f"├─ In Optimal Range (1,200-1,800): {in_range}/3 posts")
        print(f"└─ 📏 LinkedIn Optimization: {'✅ PASSED' if in_range == 3 else '⚠️  PARTIAL'}")

    # API Cost
    print(f"\nAPI Cost Summary:")
    cost_summary = generator.generator.enricher.get_cost_summary(days=1)
    print(f"├─ Total Cost (today): ${cost_summary['total_cost']:.4f}")
    print(f"├─ API Calls Made: {cost_summary['entries']}")
    if len(successful_posts) > 0:
        print(f"└─ Cost Per Post: ${cost_summary['total_cost']/len(successful_posts):.4f}")

    # Final status
    print(f"\n{'='*80}")
    if len(successful_posts) >= 2:
        print(f"🎉 OPTIMIZATION COMPLETE - POSTS READY FOR LINKEDIN")
    else:
        print(f"⚠️  OPTIMIZATION PARTIAL - SOME POSTS NEED REVIEW")
    print(f"{'='*80}\n")

    return 0 if len(successful_posts) >= 2 else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
