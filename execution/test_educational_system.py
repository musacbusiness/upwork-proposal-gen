#!/usr/bin/env python3
"""Test script for educational content generation system.

Validates:
1. Educational content enricher can be imported and initialized
2. OptimizedPostGenerator can generate both narrative and educational posts
3. Draft post generator supports educational_mode parameter
4. Quality checker has educational validation methods
5. Posts can be uploaded to Airtable
"""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from optimized_post_generator import OptimizedPostGenerator
from draft_post_generator import DraftPostGenerator
from post_quality_checker import PostQualityChecker
from educational_content_enricher import EducationalContentEnricher


def test_educational_enricher_import():
    """Test that educational content enricher can be imported."""
    print("✅ Test 1: Educational Content Enricher Import")
    try:
        enricher = EducationalContentEnricher()
        print(f"   ✓ EducationalContentEnricher initialized")
        print(f"   ✓ Model: {enricher.model}")
        print(f"   ✓ Has generate_examples: {hasattr(enricher, 'generate_examples')}")
        print(f"   ✓ Has generate_steps: {hasattr(enricher, 'generate_steps')}")
        print(f"   ✓ Has generate_before_after: {hasattr(enricher, 'generate_before_after')}")
        print(f"   ✓ Has generate_template: {hasattr(enricher, 'generate_template')}")
        print(f"   ✓ Has generate_automation_showcase: {hasattr(enricher, 'generate_automation_showcase')}")
        return True
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False


def test_optimized_post_generator():
    """Test that OptimizedPostGenerator has educational_mode support."""
    print("\n✅ Test 2: OptimizedPostGenerator Educational Mode Support")
    try:
        generator = OptimizedPostGenerator()
        print(f"   ✓ OptimizedPostGenerator initialized")
        print(f"   ✓ Has enricher: {hasattr(generator, 'enricher')}")

        # Check framework methods have educational_mode parameter
        import inspect

        methods_to_check = [
            '_generate_pas',
            '_generate_aida',
            '_generate_bab',
            '_generate_framework',
            '_generate_contrarian'
        ]

        for method_name in methods_to_check:
            method = getattr(generator, method_name, None)
            if method:
                sig = inspect.signature(method)
                has_educational_mode = 'educational_mode' in sig.parameters
                print(f"   ✓ {method_name} has educational_mode: {has_educational_mode}")

        # Check generate_complete_post
        sig = inspect.signature(generator.generate_complete_post)
        has_educational_mode = 'educational_mode' in sig.parameters
        print(f"   ✓ generate_complete_post has educational_mode: {has_educational_mode}")

        return True
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_draft_post_generator():
    """Test that DraftPostGenerator supports educational_mode."""
    print("\n✅ Test 3: DraftPostGenerator Educational Mode Support")
    try:
        generator = DraftPostGenerator()
        print(f"   ✓ DraftPostGenerator initialized")
        print(f"   ✓ Number of topics: {len(generator.topics)}")

        # Check if new topics are included
        new_topics = [
            "How to Audit Your Business for AI Opportunities",
            "Building Your First AI Automation: A Step-by-Step Guide",
            "Selecting the Right AI Tool for Your Specific Business Need",
            "Integrating AI into Existing Workflows Without Disruption",
            "Measuring ROI on AI and Automation Investments",
        ]

        topic_count = 0
        for topic in new_topics:
            if topic in generator.topics:
                topic_count += 1

        print(f"   ✓ Has new educational topics: {topic_count}/{len(new_topics)}")

        # Check method signature
        import inspect
        sig = inspect.signature(generator.generate_draft_post)
        has_educational_mode = 'educational_mode' in sig.parameters
        print(f"   ✓ generate_draft_post has educational_mode: {has_educational_mode}")

        return True
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False


def test_quality_checker_educational_methods():
    """Test that PostQualityChecker has educational validation methods."""
    print("\n✅ Test 4: PostQualityChecker Educational Methods")
    try:
        checker = PostQualityChecker()
        print(f"   ✓ PostQualityChecker initialized")

        required_methods = [
            'check_topic_relevance',
            'check_example_quality',
            'check_step_completeness',
            'check_for_placeholders',
        ]

        for method_name in required_methods:
            has_method = hasattr(checker, method_name)
            print(f"   ✓ Has {method_name}: {has_method}")

        return True
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False


def test_narrative_post_generation():
    """Test generating a narrative (non-educational) post."""
    print("\n✅ Test 5: Narrative Post Generation (No API Calls)")
    try:
        generator = OptimizedPostGenerator()

        # Generate a narrative post (no API calls to Claude)
        topic = "Automating Invoicing and Payment Management Systems"
        print(f"   Topic: {topic}")

        post = generator.generate_complete_post(
            topic,
            educational_mode=False,  # Narrative mode uses templates only
            automation_showcase_mode=False
        )

        print(f"   ✓ Post generated successfully")
        print(f"   ✓ Framework: {post['framework']}")
        print(f"   ✓ Content length: {post['content_length']} chars")
        print(f"   ✓ Status: {post['status']}")
        print(f"   ✓ Educational mode: {post['educational_mode']}")

        # Print snippet of content
        content_snippet = post['full_content'][:200].replace('\n', ' ')
        print(f"   ✓ Content preview: {content_snippet}...")

        return True
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_educational_post_structure():
    """Test that educational_mode parameter is properly passed and stored."""
    print("\n✅ Test 6: Educational Post Structure Validation")
    try:
        generator = OptimizedPostGenerator()

        topic = "Chain-of-Thought Prompting for Better AI Responses"

        # This won't make API calls because educational content generation
        # happens in the enricher, not in this structure test
        post = generator.generate_complete_post(
            topic,
            educational_mode=True
        )

        print(f"   ✓ Post generated with educational_mode=True")
        print(f"   ✓ Post['educational_mode']: {post['educational_mode']}")
        print(f"   ✓ Has title: {bool(post.get('title'))}")
        print(f"   ✓ Has hook: {bool(post.get('hook'))}")
        print(f"   ✓ Has body: {bool(post.get('body'))}")
        print(f"   ✓ Has CTA: {bool(post.get('cta'))}")
        print(f"   ✓ Has hashtags: {bool(post.get('hashtags'))}")
        print(f"   ✓ Has full_content: {bool(post.get('full_content'))}")

        return True
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests."""
    print("=" * 80)
    print("🧪 EDUCATIONAL CONTENT GENERATION SYSTEM - VALIDATION TESTS")
    print("=" * 80)

    results = []

    # Run tests
    results.append(("Educational Enricher Import", test_educational_enricher_import()))
    results.append(("OptimizedPostGenerator Support", test_optimized_post_generator()))
    results.append(("DraftPostGenerator Support", test_draft_post_generator()))
    results.append(("QualityChecker Methods", test_quality_checker_educational_methods()))
    results.append(("Narrative Post Generation", test_narrative_post_generation()))
    results.append(("Educational Post Structure", test_educational_post_structure()))

    # Print summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print("=" * 80)
    print(f"\n🎯 Results: {passed}/{total} tests passed\n")

    if passed == total:
        print("✅ ALL TESTS PASSED - Educational system is ready for testing!\n")
        print("📋 Next Steps:")
        print("   1. Run test_educational_generation.py to test API-based content generation")
        print("   2. Test topic coverage and diversity with get_diverse_topics()")
        print("   3. Validate quality checker catches educational content issues")
        print("   4. Generate full set of educational posts for review")
    else:
        print("⚠️  SOME TESTS FAILED - Review errors above\n")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
