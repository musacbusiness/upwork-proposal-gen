"""
Phase 2 Demo: Generate Educational Posts Across Multiple Frameworks

Generates 3 educational posts with diverse topics and frameworks,
demonstrating the full educational content system in action.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from draft_post_generator import DraftPostGenerator
from post_quality_checker import PostQualityChecker


def print_post_section(title: str, content: str, char: str = "="):
    """Print a formatted section."""
    print(f"\n{char * 80}")
    print(f"  {title}")
    print(f"{char * 80}\n")
    print(content)


def main():
    """Generate and validate 3 educational posts."""
    print("\n" + "="*80)
    print("🎓 PHASE 2 DEMO: Educational Post Generation System")
    print("="*80)

    generator = DraftPostGenerator()
    checker = PostQualityChecker()

    # Define diverse topics for educational content
    topics = [
        "How to Implement Chain-of-Thought Prompting for Better AI Results",
        "Building Your First Business Automation in 30 Minutes",
        "Prompt Engineering for Consistent Brand Voice"
    ]

    print(f"\nGenerating {len(topics)} educational posts with diverse frameworks...")
    print(f"Topics: {', '.join([t[:50] + '...' for t in topics])}\n")

    successful_posts = []
    failed_posts = []

    for i, topic in enumerate(topics, 1):
        print(f"\n{'─'*80}")
        print(f"📝 Generating Post {i}/{len(topics)}: {topic[:60]}...")
        print(f"{'─'*80}\n")

        try:
            # Generate educational post
            post = generator.generate_draft_post(topic=topic, educational_mode=True)

            print(f"✅ Post generated successfully")
            print(f"   Title: {post['title']}")
            print(f"   Framework: {post['framework']}")
            print(f"   Content Length: {len(post['full_content'])} characters")

            # Validate with QC
            print(f"\n   Running Quality Check...")
            qc_result = checker.validate_post(post, check_duplicates=False)

            if qc_result['passes_qc']:
                print(f"   ✅ QC PASSED\n")
                successful_posts.append((post, qc_result))

                # Show post preview
                preview_lines = post['full_content'].split('\n')[:5]
                print(f"   Content Preview:")
                for line in preview_lines:
                    if line.strip():
                        print(f"   {line[:75]}...")

            else:
                print(f"   ❌ QC FAILED")
                failed_posts.append((post, qc_result))
                if qc_result['issues']:
                    print(f"   Issues found:")
                    for issue in qc_result['issues'][:2]:
                        print(f"   • {issue[:70]}")

        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            failed_posts.append((None, None))

    # Summary
    print(f"\n{'='*80}")
    print(f"📊 PHASE 2 DEMO SUMMARY")
    print(f"{'='*80}\n")

    print(f"Posts Generated: {len(successful_posts) + len(failed_posts)}/{len(topics)}")
    print(f"✅ QC Passed: {len(successful_posts)}")
    print(f"❌ QC Failed: {len(failed_posts)}")
    print(f"Success Rate: {(len(successful_posts)/len(topics))*100:.0f}%")

    # Show full content of first successful post
    if successful_posts:
        post, qc_result = successful_posts[0]
        print_post_section(
            f"EXAMPLE: {post['title'][:70]}",
            post['full_content'],
            char="▔"
        )

        print("\n📋 Quality Check Results:")
        print(f"   Topic Relevance: {'✅ PASSED' if qc_result['details'].get('topic_relevance', {}).get('passed') else '❌ FAILED'}")
        print(f"   Content Length: {'✅ PASSED' if qc_result['details'].get('content_length', {}).get('passed') else '❌ FAILED'}")
        print(f"   Placeholders: {'✅ PASSED' if qc_result['details'].get('placeholders', {}).get('passed') else '❌ FAILED'}")
        print(f"   Framework Labels: {'✅ PASSED' if qc_result['details'].get('framework_labels', {}).get('passed') else '❌ FAILED'}")
        print(f"   Hook Completeness: {'✅ PASSED' if qc_result['details'].get('hook_completeness', {}).get('passed') else '⚠️  WARNING'}")
        print(f"   CTA Presence: {'✅ PASSED' if qc_result['details'].get('cta_presence', {}).get('passed') else '❌ FAILED'}")

    # Cost summary
    print(f"\n💰 API Cost Summary:")
    cost_summary = generator.generator.enricher.get_cost_summary(days=1)
    print(f"   Total Cost (today): ${cost_summary['total_cost']:.4f}")
    print(f"   API Calls Made: {cost_summary['entries']}")
    if cost_summary['entries'] > 0:
        print(f"   Average Cost Per Post: ${cost_summary['total_cost']/len(topics):.4f}")

    print(f"\n{'='*80}\n")

    return 0 if len(successful_posts) >= 2 else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
