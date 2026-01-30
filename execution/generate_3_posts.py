"""
Quick script to generate 3 posts with a specific topic and add to Airtable.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from draft_post_generator import DraftPostGenerator

def main():
    """Generate 3 posts with prompting techniques topic."""
    print("="*80)
    print("🚀 GENERATING 3 POSTS - PROMPTING TECHNIQUES FOR BUSINESS OWNERS")
    print("="*80 + "\n")

    generator = DraftPostGenerator()
    topic = "Prompting Techniques for Business Owners to Get More Out of AI"

    added_count = 0
    failed_count = 0

    for i in range(3):
        print(f"\n📝 Post {i+1}/3")
        print("-" * 80)

        # Generate post
        post = generator.generate_draft_post(topic=topic)

        # Add to Airtable with QC
        success, qc_result = generator.add_post_to_airtable(post)

        if success:
            added_count += 1
            print(f"✅ Successfully added: {post['title'][:70]}...")
            print(f"   Framework: {post['framework']}")
            print(f"   Hook Type: {post['hook_type']}")
            print(f"   CTA Type: {post['cta_type']}")
        else:
            failed_count += 1
            print(f"❌ Failed to add post")
            if qc_result and qc_result.get('issues'):
                print(f"   Issues:")
                for issue in qc_result['issues']:
                    print(f"   • {issue[:70]}...")

    print(f"\n{'='*80}")
    print(f"✅ GENERATION COMPLETE")
    print(f"   Successfully added: {added_count}/3 posts")
    print(f"   Failed: {failed_count}/3 posts")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
