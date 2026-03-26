"""
Database Models
"""
from sqlalchemy.ext.declarative import declarative_base
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
    is_required = Column(Boolean, default=True)
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
