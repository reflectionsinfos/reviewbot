"""
Database Models
"""
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class RAGStatus(str, enum.Enum):
    """Red Amber Green status"""
    RED = "red"
    AMBER = "amber"
    GREEN = "green"
    NA = "na"


class ReviewStatus(str, enum.Enum):
    """Review session status"""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"


class ApprovalStatus(str, enum.Enum):
    """Report approval status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"


class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="reviewer")  # reviewer, manager, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    projects = relationship("Project", back_populates="owner")
    reviews_conducted = relationship("Review", foreign_keys="Review.conducted_by", back_populates="conductor")
    approvals = relationship("ReportApproval", back_populates="approver")


class Project(Base):
    """Project model storing project information"""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    domain = Column(String)  # fintech, healthcare, e-commerce, etc.
    description = Column(Text)
    tech_stack = Column(JSON)  # List of technologies
    stakeholders = Column(JSON)  # Dict with roles and names
    
    # Project metadata
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    status = Column(String, default="active")  # active, completed, on_hold
    
    # Ownership
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="projects")
    
    # Relationships
    checklists = relationship("Checklist", back_populates="project", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="project", cascade="all, delete-orphan")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Checklist(Base):
    """Checklist template for reviews"""
    __tablename__ = "checklists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # e.g., "Delivery Check List V 1.0"
    type = Column(String, nullable=False)  # "delivery" or "technical"
    version = Column(String, default="1.0")

    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    project = relationship("Project", back_populates="checklists")

    # Is this a global template or project-specific
    is_global = Column(Boolean, default=True)

    # Optional reference to original template if cloned
    source_checklist_id = Column(Integer, ForeignKey("checklists.id", ondelete="SET NULL"), nullable=True)

    # Area code mapping: {"Security": "SEC", "Technical Architecture": "TECH"}
    area_codes = Column(JSON, nullable=True)

    items = relationship("ChecklistItem", back_populates="checklist", cascade="all, delete-orphan")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChecklistItem(Base):
    """Individual checklist items/questions"""
    __tablename__ = "checklist_items"
    
    id = Column(Integer, primary_key=True, index=True)
    checklist_id = Column(Integer, ForeignKey("checklists.id"), nullable=False)
    checklist = relationship("Checklist", back_populates="items")
    
    # Item details
    item_code = Column(String)  # e.g., "1.1", "1.10"
    area = Column(String)  # e.g., "Scope, Planning & Governance"
    question = Column(Text, nullable=False)
    category = Column(String)  # For grouping related questions
    
    # Metadata
    weight = Column(Float, default=1.0)  # For scoring
    is_review_mandatory = Column("is_required", Boolean, default=True)  # Blocks completion until reviewed
    expected_evidence = Column(Text)  # What evidence to look for
    
    # Domain-specific suggestions
    suggested_for_domains = Column(JSON)  # List of domains where this is critical
    
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class Review(Base):
    """Review session"""
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    project = relationship("Project", back_populates="reviews")
    
    checklist_id = Column(Integer, ForeignKey("checklists.id"), nullable=False)
    checklist = relationship("Checklist")
    
    # Session info
    title = Column(String)
    conducted_by = Column(Integer, ForeignKey("users.id"))
    conductor = relationship("User", foreign_keys=[conducted_by], back_populates="reviews_conducted")
    
    participants = Column(JSON)  # List of participant names/emails
    review_date = Column(DateTime, default=datetime.utcnow)
    
    # Status
    status = Column(String, default=ReviewStatus.DRAFT.value)
    voice_enabled = Column(Boolean, default=True)
    
    # Relationships
    responses = relationship("ReviewResponse", back_populates="review", cascade="all, delete-orphan")
    report = relationship("Report", back_populates="review", uselist=False, cascade="all, delete-orphan")
    
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)


class ReviewResponse(Base):
    """Individual response to a checklist item"""
    __tablename__ = "review_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False)
    review = relationship("Review", back_populates="responses")
    
    checklist_item_id = Column(Integer, ForeignKey("checklist_items.id"), nullable=False)
    checklist_item = relationship("ChecklistItem")
    
    # Response data
    answer = Column(String)  # Yes/No/Partial or free text
    comments = Column(Text)
    rag_status = Column(String, default=RAGStatus.NA.value)
    
    # Evidence
    evidence_links = Column(JSON)  # List of URLs or file paths
    attachments = Column(JSON)  # List of file metadata
    
    # Voice interaction
    voice_recording_path = Column(String, nullable=True)
    transcript = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Report(Base):
    """Generated review report"""
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False, unique=True)
    review = relationship("Review", back_populates="report")
    
    # Link to autonomous review job (for autonomous reviews)
    autonomous_review_job_id = Column(Integer, ForeignKey("autonomous_review_jobs.id"), nullable=True)
    autonomous_review_job = relationship("AutonomousReviewJob", back_populates="report")

    # Report content
    summary = Column(Text)
    overall_rag_status = Column(String)
    compliance_score = Column(Float)  # 0-100

    # Sections
    areas_followed = Column(JSON)  # List of compliant areas
    gaps_identified = Column(JSON)  # List of gaps with details
    recommendations = Column(JSON)  # List of recommendations
    action_items = Column(JSON)  # List of action items

    # Files
    pdf_path = Column(String, nullable=True)
    markdown_path = Column(String, nullable=True)

    # Approval workflow
    approval_status = Column(String, default=ApprovalStatus.PENDING.value)
    requires_approval = Column(Boolean, default=True)

    approvals = relationship("ReportApproval", back_populates="report", cascade="all, delete-orphan")

    created_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)


class ReportApproval(Base):
    """Report approval tracking"""
    __tablename__ = "report_approvals"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False)
    report = relationship("Report", back_populates="approvals")
    
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    approver = relationship("User", back_populates="approvals")
    
    status = Column(String, default=ApprovalStatus.PENDING.value)
    comments = Column(Text, nullable=True)
    
    decided_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AutoReviewStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AutonomousReviewJob(Base):
    """Tracks an autonomous code review background job"""
    __tablename__ = "autonomous_review_jobs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    checklist_id = Column(Integer, ForeignKey("checklists.id"), nullable=False)
    source_path = Column(String, nullable=False)

    status = Column(String, default=AutoReviewStatus.QUEUED.value)
    total_items = Column(Integer, default=0)
    completed_items = Column(Integer, default=0)

    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    agent_metadata = Column(JSON, nullable=True)  # hostname, IP, OS, agent version, etc.

    # Relationships
    project = relationship("Project")
    checklist = relationship("Checklist")
    results = relationship("AutonomousReviewResult", back_populates="job", cascade="all, delete-orphan")
    report = relationship("Report", back_populates="autonomous_review_job", uselist=False)


class AutonomousReviewResult(Base):
    """Per-item result from an autonomous review job"""
    __tablename__ = "autonomous_review_results"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("autonomous_review_jobs.id"), nullable=False)
    checklist_item_id = Column(Integer, ForeignKey("checklist_items.id"), nullable=False)

    strategy = Column(String)           # file_presence | pattern_scan | llm_analysis | metadata_check | human_required | ai_and_human
    rag_status = Column(String, default="na")   # green | amber | red | na | skipped
    evidence = Column(Text)             # What was found / LLM reasoning
    confidence = Column(Float, default=1.0)
    files_checked = Column(JSON, default=list)  # List of file paths examined
    skip_reason = Column(Text, nullable=True)   # Why item was skipped (human_required)
    evidence_hint = Column(Text, nullable=True) # What a human reviewer should provide
    needs_human_sign_off = Column(Boolean, default=False)  # AI ran but human must confirm

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    job = relationship("AutonomousReviewJob", back_populates="results")
    checklist_item = relationship("ChecklistItem")
    overrides = relationship("AutonomousReviewOverride", back_populates="result", cascade="all, delete-orphan")


class AutonomousReviewOverride(Base):
    """Human override for autonomous review results"""
    __tablename__ = "autonomous_review_overrides"

    id = Column(Integer, primary_key=True, index=True)
    result_id = Column(Integer, ForeignKey("autonomous_review_results.id"), nullable=False)
    
    # Relationship
    result = relationship("AutonomousReviewResult", back_populates="overrides")
    
    # Override details
    new_rag_status = Column(String, nullable=False)  # green | amber | red | na
    comments = Column(Text, nullable=False)
    reason = Column(String, nullable=True)  # project_specific | not_applicable | alternative_approach | other
    
    # Audit trail
    overridden_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    overridden_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # User relationship
    user = relationship("User")


class ChecklistRecommendation(Base):
    """AI-suggested checklist modifications"""
    __tablename__ = "checklist_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    checklist_id = Column(Integer, ForeignKey("checklists.id"), nullable=False)
    checklist = relationship("Checklist")

    # Recommendation details
    suggestion_type = Column(String)  # add_item, modify_item, remove_item
    description = Column(Text)
    rationale = Column(Text)  # Why this change is suggested
    priority = Column(String, default="medium")  # low, medium, high

    # Domain context
    based_on_domain = Column(String)
    confidence_score = Column(Float)  # AI confidence in suggestion

    # Status
    status = Column(String, default="pending")  # pending, accepted, rejected
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class ChecklistRoutingRule(Base):
    """
    Admin/PM-defined routing overrides for checklist items.
    Checked before hard-coded strategy_router rules.
    Phase 1: human_required flag per item.
    Phase 2+: full strategy + config per area/pattern.
    """
    __tablename__ = "checklist_routing_rules"

    id = Column(Integer, primary_key=True, index=True)
    checklist_item_id = Column(Integer, ForeignKey("checklist_items.id", ondelete="CASCADE"),
                               nullable=True, index=True)
    checklist_id = Column(Integer, ForeignKey("checklists.id", ondelete="CASCADE"),
                          nullable=True, index=True)  # reserved for Phase 2 area-level rules

    strategy = Column(String(50), nullable=False, default="human_required")
    skip_reason = Column(Text, nullable=True)
    evidence_hint = Column(Text, nullable=True)

    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    checklist_item = relationship("ChecklistItem")
    created_by = relationship("User")


# ── V2 Models ─────────────────────────────────────────────────────────────────

class ProjectMember(Base):
    """Persona-based team membership for a project"""
    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    persona = Column(String(100), nullable=True)  # pm|tech_lead|devops|qa|security|product_owner
    is_active = Column(Boolean, default=True)
    joined_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project")
    user = relationship("User")


class RecurringReviewSchedule(Base):
    """Scheduled recurring review configuration"""
    __tablename__ = "recurring_review_schedules"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    checklist_id = Column(Integer, ForeignKey("checklists.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), nullable=False)
    cadence = Column(String(50), nullable=False)   # daily|weekly|biweekly|monthly|quarterly
    day_of_week = Column(Integer, nullable=True)   # 0=Mon, used for weekly/biweekly
    time_of_day = Column(String(5), nullable=True) # HH:MM
    phase = Column(String(50), nullable=True)      # planning|execution|pre_launch|post_launch
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project")
    checklist = relationship("Checklist")


class MilestoneReviewTrigger(Base):
    """Event-based trigger for ad-hoc reviews"""
    __tablename__ = "milestone_review_triggers"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    checklist_id = Column(Integer, ForeignKey("checklists.id", ondelete="SET NULL"), nullable=True)
    trigger_event = Column(String(100), nullable=False)  # sprint_review|pre_release|go_no_go|post_incident
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project")
    checklist = relationship("Checklist")


class ReviewInstance(Base):
    """A concrete scheduled or triggered review occurrence"""
    __tablename__ = "review_instances"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    schedule_id = Column(Integer, ForeignKey("recurring_review_schedules.id", ondelete="SET NULL"), nullable=True)
    trigger_id = Column(Integer, ForeignKey("milestone_review_triggers.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    review_type = Column(String(50), nullable=False)  # scheduled|milestone|ad_hoc
    scheduled_at = Column(DateTime, nullable=False)
    self_review_due_at = Column(DateTime, nullable=True)
    self_review_required = Column(Boolean, default=False)
    status = Column(String(50), default="pending")
    # pending|self_review_in_progress|self_review_complete|stakeholder_meeting|completed|blocked
    readiness_score = Column(Float, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    project = relationship("Project")
    schedule = relationship("RecurringReviewSchedule")
    trigger = relationship("MilestoneReviewTrigger")
    self_review_sessions = relationship("SelfReviewSession", back_populates="review_instance", cascade="all, delete-orphan")
    reminders = relationship("ReminderQueue", back_populates="review_instance", cascade="all, delete-orphan")
    meeting_blocks = relationship("MeetingBlock", back_populates="review_instance", cascade="all, delete-orphan")
    stakeholder_preps = relationship("StakeholderPreparation", back_populates="review_instance", cascade="all, delete-orphan")


class SelfReviewSession(Base):
    """Persona-based self-review session before a stakeholder meeting"""
    __tablename__ = "self_review_sessions"

    id = Column(Integer, primary_key=True, index=True)
    review_instance_id = Column(Integer, ForeignKey("review_instances.id", ondelete="SET NULL"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    checklist_id = Column(Integer, ForeignKey("checklists.id", ondelete="SET NULL"), nullable=True)
    persona = Column(String(100), nullable=True)       # pm|tech_lead|devops|qa|security|product_owner
    participant_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    session_type = Column(String(50), default="self")  # self|persona|consolidated
    readiness_score = Column(Float, nullable=True)
    status = Column(String(50), default="pending")     # pending|in_progress|completed|skipped
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    review_instance = relationship("ReviewInstance", back_populates="self_review_sessions")
    project = relationship("Project")
    checklist = relationship("Checklist")
    participant = relationship("User")


class ConsolidatedSelfReviewReport(Base):
    """Aggregated readiness report across all personas for a review instance"""
    __tablename__ = "consolidated_self_review_reports"

    id = Column(Integer, primary_key=True, index=True)
    review_instance_id = Column(Integer, ForeignKey("review_instances.id", ondelete="SET NULL"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    overall_readiness_score = Column(Float, nullable=True)
    persona_scores = Column(JSON, nullable=True)             # {persona: score}
    cross_persona_gaps = Column(JSON, nullable=True)         # list of gap strings
    recommended_focus_areas = Column(JSON, nullable=True)    # list of area names
    generated_at = Column(DateTime, default=datetime.utcnow)
    generated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    review_instance = relationship("ReviewInstance")
    project = relationship("Project")


class ReminderQueue(Base):
    """Automated reminder scheduling for upcoming reviews"""
    __tablename__ = "reminder_queue"

    id = Column(Integer, primary_key=True, index=True)
    review_instance_id = Column(Integer, ForeignKey("review_instances.id", ondelete="CASCADE"), nullable=True)
    reminder_type = Column(String(50), nullable=False)
    # t_minus_7|t_minus_3|t_minus_2|t_minus_1|t_zero|escalation
    scheduled_at = Column(DateTime, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="pending")   # pending|sent|failed|cancelled
    recipient_ids = Column(JSON, nullable=True)
    template_name = Column(String(100), nullable=True)
    retry_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    review_instance = relationship("ReviewInstance", back_populates="reminders")


class MeetingBlock(Base):
    """Block a stakeholder meeting until self-review is complete"""
    __tablename__ = "meeting_blocks"

    id = Column(Integer, primary_key=True, index=True)
    review_instance_id = Column(Integer, ForeignKey("review_instances.id", ondelete="CASCADE"), nullable=True)
    reason = Column(String(255), nullable=False)
    status = Column(String(50), default="active")    # active|lifted|exception_approved
    blocked_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    unblocked_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    override_approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    exception_reason = Column(Text, nullable=True)
    blocked_at = Column(DateTime, default=datetime.utcnow)
    unblocked_at = Column(DateTime, nullable=True)

    review_instance = relationship("ReviewInstance", back_populates="meeting_blocks")


class StakeholderPreparation(Base):
    """Track preparation pack delivery and acknowledgement per stakeholder"""
    __tablename__ = "stakeholder_preparation"

    id = Column(Integer, primary_key=True, index=True)
    review_instance_id = Column(Integer, ForeignKey("review_instances.id", ondelete="CASCADE"), nullable=True)
    stakeholder_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    preparation_pack_sent_at = Column(DateTime, nullable=True)
    preparation_pack_viewed_at = Column(DateTime, nullable=True)
    readiness_score_viewed = Column(Boolean, default=False)
    suggested_questions_viewed = Column(Boolean, default=False)
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    review_instance = relationship("ReviewInstance", back_populates="stakeholder_preps")
    stakeholder = relationship("User")


class GapTracking(Base):
    """Persistent gap tracking across multiple reviews for a project"""
    __tablename__ = "gap_tracking"

    id = Column(Integer, primary_key=True, index=True)
    checklist_item_id = Column(Integer, ForeignKey("checklist_items.id", ondelete="SET NULL"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    first_identified_at = Column(DateTime, default=datetime.utcnow)
    gap_description = Column(Text, nullable=True)
    severity = Column(String(50), nullable=True)     # low|medium|high|critical
    status = Column(String(50), default="open")      # open|in_progress|resolved|accepted_risk
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    appeared_in_review_count = Column(Integer, default=1)
    last_seen_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    checklist_item = relationship("ChecklistItem")
    project = relationship("Project")
    owner = relationship("User")


class ReviewTrendAnalytics(Base):
    """Aggregated trend data per project per time period"""
    __tablename__ = "review_trend_analytics"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    period_type = Column(String(20), nullable=False)              # weekly|monthly|quarterly
    total_reviews = Column(Integer, default=0)
    avg_compliance_score = Column(Float, nullable=True)
    avg_readiness_score = Column(Float, nullable=True)
    self_review_completion_rate = Column(Float, nullable=True)    # 0.0–1.0
    on_time_completion_rate = Column(Float, nullable=True)        # 0.0–1.0
    meeting_block_rate = Column(Float, nullable=True)             # 0.0–1.0
    persistent_gaps = Column(JSON, nullable=True)                 # list of gap descriptions
    top_failing_areas = Column(JSON, nullable=True)               # list of area names
    computed_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project")

