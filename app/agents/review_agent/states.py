"""
Agent State Definitions for LangGraph
"""
from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime


class ReviewState(TypedDict):
    """State object for review agent workflow"""
    
    # Project context
    project_id: Optional[int]
    project_name: str
    project_domain: str
    project_context: Dict[str, Any]
    
    # Checklist data
    checklist_id: Optional[int]
    checklist_items: List[Dict[str, Any]]
    current_item_index: int
    
    # Review session
    review_id: Optional[int]
    responses: List[Dict[str, Any]]
    session_status: str  # draft, in_progress, completed, pending_approval
    
    # Voice interaction
    voice_enabled: bool
    last_transcript: Optional[str]
    last_voice_response: Optional[str]
    
    # Agent conversation
    conversation_history: List[Dict[str, str]]
    current_question: Optional[str]
    user_answer: Optional[str]
    
    # Report generation
    report_data: Optional[Dict[str, Any]]
    compliance_score: float
    overall_rag: str
    
    # Approval workflow
    requires_approval: bool
    approval_status: str  # pending, approved, rejected
    approver_id: Optional[int]
    approval_comments: Optional[str]
    
    # Errors and metadata
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]
