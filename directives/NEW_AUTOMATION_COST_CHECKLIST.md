# New Automation: Cost Optimization Checklist

> Use this checklist whenever building a new automation. It ensures cost optimization is built-in from day one, not bolted on later.

## Phase 1: Planning (Before You Code)

### Requirements Gathering

- [ ] **Understand the workflow**
  - What steps involve Claude API calls?
  - Which are simple (extraction) vs complex (reasoning)?
  - How many items are processed per run?
  - Is this urgent/real-time or can it batch?

- [ ] **Define quality metrics**
  - How will you measure success?
  - What's the baseline quality score? (0-100)
  - What's the minimum acceptable? (typically >90% of baseline)
  - Examples: acceptance rate, engagement, accuracy

### Design with Cost in Mind

- [ ] **Model selection**
  - Task 1 → Haiku/Sonnet/Opus? → Check cost_optimization.md
  - Task 2 → Haiku/Sonnet/Opus?
  - Task N → ...
  - Document decision and reasoning

- [ ] **Batch processing opportunity?**
  - Processing 5+ items? → Plan for batching (50% savings)
  - Real-time required? → Accept no batching
  - Daily task? → Good candidate for batching

- [ ] **Caching opportunities?**
  - System instructions same across calls? → Plan caching (90% savings)
  - Templates that repeat? → Plan caching
  - External docs referenced? → Plan caching

- [ ] **Input compression opportunities?**
  - Long descriptions? → Truncate to first 500 chars
  - Natural language formats? → Use JSON
  - Large context? → Summarize first

- [ ] **Output constraints?**
  - Can you specify exact format? → Reduce token variance
  - Can you constrain length? → Yes, always
  - Can you use templates? → Much cheaper

### Cost Estimation

- [ ] **Estimate monthly volume**
  ```
  Example: Daily LinkedIn automation
  - 5 posts per day × 30 days = 150 posts/month
  - Cost per post (Opus): $0.30
  - Monthly cost: 150 × $0.30 = $45/month
  ```

- [ ] **Estimate with optimizations**
  ```
  - Model downgrade: Opus → Sonnet = $0.15 → $0.10 per post
  - Batch processing: 50% off → $0.05 per post
  - Prompt caching: 90% off after first → $0.01 per post
  - Combined: $45 → ~$2/month
  ```

- [ ] **Set cost target**
  - Unoptimized cost: $X/month
  - Target cost: $X × 15-25% (85-75% savings)
  - Stretch goal: $X × 5-10% (95-90% savings)

---

## Phase 2: Directive Creation

- [ ] **Create [directives/AUTOMATION_NAME.md](directives/AUTOMATION_NAME.md)**

Template:
```markdown
# AUTOMATION_NAME

## Purpose
[What this automation does]

## Workflow Steps
1. [Step 1 with API call or not]
   - Model: Haiku/Sonnet/Opus
   - Cost: $X per call
2. [Step 2]

## Cost Optimization Strategy
- Model selection: Why Haiku/Sonnet/Opus for each step
- Batching: Batch N items, runs every X hours
- Caching: Cache system instructions (save 90%)
- Compression: Truncate inputs to 500 chars, use JSON

## Quality Metrics
- Metric: acceptance_rate
- Baseline: 28% (with original implementation)
- Target: >25% (maintain >90% of baseline)

## Monthly Cost Estimate
- Unoptimized: $45
- Optimized: $2
- Savings: 95%

## Implementation Checklist
- [ ] Directive created
- [ ] Execution script written
- [ ] Cost optimization implemented
- [ ] Quality baselines established
- [ ] Tests passing
```

---

## Phase 3: Implementation

### Setup Cost Utilities

- [ ] **Import cost optimizer utilities**
  ```python
  from execution.utils.cost_optimizer import (
      ModelSelector,
      PromptCompressor,
      PromptCache,
      BatchProcessor,
      CostTracker,
      QualityValidator,
  )
  ```

- [ ] **Initialize cost tracking**
  ```python
  tracker = CostTracker()

  # In your main function:
  response = client.messages.create(...)
  tracker.log_call(
      model=model,
      input_tokens=response.usage.input_tokens,
      output_tokens=response.usage.output_tokens,
      endpoint="automation_name",
      cached_tokens=response.usage.cache_read_input_tokens
  )
  ```

### Implement Model Selection

- [ ] **Use ModelSelector for each API call**
  ```python
  # Don't hardcode models—select intelligently
  model = ModelSelector.select("task_type")  # e.g., "proposal_writing"

  # Or specify quality requirement
  model = ModelSelector.select("task_type", quality_requirement="high")
  ```

### Implement Caching

- [ ] **Add cache_control to system prompts**
  ```python
  system = [
      PromptCache.add_cache_control(SYSTEM_INSTRUCTIONS, ttl="ephemeral")
  ]

  response = client.messages.create(
      model=model,
      max_tokens=500,
      system=system,  # Cached!
      messages=[...]
  )
  ```

### Implement Input Compression

- [ ] **Format complex inputs as JSON**
  ```python
  job_data = PromptCompressor.to_json({
      "title": job.title,
      "desc": job.description[:500],
      "budget": job.budget,
      "skills": job.skills
  }, indent=None)
  ```

