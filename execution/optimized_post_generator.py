"""
Optimized LinkedIn Post Generator
Integrates all post optimization research:
- Topic selection (weighted randomization)
- Writing frameworks
- Hook templates
- Visual specifications
- CTA strategies
- Algorithm optimization
"""

import os
import sys
import json
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import requests

# Add execution directory to path
sys.path.insert(0, str(Path(__file__).parent))
from topic_performance_analyzer import TopicPerformanceAnalyzer
from educational_content_enricher import EducationalContentEnricher

class OptimizedPostGenerator:
    """Generates LinkedIn posts with all optimization best practices."""

    def __init__(self):
        """Initialize the generator with all specs."""
        # Load environment
        env_file = "/Users/musacomma/Agentic Workflow/.env"
        if os.path.exists(env_file):
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip().strip('"\'')

        self.analyzer = TopicPerformanceAnalyzer()
        self.specs = self._load_specs()
        self.enricher = EducationalContentEnricher()  # For educational content generation
        self.airtable_api_key = os.environ.get('AIRTABLE_API_KEY')
        self.airtable_base_id = os.environ.get('AIRTABLE_BASE_ID')
        self.airtable_table_id = os.environ.get('AIRTABLE_LINKEDIN_TABLE_ID')
        self.headers = {
            "Authorization": f"Bearer {self.airtable_api_key}",
            "Content-Type": "application/json"
        }

        # LinkedIn optimal post length (2025 data)
        self.OPTIMAL_POST_LENGTH = 1600  # Target 1,200-1,800 characters

    def _load_specs(self) -> Dict:
        """Load POST_GENERATION_SPEC.json"""
        spec_file = Path(__file__).parent.parent / 'POST_GENERATION_SPEC.json'
        if not spec_file.exists():
            print(f"Warning: Spec file not found at {spec_file}")
            return {}
        with open(spec_file) as f:
            data = json.load(f)
            return data.get('post_generation_spec', data)

    def select_framework(self) -> str:
        """Randomly select a writing framework."""
        frameworks = [f['name'] for f in self.specs['writing_frameworks']]
        return random.choice(frameworks)

    def map_framework_to_airtable(self, framework: str) -> str:
        """Map internal framework names to Airtable dropdown values.

        Airtable Writing Framework options:
        - PAS (Problem-Agitate-Solution)
        - AIDA (Attention-Interest-Desire-Action)
        - BAB (Before-After-Bridge)
        - Storytelling
        - How-To Guide
        - Listicle
        - Case Study
        - Question-Answer
        """
        mapping = {
            'PAS': 'PAS (Problem-Agitate-Solution)',
            'AIDA': 'AIDA (Attention-Interest-Desire-Action)',
            'BAB': 'BAB (Before-After-Bridge)',
            'Framework': 'How-To Guide',  # Step-by-step framework
            'Contrarian': 'Listicle',  # Contrarian take with list format
        }
        return mapping.get(framework, framework)  # Fallback to original if not in mapping

    def select_hook_type(self) -> str:
        """Select hook type with priority weighting (question-first strategy).

        Research shows questions drive 5-7x more engagement than other hook types.
        Use weighted selection: 40% question, then 20% each for other top performers.
        Uses only hook types that have templates defined.
        """
        # Get actual available hook templates (these are the ones that can be used)
        hook_types = list(self.specs.get('hook_templates', {}).keys())

        if not hook_types:
            raise ValueError("No hook templates found in specs")

        # Apply weighted selection: 40% question, 20% number_data, distribute rest
        if 'question' in hook_types:
            weights = []
            for h in hook_types:
                if h == 'question':
                    weights.append(40)  # 40% weight to questions (5-7x engagement)
                elif h == 'number_data':
                    weights.append(20)  # 20% weight to data/stats (credibility)
                else:
                    # Distribute remaining 40% across other types
                    weights.append(40 / (len(hook_types) - 2))

            return random.choices(hook_types, weights=weights, k=1)[0]

        # Fallback if question not available (shouldn't happen with current spec)
        return random.choice(hook_types)

    def select_visual_type(self, post_type: str) -> Dict:
        """Select appropriate visual type based on post type."""
        visual_types = self.specs['content_mix'][post_type]['visual_type']
        selected_type = random.choice(visual_types)

        # Get visual details from spec
        if selected_type == 'carousel':
            return {
                'type': 'carousel_pdf',
                'engagement_rate': '24.42%',
                'dimensions': '1080 x 1350 px (4:5)',
                'slides': '8-12',
                'structure': 'Hook | Value (one point/slide) | CTA'
            }
        elif selected_type == 'data_visualization':
            return {
                'type': 'data_visualization',
                'engagement_rate': '650% vs text-only',
                'dimensions': '1200 x 1350 px (4:5)',
                'content': 'Infographic, chart, or graph'
            }
        elif selected_type == 'personal_photo':
            return {
                'type': 'personal_photo',
                'engagement_boost': '+30%',
                'dimensions': '1200 x 1350 px (4:5)',
                'content': 'Behind-the-scenes, authentic moment'
            }
        elif selected_type == 'multi_image':
            return {
                'type': 'multi_image',
                'engagement_rate': '6.60%',
                'dimensions': '1200 x 1350 px (4:5)',
                'images': '3-4 images',
                'content': 'Before/after or process breakdown'
            }
        elif selected_type == 'results_screenshot':
            return {
                'type': 'results_screenshot',
                'dimensions': '1200 x 1350 px (4:5)',
                'content': 'Client testimonial, metrics, or proof'
            }
        else:  # before_after or testimonial_image
            return {
                'type': selected_type,
                'dimensions': '1200 x 1350 px (4:5)',
                'content': 'Before/after or testimonial graphic'
            }

    def generate_hook(self, hook_type: str, topic: str) -> str:
        """Generate a hook for the post.

        Research shows the first 150 characters before "See more" cutoff determine
        if user expands the post or scrolls past. This is the critical engagement lever.
        """
        templates = self.specs['hook_templates'][hook_type]
        template = random.choice(templates)

        # Simple variable substitution (could be enhanced)
        hook = template.replace('{topic}', topic)
        hook = hook.replace('{target_audience}', 'business owners')
        hook = hook.replace('{number}', str(random.randint(50, 500)))
        hook = hook.replace('{percentage}', str(random.randint(70, 95)))
        hook = hook.replace('{common_frustration}', 'struggled with automation')

        # Enforce 150 character limit - this is the critical cutoff before "See more"
        # Research: 40-50% of engagement variance depends on this hook length
        critical_limit = self.specs.get('structure', {}).get('hook', {}).get('critical_cutoff_chars', 150)
        return hook[:critical_limit]

    def generate_body(self, framework: str, topic: str, educational_mode: bool = False, automation_showcase_mode: bool = False, automation_name: str = None) -> str:
        """Generate the post body based on framework.

        Args:
            framework: Writing framework (PAS, AIDA, BAB, Framework, Contrarian)
            topic: Topic for the post
            educational_mode: If True, generate instructional content with examples/steps
            automation_showcase_mode: If True, generate automation showcase content
            automation_name: Name of the automation (used in automation_showcase_mode)
        """
        framework_obj = next(f for f in self.specs['writing_frameworks'] if f['name'] == framework)

        if framework == 'PAS':
            return self._generate_pas(topic, educational_mode, automation_showcase_mode, automation_name)
        elif framework == 'AIDA':
            return self._generate_aida(topic, educational_mode, automation_showcase_mode, automation_name)
        elif framework == 'BAB':
            return self._generate_bab(topic, educational_mode, automation_showcase_mode, automation_name)
        elif framework == 'Framework':
            return self._generate_framework(topic, educational_mode, automation_showcase_mode, automation_name)
        elif framework == 'Contrarian':
            return self._generate_contrarian(topic, educational_mode, automation_showcase_mode, automation_name)

    def _generate_pas(self, topic: str, educational_mode: bool = False, automation_showcase_mode: bool = False, automation_name: str = None) -> str:
        """Generate PAS (Problem-Agitate-Solution) body with topic-specific variation.

        Args:
            topic: The topic for the post
            educational_mode: If True, generate instructional content with specific examples/steps
            automation_showcase_mode: If True, generate automation showcase content
            automation_name: Name of the automation to showcase
        """
        if automation_showcase_mode and automation_name:
            # Automation showcase variant: Show the operational value
            showcase = self.enricher.generate_automation_showcase(automation_name, f"Context: {topic}")

            problem_intro = f"Most business owners haven't heard of {automation_name.lower()}, but it could save their team 10+ hours per week."

            body = f"{problem_intro}\n\n"
            if showcase.get('how_it_works'):
                body += f"Here's how it works:\n{showcase['how_it_works']}\n\n"
            if showcase.get('problems_solved'):
                body += f"Why it matters:\n{showcase['problems_solved']}\n\n"
            if showcase.get('workflow_improvement'):
                body += f"The impact:\n{showcase['workflow_improvement']}\n\n"
            if showcase.get('example'):
                body += f"Real example:\n{showcase['example']}"

            return body
        elif educational_mode:
            # Educational variant: Focus on teaching the technique with examples
            problem_intro = f"Business owners struggle with {topic.lower()} - they're doing it inefficiently or missing the technique entirely."

            # Generate examples and steps from the enricher
            examples = self.enricher.generate_examples(topic, count=2)
            steps = self.enricher.generate_steps(topic, count=3)

            # Build educational PAS structure
            solution_content = "Here's the specific technique:\n\n"
            if steps:
                solution_content += "\n".join(steps[:3])

            if examples:
                solution_content += "\n\n**Real examples:**\n"
                solution_content += "\n".join(examples[:2])

            return f"{problem_intro}\n\n{solution_content}"
        else:
            # Original narrative variant
            # Multiple problem statements to vary the opening
            problem_variants = [
                f"Most businesses handle {topic.lower()} inefficiently because they're stuck in manual processes.",
                f"The problem with {topic.lower()}? Most teams are doing it the hard way.",
                f"{topic} is eating your team's time. But not for the reason you think.",
                f"I see the same mistake with {topic} over and over: manual, repetitive, error-prone.",
            ]

            # Multiple agitation variants
            agitation_variants = [
                "Your team spends 10+ hours/week on repetitive admin tasks. Email routing, data entry, scheduling, follow-ups. These are necessary but don't drive revenue.",
                "Every week, your best people waste hours on routine work: data entry, scheduling, formatting, follow-ups. Work that doesn't move the needle.",
                "Right now, someone on your team is doing the same repetitive tasks every single week. Data entry. Scheduling. Reminders. Hours that could be focused on growth.",
            ]

            # Multiple solution variants
            solution_variants = [
                "The solution isn't to automate your entire business. It's to automate the routine admin work. Remove the tedium. Keep your team in control of decisions that matter.",
                "The fix isn't complex: identify which tasks are purely operational (no judgment needed), automate only those, and keep your team focused on what matters.",
                "Here's what works: Automate the repetitive stuff. Keep humans in control of decisions. Free up capacity for high-impact work.",
            ]

            # Multiple result statements
            result_variants = [
                "Result: Your people spend their time on high-ROI activities. Same output, better allocation of resources.",
                "The outcome? Your team is focused on strategy and growth instead of data entry and scheduling.",
                "What happens? 20+ hours freed up per week per person. Time reallocated to client relationships, strategy, scaling.",
            ]

            problem = random.choice(problem_variants)
            agitation = random.choice(agitation_variants)
            solution = random.choice(solution_variants)
            result = random.choice(result_variants)

            return f"{problem}\n\n{agitation}\n\n{solution}\n\n{result}"

    def _generate_aida(self, topic: str, educational_mode: bool = False, automation_showcase_mode: bool = False, automation_name: str = None) -> str:
        """Generate AIDA (Attention-Interest-Desire-Action) body with variation.

        Args:
            topic: The topic for the post
            educational_mode: If True, generate instructional content with examples
            automation_showcase_mode: If True, generate automation showcase content
            automation_name: Name of the automation to showcase
        """
        if automation_showcase_mode and automation_name:
            # Automation showcase: Lead with the benefit
            showcase = self.enricher.generate_automation_showcase(automation_name, f"Context: {topic}")

            attention = f"Your business is probably still doing {automation_name.lower()} manually."
            interest = "It doesn't have to be."

            body = f"{attention}\n\n{interest}\n\n"
            if showcase.get('how_it_works'):
                body += f"Here's how it works:\n{showcase['how_it_works']}\n\n"
            if showcase.get('workflow_improvement'):
                body += f"The result:\n{showcase['workflow_improvement']}\n\n"
            if showcase.get('example'):
                body += f"Example:\n{showcase['example']}"

            return body
        elif educational_mode:
            # Educational variant: Focus on teaching with examples
            intro = f"Here's what you need to know about {topic.lower()}:"
            examples = self.enricher.generate_examples(topic, count=2)
            template = self.enricher.generate_template(topic)
            content = intro + "\n\n"
            if examples:
                content += "**Real examples:**\n" + "\n".join(examples[:2]) + "\n\n"
            if template.get('template_content'):
                content += f"**Template to use:**\n{template['template_content']}"
            return content
        # Variations of client stories
        stories = [
            "I recently helped a client reclaim 40 hours/month from routine admin work.\n\nTheir process: receive request → create proposal → send to client → follow up.\n8 hours per proposal. 5 proposals per week.\nThat's 40 hours every month on repetitive tasks.",
            "Last week, I worked with a founder who was buried in routine tasks.\nHer team spent 30+ hours/week on administrative work: scheduling, data entry, invoicing, follow-ups.\nAll necessary. None of it growing the business.",
            "One of my clients recently told me they were working 60-hour weeks but only 20 hours were actually strategic.\nThe other 40? Email management, task coordination, document organization, scheduling follow-ups.",
        ]

        # Variations of workflow outcomes
        workflows = [
            "We built a workflow that handles the repetitive parts:\n→ Receives requests from email/form\n→ Auto-generates proposal from templates\n→ Sends with proper formatting\n→ Triggers follow-up reminders",
            "We implemented a system that:\n→ Captures routine tasks automatically\n→ Schedules them intelligently\n→ Removes manual coordination overhead\n→ Keeps humans in control of decisions",
            "The solution involved:\n→ Identifying which tasks repeat weekly\n→ Building automation for those specific tasks\n→ Keeping quality control in human hands\n→ Measuring the time savings",
        ]

        # Variations of outcome
        outcomes = [
            "The difference: The team still reviews each proposal before sending. They still make the decisions. They just don't waste time on the routine data entry and formatting.\n\nNow those 40 hours go to client strategy and business development instead. Same quality work. Better use of their capacity.",
            "The result: Their team went from 60-hour weeks to 45-hour weeks. Same output quality. Better focus on growth. And no loss of control over decisions that matter.",
            "What changed: The team freed up 25 hours per week. Hours that are now going toward strategy, client relationships, and revenue-generating activities.",
        ]

        # Variations of CTA
        ctas = [
            "If your team is spending time on routine admin tasks, let's talk about freeing that up.",
            "If this sounds like your situation, there's a path forward.",
            "Sound familiar? This is exactly what I help teams fix.",
        ]

        story = random.choice(stories)
        workflow = random.choice(workflows)
        outcome = random.choice(outcomes)
        cta = random.choice(ctas)

        return f"{story}\n\n{workflow}\n\n{outcome}\n\n{cta}"

    def _generate_bab(self, topic: str, educational_mode: bool = False, automation_showcase_mode: bool = False, automation_name: str = None) -> str:
        """Generate BAB (Before-After-Bridge) body with variation.

        Args:
            topic: The topic for the post
            educational_mode: If True, generate instructional content with before/after examples
            automation_showcase_mode: If True, generate automation showcase content
            automation_name: Name of the automation to showcase
        """
        if automation_showcase_mode and automation_name:
            # Automation showcase: Before/After with the automation
            showcase = self.enricher.generate_automation_showcase(automation_name, f"Context: {topic}")

            body = f"Before {automation_name.lower()}: Manual processes, errors, wasted time.\n\n"
            if showcase.get('example'):
                body += f"{showcase['example']}\n\n"
            if showcase.get('workflow_improvement'):
                body += f"After implementation:\n{showcase['workflow_improvement']}"

            return body
        elif educational_mode:
            # Educational variant: Focus on teaching with before/after comparison and step-by-step bridge
            before_after = self.enricher.generate_before_after(topic)
            steps = self.enricher.generate_steps(topic, count=4)

            # Build educational BAB structure
            content = f"**The Problem (Before):**\n{before_after['before']}\n\n"
            content += f"**The Solution (After):**\n{before_after['after']}\n\n"
            content += f"**Key Differences:**\n{before_after['key_differences']}\n\n"
            content += "**How to Implement This:**\n"

            if steps:
                content += "\n".join(steps[:4])

            return content
        else:
            # Original narrative variant
            # Variations of before state
            befores = [
                "6 months ago, I was spending 20 hours/week on routine admin work.\nClient onboarding: manual data entry, document organization\nInvoicing: creating files, tracking payments\nFollow-ups: sending repetitive emails\nI was trapped in operational work instead of growing the business.",
                "A year ago, my business was drowning in manual work.\nEvery day: scheduling meetings, entering data into systems, creating documents, sending follow-ups.\n30+ hours every week on tasks that don't require strategic thinking.\nMy actual business work? Squeezed into nights and weekends.",
                "18 months ago, I realized something: I was building a business, not running one.\nMy time was consumed by routine coordination work. Email management. Document prep. Task tracking.\nI was working 55+ hours but maybe 20 of them were actually valuable.",
            ]

            # Variations of transformation (bridge + after)
            transformations = [
                "What changed? I identified which tasks are repetitive vs strategic.\n\nI audited my week and separated:\n→ Decisions I must make (client strategy, approvals)\n→ Routine work I don't need to touch (data entry, formatting, scheduling)\n\nI automated only the routine work. Everything strategic stays under my control.\n\nToday, I still handle all client decisions and strategy. But the routine admin work is streamlined.\nClient onboarding: 30 minutes instead of 4 hours (I verify everything, the system just removes data entry)\nInvoicing: 15 minutes instead of 2 hours (I approve it, the system formats and files)\nFollow-ups: sent automatically, I review results weekly\nI now work 40 hours focused on growth instead of 60 hours stuck in operations.",
                "The breakthrough came when I stopped trying to automate everything.\n\nInstead, I mapped my week:\n→ What requires judgment? (Keep it)\n→ What's repetitive? (Automate it)\n\nThen I built systems for only the repetitive stuff.\n\nResult: My week went from 55 hours to 40 hours. Same revenue. Same client satisfaction. Just less time wasted.\nI now spend 30 hours on strategy, sales, and client relationships. 10 hours on necessary but routine work.",
                "The key insight: Not everything needs human attention.\n\nSome tasks are purely routine. Others require decisions.\n\nI separated them ruthlessly:\n→ Strategic work stays with me (approvals, strategy, client calls)\n→ Routine work goes to systems (data entry, scheduling, follow-ups)\n\nBefore: 60-hour weeks, 30 hours wasted on admin\nAfter: 40-hour weeks, all strategic\nControl: I still review everything. The system just handles the repetition.",
            ]

            # Variations of lesson
            lessons = [
                "The result? More time for what actually scales the business. No loss of control. Better risk management.",
                "The outcome: I freed up 15-20 hours per week without sacrificing quality or control.",
                "What I learned: Automation doesn't mean loss of control. It means smarter work distribution.",
            ]

            before = random.choice(befores)
            transformation = random.choice(transformations)
            lesson = random.choice(lessons)

            return f"{before}\n\n{transformation}\n\n{lesson}"

    def _generate_framework(self, topic: str, educational_mode: bool = False, automation_showcase_mode: bool = False, automation_name: str = None) -> str:
        """Generate Framework body with variation.

        Args:
            topic: The topic for the post
            educational_mode: If True, generate instructional content with step-by-step guide
            automation_showcase_mode: If True, generate automation showcase content
            automation_name: Name of the automation to showcase
        """
        if automation_showcase_mode and automation_name:
            # Automation showcase: Show implementation framework
            showcase = self.enricher.generate_automation_showcase(automation_name, f"Context: {topic}")

            body = f"How to implement {automation_name.lower()}:\n\n"
            if showcase.get('how_it_works'):
                body += f"{showcase['how_it_works']}\n\n"
            if showcase.get('problems_solved'):
                body += f"Why it matters:\n{showcase['problems_solved']}\n\n"
            if showcase.get('workflow_improvement'):
                body += f"Expected results:\n{showcase['workflow_improvement']}"

            return body
        elif educational_mode:
            # Educational variant: Focus on teaching the framework step-by-step with examples
            framework_intro = f"Here's the framework for {topic.lower()}:\n\n"
            steps = self.enricher.generate_steps(topic, count=5)
            template = self.enricher.generate_template(topic)

            content = framework_intro

            if steps:
                content += "\n".join(steps[:5])
            else:
                content += "Steps not available\n"

            content += "\n\n**Adaptable Template:**\n"
            if template.get('template_content'):
                content += f"{template['template_content']}\n\n"
            if template.get('customization_guide'):
                content += f"**How to Customize:**\n{template['customization_guide']}"

            return content
        else:
            # Original narrative variant
            # Multiple 3-step framework variations
            frameworks_list = [
                {
                    "steps": [
                        ("Step 1: The Audit", "Spend 1 week tracking every task you do.\nMark which ones repeat weekly.\nCalculate hours spent on each.\nSeparate routine admin work from strategic decisions."),
                        ("Step 2: The Stack", "For your routine tasks, identify automation tools (Zapier, Make, APIs).\nStart with the highest time-consumer.\nSet it up. Test it. Keep your team in the loop.\nDon't automate decisions—only repetitive data work."),
                        ("Step 3: The Allocate", "Once automation handles routine work, reallocate that time.\nUse it for business growth, client relationships, strategy.\nDocument what changed.\nMeasure the impact on revenue."),
                    ],
                    "meta": "Time to implement: 5-10 hours\nTime freed up: 20+ hours/week\nWhere it goes: High-ROI activities (not just free time)",
                    "lesson": "This framework works because it's selective. Not everything gets automated—just the stuff keeping you from scaling."
                },
                {
                    "steps": [
                        ("Step 1: Map", "List out everything you do in a week.\nNote which tasks repeat.\nIdentify which ones don't require your judgment."),
                        ("Step 2: Automate", "Focus on repetitive, judgment-free tasks.\nUse no-code automation (Make, Zapier, etc.).\nStart with 1-2 tasks. Test thoroughly."),
                        ("Step 3: Reallocate", "Move freed-up time to revenue-generating activities.\nClient relationships. Business development. Strategy.\nMeasure the revenue impact."),
                    ],
                    "meta": "Typical timeline: 2 weeks to implement\nAverage time freed: 15-25 hours/week per person\nRisk level: Low (automation handles routine only)",
                    "lesson": "The key: Automate only what's truly routine. Keep yourself in control of what matters."
                },
                {
                    "steps": [
                        ("Step 1: Audit Your Week", "For 7 days, track every task.\nHow long does each take? How often does it repeat?\nDoes it require a business decision or just execution?"),
                        ("Step 2: Identify Automation Candidates", "Find tasks that are:\n- Repetitive (happen weekly or more)\n- Predictable (same process every time)\n- Safe (don't require judgment)"),
                        ("Step 3: Build & Monitor", "Implement automation for 2-3 high-impact tasks.\nTest thoroughly before going live.\nMonitor for issues. Adjust as needed."),
                    ],
                    "meta": "Setup time: 3-8 hours\nTime savings: Compound as you add more automations\nBusiness impact: More time for growth activities",
                    "lesson": "Start small. Prove the value. Then expand systematically."
                },
            ]

            framework = random.choice(frameworks_list)
            steps_formatted = "\n\n".join([f"🔹 {step[0]}\n{step[1]}" for step in framework["steps"]])

            return f"{steps_formatted}\n\n{framework['meta']}\n\n{framework['lesson']}"

    def _generate_contrarian(self, topic: str, educational_mode: bool = False, automation_showcase_mode: bool = False, automation_name: str = None) -> str:
        """Generate Contrarian body with variation.

        Args:
            topic: The topic for the post
            educational_mode: If True, generate instructional content with contrarian hook + examples
            automation_showcase_mode: If True, generate automation showcase content
            automation_name: Name of the automation to showcase
        """
        if automation_showcase_mode and automation_name:
            # Automation showcase: Contrarian take on why people aren't using it
            showcase = self.enricher.generate_automation_showcase(automation_name, f"Context: {topic}")

            body = f"Unpopular opinion: Most business owners still do {automation_name.lower()} manually.\n\n"
            body += "They could save 10+ hours per week, but they don't.\n\n"
            if showcase.get('how_it_works'):
                body += f"Here's how it works:\n{showcase['how_it_works']}\n\n"
            if showcase.get('workflow_improvement'):
                body += f"The impact:\n{showcase['workflow_improvement']}"

            return body
        elif educational_mode:
            # Educational variant: Contrarian hook + list of techniques with specific examples
            examples = self.enricher.generate_examples(topic, count=4)

            # Build contrarian hook
            content = f"Unpopular opinion about {topic.lower()}: Most people get it wrong.\n\n"
            content += "Here's what actually works:\n\n"

            if examples:
                for i, example in enumerate(examples[:4], 1):
                    content += f"{i}. {example}\n\n"
            else:
                content += "Key techniques available upon request.\n"

            content += "The mistake most people make: They follow conventional wisdom instead of testing what actually works."

            return content
        else:
            # Original narrative variant
            contrarian_takes = [
                {
                    "hot_take": "Unpopular opinion: Most people try to automate everything instead of automating strategically.",
                    "traps": "They get caught in:\n→ \"Let's automate this too\"\n→ \"What if the system could handle that?\"\n→ \"Maybe we don't need anyone to make decisions\"",
                    "risk": "This creates fragility and catastrophic risk.",
                    "solution": "1. Identify tasks that are routine, repeatable, and safe to automate (data entry, scheduling, follow-ups)\n2. Identify tasks that require human judgment (client strategy, approvals, quality decisions)\n3. Automate ONLY #1. Keep humans in control of #2.\n4. Use the freed-up time for high-ROI activities",
                    "mistake": "They try to remove humans entirely. They build systems that make decisions without oversight.",
                    "truth": "Smart automation is selective. Remove the tedious parts. Keep the thinking.",
                    "cta": "What's one routine admin task that's eating your time but doesn't need human judgment? That's your automation candidate."
                },
                {
                    "hot_take": "Hot take: Over-automation is killing businesses faster than under-automation ever could.",
                    "traps": "The seductive trap:\n→ \"AI can handle this\"\n→ \"Let's remove that person from the process\"\n→ \"The system is more reliable than humans\"",
                    "risk": "Result? Systems that fail catastrophically. No human to catch errors. Decisions made by algorithms with no oversight.",
                    "solution": "1. Automate only what's truly mechanical (data entry, scheduling, reminders)\n2. Keep humans in charge of judgment calls (approvals, strategy, quality)\n3. Make automation augment humans, not replace them\n4. Build in checkpoints and escalation paths",
                    "mistake": "They assume 'automated' means 'better.' It just means 'faster.' Fast + wrong = disaster.",
                    "truth": "The smartest companies don't automate everything. They automate wisely.",
                    "cta": "Before you automate something, ask: If this breaks silently, what happens? If the answer is 'nothing good,' keep a human in the loop."
                },
                {
                    "hot_take": "Controversial take: Your automation strategy is probably backwards.",
                    "traps": "What I see most:\n→ Automate the high-stakes decisions (dangerous)\n→ Ignore the low-value repetitive work (wasteful)\n→ Build systems nobody understands (fragile)",
                    "risk": "Result? Brittle businesses that look efficient until something breaks.",
                    "solution": "1. Start with the boring stuff (data entry, scheduling, follow-ups)\n2. Keep every high-stakes decision under human control\n3. Build automation for clarity, not just speed\n4. Make it so anyone on your team understands the system",
                    "mistake": "They focus on big, flashy automation and ignore the tedium that's costing them 30 hours/week.",
                    "truth": "The best automation is invisible and boring. It just makes routine work disappear.",
                    "cta": "What's the most boring, repetitive task you do? That's your priority. Not the flashy stuff."
                },
            ]

            take = random.choice(contrarian_takes)

            return f"{take['hot_take']}\n\n{take['traps']}\n\n{take['risk']}\n\nHere's what actually works:\n\n{take['solution']}\n\nThe mistake most people make: {take['mistake']}\n\n{take['truth']}\n\n{take['cta']}"

    def select_cta(self, post_type: str) -> Tuple[str, str]:
        """Select CTA based on post type."""
        cta_type = self.specs['content_mix'][post_type]['cta_type']

        if cta_type == 'soft':
            cta = random.choice(self.specs['cta_templates']['soft_engagement'])
        else:  # direct
            cta = random.choice(self.specs['cta_templates']['direct_booking'])

        # Format CTA
        cta = cta.replace('{topic}', 'this')
        cta = cta.replace('{outcome}', 'scale your business')
        cta = cta.replace('{target_audience}', 'founders and entrepreneurs')
        cta = cta.replace('{achieve_outcome}', 'automate and scale')

        return cta, cta_type

    def generate_eyecatching_title(self, topic: str, framework: str, hook_type: str) -> str:
        """Generate an eye-catching, clickable title for the post."""
        # Title patterns that drive clicks and engagement
        title_templates = [
            # Curiosity/Mystery
            f"The {random.choice(['Hidden', 'Secret', 'Overlooked', 'Untold'])} Truth About {topic}",
            f"Why Nobody Talks About {topic} (But They Should)",
            f"I Discovered Something About {topic}... and It Changed Everything",

            # Data/Numbers
            f"I Saved 100+ Hours With {topic}",
            f"The {random.randint(3, 7)}-Step System for {topic}",
            f"{random.randint(50, 300)}% More Productivity With {topic}",

            # Contrarian
            f"Stop Doing {topic} the Wrong Way",
            f"The Unpopular Truth About {topic}",
            f"Everyone's Wrong About {topic}",

            # Before/After
            f"From Chaos to {topic}: Here's What Changed",
            f"How I Went From Struggling With {topic} to Mastering It",

            # How-To
            f"How to Implement {topic} in 30 Minutes",
            f"The Complete {topic} Playbook",
            f"Master {topic} in 3 Steps",

            # Authority/Proof
            f"What {random.randint(50, 500)}+ Entrepreneurs Know About {topic}",
            f"The {topic} Framework That Works",

            # Emotion/Impact
            f"This {topic} Insight Will Reshape How You Work",
            f"Stop Wasting Time on {topic}",
            f"The Real Cost of Ignoring {topic}",

            # FOMO/Urgency
            f"Most Business Owners Don't Understand {topic}... Yet",
            f"What Smart Founders Know About {topic}",

            # Unique Angle
            f"My Honest Take on {topic}",
            f"Why {topic} Is More Important Than You Think",
            f"The {topic} Nobody's Talking About"
        ]

        selected_title = random.choice(title_templates)

        # Truncate to reasonable length for LinkedIn
        return selected_title[:100]

    def generate_hashtags(self, topic: str) -> str:
        """Generate relevant hashtags with 30% broad + 70% niche strategy.

        Research shows posts with relevant hashtags get 30% more engagement.
        Optimal mix: 30% broad industry hashtags + 70% niche/specific hashtags.
        This ensures visibility while targeting specific audience.
        """
        # Broad hashtags (30% of selection)
        broad_hashtags = [
            '#AI',
            '#Automation',
            '#Business',
            '#Entrepreneurship',
            '#Productivity',
            '#Leadership',
            '#Growth'
        ]

        # Niche hashtags specific to AI/Automation business niche (70% of selection)
        niche_hashtags = [
            '#AIAutomation',
            '#WorkflowOptimization',
            '#BusinessOwners',
            '#SmartAutomation',
            '#BusinessAutomation',
            '#AIForBusiness',
            '#AutomationStrategy',
            '#ProcessOptimization',
            '#DigitalTransformation',
            '#BusinessEfficiency'
        ]

        # Select hashtags based on 30/70 ratio
        # Weighted toward more niche hashtags to hit ~30% broad target
        # For 3-5 hashtags:
        #   3 hashtags: 1 broad (33%) + 2 niche (67%)
        #   4 hashtags: 1 broad (25%) + 3 niche (75%) [occasionally 2B for variety]
        #   5 hashtags: 1-2 broad (20-40%) + 3-4 niche
        total_count = random.randint(3, 5)  # 3-5 hashtags per spec
        if total_count == 3:
            broad_count = 1  # 33% broad
        elif total_count == 4:
            broad_count = random.choices([1, 2], weights=[75, 25], k=1)[0]  # 25% mostly, 50% occasionally
        else:  # 5 hashtags
            broad_count = random.choices([1, 2], weights=[60, 40], k=1)[0]  # 20% mostly, 40% sometimes
        niche_count = total_count - broad_count

        selected_broad = random.sample(broad_hashtags, min(broad_count, len(broad_hashtags)))
        selected_niche = random.sample(niche_hashtags, min(niche_count, len(niche_hashtags)))

        selected = selected_broad + selected_niche
        return ' '.join(selected)

    def generate_complete_post(self, topic: str, educational_mode: bool = False, automation_showcase_mode: bool = False, automation_name: str = None) -> Dict:
        """Generate a complete optimized post.

        Args:
            topic: The topic for the post
            educational_mode: If True, generate instructional content with examples/steps
            automation_showcase_mode: If True, generate automation showcase content
            automation_name: Name of the automation (used in automation_showcase_mode)
        """
        # Determine post type (40% expertise, 40% engagement, 20% promotional)
        rand = random.random()
        if rand < 0.4:
            post_type = 'expertise_posts'
        elif rand < 0.8:
            post_type = 'engagement_posts'
        else:
            post_type = 'promotional_posts'

        # Select components
        framework = self.select_framework()
        hook_type = self.select_hook_type()
        hook = self.generate_hook(hook_type, topic)
        body = self.generate_body(framework, topic, educational_mode=educational_mode, automation_showcase_mode=automation_showcase_mode, automation_name=automation_name)
        cta, cta_type = self.select_cta(post_type)
        hashtags = self.generate_hashtags(topic)
        visual_spec = self.select_visual_type(post_type)
        title = self.generate_eyecatching_title(topic, framework, hook_type)

        # Build full post
        full_content = f"{hook}\n\n{body}\n\n{cta}\n\n{hashtags}"

        # Optimize post length for LinkedIn (target 1,200-1,800 characters)
        if (educational_mode or automation_showcase_mode) and len(full_content) > 1800:
            # Intelligently trim the body to reach optimal length
            full_content = self._optimize_post_length(hook, body, cta, hashtags)

        return {
            'title': title,
            'topic': topic,
            'hook': hook,
            'body': body,
            'cta': cta,
            'full_content': full_content,
            'framework': framework,  # Internal name (for logic)
            'framework_airtable': self.map_framework_to_airtable(framework),  # Airtable-compatible name
            'hook_type': hook_type,
            'cta_type': cta_type,
            'post_type': post_type,
            'visual_type': visual_spec['type'],
            'visual_spec': visual_spec,
            'hashtags': hashtags,
            'generated_at': datetime.now().isoformat(),
            'scheduled_time': None,  # Only set when status changes to "Pending Review"
            'status': 'Draft',
            'educational_mode': educational_mode,
            'automation_showcase_mode': automation_showcase_mode,
            'automation_name': automation_name,
            'content_length': len(full_content)
        }

    def _sanitize_content(self, content: str) -> str:
        """Remove all markdown artifacts (asterisks) from content.

        Removes:
        - **bold** markdown → bold
        - *italic* markdown → italic
        - Any stray asterisks
        """
        # Remove markdown bold (**text**)
        content = content.replace('**', '')
        # Remove any remaining single asterisks
        content = content.replace('*', '')
        return content

    def _optimize_post_length(self, hook: str, body: str, cta: str, hashtags: str) -> str:
        """Intelligently trim post to stay within 1,200-1,800 character optimal range.

        Strategy:
        1. Keep hook intact (crucial for engagement)
        2. Keep CTA intact (crucial for action)
        3. Trim body by removing examples and steps
        4. Final length: 1,200-1,800 characters
        """
        # Start with full content
        optimized_body = body

        # If over 1,800 chars, start removing educational elements
        while len(f"{hook}\n\n{optimized_body}\n\n{cta}\n\n{hashtags}") > 1800:
            # Remove the last "example" block (look for **Real examples:** and everything after)
            if "**Real examples:**" in optimized_body:
                optimized_body = optimized_body[:optimized_body.rfind("**Real examples:**")].strip()
                continue

            # Remove the last numbered step (look for lines starting with digits followed by .)
            lines = optimized_body.split('\n')
            removed_step = False
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].strip() and lines[i].strip()[0].isdigit() and '.' in lines[i][:3]:
                    # Found a step, remove it and following explanation lines
                    # But preserve at least the first line and some content before
                    if i > 2:  # Only remove if not one of the first few lines
                        lines = lines[:i]
                        optimized_body = '\n'.join(lines).strip()
                        removed_step = True
                    break

            if not removed_step:
                # If no steps to remove, try to intelligently remove last paragraph
                paragraphs = optimized_body.split('\n\n')
                if len(paragraphs) > 2:
                    # Remove last paragraph only if it won't create incomplete text
                    last_para = paragraphs[-1].strip()

                    # Check if last paragraph ends with complete punctuation (not mid-word)
                    if last_para and not re.search(r'[a-z]{2,}$', last_para):
                        # Paragraph ends with punctuation/normal ending, safe to remove
                        optimized_body = '\n\n'.join(paragraphs[:-1]).strip()
                    else:
                        # Last paragraph ends mid-word or incomplete, truncate at sentence instead
                        # Find last period, question mark, or exclamation
                        last_sentence_end = max(
                            last_para.rfind('.'),
                            last_para.rfind('?'),
                            last_para.rfind('!')
                        )

                        if last_sentence_end > 50:  # Only truncate if there's substantial content before
                            last_para_truncated = last_para[:last_sentence_end + 1].strip()
                            optimized_body = '\n\n'.join(paragraphs[:-1] + [last_para_truncated]).strip()
                        else:
                            # Can't safely truncate, remove entire paragraph
                            optimized_body = '\n\n'.join(paragraphs[:-1]).strip()
                else:
                    # Only one paragraph left, break to avoid over-truncation
                    break

            # Safety check: if we've trimmed too much, break
            if len(optimized_body) < 300:
                break

        # Ensure we're not below minimum length (900 chars)
        if len(f"{hook}\n\n{optimized_body}\n\n{cta}\n\n{hashtags}") < 900:
            # If we trimmed too much, use original body
            optimized_body = body

        # Build final content
        final_content = f"{hook}\n\n{optimized_body}\n\n{cta}\n\n{hashtags}"

        # Log optimization
        original_length = len(f"{hook}\n\n{body}\n\n{cta}\n\n{hashtags}")
        final_length = len(final_content)
        if final_length < original_length:
            print(f"   📏 Post optimized: {original_length} → {final_length} chars (target: 1,200-1,800)")

        return final_content

    def add_post_to_airtable(self, post: Dict) -> bool:
        """Add generated post to Airtable."""
        url = f"https://api.airtable.com/v0/{self.airtable_base_id}/{self.airtable_table_id}"

        # Build notes with metadata
        metadata = f"""Framework: {post['framework']}
Hook Type: {post['hook_type']}
CTA Type: {post['cta_type']}
Post Type: {post['post_type']}
Visual Type: {post['visual_type']}
Visual Spec: {json.dumps(post['visual_spec'])}"""

        # Sanitize content to remove markdown artifacts
        clean_content = self._sanitize_content(post['full_content'])

        # Build fields payload - only include Scheduled Time if it's set
        fields = {
            "Title": post['title'],
            "Post Content": clean_content,
            "Status": post['status'],
            "Image Prompt": f"Visual Type: {post['visual_type']} | Dimensions: {post['visual_spec'].get('dimensions', 'N/A')}",
            "Notes": metadata
        }

        # Add image URL if available
        if post.get('image_url'):
            fields["Image URL"] = post['image_url']
            # Also add to Image attachment field (Airtable format)
            fields["Image"] = [{"url": post['image_url']}]

        # Only add scheduled time if it's set (not None)
        if post['scheduled_time']:
            fields["Scheduled Time"] = post['scheduled_time']

        payload = {
            "records": [
                {
                    "fields": fields
                }
            ]
        }

        response = requests.post(url, headers=self.headers, json=payload)

        if response.status_code == 200:
            record_id = response.json()['records'][0]['id']
            print(f"✅ Post added to Airtable: {record_id}")
            return True
        else:
            print(f"❌ Error adding post: {response.status_code}")
            print(response.json())
            return False

    def update_post_image(self, record_id: str, image_url: str, image_prompt: str = None) -> bool:
        """Update image URL for existing Airtable record.

        This is used when a new image is generated for an existing post.

        Args:
            record_id: Airtable record ID
            image_url: URL of generated image
            image_prompt: Optional updated image prompt

        Returns:
            True if successful, False otherwise
        """
        url = f"https://api.airtable.com/v0/{self.airtable_base_id}/{self.airtable_table_id}/{record_id}"

        fields = {
            "Image URL": image_url,
            "Image": [{"url": image_url}]
        }

        # Update image prompt if provided
        if image_prompt:
            fields["Image Prompt"] = image_prompt

        payload = {
            "fields": fields
        }

        response = requests.patch(url, headers=self.headers, json=payload)

        if response.status_code == 200:
            print(f"✅ Image updated for record {record_id}")
            return True
        else:
            print(f"❌ Error updating image: {response.status_code}")
            print(response.json())
            return False

    def delete_all_posts(self) -> int:
        """Delete all existing posts from Airtable."""
        url = f"https://api.airtable.com/v0/{self.airtable_base_id}/{self.airtable_table_id}"

        response = requests.get(url, headers=self.headers)
        records = response.json().get('records', [])

        deleted_count = 0
        for record in records:
            delete_url = f"{url}/{record['id']}"
            delete_response = requests.delete(delete_url, headers=self.headers)
            if delete_response.status_code == 200:
                deleted_count += 1

        print(f"✅ Deleted {deleted_count} posts from Airtable")
        return deleted_count

    def print_post_summary(self, post: Dict):
        """Print a formatted post summary."""
        print("\n" + "="*80)
        print("📝 GENERATED POST")
        print("="*80)
        print(f"\nTopic: {post['topic']}")
        print(f"Framework: {post['framework']}")
        print(f"Hook Type: {post['hook_type']}")
        print(f"CTA Type: {post['cta_type']} ({post['post_type']})")
        print(f"Visual: {post['visual_type']}")
        print(f"Scheduled: {post['scheduled_time']}")
        print(f"\n{'-'*80}")
        print("POST CONTENT:")
        print(f"{'-'*80}\n")
        print(post['full_content'])
        print(f"\n{'-'*80}")
        print("VISUAL SPECIFICATION:")
        print(f"{'-'*80}")
        for key, value in post['visual_spec'].items():
            print(f"  {key}: {value}")
        print("="*80 + "\n")


