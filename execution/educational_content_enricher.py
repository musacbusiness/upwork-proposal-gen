"""
Educational Content Enricher - Generates instructional content using Claude API

Provides methods to enhance template-based post generation with dynamic educational content:
- Specific, copyable examples
- Step-by-step instructions
- Before/after comparisons
- Adaptable templates

Uses Haiku 4.5 for cost efficiency (80% cheaper than Sonnet) with quality validation.
"""

import os
import sys
from pathlib import Path
from typing import Optional, List, Dict
import anthropic

sys.path.insert(0, str(Path(__file__).parent))
from utils.cost_optimizer import ModelSelector, CostTracker, PromptCache


class EducationalContentEnricher:
    """Generate instructional content using Claude API."""

    def __init__(self):
        """Initialize enricher with Anthropic client and cost tracking."""
        # Load environment variables
        env_file = "/Users/musacomma/Agentic Workflow/.env"
        if os.path.exists(env_file):
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip().strip('\"\'')

        self.client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
        self.cost_tracker = CostTracker()

        # Use Haiku 4.5 for educational content (simple extraction/formatting)
        self.model = ModelSelector.select("extraction", quality_requirement="normal")

        # System prompt for all enrichment tasks
        self.system_prompt = """You are an expert business educator creating specific, actionable content for business owners.

Your content must be:
- Concrete and specific (never use placeholders like {company} or {product})
- Immediately actionable (copy-paste ready)
- Realistic and believable
- Tailored for business owners learning AI and automation

Generate exactly what is requested. No explanations or meta-commentary."""

    def generate_examples(
        self,
        topic: str,
        context: str = "",
        count: int = 2
    ) -> List[str]:
        """
        Generate specific, copyable examples for a topic.

        Args:
            topic: The educational topic (e.g., "Chain-of-Thought Prompting")
            context: Additional context about the post (e.g., target audience, pain point)
            count: Number of examples to generate (default 2, optimized for LinkedIn)

        Returns:
            List of specific examples ready to copy-paste
        """
        prompt = f"""Topic: {topic}
Context: {context}

Generate {count} specific, realistic examples that business owners can use immediately.
Keep each example concise - max 2-3 sentences per example.
Each example should be concrete, actionable, and copy-paste ready.

Format each example as:
**Example [number]: [Scenario]**
[Exact technique/prompt/code/method - keep concise]

Requirements:
- No placeholders like {{company}}, {{product}}, {{year}} - use realistic details
- Each example shows a real business scenario
- Make examples immediately usable
- IMPORTANT: Keep examples SHORT and punchy (not long-winded)"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                system=[PromptCache.add_cache_control(self.system_prompt)],
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Track cost
            self.cost_tracker.log_call(
                model=self.model,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                endpoint="generate_examples",
                cached_tokens=getattr(response.usage, 'cache_read_input_tokens', 0)
            )

            # Parse response - split by **Example [number]** markers
            content = response.content[0].text
            examples = []

            # Split by example markers
            parts = content.split('\n**Example ')
            for part in parts[1:]:  # Skip the first empty part
                # Extract just the example content
                if '**' in part:
                    example = part.split('**', 1)[1].strip()
                    examples.append(example)
                else:
                    examples.append(part.strip())

            return examples[:count]

        except Exception as e:
            print(f"⚠️  Error generating examples: {str(e)}")
            return []

    def generate_steps(
        self,
        topic: str,
        context: str = "",
        count: int = 3
    ) -> List[str]:
        """
        Generate step-by-step instructions for implementing a technique.

        Args:
            topic: The educational topic
            context: Additional context
            count: Number of steps (default 3, optimized for LinkedIn)

        Returns:
            List of numbered, actionable steps with examples
        """
        prompt = f"""Topic: {topic}
Context: {context}

Generate {count} numbered steps for implementing this technique or process.
Keep each step SHORT and actionable (2-3 sentences max per step).
Include a brief concrete example for each step.

Format as:
1. [Step Name] - [Brief description of what to do]
   Example: [One specific, concise example]

