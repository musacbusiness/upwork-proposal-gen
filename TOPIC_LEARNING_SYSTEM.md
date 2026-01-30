# Topic Learning System: Self-Annealing LinkedIn Post Generation

## Overview

Your LinkedIn post automation now includes a **self-learning feedback loop** that automatically adapts to your preferences. The system tracks which topics resonate with you and biases post generation accordingly.

---

## How It Works

### 1. **Intelligent Topic Selection**
- Posts are generated from **randomly selected topics** from your 73 approved topics
- Initially, all topics have equal weight (100% baseline approval rate)
- As you approve/deny posts, the system learns

### 2. **Approval Rate Tracking**
The system tracks for each topic:
- **Total posts generated** from that topic
- **Approved posts** - posts you liked from that topic
- **Denied posts** - posts you rejected from that topic
- **Approval rate** = Approved / Total

**Example:**
- "Dynamic Pricing Automation": 3 posts generated, 0 approved, 3 denied → 0% approval rate → DEPRECATED ✓
- "Personalized Outreach at Scale": 3 posts generated, 2 approved, 1 denied → 66.7% approval rate ✓
- "Prompt Engineering Fundamentals": 4 posts generated, 4 approved, 0 denied → 100% approval rate ✓

### 3. **Weighted Randomization**
The system uses **weighted random selection** to pick the next topic:

```
Weight for each topic = (Approval Rate)²
```

This formula amplifies the difference:
- 100% approval = weight of 1.0 (100% chance if all others are 0%)
- 80% approval = weight of 0.64
- 50% approval = weight of 0.25
- 0% approval = weight of 0.0 (never selected if any other options exist)

**Why squared?** It amplifies the bias. A topic with 80% approval gets 36% higher priority than 50% approval. Small differences in approval rates lead to significant differences in selection probability.

### 4. **Automatic Topic Deprecation**
When a topic reaches **100% rejection rate** (3+ denied posts, 0 approved):
- Topic is automatically marked as DEPRECATED
- No future posts will be generated from that topic
- The topic is removed from the selection pool
- You're notified via the performance dashboard

---

## The Loop in Action

### Example Scenario

**Starting State:**
- All 73 topics initialized with 100% baseline approval
- Posts generated via pure randomization

**Your Approvals/Denials:**

| Post # | Topic | Your Decision | Action |
|--------|-------|---------------|--------|
| 1 | Prompt Engineering | ✅ Approved | Topic: 1 approved, 0 denied |
| 2 | Dynamic Pricing | ❌ Denied | Topic: 0 approved, 1 denied |
| 3 | Prompt Engineering | ✅ Approved | Topic: 2 approved, 0 denied |
| 4 | Dynamic Pricing | ❌ Denied | Topic: 0 approved, 2 denied |
| 5 | Personalized Outreach | ✅ Approved | Topic: 1 approved, 0 denied |
| 6 | Dynamic Pricing | ❌ Denied | Topic: 0 approved, 3 denied → **DEPRECATED** |

**System Response After Post #6:**
- "Prompt Engineering": 100% approval rate (2/2) → Weight = 1.0
- "Personalized Outreach": 100% approval rate (1/1) → Weight = 1.0
- "Dynamic Pricing": 0% approval rate (0/3) → Weight = 0.0 → **Removed from pool**
- Next post suggestions heavily favor "Prompt Engineering" and "Personalized Outreach"
- 71 active topics remain in pool

**System Response After Posts #7-10:**
If you continue approving from "Prompt Engineering" but only half from "Personalized Outreach":
- "Prompt Engineering": 90% approval → Weight = 0.81
- "Personalized Outreach": 60% approval → Weight = 0.36
- Selection ratio: 69% chance for Prompt Engineering, 31% chance for Personalized Outreach

---

## How to Use This System

### Step 1: Generate Posts (Normal Workflow)
When generating new LinkedIn posts:
```python
from execution.post_generation_with_topic_learning import suggest_next_topic_for_generation

# Get next topic suggestion
topic = suggest_next_topic_for_generation()
# Output: "🎯 Suggested Topic: Prompt Engineering Fundamentals"
# Output: "   Approval Rate: 100.0%"
```

The system will suggest high-performing topics more often.

### Step 2: Add Topic to Post in Airtable
When you create a post, the "Topic" field should be set to the suggested topic:

| Field | Value |
|-------|-------|
| Title | "3 Secrets of Effective Prompting..." |
| Post Content | Full post text |
| **Topic** | "Prompt Engineering Fundamentals" |
| Status | Draft |
| Scheduled Time | (scheduled date/time) |

### Step 3: Approve or Deny Posts
When reviewing/editing posts in Airtable, change the Status field:

