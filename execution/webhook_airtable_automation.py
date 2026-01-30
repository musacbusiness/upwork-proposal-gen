"""
Upwork Automation Webhook Server
================================
Monitors Airtable for status changes and automatically:
1. Generates proposals when status → "Under Review"
2. Submits proposals when status → "Approved"

Setup:
1. Run this server: python webhook_airtable_automation.py
2. Configure Airtable Automation to POST to this webhook on record updates
3. Or run in polling mode to check Airtable periodically

Workflow:
  New → Under Review (auto-generates proposal)
      → Approved (auto-submits proposal with connects)
      → Applied (done!)
"""

import os
import sys
import json
import time
import logging
import threading
from datetime import datetime
from typing import Dict, List, Optional
from flask import Flask, request, jsonify
import requests

# Add execution path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/upwork_webhook.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Airtable config
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_UPWORK_BASE_ID') or os.getenv('AIRTABLE_BASE_ID')
AIRTABLE_TABLE = 'Upwork Jobs'

# Track processed records to avoid duplicates
processed_records = {}
COOLDOWN_SECONDS = 300  # 5 minutes cooldown per record


def load_settings():
    """Load proposal settings from config."""
    try:
        with open('config/proposal_settings.json', 'r') as f:
            return json.load(f)
    except:
        return {'connects': {'boost_amount': 4}}


def get_airtable_headers():
    return {
        'Authorization': f'Bearer {AIRTABLE_API_KEY}',
        'Content-Type': 'application/json'
    }


def update_airtable_record(record_id: str, fields: dict) -> bool:
    """Update a record in Airtable."""
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE}/{record_id}"
    
    try:
        response = requests.patch(url, headers=get_airtable_headers(), json={'fields': fields})
        if response.status_code == 200:
            logger.info(f"Updated record {record_id}: {list(fields.keys())}")
            return True
        else:
            logger.error(f"Failed to update {record_id}: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error updating record: {e}")
        return False


def delete_airtable_record(record_id: str) -> bool:
    """Delete a record from Airtable."""
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE}/{record_id}"
    
    try:
        response = requests.delete(url, headers=get_airtable_headers())
        if response.status_code == 200:
            logger.info(f"🗑️ Deleted record {record_id}")
            return True
        else:
            logger.error(f"Failed to delete {record_id}: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error deleting record: {e}")
        return False


