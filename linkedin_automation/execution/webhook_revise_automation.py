#!/usr/bin/env python3
"""
webhook_revise_automation.py - Enhanced webhook with automation endpoint

Adds support for Airtable Automations to trigger revisions via webhook
without requiring button clicks.

Usage:
    python3 webhook_revise_automation.py
"""

from flask import Flask, request, jsonify, Response
import sys
import os
from pathlib import Path
import logging

# Add execution directory to path
sys.path.insert(0, str(Path(__file__).parent))

from content_revisions import ContentRevisionProcessor
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def html_response(success, message):
    """Return an HTML page that shows status and auto-closes"""
    color = "#10B981" if success else "#EF4444"
    icon = "✅" if success else "⚠️"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Revision Status</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }}
            .card {{
                background: white;
                padding: 40px 60px;
                border-radius: 16px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                text-align: center;
                max-width: 400px;
            }}
            .icon {{ font-size: 48px; margin-bottom: 16px; }}
            .title {{ color: {color}; font-size: 24px; font-weight: 600; margin-bottom: 8px; }}
            .message {{ color: #6B7280; font-size: 14px; margin-bottom: 20px; }}
            .close-note {{ color: #9CA3AF; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="icon">{icon}</div>
            <div class="title">{'Revision Complete!' if success else 'No Changes Needed'}</div>
            <div class="message">{message}</div>
            <div class="close-note">You can close this tab and return to Airtable</div>
        </div>
        <script>
            // Auto-close after 3 seconds
            setTimeout(function() {{ window.close(); }}, 3000);
        </script>
    </body>
    </html>
    """
    return Response(html, mimetype='text/html')


@app.route('/revise/<record_id>', methods=['GET', 'POST'])
def revise_record(record_id):
    """
    Trigger revision for a specific Airtable record
    Can be called from button or automation
    """
    try:
        logger.info(f"Received revision request for record: {record_id}")
        
        processor = ContentRevisionProcessor()
        result = processor.check_for_revisions(record_ids=[record_id])
        
        if result:
            return html_response(True, f"Successfully regenerated content for this record. Check Airtable for updates!")
        else:
            return html_response(False, f"No revision prompt found. Add instructions to the 'Revision Prompt' field first.")
            
    except Exception as e:
        logger.error(f"Error processing revision: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'record_id': record_id
        }), 500


@app.route('/revise-all', methods=['GET', 'POST'])
def revise_all():
    """Trigger revision check for all records with Revision Prompt"""
    try:
        logger.info("Received revision request for all records")
        
        processor = ContentRevisionProcessor()
        result = processor.check_for_revisions()
        
        return jsonify({
            'success': True,
            'message': 'Revision check completed for all records',
            'processed': result
        }), 200
            
    except Exception as e:
        logger.error(f"Error processing revisions: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/automation/revise', methods=['POST'])
def automation_revise():
    """
    Endpoint specifically for Airtable Automations
    Expects JSON: {"record_id": "recXXXXXXXXXXXXXX"}
    """
    try:
        data = request.get_json()
        
        if not data or 'record_id' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing record_id in request body'
            }), 400
        
        record_id = data['record_id']
        logger.info(f"Automation triggered revision for record: {record_id}")
        
        processor = ContentRevisionProcessor()
        result = processor.check_for_revisions(record_ids=[record_id])
        
        return jsonify({
            'success': True,
            'message': f'Automation processed revision for {record_id}',
            'record_id': record_id,
            'revised': result > 0
        }), 200
            
    except Exception as e:
        logger.error(f"Error in automation endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'linkedin-automation-server',
        'auto_poster': auto_poster_running,
        'endpoints': {
            'button': '/revise/<record_id>',
            'automation': '/automation/revise',
            'batch': '/revise-all',
            'poster_status': '/poster/status',
            'poster_start': '/poster/start',
            'poster_stop': '/poster/stop'
        }
    }), 200


# ============================================
# Auto-Poster Integration
# ============================================

import threading
from auto_poster_daemon import AutoPosterDaemon

auto_poster_thread = None
auto_poster_running = False
auto_poster_daemon = None


def run_auto_poster():
    """Run the auto-poster in a background thread"""
    global auto_poster_daemon, auto_poster_running
    auto_poster_daemon = AutoPosterDaemon()
    auto_poster_running = True
    
    while auto_poster_running:
        try:
            auto_poster_daemon.process_due_posts()
        except Exception as e:
            logger.error(f"Auto-poster error: {e}")
        
        # Check every 60 seconds
        for _ in range(60):
            if not auto_poster_running:
                break
            import time
            time.sleep(1)
    
    if auto_poster_daemon:
        auto_poster_daemon.cleanup()


@app.route('/poster/status', methods=['GET'])
def poster_status():
    """Check auto-poster status"""
    return jsonify({
        'running': auto_poster_running,
        'message': 'Auto-poster is running' if auto_poster_running else 'Auto-poster is stopped'
    }), 200


@app.route('/poster/start', methods=['POST', 'GET'])
def poster_start():
    """Start the auto-poster"""
    global auto_poster_thread, auto_poster_running
    
    if auto_poster_running:
        return jsonify({
            'success': False,
            'message': 'Auto-poster is already running'
        }), 200
    
    auto_poster_thread = threading.Thread(target=run_auto_poster, daemon=True)
    auto_poster_thread.start()
    
    return jsonify({
        'success': True,
        'message': 'Auto-poster started'
    }), 200


@app.route('/poster/stop', methods=['POST', 'GET'])
def poster_stop():
    """Stop the auto-poster"""
    global auto_poster_running
    
    if not auto_poster_running:
        return jsonify({
            'success': False,
            'message': 'Auto-poster is not running'
        }), 200
    
    auto_poster_running = False
    
    return jsonify({
        'success': True,
        'message': 'Auto-poster stopping...'
    }), 200


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--auto-poster', action='store_true', help='Start auto-poster on launch')
    args = parser.parse_args()
    
    print("=" * 60)
    print("LinkedIn Automation Server")
    print("=" * 60)
    print("\nStarting server on http://localhost:5050")
    print("\nRevision Endpoints:")
    print("  Button (single):      http://localhost:5050/revise/{record_id}")
    print("  Button (all):         http://localhost:5050/revise-all")
    print("  Automation:           http://localhost:5050/automation/revise")
    print("\nAuto-Poster Endpoints:")
    print("  Status:               http://localhost:5050/poster/status")
    print("  Start:                http://localhost:5050/poster/start")
    print("  Stop:                 http://localhost:5050/poster/stop")
    print("\nAirtable Button Formula:")
    print("  CONCATENATE('http://localhost:5050/revise/', RECORD_ID())")
    
    # Auto-start poster if flag is set
    if args.auto_poster:
        print("\n✓ Auto-poster enabled - starting background poster...")
        auto_poster_thread = threading.Thread(target=run_auto_poster, daemon=True)
        auto_poster_thread.start()
    else:
        print("\nAuto-poster NOT started. Use --auto-poster flag or call /poster/start")
    
    print("\nPress Ctrl+C to stop")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5050, debug=False)