# Main execution
if __name__ == "__main__":
    print("🚀 Initializing Optimized Post Generator...")
    generator = OptimizedPostGenerator()
    generator.analyzer.initialize_topic("Automation Audit Framework")

    # All 73 topics
    topics = [
        "Prompt Engineering Fundamentals",
        "The 80/20 Rule of AI Adoption",
        "AI-Powered Customer Service Responses",
        "Automated Content Repurposing with AI",
        "AI-Assisted Proposal Writing",
        "Intelligent Email Triage and Prioritization",
        "Custom GPT Creation for Specific Business Functions",
        "AI-Powered Meeting Summarization",
        "Contextual AI Knowledge Bases",
        "Prompt Chaining for Complex Tasks",
        "The Automation Audit Framework",
        "Zapier vs Make vs Custom Scripts: Decision Framework",
        "Building Your First Business Automation in 30 Minutes",
        "Multi-Step Workflow Automation Design",
        "Error Handling in Automated Workflows",
        "Automated Data Entry from Emails and Forms",
        "CRM Automation Beyond the Basics",
        "Automated Invoicing and Payment Follow-ups",
        "Document Generation Automation",
        "Slack/Teams Notification Systems",
        "Client Onboarding Automation",
        "Project Status Updates Without Manual Work",
        "Automated Quality Assurance Checklists",
        "Customer Feedback Collection and Analysis",
        "Proactive Issue Detection",
        "Resource Allocation Optimization",
        "Scope Creep Prevention Systems",
        "Delivery Timeline Automation",
        "Post-Project Review Automation",
        "Upsell and Cross-Sell Trigger Systems",
        "The Virtual Employee Framework",
        "Automated Training and Onboarding",
        "Self-Service Customer Portals",
        "AI-Powered First-Line Support",
        "Automated Lead Qualification",
        "Delegation Frameworks for Founders",
        "Asynchronous Communication Systems",
        "ChatGPT vs Claude vs Gemini: Business Use Cases",
        "AI-Powered Market Research",
        "Automated Social Media Management",
        "AI Writing Assistants for Business Communication",
        "Voice-to-Text Automation for Documentation",
        "AI-Powered Translation for Global Business",
        "AI-Powered Competitor Analysis",
        "Sentiment Analysis for Customer Communications",
        "AI-Generated Case Studies and Testimonials",
        "Personalized Outreach at Scale",
        "AI-Powered Contract Review",
        "Automated Competitive Pricing Intelligence",
        "AI-Enhanced Sales Call Analysis",
        "Smart Content Recommendations for Leads",
        "AI-Powered Meeting Preparation",
        "Automated Follow-Up Sequences Based on Engagement",
        "Automated Appointment Scheduling and Reminders",
        "Dynamic Pricing Automation",
        "Automated Referral Request Systems",
        "Subscription and Recurring Revenue Automation",
        "Automated Proposal Follow-Up Sequences",
        "Win-Back Campaigns for Lost Customers",
        "Automated Testimonial Collection",
        "Cart Abandonment Recovery Automation",
        "Automated Renewal and Upgrade Prompts",
        "Lead Magnet Delivery and Nurture Automation",
        "Automated Expense Tracking and Categorization",
        "Inventory and Stock Alert Automation",
        "Automated Vendor Management",
        "Meeting-Free Monday Automation",
        "Automated Task Prioritization",
        "Client Communication Templates with AI Personalization",
        "Automated Project Kickoff Workflows",
        "Time Zone Management Automation",
        "Automated Weekly Review Generation",
        "Smart Notification Filtering"
    ]

    print(f"📊 Generating 3 new optimized posts...\n")

    # Generate 3 posts
    generated_posts = []
    for i in range(3):
        topic = random.choice(topics)
        post = generator.generate_complete_post(topic)
        generator.print_post_summary(post)
        generated_posts.append(post)

    print("\n✅ Post generation complete!")
