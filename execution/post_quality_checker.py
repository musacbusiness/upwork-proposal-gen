"""
Post Quality Checker - Validates posts before upload to Airtable
Catches issues like:
- Duplicate/near-duplicate content
- Missing structural elements (hook, body, CTA)
- Placeholder variables
- Framework labels in content
- Incomplete narrative arcs
"""

import os
import sys
import difflib
import re
import requests
from pathlib import Path
from typing import Dict, List, Tuple, Optional

sys.path.insert(0, str(Path(__file__).parent))


class PostQualityChecker:
    """Validates posts before they're uploaded to Airtable."""

    def __init__(self):
        """Initialize quality checker."""
        env_file = "/Users/musacomma/Agentic Workflow/.env"
        if os.path.exists(env_file):
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip().strip('"\'')

        self.airtable_api_key = os.environ.get('AIRTABLE_API_KEY')
        self.airtable_base_id = os.environ.get('AIRTABLE_BASE_ID')
        self.airtable_table_id = os.environ.get('AIRTABLE_LINKEDIN_TABLE_ID')
        self.headers = {
            "Authorization": f"Bearer {self.airtable_api_key}",
            "Content-Type": "application/json"
        }

        # Thresholds
        self.SIMILARITY_THRESHOLD = 0.85  # 85%+ similarity = likely duplicate
        self.MIN_CONTENT_LENGTH = 300  # Minimum characters for post body
        self.MAX_SIMILARITY_TO_EXISTING = 0.75  # Post should be < 75% similar to any existing post

        # Topic relevance thresholds
        self.MIN_TOPIC_KEYWORD_COVERAGE = 0.3  # At least 30% of topic keywords should appear

    def fetch_existing_posts(self) -> List[Dict]:
        """Get all existing posts from Airtable."""
        try:
            url = f"https://api.airtable.com/v0/{self.airtable_base_id}/{self.airtable_table_id}"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                return response.json().get('records', [])
            return []
        except Exception as e:
            print(f"⚠️  Warning: Couldn't fetch existing posts for comparison: {str(e)}")
            return []

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts (0.0 to 1.0)."""
        # Normalize: remove extra whitespace, lowercase for comparison
        text1_norm = ' '.join(text1.lower().split())
        text2_norm = ' '.join(text2.lower().split())

        matcher = difflib.SequenceMatcher(None, text1_norm, text2_norm)
        return matcher.ratio()

    def check_for_placeholders(self, content: str) -> List[str]:
        """Find any unfilled placeholder variables like {things}, {year}, etc."""
        # Pattern: {word} but not {{word}} (hashtags)
        pattern = r'\{[a-zA-Z_][a-zA-Z0-9_]*\}(?!\})'
        placeholders = re.findall(pattern, content)
        return list(set(placeholders))  # Return unique

    def check_for_framework_labels(self, content: str) -> List[str]:
        """Find any framework labels that shouldn't be in final content."""
        labels = [
            '[BEFORE]', '[AFTER]', '[BRIDGE]',
            '[PROBLEM]', '[AGITATE]', '[SOLUTION]',
            '[ATTENTION]', '[INTEREST]', '[DESIRE]', '[ACTION]',
            '[FRAMEWORK]', '[STEP', '[CONTRARIAN]'
        ]
        found = [label for label in labels if label in content]
        return found

    def check_for_complete_hook(self, content: str) -> Tuple[bool, str]:
        """Verify hook has complete narrative arc."""
        # Check for hanging statements/questions
        # A good hook should lead somewhere, not end abruptly

        lines = content.split('\n')
        if not lines:
            return False, "Empty content"

        first_para = lines[0].strip()
        if not first_para:
            return False, "No hook found"

        # Look for incomplete patterns
        incomplete_patterns = [
            r'^(Last week|A few days ago|Recently|Once|I had),?\s+[^.!?]*$',  # Ends without conclusion
            r'^\w+\s+\w+\?\s*$',  # Just a question, nothing after
            r'^(What if|Imagine|Picture this)\s+[^.!?]*$',  # Incomplete thought
        ]

        for pattern in incomplete_patterns:
            if re.search(pattern, first_para):
                # Check if there's a follow-up that completes it
                if len(lines) > 1 and lines[1].strip():
                    # Has follow-up, probably okay
                    continue
                else:
                    return False, f"Hook appears incomplete: '{first_para}'"

        return True, "Hook looks complete"

    def check_for_complete_cta(self, content: str) -> Tuple[bool, str]:
        """Verify post has a call-to-action."""
        cta_keywords = [
            'comment', 'share', 'save', 'dm', 'message',
            'link in', 'reply', 'tag', 'reach out',
            'book a', 'schedule a', 'grab your', 'download',
            'let me know', 'what do you think', 'thoughts?',
            'questions?', 'agree or disagree'
        ]

        content_lower = content.lower()
        found_cta = any(keyword in content_lower for keyword in cta_keywords)

        if not found_cta:
            return False, "No CTA found in post"

        return True, "CTA present"

    def check_content_length(self, content: str) -> Tuple[bool, str]:
        """Verify post has sufficient content."""
        body_length = len(content)

        if body_length < self.MIN_CONTENT_LENGTH:
            return False, f"Post too short: {body_length} chars (min: {self.MIN_CONTENT_LENGTH})"

        return True, f"Content length okay: {body_length} chars"

    def check_topic_relevance(self, content: str, post_topic: str) -> Tuple[bool, str]:
        """Check if content is relevant to the topic and contains key concepts."""
        if not post_topic:
            return True, "No topic specified"

        # Extract key words from topic (nouns, verbs, key concepts)
        topic_lower = post_topic.lower()
        content_lower = content.lower()

        # Split topic into meaningful words (filter out common words)
        common_words = {'a', 'an', 'the', 'and', 'or', 'to', 'for', 'of', 'in', 'on', 'is', 'are', 'with', 'by'}
        topic_words = [word for word in topic_lower.split() if word not in common_words and len(word) > 3]

        # Count how many topic keywords appear in content
        keywords_found = sum(1 for word in topic_words if word in content_lower)
        coverage = keywords_found / len(topic_words) if topic_words else 1.0

        if coverage < self.MIN_TOPIC_KEYWORD_COVERAGE:
            return False, f"Low topic relevance: only {keywords_found}/{len(topic_words)} key concepts mentioned ({coverage:.0%})"

        # Check for instructional indicators when title suggests teaching
        instructional_keywords = ['how to', 'step', 'technique', 'method', 'here\'s', 'here is', 'follow', 'example', 'template', 'prompt']
        has_instructional = any(keyword in content_lower for keyword in instructional_keywords)

        if 'how to' in post_topic.lower() and not has_instructional:
            return False, "Title promises 'how-to' content but post lacks instructional steps or examples"

        return True, "Topic relevance verified"

    def check_example_quality(self, content: str) -> Tuple[bool, str]:
        """Check quality of examples in educational content.

        Validates:
        - Examples don't contain generic placeholders like {company}, {your_business}
        - Sufficient concrete examples provided
        - Examples show specific business scenarios
        """
        if 'example' not in content.lower():
            return True, "No examples to check"

        # Check for common placeholder patterns in examples
        placeholder_patterns = [
            r'\{[a-z_]+\}',  # Generic placeholders like {company}, {year}
            r'\[your [a-z_]+\]',  # [your business], [your company]
            r'\[COMPANY\]', r'\[PRODUCT\]', r'\[NAME\]',  # Uppercase placeholders
            r'<[a-z_]+>',  # Angle bracket placeholders
        ]

        import re
        for pattern in placeholder_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return False, "Examples contain unfilled placeholders - should be specific and concrete"

        return True, "Example quality verified"

    def check_step_completeness(self, content: str) -> Tuple[bool, str]:
        """Check completeness of step-by-step instructions.

        Validates:
        - Steps are numbered (1., 2., 3. or Step 1: Step 2: etc.)
        - Each step has actionable instruction
        - Logical sequence is maintained
        """
        if 'step' not in content.lower():
            return True, "No steps to check"

        # Look for numbered steps
        step_patterns = [
            r'^\d+\.\s+',  # 1. Step description
            r'^Step\s+\d+:',  # Step 1: description
            r'^\d+\)\s+',  # 1) Step description
        ]

        lines = content.split('\n')
        step_count = 0
        step_numbers = []

        import re
        for line in lines:
            for pattern in step_patterns:
                if re.match(pattern, line.strip(), re.IGNORECASE):
                    step_count += 1
                    # Extract step number
                    match = re.search(r'\d+', line)
                    if match:
                        step_numbers.append(int(match.group()))

        if step_count == 0:
            return True, "No numbered steps found (might use descriptive format)"

        if step_count < 2:
            return False, "Only found 1 step - should have multiple steps"

        # Check if steps are in logical sequence (numbers should be consecutive or close)
        if step_numbers:
            # Check for major gaps in numbering
            sorted_nums = sorted(step_numbers)
            for i in range(len(sorted_nums) - 1):
                if sorted_nums[i+1] - sorted_nums[i] > 2:
                    return False, f"Steps not in logical sequence: gaps detected in numbering"

        return True, f"Step completeness verified: {step_count} steps found"

    def check_for_truncation(self, content: str) -> Tuple[bool, str]:
        """Detect if content is truncated (ends mid-word or incomplete).

        Scans ALL paragraphs for mid-word truncations, not just the last line.

        Flags:
        - Text ending with incomplete word (e.g., "Here's what actu")
        - Missing closing punctuation or hanging sentence
        - Text cuts off at unusual character in any line
        """
        if not content or len(content.strip()) < 10:
            return True, "Content too short to assess truncation"

        # Remove hashtags from the end to check the actual body
        content_stripped = content.rstrip()

        # Split into lines, skip hashtag lines
        lines = content_stripped.split('\n')
        body_lines = []
        for line in lines:
            if line.strip() and not line.strip().startswith('#'):
                body_lines.append(line)

        if not body_lines:
            return True, "No body content to check"

        # Common incomplete word patterns (mid-word cuts)
        incomplete_patterns = [
            r'actu$',      # actually, actual, etc.
            r'begi$',      # begin, beginning, etc.
            r'reali$',     # realize, reality, etc.
            r'happe$',     # happen, happened, etc.
            r'speci$',     # special, specific, etc.
            r'complet$',   # complete, completion, etc.
            r'produ$',     # produce, product, etc.
            r'intere$',    # interest, interesting, etc.
            r'busine$',    # business, etc.
            r'solut$',     # solution, solve, etc.
            r'mos$',       # most, etc.
            r'tho$',       # though, thorough, etc.
            r'tha$',       # that, than, etc.
            r'wh$',        # which, what, where, etc.
        ]

        # Valid English word endings that should NOT be flagged (even if consonant clusters)
        valid_endings = [
            r'ly$',        # weekly, daily, only, etc.
            r'ing$',       # running, testing, etc.
            r'tion$',      # action, solution, etc.
            r'ness$',      # business, happiness, etc.
            r'ment$',      # agreement, statement, etc.
            r'er$',        # better, faster, etc.
            r'ed$',        # worked, tested, etc.
            r'll$',        # will, still, etc.
            r'nd$',        # and, friend, etc.
            r'st$',        # best, most, test, etc.
            r'ck$',        # back, check, etc.
        ]

        # Scan EVERY line in the body for truncation patterns
        for line_idx, line in enumerate(body_lines):
            if not line.strip():
                continue

            # Skip short label lines (like "🔹 Step 1: Map") - these are intentional formatting
            # These are typically <30 chars and don't represent real content
            if len(line.strip()) < 30 and re.search(r'^[🔹🎯📌✨•→\-]\s*.*:\s*\w+$', line.strip()):
                continue  # This is an intentional label, not truncation

            # Get the last word of this line
            words = line.split()
            if not words:
                continue

            last_word = words[-1]

            # Remove punctuation temporarily for pattern checking
            word_clean = re.sub(r'[,;:!?.🔄♻️\-—].*$', '', last_word).lower()

            # Check if word ends with a valid English ending (skip if it does)
            is_valid_ending = any(re.search(pattern, word_clean) for pattern in valid_endings)

            if is_valid_ending:
                # This is a complete word with valid English ending
                continue

            # Check if this word matches any incomplete pattern
            for pattern in incomplete_patterns:
                if re.search(pattern, word_clean):
                    # Verify it's actually incomplete (no punctuation at end)
                    if not re.search(r'[.!?:;,\)]$', last_word):
                        # This is a truncated line
                        line_preview = line[:80] + "..." if len(line) > 80 else line
                        return False, f"Content appears truncated - Line {line_idx}: ends mid-word '{last_word}'"

        # Also check that content ends properly (last line before hashtags)
        last_content_line = body_lines[-1]
        if last_content_line:
            valid_endings = r'[.!?\)]$|[🔄♻️✨📌💡🎯]\s*$'
            if not re.search(valid_endings, last_content_line.strip()):
                # Check if last sentence is complete
                if len(last_content_line.split()) < 3:
                    return False, "Content appears incomplete - final line too short and doesn't end with punctuation"

        return True, "Content completeness verified"

    def check_hook_authenticity(self, content: str) -> Tuple[bool, str]:
        """Check if hook is authentic and specific, not generic/bland.

        Detects:
        - Generic opening patterns (Most business owners, Most teams, etc.)
        - Lack of specific details (numbers, names, personal pronouns)
        - Robotic phrasing patterns
        """
        lines = content.split('\n')
        if not lines:
            return True, "No content to check"

        hook_text = lines[0].strip()
        if not hook_text:
            return True, "No hook found"

        # Generic patterns that indicate bland, reused hooks
        generic_patterns = [
            r'most\s+(business owners|companies|teams|organizations|people)',  # Most X still...
            r'.*\s+still\s+(do|use|spend|waste)',  # ...still do X
            r'here\'s\s+what\s+(kills|breaks|destroys|ruins)',  # Here's what kills
            r'^i\s+realized\s+our\s+',  # I realized our...
            r'nobody\s+(is|\'s)\s+talking\s+about',  # Nobody's talking about
            r'^here\'s\s+the\s+(dirty\s+)?secret',  # Here's the secret
        ]

        # Check for generic hook patterns (these are overused templates)
        for pattern in generic_patterns:
            if re.search(pattern, hook_text.lower()):
                # Check if it has specific details to make it authentic
                # Look for numbers, specific times, names, or specific outcomes
                has_specifics = bool(re.search(r'\d+\s*(minutes?|hours?|days?|weeks?|%|times?)', hook_text)) or \
                               bool(re.search(r'\$\d+', hook_text)) or \
                               bool(re.search(r'[A-Z][a-z]+\s+[A-Z][a-z]+', hook_text))  # Names

                if not has_specifics:
                    return False, f"Hook is generic and lacks specific details. Patterns like '{hook_text[:40]}...' feel reused and bland"

        # Check for personal, conversational tone
        # Look for contractions (any word with apostrophe like "here's", "we're", "it's", etc.)
        contractions = re.findall(r'\b\w+\'[a-z]+\b', hook_text, re.IGNORECASE)
        personal_pronouns = re.findall(r'\b(I\s|we\s|our\s|i\'|we\'|our\')', hook_text, re.IGNORECASE)

        if not contractions and not personal_pronouns:
            return False, f"Hook lacks personal voice - no contractions or personal pronouns detected. Consider adding conversational language"

        return True, "Hook appears authentic and specific"

    def check_ai_generation_markers(self, content: str) -> Tuple[bool, str]:
        """Detect AI-generated content markers that indicate inauthentic writing.

        Flags:
        - Emoji frames (before/after emojis around sections)
        - Perfect grammar everywhere (no typos, contractions, natural imperfections)
        - Robotic phrase patterns
        - Corporate/corporate language
        """
        issues = []

        # Check for emoji frame patterns
        emoji_frame_patterns = [
            r'🎯.*?🎯',
            r'📌.*?📌',
            r'⭐.*?⭐',
            r'👉.*?👈',
        ]
        for pattern in emoji_frame_patterns:
            if re.search(pattern, content, re.DOTALL):
                issues.append("Emoji frames detected - this is a hallmark of AI-generated LinkedIn content")
                break

        # Check for robotic phrase patterns
        robotic_phrases = [
            r'\b(as\s+an\s+ai|as\s+a\s+language\s+model)',
            r'\b(in\s+conclusion|to\s+summarize|in\s+summary)',
            r'\b(it\'s\s+important\s+to\s+note)',
            r'\b(without\s+further\s+ado)',
            r'\b(on\s+the\s+other\s+hand)',
            r'\b(the\s+bottom\s+line\s+is)',
        ]

        content_lower = content.lower()
        for pattern in robotic_phrases:
            if re.search(pattern, content_lower):
                issues.append("Robotic phrasing detected - sounds like corporate/AI template language")
                break

        # Check for corporate language patterns
        corporate_words = [
            r'\bsynergy\b', r'\bparadigm\b', r'\bleverage\b', r'\bcircle\s+back\b',
            r'\btouchpoint\b', r'\bvertical\b', r'\bblueprint\b', r'\bstrategic\b'
        ]

        for word in corporate_words:
            if re.search(word, content_lower):
                issues.append("Corporate jargon detected - feels less authentic than conversational business language")
                break

        if issues:
            return False, " | ".join(issues)

        return True, "No AI generation markers detected"

    def check_hook_repetition(self, hook_text: str, existing_posts: List[Dict]) -> Tuple[bool, str]:
        """Check if hook is too similar to hooks in existing posts.

        Prevents repeated hooks from different posts.
        """
        if not existing_posts:
            return True, "No existing posts to compare"

        hook_words = set(hook_text.lower().split())
        if len(hook_words) < 5:
            return True, "Hook too short to compare"

        for existing in existing_posts:
            existing_content = existing.get('fields', {}).get('Post Content', '')
            if not existing_content:
                continue

            # Extract first paragraph as potential hook
            existing_lines = existing_content.split('\n')
            existing_hook = existing_lines[0].strip() if existing_lines else ""

            if not existing_hook:
                continue

            existing_words = set(existing_hook.lower().split())

            # Check word overlap
            common_words = hook_words & existing_words
            overlap_ratio = len(common_words) / max(len(hook_words), len(existing_words)) if max(len(hook_words), len(existing_words)) > 0 else 0

            # If >50% of words overlap in hook, it's probably the same hook template
            if overlap_ratio > 0.5 and len(common_words) > 3:
                return False, f"Hook too similar to existing post (>50% word overlap detected). This suggests hook repetition across posts"

        return True, "Hook is unique"

    def check_excessive_technical_detail(self, content: str, automation_mode: bool = True) -> Tuple[bool, str]:
        """Check if post has excessive technical workflow description.

        For automation showcase posts, too much technical detail kills engagement.
        Looks for long workflow explanations that nobody will read.
        """
        if not automation_mode:
            return True, "Not in automation mode"

        # Look for workflow sections
        workflow_keywords = ['workflow', 'how it works', 'process', 'steps']
        has_workflow_section = any(keyword in content.lower() for keyword in workflow_keywords)

        if not has_workflow_section:
            return True, "No workflow section detected"

        # Find sections with "workflow" or "how it works"
        lines = content.split('\n')
        in_workflow = False
        workflow_lines = []

        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ['workflow', 'how it works', 'process']):
                in_workflow = True
                workflow_lines = []
            elif in_workflow:
                # Check if we've left the workflow section
                if line.strip() == '' or any(keyword in line_lower for keyword in ['impact', 'example', 'what', 'result']):
                    # End of workflow section
                    in_workflow = False
                    workflow_text = '\n'.join(workflow_lines)

                    # Check if workflow explanation is too long
                    if len(workflow_text) > 600:
                        return False, f"Workflow explanation is too detailed ({len(workflow_text)} chars). Cut technical details to focus on business impact instead"

                    workflow_lines = []
                else:
                    workflow_lines.append(line)

        return True, "Technical detail level appropriate"

    def check_authenticity_signals(self, content: str) -> Tuple[bool, str]:
        """Check for genuine authenticity signals in the content.

        Looks for:
        - Specific numbers (not round/generic)
        - Personal pronouns and ownership language
        - Concrete examples with scenarios
        - Acknowledgment of challenges
        """
        signals = {
            'specific_numbers': 0,
            'personal_language': 0,
            'concrete_examples': 0,
            'vulnerability': 0,
        }

        # Check for specific numbers (45 minutes, 7 days, not just "10")
        specific_numbers = re.findall(r'(\d+)\s*(minutes?|hours?|days?|weeks?|%)', content)
        if specific_numbers:
            signals['specific_numbers'] = len(specific_numbers)

        # Check for personal pronouns and ownership language
        personal_patterns = [
            r'\bI\s+',
            r'\bwe\s+',
            r'\bour\s+',
            r'\bI\'ve\s+',
            r'\bwe\'ve\s+',
        ]
        for pattern in personal_patterns:
            signals['personal_language'] += len(re.findall(pattern, content, re.IGNORECASE))

        # Check for concrete examples (specific names, scenarios, not placeholders)
        # Look for sentences with proper nouns or specific business scenarios
        concrete_keywords = ['client', 'team member', 'sales rep', 'manager', 'owner', 'business', 'company']
        for keyword in concrete_keywords:
            signals['concrete_examples'] += content.lower().count(keyword)

        # Check for vulnerability (acknowledgment of challenges/mistakes)
        vulnerability_keywords = [
            'mistake', 'wrong', 'failed', 'struggle', 'challenge', 'lost', 'expensive',
            'realized', 'discovered', 'admit', 'wasn\'t'
        ]
        for keyword in vulnerability_keywords:
            signals['vulnerability'] += content.lower().count(keyword)

        # Calculate authenticity score
        total_signals = sum(signals.values())

        if total_signals < 3:
            return False, f"Low authenticity signals detected. Add specific numbers, personal pronouns, concrete examples, or acknowledge real challenges"

        return True, f"Authenticity signals present: {total_signals} detected (numbers:{signals['specific_numbers']}, personal:{signals['personal_language']}, examples:{signals['concrete_examples']}, vulnerability:{signals['vulnerability']})"

    def check_for_duplicates(self, post_content: str, existing_posts: List[Dict]) -> Tuple[bool, str, float]:
        """Check if post is too similar to existing posts."""
        if not existing_posts:
            return True, "No existing posts to compare against", 0.0

        max_similarity = 0.0
        most_similar_title = ""

        for existing in existing_posts:
            existing_content = existing.get('fields', {}).get('Post Content', '')
            if not existing_content:
                continue

            similarity = self.calculate_similarity(post_content, existing_content)

            if similarity > max_similarity:
                max_similarity = similarity
                most_similar_title = existing.get('fields', {}).get('Title', 'Unknown')

            # If too similar to any post, flag it
            if similarity > self.MAX_SIMILARITY_TO_EXISTING:
                return False, f"Too similar to: '{most_similar_title}' ({similarity:.1%} match)", similarity

        return True, f"Unique content (max similarity: {max_similarity:.1%})", max_similarity

    def validate_post(self, post: Dict, check_duplicates: bool = True) -> Dict:
        """
        Comprehensive quality check on a post.
        Returns: {
            'passes_qc': bool,
            'issues': List[str],
            'warnings': List[str],
            'details': Dict with check results
        }
        """
        issues = []
        warnings = []
        details = {}

        content = post.get('full_content', '')
        title = post.get('title', '')
        topic = post.get('post_topic', '')
        automation_mode = post.get('automation_showcase_mode', False)

        # Check 0: Topic relevance
        topic_ok, topic_msg = self.check_topic_relevance(content, topic)
        details['topic_relevance'] = {'passed': topic_ok, 'message': topic_msg}
        if not topic_ok:
            issues.append(f"Topic Relevance: {topic_msg}")

        # Check 1: Content length
        check_passed, msg = self.check_content_length(content)
        details['content_length'] = {'passed': check_passed, 'message': msg}
        if not check_passed:
            issues.append(f"Content Length: {msg}")

        # Check 1.5: Truncation (NEW - CRITICAL - catch incomplete posts before they upload)
        trunc_ok, trunc_msg = self.check_for_truncation(content)
        details['truncation'] = {'passed': trunc_ok, 'message': trunc_msg}
        if not trunc_ok:
            issues.append(f"Truncation Alert: {trunc_msg}")

        # Check 2: Placeholder variables
        placeholders = self.check_for_placeholders(content)
        details['placeholders'] = {'found': placeholders, 'passed': len(placeholders) == 0}
        if placeholders:
            issues.append(f"Placeholder Variables: Found unfilled variables: {', '.join(placeholders)}")

        # Check 3: Framework labels
        labels = self.check_for_framework_labels(content)
        details['framework_labels'] = {'found': labels, 'passed': len(labels) == 0}
        if labels:
            issues.append(f"Framework Labels: Found {len(labels)} labels that shouldn't be visible: {', '.join(labels)}")

        # Check 4: Complete hook
        hook_ok, hook_msg = self.check_for_complete_hook(content)
        details['hook_completeness'] = {'passed': hook_ok, 'message': hook_msg}
        if not hook_ok:
            warnings.append(f"Hook Quality: {hook_msg}")

        # Check 5: Hook authenticity (NEW - critical for LinkedIn engagement)
        auth_ok, auth_msg = self.check_hook_authenticity(content)
        details['hook_authenticity'] = {'passed': auth_ok, 'message': auth_msg}
        if not auth_ok:
            issues.append(f"Hook Authenticity: {auth_msg}")

        # Check 6: AI generation markers (NEW - flag inauthentic AI writing patterns)
        ai_ok, ai_msg = self.check_ai_generation_markers(content)
        details['ai_markers'] = {'passed': ai_ok, 'message': ai_msg}
        if not ai_ok:
            issues.append(f"Authenticity: {ai_msg}")

        # Check 7: Complete CTA
        cta_ok, cta_msg = self.check_for_complete_cta(content)
        details['cta_presence'] = {'passed': cta_ok, 'message': cta_msg}
        if not cta_ok:
            issues.append(f"CTA: {cta_msg}")

        # Check 8: Excessive technical detail (NEW - for automation mode)
        if automation_mode:
            tech_ok, tech_msg = self.check_excessive_technical_detail(content, automation_mode=True)
            details['technical_detail'] = {'passed': tech_ok, 'message': tech_msg}
            if not tech_ok:
                issues.append(f"Technical Detail: {tech_msg}")

        # Check 9: Authenticity signals (NEW - check for genuine voice)
        auth_signals_ok, auth_signals_msg = self.check_authenticity_signals(content)
        details['authenticity_signals'] = {'passed': auth_signals_ok, 'message': auth_signals_msg}
        if not auth_signals_ok:
            issues.append(f"Authenticity Signals: {auth_signals_msg}")

        # Check 10: Example quality (for educational content)
        example_ok, example_msg = self.check_example_quality(content)
        details['example_quality'] = {'passed': example_ok, 'message': example_msg}
        if not example_ok:
            issues.append(f"Example Quality: {example_msg}")

        # Check 11: Step completeness (for educational content)
        step_ok, step_msg = self.check_step_completeness(content)
        details['step_completeness'] = {'passed': step_ok, 'message': step_msg}
        if not step_ok:
            issues.append(f"Step Completeness: {step_msg}")

        # Check 12: Hook repetition (NEW - prevent same hooks across posts)
        if check_duplicates:
            existing_posts = self.fetch_existing_posts()

            # Check for hook repetition
            hook_text = content.split('\n')[0] if content else ""
            hook_rep_ok, hook_rep_msg = self.check_hook_repetition(hook_text, existing_posts)
            details['hook_repetition'] = {'passed': hook_rep_ok, 'message': hook_rep_msg}
            if not hook_rep_ok:
                issues.append(f"Hook Repetition: {hook_rep_msg}")

            # Check for duplicates
            dup_ok, dup_msg, similarity = self.check_for_duplicates(content, existing_posts)
            details['duplicate_check'] = {'passed': dup_ok, 'message': dup_msg, 'max_similarity': similarity}
            if not dup_ok:
                issues.append(f"Duplicate Detection: {dup_msg}")

        # Determine overall pass/fail
        passes_qc = len(issues) == 0

        return {
            'passes_qc': passes_qc,
            'issues': issues,
            'warnings': warnings,
            'details': details,
            'title': title
        }

    def print_qc_report(self, qc_result: Dict, post_title: str = ""):
        """Pretty-print QC report."""
        status_icon = "✅" if qc_result['passes_qc'] else "❌"

        print(f"\n{status_icon} QC Report: {post_title or qc_result['title'][:60]}")
        print("=" * 80)

        if qc_result['issues']:
            print("\n❌ ISSUES (must fix):")
            for issue in qc_result['issues']:
                print(f"   • {issue}")

        if qc_result['warnings']:
            print("\n⚠️  WARNINGS (review):")
            for warning in qc_result['warnings']:
                print(f"   • {warning}")

        if qc_result['passes_qc']:
            print("\n✅ All checks passed!")

        print("=" * 80)


def main():
    """Test the quality checker."""
    checker = PostQualityChecker()

    # Test with a sample post
    test_post = {
        'title': 'Test Post',
        'full_content': """This is a test post that's incomplete.

        Here's the body with content.

        What do you think?"""
    }

    result = checker.validate_post(test_post)
    checker.print_qc_report(result)


if __name__ == "__main__":
    main()
