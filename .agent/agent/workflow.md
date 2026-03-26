# Agent Workflow

## Overview

The Review Agent uses LangGraph to orchestrate a stateful, multi-step review workflow.

## State Machine

```
┌─────────────────────────────────────────────────────────────┐
│                    ReviewState                              │
├─────────────────────────────────────────────────────────────┤
│  project_id: Optional[int]                                  │
│  project_name: str                                          │
│  project_domain: str                                        │
│  checklist_items: List[Dict[str, Any]]                      │
│  current_item_index: int                                    │
│  responses: List[Dict[str, Any]]                            │
│  conversation_history: List[Dict[str, str]]                 │
│  current_question: Optional[str]                            │
│  user_answer: Optional[str]                                 │
│  report_data: Optional[Dict[str, Any]]                      │
│  compliance_score: float                                    │
│  overall_rag: str                                           │
│  approval_status: str                                       │
│  errors: List[str]                                          │
│  warnings: List[str]                                        │
└─────────────────────────────────────────────────────────────┘
```

## Workflow Graph

```python
from langgraph.graph import StateGraph, END

workflow = StateGraph(ReviewState)

# Add nodes
workflow.add_node("initialize", initialize_review)
workflow.add_node("checklist_optimization", optimize_checklist)
workflow.add_node("ask_question", ask_question)
workflow.add_node("process_response", process_response)
workflow.add_node("assess_rag", assess_rag_status)
workflow.add_node("generate_report", generate_report)
workflow.add_node("request_approval", request_approval)

# Define edges
workflow.set_entry_point("initialize")

workflow.add_conditional_edges(
    "initialize",
    should_optimize_checklist,
    {
        "optimize": "checklist_optimization",
        "start_review": "ask_question"
    }
)

workflow.add_edge("checklist_optimization", "ask_question")
workflow.add_edge("ask_question", "process_response")
workflow.add_edge("process_response", "assess_rag")

workflow.add_conditional_edges(
    "assess_rag",
    has_more_questions,
    {
        "continue": "ask_question",
        "generate": "generate_report"
    }
)

workflow.add_edge("generate_report", "request_approval")
workflow.add_edge("request_approval", END)

# Compile
graph = workflow.compile()
```

## Node Implementations

### 1. Initialize Review

```python
def initialize_review(state: ReviewState) -> ReviewState:
    """Initialize the review session"""
    state["session_status"] = "in_progress"
    state["current_item_index"] = 0
    state["responses"] = []
    state["conversation_history"] = []
    state["errors"] = []
    state["warnings"] = []
    
    # Welcome message
    state["conversation_history"].append({
        "role": "assistant",
        "content": f"Hello! I'm your AI Review Agent. "
                  f"Let's begin the review for {state['project_name']}."
    })
    
    return state
```

### 2. Checklist Optimization (Optional)

```python
def optimize_checklist(state: ReviewState) -> ReviewState:
    """Generate AI recommendations for checklist enhancement"""
    optimizer = get_checklist_optimizer()
    
    recommendations = optimizer.analyze_and_recommend(
        project_domain=state["project_domain"],
        current_checklist={"delivery": state["checklist_items"]},
        project_context=state.get("project_context")
    )
    
    state["metadata"]["checklist_recommendations"] = recommendations
    state["warnings"].append(
        f"Generated {len(recommendations)} recommendations"
    )
    
    return state
```

### 3. Ask Question

```python
def ask_question(state: ReviewState) -> ReviewState:
    """Ask the next checklist question"""
    items = state["checklist_items"]
    idx = state["current_item_index"]
    
    if idx >= len(items):
        return state
    
    item = items[idx]
    question = item.get("question")
    area = item.get("area", "General")
    
    state["current_question"] = question
    
    prompt = f"**{area}**\n\n{question}\n\n"
            f"Please respond with Yes/No/Partial and any additional context."
    
    state["conversation_history"].append({
        "role": "assistant",
        "content": prompt
    })
    
    return state
```

### 4. Process Response

```python
def process_response(state: ReviewState) -> ReviewState:
    """Process user's response to a question"""
    user_answer = state.get("user_answer", "")
    
    if not user_answer:
        state["errors"].append("No answer provided")
        return state
    
    # Store response
    current_item = state["checklist_items"][state["current_item_index"]]
    
    state["responses"].append({
        "checklist_item_id": current_item.get("id"),
        "question": current_item.get("question"),
        "area": current_item.get("area"),
        "answer": user_answer,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    # Move to next item
    state["current_item_index"] += 1
    state["user_answer"] = None
    
    return state
```

### 5. Assess RAG Status