- **✅ Approve**: Set Status = "Approved" (you like this post)
- **❌ Deny**: Set Status = "Rejected" (you don't like this post)

The system automatically tracks this decision and updates the topic's approval rate.

### Step 4: Monitor Performance
Check your topic performance dashboard:

```python
from execution.post_generation_with_topic_learning import LinkedInPostGenerator

generator = LinkedInPostGenerator()
generator.initialize_topics()
generator.get_performance_dashboard()
```

This shows:
- Total posts analyzed
- Active vs deprecated topics
- Approval rates for each topic
- Visual bars showing performance

**Example Output:**
```
📊 TOPIC PERFORMANCE ANALYSIS

Total Posts Analyzed: 25
Active Topics: 72/73
Deprecated Topics: 1

Topic                                          Approval Rate    Posts
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Prompt Engineering Fundamentals                 100.0% ████████████████████  4
Personalized Outreach at Scale                   66.7% █████████████░░░░░░░  3
AI-Powered Meeting Summarization                 50.0% ██████████░░░░░░░░░░  4
Dynamic Pricing Automation                        0.0% ░░░░░░░░░░░░░░░░░░░░  3 🔴 DEPRECATED
```

---

## The Self-Annealing Benefit

### Why This Works

1. **Removes Bias Manually**: You don't have to tell the system "stop suggesting topics I don't like." It learns automatically.

2. **Finds Your Sweet Spot**: Over time, the system identifies which topics resonate with your audience and your style.

3. **Speeds Up Iteration**: Instead of generating 10 posts and rejecting 7, the system learns to suggest topics with higher approval rates first.

4. **Creates Accountability**: The performance dashboard shows exactly which topics work for you.

### Expected Outcomes

**Early Phase (Posts 1-20):**
- Most topics still have equal weight
- Mixed approval rates
- System learning what works

**Mid Phase (Posts 20-50):**
- Clear winners emerge (80%+ approval topics)
- Losers deprecate (0% approval)
- Selection heavily biased toward winners

**Mature Phase (Posts 50+):**
- Top 10-20 topics handle majority of generation
- Consistently high approval rates
- Efficient, optimized content pipeline

---

## Integration with Your Workflow

### In Modal Cloud Functions
When the scheduler generates new posts:

```python
from execution.post_generation_with_topic_learning import suggest_next_topic_for_generation

# Before generating a post
topic = suggest_next_topic_for_generation()

# Generate post content for this topic
post_content = generate_post_about_topic(topic)

# Add to Airtable with topic field
create_airtable_post(
    title=post_content['title'],
    content=post_content['content'],
    topic=topic,  # ← Store the topic used
    status="Draft"
)
```

### Tracking Approvals
When you update a post status in Airtable:

```python
from execution.post_generation_with_topic_learning import AirtableApprovalTracker

tracker = AirtableApprovalTracker()

# This scans Airtable for status changes and updates topic performance
results = tracker.process_post_status_changes()

print(f"Approved: {results['approved']}")
print(f"Denied: {results['denied']}")

if results['deprecated']:
    print("🔴 Deprecated topics:")
    for notice in results['deprecated']:
        print(f"  - {notice['topic']}")
```

---

## Performance Data Storage

The system stores topic performance in **`.tmp/topic_performance.json`**:

```json
{
  "topics": {
    "Prompt Engineering Fundamentals": {
      "total_posts": 4,
      "approved_posts": 4,
      "denied_posts": 0,
      "approval_rate": 1.0,
      "deprecated": false,
      "created_at": "2026-01-04T..."
    },
    "Dynamic Pricing Automation": {
      "total_posts": 3,
      "approved_posts": 0,
      "denied_posts": 3,
      "approval_rate": 0.0,
      "deprecated": true,
      "created_at": "2026-01-04T..."
    }
  },
  "deprecated_topics": ["Dynamic Pricing Automation"],
  "total_posts_analyzed": 25,
  "last_updated": "2026-01-04T..."
}
```

---

## Key Statistics & Thresholds

| Metric | Threshold | Action |
|--------|-----------|--------|
| **Approval Rate** | 75%+ | High performer (weight amplified) |
| | 50-75% | Medium performer |
| | 25-50% | Low performer |
| | 0-25% | Very low performer |
| **Deprecation** | 0% with 3+ posts | Topic deprecated |
| **Weight Formula** | rate² | Amplifies bias |
| **Selection** | Weighted random | Favors high performers |

---

## FAQ

### Q: Can I manually control which topics to use?
**A:** Yes. You can directly set the "Topic" field in Airtable and it will override the suggestion. The system learns from your choice.

### Q: What if I don't want a topic deprecated?
**A:** Don't reject 3+ posts from that topic. If you accidentally deprecated a topic, you can manually edit `.tmp/topic_performance.json` to set `"deprecated": false`.

### Q: How often should I check performance?
**A:** Ideally after every 10-15 posts. The system is most effective with regular feedback.

### Q: Can deprecated topics come back?
**A:** Currently, no. Once deprecated, a topic is removed permanently. This prevents wasting generation budget on consistently rejected topics.

### Q: Does the system start over if I delete my data?
**A:** Yes. If you delete `.tmp/topic_performance.json`, the system reinitializes with all topics at 100% baseline approval. The learning starts over.

### Q: How do I see which topics are performing best?
**A:** Call `generator.get_performance_dashboard()` in Python or check the formatted report in the console output.

---

## Summary

The Topic Learning System is a **self-annealing feedback loop** that:

1. ✅ Tracks approval rates per topic
2. ✅ Uses weighted randomization based on approval rates
3. ✅ Amplifies the bias (high performers get much more selection)
4. ✅ Automatically deprecates consistently rejected topics
5. ✅ Creates efficiency over time (fewer rejects, more approvals)

**Result**: Your LinkedIn post generation becomes increasingly optimized for your preferences and audience preferences, automatically learning what works best.
