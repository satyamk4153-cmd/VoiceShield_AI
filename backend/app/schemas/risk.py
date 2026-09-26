from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.audio import AudioQualityResult
from app.schemas.speaker import SpeakerVerificationResult
from app.schemas.fraud import FraudSignal, ContextualSignal, FraudIntentResult


class VoiceAuthenticityResult(BaseModel):
    authenticity_probability: float = Field(..., ge=0.0, le=1.0)
    spoof_probability: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    classification: str = Field(..., description="AUTHENTIC, POSSIBLE_SPOOF, SUSPICIOUS, UNCERTAIN, or UNAVAILABLE")
    explanation: str = Field(..., description="Explainable description of synthetic voice artifacts")
    model_name: str = Field("acoustic-spectral-anti-spoof", description="Anti-spoofing model architecture")
    model_version: str = Field("v1.0", description="Model version")
    inference_ms: int = Field(0, description="Inference latency in milliseconds")
    status: str = Field("OK", description="Inference status: OK, UNCERTAIN, or UNAVAILABLE")
    is_demo: bool = Field(False)


class RiskAssessment(BaseModel):
    score: int = Field(..., ge=0, le=100, description="Composite Risk Score 0-100")
    level: str = Field(..., description="LOW, MEDIUM, HIGH, or CRITICAL")
    decision: str = Field(..., description="ALLOW, STEP_UP_REQUIRED, ANALYST_REVIEW, BLOCK_CALL, or ESCALATE")
    confidence: float = Field(..., ge=0.0, le=1.0)
    risk_breakdown: Dict[str, int] = Field(default_factory=dict, description="Point contribution breakdown")
    policy_id: Optional[str] = None
    policy_version: Optional[str] = None
    reason_codes: List[str] = Field(default_factory=list)


class EvidenceItem(BaseModel):
    id: str
    timestamp: str = Field(..., description="Timestamp offset (e.g. 00:06)")
    title: str = Field(..., description="Brief headline e.g. 'OTP request detected'")
    category: str = Field(..., description="E.g. AUTHENTICATION, IMPERSONATION, BIOMETRIC, SYNTHETIC_AUDIO")
    severity: str = Field(..., description="CRITICAL, HIGH, MEDIUM, LOW")
    explanation: str = Field(..., description="Detailed rationale")
    contribution_points: int = Field(..., description="Points added to total risk score")


class FinalAnalysisResponse(BaseModel):
    analysis_id: str
    session_id: Optional[str] = None
    incident_id: Optional[str] = None
    status: str = "completed"
    created_at: str
    is_demo_data: bool = False
    provider_used: str = "local"
    transcript: Optional[str] = None
    caller_claimed_identity: Optional[str] = None
    
    risk: RiskAssessment
    voice: VoiceAuthenticityResult
    speaker: SpeakerVerificationResult
    audio: AudioQualityResult
    fraud_signals: List[FraudSignal]
    contextual_signals: List[ContextualSignal]
    evidence: List[EvidenceItem]
    recommended_actions: List[str]


class DirectRiskScoreRequest(BaseModel):
    intent_score: float = Field(..., ge=0.0, le=1.0)
    spoof_probability: float = Field(0.5, ge=0.0, le=1.0)
    speaker_similarity: float = Field(0.5, ge=0.0, le=1.0)
    context_urgency: float = Field(0.5, ge=0.0, le=1.0)
    audio_quality_score: float = Field(0.8, ge=0.0, le=1.0)
