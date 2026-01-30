"""
Simple test to debug post generation with optimizations.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from draft_post_generator import DraftPostGenerator
from post_quality_checker import PostQualityChecker

print("Starting test...", flush=True)

try:
    print("1. Initializing generators...", flush=True)
    generator = DraftPostGenerator()
    checker = PostQualityChecker()

    print("2. Deleting old posts...", flush=True)
    deleted = generator.generator.delete_all_posts()
    print(f"   Deleted {deleted} posts", flush=True)

    print("3. Generating 1 test post...", flush=True)
    post = generator.generate_draft_post(educational_mode=True)
    print(f"   ✅ Generated: {post['title'][:60]}", flush=True)
    print(f"   Length: {post.get('content_length', len(post['full_content']))} chars", flush=True)

    print("4. Running QC...", flush=True)
    qc_result = checker.validate_post(post, check_duplicates=False)
    status = "✅ PASSED" if qc_result['passes_qc'] else "❌ FAILED"
    print(f"   {status}", flush=True)

    if not qc_result['passes_qc']:
        print(f"   Issues:")
        for issue in qc_result['issues']:
            print(f"   - {issue[:70]}", flush=True)

    print("5. Adding to Airtable...", flush=True)
    if qc_result['passes_qc']:
        if generator.generator.add_post_to_airtable(post):
            print("   ✅ Added successfully", flush=True)
        else:
            print("   ❌ Upload failed", flush=True)

    print("\n✅ TEST COMPLETE", flush=True)

except Exception as e:
    print(f"❌ ERROR: {str(e)}", flush=True)
    import traceback
    traceback.print_exc()
