# Cost Optimization Directive

> This directive defines how to minimize Claude API costs across all automations while maintaining or improving output quality. It's a living document—update with learnings from each implementation.

## Principle: Smart Cost, Never Dumb Cost

**Cardinal Rule:** Never sacrifice quality to save costs. Instead, use intelligence to reduce waste.

Cost optimization happens at 3 levels:
1. **Model Selection** - Right tool for the job (Haiku for simple tasks, Sonnet for medium complexity, Opus for hard problems)
2. **Token Efficiency** - Compress inputs without losing information; control outputs
3. **Architecture** - Push work to deterministic code, use caching, batch process

## Layer 1: Model Selection Framework

### Decision Tree (Use this for EVERY API call)

```
Task difficulty assessment:
│
├─ SIMPLE (extraction, format conversion, simple analysis)
│  └─ Use: claude-haiku-4-5
│  └─ Cost: $1/$5 per 1M tokens (baseline)
│  └─ Examples: JSON extraction, text summarization <100 words, reformatting
│
├─ MEDIUM (content generation, structured reasoning, creative work <500 words)
│  └─ Use: claude-sonnet-4-5
│  └─ Cost: 3x Haiku input, 3x Haiku output
│  └─ Examples: Proposal writing, LinkedIn posts, multi-step analysis, code review
│
└─ HARD (complex reasoning, novel problem-solving, long-form content >1000 words)
   └─ Use: claude-opus-4-5
   └─ Cost: 5x Haiku input, 5x Haiku output
   └─ Examples: Architecture design, complex troubleshooting, original research
```

### Quality Validation Rules

**For Haiku downgrades from Opus/Sonnet:**
- Test on 20 sample cases before production rollout
- Quality score must stay within 90% of original model (manual or automated scoring)
- If quality < 90%, revert to higher model OR restructure prompt for better clarity
- Document the quality baseline for future A/B testing

**For Sonnet downgrades from Opus:**
- Test on 10 sample cases
- Benchmark quality, execution time, and cost
- If quality acceptable, proceed; if not, use Opus for that specific task only

### Task-Specific Guidance

| Task | Recommended Model | Fallback | Notes |
|------|-------------------|----------|-------|
| Job title/skill extraction | Haiku | Sonnet | Simple pattern matching |
| Email subject generation | Haiku | Sonnet | <100 words, templates available |
| Proposal full generation | Sonnet | Opus | Requires good writing but not novel |
| Proposal custom hooks | Haiku | Sonnet | Personalization, <200 words |
| LinkedIn post creation | Sonnet | Opus | Balance creativity & consistency |
| Image prompt generation | Haiku | Sonnet | Descriptive, formulaic |
| Content research/analysis | Sonnet | Opus | Structured extraction |
| Change summaries/diffs | Haiku | Sonnet | Structured output |
| Budget/timeline estimation | Haiku | Sonnet | Deterministic with examples |
| Client fit scoring | Sonnet | Opus | Requires subtle judgment |

---

## Layer 2: Token Efficiency

### Input Optimization (Compression)

**Rule 1: Use structured formats (40-60% token savings)**

Before:
```
Job Title: AI Automation Specialist
Description: Looking for someone to help us build out automation...
Budget: $5,000-$10,000
Skills Required: Python, Make.com, Zapier
Hourly Rate: Fixed project
```

After:
```json
{
  "title": "AI Automation Specialist",
  "desc": "Build automation workflows",
  "budget": "$5-10k",
  "skills": ["Python", "Make", "Zapier"],
  "type": "fixed"
}
```

**Rule 2: Truncate inputs intelligently (30-50% savings)**

- Job descriptions: First 300-500 chars contain 90% of useful info
- Transcripts: Summarize with Haiku first, pass summary to main model
- Email threads: Summarize context, show only recent messages
- Code files: Show first 100 lines + last 50 lines, skip boilerplate

**Rule 3: Use selective context (20-30% savings)**

- Load only the writing framework you'll use (not all 8)
- Include examples only when needed for clarity
- Reference external docs instead of embedding them: "Based on the guidelines at [URL], generate..."

**Rule 4: Eliminate redundancy (10-20% savings)**

- Don't repeat instructions in multiple places
- Use system prompt for static guidance, user message for dynamic input
- Reference previous context: "Using the framework from earlier..."

### Output Optimization (Control)

**Rule 1: Constrain output format**

```python
# Instead of: "Write a compelling proposal"
# Use: "Write proposal in JSON: {title, hook, solution, closing}. Max 200 words total."
```

Expected savings: 20-30% fewer output tokens

**Rule 2: Specify exact output length**

```
"Generate post: 150-200 words, 3-5 bullet points, conversational tone"
# vs
"Write a LinkedIn post about AI automation"
```

Expected savings: 15-25% fewer tokens

