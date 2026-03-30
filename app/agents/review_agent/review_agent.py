"""
Review Agent Core
LangGraph-based agent for conducting project reviews
"""
from typing import Dict, List, Any, Optional, Annotated
from datetime import datetime
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from app.core.config import settings
from app.agents.review_agent.states import ReviewState
from app.services.report_generator import get_report_generator
from app.services.checklist_optimizer import get_checklist_optimizer


# System prompt for the review agent
REVIEW_AGENT_SYSTEM_PROMPT = """
You are an AI Tech & Delivery Review Agent, an expert in evaluating software projects.

Your role:
1. Conduct thorough project reviews using structured checklists
2. Ask clear, concise questions one at a time
3. Listen actively and probe deeper when answers are unclear
4. Assess responses objectively and assign appropriate RAG (Red/Amber/Green) status
5. Provide constructive feedback and recommendations
6. Always ensure human approval before finalizing reports

Communication style:
- Professional yet conversational
- Clear and direct
- Supportive, not judgmental
- Ask follow-up questions when needed

RAG Assessment Guidelines:
- GREEN: Fully compliant, evidence provided, no concerns
- AMBER: Partially compliant, minor gaps, improvement needed
- RED: Not compliant, significant gaps, immediate action required
- NA: Not applicable to this project

Remember: Your goal is to help teams improve, not to find fault.
"""


