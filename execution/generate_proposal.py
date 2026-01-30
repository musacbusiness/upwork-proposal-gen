import json
import logging
from typing import Dict, Optional, List
import os
from dotenv import load_dotenv
from datetime import datetime
import anthropic  # Using Claude
import sys

# Add execution/utils to path for cost_optimizer import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.cost_optimizer import CostTracker, PromptCache, PromptCompressor

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

# Initialize cost tracker
cost_tracker = CostTracker()

# Load environment variables
load_dotenv()


class ProposalGenerator:
    """Generate personalized proposals for Upwork jobs using Claude AI"""
    
    def __init__(self, api_key: str = None, template_path: str = 'templates/proposal_template.md'):
        """
        Initialize proposal generator
        
        Args:
            api_key: Claude API key (defaults to ANTHROPIC_API_KEY env var)
            template_path: Path to proposal template
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.template_path = template_path
        self.template = self._load_template()
        self.logger = logger
    
    def _load_template(self) -> str:
        """Load proposal template from file"""
        try:
            with open(self.template_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            self.logger.warning(f"Template not found at {self.template_path}, using default")
            return self._get_default_template()
    
    def _get_default_template(self) -> str:
        """Return default proposal template for no-code automation"""
        return """
I can help you build this automation using {tools}.

## What I'll Deliver

Based on your requirements, here's my approach:

1. **Discovery Call** - Quick 15-min call to understand your exact workflow
2. **Build & Test** - Create the automation with proper error handling
3. **Documentation** - Clear guide so you can manage it yourself
4. **Support** - 30 days of support to ensure everything runs smoothly

## Why Me?

I specialize in no-code automation, primarily using Make.com for its visual workflow builder and cost-effectiveness at scale. I'm also proficient with Zapier and n8n when the project calls for it.

My focus areas:
- CRM integrations (HubSpot, Salesforce, Pipedrive)
- E-commerce automation (Shopify, WooCommerce)
- Data sync between apps
- Custom webhooks and API connections

## Timeline

For a project like this, I typically deliver within {timeline}.

Let's hop on a quick call to discuss the specifics. I'm available to start immediately.
""".strip()
    
    def extract_job_insights(self, job: Dict) -> Dict:
        """
        Use Claude to extract key insights from job description (OPTIMIZED)

        Optimizations:
        - Uses Haiku (simple extraction task) instead of Opus: 80% cost savings
        - Compresses job data to JSON format: 40% token savings
        - Truncates description to 300 chars: 50% token savings
        - Adds prompt caching for system instruction: 90% savings after 1st call

        Returns:
            Dict with extracted pain points, requirements, opportunities
        """
        try:
            # Compress job data to JSON (instead of natural language)
            job_data = {
                "title": job.get('title', 'N/A'),
                "desc": PromptCompressor.truncate_description(job.get('description', 'N/A'), max_chars=300),
                "budget": job.get('budget', 'N/A'),
                "skills": job.get('skills', [])
            }
            job_json = PromptCompressor.to_json(job_data, indent=None)

            # Compress the prompt instructions
            system_instruction = """Extract from job posting: pain points, tech requirements, opportunities, positioning.
