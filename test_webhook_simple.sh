#!/bin/bash

WEBHOOK_URL="https://hook.us2.make.com/yvmn4bog8f8opam42w1ckabush6nz0mt"

echo "=== Testing Make.com Webhook ==="
echo "URL: $WEBHOOK_URL"
echo ""

# Test 1: Simple GET request to check if webhook exists
echo "Test 1: GET request to webhook URL"
curl -i -X GET "$WEBHOOK_URL" 2>&1 | head -20
echo ""
echo ""

# Test 2: POST with minimal JSON
echo "Test 2: POST with minimal JSON payload"
curl -i -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}' 2>&1 | head -30
echo ""
echo ""

# Test 3: POST with exact sample structure
echo "Test 3: POST with full sample payload"
curl -i -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "record_id": "recTEST123abc",
    "content": "Test post",
    "image_url": "https://example.com/image.jpg",
    "base_id": "appw88uD6ZM0ckF8f",
    "table_id": "tbljg75KMQWDo2Hgu",
    "scheduled_deletion_date": "2025-12-31T00:00:00.000Z"
  }' 2>&1 | head -30
echo ""
echo ""

# Test 4: Check DNS resolution
echo "Test 4: DNS resolution for hook.us2.make.com"
nslookup hook.us2.make.com 2>&1 | head -20
echo ""
echo ""

# Test 5: Check if we can reach the domain at all
echo "Test 5: Check connectivity to Make.com domain"
curl -i -X HEAD "https://hook.us2.make.com/" 2>&1 | head -20

