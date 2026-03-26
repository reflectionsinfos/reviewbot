# RAG Assessment Logic

## Overview

RAG (Red/Amber/Green) status is used to assess compliance for each checklist item and overall project health.

## RAG Status Values

| Status | Color | Score | Meaning |
|--------|-------|-------|---------|
| `green` | 🟢 | 100 | Fully compliant |
| `amber` | 🟡 | 50 | Partially compliant |
| `red` | 🔴 | 0 | Not compliant |
| `na` | ⚪ | - | Not applicable (excluded) |

---

## Assessment Methods

### Method 1: Rule-Based (Default)

Simple keyword matching for quick assessment.

```python
def assess_rag_status(answer: str) -> str:
    """Assess RAG status based on answer keywords"""
    answer_lower = answer.lower()
    
    # Green indicators
    if any(word in answer_lower for word in [
        "yes", "yeah", "yep", "done", "completed", "correct", 
        "all", "fully", "entirely"
    ]):
        return "green"
    
    # Red indicators
    if any(word in answer_lower for word in [
        "no", "nope", "not done", "missing", "lacking", 
        "don't have", "doesn't have", "failed"
    ]):
        return "red"
    
    # Amber indicators
    if any(word in answer_lower for word in [
        "partial", "partially", "in progress", "working on",
        "mostly", "almost", "nearly", "planned", "upcoming"
    ]):
        return "amber"
    
    # Default to NA for unclear answers
    return "na"
```

**Examples:**

| Answer | RAG Status | Reason |
|--------|------------|--------|
| "Yes, all baselines are signed off" | 🟢 Green | Contains "yes", "all" |
| "No, this is not done yet" | 🔴 Red | Contains "no", "not done" |
| "Partially complete, working on it" | 🟡 Amber | Contains "partially", "working on" |
| "We have started but need more time" | 🟡 Amber | Implies partial progress |
| "This doesn't apply to our project" | ⚪ NA | Not applicable |

---

### Method 2: LLM-Enhanced (Optional)

Use LLM for nuanced assessment with context.

```python
async def assess_rag_with_llm(question: str, answer: str, context: str = "") -> str:
    """Use LLM for nuanced RAG assessment"""
    
    system_prompt = """
You are evaluating project review responses. Assess the answer quality and suggest RAG status.

RAG Guidelines:
- GREEN: Clear affirmative with evidence, fully compliant
- AMBER: Partial compliance, concerns mentioned, in progress
- RED: Negative response, significant gaps, not compliant
- NA: Not applicable or insufficient information

Respond with JSON: {"rag": "green|amber|red|na", "reasoning": "..."}
"""
    
    user_prompt = f"""
Question: {question}
Answer: {answer}
Context: {context}

Provide your RAG assessment with reasoning.
"""
    
    response = await llm.ainvoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ])
    
    # Parse response
    assessment = json.loads(response.content)
    return assessment["rag"]
```

**When to Use LLM:**
- Complex answers with multiple aspects
- Answers with qualifiers or conditions
- Need for detailed reasoning
- Edge cases not covered by rules

---

## Compliance Score Calculation

### Formula

```
Compliance Score = (Σ (RAG Score × Weight)) / (Σ Weights for non-NA items)
```

### Implementation

```python
def calculate_compliance_score(
    responses: List[Dict[str, Any]],
    checklist_items: List[Dict[str, Any]]
) -> float:
    """Calculate overall compliance score"""
    
    rag_scores = {
        'green': 100,
        'amber': 50,
        'red': 0,
        'na': None  # Exclude from calculation
    }
    
    total_weight = 0
    weighted_score = 0
    
    for response in responses:
        rag = response.get('rag_status', 'na').lower()
        weight = response.get('weight', 1.0)
        
        score = rag_scores.get(rag)
        
        # Skip NA items
        if score is None:
            continue
        
        weighted_score += score * weight
        total_weight += weight
    
    if total_weight == 0:
        return 0.0
    
    return weighted_score / total_weight
```

### Examples

**Example 1: All Green**
```
Responses: [green(100), green(100), green(100)]
Score = (100 + 100 + 100) / 3 = 100%
```

**Example 2: Mixed**
```
Responses: [green(100), amber(50), red(0), green(100)]
Score = (100 + 50 + 0 + 100) / 4 = 62.5%
```

**Example 3: With NA**
```
Responses: [green(100), na(exclude), amber(50), red(0)]
Score = (100 + 50 + 0) / 3 = 50%
```

**Example 4: Weighted**
```
Responses: [
  {rag: green, weight: 2.0},  # High priority
  {rag: red, weight: 1.0},
  {rag: amber, weight: 1.0}
]
Score = (100×2 + 0×1 + 50×1) / (2+1+1) = 250/4 = 62.5%
```

---

## Overall RAG Determination

### Thresholds