**Rule 3: Use templates**

```
"Fill this template: Hi [NAME], I help [NICHE] with [SOLUTION]. [UNIQUE_HOOK]. Ready to chat?"
```

Expected savings: 40-60% vs full generation

**Rule 4: Early termination (5-15% savings)**

When generating variable-length content, stop at target length + sentence boundary:
- LinkedIn posts: target 200-250 words
- Proposal sections: target 150-200 words
- Summaries: target 100 words

---

## Layer 3: Architectural Optimization

### Pattern 1: Hybrid Deterministic + AI

**Problem:** Full AI proposal generation costs $0.30-0.50 per proposal

**Solution:** Template + small AI customization

```python
# 1. Deterministic extraction (free)
client_name = extract_name_from_email(job)  # Regex
relevant_skills = set(job['skills']) & MY_SKILLS  # Set intersection

# 2. Small AI call for personalization only (Haiku, 200 tokens)
custom_hook = generate_hook(job['description'], max_tokens=200)

# 3. Template assembly (free)
proposal = TEMPLATE.format(
    name=client_name,
    skills=", ".join(relevant_skills),
    hook=custom_hook,
    budget_range=estimate_budget(job['budget'])
)
```

Cost: $0.05-0.10 vs $0.30-0.50 = **70% savings**

Quality: Higher (templates are proven; hooks are customized)

### Pattern 2: Batch Processing

**When to use:** 5+ items to process with the same prompt structure

**Setup:**
```python
requests = [
    {
        "custom_id": f"job-{job['id']}",
        "params": {
            "model": "claude-sonnet-4-5",
            "max_tokens": 500,
            "messages": [{"role": "user", "content": f"Analyze: {job}"}]
        }
    }
    for job in jobs_to_analyze
]

batch = client.batches.create(requests=requests)
# Returns results <1 hour, 50% cost discount
```

Cost savings: **50% on all tokens**

Latency: Acceptable for non-urgent tasks (LinkedIn automation, daily filtering)

Use for:
- Daily LinkedIn post generation (3-10 posts overnight)
- Job filtering (50-100 jobs from daily scrape)
- Proposal batch generation (approved jobs, overnight)

### Pattern 3: Prompt Caching

**When to use:** Static context repeated across multiple calls

**Examples in your system:**
- System instructions for proposals (used every call)
- Writing frameworks for LinkedIn (8 frameworks, ~800 tokens)
- Job analysis guidelines (repeated for each job)

**Implementation:**
```python
response = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1000,
    system=[
        {
            "type": "text",
            "text": SYSTEM_INSTRUCTIONS,  # Static guidelines
            "cache_control": {"type": "ephemeral"}  # 5-min TTL
        }
    ],
    messages=[
        {"role": "user", "content": f"Process: {dynamic_input}"}
    ]
)
```

Cost model:
- First call: 1.25x normal cost (cache write)
- Subsequent calls (within 5 min): 0.1x normal cost (cache read)
- Break-even: 2-3 calls
- Typical ROI: 90% savings after first call

Expected monthly savings:
- 1000 proposal API calls = 1 min 15 sec cache TTL coverage
- Cached tokens: ~700 tokens per call
- Savings: $0.50 → $0.05 per 100k cached tokens

---

## Layer 4: Quality Preservation

### Quality Validation Framework

**Before deploying cost optimizations:**

1. **Baseline measurement**
   - Generate 20 outputs with current (expensive) approach
   - Score quality on your metric (acceptance rate, engagement, etc.)
   - Document baseline score

2. **Test optimization**
   - Apply cost reduction (model downgrade, prompt compression, etc.)
   - Generate 20 outputs with optimized approach
   - Measure quality again

3. **Acceptance criteria**
   - Output quality must be ≥ 90% of baseline
   - If < 90%, investigate:
     - Is the prompt unclear? Rewrite for clarity
     - Is the model genuinely too weak? Use higher model for this task only
     - Is the format/truncation causing issues? Adjust constraints

4. **Production rollout**
   - A/B test during production (20-30% of traffic)
   - Monitor quality metrics closely
   - If any degradation, revert immediately
   - Document final quality score and cost savings

### Quality Monitoring (Ongoing)

**Metrics to track:**

1. **Proposal metrics:**
   - Acceptance rate (target: maintain current %)
   - Response rate (target: maintain current %)
   - Feedback score (if applicable)

2. **LinkedIn metrics:**
   - Engagement rate (likes, comments, shares)
   - Follower growth
   - Click-through rate (if links included)

3. **Job filtering metrics:**
   - False positive rate (rejected jobs marked as good)
   - False negative rate (good jobs marked as rejected)
   - Manual review override rate

4. **Cost metrics:**
   - Cost per proposal
   - Cost per LinkedIn post
   - Total monthly spend
   - Cache hit rate