Respond in JSON with keys: pain_points, technical_requirements, opportunities, positioning."""

            message = self.client.messages.create(
                model="claude-haiku-4-5",  # CHANGED: Opus → Haiku (80% savings)
                max_tokens=400,  # CHANGED: Reduced from 500
                system=[
                    PromptCache.add_cache_control(system_instruction, ttl="ephemeral")  # ADDED: Caching
                ],
                messages=[
                    {
                        "role": "user",
                        "content": f"Analyze: {job_json}"
                    }
                ]
            )

            response_text = message.content[0].text

            # Log cost for this API call
            cost_tracker.log_call(
                model="claude-haiku-4-5",
                input_tokens=message.usage.input_tokens,
                output_tokens=message.usage.output_tokens,
                endpoint="extract_job_insights",
                cached_tokens=message.usage.cache_read_input_tokens if hasattr(message.usage, 'cache_read_input_tokens') else 0
            )

            # Try to parse JSON from response
            try:
                insights = json.loads(response_text)
            except json.JSONDecodeError:
                # Fallback if response isn't pure JSON
                insights = {
                    "pain_points": [job.get('description', '')[:100]],
                    "technical_requirements": job.get('skills', []),
                    "opportunities": ["Potential for ongoing maintenance/support"],
                    "positioning": "Position as a reliable expert in automation"
                }

            self.logger.info(f"Extracted insights for job {job.get('id')} (Haiku, cached)")
            return insights

        except Exception as e:
            self.logger.error(f"Error extracting job insights: {e}")
            return {
                "pain_points": [],
                "technical_requirements": job.get('skills', []),
                "opportunities": [],
                "positioning": "Professional approach to solving your automation needs"
            }
    
    def generate_proposal(self, job: Dict) -> str:
        """
        Generate a personalized proposal for a job (OPTIMIZED)

        Optimizations:
        - Uses Sonnet instead of Opus: 40% cost savings
        - System instructions cached with prompt caching: 90% savings after 1st call
        - Compressed prompt (removed redundant explanations): 30% token savings
        - Truncates description to 300 chars: 50% token savings on inputs
        - Constrained output to 250 words: 30% reduction in output tokens

        Args:
            job: Job dictionary with details

        Returns:
            Generated proposal text
        """
        try:
            # Extract insights
            insights = self.extract_job_insights(job)

            # Prepare context for Claude
            pain_points = ', '.join(insights.get('pain_points', ['automation challenges']))
            required_skills = ', '.join(job.get('skills', ['automation']))
            budget_range = f"${job.get('budget', 'negotiable')}"
            description_short = PromptCompressor.truncate_description(
                job.get('description', 'N/A'),
                max_chars=300
            )

            # Cached system instruction (same for all proposals)
            system_instruction = """You are an expert no-code automation specialist. Primary tool: Make.com (visual workflow builder, cost-effective).
Use Zapier/n8n if client requests. Generate compelling, conversational proposals under 250 words.
RULES: Hook with SPECIFIC problem understanding. No generic phrases. No fake stats. Focus on clarity, specificity, timeline.
Output ONLY proposal text, ready to submit."""

            # Ask Claude to generate proposal
            message = self.client.messages.create(
                model="claude-sonnet-4-5",  # CHANGED: Opus → Sonnet (40% savings)
                max_tokens=350,  # CHANGED: Reduced from 1000
                system=[
                    PromptCache.add_cache_control(system_instruction, ttl="ephemeral")  # ADDED: Caching
                ],
                messages=[
                    {
                        "role": "user",
                        "content": f"""Job: {job.get('title', 'N/A')}
Desc: {description_short}
Budget: {budget_range}
Skills: {required_skills}
Pain Points: {pain_points}

Generate under 250 words."""
                    }
                ]
            )

            proposal = message.content[0].text

            # Log cost for this API call
            cost_tracker.log_call(
                model="claude-sonnet-4-5",
                input_tokens=message.usage.input_tokens,
                output_tokens=message.usage.output_tokens,
                endpoint="generate_proposal",
                cached_tokens=message.usage.cache_read_input_tokens if hasattr(message.usage, 'cache_read_input_tokens') else 0
            )

            self.logger.info(f"Generated proposal for job {job.get('id')} (Sonnet, cached)")
            return proposal

        except Exception as e:
            self.logger.error(f"Error generating proposal: {e}")
            return self._generate_fallback_proposal(job)
    
    def _generate_fallback_proposal(self, job: Dict) -> str:
        """Generate a basic proposal as fallback"""
        return f"""
Thank you for posting this {job.get('title', 'project')}. I'm interested in helping.

I have extensive experience with {', '.join(job.get('skills', ['automation']))} and have successfully completed similar projects.

My Approach:
- Thorough understanding of your requirements
- Clear communication and timeline
- Professional and reliable delivery
- Ongoing support and optimization

I'm confident I can deliver excellent results for your project within your ${job.get('budget', 'stated')} budget.

