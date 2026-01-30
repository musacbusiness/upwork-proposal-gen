import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../logs/upwork_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class JobFilter:
    """Filter Upwork jobs based on criteria"""
    
    def __init__(self, filter_config: Dict):
        """
        Initialize filter with configuration
        
        Args:
            filter_config: Dictionary with filter criteria (budget, rating, skills, etc.)
        """
        self.config = filter_config
        self.logger = logger
    
    def load_raw_jobs(self, filepath: str) -> List[Dict]:
        """Load raw jobs from JSON file"""
        try:
            with open(filepath, 'r') as f:
                jobs = json.load(f)
            self.logger.info(f"Loaded {len(jobs)} raw jobs from {filepath}")
            return jobs
        except FileNotFoundError:
            self.logger.error(f"Jobs file not found: {filepath}")
            return []
    
    def check_budget(self, job: Dict) -> bool:
        """Check if job budget is within acceptable range"""
        budget = job.get('budget', 0)
        min_budget = self.config.get('budget', {}).get('min', 0)
        max_budget = self.config.get('budget', {}).get('max', float('inf'))
        
        # Handle both fixed and hourly rates
        if isinstance(budget, dict):
            budget = budget.get('amount', 0)
        
        return min_budget <= budget <= max_budget
    
    def check_client_rating(self, job: Dict) -> bool:
        """Check if client rating is acceptable"""
        rating = job.get('client', {}).get('rating', 0)
        min_rating = self.config.get('client_rating', {}).get('min', 0)
        return rating >= min_rating
    
    def check_client_reviews(self, job: Dict) -> bool:
        """Check if client has minimum number of reviews"""
        reviews = job.get('client', {}).get('reviews', 0)
        min_reviews = self.config.get('client_reviews', {}).get('min', 0)
        return reviews >= min_reviews
    
    def check_job_category(self, job: Dict) -> bool:
        """Check if job category matches allowed categories"""
        allowed_categories = self.config.get('job_category', [])
        if not allowed_categories:
            return True  # No restriction if empty
        
        job_category = job.get('category', '')
        return job_category in allowed_categories
    
    def check_required_skills(self, job: Dict) -> bool:
        """Check if job requires minimum required skills"""
        required_skills = set(self.config.get('skills_required', []))
        if not required_skills:
            return True  # No restriction if empty
        
        job_skills = set(job.get('skills', []))
        # At least one required skill must be in the job
        return bool(required_skills & job_skills)
    
    def check_exclude_keywords(self, job: Dict) -> bool:
        """Check if job contains excluded keywords"""
        excluded = self.config.get('exclude_keywords', [])
        if not excluded:
            return True
        
        job_text = (job.get('title', '') + ' ' + job.get('description', '')).lower()
        for keyword in excluded:
            if keyword.lower() in job_text:
                return False
        return True
    
    def check_proposals_required(self, job: Dict) -> bool:
        """Check if proposals count is within acceptable range"""
        proposals = job.get('proposals_required', float('inf'))
        max_proposals = self.config.get('proposals_required', {}).get('max', float('inf'))
        return proposals <= max_proposals
    
    def check_job_type(self, job: Dict) -> bool:
        """Check if job type matches (fixed-price vs hourly)"""
        allowed_types = self.config.get('job_type', [])
        if not allowed_types:
            return True
        
        job_type = job.get('type', '')
        return job_type in allowed_types if isinstance(allowed_types, list) else job_type == allowed_types
    
    def calculate_job_score(self, job: Dict) -> float:
        """
        Calculate a score (0-100) for how good a job fit is
        Higher score = better fit
        """
        score = 50  # Base score
        
        # Budget score (±20 points)
        budget = job.get('budget', 0)
        if isinstance(budget, dict):
            budget = budget.get('amount', 0)
        
        min_budget = self.config.get('budget', {}).get('min', 0)
        max_budget = self.config.get('budget', {}).get('max', 10000)
        
        if budget >= min_budget and budget <= max_budget:
            # Scale: jobs at max_budget get +20, at min get 0
            budget_score = ((budget - min_budget) / (max_budget - min_budget)) * 20
            score += min(budget_score, 20)
        
        # Client rating score (±15 points)
        rating = job.get('client', {}).get('rating', 0)
        min_rating = self.config.get('client_rating', {}).get('min', 0)
        if rating >= 4.5:
            score += 15
        elif rating >= 4.0:
            score += 10
        elif rating >= min_rating:
            score += 5
        
        # Client reviews score (±10 points)
        reviews = job.get('client', {}).get('reviews', 0)
        if reviews >= 100:
            score += 10
        elif reviews >= 50:
            score += 5
        
        # Proposals required score (±15 points)
        proposals = job.get('proposals_required', 50)
        if proposals <= 10:
            score += 15
        elif proposals <= 20:
            score += 10
        elif proposals <= 50:
            score += 5
        
        # Skills match score (±10 points)
        required_skills = set(self.config.get('skills_required', []))
        job_skills = set(job.get('skills', []))
        if required_skills:
            match_ratio = len(required_skills & job_skills) / len(required_skills)
            score += match_ratio * 10
        
        return min(100, max(0, score))
    
    def filter_job(self, job: Dict) -> tuple[bool, str, float]:
        """
        Filter a single job based on all criteria
        
        Returns:
            (passes_filter, reason, score)
        """
        checks = [
            (self.check_budget, "Budget out of range"),
            (self.check_client_rating, "Client rating too low"),
            (self.check_client_reviews, "Client has insufficient reviews"),
            (self.check_job_category, "Job category not allowed"),
            (self.check_required_skills, "Missing required skills"),
            (self.check_exclude_keywords, "Contains excluded keywords"),
            (self.check_proposals_required, "Too many proposals required"),
            (self.check_job_type, "Job type not allowed"),
        ]
        
        for check_func, failure_reason in checks:
            if not check_func(job):
                score = self.calculate_job_score(job)
                return False, failure_reason, score
        
        score = self.calculate_job_score(job)
        return True, "Passed all filters", score
    
    def filter_jobs(self, jobs: List[Dict]) -> tuple[List[Dict], List[Dict]]:
        """
        Filter all jobs and return accepted and rejected lists
        
        Returns:
            (accepted_jobs, rejected_jobs)
        """
        accepted = []
        rejected = []
        
        for job in jobs:
            passes, reason, score = self.filter_job(job)
            
            job['filter_score'] = score
            job['filter_reason'] = reason
            job['filtered_at'] = datetime.now().isoformat()
            
            if passes:
                accepted.append(job)
                self.logger.info(f"✓ Job {job.get('id')} ACCEPTED (Score: {score:.1f}) - {job.get('title', 'N/A')[:50]}")
            else:
                rejected.append(job)
                self.logger.debug(f"✗ Job {job.get('id')} REJECTED ({reason}) - {job.get('title', 'N/A')[:50]}")
        
        self.logger.info(f"Filtering complete: {len(accepted)} accepted, {len(rejected)} rejected out of {len(jobs)} total")
        return accepted, rejected
    
    def save_filtered_jobs(self, accepted: List[Dict], rejected: List[Dict], output_prefix: str = '.tmp/'):
        """Save filtered jobs to JSON files"""
        # Sort by score descending
        accepted_sorted = sorted(accepted, key=lambda x: x.get('filter_score', 0), reverse=True)
        
        # Save accepted
        accepted_file = f"{output_prefix}filtered_jobs_accepted.json"
        with open(accepted_file, 'w') as f:
            json.dump(accepted_sorted, f, indent=2)
        self.logger.info(f"Saved {len(accepted_sorted)} accepted jobs to {accepted_file}")
        
        # Save rejected
        rejected_file = f"{output_prefix}filtered_jobs_rejected.json"
        with open(rejected_file, 'w') as f:
            json.dump(rejected, f, indent=2)
        self.logger.info(f"Saved {len(rejected)} rejected jobs to {rejected_file}")
        
        return accepted_file, rejected_file


def load_filter_config(config_path: str = 'config/filter_rules.json') -> Dict:
    """Load filter configuration from JSON file"""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Filter config not found at {config_path}, using defaults")
        return get_default_filter_config()


def get_default_filter_config() -> Dict:
    """Return default filter configuration"""
    return {
        "budget": {"min": 500, "max": 10000},
        "client_rating": {"min": 4.5},
        "client_reviews": {"min": 50},
        "job_category": ["Web Development", "Automation"],
        "skills_required": ["Python"],
        "exclude_keywords": ["blockchain", "ai training"],
        "proposals_required": {"max": 50},
        "job_type": "fixed-price"
    }


if __name__ == "__main__":
    # Example usage
    config = load_filter_config()
    filter_engine = JobFilter(config)
    
    # Load raw jobs
    raw_jobs = filter_engine.load_raw_jobs('.tmp/raw_jobs.json')
    
    if raw_jobs:
        # Filter jobs
        accepted, rejected = filter_engine.filter_jobs(raw_jobs)
        
        # Save results
        filter_engine.save_filtered_jobs(accepted, rejected)
    else:
        logger.warning("No jobs to filter")
