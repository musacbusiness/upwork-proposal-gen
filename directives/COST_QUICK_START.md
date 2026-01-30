# Cost Optimization Quick Start

> Save this—you'll reference it constantly. Updated every time we learn something new.

## The 3 Questions to Ask for Every Task

```
Task received
│
├─ 1. Can I do this without Claude API? → YES → Do it free
│
├─ 2. What's the complexity? → Pick model:
│     SIMPLE (extraction) → Haiku 80% cheaper
│     MEDIUM (writing) → Sonnet 40% cheaper
│     HARD (novel thinking) → Opus (accept cost)
│
└─ 3. Optimize the approach:
      5+ items? → Batch (50% off)
      Repeating system prompt? → Cache (90% off after first)
      Long input? → Compress JSON format (40-60% off)
      Variable output? → Constrain length (20% off)
```

## Model Selection Cheat Sheet

| What You're Doing | Model | Cost | Examples |
|---|---|---|---|
| Extract/reformat data | Haiku | $1/$5 | Job titles, JSON parsing, summaries |
| Generate under 500 words | Sonnet | $3/$15 | Proposals, LinkedIn posts, emails |
| Complex reasoning | Opus | $5/$25 | Architecture, troubleshooting, research |
| ❌ Always use expensive model | ❌ Never | ❌ Always waste money | ❌ Avoid this |

## Cost Saving Tactics (Ordered by Ease)

### Tactic 1: Prompt Caching (90% savings, no quality risk)

```python
from execution.utils.cost_optimizer import PromptCache

# Your system prompt repeats? Cache it!
system = [PromptCache.add_cache_control(INSTRUCTIONS)]

# First call: Normal cost
# Next 10 calls (within 5 min): 0.1x cost
# Break-even: 2 calls
```

✅ **Safe to use always**

### Tactic 2: Model Downgrade (40-80% savings, test first)

```python
from execution.utils.cost_optimizer import ModelSelector

# Simple task → Use cheaper model
model = ModelSelector.select("image_prompt")  # Returns Haiku

# But: Test on 20 samples, verify quality stays >90%
```

⚠️ **Test before production**

### Tactic 3: Compress Input (20-60% savings, no quality risk)

```python
from execution.utils.cost_optimizer import PromptCompressor

# Convert to JSON (40-60% token savings)
job_json = PromptCompressor.to_json({
    "title": job.title,
    "desc": job.description[:500],  # Truncate
    "budget": job.budget
})

# Truncate long text intelligently
summary = PromptCompressor.truncate_description(transcript, max_chars=500)
```

✅ **Safe to use always**

### Tactic 4: Batch Processing (50% savings, requires patience)

```python
from execution.utils.cost_optimizer import BatchProcessor

# Processing 5+ items? Batch them
processor = BatchProcessor(client)
batch_id = processor.create_batch(
    items=[job1, job2, job3],
    model="claude-sonnet-4-5",
    system_prompt="Analyze jobs"
)

# Results in <1 hour, 50% discount on all tokens
results = processor.retrieve_batch(batch_id)
```

✅ **Use for non-urgent daily tasks** (LinkedIn posts, job filtering)

### Tactic 5: Hybrid Deterministic + AI (70% savings, requires planning)

```python
# Instead of full AI proposal ($0.50)
# Use template + small AI hook ($0.05)

# Deterministic (free)
name = extract_name(email)
skills = job.skills & my_skills

# Small AI call (Haiku, 200 tokens)
hook = ai_generate_hook(job, model="haiku", max_tokens=200)

# Assemble
proposal = template.format(name=name, hook=hook, skills=skills)
```

⚠️ **Plan ahead, test quality**

## Cost Tracking

