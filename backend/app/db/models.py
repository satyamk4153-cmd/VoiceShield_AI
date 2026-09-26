import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime,
    ForeignKey, Text, JSON, Enum, Index
)
from sqlalchemy.orm import relationship
from app.db.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


# ==============================================================================
# Organizations, Users & RBAC
# ==============================================================================

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(128), nullable=False)
    slug = Column(String(64), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    settings = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    call_sessions = relationship("CallSession", back_populates="organization")
    incidents = relationship("Incident", back_populates="organization")
    policies = relationship("RiskPolicy", back_populates="organization")


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(128), nullable=False)
    role = Column(String(32), default="SOC_ANALYST", nullable=False) # ADMIN, SOC_ANALYST, INVESTIGATOR, AUDITOR
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    organization = relationship("Organization", back_populates="users")
    assigned_incidents = relationship("Incident", back_populates="assignee")


# ==============================================================================
# Call Sessions & Ingestion Stream
# ==============================================================================

class CallSession(Base):
    __tablename__ = "call_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    channel = Column(String(32), default="TELEPHONY_STREAM") # TELEPHONY_STREAM, AUDIO_UPLOAD, WEBSOCKET_LIVE
    claimed_identity = Column(String(128), nullable=True)
    caller_phone = Column(String(32), nullable=True)
    status = Column(String(32), default="ACTIVE") # ACTIVE, COMPLETED, FAILED, TERMINATED
    language = Column(String(32), default="English")
    risk_score = Column(Integer, nullable=True)
    decision = Column(String(32), nullable=True)
    start_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    end_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    organization = relationship("Organization", back_populates="call_sessions")
    analyses = relationship("AnalysisModel", back_populates="session", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="session")
    transcript_segments = relationship("TranscriptSegment", back_populates="session", cascade="all, delete-orphan")


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("call_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    segment_index = Column(Integer, default=0)
    speaker_label = Column(String(32), default="CALLER")
    raw_text = Column(Text, nullable=False)
    redacted_text = Column(Text, nullable=False)
    start_time = Column(Float, default=0.0)
    end_time = Column(Float, default=0.0)
    confidence = Column(Float, default=1.0)
    language = Column(String(32), default="en")

    session = relationship("CallSession", back_populates="transcript_segments")


# ==============================================================================
# Biometric Speaker Profiles & Enrolled Embeddings
# ==============================================================================

class SpeakerProfile(Base):
    __tablename__ = "speaker_profiles"

    id = Column(String(64), primary_key=True) # e.g. SPK-HDFC-OFFICIAL-01
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    identity_claimed = Column(String(128), nullable=False)
    consent_recorded = Column(Boolean, default=True)
    consent_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    retention_days = Column(Integer, default=365)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    enrollments = relationship("SpeakerEnrollment", back_populates="profile", cascade="all, delete-orphan")


class SpeakerEnrollment(Base):
    __tablename__ = "speaker_enrollments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    profile_id = Column(String(64), ForeignKey("speaker_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    audio_duration = Column(Float, default=0.0)
    sample_rate = Column(Integer, default=16000)
    embedding_vector = Column(JSON, nullable=False) # Serialized acoustic feature vector
    model_version = Column(String(64), default="vocal-tract-filterbank-v1")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    profile = relationship("SpeakerProfile", back_populates="enrollments")


# ==============================================================================
# Analysis & Risk Engine Core Models
# ==============================================================================

class AnalysisModel(Base):
    __tablename__ = "analyses"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    session_id = Column(String(36), ForeignKey("call_sessions.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    status = Column(String(32), default="COMPLETED", index=True) # QUEUED, PROCESSING, COMPLETED, FAILED, PARTIAL, UNAVAILABLE
    is_demo = Column(Boolean, default=False)
    provider_used = Column(String(32), default="local")
    
    # Risk Engine Scores
    risk_score = Column(Integer, nullable=False, index=True)
    risk_level = Column(String(16), nullable=False, index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    decision = Column(String(32), nullable=False, index=True)    # ALLOW, STEP_UP_REQUIRED, ANALYST_REVIEW, BLOCK_CALL
    confidence = Column(Float, default=0.90)
    
    # Audio Quality Metrics
    audio_quality = Column(String(16), default="FAIR")  # GOOD, FAIR, POOR, UNAVAILABLE
    telephony_condition = Column(String(32), default="NORMAL") # NORMAL, DEGRADED, HIGHLY_DEGRADED
    
    # Voice Authenticity
    voice_authenticity = Column(String(32), default="AUTHENTIC") # AUTHENTIC, POSSIBLE_SPOOF, SUSPICIOUS, UNAVAILABLE
    spoof_probability = Column(Float, default=0.0)
    
    # Speaker Verification
    speaker_result = Column(String(16), default="NOT_EVALUATED") # MATCH, MISMATCH, UNCERTAIN, NOT_EVALUATED
    speaker_similarity = Column(Float, default=0.0)
    
    # Fraud Intent
    fraud_category = Column(String(64), default="BENIGN")
    caller_claimed = Column(String(128), nullable=True)
    transcript_redacted = Column(Text, nullable=True)
    
    # Stored payload summaries
    risk_breakdown = Column(JSON, default=dict)
    recommended_actions = Column(JSON, default=list)
    explanation = Column(Text, nullable=True)

    # Relations
    session = relationship("CallSession", back_populates="analyses")
    signals = relationship("FraudSignalModel", back_populates="analysis", cascade="all, delete-orphan")
    incident = relationship("Incident", back_populates="analysis", uselist=False)


class FraudSignalModel(Base):
    __tablename__ = "fraud_signals"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    analysis_id = Column(String(36), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    signal_type = Column(String(64), nullable=False, index=True)
    category = Column(String(32), nullable=False)
    severity = Column(String(16), default="HIGH") # LOW, MEDIUM, HIGH, CRITICAL
    confidence = Column(Float, default=0.9)
    description = Column(Text, nullable=False)
    timestamp = Column(String(16), nullable=True)
    risk_contribution = Column(Integer, default=15)
    
    analysis = relationship("AnalysisModel", back_populates="signals")


class RiskPolicy(Base):
    __tablename__ = "risk_policies"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    version = Column(String(32), default="v1.0")
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    min_score_step_up = Column(Integer, default=40)
    min_score_review = Column(Integer, default=65)
    min_score_block = Column(Integer, default=85)
    rules_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    organization = relationship("Organization", back_populates="policies")


# ==============================================================================
# Incident Management & SOC Investigation
# ==============================================================================

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String(36), primary_key=True, default=generate_uuid) # e.g. INC-9401
    incident_number = Column(String(32), unique=True, nullable=False, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(36), ForeignKey("call_sessions.id", ondelete="SET NULL"), nullable=True)
    analysis_id = Column(String(36), ForeignKey("analyses.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    status = Column(String(32), default="NEW", index=True) # NEW, UNDER_INVESTIGATION, RESOLVED, FALSE_POSITIVE, ESCALATED
    severity = Column(String(16), default="HIGH", index=True) # LOW, MEDIUM, HIGH, CRITICAL
    risk_score = Column(Integer, nullable=False, index=True)
    decision = Column(String(32), nullable=False)
    caller_claimed = Column(String(128), nullable=True)
    assigned_to = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    flags = Column(JSON, default=list)
    analyst_override_decision = Column(String(32), nullable=True)
    analyst_override_reason = Column(Text, nullable=True)
    analyst_override_by = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime, nullable=True)

    organization = relationship("Organization", back_populates="incidents")
    session = relationship("CallSession", back_populates="incidents")
    analysis = relationship("AnalysisModel", back_populates="incident")
    assignee = relationship("User", back_populates="assigned_incidents")
    timeline_events = relationship("IncidentEvent", back_populates="incident", cascade="all, delete-orphan")
    notes = relationship("IncidentNote", back_populates="incident", cascade="all, delete-orphan")
    evidence_items = relationship("EvidenceItem", back_populates="incident", cascade="all, delete-orphan")


class IncidentEvent(Base):
    __tablename__ = "incident_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False) # SESSION_STARTED, FRAUD_SIGNAL, VOICE_SPOOF, SPEAKER_MISMATCH, OVERRIDE
    label = Column(String(128), nullable=False)
    timestamp_offset = Column(String(16), default="00:00")
    description = Column(Text, nullable=False)
    severity = Column(String(16), default="INFO")
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    incident = relationship("Incident", back_populates="timeline_events")


class IncidentNote(Base):
    __tablename__ = "incident_notes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(String(36), nullable=True)
    author_name = Column(String(128), nullable=False)
    note_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    incident = relationship("Incident", back_populates="notes")


class EvidenceItem(Base):
    __tablename__ = "evidence_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(128), nullable=False)
    category = Column(String(32), nullable=False)
    severity = Column(String(16), default="HIGH")
    explanation = Column(Text, nullable=False)
    contribution_points = Column(Integer, default=0)
    timestamp_offset = Column(String(16), default="00:00")
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    incident = relationship("Incident", back_populates="evidence_items")


# ==============================================================================
# Security Audit Logs & Model Registry
# ==============================================================================

class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), nullable=True, index=True)
    user_id = Column(String(36), nullable=True, index=True)
    action = Column(String(64), nullable=False, index=True)
    resource = Column(String(64), nullable=True)
    resource_id = Column(String(64), nullable=True)
    endpoint = Column(String(128), nullable=False)
    client_ip = Column(String(64), default="unknown")
    status_code = Column(Integer, default=200)
    request_id = Column(String(64), nullable=True, index=True)
    risk_score_generated = Column(Integer, nullable=True)
    metadata_json = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


class ModelRegistry(Base):
    __tablename__ = "model_registry"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    model_name = Column(String(128), nullable=False, index=True)
    version = Column(String(32), nullable=False)
    task_type = Column(String(64), nullable=False) # ANTI_SPOOFING, SPEAKER_VERIFICATION, INTENT_CLASSIFICATION
    framework = Column(String(64), default="scipy_dsp_pipeline")
    artifact_uri = Column(String(255), nullable=True)
    hash_digest = Column(String(128), nullable=True)
    license = Column(String(64), default="Apache-2.0")
    metrics_json = Column(JSON, default=dict)
    status = Column(String(32), default="ACTIVE") # ACTIVE, SHADOW, DEPRECATED, DISABLED
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# ==============================================================================
# Isolated Demo Scenarios (Strictly for Demo Mode & Unit Fixtures)
# ==============================================================================

class DemoScenarioModel(Base):
    __tablename__ = "demo_scenarios"

    id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False)
    category = Column(String(64), nullable=False)
    description = Column(Text, nullable=False)
    caller_claimed = Column(String(128), nullable=False)
    transcript = Column(Text, nullable=False)
    language = Column(String(32), default="English")
    expected_risk_score = Column(Integer, nullable=False)
    expected_risk_level = Column(String(16), nullable=False)
    expected_decision = Column(String(32), nullable=False)
    voice_spoof_prob = Column(Float, default=0.5)
    speaker_similarity = Column(Float, default=0.5)
    audio_quality = Column(String(16), default="FAIR")
    telephony_condition = Column(String(32), default="NORMAL")
    signals_data = Column(JSON, default=list)
    timeline_data = Column(JSON, default=list)