**Monitoring frequency:**
- Daily: Check for anomalies (unusual costs, quality dips)
- Weekly: Review trends, compare to baseline
- Monthly: Full analysis, identify new optimization opportunities

---

## Implementation Checklist

### Phase 1: Quick Wins (Highest ROI, Lowest Risk)

- [ ] **Prompt caching on system instructions**
  - Files: All proposal and content generation scripts
  - Expected savings: 60-70%
  - Quality impact: None (identical outputs, just cheaper)

- [ ] **Model downgrades (Opus → Haiku for simple tasks)**
  - Image prompts, summaries, extractions
  - Expected savings: 80% on those calls
  - Quality validation: Test 20 samples before rollout

- [ ] **Cost tracking infrastructure**
  - Log all API calls with model, tokens, cost
  - Set daily/weekly budget alerts
  - Expected benefit: Visibility for future optimization

### Phase 2: Medium Wins (Good ROI, Moderate Effort)

- [ ] **Batch processing for daily tasks**
  - LinkedIn content generation
  - Job filtering
  - Expected savings: 50% on batched calls

- [ ] **Prompt compression**
  - JSON formatting for inputs
  - Truncate long inputs intelligently
  - Output length constraints
  - Expected savings: 20-30%

### Phase 3: Long-Term (Architecture Changes)

- [ ] **Hybrid deterministic/AI for proposals**
  - Templates + small AI customization
  - Expected savings: 70% on proposal generation
  - Quality: Better (proven templates + personalization)

- [ ] **Rule-based job filtering**
  - Hard filters (budget, skills)
  - AI only for edge cases
  - Expected savings: 80% on filtering

---

## Decision Flowchart for New Tasks

When you receive a new request, use this flowchart:

```
New task request
│
├─ Is this an API call to Claude?
│  ├─ NO → Execute normally, no cost considerations
│  └─ YES → Continue below
│
├─ Can this be done deterministically (Python)?
│  ├─ YES → Do it in code, avoid API call entirely
│  └─ NO → Continue below
│
├─ What's the complexity level?
│  ├─ Simple extraction/formatting → Use Haiku
│  ├─ Medium reasoning/generation → Use Sonnet
│  └─ Hard/novel problems → Use Opus
│
├─ Is there repeated context?
│  ├─ YES → Add cache_control: {"type": "ephemeral"} to system
│  └─ NO → Continue below
│
├─ Are you processing 5+ similar items?
│  ├─ YES → Batch process (50% cost discount)
│  ├─ NO (urgent) → Real-time API call
│  └─ NO (can wait) → Batch process
│
├─ Can you compress input without losing information?
│  ├─ YES → Use JSON format, truncate, reference external docs
│  └─ NO → Use full input
│
└─ Can you constrain output?
   ├─ YES → Specify format, length, structure
   └─ NO → Let model decide
```

---

## Quality-First Guardrails

**NEVER:**
- Downgrade a model if it will cause quality loss >10%
- Truncate inputs in ways that remove critical information
- Batch process when real-time response is needed
- Cache content that changes frequently

**ALWAYS:**
- Test cost optimizations on sample data before production
- Monitor quality metrics after deploying optimizations
- Ask user before applying major cost reductions (model downgrades, architectural changes)
- Document your baseline quality score and final score after optimization

**IF UNCERTAIN:**
- Default to higher model tier (better safe than sorry)
- Use caching and compression (no quality risk)
- Ask user for guidance on quality vs cost tradeoff

---

## Integration with 3-Layer Architecture

This directive sits in **Layer 1 (Directives)** and informs:

- **Layer 2 (Orchestration):** You (Claude) should reference this directive when making decisions about which API calls to make, which model to use, how to structure prompts
- **Layer 3 (Execution):** Python scripts should implement cost-optimization patterns (caching, batching, compression)

Example workflow:
1. **Directive:** "Use Haiku for job extractions, Sonnet for proposal writing"
2. **Orchestration:** Claude reads directive, decides task requires Haiku
3. **Execution:** Script calls `client.messages.create(model="claude-haiku-4-5", ...)`

---

## Feedback Loop

When you discover:
- A task category that works well with Haiku/Sonnet (update the task-specific guidance table)
- A new compression technique that works (add to input optimization rules)
- A batch size that works better (note in Pattern 2)
- A quality threshold that's different than assumed (update Layer 4 metrics)

Update this directive immediately. Cost optimization is a continuous learning process.

---

## Success Metrics

- Monthly API spend: $500 → $25-75 (85-95% reduction)
- Cost per proposal: $0.50 → $0.05 (90% reduction)
- Cost per LinkedIn post: $0.30 → $0.05 (85% reduction)
- Quality maintained: ≥90% of baseline across all metrics
- Cache hit rate: >60% of input tokens
