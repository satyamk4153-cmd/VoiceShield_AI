from typing import List, Optional
from pydantic import BaseModel, Field


class FraudSignal(BaseModel):
    id: str = Field(..., description="Unique signal identifier")
    signal_type: str = Field(..., description="E.g. OTP_REQUEST, BANK_IMPERSONATION, ACCOUNT_BLOCK_THREAT")
    category: str = Field(..., description="AUTHENTICATION, IMPERSONATION, THREAT, FINANCIAL, TECHNICAL, SCAM")
    severity: str = Field("HIGH", description="CRITICAL, HIGH, MEDIUM, LOW")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Signal confidence score")
    description: str = Field(..., description="Human-readable explanation of why this was flagged")
    timestamp: Optional[str] = Field(None, description="Offset timestamp in interaction (e.g. 00:04)")
    risk_contribution: int = Field(..., ge=0, le=100, description="Contribution to total risk points")
    detected_phrases: List[str] = Field(default_factory=list, description="Extracted keywords or matched phrases")


class ContextualSignal(BaseModel):
    name: str = Field(..., description="Name of contextual factor (e.g. Urgency, Coercion, Secrecy)")
    score: float = Field(..., ge=0.0, le=1.0, description="Intensity of the contextual signal")
    severity: str = Field("MEDIUM", description="Severity tag")
    description: str = Field(..., description="Context explanation")


class FraudIntentResult(BaseModel):
    primary_category: str = Field("AUTHENTICATION_THEFT", description="Primary fraud classification")
    fraud_detected: bool = Field(True, description="Whether conversational fraud intent was identified")
    intent_score: float = Field(..., ge=0.0, le=1.0, description="Normalized fraud intent probability")
    detected_signals: List[FraudSignal] = Field(default_factory=list)
    contextual_signals: List[ContextualSignal] = Field(default_factory=list)
    language_detected: str = Field("English", description="English, Hindi, or Hinglish")


class TranscriptAnalysisRequest(BaseModel):
    transcript: str = Field(..., min_length=3, description="Call transcript text to analyze for fraud intent")
    caller_claimed_identity: Optional[str] = Field(None, description="Claimed organization e.g. HDFC Bank, Police")
    scenario_id: Optional[str] = Field(None, description="Optional preset scenario id")
