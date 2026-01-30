#!/usr/bin/env python3
"""
webhook_revise.py - Webhook endpoint for Airtable button to trigger revisions

This creates a simple web server that Airtable buttons can call to trigger
the revision process for a specific record.

Usage:
    python3 webhook_revise.py

Then in Airtable, create a button with URL:
    http://localhost:5050/revise/{record_id}
"""

from flask import Flask, request, jsonify
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


@app.route('/revise/<record_id>', methods=['GET', 'POST'])
def revise_record(record_id):
    """
    Trigger revision for a specific Airtable record
    
    Args:
        record_id: The Airtable record ID to process
        
    Returns:
        JSON response with success/failure status
    """
    try:
        logger.info(f"Received revision request for record: {record_id}")
        
        # Initialize revision processor
        processor = ContentRevisionProcessor()
        
        # Process only this specific record
        result = processor.check_for_revisions(record_ids=[record_id])
        
        if result:
            return jsonify({
                'success': True,
                'message': f'Revision completed for record {record_id}',
                'record_id': record_id
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': f'No revisions needed or Notes field empty for {record_id}',
                'record_id': record_id
            }), 200
            
    except Exception as e:
        logger.error(f"Error processing revision: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'record_id': record_id
        }), 500


@app.route('/revise-all', methods=['GET', 'POST'])
def revise_all():
    """
    Trigger revision check for all records with Notes
    
    Returns:
        JSON response with success/failure status
    """
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


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'linkedin-revision-webhook'}), 200


if __name__ == '__main__':
    print("=" * 60)
    print("LinkedIn Revision Webhook Server")
    print("=" * 60)
    print("\nStarting server on http://localhost:5050")
    print("\nAirtable Button URLs:")
    print("  Single record: http://localhost:5050/revise/{record_id}")
    print("  All records:   http://localhost:5050/revise-all")
    print("\nPress Ctrl+C to stop")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5050, debug=False)
