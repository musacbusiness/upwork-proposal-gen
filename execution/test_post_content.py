"""
Check actual post content to debug CTA issue.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from draft_post_generator import DraftPostGenerator

print("Generating 1 post to check content...", flush=True)

generator = DraftPostGenerator()
post = generator.generate_draft_post(educational_mode=True)

print(f"\n=== POST DETAILS ===")
print(f"Title: {post['title']}")
print(f"Framework: {post['framework']}")
print(f"Educational Mode: {post['educational_mode']}")
print(f"Content Length: {post.get('content_length', len(post['full_content']))} chars")
print(f"\n=== FULL CONTENT (first 1000 chars) ===")
print(post['full_content'][:1000])
print(f"\n... [truncated] ...\n")
print(f"\n=== FULL CONTENT (last 500 chars) ===")
print(post['full_content'][-500:])
print(f"\n=== CTA FIELD ===")
print(post['cta'])
print(f"\n=== FULL CONTENT LENGTH ===")
print(f"{len(post['full_content'])} characters")
