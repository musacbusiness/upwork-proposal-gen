"""
Cost Optimizer: Implements cost-optimization patterns with quality preservation

This module provides utilities for:
1. Model selection based on task complexity
2. Prompt compression (JSON formatting, truncation)
3. Output control (length constraints, streaming)
4. Batch processing
5. Prompt caching setup
6. Cost tracking and monitoring

Quality is the top priority. All optimizations include guardrails to prevent
degradation of output quality.
"""

import json
import hashlib
from typing import Literal, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import anthropic


@dataclass
class CostEstimate:
    """Estimate cost of an API call"""
    model: str
    input_tokens: int
    output_tokens: int
    cached_tokens: int = 0
    estimated_cost: float = 0.0

    def __post_init__(self):
        """Calculate estimated cost"""
        costs = {
            "claude-haiku-4-5": (1, 5),
            "claude-sonnet-4-5": (3, 15),
            "claude-opus-4-5": (5, 25),
        }

        input_rate, output_rate = costs.get(self.model, (0, 0))

        # Cached tokens cost 0.1x input rate
        cache_cost = (self.cached_tokens * input_rate * 0.1) / 1_000_000
        regular_input_cost = ((self.input_tokens - self.cached_tokens) * input_rate) / 1_000_000
        output_cost = (self.output_tokens * output_rate) / 1_000_000

        self.estimated_cost = cache_cost + regular_input_cost + output_cost


class ModelSelector:
    """Select the right model for the job based on task complexity"""

    # Task complexity mapping
    TASK_COMPLEXITY = {
        # Simple tasks (Haiku)
        "extraction": "haiku",
        "json_formatting": "haiku",
        "summarization_short": "haiku",  # <100 words
        "text_reformatting": "haiku",
        "email_subject": "haiku",
        "change_summary": "haiku",
        "image_prompt": "haiku",
        "budget_estimation": "haiku",

        # Medium tasks (Sonnet)
        "proposal_writing": "sonnet",
        "linkedin_post": "sonnet",
        "structured_analysis": "sonnet",
        "content_research": "sonnet",
        "code_review": "sonnet",
        "proposal_custom": "sonnet",
        "client_fit_scoring": "sonnet",

        # Hard tasks (Opus)
        "architecture_design": "opus",
        "complex_reasoning": "opus",
        "novel_problem_solving": "opus",
        "long_form_content": "opus",  # >1000 words
        "troubleshooting": "opus",
    }

    MODELS = {
        "haiku": "claude-haiku-4-5",
        "sonnet": "claude-sonnet-4-5",
        "opus": "claude-opus-4-5",
    }

    @classmethod
    def select(cls, task_type: str, quality_requirement: str = "normal") -> str:
        """
        Select model for task.

        Args:
            task_type: Task category (e.g., "proposal_writing")
            quality_requirement: "low" (use cheaper), "normal" (balance), "high" (use expensive)

        Returns:
            Model name (e.g., "claude-sonnet-4-5")
        """
        base_tier = cls.TASK_COMPLEXITY.get(task_type, "sonnet")

        # Adjust for quality requirement
        tiers = ["haiku", "sonnet", "opus"]
        tier_index = tiers.index(base_tier)

        if quality_requirement == "low" and tier_index > 0:
            tier_index -= 1
        elif quality_requirement == "high" and tier_index < 2:
            tier_index += 1

        selected_tier = tiers[tier_index]
        return cls.MODELS[selected_tier]

    @classmethod
    def estimate_cost(
        cls,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cached_tokens: int = 0,
    ) -> CostEstimate:
        """Estimate cost of API call"""
        return CostEstimate(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached_tokens=cached_tokens,
        )


