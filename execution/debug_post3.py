"""
Debug post 3 CTA issue - generate until we get a long post that needs trimming.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from draft_post_generator import DraftPostGenerator
from post_quality_checker import PostQualityChecker

print("Generating posts until we get one that needs trimming...", flush=True)

generator = DraftPostGenerator()
checker = PostQualityChecker()

for attempt in range(1, 6):
    print(f"\nAttempt {attempt}...", flush=True)
    post = generator.generate_draft_post(educational_mode=True)

    length = post.get('content_length', len(post['full_content']))
    print(f"  Length: {length} chars")

    # If it's a trimmed post (between 1500-1800), check it
    if 1500 <= length <= 1800:
        print(f"  Checking QC...", flush=True)
        qc_result = checker.validate_post(post, check_duplicates=False)

        if qc_result['passes_qc']:
            print(f"  ✅ QC PASSED")
        else:
            print(f"  ❌ QC FAILED")
            print(f"  Issues:")
            for issue in qc_result['issues']:
                print(f"    - {issue[:80]}")

            # Print the actual content to debug
            print(f"\n  === LAST 800 CHARS OF CONTENT ===")
            print(post['full_content'][-800:])
            print(f"\n  === CHECKING FOR CTA KEYWORDS ===")
            content_lower = post['full_content'].lower()
            cta_keywords = ['comment', 'share', 'save', 'dm', 'message', 'link in',
                          'reply', 'tag', 'reach out', 'book a', 'schedule a',
                          'grab your', 'download', 'let me know', 'what do you think',
                          'thoughts?', 'questions?', 'agree or disagree']
            for keyword in cta_keywords:
                if keyword in content_lower:
                    print(f"    ✅ Found: '{keyword}'")

            break