- [ ] **Truncate long inputs**
  ```python
  description = PromptCompressor.truncate_description(
      job.full_description,
      max_chars=500
  )
  ```

### Implement Output Constraints

- [ ] **Specify output format and length**
  ```python
  prompt = f"""Generate proposal in JSON format: {{title, hook, solution, closing}}.

  Constraints:
  - Max 200 words total
  - No pleasantries, be direct
  - Focus on client's budget and timeline"""
  ```

### Implement Batching (if applicable)

- [ ] **Setup batch processor**
  ```python
  processor = BatchProcessor(client)

  # Collect items to batch
  items = [
      {"id": f"job-{i}", "content": f"Analyze: {job}"}
      for i, job in enumerate(jobs_to_process)
  ]

  # Submit batch (runs async, 50% discount)
  batch_id = processor.create_batch(
      items=items,
      model="claude-sonnet-4-5",
      system_prompt=SYSTEM_INSTRUCTIONS,
      batch_name="daily_proposals"
  )

  # Retrieve results later
  results = processor.retrieve_batch(batch_id)
  for result in results:
      job_id = result["custom_id"]
      response = result["result"]["message"]
      # Process...
  ```

---

## Phase 4: Quality Validation

### Baseline Establishment

- [ ] **Generate baseline with original model**
  ```python
  from execution.utils.cost_optimizer import QualityValidator

  # Use expensive model to establish baseline
  baseline_outputs = []
  for job in test_jobs:
      output = client.messages.create(
          model="claude-opus-4-5",  # Baseline model
          max_tokens=500,
          messages=[{"role": "user", "content": f"Analyze: {job}"}]
      )
      baseline_outputs.append(output.content[0].text)

  # Score baseline
  baseline_score = QualityValidator.baseline_quality_score(
      baseline_outputs,
      metric_fn=your_quality_scoring_function
  )
  print(f"Baseline quality: {baseline_score}")
  ```

- [ ] **Test optimized version**
  ```python
  # Run same test with optimized approach (Haiku, compressed, etc.)
  optimized_outputs = []
  for job in test_jobs:
      # Your optimized implementation
      output = generate_optimized(job)
      optimized_outputs.append(output)

  # Score optimized
  optimized_score = QualityValidator.baseline_quality_score(
      optimized_outputs,
      metric_fn=your_quality_scoring_function
  )
  print(f"Optimized quality: {optimized_score}")
  ```

- [ ] **Compare and decide**
  ```python
  comparison = QualityValidator.compare_quality(baseline_score, optimized_score)
  print(comparison["recommendation"])
  # Output: "PASS: Optimization acceptable" OR "FAIL: Quality degradation..."

  if comparison["passed"]:
      # Deploy optimization
      pass
  else:
      # Adjust (improve prompt, use higher model, etc.)
      pass
  ```

### Production Monitoring

- [ ] **Track quality metrics daily**
  ```python
  # Add to your daily reporting
  metrics = {
      "date": datetime.now(),
      "task": "proposal_generation",
      "acceptance_rate": calculate_acceptance_rate(),
      "avg_proposal_score": calculate_avg_score(),
      "model_used": "claude-sonnet-4-5",
      "cost_per_item": cost_tracker.get_avg_cost()
  }

  # Compare to baseline
  if metrics["acceptance_rate"] < baseline * 0.90:
      alert("Quality degradation detected!")
  ```

---

## Phase 5: Documentation

- [ ] **Update directive with results**
  ```markdown
  ## Actual Results

  ### Quality
  - Baseline: 28% acceptance rate (Opus)
  - Optimized: 26% acceptance rate (Sonnet)
  - Pct change: -7% (✅ Passes >90% threshold)

  ### Cost
  - Unoptimized: $45/month
  - Optimized: $2.50/month (includes 50% batch discount)
  - Savings: 94%

  ### Lessons Learned
  - Sonnet works just as well as Opus for proposals
  - Batching saves 50% with no quality impact
  - Caching system prompt saves $0.30 per 100k tokens
  ```

- [ ] **Document any new patterns discovered**
  - If you found a compression technique that works well
  - If a task category can use cheaper model than expected
  - If batching created unexpected issues

- [ ] **Add to cost_optimization.md if generalizable**
  - New task category discovered? Add to table
  - New compression technique? Add to input optimization
  - New quality threshold insight? Update layer 4

---

## Phase 6: Deployment & Monitoring

### Before Launch

- [ ] **Final cost estimate**
  ```
  Monthly calls: 150 (5 per day × 30)
  Cost per call: $0.017 (Sonnet + batch discount + caching)
  Monthly total: 150 × $0.017 = $2.55
  Target: Keep below $5/month
  ```

- [ ] **Rollout plan**
  ```
  - Day 1-3: 10% of traffic (15 calls/day)
  - Monitor quality metrics, cost tracking
  - Day 4-7: 50% of traffic
  - Day 8+: 100% full deployment
  ```

### During Operation

- [ ] **Daily checks** (5 min)
  - Any cost spikes?
  - Any quality degradation?
  - Any errors?

