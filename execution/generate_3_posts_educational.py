"""
Generate 3 posts and add to Airtable using the educational content system
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from draft_post_generator import DraftPostGenerator


def main():
    """Generate and add 3 posts to Airtable."""
    print("\n" + "="*80)
    print("🚀 GENERATING 3 EDUCATIONAL POSTS")
    print("="*80 + "\n")

    generator = DraftPostGenerator()

    # Select 3 diverse topics from the expanded list
    topics = [
        "How to Audit Your Business for AI Opportunities",
        "Prompt Engineering for Consistent Brand Voice",
        "Building an AI Adoption Roadmap for Your Business"
    ]

    added_count = 0
    failed_count = 0

    for i, topic in enumerate(topics, 1):
        print(f"\n{'─'*80}")
        print(f"📝 Post {i}/3: {topic}")
        print(f"{'─'*80}\n")

        try:
            # Generate educational post
            post = generator.generate_draft_post(topic=topic, educational_mode=True)

            print(f"  ✅ Generated:")
            print(f"     Title: {post['title']}")
            print(f"     Framework: {post['framework']}")
            print(f"     Length: {len(post['full_content'])} characters")

            # Add to Airtable with QC
            success, qc_result = generator.add_post_to_airtable(post)

            if success:
                print(f"  ✅ Successfully added to Airtable")
                added_count += 1
            else:
                print(f"  ❌ Failed to add to Airtable")
                if qc_result and qc_result.get('issues'):
                    print(f"     QC Issues:")
                    for issue in qc_result['issues'][:2]:
                        print(f"     • {issue[:70]}")
                failed_count += 1

        except Exception as e:
            print(f"  ❌ Error: {str(e)[:100]}")
            failed_count += 1

    # Summary
    print(f"\n{'='*80}")
    print(f"📊 GENERATION SUMMARY")
    print(f"{'='*80}\n")
    print(f"✅ Successfully added: {added_count}/3 posts")
    print(f"❌ Failed: {failed_count}/3 posts")
    print(f"Success rate: {(added_count/3)*100:.0f}%")

    # Cost summary
    print(f"\n💰 API Cost Summary:")
    cost_summary = generator.generator.enricher.get_cost_summary(days=1)
    print(f"Total API cost (today): ${cost_summary['total_cost']:.4f}")
    print(f"API calls made: {cost_summary['entries']}")
    if added_count > 0:
        print(f"Average cost per post: ${cost_summary['total_cost']/added_count:.4f}")

    print(f"\n{'='*80}\n")

    return 0 if added_count >= 2 else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
