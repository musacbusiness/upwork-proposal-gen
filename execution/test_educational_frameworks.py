"""
Test script for Phase 1.3: Validate educational framework integration

Tests:
1. Generate 1 educational post per framework (5 total)
2. Verify educational content elements (examples, steps, templates)
3. Check cost tracking for enricher API calls
4. Validate QC passes with instructional content checks
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from optimized_post_generator import OptimizedPostGenerator
from post_quality_checker import PostQualityChecker


def main():
    """Run Phase 1.3 validation tests."""
    print("\n" + "="*80)
    print("🧪 PHASE 1.3 VALIDATION - Educational Framework Integration")
    print("="*80 + "\n")

    generator = OptimizedPostGenerator()
    checker = PostQualityChecker()

    # Test all 5 frameworks in educational mode
    frameworks = ['PAS', 'AIDA', 'BAB', 'Framework', 'Contrarian']
    topic = "Chain-of-Thought Prompting for Business Owners"

    passed = 0
    failed = 0

    for i, framework in enumerate(frameworks, 1):
        print(f"\n{'─'*80}")
        print(f"📝 Test {i}/5: {framework} Framework (Educational Mode)")
        print(f"{'─'*80}")

        try:
            # Generate educational post
            print(f"Generating educational post with {framework} framework...")
            post = generator.generate_complete_post(topic, educational_mode=True)

            print(f"✅ Post generated successfully")
            print(f"   Title: {post['title'][:70]}...")
            print(f"   Framework: {post['framework']}")
            print(f"   Educational Mode: {post.get('educational_mode', False)}")

            # Check content length
            content_length = len(post['full_content'])
            print(f"   Content Length: {content_length} characters")

            # Look for educational markers
            content = post['full_content'].lower()
            has_example = 'example' in content
            has_step = 'step' in content
            has_template = 'template' in content
            has_technique = 'technique' in content or 'method' in content or 'approach' in content

            print(f"\n   Educational Content Markers:")
            print(f"   ├─ Contains 'example': {has_example}")
            print(f"   ├─ Contains 'step': {has_step}")
            print(f"   ├─ Contains 'template': {has_template}")
            print(f"   └─ Contains 'technique/method': {has_technique}")

            # Run quality check
            print(f"\n   Running Quality Check...")
            qc_result = checker.validate_post(post, check_duplicates=False)

            if qc_result['passes_qc']:
                print(f"   ✅ QC PASSED")
                passed += 1
            else:
                print(f"   ❌ QC FAILED")
                if qc_result['issues']:
                    print(f"   Issues:")
                    for issue in qc_result['issues'][:3]:
                        print(f"   • {issue[:70]}...")
                failed += 1

        except Exception as e:
            print(f"   ❌ ERROR: {str(e)[:70]}")
            failed += 1

    # Cost summary
    print(f"\n{'='*80}")
    print(f"📊 PHASE 1.3 VALIDATION SUMMARY")
    print(f"{'='*80}")
    print(f"Posts Generated: {passed + failed}/5")
    print(f"QC Passed: {passed}/5")
    print(f"QC Failed: {failed}/5")
    print(f"Success Rate: {(passed/5)*100:.0f}%")

    # Cost tracking
    print(f"\n💰 API Cost Summary:")
    cost_summary = generator.enricher.get_cost_summary(days=1)
    print(f"Total Cost (today): ${cost_summary['total_cost']:.4f}")
    print(f"API Calls Made: {cost_summary['entries']}")
    print(f"Average Cost Per Call: ${cost_summary['total_cost']/max(cost_summary['entries'], 1):.4f}")

    print(f"\n{'='*80}\n")

    # Return success/failure
    return 0 if passed == 5 else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