Requirements:
- Steps must be sequential and logical
- Each step should be completable in under 15 minutes
- Be concrete but CONCISE - no long explanations
- Include actual values/names (not placeholders)
- IMPORTANT: Keep the entire response under 400 characters total"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                system=[PromptCache.add_cache_control(self.system_prompt)],
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Track cost
            self.cost_tracker.log_call(
                model=self.model,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                endpoint="generate_steps",
                cached_tokens=getattr(response.usage, 'cache_read_input_tokens', 0)
            )

            # Parse numbered steps
            content = response.content[0].text
            steps = []

            lines = content.split('\n')
            current_step = []

            for line in lines:
                # Check if line starts with a number (new step)
                if line and line[0].isdigit() and '.' in line[:3]:
                    if current_step:
                        steps.append('\n'.join(current_step).strip())
                    current_step = [line]
                elif line.strip():
                    current_step.append(line)

            if current_step:
                steps.append('\n'.join(current_step).strip())

            return steps[:count]

        except Exception as e:
            print(f"⚠️  Error generating steps: {str(e)}")
            return []

    def generate_before_after(
        self,
        topic: str,
        context: str = ""
    ) -> Dict[str, str]:
        """
        Generate before/after comparison showing transformation.

        Args:
            topic: The educational topic
            context: Additional context

        Returns:
            Dict with 'before', 'after', and 'key_differences'
        """
        prompt = f"""Topic: {topic}
Context: {context}

Generate a realistic before/after comparison showing clear transformation.

Use this exact format:

BEFORE:
[Specific example of the wrong/old way]

AFTER:
[Specific example of the right/new way]

KEY DIFFERENCES:
- [What changed]
- [Specific improvement]
- [Quantifiable benefit]

Requirements:
- Use realistic business scenarios
- Show tangible difference in outcomes
- Make it immediately clear why "after" is better
- Include actual numbers/metrics where possible
- Both examples should be copy-paste ready"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1200,
                system=[PromptCache.add_cache_control(self.system_prompt)],
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Track cost
            self.cost_tracker.log_call(
                model=self.model,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                endpoint="generate_before_after",
                cached_tokens=getattr(response.usage, 'cache_read_input_tokens', 0)
            )

            content = response.content[0].text

            # Parse before/after/key differences
            result = {
                "before": "",
                "after": "",
                "key_differences": ""
            }

            # Split by section headers
            sections = content.split('\n')
            current_section = None
            current_content = []

            for line in sections:
                line_upper = line.upper().strip()
                if 'BEFORE:' in line_upper:
                    if current_content and current_section:
                        result[current_section] = '\n'.join(current_content).strip()
                    current_section = 'before'
                    current_content = []
                elif 'AFTER:' in line_upper:
                    if current_content and current_section:
                        result[current_section] = '\n'.join(current_content).strip()
                    current_section = 'after'
                    current_content = []
                elif 'KEY' in line_upper and 'DIFFERENCE' in line_upper:
                    if current_content and current_section:
                        result[current_section] = '\n'.join(current_content).strip()
                    current_section = 'key_differences'
                    current_content = []
                elif line.strip() and current_section:
                    current_content.append(line)

            if current_content and current_section:
                result[current_section] = '\n'.join(current_content).strip()

            return result

        except Exception as e:
            print(f"⚠️  Error generating before/after: {str(e)}")
            return {
                "before": "",
                "after": "",
                "key_differences": ""
            }

    def generate_template(
        self,
        topic: str,
        context: str = ""
    ) -> Dict[str, str]:
        """
        Generate an adaptable template business owners can customize.

        Args:
            topic: The educational topic
            context: Additional context

        Returns:
            Dict with 'template_name', 'template_content', and 'customization_guide'
        """
        prompt = f"""Topic: {topic}
Context: {context}

Create a complete, ready-to-use template that business owners can adapt for their specific needs.

Use this exact format:

TEMPLATE NAME:
[Clear, descriptive name]

TEMPLATE:
[Complete template with clear sections and placeholders clearly marked with [SECTION NAME]]

HOW TO CUSTOMIZE:
1. [First customization step - what to change]
2. [Second customization step - what to change]
3. [Third customization step - what to change]

EXAMPLE IN USE:
[Show the template filled in with a realistic example]