```bash
# Check costs for last 7 days
python -c "
from execution.utils.cost_optimizer import CostTracker
tracker = CostTracker()
print(tracker.get_summary(days=7))
"

# Expected output:
# {
#   "days": 7,
#   "total_cost": 45.67,
#   "entries": 234,
#   "by_model": {
#     "claude-haiku-4-5": 5.43,
#     "claude-sonnet-4-5": 28.54,
#     "claude-opus-4-5": 11.70
#   }
# }
```

## Quality Validation Template

Before deploying cost optimization:

```python
from execution.utils.cost_optimizer import QualityValidator

# 1. Get baseline (with expensive model)
baseline_outputs = [expensive_model(job) for job in test_jobs]
baseline_score = QualityValidator.baseline_quality_score(
    baseline_outputs,
    metric_fn=lambda x: your_quality_score(x)  # Return 0-100
)

# 2. Test optimization
optimized_outputs = [cheap_model(job) for job in test_jobs]
optimized_score = QualityValidator.baseline_quality_score(optimized_outputs, metric_fn)

# 3. Check acceptance
result = QualityValidator.compare_quality(baseline_score, optimized_score)
print(result["recommendation"])  # Will say PASS/FAIL/MARGINAL
```

## Decision Tree (Flowchart)

```
Task received
│
├─ Is this an API call? NO → Do it without API
│
├─ Check task type
│  ├─ Extraction → Haiku
│  ├─ Writing → Sonnet
│  └─ Novel → Opus
│
├─ Can you compress input?
│  └─ YES → Use JSON format, truncate to first 500 chars
│
├─ Does prompt repeat?
│  └─ YES → Add cache_control: ephemeral
│
├─ 5+ items to process?
│  └─ YES → Batch them (50% off, <1hr)
│
└─ Execute, log cost, done
```

## Files You Need to Know

- **[directives/cost_optimization.md](directives/cost_optimization.md)** - Full decision framework
- **[execution/utils/cost_optimizer.py](execution/utils/cost_optimizer.py)** - All the tools
- **[directives/claude_code_system_prompt.md](directives/claude_code_system_prompt.md)** - How Claude Code operates

## Red Flags (Don't Do These)

❌ **Never truncate** if you're removing critical info
❌ **Never cache** content that changes daily
❌ **Never batch** when real-time response is needed
❌ **Never downgrade model** without testing quality first
❌ **Never ignore** quality baseline—it's your safety net

## Green Flags (Always Safe)

✅ Prompt caching (identical outputs, cheaper)
✅ JSON input formatting (more efficient, clearer)
✅ Output length constraints (actually improve clarity)
✅ Using Haiku for simple tasks (proven to work)
✅ Tracking costs (visibility is safety)

## Your Job as Orchestrator

When you get a task, think:

1. **"Can I avoid API call entirely?"** (Best option)
2. **"What's the cheapest model that works?"** (Haiku→Sonnet→Opus)
3. **"How can I compress this?"** (JSON, truncate, constrain)
4. **"Should this batch/cache?"** (5+ items or repeating content)
5. **"Have I validated quality?"** (≥90% baseline before production)

That's it. Everything else follows from those 5 questions.

## Expected Results

After implementing these optimizations:

| Metric | Before | After | Savings |
|--------|--------|-------|---------|
| Monthly spend | $500 | $50-75 | 85-90% |
| Cost per proposal | $0.50 | $0.05 | 90% |
| Cost per LinkedIn post | $0.30 | $0.05 | 85% |
| Quality | Baseline | ≥90% baseline | 0% loss |

## When to Break the Rules

✋ **Use Opus without hesitation if:**
- User explicitly asks for highest quality
- Task is novel/complex (you can't judge with Haiku)
- Cost optimization already applied elsewhere
- Troubleshooting (clarity > cost)

Just tell the user you're using expensive model and why.

## One More Thing

**This is a living document.** Every time you learn something:
- Optimization that works better? → Update this
- Quality threshold that changes? → Update this
- New pattern discovered? → Update this

The goal is continuous improvement. Future instances of Claude Code will benefit from your learnings.