class ReviewAgent:
    """
    AI-powered review agent using LangGraph for workflow orchestration
    """
    
    def __init__(self):
        self.llm = None
        if settings.OPENAI_API_KEY:
            self.llm = ChatOpenAI(
                model="gpt-4o",
                temperature=0.3,
                api_key=settings.OPENAI_API_KEY
            )
        
        self.report_generator = get_report_generator()
        self.checklist_optimizer = get_checklist_optimizer()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        workflow = StateGraph(ReviewState)
        
        # Add nodes
        workflow.add_node("initialize", self.initialize_review)
        workflow.add_node("checklist_optimization", self.optimize_checklist)
        workflow.add_node("ask_question", self.ask_question)
        workflow.add_node("process_response", self.process_response)
        workflow.add_node("assess_rag", self.assess_rag_status)
        workflow.add_node("generate_report", self.generate_report)
        workflow.add_node("request_approval", self.request_approval)
        
        # Define edges
        workflow.set_entry_point("initialize")
        
        workflow.add_conditional_edges(
            "initialize",
            self._should_optimize_checklist,
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
            self._has_more_questions,
            {
                "continue": "ask_question",
                "generate": "generate_report"
            }
        )
        
        workflow.add_edge("generate_report", "request_approval")
        workflow.add_edge("request_approval", END)
        
        return workflow.compile()
    
    def initialize_review(self, state: ReviewState) -> ReviewState:
        """Initialize the review session"""
        state["session_status"] = "in_progress"
        state["current_item_index"] = 0
        state["responses"] = []
        state["conversation_history"] = []
        state["errors"] = []
        state["warnings"] = []
        state["metadata"]["started_at"] = datetime.utcnow().isoformat()
        
        # Add welcome message
        state["conversation_history"].append({
            "role": "assistant",
            "content": f"Hello! I'm your AI Review Agent. I'll be conducting the review for **{state['project_name']}**. "
                      f"Let's begin with the checklist. I'll ask you questions one by one."
        })
        
        return state
    
    def _should_optimize_checklist(self, state: ReviewState) -> str:
        """Decide whether to optimize checklist before review"""
        # If domain is specified and we have an LLM, optimize
        if state.get("project_domain") and self.llm:
            return "optimize"
        return "start_review"
    
    def optimize_checklist(self, state: ReviewState) -> ReviewState:
        """Generate AI recommendations for checklist enhancement"""
        # This would be async in production
        recommendations = self.checklist_optimizer.analyze_and_recommend(
            project_domain=state["project_domain"],
            current_checklist={"delivery": state["checklist_items"]},
            project_context=state.get("project_context")
        )
        
        state["metadata"]["checklist_recommendations"] = recommendations
        state["warnings"].append(
            f"Generated {len(recommendations)} checklist enhancement recommendations"
        )
        
        return state
    
    def ask_question(self, state: ReviewState) -> ReviewState:
        """Ask the next checklist question"""
        items = state["checklist_items"]
        idx = state["current_item_index"]
        
        if idx >= len(items):
            return state
        
        item = items[idx]
        question = item.get("question", "No question available")
        area = item.get("area", "General")
        
        state["current_question"] = question
        
        # Create conversational prompt
        prompt = f"**{area}**\n\n{question}\n\nPlease respond with Yes/No/Partial and any additional context."
        
        state["conversation_history"].append({
            "role": "assistant",
            "content": prompt
        })
        
        return state
    
    def process_response(self, state: ReviewState) -> ReviewState:
        """Process user's response to a question"""
        user_answer = state.get("user_answer", "")
        
        if not user_answer:
            state["errors"].append("No answer provided")
            return state
        
        # Use LLM to analyze response if available
        if self.llm and state["current_question"]:
            analysis = self._analyze_response_with_llm(
                question=state["current_question"],
                answer=user_answer
            )
            state["metadata"]["last_analysis"] = analysis
        
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
        state["user_answer"] = None  # Reset for next question
        
        return state
    
    def assess_rag_status(self, state: ReviewState) -> ReviewState:
        """Assess RAG status for the last response"""
        if not state["responses"]:
            return state
        
        last_response = state["responses"][-1]
        answer = last_response.get("answer", "").lower()
        
        # Simple rule-based RAG assignment
        # In production, use LLM for more nuanced assessment
        rag_status = "na"
        
        if any(word in answer for word in ["yes", "yeah", "yep", "correct", "done"]):
            rag_status = "green"
        elif any(word in answer for word in ["no", "nope", "not done", "missing"]):
            rag_status = "red"
        elif any(word in answer for word in ["partial", "partially", "in progress", "working on"]):
            rag_status = "amber"
        
        # Check for LLM analysis override
        if state["metadata"].get("last_analysis", {}).get("suggested_rag"):
            rag_status = state["metadata"]["last_analysis"]["suggested_rag"]
        
        last_response["rag_status"] = rag_status
        
        return state
    
    def _has_more_questions(self, state: ReviewState) -> str:
        """Check if there are more questions to ask"""
        if state["current_item_index"] < len(state["checklist_items"]):
            return "continue"
        return "generate"
    
    def generate_report(self, state: ReviewState) -> ReviewState:
        """Generate comprehensive review report"""
        state["session_status"] = "completed"
        state["metadata"]["completed_at"] = datetime.utcnow().isoformat()
        
        # Calculate compliance score
        responses = state["responses"]
        compliance_score = self.report_generator.calculate_compliance_score(
            responses=responses,
            checklist_items=state["checklist_items"]
        )
        
        state["compliance_score"] = compliance_score
        state["overall_rag"] = self.report_generator.determine_overall_rag(compliance_score)
        
        # Analyze gaps
        gaps = self.report_generator.analyze_gaps(responses)
        
        # Generate action items
        action_items = self.report_generator.generate_action_items(
            gaps=gaps,
            participants=state.get("project_context", {}).get("participants", [])
        )
        
        # Areas followed well (green items)
        areas_followed = [
            r.get("question") for r in responses
            if r.get("rag_status") == "green"
        ]
        
        # Build report data
        state["report_data"] = {
            "project_name": state["project_name"],
            "review_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "overall_rag_status": state["overall_rag"],
            "compliance_score": compliance_score,
            "participants": state.get("project_context", {}).get("participants", []),
            "areas_followed": areas_followed,
            "gaps_identified": gaps,
            "recommendations": self._generate_recommendations(gaps, state),
            "action_items": action_items,
            "detailed_findings": self._format_detailed_findings(responses)
        }
        
        # Generate files
        md_path = self.report_generator.generate_markdown_report(state["report_data"])
        state["metadata"]["markdown_report_path"] = md_path
        
        # PDF generation (optional)
        try:
            pdf_path = self.report_generator.generate_pdf_report(state["report_data"])
            state["metadata"]["pdf_report_path"] = pdf_path
        except Exception as e:
            state["warnings"].append(f"PDF generation failed: {e}")
        
        return state
    
    def request_approval(self, state: ReviewState) -> ReviewState:
        """Set up approval workflow"""
        if state.get("requires_approval", True):
            state["approval_status"] = "pending"
            state["session_status"] = "pending_approval"
        else:
            state["approval_status"] = "approved"
        
        state["metadata"]["approval_requested_at"] = datetime.utcnow().isoformat()
        
        return state
    
    def _analyze_response_with_llm(
        self,
        question: str,
        answer: str
    ) -> Dict[str, Any]:
        """Use LLM to analyze response quality and suggest RAG"""
        if not self.llm:
            return {}
        
        try:
            system_msg = SystemMessage(content="""
You are evaluating project review responses. Assess the answer quality and suggest RAG status.

RAG Guidelines:
- GREEN: Clear affirmative with evidence
- AMBER: Partial compliance or concerns mentioned
- RED: Negative response or significant gaps

Respond with JSON: {"assessment": "...", "suggested_rag": "green|amber|red|na"}
""")
            
            user_msg = HumanMessage(content=f"""
Question: {question}
Answer: {answer}

Provide your assessment.
""")
            
            response = self.llm.invoke([system_msg, user_msg])
            # Parse response (simplified - use proper JSON parsing in production)
            return {
                "assessment": response.content,
                "suggested_rag": "green"  # Default
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _generate_recommendations(
        self,
        gaps: List[Dict[str, Any]],
        state: ReviewState
    ) -> List[str]:
        """Generate recommendations based on gaps"""
        recommendations = []
        
        # Domain-specific recommendations
        domain = state.get("project_domain", "").lower()
        if domain in ["fintech", "healthcare", "ecommerce"]:
            recommendations.append(
                f"Enhance {domain}-specific compliance checks based on industry standards"
            )
        
        # Gap-based recommendations
        high_severity_gaps = [g for g in gaps if g.get("severity") == "high"]
        if high_severity_gaps:
            recommendations.append(
                f"Prioritize addressing {len(high_severity_gaps)} high-severity gaps immediately"
            )
        
        # General recommendations
        if state["compliance_score"] < 80:
            recommendations.append(
                "Schedule follow-up review in 30 days to track improvement"
            )
        
        return recommendations
    
    def _format_detailed_findings(
        self,
        responses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Format detailed findings for report"""
        findings = []
        
        # Group by area
        areas = {}
        for response in responses:
            area = response.get("area", "General")
            if area not in areas:
                areas[area] = []
            areas[area].append(response)
        
        for area, area_responses in areas.items():
            green_count = sum(1 for r in area_responses if r.get("rag_status") == "green")
            total = len(area_responses)
            
            findings.append({
                "area": area,
                "description": f"{green_count}/{total} items compliant ({green_count/total*100:.0f}%)",
                "details": area_responses
            })
        
        return findings
    
    def run_review(self, initial_state: ReviewState) -> ReviewState:
        """Run the complete review workflow"""
        return self.graph.invoke(initial_state)
    
    async def run_review_async(self, initial_state: ReviewState) -> ReviewState:
        """Run the complete review workflow asynchronously"""
        return await self.graph.ainvoke(initial_state)


# Global instance
_agent: Optional[ReviewAgent] = None


def get_review_agent() -> ReviewAgent:
    """Get or create review agent instance"""
    global _agent
    if _agent is None:
        _agent = ReviewAgent()
    return _agent