Requirements:
- Template should be functional as-is
- Use [BRACKETS] only for clear customization points
- Include realistic section names
- Example should show actual use case
- No vague instructions"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                system=[PromptCache.add_cache_control(self.system_prompt)],
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Track cost
            self.cost_tracker.log_call(
                model=self.model,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                endpoint="generate_template",
                cached_tokens=getattr(response.usage, 'cache_read_input_tokens', 0)
            )

            content = response.content[0].text

            # Parse template sections
            result = {
                "template_name": "",
                "template_content": "",
                "customization_guide": "",
                "example": ""
            }

            sections = content.split('\n')
            current_section = None
            current_content = []

            for line in sections:
                line_upper = line.upper().strip()
                if 'TEMPLATE NAME:' in line_upper:
                    if current_content and current_section:
                        result[current_section] = '\n'.join(current_content).strip()
                    current_section = 'template_name'
                    current_content = []
                elif line_upper.startswith('TEMPLATE:') and 'NAME' not in line_upper:
                    if current_content and current_section:
                        result[current_section] = '\n'.join(current_content).strip()
                    current_section = 'template_content'
                    current_content = []
                elif 'CUSTOMIZE' in line_upper:
                    if current_content and current_section:
                        result[current_section] = '\n'.join(current_content).strip()
                    current_section = 'customization_guide'
                    current_content = []
                elif 'EXAMPLE' in line_upper:
                    if current_content and current_section:
                        result[current_section] = '\n'.join(current_content).strip()
                    current_section = 'example'
                    current_content = []
                elif line.strip() and current_section:
                    current_content.append(line)

            if current_content and current_section:
                result[current_section] = '\n'.join(current_content).strip()

            return result

        except Exception as e:
            print(f"⚠️  Error generating template: {str(e)}")
            return {
                "template_name": "",
                "template_content": "",
                "customization_guide": "",
                "example": ""
            }

    def generate_automation_showcase(
        self,
        automation_name: str,
        context: str = ""
    ) -> Dict[str, str]:
        """Generate content showcasing a specific automation with operational details.

        Args:
            automation_name: Name of the automation (e.g., "Proposal Generation Automation")
            context: Additional context about the use case

        Returns:
            Dict with 'how_it_works', 'problems_solved', 'workflow_improvement', and 'example'
        """
        prompt = f"""Automation: {automation_name}
Context: {context}

Create a detailed showcase of this business automation that helps business owners understand:
1. HOW IT WORKS - The operational breakdown
2. PROBLEMS SOLVED - What specific business problems it eliminates
3. WORKFLOW IMPROVEMENT - Time saved and process improvements
4. REAL EXAMPLE - A realistic business scenario showing the before/after

Use this exact format:

HOW IT WORKS:
[Step-by-step breakdown of how the automation operates, 3-4 bullets]

PROBLEMS SOLVED:
[Specific problems this automation eliminates, 3 bullets]

WORKFLOW IMPROVEMENT:
[Time saved per week/month, errors reduced, efficiency gains]
[Include specific numbers where possible]

REAL EXAMPLE:
[Name and business type]: [Specific scenario showing time saved and improvement]

Requirements:
- Be specific and operational (explain actual workflow, not abstract concepts)
- Include concrete numbers (hours saved per week, % reduction in errors, etc.)
- Make it immediately relatable to business owners
- Use realistic business scenarios (not fictional)
- Keep language clear and jargon-free"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                system=[PromptCache.add_cache_control(self.system_prompt)],
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Track cost
            self.cost_tracker.log_call(
                model=self.model,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                endpoint="generate_automation_showcase",
                cached_tokens=getattr(response.usage, 'cache_read_input_tokens', 0)
            )

            content = response.content[0].text

            # Parse showcase sections
            result = {
                "how_it_works": "",
                "problems_solved": "",
                "workflow_improvement": "",
                "example": ""
            }

            sections = content.split('\n')
            current_section = None
            current_content = []

            for line in sections:
                line_upper = line.upper().strip()
                if 'HOW IT WORKS:' in line_upper:
                    if current_content and current_section:
                        result[current_section] = '\n'.join(current_content).strip()
                    current_section = 'how_it_works'
                    current_content = []
                elif 'PROBLEMS SOLVED:' in line_upper:
                    if current_content and current_section:
                        result[current_section] = '\n'.join(current_content).strip()
                    current_section = 'problems_solved'
                    current_content = []
                elif 'WORKFLOW IMPROVEMENT:' in line_upper or 'WORKFLOW' in line_upper and 'IMPROVE' in line_upper:
                    if current_content and current_section:
                        result[current_section] = '\n'.join(current_content).strip()
                    current_section = 'workflow_improvement'
                    current_content = []
                elif 'REAL EXAMPLE:' in line_upper or 'EXAMPLE:' in line_upper:
                    if current_content and current_section:
                        result[current_section] = '\n'.join(current_content).strip()
                    current_section = 'example'
                    current_content = []
                elif line.strip() and current_section:
                    current_content.append(line)

            if current_content and current_section:
                result[current_section] = '\n'.join(current_content).strip()

            return result

        except Exception as e:
            print(f"⚠️  Error generating automation showcase: {str(e)}")
            return {
                "how_it_works": "",
                "problems_solved": "",
                "workflow_improvement": "",
                "example": ""
            }

    def get_cost_summary(self, days: int = 7) -> dict:
        """Get cost summary for educational content enrichment."""
        return self.cost_tracker.get_summary(days=days)


# Test the enricher
if __name__ == "__main__":
    print("🧪 Testing Educational Content Enricher\n")

    enricher = EducationalContentEnricher()

    # Test with a sample topic
    topic = "Chain-of-Thought Prompting for Business Owners"
    context = "Teaching business owners how to structure AI prompts for better results"

    print(f"📝 Topic: {topic}\n")

    # Test examples
    print("1️⃣  Generating Examples...")
    examples = enricher.generate_examples(topic, context, count=2)
    for i, example in enumerate(examples, 1):
        print(f"\n{example}\n")

    # Test steps
    print("\n2️⃣  Generating Steps...")
    steps = enricher.generate_steps(topic, context, count=3)
    for step in steps:
        print(f"\n{step}\n")

    # Test before/after
    print("\n3️⃣  Generating Before/After...")
    before_after = enricher.generate_before_after(topic, context)
    print(f"\nBEFORE:\n{before_after['before']}")
    print(f"\nAFTER:\n{before_after['after']}")
    print(f"\nKEY DIFFERENCES:\n{before_after['key_differences']}")

    # Test template
    print("\n4️⃣  Generating Template...")
    template = enricher.generate_template(topic, context)
    print(f"\nTemplate Name: {template['template_name']}")
    print(f"\nTemplate:\n{template['template_content']}")
    print(f"\nCustomization Guide:\n{template['customization_guide']}")
    print(f"\nExample:\n{template['example']}")

    # Cost summary
    print("\n💰 Cost Summary:")
    summary = enricher.get_cost_summary(days=1)
    print(f"Total API cost (today): ${summary['total_cost']}")
    print(f"API calls made: {summary['entries']}")
