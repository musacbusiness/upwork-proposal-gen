#!/usr/bin/env python3
"""
Simple webhook server for handling Airtable automation webhooks.
Receives status change events from Airtable and spawns Modal functions.

Run: python webhook_server.py
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import sys
import logging
import modal

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the Modal app
sys.path.insert(0, '/Users/musacomma/Agentic Workflow/cloud')
from modal_linkedin_automation import (
    generate_images_for_post,
    schedule_approved_post,
    handle_rejected_post
)


class WebhookHandler(BaseHTTPRequestHandler):
    """Handle incoming Airtable webhook requests"""

    def do_POST(self):
        """Handle POST requests from Airtable"""
        try:
            # Parse request
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            payload = json.loads(body)

            logger.info(f"Webhook received: {payload}")

            record_id = payload.get('record_id')
            status = payload.get('status')
            base_id = payload.get('base_id', os.environ.get('AIRTABLE_BASE_ID'))
            table_id = payload.get('table_id', os.environ.get('AIRTABLE_LINKEDIN_TABLE_ID'))

            logger.info(f"Status change: {record_id} → {status}")

            if status == "Pending Review":
                logger.info("Triggering image generation...")
                generate_images_for_post.spawn(record_id, base_id, table_id)
                response = {"success": True, "action": "image_generation_triggered"}

            elif status == "Approved - Ready to Schedule":
                logger.info("Triggering post scheduling...")
                schedule_approved_post.spawn(record_id, base_id, table_id)
                response = {"success": True, "action": "scheduling_triggered"}

            elif status == "Rejected":
                logger.info("Handling rejected post...")
                handle_rejected_post.spawn(record_id, base_id, table_id)
                response = {"success": True, "action": "rejection_handled"}

            else:
                logger.warning(f"Unknown status: {status}")
                response = {"success": False, "error": f"Unknown status: {status}"}
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
                return

            # Send success response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            logger.info(f"Response sent: {response}")

        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {"success": False, "error": str(e)}
            self.wfile.write(json.dumps(response).encode())

    def do_GET(self):
        """Handle health check requests"""
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {
                "status": "healthy",
                "service": "linkedin-automation-webhook",
                "timestamp": __import__('datetime').datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {"error": "Not found"}
            self.wfile.write(json.dumps(response).encode())

    def log_message(self, format, *args):
        """Suppress default logging"""
        logger.info(format % args)


def main():
    """Start the webhook server"""
    host = '127.0.0.1'
    port = 8000

    server = HTTPServer((host, port), WebhookHandler)
    logger.info(f"Webhook server starting on http://{host}:{port}")
    logger.info(f"Health check: http://{host}:{port}/health")
    logger.info("Waiting for Airtable webhooks...")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down webhook server...")
        server.shutdown()


if __name__ == '__main__':
    main()
