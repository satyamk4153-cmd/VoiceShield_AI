from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class IncidentNoteSchema(BaseModel):
    id: str
    author_id: Optional[str] = None
    author_name: str
    note_text: str
    created_at: str


class IncidentEventSchema(BaseModel):
    id: str
    event_type: str
    label: str
    timestamp_offset: str
    description: str
    severity: str
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: str


class EvidenceItemSchema(BaseModel):
    id: str
    title: str
    category: str
    severity: str
    explanation: str
    contribution_points: int
    timestamp_offset: str
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class IncidentDetailResponse(BaseModel):
    id: str
    incident_number: str
    organization_id: str
    session_id: Optional[str] = None
    analysis_id: Optional[str] = None
    title: str
    status: str
    severity: str
    risk_score: int
    decision: str
    caller_claimed: Optional[str] = None
    assigned_to: Optional[str] = None
    assignee_name: Optional[str] = None
    flags: List[str] = Field(default_factory=list)
    analyst_override_decision: Optional[str] = None
    analyst_override_reason: Optional[str] = None
    analyst_override_by: Optional[str] = None
    created_at: str
    updated_at: str
    resolved_at: Optional[str] = None
    timeline_events: List[IncidentEventSchema] = Field(default_factory=list)
    notes: List[IncidentNoteSchema] = Field(default_factory=list)
    evidence_items: List[EvidenceItemSchema] = Field(default_factory=list)


class IncidentListResponse(BaseModel):
    items: List[IncidentDetailResponse]
    total: int
    page: int
    page_size: int


class IncidentStatusUpdate(BaseModel):
    status: str = Field(..., description="NEW, UNDER_INVESTIGATION, RESOLVED, FALSE_POSITIVE, ESCALATED")
    assigned_to: Optional[str] = None


class IncidentNoteCreate(BaseModel):
    note_text: str = Field(..., min_length=1)


class IncidentOverrideRequest(BaseModel):
    new_decision: str = Field(..., description="ALLOW, STEP_UP_REQUIRED, ANALYST_REVIEW, BLOCK_CALL, FALSE_POSITIVE")
    reason: str = Field(..., min_length=5, description="Audited justification for overriding automated policy decision")
