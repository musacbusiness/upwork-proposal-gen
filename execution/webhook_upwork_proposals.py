"""
Upwork Proposal Webhook Serverexport PATH="$PATH:/Users/musacomma/Library/Python/3.9/bin" && modal token new
==============================
Listens for Airtable webhooks when job status changes to "Approved".
Automatically generates and submits proposals with connect boosting.

Setup:
1. Run this server: python webhook_upwork_proposals.py
2. Expose with ngrok: ngrok http 5051
3. Configure Airtable webhook to POST to your ngrok URL

Workflow:
1. You review jobs in Airtable
2. Change Status to "Approved" for jobs you want to apply to
3. Webhook triggers automatic proposal submission
4. Status updates to "Applied" or stays "Under Review" if failed
"""

import os
import json
import logging
import threading
from datetime import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Import submitter
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from upwork_proposal_submitter import UpworkProposalSubmitter

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/upwork_webhook.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Track submissions to avoid duplicates
recent_submissions = {}
SUBMISSION_COOLDOWN = 300  # 5 minutes cooldown per job


def load_proposal_settings():
    """Load proposal settings from config file."""
    try:
        with open('config/proposal_settings.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            'connects': {'boost_amount': 4},
            'submission_limits': {'max_per_run': 5, 'delay_between_submissions': 30}
        }


def process_job_async(job_data: dict, settings: dict):
    """Process job submission in background thread."""
    job_id = job_data.get('Job ID', 'unknown')
    
    # Check cooldown
    last_submission = recent_submissions.get(job_id)
    if last_submission:
        elapsed = (datetime.now() - last_submission).total_seconds()
        if elapsed < SUBMISSION_COOLDOWN:
            logger.info(f"Job {job_id} on cooldown ({int(SUBMISSION_COOLDOWN - elapsed)}s remaining)")
            return
    
    logger.info(f"Processing approved job: {job_data.get('Job Title', 'Unknown')[:50]}...")
    
    try:
        # Initialize submitter with settings
        boost = settings.get('connects', {}).get('boost_amount', 4)
        submitter = UpworkProposalSubmitter(boost_connects=boost)
        
        # Submit proposal
        success, message = submitter.submit_proposal(job_data)
        
        # Track submission
        recent_submissions[job_id] = datetime.now()
        
        if success:
            logger.info(f"✓ Successfully submitted proposal for job {job_id}")
        else:
            logger.warning(f"✗ Failed to submit proposal for job {job_id}: {message}")
        
        submitter.close()
        
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {e}")


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'upwork-proposal-webhook',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/webhook/upwork', methods=['POST'])
def handle_upwork_webhook():
    """
    Handle Airtable webhook for Upwork job approvals.
    
    Expected payload format (from Airtable):
    {
        "record_id": "recXXX",
        "fields": {
            "Job Title": "...",
            "Job URL": "...",
            "Description": "...",
            "Status": "Approved",
            ...
        }
    }
    """
    try:
        data = request.json
        logger.info(f"Received webhook: {json.dumps(data)[:200]}...")
        
        # Handle Airtable webhook format
        if 'fields' in data:
            fields = data.get('fields', {})
            record_id = data.get('record_id') or data.get('id')
        else:
            # Direct field format
            fields = data
            record_id = data.get('_record_id') or data.get('record_id')
        
        # Check if this is an approval
        status = fields.get('Status', '')
        if status != 'Approved':
            logger.info(f"Ignoring non-approval status: {status}")
            return jsonify({'status': 'ignored', 'reason': f'Status is {status}, not Approved'})
        
        # Add record ID to fields
        fields['_record_id'] = record_id
        
        # Load settings
        settings = load_proposal_settings()
        
        # Process in background thread
        thread = threading.Thread(
            target=process_job_async,
            args=(fields, settings)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'status': 'accepted',
            'message': 'Job queued for proposal submission',
            'job_title': fields.get('Job Title', 'Unknown')[:50]
        })
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/webhook/batch', methods=['POST'])
def handle_batch_webhook():
    """
    Process multiple approved jobs at once.
    
    Expected payload:
    {
        "jobs": [
            {"record_id": "...", "fields": {...}},
            ...
        ]
    }
    """
    try:
        data = request.json
        jobs = data.get('jobs', [])
        
        if not jobs:
            return jsonify({'status': 'error', 'message': 'No jobs provided'})
        
        settings = load_proposal_settings()
        max_per_run = settings.get('submission_limits', {}).get('max_per_run', 5)
        
        queued = 0
        for job_data in jobs[:max_per_run]:
            fields = job_data.get('fields', job_data)
            record_id = job_data.get('record_id') or job_data.get('id')
            fields['_record_id'] = record_id
            
            thread = threading.Thread(
                target=process_job_async,
                args=(fields, settings)
            )
            thread.daemon = True
            thread.start()
            queued += 1
        
        return jsonify({
            'status': 'accepted',
            'queued': queued,
            'message': f'Queued {queued} jobs for proposal submission'
        })
        
    except Exception as e:
        logger.error(f"Batch webhook error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/submit/manual', methods=['POST'])
def manual_submission():
    """
    Manually trigger submission for a specific job.
    
    Payload:
    {
        "job_url": "https://upwork.com/jobs/...",
        "job_title": "...",
        "description": "...",
        "proposal": "Optional pre-written proposal"
    }
    """
    try:
        data = request.json
        
        required = ['job_url']
        for field in required:
            if field not in data:
                return jsonify({'status': 'error', 'message': f'Missing required field: {field}'}), 400
        
        # Build job dict
        job_data = {
            'Job URL': data.get('job_url'),
            'Job Title': data.get('job_title', 'Manual Submission'),
            'Description': data.get('description', ''),
            'Skills': data.get('skills', ''),
            'Budget': data.get('budget', 0),
            'Proposal': data.get('proposal', ''),
            '_record_id': None  # No Airtable record
        }
        
        settings = load_proposal_settings()
        
        # Process synchronously for manual submissions
        boost = settings.get('connects', {}).get('boost_amount', 4)
        submitter = UpworkProposalSubmitter(boost_connects=boost)
        
        success, message = submitter.submit_proposal(job_data, proposal_text=data.get('proposal'))
        submitter.close()
        
        return jsonify({
            'status': 'success' if success else 'failed',
            'message': message
        })
        
    except Exception as e:
        logger.error(f"Manual submission error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/status', methods=['GET'])
def get_status():
    """Get current submission status and recent activity."""
    settings = load_proposal_settings()
    
    return jsonify({
        'status': 'running',
        'settings': {
            'boost_connects': settings.get('connects', {}).get('boost_amount', 4),
            'max_per_run': settings.get('submission_limits', {}).get('max_per_run', 5),
        },
        'recent_submissions': len(recent_submissions),
        'cooldown_seconds': SUBMISSION_COOLDOWN
    })


def main():
    """Run the webhook server."""
    port = int(os.getenv('UPWORK_WEBHOOK_PORT', 5051))
    
    print("\n" + "=" * 60)
    print("UPWORK PROPOSAL WEBHOOK SERVER")
    print("=" * 60)
    print(f"Server running on http://localhost:{port}")
    print(f"\nEndpoints:")
    print(f"  POST /webhook/upwork  - Airtable webhook for approvals")
    print(f"  POST /webhook/batch   - Process multiple jobs")
    print(f"  POST /submit/manual   - Manual job submission")
    print(f"  GET  /status          - Check server status")
    print(f"  GET  /health          - Health check")
    print(f"\nTo expose publicly:")
    print(f"  ngrok http {port}")
    print("=" * 60 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=False)


if __name__ == '__main__':
    main()
