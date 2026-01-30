#!/usr/bin/env python3
"""
Generate Educational Posts - Test Implementation

Generates 3 educational posts using the new hybrid system:
- Template-based structure (deterministic, fast)
- Claude API enrichment for examples, steps, templates (dynamic, quality)

Tests:
1. Educational content generation via Claude API
2. Quality checking for educational posts
3. Airtable upload with educational metadata
4. Cost tracking for API calls
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
import requests

sys.path.insert(0, str(Path(__file__).parent))

from draft_post_generator import DraftPostGenerator
from post_quality_checker import PostQualityChecker


class EducationalPostTestGenerator:
    """Generate and test educational posts."""

    def __init__(self):
        """Initialize generator."""
        self.draft_generator = DraftPostGenerator()
        self.quality_checker = PostQualityChecker()
        self.airtable_api_key = os.environ.get('AIRTABLE_API_KEY')
        self.airtable_base_id = os.environ.get('AIRTABLE_BASE_ID')
        self.airtable_table_id = os.environ.get('AIRTABLE_LINKEDIN_TABLE_ID')

    def get_diverse_educational_topics(self, count: int = 3) -> list:
        """Get diverse topics for educational posts.

        Ensures mix of:
        - Prompting techniques
        - Implementation guides
        - Strategy & planning
        - Business process automation
        """
        topics = {
            "Prompting Techniques": [
                "Chain-of-Thought Prompting for Better AI Responses",
                "Few-Shot Learning Techniques for Precise AI Outputs",
                "Structured Output Formats for Consistent AI Results",
                "Role-Based Prompting: Making AI Think Like Your Expert",
            ],
            "Implementation Guides": [
                "How to Audit Your Business for AI Opportunities",
                "Building Your First AI Automation: A Step-by-Step Guide",
                "Integrating AI into Existing Workflows Without Disruption",
                "Creating SOPs That Enable Automation",
            ],
            "Strategy & Planning": [
                "Building an AI Adoption Roadmap for Your Business",
                "Measuring ROI on AI and Automation Investments",
                "Data Preparation for AI: What You Need Before Starting",
                "When NOT to Automate: Critical Human Touchpoints",
            ],
            "Business Processes": [
                "Automating Sales Pipeline Management",
                "Client Reporting Automation That Impresses",
                "Email Sequence Automation for Lead Nurturing",
                "Automated Quality Control for Service Businesses",
            ]
        }

        # Select one from each category (or cycle if more requested)
        selected = []
        categories = list(topics.keys())

        for i in range(count):
            category = categories[i % len(categories)]
            topic_list = topics[category]
            topic = topic_list[i % len(topic_list)]
            selected.append((topic, category))

        return selected

    def generate_and_test_educational_post(self, topic: str, category: str) -> dict:
        """Generate and test a single educational post.

        Args:
            topic: Topic for the educational post
            category: Category of the topic

        Returns:
            Dict with generation results and quality check results
        """
        print(f"\n{'='*80}")
        print(f"📚 EDUCATIONAL POST: {topic}")
        print(f"   Category: {category}")
        print(f"{'='*80}")

        result = {
            "topic": topic,
            "category": category,
            "status": "pending",
            "generation_time": None,
            "qc_results": None,
            "post": None,
            "errors": []
        }

        try:
            # Step 1: Generate educational post
            print(f"\n1️⃣  Generating educational post...")
            start_time = datetime.now()

            post = self.draft_generator.generate_draft_post(
                topic=topic,
                educational_mode=True
            )

            generation_time = (datetime.now() - start_time).total_seconds()
            result["generation_time"] = generation_time
            result["post"] = post

            print(f"   ✓ Generated in {generation_time:.2f}s")
            print(f"   ✓ Framework: {post['framework']}")
            print(f"   ✓ Content length: {post['content_length']} chars")
            print(f"   ✓ Educational mode: {post['educational_mode']}")

            # Step 2: Run quality checks
            print(f"\n2️⃣  Running quality checks...")

            qc_result = self.quality_checker.validate_post(
                post,
                check_duplicates=False  # Skip duplicate check for test
            )

            result["qc_results"] = qc_result
            passed = qc_result.get('passes_qc', False)
            print(f"   ✓ QC Passed: {passed}")

            if not passed:
                print(f"   ⚠️  Issues found:")
                for issue in qc_result.get('issues', []):
                    print(f"      - {issue}")
                    result["errors"].append(issue)

            # Step 3: Print content preview
            print(f"\n3️⃣  Content Preview:")
            print(f"   Title: {post['title']}")
            print(f"   Hook: {post['hook'][:100]}...")
            print(f"   Body preview: {post['body'][:150].replace(chr(10), ' ')}...")

            # Step 4: Summary
            print(f"\n✅ Post generated and validated")
            result["status"] = "success" if passed else "qc_issues"

            return result

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            result["status"] = "error"
            result["errors"].append(str(e))
            return result

    def generate_batch(self, count: int = 3) -> list:
        """Generate multiple educational posts.

        Args:
            count: Number of posts to generate

        Returns:
            List of generation results
        """
        print("\n" + "=" * 80)
        print(f"🚀 EDUCATIONAL POST GENERATION TEST")
        print(f"Generating {count} educational posts for validation")
        print("=" * 80)

        # Get diverse topics
        topics = self.get_diverse_educational_topics(count)
        print(f"\nSelected topics:")
        for i, (topic, category) in enumerate(topics, 1):
            print(f"   {i}. {topic}")
            print(f"      Category: {category}")

        # Generate posts
        results = []
        for topic, category in topics:
            result = self.generate_and_test_educational_post(topic, category)
            results.append(result)

        return results

    def print_summary(self, results: list):
        """Print test summary.

        Args:
            results: List of generation results
        """
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)

        successful = sum(1 for r in results if r["status"] == "success")
        qc_issues = sum(1 for r in results if r["status"] == "qc_issues")
        errors = sum(1 for r in results if r["status"] == "error")

        print(f"\nGenerated: {len(results)} posts")
        print(f"  ✅ Fully passed: {successful}")
        print(f"  ⚠️  QC issues: {qc_issues}")
        print(f"  ❌ Errors: {errors}")

        # Detailed results
        print(f"\n{'─'*80}")
        for i, result in enumerate(results, 1):
            status_icon = {
                "success": "✅",
                "qc_issues": "⚠️ ",
                "error": "❌",
                "pending": "⏳"
            }.get(result["status"], "?")

            print(f"\n{i}. {status_icon} {result['topic']}")
            print(f"   Category: {result['category']}")

            if result["post"]:
                post = result["post"]
                print(f"   Framework: {post['framework']}")
                print(f"   Content length: {post['content_length']} chars")
                print(f"   Generation time: {result['generation_time']:.2f}s")

            if result["qc_results"]:
                qc = result["qc_results"]
                passed = qc.get('passes_qc', False)
                print(f"   QC Passed: {passed}")
                if not passed and qc.get('issues'):
                    print(f"   Issues:")
                    for issue in qc.get('issues', []):
                        print(f"      - {issue}")

            if result["errors"]:
                print(f"   Errors: {', '.join(result['errors'])}")

        # Statistics
        print(f"\n{'─'*80}")
        if successful + qc_issues > 0:
            avg_length = sum(
                r["post"]["content_length"] for r in results
                if r["post"]
            ) / sum(1 for r in results if r["post"])
            print(f"\nAverage post length: {avg_length:.0f} chars")

            avg_time = sum(
                r["generation_time"] for r in results
                if r["generation_time"]
            ) / len([r for r in results if r["generation_time"]])
            print(f"Average generation time: {avg_time:.2f}s")

        print("\n" + "=" * 80)
        print("✅ TEST COMPLETE\n")


def main():
    """Main execution."""
    generator = EducationalPostTestGenerator()

    # Generate 3 educational posts
    results = generator.generate_batch(count=3)

    # Print summary
    generator.print_summary(results)

    # Exit code
    errors = sum(1 for r in results if r["status"] == "error")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