I'd love to discuss how I can help achieve your goals. Looking forward to hearing from you.
"""
    
    def save_proposal(self, job: Dict, proposal: str, output_dir: str = '.tmp/proposals/') -> str:
        """
        Save proposal to file
        
        Returns:
            Path to saved proposal
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"{output_dir}{job.get('id', 'unknown')}_proposal.txt"
        
        # Add metadata header
        content = f"""================================================================================
UPWORK PROPOSAL - {job.get('title', 'Project')}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Job URL: {job.get('url', 'N/A')}
Client: {job.get('client', {}).get('name', 'N/A')}
Budget: ${job.get('budget', 'N/A')}
================================================================================

{proposal}

================================================================================
NOTES:
1. Copy the proposal text above (between the dashes)
2. Paste it into the Upwork proposal textbox
3. Add your name/sign-off at the top
4. Review for any personalization needed
5. Submit on Upwork
================================================================================
"""
        
        with open(filename, 'w') as f:
            f.write(content)
        
        self.logger.info(f"Saved proposal to {filename}")
        return filename
    
    def generate_proposals_batch(self, jobs: List[Dict], output_dir: str = '.tmp/proposals/') -> Dict:
        """
        Generate proposals for multiple jobs
        
        Returns:
            Summary dict with generated/failed counts
        """
        generated = 0
        failed = 0
        proposals = []
        
        for job in jobs:
            try:
                proposal = self.generate_proposal(job)
                proposal_file = self.save_proposal(job, proposal, output_dir)
                generated += 1
                proposals.append({
                    "job_id": job.get('id'),
                    "job_title": job.get('title'),
                    "proposal_file": proposal_file
                })
            except Exception as e:
                self.logger.error(f"Failed to generate proposal for job {job.get('id')}: {e}")
                failed += 1
        
        summary = {
            "total": len(jobs),
            "generated": generated,
            "failed": failed,
            "proposals": proposals,
            "generated_at": datetime.now().isoformat()
        }
        
        self.logger.info(f"Batch proposal generation complete: {generated} generated, {failed} failed")
        return summary
    
    def generate_proposal_from_clickup_task(self, task: Dict) -> str:
        """Generate proposal directly from a ClickUp task (for webhook integration)"""
        # Extract job details from ClickUp task custom fields
        job = {
            "id": task.get('id'),
            "title": task.get('name'),
            "description": task.get('description', ''),
            "budget": self._extract_custom_field(task, 'budget'),
            "skills": self._extract_custom_field(task, 'skills', []),
            "client": {
                "name": "Valued Client",
                "rating": self._extract_custom_field(task, 'client_rating')
            },
            "url": self._extract_custom_field(task, 'job_url')
        }
        
        return self.generate_proposal(job)
    
    def _extract_custom_field(self, task: Dict, field_name: str, default=None):
        """Extract custom field value from ClickUp task"""
        custom_fields = task.get('custom_fields', [])
        for field in custom_fields:
            if field.get('name') == field_name:
                return field.get('value', default)
        return default


def load_approved_jobs(filepath: str = '.tmp/clickup_approved_jobs.json') -> List[Dict]:
    """Load approved jobs from ClickUp export"""
    try:
        with open(filepath, 'r') as f:
            jobs = json.load(f)
        logger.info(f"Loaded {len(jobs)} approved jobs from {filepath}")
        return jobs
    except FileNotFoundError:
        logger.error(f"Approved jobs file not found: {filepath}")
        return []


def save_proposals_summary(summary: Dict, output_path: str = '.tmp/proposals_summary.json'):
    """Save proposals generation summary to file"""
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Saved proposals summary to {output_path}")


if __name__ == "__main__":
    # Load API key from environment
    api_key = os.getenv('ANTHROPIC_API_KEY')
    
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not found in .env file")
        exit(1)
    
    # Initialize proposal generator
    generator = ProposalGenerator(api_key)
    
    # Load approved jobs (you'd get these from ClickUp webhook or manual export)
    jobs = load_approved_jobs()
    
    if jobs:
        # Generate proposals
        summary = generator.generate_proposals_batch(jobs)
        
        # Save summary
        save_proposals_summary(summary)
    else:
        logger.warning("No approved jobs to generate proposals for")