```python
def determine_overall_rag(compliance_score: float) -> str:
    """Determine overall RAG status based on compliance score"""
    
    if compliance_score >= 80:
        return 'green'
    elif compliance_score >= 50:
        return 'amber'
    else:
        return 'red'
```

### Threshold Rationale

| Score Range | RAG | Rationale |
|-------------|-----|-----------|
| 80-100% | 🟢 Green | Strong compliance, minor improvements needed |
| 50-79% | 🟡 Amber | Moderate compliance, significant improvements needed |
| 0-49% | 🔴 Red | Poor compliance, immediate action required |

### Customization

Thresholds can be adjusted per organization:

```python
# Stricter thresholds
STRICT_THRESHOLDS = {
    'green': 90,
    'amber': 60
}

# More lenient thresholds
LENIENT_THRESHOLDS = {
    'green': 70,
    'amber': 40
}
```

---

## Gap Analysis

### Identifying Gaps

```python
def analyze_gaps(responses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Identify gaps from responses"""
    gaps = []
    
    for response in responses:
        rag = response.get('rag_status', 'na').lower()
        
        # Only red and amber are gaps
        if rag in ['red', 'amber']:
            gap = {
                'title': response.get('question', 'Unknown'),
                'description': response.get('comments', ''),
                'rag_status': rag,
                'area': response.get('area', 'General'),
                'severity': 'high' if rag == 'red' else 'medium'
            }
            gaps.append(gap)
    
    return gaps
```

### Severity Assignment

| RAG Status | Severity | Action Timeline |
|------------|----------|-----------------|
| Red | High | Immediate (within 1 week) |
| Amber | Medium | Short-term (within 1 month) |

---

## Action Item Generation

### From Gaps

```python
def generate_action_items(
    gaps: List[Dict[str, Any]],
    participants: List[str]
) -> List[Dict[str, Any]]:
    """Generate action items from gaps"""
    action_items = []
    
    for idx, gap in enumerate(gaps, 1):
        action_item = {
            'item': f"Address: {gap['title']}",
            'owner': 'TBD',  # Assign during review
            'due_date': 'TBD',
            'priority': gap.get('severity', 'medium').capitalize(),
            'related_gap': gap['title'],
            'status': 'open'
        }
        action_items.append(action_item)
    
    return action_items
```

### Priority Mapping

| Gap Severity | Action Priority | Example Due Date |
|--------------|-----------------|------------------|
| High | High | 1 week |
| Medium | Medium | 2-4 weeks |
| Low | Low | 1-3 months |

---

## Trend Analysis

### Tracking Over Time

```python
def calculate_trend(
    scores: List[Tuple[datetime, float]]
) -> Dict[str, Any]:
    """Calculate compliance trend over time"""
    
    if len(scores) < 2:
        return {"trend": "stable", "change": 0}
    
    # Sort by date
    scores.sort(key=lambda x: x[0])
    
    # Calculate change
    oldest = scores[0][1]
    latest = scores[-1][1]
    change = latest - oldest
    
    # Determine trend
    if change > 5:
        trend = "improving"
    elif change < -5:
        trend = "declining"
    else:
        trend = "stable"
    
    return {
        "trend": trend,
        "change": round(change, 2),
        "oldest_score": oldest,
        "latest_score": latest
    }
```

### Example Trends

```
Project: NeuMoney Platform

Review History:
- 2026-Q1: 62.5% (Amber)
- 2026-Q2: 72.5% (Amber) ↑ +10%
- 2026-Q3: 85.0% (Green) ↑ +12.5%

Trend: Improving (+22.5% over 2 quarters)
```

---

## Edge Cases

### Case 1: All NA Responses

```python
responses = [
    {"rag_status": "na"},
    {"rag_status": "na"},
    {"rag_status": "na"}
]

# Result: 0% (no compliant items)
# Recommendation: Review checklist relevance
```

### Case 2: Empty Responses

```python
responses = []

# Result: 0% (no data)
# Recommendation: Complete review first
```

### Case 3: Single Response

```python
responses = [{"rag_status": "green", "weight": 1.0}]

# Result: 100% (but low confidence)
# Recommendation: Complete more items
```

### Case 4: Conflicting Evidence

```python
answer = "Yes, but we have some concerns about scalability"

# Rule-based: Green (contains "yes")
# LLM-enhanced: Amber (qualifier detected)
# Recommendation: Use LLM for nuanced cases
```

---

## Best Practices

1. **Combine Methods:** Use rule-based for speed, LLM for edge cases
2. **Human Review:** Allow manual RAG override with comments
3. **Trend Tracking:** Monitor scores over time, not just point-in-time
4. **Weighted Scoring:** Assign higher weights to critical items
5. **Context Matters:** Consider project domain and maturity
6. **Actionable Gaps:** Ensure every red/amber has associated action item

---

*Last Updated: 2026-03-25*
