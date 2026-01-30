#!/usr/bin/env python3
"""
Generate Educational Posts - Production Script

CLI for generating diverse LinkedIn posts with instructional and narrative content.

Usage:
    python3 generate_educational_posts.py               # Generate 3 educational posts
    python3 generate_educational_posts.py 6 --mixed     # Generate 3 narrative + 3 educational
    python3 generate_educational_posts.py 5             # Generate 5 posts (diverse frameworks)
    python3 generate_educational_posts.py 5 --upload    # Generate and upload to Airtable
    python3 generate_educational_posts.py --list-topics # List all 62 available topics
    python3 generate_educational_posts.py --topic "..." # Generate with specific topic

Features:
    - Framework diversity (PAS, AIDA, BAB, Framework, Contrarian)
    - Hook variety (curiosity, data, contrarian, before/after, etc.)
    - Mixed narrative and educational modes
    - Automatic quality checking
    - Optional Airtable upload
"""

import os
import sys
import argparse
import json
import random
from pathlib import Path
from datetime import datetime
import requests

sys.path.insert(0, str(Path(__file__).parent))

from draft_post_generator import DraftPostGenerator
from post_quality_checker import PostQualityChecker


class EducationalPostGenerator:
    """Generate educational posts with quality checking and optional Airtable upload."""

    def __init__(self):
        """Initialize generator."""
        self.draft_generator = DraftPostGenerator()
        self.quality_checker = PostQualityChecker()
        self.airtable_api_key = os.environ.get('AIRTABLE_API_KEY')
        self.airtable_base_id = os.environ.get('AIRTABLE_BASE_ID')
        self.airtable_table_id = os.environ.get('AIRTABLE_LINKEDIN_TABLE_ID')
        self.headers = {
            "Authorization": f"Bearer {self.airtable_api_key}",
            "Content-Type": "application/json"
        }

    def generate_post(self, topic: str = None, educational_mode: bool = True) -> dict:
        """Generate a single post.

        Args:
            topic: Optional specific topic. If None, random selection.
            educational_mode: If True, generate instructional content. If False, narrative content.

        Returns:
            Generated post dict with metadata
        """
        post = self.draft_generator.generate_draft_post(
            topic=topic,
            educational_mode=educational_mode
        )
        return post

    def validate_post(self, post: dict) -> dict:
        """Validate post quality.

        Args:
            post: Post to validate

        Returns:
            Validation result
        """
        return self.quality_checker.validate_post(post, check_duplicates=False)

    def upload_to_airtable(self, post: dict) -> bool:
        """Upload post to Airtable.

        Args:
            post: Post to upload

        Returns:
            True if successful, False otherwise
        """
        url = f"https://api.airtable.com/v0/{self.airtable_base_id}/{self.airtable_table_id}"

        # Build fields
        # Get the Airtable-compatible framework name (maps internal names to dropdown values)
        framework_airtable = post.get('framework_airtable', post.get('framework', 'Unknown'))

        fields = {
            "Title": post['title'],
            "Post Content": post['full_content'],
            "Status": "Draft",
            "Writing Framework": framework_airtable,  # Maps to Airtable dropdown
            "Image Prompt": f"Visual: {post['visual_type']}",
            "Notes": f"Framework: {post['framework']}\nHook Type: {post['hook_type']}\nEducational Mode: True"
        }

        # Add image URL if available
        if post.get('image_url'):
            fields["Image URL"] = post['image_url']
            # Also add to Image attachment field (Airtable format)
            fields["Image"] = [{"url": post['image_url']}]

        payload = {"records": [{"fields": fields}]}

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            if response.status_code == 200:
                record_id = response.json()['records'][0]['id']
                print(f"   ✅ Uploaded: {record_id}")
                return True
            else:
                print(f"   ❌ Upload failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Error uploading: {e}")
            return False

    def update_post_image(self, record_id: str, image_url: str, image_prompt: str = None) -> bool:
        """Update image URL for existing Airtable record.

        This is used when a new image is generated for an existing post.

        Args:
            record_id: Airtable record ID
            image_url: URL of generated image
            image_prompt: Optional updated image prompt

        Returns:
            True if successful, False otherwise
        """
        url = f"https://api.airtable.com/v0/{self.airtable_base_id}/{self.airtable_table_id}/{record_id}"

        fields = {
            "Image URL": image_url,
            "Image": [{"url": image_url}]
        }

        # Update image prompt if provided
        if image_prompt:
            fields["Image Prompt"] = image_prompt

        payload = {"fields": fields}

        try:
            response = requests.patch(url, headers=self.headers, json=payload)
            if response.status_code == 200:
                print(f"   ✅ Image updated: {record_id}")
                return True
            else:
                print(f"   ❌ Update failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Error updating: {e}")
            return False

    def print_post(self, post: dict, validation: dict = None, number: int = None):
        """Print post in readable format.

        Args:
            post: Post to print
            validation: Optional validation result
            number: Optional post number for numbering
        """
        prefix = f"[{number}] " if number else ""
        print(f"\n{prefix}📝 {post['title']}")
        print(f"{'─'*80}")
        print(f"Topic: {post['post_topic']}")
        print(f"Framework: {post['framework']} | Visual: {post['visual_type']}")
        print(f"Length: {post['content_length']} chars | Educational: {post['educational_mode']}")

        if validation:
            status = "✅ PASSED" if validation.get('passes_qc') else "⚠️  ISSUES"
            print(f"QC Status: {status}")
            if validation.get('issues'):
                for issue in validation['issues']:
                    print(f"  • {issue}")

        print(f"\n{post['full_content']}")
        print(f"\n{'═'*80}")

    def generate_batch(self, count: int = 3, topic: str = None, upload: bool = False, verbose: bool = True, mixed: bool = False):
        """Generate multiple posts with diversity.

        Args:
            count: Number of posts to generate
            topic: Optional specific topic for all posts
            upload: Whether to upload to Airtable
            verbose: Whether to print detailed output
            mixed: If True, generate mix of narrative (50%) and educational (50%)

        Returns:
            List of (post, validation) tuples
        """
        results = []
        frameworks = ['PAS', 'AIDA', 'BAB', 'Framework', 'Contrarian']

        mode_label = "MIXED (Narrative + Educational)" if mixed else "EDUCATIONAL"

        if verbose:
            print(f"\n{'='*80}")
            print(f"🚀 GENERATING {count} {mode_label} POSTS")
            print(f"{'='*80}\n")

        for i in range(count):
            if verbose:
                print(f"Generating post {i+1}/{count}...")

            # Determine mode (alternate if mixed: even=educational, odd=narrative)
            if mixed:
                educational_mode = i % 2 == 0
            else:
                educational_mode = True  # All educational if not mixed

            # Randomize framework selection for diversity (shuffle the frameworks list)
            selected_framework = random.choice(frameworks)

            # Force the framework selection by generating until we get it
            max_attempts = 5
            attempts = 0
            post = None

            while attempts < max_attempts and (post is None or post['framework'] != selected_framework):
                post = self.generate_post(topic=topic, educational_mode=educational_mode)

                # If we got a different framework, regenerate
                if post['framework'] != selected_framework and attempts < max_attempts - 1:
                    attempts += 1
                else:
                    break

            # Validate
            validation = self.validate_post(post)

            # Upload if requested
            upload_success = False
            if upload:
                print(f"   Uploading post {i+1}/{count}...")
                upload_success = self.upload_to_airtable(post)

            # Print summary with mode and framework
            if verbose:
                status = "✅" if validation.get('passes_qc') else "⚠️ "
                mode_str = "📚 Educational" if educational_mode else "📖 Narrative"
                print(f"   {status} [{mode_str}] {post['title'][:50]}...")
                print(f"      Length: {post['content_length']} chars | Framework: {post['framework']} | Hook: {post['hook_type']}")

            results.append({
                "post": post,
                "validation": validation,
                "uploaded": upload_success,
                "mode": "educational" if educational_mode else "narrative"
            })

        if verbose:
            print(f"\n{'='*80}")
            print(f"✅ GENERATION COMPLETE")
            print(f"   Generated: {len(results)} posts")

            # Count by mode
            educational_count = sum(1 for r in results if r.get('mode') == 'educational')
            narrative_count = sum(1 for r in results if r.get('mode') == 'narrative')
            if mixed:
                print(f"   Narrative: {narrative_count} | Educational: {educational_count}")

            # Count by framework
            frameworks_used = {}
            for r in results:
                fw = r['post']['framework']
                frameworks_used[fw] = frameworks_used.get(fw, 0) + 1
            print(f"   Frameworks: {', '.join([f'{k}({v})' for k, v in sorted(frameworks_used.items())])}")

            # QC pass rate
            passed = sum(1 for r in results if r['validation'].get('passes_qc'))
            print(f"   QC Passed: {passed}/{len(results)}")

            if upload:
                uploaded = sum(1 for r in results if r['uploaded'])
                print(f"   Uploaded: {uploaded}/{len(results)}")
            print(f"{'='*80}\n")

        return results