- [ ] **Weekly reviews** (15 min)
  ```
  # Run cost summary
  python -c "
  from execution.utils.cost_optimizer import CostTracker
  tracker = CostTracker()
  print(tracker.get_summary(days=7))
  "

  # Compare to target
  # Adjust if needed
  ```

- [ ] **Monthly analysis** (1 hour)
  - Full cost breakdown
  - Quality metrics vs baseline
  - Identify new optimization opportunities
  - Update directive with learnings

---

## Checklist Summary

**Before Code:**
- [ ] Understand workflow
- [ ] Define quality metrics
- [ ] Select models for each step
- [ ] Plan batching/caching
- [ ] Estimate costs
- [ ] Create directive

**During Code:**
- [ ] Import cost utilities
- [ ] Use ModelSelector (don't hardcode)
- [ ] Add caching where applicable
- [ ] Compress inputs
- [ ] Constrain outputs
- [ ] Implement batching (if applicable)
- [ ] Track all costs

**Before Launch:**
- [ ] Establish quality baseline
- [ ] Test optimization
- [ ] Compare to acceptance threshold
- [ ] Plan rollout strategy

**After Launch:**
- [ ] Monitor daily
- [ ] Review weekly
- [ ] Analyze monthly
- [ ] Update directive with learnings

---

## Example Automation: Complete Walkthrough

**Scenario:** Building daily LinkedIn post generator (5 posts/day)

### Phase 1: Planning
```
Workflow:
1. Get 5 topics from database (no API cost)
2. For each topic: Generate LinkedIn post (API call) → Sonnet
3. Post content to LinkedIn (no API cost)

Cost estimate:
- 5 posts × $0.30 (Opus) = $1.50/day = $45/month

Optimization strategy:
- Use Sonnet instead of Opus: $0.15 per post
- Batch all 5 posts: 50% off = $0.075 per post
- Cache system instructions: 90% off = $0.01 per post
- Target: $0.01 × 5 = $0.05/day = $1.50/month (96.7% savings)
```

### Phase 2: Directive
```markdown
# Daily LinkedIn Post Generator

## Workflow
1. Fetch topics (free)
2. Generate 5 posts (Claude API, batch)
3. Post to LinkedIn (external API)

## Cost Optimization
- Model: Sonnet (medium complexity)
- Batching: Yes, 5 posts per batch
- Caching: System instructions (5 min TTL)
- Compression: Output constraint (150-200 words)

## Quality Metrics
- Baseline: 8% engagement rate (with Opus)
- Target: >7.2% (maintain >90%)
- Measure: Likes + comments / impressions

## Cost
- Unoptimized: $45/month
- Optimized: $1.50/month (96% savings)
```

### Phase 3: Implementation
```python
from execution.utils.cost_optimizer import (
    ModelSelector, PromptCache, BatchProcessor, CostTracker
)

def generate_daily_posts():
    # Get topics
    topics = fetch_topics()

    # Setup batch
    processor = BatchProcessor(client)
    tracker = CostTracker()

    # Prepare batch requests
    requests = []
    for i, topic in enumerate(topics):
        requests.append({
            "custom_id": f"post-{i}",
            "params": {
                "model": ModelSelector.select("linkedin_post"),
                "max_tokens": 250,
                "system": [
                    PromptCache.add_cache_control(SYSTEM_INSTRUCTIONS)
                ],
                "messages": [{
                    "role": "user",
                    "content": f"Generate 150-200 word LinkedIn post about: {topic}"
                }]
            }
        })

    # Submit batch (runs async, <1 hour)
    batch_id = processor.create_batch(
        items=requests,
        model="claude-sonnet-4-5",
        batch_name="daily_linkedin"
    )

    # Later: retrieve results
    results = processor.retrieve_batch(batch_id)

    # Post to LinkedIn and log costs
    for result in results:
        post_content = result["result"]["message"]["content"][0]["text"]
        post_to_linkedin(post_content)

        # Log cost
        tracker.log_call(
            model="claude-sonnet-4-5",
            input_tokens=result["result"]["usage"]["input_tokens"],
            output_tokens=result["result"]["usage"]["output_tokens"],
            endpoint="linkedin_daily_post",
            cached_tokens=result["result"]["usage"].get("cache_read_input_tokens", 0)
        )
```

### Phase 4: Quality Validation
```python
# Baseline: 8% engagement (with Opus)
# Test optimized: Generate 20 posts with Sonnet
# Score: 7.6% engagement (95% of baseline) ✅ PASS

# Deploy optimization
```

### Phase 5: Results
```
Monthly cost: $1.50 (vs $45 without optimization)
Quality: 7.6% engagement (vs 8% baseline, -5%, but >90% threshold)
Deployment: Week 1 at 10%, week 2 at 50%, week 3+ at 100%
```

---

## Final Thoughts

**This checklist is your insurance policy.** Following it ensures:
- ✅ Costs are minimized from day one
- ✅ Quality is validated before production
- ✅ Learnings are captured for future automations
- ✅ Future instances of Claude Code benefit from your work

Use it. Improve it. Share learnings. Build better automations.
