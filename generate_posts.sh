#!/bin/bash
# Generate daily LinkedIn posts with authentic voice

echo "🚀 Triggering cloud content generation..."
echo ""

python3 << PYTHON
import modal
import json

# Access the deployed Modal app
try:
    generate_daily_content_fn = modal.Function.from_name("linkedin-automation", "generate_daily_content")
    print("✅ Connected to Modal app")
    print()
    print("📝 Generating posts...")
    result = generate_daily_content_fn.remote()
    print()
    if result:
        print("✅ Posts generated successfully!")
    else:
        print("⚠️  Generation completed with errors")
    print()
except Exception as e:
    print(f"❌ Error: {e}")

PYTHON

echo ""
echo "Check your Airtable for new posts!"
