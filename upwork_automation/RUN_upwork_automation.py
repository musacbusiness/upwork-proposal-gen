#!/usr/bin/env python3
"""
RUN_upwork_automation.py - ENTRY POINT FOR UPWORK AUTOMATION

This is the main interaction point for the Upwork job automation system.
Use this script to run any part of the automation pipeline.

Usage:
    python RUN_upwork_automation.py --action filter     # Filter raw jobs
    python RUN_upwork_automation.py --action sync       # Sync to ClickUp
    python RUN_upwork_automation.py --action proposals  # Generate proposals for approved jobs
    python RUN_upwork_automation.py --action full       # Run complete pipeline
    python RUN_upwork_automation.py --action status     # Check system status
"""

import json
import logging
import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add execution directory to path
sys.path.insert(0, str(Path(__file__).parent / 'execution'))

from execution.filter_jobs import JobFilter, load_filter_config, get_default_filter_config
from execution.sync_to_clickup import ClickUpIntegration, load_filtered_jobs, save_sync_summary
from execution.generate_proposal import ProposalGenerator, save_proposals_summary
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/upwork_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()


class UpworkAutomationOrchestrator:
    """Orchestrate the complete Upwork job automation pipeline"""
    
    def __init__(self):
        self.logger = logger
        self.ensure_directories()
    
    def ensure_directories(self):
        """Create necessary directories if they don't exist"""
        dirs = [
            'logs',
            'config',
            'templates',
            '.tmp',
            '.tmp/proposals'
        ]
        for d in dirs:
            Path(d).mkdir(parents=True, exist_ok=True)
    
    def action_filter(self):
        """Filter raw jobs based on criteria"""
        self.logger.info("=" * 60)
        self.logger.info("ACTION: Filter Jobs")
        self.logger.info("=" * 60)
        
        # Load filter config
        try:
            config = load_filter_config('config/filter_rules.json')
        except Exception as e:
            self.logger.warning(f"Could not load filter config, using defaults: {e}")
            config = get_default_filter_config()
        
        # Initialize filter
        filter_engine = JobFilter(config)
        
        # Load raw jobs
        raw_jobs = filter_engine.load_raw_jobs('.tmp/raw_jobs.json')
        if not raw_jobs:
            self.logger.error("No raw jobs found at .tmp/raw_jobs.json")
            self.logger.info("First, you need to scrape jobs. See README.md")
            return False
        
        # Filter jobs
        accepted, rejected = filter_engine.filter_jobs(raw_jobs)
        
        # Save results
        filter_engine.save_filtered_jobs(accepted, rejected)
        
        self.logger.info(f"✓ Filtering complete: {len(accepted)} accepted, {len(rejected)} rejected")
        return True
    
    def action_sync(self):
        """Sync filtered jobs to ClickUp"""
        self.logger.info("=" * 60)
        self.logger.info("ACTION: Sync to ClickUp")
        self.logger.info("=" * 60)
        
        # Load credentials
        api_key = os.getenv('CLICKUP_API_KEY')
        workspace_id = os.getenv('CLICKUP_WORKSPACE_ID')
        list_id = os.getenv('CLICKUP_LIST_ID')
        
        if not all([api_key, workspace_id, list_id]):
            self.logger.error("Missing ClickUp credentials in .env file")
            self.logger.info("Required: CLICKUP_API_KEY, CLICKUP_WORKSPACE_ID, CLICKUP_LIST_ID")
            return False
        
        # Initialize ClickUp
        clickup = ClickUpIntegration(api_key, workspace_id, list_id)
        
        # Load filtered jobs
        jobs = load_filtered_jobs('.tmp/filtered_jobs_accepted.json')
        if not jobs:
            self.logger.error("No filtered jobs found. Run 'filter' action first.")
            return False
        
        # Sync to ClickUp
        summary = clickup.sync_jobs_to_clickup(jobs)
        save_sync_summary(summary)
        
        self.logger.info(f"✓ ClickUp sync complete: {summary['created']} created, {summary['duplicates']} duplicates, {summary['failed']} failed")
        return True
    
    def action_proposals(self):
        """Generate proposals for approved jobs"""
        self.logger.info("=" * 60)
        self.logger.info("ACTION: Generate Proposals")
        self.logger.info("=" * 60)
        
        # Load API key
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            self.logger.error("ANTHROPIC_API_KEY not found in .env file")
            return False
        
        # Initialize proposal generator
        generator = ProposalGenerator(api_key)
        
        # Load approved jobs
        # First try to load from ClickUp export
        approved_file = '.tmp/approved_jobs.json'
        if not Path(approved_file).exists():
            self.logger.warning(f"Approved jobs file not found at {approved_file}")
            self.logger.info("You can export approved jobs from ClickUp by:")
            self.logger.info("1. Filter ClickUp list to status='APPROVED'")
            self.logger.info("2. Export as JSON with custom fields")
            self.logger.info("3. Save to .tmp/approved_jobs.json")
            
            # Alternative: use filtered jobs as demo
            approved_file = '.tmp/filtered_jobs_accepted.json'
            self.logger.info(f"Using filtered jobs from {approved_file} instead")
        
        try:
            with open(approved_file, 'r') as f:
                jobs = json.load(f)
        except FileNotFoundError:
            self.logger.error(f"Could not load jobs from {approved_file}")
            return False
        
        if not jobs:
            self.logger.error("No jobs to generate proposals for")
            return False
        
        # Generate proposals
        summary = generator.generate_proposals_batch(jobs, '.tmp/proposals/')
        save_proposals_summary(summary)
        
        self.logger.info(f"✓ Proposal generation complete: {summary['generated']} generated, {summary['failed']} failed")
        return True
    
    def action_full(self):
        """Run complete pipeline: filter -> sync -> proposals"""
        self.logger.info("=" * 60)
        self.logger.info("ACTION: Full Pipeline")
        self.logger.info("=" * 60)
        
        steps = [
            ("filter", self.action_filter),
            ("sync", self.action_sync),
            ("proposals", self.action_proposals)
        ]
        
        results = {}
        for step_name, step_func in steps:
            self.logger.info(f"\n>>> Running step: {step_name}")
            try:
                results[step_name] = step_func()
            except Exception as e:
                self.logger.error(f"Error in {step_name}: {e}")
                results[step_name] = False
        
        # Summary
        self.logger.info("\n" + "=" * 60)
        self.logger.info("PIPELINE SUMMARY")
        self.logger.info("=" * 60)
        for step_name, success in results.items():
            status = "✓ PASS" if success else "✗ FAIL"
            self.logger.info(f"{status} - {step_name}")
        
        return all(results.values())
    
    def action_status(self):
        """Show current status of the system"""
        self.logger.info("=" * 60)
        self.logger.info("SYSTEM STATUS")
        self.logger.info("=" * 60)
        
        # Check files
        files_status = {
            '.tmp/raw_jobs.json': 'Raw scraped jobs',
            '.tmp/filtered_jobs_accepted.json': 'Filtered & accepted jobs',
            '.tmp/filtered_jobs_rejected.json': 'Filtered & rejected jobs',
            '.tmp/clickup_sync_summary.json': 'ClickUp sync summary',
            '.tmp/approved_jobs.json': 'Approved jobs from ClickUp',
            '.tmp/proposals_summary.json': 'Proposals generation summary',
        }
        
        for filepath, description in files_status.items():
            exists = Path(filepath).exists()
            status = "✓" if exists else "✗"
            size = f"({Path(filepath).stat().st_size} bytes)" if exists else ""
            self.logger.info(f"{status} {description} - {filepath} {size}")
        
        # Check credentials
        self.logger.info("\n" + "-" * 60)
        self.logger.info("CREDENTIALS STATUS")
        self.logger.info("-" * 60)
        
        creds = {
            'CLICKUP_API_KEY': 'ClickUp API',
            'ANTHROPIC_API_KEY': 'Claude API',
            'UPWORK_EMAIL': 'Upwork Email',
        }
        
        for env_var, description in creds.items():
            value = os.getenv(env_var)
            status = "✓" if value else "✗"
            masked = value[:10] + "..." if value else "NOT SET"
            self.logger.info(f"{status} {description}: {masked}")


def main():
    parser = argparse.ArgumentParser(
        description='Upwork Job Automation - Main Entry Point',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python RUN_upwork_automation.py --action filter      # Filter raw jobs
  python RUN_upwork_automation.py --action sync        # Sync to ClickUp
  python RUN_upwork_automation.py --action proposals   # Generate proposals
  python RUN_upwork_automation.py --action full        # Run complete pipeline
  python RUN_upwork_automation.py --action status      # Check system status
        """
    )
    
    parser.add_argument(
        '--action',
        choices=['filter', 'sync', 'proposals', 'full', 'status'],
        required=True,
        help='Action to perform'
    )
    
    args = parser.parse_args()
    
    orchestrator = UpworkAutomationOrchestrator()
    
    action_map = {
        'filter': orchestrator.action_filter,
        'sync': orchestrator.action_sync,
        'proposals': orchestrator.action_proposals,
        'full': orchestrator.action_full,
        'status': orchestrator.action_status,
    }
    
    success = action_map[args.action]()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