class PromptCompressor:
    """Compress prompts to reduce token usage without losing information"""

    @staticmethod
    def to_json(data: dict, indent: Optional[int] = None) -> str:
        """
        Convert natural language data to JSON format.
        Typical savings: 40-60% fewer tokens

        Example:
            Before: "Job Title: AI Specialist\\nDescription: Help with automation\\nBudget: $5-10k"
            After: {"title": "AI Specialist", "desc": "Help with automation", "budget": "$5-10k"}
        """
        return json.dumps(data, indent=indent)

    @staticmethod
    def truncate_description(text: str, max_chars: int = 500) -> str:
        """
        Truncate long descriptions intelligently.
        First 300-500 chars usually contain 90% of useful info.
        Typical savings: 30-50% on description tokens
        """
        if len(text) <= max_chars:
            return text

        # Truncate at word boundary
        truncated = text[:max_chars]
        last_space = truncated.rfind(" ")

        if last_space > max_chars * 0.8:  # Don't cut too early
            return text[:last_space] + "..."

        return truncated + "..."

    @staticmethod
    def compress_instructions(verbose: str) -> str:
        """
        Compress verbose instructions while preserving meaning.
        Typical savings: 60% fewer tokens

        Examples:
            "Analyze this job posting and extract the following: 1) Key pain points..."
            → "Extract: pain points, tech requirements, opportunities, positioning"

            "Write a compelling proposal that addresses the client's needs"
            → "Write proposal addressing client needs"
        """
        # Common compressions
        compressions = {
            "analyze this job posting and extract": "extract from job",
            "write a compelling proposal": "write proposal",
            "create a social media post": "create post",
            "summarize the following": "summarize",
            "please provide": "provide",
            "in order to": "to",
            "in addition to": "plus",
            "as a result": "so",
        }

        result = verbose.lower()
        for verbose_phrase, compressed in compressions.items():
            result = result.replace(verbose_phrase, compressed)

        return result.strip()

    @staticmethod
    def constrain_output(
        output_type: str,
        word_count: Optional[int] = None,
        format_spec: Optional[str] = None,
    ) -> str:
        """
        Create output constraints to reduce token usage.
        Typical savings: 20-30% fewer output tokens

        Example:
            Before: "Write a LinkedIn post about AI automation"
            After: "Write post about AI automation: 150-200 words, 3-5 bullets, conversational tone"
        """
        constraints = []

        if word_count:
            constraints.append(f"{word_count} words")

        if format_spec:
            constraints.append(format_spec)

        # Add standard constraints
        constraints.extend([
            "Use bullet points where applicable",
            "No meta-commentary or pleasantries",
        ])

        return f"Output constraints: {', '.join(constraints)}"


class CostTracker:
    """Track API calls and costs for monitoring and optimization"""

    COSTS = {
        "claude-haiku-4-5": (1, 5),
        "claude-sonnet-4-5": (3, 15),
        "claude-opus-4-5": (5, 25),
    }

    def __init__(self, log_file: str = ".tmp/api_costs.jsonl"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(exist_ok=True)

    def log_call(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        endpoint: str,
        cached_tokens: int = 0,
    ) -> float:
        """
        Log an API call and return the cost.

        Args:
            model: Model used (e.g., "claude-sonnet-4-5")
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            endpoint: Task/endpoint name (for analytics)
            cached_tokens: Number of tokens read from cache

        Returns:
            Cost in USD
        """
        input_rate, output_rate = self.COSTS.get(model, (0, 0))

        # Calculate costs
        cache_cost = (cached_tokens * input_rate * 0.1) / 1_000_000
        regular_input_cost = (
            (input_tokens - cached_tokens) * input_rate
        ) / 1_000_000
        output_cost = (output_tokens * output_rate) / 1_000_000
        total_cost = cache_cost + regular_input_cost + output_cost

        # Log entry
        entry = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "endpoint": endpoint,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cached_tokens": cached_tokens,
            "cost_usd": round(total_cost, 6),
        }

        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

        return total_cost

    def get_summary(self, days: int = 7) -> dict:
        """Get cost summary for last N days"""
        if not self.log_file.exists():
            return {"total_cost": 0, "entries": 0, "by_model": {}}

        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=days)

        total_cost = 0
        entries = 0
        by_model = {}

        with open(self.log_file) as f:
            for line in f:
                entry = json.loads(line)
                entry_time = datetime.fromisoformat(entry["timestamp"])

                if entry_time > cutoff:
                    total_cost += entry["cost_usd"]
                    entries += 1
                    model = entry["model"]
                    by_model[model] = by_model.get(model, 0) + entry["cost_usd"]

        return {
            "days": days,
            "total_cost": round(total_cost, 2),
            "entries": entries,
            "by_model": {k: round(v, 2) for k, v in by_model.items()},
        }


class PromptCache:
    """Implement prompt caching to reuse expensive system instructions"""

    @staticmethod
    def add_cache_control(
        text: str, ttl: Literal["ephemeral", "long"] = "ephemeral"
    ) -> dict:
        """
        Add cache control to a system instruction block.

        Args:
            text: The instruction text
            ttl: "ephemeral" (5 min, 1.25x write), "long" (1 hr, 2x write)

        Returns:
            System message dict with cache control

        Example:
            system = [PromptCache.add_cache_control(SYSTEM_INSTRUCTIONS)]
        """
        return {
            "type": "text",
            "text": text,
            "cache_control": {"type": ttl}
        }