def generate_proposal_for_job(job: dict) -> Optional[str]:
    """Generate a proposal using Claude Opus 4.5."""
    try:
        import anthropic
        
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            logger.error("ANTHROPIC_API_KEY not set")
            return None
        
        client = anthropic.Anthropic(api_key=api_key)
        
        job_title = job.get('Job Title', 'Unknown')
        job_description = job.get('Description', '')[:800]
        job_skills = job.get('Skills', '')
        budget = job.get('Budget', 'Not specified')
        
        prompt = f"""You are an expert no-code automation specialist. Your PRIMARY tool is Make.com (formerly Integromat) because of its visual workflow builder and cost-effectiveness. You also use Zapier or n8n when clients specifically request them.

Write a compelling Upwork proposal for this job.

JOB TITLE: {job_title}

JOB DESCRIPTION:
{job_description}

REQUIRED SKILLS: {job_skills}

BUDGET: ${budget}

CRITICAL RULES:
1. Start with a hook that shows you understand their SPECIFIC problem
2. Be conversational, not formal - no generic openings
3. If they mention Zapier/n8n specifically, use that tool. Otherwise, recommend Make.com for flexibility and cost savings
4. Keep it SHORT - under 250 words. Clients don't read long proposals.
5. End with a clear call to action
6. NO generic phrases like "I came across your posting"
7. DO NOT make up fake stats or claim experience you don't have (no "I've built 100+ workflows" or "worked with 50+ clients")
8. Instead of fake social proof, be compelling through: understanding their problem, clear solution approach, specific deliverables, realistic timeline
9. Sound confident through CLARITY and SPECIFICITY, not inflated claims
10. Include a specific timeline estimate

Generate ONLY the proposal text, ready to submit."""

        response = client.messages.create(
            model="claude-opus-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        proposal = response.content[0].text.strip()
        logger.info(f"Generated proposal ({len(proposal)} chars) for: {job_title[:40]}...")
        return proposal
        
    except Exception as e:
        logger.error(f"Error generating proposal: {e}")
        return None


def submit_proposal_for_job(job: dict, proposal_text: str) -> tuple[bool, str]:
    """Submit a proposal using Selenium browser automation."""
    try:
        from upwork_proposal_submitter import UpworkProposalSubmitter
        
        settings = load_settings()
        boost = settings.get('connects', {}).get('boost_amount', 4)
        
        # Build job dict for submitter
        job_data = {
            'Job Title': job.get('Job Title'),
            'Job URL': job.get('Job URL'),
            'Description': job.get('Description'),
            'Skills': job.get('Skills'),
            'Budget': job.get('Budget'),
            '_record_id': job.get('_record_id'),
            'Proposal': proposal_text
        }
        
        submitter = UpworkProposalSubmitter(boost_connects=boost)
        success, message = submitter.submit_proposal(job_data, proposal_text=proposal_text)
        submitter.close()
        
        return success, message
        
    except Exception as e:
        logger.error(f"Error submitting proposal: {e}")
        return False, str(e)


def process_under_review(record_id: str, job: dict):
    """Process a job that changed to 'Under Review' - generate proposal."""
    job_title = job.get('Job Title', 'Unknown')
    logger.info(f"🔄 Generating proposal for: {job_title[:50]}...")
    
    # Check if proposal already exists
    if job.get('Proposal'):
        logger.info(f"Proposal already exists for {record_id}, skipping generation")
        return
    
    # Generate proposal
    proposal = generate_proposal_for_job(job)
    
    if proposal:
        # Save to Airtable
        update_airtable_record(record_id, {
            'Proposal': proposal,
            'Notes': f"Proposal auto-generated at {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        })
        logger.info(f"✓ Proposal saved for: {job_title[:40]}...")
    else:
        update_airtable_record(record_id, {
            'Notes': f"Failed to generate proposal at {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        })
        logger.error(f"✗ Failed to generate proposal for: {job_title[:40]}...")


def process_approved(record_id: str, job: dict):
    """Process a job that changed to 'Approved' - submit proposal."""
    job_title = job.get('Job Title', 'Unknown')
    logger.info(f"📤 Submitting proposal for: {job_title[:50]}...")
    
    # Get the proposal text
    proposal_text = job.get('Proposal')
    
    if not proposal_text:
        logger.error(f"No proposal found for {record_id}, generating now...")
        proposal_text = generate_proposal_for_job(job)
        if not proposal_text:
            update_airtable_record(record_id, {
                'Status': 'Under Review',
                'Notes': f"Submission failed - no proposal. {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            })
            return
    
    # Add record_id for status updates
    job['_record_id'] = record_id
    
    # Submit the proposal
    success, message = submit_proposal_for_job(job, proposal_text)
    
    if success:
        update_airtable_record(record_id, {
            'Status': 'Applied',
            'Applied': True,
            'Submitted At': datetime.now().isoformat(),
            'Notes': f"✓ Submitted: {message}"
        })
        logger.info(f"✓ Proposal submitted for: {job_title[:40]}...")
    else:
        update_airtable_record(record_id, {
            'Status': 'Under Review',  # Revert to review
            'Notes': f"✗ Submission failed: {message} at {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        })
        logger.error(f"✗ Submission failed for: {job_title[:40]}... - {message}")


def check_cooldown(record_id: str, action: str) -> bool:
    """Check if record is on cooldown to avoid duplicate processing."""
    key = f"{record_id}:{action}"
    last_processed = processed_records.get(key)
    
    if last_processed:
        elapsed = (datetime.now() - last_processed).total_seconds()
        if elapsed < COOLDOWN_SECONDS:
            return False  # On cooldown
    
    processed_records[key] = datetime.now()
    return True  # OK to process


def poll_airtable():
    """Poll Airtable for jobs needing processing."""
    logger.info("Polling Airtable for status changes...")
    
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE}"
    
    # Get jobs that need processing
    # 1. Under Review without proposal
    # 2. Approved (ready to submit)
    # 3. Rejected (auto-delete)
    
    try:
        # Check for "Under Review" jobs needing proposals
        params = {
            'filterByFormula': "AND({Status} = 'Under Review', {Proposal} = '')",
            'maxRecords': 5
        }
        response = requests.get(url, headers=get_airtable_headers(), params=params)
        
        if response.status_code == 200:
            records = response.json().get('records', [])
            for record in records:
                record_id = record['id']
                if check_cooldown(record_id, 'under_review'):
                    job = record.get('fields', {})
                    threading.Thread(target=process_under_review, args=(record_id, job)).start()
        
        # Check for "Approved" jobs ready to submit
        params = {
            'filterByFormula': "{Status} = 'Approved'",
            'maxRecords': 3
        }
        response = requests.get(url, headers=get_airtable_headers(), params=params)
        
        if response.status_code == 200:
            records = response.json().get('records', [])
            for record in records:
                record_id = record['id']
                if check_cooldown(record_id, 'approved'):
                    job = record.get('fields', {})
                    threading.Thread(target=process_approved, args=(record_id, job)).start()
                    time.sleep(30)  # Delay between submissions
        
        # Check for "Rejected" jobs to auto-delete
        params = {
            'filterByFormula': "{Status} = 'Rejected'",
            'maxRecords': 50  # Delete in batches
        }
        response = requests.get(url, headers=get_airtable_headers(), params=params)
        
        if response.status_code == 200:
            records = response.json().get('records', [])
            if records:
                logger.info(f"🗑️ Found {len(records)} rejected jobs to delete...")
            for record in records:
                record_id = record['id']
                job_title = record.get('fields', {}).get('Job Title', 'Unknown')
                if delete_airtable_record(record_id):
                    logger.info(f"🗑️ Deleted rejected job: {job_title[:40]}...")
    
    except Exception as e:
        logger.error(f"Polling error: {e}")


def polling_loop(interval: int = 60):
    """Continuous polling loop."""
    logger.info(f"Starting polling loop (every {interval}s)...")
    while True:
        try:
            poll_airtable()
        except Exception as e:
            logger.error(f"Polling loop error: {e}")
        time.sleep(interval)


# ============== Flask Routes ==============

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})


@app.route('/webhook/status-change', methods=['POST'])
def handle_status_change():
    """Handle Airtable webhook for status changes."""
    try:
        data = request.json
        logger.info(f"Received webhook: {json.dumps(data)[:200]}...")
        
        record_id = data.get('record_id') or data.get('id')
        fields = data.get('fields', data)
        status = fields.get('Status', '')
        
        if not record_id:
            return jsonify({'error': 'No record_id'}), 400
        
        if status == 'Under Review':
            if check_cooldown(record_id, 'under_review'):
                threading.Thread(target=process_under_review, args=(record_id, fields)).start()
                return jsonify({'status': 'processing', 'action': 'generate_proposal'})
        
        elif status == 'Approved':
            if check_cooldown(record_id, 'approved'):
                threading.Thread(target=process_approved, args=(record_id, fields)).start()
                return jsonify({'status': 'processing', 'action': 'submit_proposal'})
        
        return jsonify({'status': 'ignored', 'reason': f'Status is {status}'})
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/trigger/generate', methods=['POST'])
def trigger_generate():
    """Manually trigger proposal generation for a record."""
    data = request.json
    record_id = data.get('record_id')
    
    if not record_id:
        return jsonify({'error': 'record_id required'}), 400
    
    # Fetch record from Airtable
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE}/{record_id}"
    response = requests.get(url, headers=get_airtable_headers())
    
    if response.status_code != 200:
        return jsonify({'error': 'Record not found'}), 404
    
    job = response.json().get('fields', {})
    threading.Thread(target=process_under_review, args=(record_id, job)).start()
    
    return jsonify({'status': 'processing', 'action': 'generate_proposal'})


@app.route('/trigger/submit', methods=['POST'])
def trigger_submit():
    """Manually trigger proposal submission for a record."""
    data = request.json
    record_id = data.get('record_id')
    
    if not record_id:
        return jsonify({'error': 'record_id required'}), 400
    
    # Fetch record from Airtable
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE}/{record_id}"
    response = requests.get(url, headers=get_airtable_headers())
    
    if response.status_code != 200:
        return jsonify({'error': 'Record not found'}), 404
    
    job = response.json().get('fields', {})
    threading.Thread(target=process_approved, args=(record_id, job)).start()
    
    return jsonify({'status': 'processing', 'action': 'submit_proposal'})


@app.route('/status', methods=['GET'])
def get_status():
    """Get server status and recent activity."""
    return jsonify({
        'status': 'running',
        'processed_count': len(processed_records),
        'cooldown_seconds': COOLDOWN_SECONDS,
        'settings': load_settings()
    })


def main():
    """Run the webhook server with polling."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Upwork Automation Webhook Server')
    parser.add_argument('--port', type=int, default=5051, help='Server port')
    parser.add_argument('--poll', type=int, default=60, help='Polling interval in seconds (0 to disable)')
    parser.add_argument('--no-server', action='store_true', help='Run polling only, no HTTP server')
    
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("UPWORK AUTOMATION SERVER")
    print("=" * 60)
    print(f"""
Workflow:
  1. Change job status to 'Under Review' → Auto-generates proposal
  2. Review proposal in Airtable, edit if needed
  3. Change status to 'Approved' → Auto-submits proposal
  4. Status changes to 'Applied' when done
  5. Change status to 'Rejected' → Auto-deletes from Airtable

Endpoints:
  POST /webhook/status-change  - Airtable webhook
  POST /trigger/generate       - Manual proposal generation
  POST /trigger/submit         - Manual submission
  GET  /status                 - Server status

Polling: Every {args.poll}s (checking Airtable for status changes)
Port: {args.port}
""")
    print("=" * 60 + "\n")
    
    # Start polling thread
    if args.poll > 0:
        poll_thread = threading.Thread(target=polling_loop, args=(args.poll,), daemon=True)
        poll_thread.start()
        logger.info(f"Polling started (every {args.poll}s)")
    
    if args.no_server:
        # Just run polling
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
    else:
        # Run Flask server
        app.run(host='0.0.0.0', port=args.port, debug=False)


if __name__ == '__main__':
    main()