```python
def assess_rag_status(state: ReviewState) -> ReviewState:
    """Assess RAG status for the last response"""
    if not state["responses"]:
        return state
    
    last_response = state["responses"][-1]
    answer = last_response.get("answer", "").lower()
    
    # Rule-based assessment
    if any(word in answer for word in ["yes", "yeah", "yep", "done"]):
        rag_status = "green"
    elif any(word in answer for word in ["no", "nope", "missing"]):
        rag_status = "red"
    elif any(word in answer for word in ["partial", "in progress", "working"]):
        rag_status = "amber"
    else:
        rag_status = "na"
    
    last_response["rag_status"] = rag_status
    return state
```

### 6. Generate Report

```python
def generate_report(state: ReviewState) -> ReviewState:
    """Generate comprehensive review report"""
    state["session_status"] = "completed"
    
    # Calculate compliance score
    generator = get_report_generator()
    
    compliance_score = generator.calculate_compliance_score(
        responses=state["responses"],
        checklist_items=state["checklist_items"]
    )
    
    state["compliance_score"] = compliance_score
    state["overall_rag"] = generator.determine_overall_rag(compliance_score)
    
    # Analyze gaps
    gaps = generator.analyze_gaps(state["responses"])
    
    # Generate action items
    action_items = generator.generate_action_items(
        gaps=gaps,
        participants=state.get("project_context", {}).get("participants", [])
    )
    
    # Build report data
    state["report_data"] = {
        "project_name": state["project_name"],
        "review_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "overall_rag_status": state["overall_rag"],
        "compliance_score": compliance_score,
        "areas_followed": [
            r["question"] for r in state["responses"]
            if r.get("rag_status") == "green"
        ],
        "gaps_identified": gaps,
        "recommendations": generate_recommendations(gaps, state),
        "action_items": action_items
    }
    
    # Generate files
    md_path = generator.generate_markdown_report(state["report_data"])
    state["metadata"]["markdown_report_path"] = md_path
    
    return state
```

### 7. Request Approval

```python
def request_approval(state: ReviewState) -> ReviewState:
    """Set up approval workflow"""
    if state.get("requires_approval", True):
        state["approval_status"] = "pending"
        state["session_status"] = "pending_approval"
    else:
        state["approval_status"] = "approved"
    
    return state
```

## Conditional Edges

### Should Optimize Checklist?

```python
def should_optimize_checklist(state: ReviewState) -> str:
    """Decide whether to optimize checklist before review"""
    if state.get("project_domain") and settings.OPENAI_API_KEY:
        return "optimize"
    return "start_review"
```

### Has More Questions?

```python
def has_more_questions(state: ReviewState) -> str:
    """Check if there are more questions to ask"""
    if state["current_item_index"] < len(state["checklist_items"]):
        return "continue"
    return "generate"
```

## Usage Example

```python
from app.agents.review_agent import get_review_agent

# Get agent instance
agent = get_review_agent()

# Initialize state
initial_state = {
    "project_id": 1,
    "project_name": "NeuMoney Platform",
    "project_domain": "fintech",
    "checklist_items": [...],
    "review_id": 1,
    "responses": [],
    "current_item_index": 0,
    "requires_approval": True,
    "approval_status": "pending"
}

# Run workflow
final_state = agent.run_review(initial_state)

# Access results
print(f"Compliance Score: {final_state['compliance_score']}")
print(f"Overall RAG: {final_state['overall_rag']}")
print(f"Report: {final_state['report_data']}")
```

## State Transitions Example

```
Initial State:
{
  "current_item_index": 0,
  "responses": [],
  "session_status": "draft"
}

↓ After Initialize

{
  "current_item_index": 0,
  "responses": [],
  "session_status": "in_progress",
  "conversation_history": [
    {"role": "assistant", "content": "Hello! I'm your AI Review Agent..."}
  ]
}

↓ After Ask Question (item 0)

{
  "current_item_index": 0,
  "current_question": "Are scope baselines defined?",
  "conversation_history": [
    {"role": "assistant", "content": "Are scope baselines defined?"}
  ]
}

↓ After Process Response

{
  "current_item_index": 1,
  "responses": [
    {
      "question": "Are scope baselines defined?",
      "answer": "Yes, all signed off",
      "rag_status": null
    }
  ]
}

↓ After Assess RAG

{
  "current_item_index": 1,
  "responses": [
    {
      "question": "Are scope baselines defined?",
      "answer": "Yes, all signed off",
      "rag_status": "green"
    }
  ]
}

↓ Loop (More Questions)

... continues for all items ...

↓ After Generate Report

{
  "compliance_score": 72.5,
  "overall_rag": "amber",
  "report_data": {...},
  "session_status": "completed"
}

↓ After Request Approval

{
  "approval_status": "pending",
  "session_status": "pending_approval"
}

↓ END
```

---

*Last Updated: 2026-03-25*
