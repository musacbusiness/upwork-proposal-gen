# Image URL Handling in LinkedIn Post System

## Overview
This document explains how image URLs are populated and maintained across the LinkedIn post automation system.

## Image URL Population Points

### 1. During Post Creation
When a new post is created via `optimized_post_generator.py` or `generate_educational_posts.py`:

- **If image_url exists in post dict:**
  - Populates `Image URL` field in Airtable (string field with direct URL)
  - Populates `Image` field in Airtable (attachment field format: `[{"url": "..."}]`)
  
- **If image_url is None/missing:**
  - `Image URL` field remains empty
  - Post is created with just visual type info for later image generation

**Code Location:** 
- `optimized_post_generator.py:888-892` → `add_post_to_airtable()`
- `generate_educational_posts.py:104-108` → `upload_to_airtable()`

### 2. During Image Regeneration/Updates
When an image is regenerated for an existing post:

- **Method:** `update_post_image(record_id, image_url, image_prompt=None)`
- **Updates both fields:**
  - `Image URL` → New image URL
  - `Image` → Attachment field with new URL
  - `Image Prompt` → Optional updated prompt (if provided)

**Code Location:**
- `optimized_post_generator.py:917-953` → `update_post_image()`
- `generate_educational_posts.py:125-161` → `update_post_image()`

## Airtable Field Structure

### Image URL Field
- **Type:** Single line text
- **Purpose:** Direct link to the generated image
- **Format:** `https://replicate.com/...` (from Replicate API)
- **Usage:** Can be used in Make.com webhooks, email sends, etc.

### Image Field (Attachment)
- **Type:** Attachments (native Airtable field)
- **Purpose:** Embedded image in Airtable UI
- **Format:** Array of attachment objects: `[{"url": "https://..."}]`
- **Usage:** Displays image thumbnail in Airtable

### Image Prompt Field
- **Type:** Long text
- **Purpose:** Description of what the image shows (for regeneration/revision)
- **Format:** Text describing visual type and dimensions
- **Example:** `"Visual Type: Modern business dashboard | Dimensions: 1024x1024"`

## Image Generation Workflow

```
Post Generation
    ↓
[Check if image_url provided]
    ├─ YES → add_post_to_airtable() with image URL
    └─ NO  → add_post_to_airtable() without image URL
    ↓
[Later: Image generation service runs]
    ↓
[New image URL available]
    ↓
update_post_image(record_id, image_url)
    ↓
[Airtable record updated with image URL]
```

## How to Use Image URL Methods

### Adding a post with image URL:
```python
post = {
    'title': 'My Post',
    'full_content': '...',
    'visual_type': 'Modern business dashboard',
    'visual_spec': {...},
    'image_url': 'https://replicate.com/...',  # Include if image exists
    # ... other fields
}
generator.add_post_to_airtable(post)
```

### Updating image for existing record:
```python
# After generating a new image
record_id = 'recXXXXXXXX'
new_image_url = 'https://replicate.com/...'
new_prompt = 'Visual Type: Modern dashboard | Dimensions: 1024x1024'

generator.update_post_image(record_id, new_image_url, new_prompt)
```

## Integration with Image Generation Services

When Replicate or other image generation services create images:

1. **Get image URL** from service response
2. **Call `update_post_image()`** with the URL
3. **Airtable automatically updates** both Image URL and Image fields
4. **Image is now visible** in Airtable UI and available for Make.com webhooks

## Cost Optimization

- Image URL storage is **included** in every post creation (no extra API cost)
- Image URL updates via PATCH are **single operation** (no batch overhead)
- Both text and attachment fields updated **in one PATCH call** (efficient)

## Error Handling

- If image URL is empty/None → Fields are **skipped** (not set to empty string)
- If update fails → **Error logged** with response code
- If post creation fails → **Entire record not created** (no partial uploads)

## Future Integration Points

When image generation is added:
1. Generate image via Replicate API
2. Get image URL from API response
3. Call `update_post_image(record_id, image_url)`
4. Image automatically appears in Airtable
5. Ready for Make.com webhook posting

This ensures images are properly stored and available throughout the entire LinkedIn posting workflow.
