"""
Test sanitization function.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from optimized_post_generator import OptimizedPostGenerator

generator = OptimizedPostGenerator()

# Test content with asterisks
test_content = """Here's a sample post.

**Real examples:**
- This is bold
- *And this is italic*

That's all folks!"""

print("Original content:")
print(test_content)
print(f"\nAsterisks count: {test_content.count('*')}")

clean = generator._sanitize_content(test_content)

print("\n" + "="*50)
print("Sanitized content:")
print(clean)
print(f"\nAsterisks count: {clean.count('*')}")
print(f"\n✅ Sanitization works!" if clean.count('*') == 0 else "❌ Still has asterisks")
