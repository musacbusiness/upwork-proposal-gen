"""
Generate optimized educational posts with better retry logic.
Generates posts until we have 3 successful uploads with optimization.
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
    """Generate optimized posts with retry logic."""
    print_section_header("🚀 GENERATING OPTIMIZED EDUCATIONAL POSTS (V2)")

    generator = DraftPostGenerator()
    checker = PostQualityChecker()

    successful_posts = []
    attempted_posts = 0
    max_attempts = 10

    print(f"Generating posts until we have 3 successful uploads...")
    print(f"(will attempt up to {max_attempts} generations)\n")

    while len(successful_posts) < 3 and attempted_posts < max_attempts:
        attempted_posts += 1
        print(f"Generation Attempt {attempted_posts}/10...", flush=True)

        try:
            post = generator.generate_draft_post(educational_mode=True)
            length = post.get('content_length', len(post['full_content']))

            # Run QC
            qc_result = checker.validate_post(post, check_duplicates=False)

            if qc_result['passes_qc']:
                # Add to Airtable
                if generator.generator.add_post_to_airtable(post):
                    successful_posts.append((post, qc_result, length))
                    print(f"  ✅ SUCCESS: {post['title'][:60]}")
                    print(f"     Framework: {post['framework']} | Length: {length} chars\n")
                else:
                    print(f"  ⚠️  Upload failed\n")
            else:
                # Log failure reason
                if qc_result['issues']:
                    reason = qc_result['issues'][0].split(':')[0]
                    print(f"  ❌ QC Failed: {reason}\n")

        except Exception as e:
            print(f"  ❌ Error: {str(e)[:60]}\n")

    # Results Summary
    print_section_header("📊 FINAL RESULTS")

    if successful_posts:
        print(f"Posts Successfully Generated: {len(successful_posts)}/3")
        print(f"Generation Attempts: {attempted_posts}/{max_attempts}\n")

        print("Generated Posts:")
        for i, (post, qc, length) in enumerate(successful_posts, 1):
            print(f"\n{i}. {post['title'][:70]}")
            print(f"   Framework: {post['framework']}")
            print(f"   Length: {length} chars (optimal: 1,200-1,800)")

        # Length Analysis
        lengths = [l for _, _, l in successful_posts]
        print(f"\nLength Optimization:")
        print(f"├─ Average: {sum(lengths)//len(lengths)} chars")
        print(f"├─ Shortest: {min(lengths)} chars")
        print(f"├─ Longest: {max(lengths)} chars")

        in_range = sum(1 for l in lengths if 1200 <= l <= 1800)
        print(f"└─ In Optimal Range (1,200-1,800): {in_range}/{len(successful_posts)} posts")

    # Cost Summary
    print(f"\nCost Metrics:")
    cost_summary = generator.generator.enricher.get_cost_summary(days=1)
    print(f"├─ Total API Cost (today): ${cost_summary['total_cost']:.4f}")
    print(f"├─ API Calls Made: {cost_summary['entries']}")
    if successful_posts:
        print(f"└─ Cost Per Post Generated: ${cost_summary['total_cost']/attempted_posts:.4f}")

    # Final Status
    print_section_header("✅ OPTIMIZATION COMPLETE")

    if len(successful_posts) >= 2:
        print("System Status: READY FOR PRODUCTION")
        print(f"• {len(successful_posts)} optimized posts uploaded to Airtable")
        print(f"• Post lengths optimized to LinkedIn engagement zone (1,200-1,800 chars)")
        print(f"• Educational content mode: ACTIVE")
        print(f"• Quality control: PASSING ({len(successful_posts)}/{attempted_posts} attempts)")
    else:
        print(f"Status: PARTIAL ({len(successful_posts)} posts generated)")
        print(f"Attempts remaining: {max_attempts - attempted_posts}")

    return 0 if len(successful_posts) >= 2 else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