def main():
    """Main CLI."""
    parser = argparse.ArgumentParser(
        description="Generate diverse LinkedIn posts with educational and narrative content",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate 3 educational posts (diverse frameworks)
  python3 generate_educational_posts.py

  # Generate 6 posts (3 narrative + 3 educational, diverse frameworks)
  python3 generate_educational_posts.py 6 --mixed

  # Generate 5 educational posts with diverse frameworks
  python3 generate_educational_posts.py 5

  # Generate and upload to Airtable
  python3 generate_educational_posts.py 5 --upload

  # Generate with specific topic
  python3 generate_educational_posts.py 3 --topic "Chain-of-Thought Prompting"

  # List all 62 available topics
  python3 generate_educational_posts.py --list-topics

Features:
  - Framework diversity: Each post uses different framework (PAS, AIDA, BAB, etc.)
  - Hook variety: Different hooks, titles, and approaches per post
  - Mixed modes: --mixed flag creates 50/50 narrative and educational split
  - Quality checking: Automatic validation with detailed feedback
  - Airtable: Optional direct upload to your LinkedIn posts table
        """
    )

    parser.add_argument(
        'count',
        nargs='?',
        type=int,
        default=3,
        help='Number of posts to generate (default: 3)'
    )
    parser.add_argument(
        '--topic',
        type=str,
        default=None,
        help='Specific topic for all posts (default: random selection)'
    )
    parser.add_argument(
        '--upload',
        action='store_true',
        help='Upload posts to Airtable'
    )
    parser.add_argument(
        '--list-topics',
        action='store_true',
        help='List all available topics'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Minimal output'
    )
    parser.add_argument(
        '--mixed',
        action='store_true',
        help='Generate mix of narrative (50%) and educational (50%) posts'
    )

    args = parser.parse_args()

    # Handle --list-topics
    if args.list_topics:
        generator = EducationalPostGenerator()
        print("\n📚 AVAILABLE TOPICS:")
        print(f"{'─'*80}\n")
        for i, topic in enumerate(generator.draft_generator.topics, 1):
            print(f"{i:2d}. {topic}")
        print(f"\nTotal: {len(generator.draft_generator.topics)} topics\n")
        return 0

    # Generate posts
    generator = EducationalPostGenerator()
    results = generator.generate_batch(
        count=args.count,
        topic=args.topic,
        upload=args.upload,
        verbose=not args.quiet,
        mixed=args.mixed
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
