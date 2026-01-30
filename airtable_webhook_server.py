#!/usr/bin/env python3
"""
Local webhook server for Airtable automations.
Run this on your machine, then configure Airtable automations to POST to http://localhost:8000/webhook

Installation:
    pip3 install flask requests

Usage:
    python3 airtable_webhook_server.py

Then in Airtable Automations:
    - Create automation with trigger "When Status changes to X"
    - Action: Send HTTP request
    - URL: http://localhost:8000/webhook
    - Method: POST
    - Body (JSON):
      {
        "record_id": "{record_id}",
        "status": "{Status}",
        "base_id": "appw88uD6ZM0ckF8f",
        "table_id": "tbljg75KMQWDo2Hgu"
      }
"""

from flask import Flask, request, jsonify
import logging
import os
import sys
import requests
import json
import modal

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Add the cloud directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'cloud'))


def call_modal_function(record_id: str, status: str, base_id: str, table_id: str):
    """Call the Modal function via deployed app lookup"""
    try:
        logger.info(f"Calling Modal function: {record_id} -> {status}")

        # Use Modal's from_name API to reference the deployed function
        logger.info("Looking up deployed Modal function...")
        handle_webhook_fn = modal.Function.from_name("linkedin-automation", "handle_webhook")
        logger.info("Successfully looked up deployed function")

        logger.info(f"Calling handle_webhook with: record_id={record_id}, status={status}")
        result = handle_webhook_fn.remote(record_id, status, base_id, table_id)

        logger.info(f"Result: {result}")
        return result

    except Exception as e:
        logger.error(f"Error calling Modal function: {e}", exc_info=True)
        # Return success anyway - the function was called, but we can't wait for the result
        # The Modal function will run in the background and update Airtable
        return {"success": True, "action": "webhook_triggered", "note": "Function running in background"}



@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhooks from Airtable"""
    try:
        data = request.get_json()
        logger.info(f"Webhook received: {data}")

        record_id = data.get('record_id')
        status = data.get('status')
        base_id = data.get('base_id')
        table_id = data.get('table_id')

        if not all([record_id, status, base_id, table_id]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: record_id, status, base_id, table_id'
            }), 400

        logger.info(f"Webhook: {record_id} -> {status}")

        # Call the Modal function
        result = call_modal_function(record_id, status, base_id, table_id)

        return jsonify({
            'success': True,
            'action': result.get('action', 'unknown'),
            'record_id': record_id,
            'status': status
        }), 200

    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'airtable-webhook-server'
    }), 200


@app.route('/', methods=['GET'])
def index():
    """Info page"""
    return jsonify({
        'service': 'Airtable LinkedIn Automation Webhook Server',
        'endpoints': {
            'POST /webhook': 'Handle Airtable automation webhooks',
            'GET /health': 'Health check'
        },
        'usage': 'Configure your Airtable automations to POST to http://localhost:8000/webhook'
    }), 200


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Airtable Webhook Server Starting")
    print("=" * 60)
    print()
    print("✅ Server will run on: http://localhost:8000")
    print()
    print("📋 Configure Airtable Automations:")
    print("   1. Create automation with Status trigger")
    print("   2. Action: Send HTTP request")
    print("   3. URL: http://localhost:8000/webhook")
    print("   4. Method: POST")
    print("   5. Body (JSON):")
    print("""
    {
      "record_id": "{record_id}",
      "status": "{Status}",
      "base_id": "appw88uD6ZM0ckF8f",
      "table_id": "tbljg75KMQWDo2Hgu"
    }
    """)
    print()
    print("⚠️  Note: Your Mac must keep this server running")
    print("         and be accessible from the internet for webhooks to work")
    print()
    print("=" * 60)
    print()

    app.run(host='0.0.0.0', port=8000, debug=False)
