from typing import List, Literal, Optional
from pydantic import AliasChoices, BaseModel, Field


class ChecklistItemCreate(BaseModel):
    area: str
    question: str
    category: Optional[str] = None
    weight: float = 1.0
    is_review_mandatory: bool = Field(
        default=True,
        validation_alias=AliasChoices("is_review_mandatory", "is_required"),
    )
    expected_evidence: Optional[str] = None
    team_category: Optional[str] = None
    guidance: Optional[str] = None
    applicability_tags: Optional[List[str]] = None
    item_code: Optional[str] = None
    order: int = 0


class ChecklistItemUpdate(BaseModel):
    area: Optional[str] = None
    question: Optional[str] = None
    category: Optional[str] = None
    weight: Optional[float] = None
    is_review_mandatory: Optional[bool] = Field(
        default=None,
        validation_alias=AliasChoices("is_review_mandatory", "is_required"),
    )
    expected_evidence: Optional[str] = None
    team_category: Optional[str] = None
    guidance: Optional[str] = None
    applicability_tags: Optional[List[str]] = None
    item_code: Optional[str] = None
    order: Optional[int] = None


class ItemReorderReq(BaseModel):
    id: int
    order: int


class CloneChecklistResponse(BaseModel):
    id: int
    name: str
    type: str
    version: str
    project_id: Optional[int] = None
    is_global: bool
    item_count: int
    source_checklist_id: Optional[int] = None


class CloneChecklistReq(BaseModel):
    custom_name: Optional[str] = None


class SyncStrategyReq(BaseModel):
    strategy: Literal["add_new_only", "add_and_update", "full_reset"]


class SyncResult(BaseModel):
    added: int
    updated: int
    flagged_removed: int
    strategy_used: str
    flagged_items: List[str]


class GlobalChecklistCreate(BaseModel):
    name: str
    type: str = "master"
    version: Optional[str] = "1.0"
    organization_id: Optional[int] = None


class GlobalChecklistUpdate(BaseModel):
    name: Optional[str] = None
    version: Optional[str] = None


class GlobalChecklistItemCreate(BaseModel):
    item_code: Optional[str] = None
    area: str
    question: str
    category: Optional[str] = None
    weight: float = 1.0
    is_review_mandatory: bool = Field(
        default=True,
        validation_alias=AliasChoices("is_review_mandatory", "is_required"),
    )
    expected_evidence: Optional[str] = None
    team_category: Optional[str] = None
    guidance: Optional[str] = None
    applicability_tags: Optional[List[str]] = None
    order: int = 0


class GlobalChecklistItemUpdate(BaseModel):
    item_code: Optional[str] = None
    area: Optional[str] = None
    question: Optional[str] = None
    category: Optional[str] = None
    weight: Optional[float] = None
    is_review_mandatory: Optional[bool] = Field(
        default=None,
        validation_alias=AliasChoices("is_review_mandatory", "is_required"),
    )
    expected_evidence: Optional[str] = None
    team_category: Optional[str] = None
    guidance: Optional[str] = None
    applicability_tags: Optional[List[str]] = None
    order: Optional[int] = None
