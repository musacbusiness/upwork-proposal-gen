# Topic Learning System - Quick Start

## What Was Built

A **self-learning feedback loop** that automatically optimizes topic selection based on your approval/denial patterns.

---

## The Three Files

### 1. `execution/topic_performance_analyzer.py`
Core system that:
- Tracks approval rates per topic (% of posts you approved)
- Calculates weighted selection probabilities
- Auto-deprecates topics with 100% rejection (3+ denials)
- Stores data in `.tmp/topic_performance.json`

**Key Class:** `TopicPerformanceAnalyzer`

### 2. `execution/post_generation_with_topic_learning.py`
Integration layer that:
- Selects topics using weighted randomization
- Records approvals/denials in Airtable
- Syncs performance to dashboards
- Suggests topics for next post generation

**Key Function:** `suggest_next_topic_for_generation()`

### 3. `TOPIC_LEARNING_SYSTEM.md`
Documentation explaining:
- How the system learns from your decisions
- How weighted selection works (formula)
- How to use it in your workflow
- Performance metrics and thresholds

---

## Quick Example

### Scenario: You reject 3 posts from "Dynamic Pricing"

```
POST 1: "Dynamic Pricing Automation" → You: ❌ DENIED
         Topic: 0 approved, 1 denied → Approval Rate: 0%

POST 2: "Dynamic Pricing Automation" → You: ❌ DENIED
         Topic: 0 approved, 2 denied → Approval Rate: 0%

POST 3: "Dynamic Pricing Automation" → You: ❌ DENIED
         Topic: 0 approved, 3 denied → Approval Rate: 0%
         🔴 TOPIC DEPRECATED - Removed from future suggestions
```

**Result:** "Dynamic Pricing Automation" never appears in suggestions again.

### Scenario: You approve 3 from "Prompt Engineering", 1 from "AI Market Research"

```
Topics Table:
┌─────────────────────────────────┬───────────┬──────────┬──────┐
│ Topic                           │ Approval  │ Posts    │ Bias │
├─────────────────────────────────┼───────────┼──────────┼──────┤
│ Prompt Engineering              │ 100%      │ 3/3 ✅   │ 1.0  │
│ AI-Powered Market Research      │ 100%      │ 1/1 ✅   │ 1.0  │
│ All other topics                │ 100%      │ 0/0      │ 1.0  │
└─────────────────────────────────┴───────────┴──────────┴──────┘

Next 10 random selections will heavily favor:
"Prompt Engineering" and "AI-Powered Market Research"
```

---

## How to Use

### Step 1: When Creating a Post
```python
from execution.post_generation_with_topic_learning import suggest_next_topic_for_generation

topic = suggest_next_topic_for_generation()
# Output: "🎯 Suggested Topic: Prompt Engineering Fundamentals"
```

Add this topic to the Airtable post record in the "Topic" field.

### Step 2: When Approving/Denying
In Airtable, update the post Status:
- **"Approved"** = You liked this post ✅
- **"Rejected"** = You didn't like this post ❌

The system auto-learns from your decision.

### Step 3: Check Performance
```python
from execution.post_generation_with_topic_learning import LinkedInPostGenerator

generator = LinkedInPostGenerator()
generator.initialize_topics()
generator.get_performance_dashboard()
```

---

## The Math

### Weighted Selection Formula

```
Weight = (Approval Rate)²
```

**Examples:**
| Approval Rate | Weight | Selection Probability* |
|--------------|--------|----------------------|
| 100% | 1.00 | 25% (if 4 topics at 100%) |
| 80% | 0.64 | 16% |
| 60% | 0.36 | 9% |
| 40% | 0.16 | 4% |
| 20% | 0.04 | 1% |
| 0% | 0.00 | 0% |

*Assuming equal number of topics at each rate

### Why Squared?
It **amplifies** the difference:
- 80% vs 50% approval → 60% more likely to select 80%
- 100% vs 50% approval → 300% more likely to select 100%

Small differences in quality lead to big differences in selection.

---

## Data Storage

Performance data lives in: **`.tmp/topic_performance.json`**

```json
{
  "topics": {
    "Prompt Engineering Fundamentals": {
      "total_posts": 3,
      "approved_posts": 3,
      "denied_posts": 0,
      "approval_rate": 1.0,
      "deprecated": false
    },
    "Dynamic Pricing Automation": {
      "total_posts": 3,
      "approved_posts": 0,
      "denied_posts": 3,
      "approval_rate": 0.0,
      "deprecated": true
    }
  },
  "deprecated_topics": ["Dynamic Pricing Automation"],
  "total_posts_analyzed": 14
}
```

---

## Deprecation Rules

A topic is **automatically deprecated** when:
- ✓ 3+ posts have been generated from that topic
- ✓ 0 of them were approved
- ✓ All 3+ were denied

**Once deprecated:**
- Topic never appears in suggestions
- Topic removed from active pool
- System notification: "🔴 TOPIC DEPRECATED"

---

## Performance Thresholds

| Rate | Status | Selection |
|------|--------|-----------|
| 90-100% | ⭐ Excellent | Heavy bias toward selection |
| 70-90% | ✅ Good | Moderate bias |
| 50-70% | 🟡 Fair | Slight bias |
| 25-50% | ⚠️ Weak | Low selection |
| 0-25% | 🔴 Poor | Rarely selected |
| 0% (3+ posts) | 🔴 DEPRECATED | Never selected |

---

## Integration Points

### Modal Cloud Function
When scheduler generates posts, call:
```python
topic = suggest_next_topic_for_generation()
```

### Airtable Field
Add to LinkedIn Posts table:
- **Field Name:** "Topic"
- **Field Type:** Single Select (or Text)
- **Value:** Topic name from the 73-topic list

### Status Updates
When user changes Status to "Approved" or "Rejected":
- System reads Topic field
- Records result in analyzer
- Updates topic performance
- May trigger deprecation

---

## Testing the System

```bash
cd "/Users/musacomma/Agentic Workflow"
python3 execution/topic_performance_analyzer.py
```

Output shows:
- All topics initialized
- Test results recorded
- Performance report with approval rates
- Deprecated topics highlighted
- Weighted selection test (10 random picks)

---

## Next Steps

1. **Start using** the Topic field in Airtable posts
2. **Set Status** to "Approved" or "Rejected" for posts you review
3. **Run dashboard** every 10-15 posts to see which topics are winning
4. **Let the system learn** - over time, selection will bias toward your preferred topics

The beauty of this system: **You don't do anything special. Just approve/deny posts normally, and the system learns.**