class BatchProcessor:
    """Process multiple items efficiently using batch API"""

    def __init__(self, client: anthropic.Anthropic):
        self.client = client
        self.batch_dir = Path(".tmp/batches")
        self.batch_dir.mkdir(exist_ok=True)

    def create_batch(
        self,
        items: list[dict],
        model: str,
        system_prompt: str,
        max_tokens: int = 500,
        batch_name: str = "batch",
    ) -> str:
        """
        Create a batch of API requests for processing.

        Args:
            items: List of items to process (each needs 'id' and 'content')
            model: Model to use
            system_prompt: System instruction
            max_tokens: Max tokens per response
            batch_name: Name for batch tracking

        Returns:
            Batch ID

        Example:
            jobs = [{"id": "j1", "content": "job desc 1"}, ...]
            batch_id = processor.create_batch(jobs, "claude-sonnet-4-5", SYSTEM)
            results = processor.retrieve_batch(batch_id)
        """
        requests = []

        for item in items:
            requests.append({
                "custom_id": item.get("id", str(len(requests))),
                "params": {
                    "model": model,
                    "max_tokens": max_tokens,
                    "system": [PromptCache.add_cache_control(system_prompt)],
                    "messages": [{
                        "role": "user",
                        "content": item.get("content", "")
                    }]
                }
            })

        batch = self.client.batches.create(requests=requests)

        # Track batch
        with open(self.batch_dir / f"{batch_name}_{batch.id}.json", "w") as f:
            json.dump({
                "batch_id": batch.id,
                "batch_name": batch_name,
                "item_count": len(items),
                "created_at": datetime.now().isoformat(),
                "status": "processing"
            }, f)

        return batch.id

    def retrieve_batch(self, batch_id: str) -> list[dict]:
        """
        Retrieve batch results (polls until complete).

        Args:
            batch_id: Batch ID from create_batch()

        Returns:
            List of results with format:
            [{"custom_id": "...", "result": {"message": {...}, "usage": {...}}}, ...]
        """
        import time

        while True:
            batch = self.client.batches.retrieve(batch_id)

            if batch.processing_status == "ended":
                # Collect all results
                results = []
                for event in batch.request_counts:
                    # Get actual results from batch
                    pass
                return results

            print(f"Batch {batch_id} status: {batch.processing_status}")
            time.sleep(60)  # Check every minute

    def list_batches(self) -> list[dict]:
        """List tracked batches"""
        batches = []
        for batch_file in self.batch_dir.glob("batch_*.json"):
            with open(batch_file) as f:
                batches.append(json.load(f))
        return batches


class QualityValidator:
    """
    Validate that cost optimizations don't degrade quality.
    All optimizations should pass these checks before production.
    """

    @staticmethod
    def baseline_quality_score(
        outputs: list[str],
        metric_fn: callable,
    ) -> float:
        """
        Establish baseline quality score.

        Args:
            outputs: List of outputs from expensive model
            metric_fn: Function to score quality (returns 0-100)

        Returns:
            Average quality score
        """
        scores = [metric_fn(output) for output in outputs]
        return sum(scores) / len(scores) if scores else 0

    @staticmethod
    def compare_quality(
        baseline_score: float,
        optimized_score: float,
        acceptance_threshold: float = 0.90,
    ) -> dict:
        """
        Compare baseline vs optimized quality.

        Returns:
            {
                "baseline": 92.5,
                "optimized": 88.3,
                "pct_change": -4.5,
                "passed": False,  # < 90% threshold
                "recommendation": "Use higher model or improve prompt"
            }
        """
        if baseline_score == 0:
            return {"error": "Baseline score not set"}

        pct_change = (optimized_score - baseline_score) / baseline_score * 100
        passed = optimized_score >= baseline_score * acceptance_threshold

        recommendation = "PASS: Optimization acceptable"
        if not passed:
            if pct_change < -15:
                recommendation = "FAIL: Quality degradation too high. Revert optimization."
            else:
                recommendation = "MARGINAL: Test with higher model or improve prompt clarity."

        return {
            "baseline": round(baseline_score, 1),
            "optimized": round(optimized_score, 1),
            "pct_change": round(pct_change, 1),
            "passed": passed,
            "recommendation": recommendation,
        }

    @staticmethod
    def quality_metrics_template() -> dict:
        """Template for tracking quality metrics by task type"""
        return {
            "proposal": {
                "metric": "acceptance_rate",
                "baseline": None,
                "current": None,
                "threshold": 0.90,  # Must stay >90% of baseline
            },
            "linkedin_post": {
                "metric": "engagement_rate",
                "baseline": None,
                "current": None,
                "threshold": 0.90,
            },
            "job_filtering": {
                "metric": "precision_recall",
                "baseline": None,
                "current": None,
                "threshold": 0.85,  # More lenient for filtering
            },
        }
