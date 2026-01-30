#!/usr/bin/env python3
"""
Upwork Job Automation Orchestrator

Main script to coordinate all steps of the automation pipeline:
1. Scrape jobs (manual or via Apify)
2. Filter jobs
3. Sync to ClickUp
4. Generate proposals (on-demand or via webhook)

Usage:
    python orchestrate.py --action filter     # Filter raw jobs
    python orchestrate.py --action sync       # Sync to ClickUp
    python orchestrate.py --action proposals  # Generate proposals for approved jobs
    python orchestrate.py --action full       # Run complete pipeline
"""

import json
import logging
import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add execution directory to path
sys.path.insert(0, str(Path(__file__).parent / 'execution'))

from filter_jobs import JobFilter, load_filter_config, get_default_filter_config
from sync_to_clickup import ClickUpIntegration, load_filtered_jobs, save_sync_summary
from airtable_upwork import UpworkAirtable
from generate_proposal import ProposalGenerator, save_proposals_summary
from upwork_scraper_selenium import UpworkScraperSelenium, scrape_upwork_jobs
from upwork_proposal_submitter import UpworkProposalSubmitter, submit_approved_proposals
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
    
    def action_scrape(self, search_query: str = None, max_jobs: int = 100, headless: bool = False, manual_login: bool = False):
        """Scrape jobs from Upwork using browser automation"""
        self.logger.info("=" * 60)
        self.logger.info("ACTION: Scrape Upwork Jobs")
        self.logger.info("=" * 60)
        
        # Check credentials (not required for manual login)
        upwork_email = os.getenv('UPWORK_EMAIL')
        upwork_password = os.getenv('UPWORK_PASSWORD')
        
        if not manual_login and (not upwork_email or not upwork_password):
            self.logger.error("UPWORK_EMAIL and UPWORK_PASSWORD must be set in .env file")
            self.logger.info("Or use --manual flag to log in manually")
            return False
        
        # Get search query
        if not search_query:
            # Load from config if available
            try:
                config = load_filter_config('config/filter_rules.json')
                skills = config.get('skills_required', [])
                # Filter out notes
                skills = [s for s in skills if not s.startswith('note:')]
                search_query = ' '.join(skills[:3])  # Use first 3 skills as search
            except:
                pass
        
        if not search_query:
            search_query = "Python automation"  # Default fallback
            
        self.logger.info(f"Search query: {search_query}")
        self.logger.info(f"Max jobs: {max_jobs}")
        self.logger.info(f"Headless mode: {headless}")
        self.logger.info(f"Manual login: {manual_login}")
        self.logger.info("-" * 60)
        
        try:
            jobs = scrape_upwork_jobs(
                search_query=search_query,
                max_jobs=max_jobs,
                output_file='.tmp/raw_jobs.json',
                headless=headless,
                manual_login=manual_login
            )
            
            self.logger.info(f"✓ Scraped {len(jobs)} jobs successfully")
            self.logger.info(f"✓ Saved to .tmp/raw_jobs.json")
            return True
            
        except Exception as e:
            self.logger.error(f"Scraping failed: {e}")
            return False
    
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
            self.logger.info("First, you need to scrape jobs. See directives/upwork_job_automation.md")
            return False
        
        # Filter jobs
        accepted, rejected = filter_engine.filter_jobs(raw_jobs)
        
        # Save results
        filter_engine.save_filtered_jobs(accepted, rejected)
        
        self.logger.info(f"✓ Filtering complete: {len(accepted)} accepted, {len(rejected)} rejected")
        return True
    
    def action_sync(self):
        """Sync filtered jobs to Airtable"""
        self.logger.info("=" * 60)
        self.logger.info("ACTION: Sync to Airtable")
        self.logger.info("=" * 60)
        
        # Check for Airtable credentials in env
        api_key = os.getenv('AIRTABLE_API_KEY')
        base_id = os.getenv('AIRTABLE_UPWORK_BASE_ID')
        
        if not api_key:
            self.logger.error("Missing AIRTABLE_API_KEY in .env file")
            return False
        
        if not base_id:
            self.logger.error("Missing AIRTABLE_UPWORK_BASE_ID in .env file")
            self.logger.info("Run: python setup_airtable_upwork.py to create the Airtable table")
            return False
        
        # Initialize Airtable (reads credentials from env)
        airtable = UpworkAirtable()
        
        # Load filtered jobs
        jobs = load_filtered_jobs('.tmp/filtered_jobs_accepted.json')
        if not jobs:
            self.logger.error("No filtered jobs found. Run 'filter' action first.")
            return False
        
        # Sync to Airtable
        summary = airtable.sync_jobs(jobs)
        
        # Save summary
        summary_path = '.tmp/airtable_sync_summary.json'
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        self.logger.info(f"✓ Airtable sync complete: {summary['created']} created, {summary.get('updated', 0)} updated, {summary.get('skipped', 0)} duplicates, {summary['failed']} failed")
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
        
        # Load approved jobs from Airtable
        airtable_api_key = os.getenv('AIRTABLE_API_KEY')
        airtable_base_id = os.getenv('AIRTABLE_UPWORK_BASE_ID')
        
        jobs = []
        if airtable_api_key and airtable_base_id:
            try:
                airtable = UpworkAirtable()  # Reads from env
                jobs = airtable.get_approved_jobs()
                self.logger.info(f"Loaded {len(jobs)} approved jobs from Airtable")
            except Exception as e:
                self.logger.warning(f"Could not load from Airtable: {e}")
        
        # Fallback to local file if no Airtable jobs
        if not jobs:
            approved_file = '.tmp/approved_jobs.json'
            if not Path(approved_file).exists():
                self.logger.warning(f"Approved jobs file not found at {approved_file}")
                self.logger.info("Mark jobs as 'Approved' in Airtable to generate proposals")
                
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
    
    def action_full(self, search_query: str = None, max_jobs: int = 100, headless: bool = False, manual_login: bool = False):
        """Run complete pipeline: scrape -> filter -> sync -> proposals"""
        self.logger.info("=" * 60)
        self.logger.info("ACTION: Full Pipeline")
        self.logger.info("=" * 60)
        
        steps = [
            ("scrape", lambda: self.action_scrape(search_query, max_jobs, headless, manual_login)),
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
            '.tmp/airtable_sync_summary.json': 'Airtable sync summary',
            '.tmp/approved_jobs.json': 'Approved jobs',
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
            'AIRTABLE_API_KEY': 'Airtable API',
            'AIRTABLE_UPWORK_BASE_ID': 'Airtable Upwork Base',
            'ANTHROPIC_API_KEY': 'Claude API',
            'UPWORK_EMAIL': 'Upwork Email',
        }
        
        for env_var, description in creds.items():
            value = os.getenv(env_var)
            status = "✓" if value else "✗"
            masked = value[:10] + "..." if value else "NOT SET"
            self.logger.info(f"{status} {description}: {masked}")
    
    def action_submit(self, boost_connects: int = 4, max_submissions: int = 5):
        """Submit proposals for approved jobs with connect boosting"""
        self.logger.info("=" * 60)
        self.logger.info("ACTION: Submit Proposals")
        self.logger.info("=" * 60)
        
        # Load settings
        try:
            with open('config/proposal_settings.json', 'r') as f:
                settings = json.load(f)
                boost_connects = settings.get('connects', {}).get('boost_amount', boost_connects)
                max_submissions = settings.get('submission_limits', {}).get('max_per_run', max_submissions)
        except FileNotFoundError:
            self.logger.warning("proposal_settings.json not found, using defaults")
        
        self.logger.info(f"Connect boost: +{boost_connects}")
        self.logger.info(f"Max submissions: {max_submissions}")
        self.logger.info("-" * 60)
        
        try:
            summary = submit_approved_proposals(
                boost_connects=boost_connects,
                max_submissions=max_submissions
            )
            
            # Save summary
            summary['timestamp'] = datetime.now().isoformat()
            with open('.tmp/submission_summary.json', 'w') as f:
                json.dump(summary, f, indent=2)
            
            self.logger.info(f"✓ Submission complete: {summary['submitted']} submitted, {summary['failed']} failed")
            return summary['submitted'] > 0 or summary['processed'] == 0
            
        except Exception as e:
            self.logger.error(f"Submission failed: {e}")
            return False
    
    def action_webhook(self, port: int = 5051):
        """Start the webhook server for automatic proposal submission"""
        self.logger.info("=" * 60)
        self.logger.info("ACTION: Start Webhook Server")
        self.logger.info("=" * 60)
        
        import subprocess
        webhook_script = Path(__file__).parent / 'execution' / 'webhook_upwork_proposals.py'
        
        self.logger.info(f"Starting webhook server on port {port}...")
        self.logger.info("Use Ctrl+C to stop")
        self.logger.info("-" * 60)
        
        try:
            subprocess.run(['python3', str(webhook_script)], check=True)
            return True
        except KeyboardInterrupt:
            self.logger.info("\nWebhook server stopped")
            return True
        except Exception as e:
            self.logger.error(f"Webhook server error: {e}")
            return False
    
    def action_auto(self, port: int = 5051, poll_interval: int = 30):
        """Start the Airtable automation server for status-based workflow
        
        This monitors Airtable for status changes:
        - Status → "Under Review": Auto-generates proposal
        - Status → "Approved": Auto-submits proposal
        """
        self.logger.info("=" * 60)
        self.logger.info("ACTION: Start Airtable Automation Server")
        self.logger.info("=" * 60)
        
        import subprocess
        automation_script = Path(__file__).parent / 'execution' / 'webhook_airtable_automation.py'
        
        self.logger.info(f"Starting Airtable automation on port {port}...")
        self.logger.info(f"Poll interval: {poll_interval} seconds")
        self.logger.info("")
        self.logger.info("Workflow:")
        self.logger.info("  1. Change job status to 'Under Review' → Auto-generates proposal")
        self.logger.info("  2. Change job status to 'Approved' → Auto-submits proposal")
        self.logger.info("")
        self.logger.info("Use Ctrl+C to stop")
        self.logger.info("-" * 60)
        
        env = os.environ.copy()
        env['POLL_INTERVAL'] = str(poll_interval)
        env['FLASK_PORT'] = str(port)
        
        try:
            subprocess.run(['python3', str(automation_script)], check=True, env=env)
            return True
        except KeyboardInterrupt:
            self.logger.info("\nAirtable automation stopped")
            return True
        except Exception as e:
            self.logger.error(f"Airtable automation error: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description='Upwork Job Automation Orchestrator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python orchestrate.py --action scrape --query "Python API"   # Scrape jobs
  python orchestrate.py --action scrape --query "automation" --max 100
  python orchestrate.py --action scrape --manual --query "Python"  # Manual login mode
  python orchestrate.py --action filter      # Filter raw jobs
  python orchestrate.py --action sync        # Sync to Airtable
  python orchestrate.py --action proposals   # Generate proposals
  python orchestrate.py --action submit      # Submit proposals for approved jobs
  python orchestrate.py --action submit --boost 8   # Submit with higher connect bid
  python orchestrate.py --action auto        # Start auto-workflow (recommended!)
  python orchestrate.py --action auto --poll 60   # Auto-workflow with 60s poll interval
  python orchestrate.py --action webhook     # Start webhook server (legacy)
  python orchestrate.py --action full --query "Python automation"  # Run complete pipeline
  python orchestrate.py --action status      # Check system status

Auto-Workflow (--action auto):
  This starts the Airtable automation server that monitors for status changes:
  - When you change a job status to "Under Review" → Proposal is auto-generated
  - When you change a job status to "Approved" → Proposal is auto-submitted
        """
    )
    
    parser.add_argument(
        '--action',
        choices=['scrape', 'filter', 'sync', 'proposals', 'submit', 'auto', 'webhook', 'full', 'status'],
        required=True,
        help='Action to perform'
    )
    
    parser.add_argument(
        '--boost',
        type=int,
        default=4,
        help='Connect boost amount for higher proposal visibility (default: 4)'
    )
    
    parser.add_argument(
        '--submissions',
        type=int,
        default=5,
        help='Maximum proposals to submit per run (default: 5)'
    )
    
    parser.add_argument(
        '--poll',
        type=int,
        default=30,
        help='Poll interval in seconds for auto action (default: 30)'
    )
    
    parser.add_argument(
        '--query', '-q',
        type=str,
        default=None,
        help='Search query for Upwork jobs (used with scrape/full actions)'
    )
    
    parser.add_argument(
        '--max', '-m',
        type=int,
        default=100,
        help='Maximum jobs to scrape (default: 100)'
    )
    
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browser in headless mode (no visible window)'
    )
    
    parser.add_argument(
        '--manual',
        action='store_true',
        help='Manual login mode - opens browser and waits for you to log in'
    )
    
    args = parser.parse_args()
    
    orchestrator = UpworkAutomationOrchestrator()
    
    # Handle actions with parameters
    if args.action == 'scrape':
        success = orchestrator.action_scrape(args.query, args.max, args.headless, args.manual)
    elif args.action == 'full':
        success = orchestrator.action_full(args.query, args.max, args.headless, args.manual)
    elif args.action == 'submit':
        success = orchestrator.action_submit(args.boost, args.submissions)
    elif args.action == 'webhook':
        success = orchestrator.action_webhook()
    elif args.action == 'auto':
        success = orchestrator.action_auto(poll_interval=args.poll)
    else:
        action_map = {
            'filter': orchestrator.action_filter,
            'sync': orchestrator.action_sync,
            'proposals': orchestrator.action_proposals,
            'status': orchestrator.action_status,
        }
        success = action_map[args.action]()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
