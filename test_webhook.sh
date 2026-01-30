#!/bin/bash

# Test Make.com Webhook
# This script sends a sample payload to your Make.com webhook
# so it can establish the data structure for all 4 modules

WEBHOOK_URL="https://hook.us2.make.com/yvmn4bog8f8opam42w1ckabush6nz0mt"
PAYLOAD_FILE="test_webhook_payload.json"

echo "=================================================="
echo "Testing Make.com Webhook"
echo "=================================================="
echo ""
echo "Webhook URL: $WEBHOOK_URL"
echo "Payload File: $PAYLOAD_FILE"
echo ""

# Send the test payload
echo "Sending test payload..."
echo ""

curl -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d @"$PAYLOAD_FILE" \
  -v

echo ""
echo ""
echo "=================================================="
echo "Test Complete"
echo "=================================================="
echo ""
echo "✅ If successful, Make.com webhook should have received the payload"
echo "✅ Check Make.com scenario: View execution history"
echo "✅ All 4 modules should now understand the data structure"
echo ""
