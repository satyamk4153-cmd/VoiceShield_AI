from typing import Optional, List
from pydantic import BaseModel, Field


class SpeakerProfileCreate(BaseModel):
    id: str = Field(..., description="Unique profile identifier, e.g., SPK-HDFC-OFFICIAL-01")
    name: str = Field(..., description="Full descriptive name of speaker")
    identity_claimed: str = Field(..., description="Organization role/title claimed")
    consent_recorded: bool = Field(True, description="Explicit biometric consent recorded flag")
    retention_days: int = Field(365, description="Data retention period in days")


class SpeakerProfileResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    identity_claimed: str
    consent_recorded: bool
    retention_days: int
    is_active: bool
    enrollment_count: int
    created_at: str


class SpeakerVerificationResult(BaseModel):
    similarity: float = Field(..., ge=0.0, le=1.0, description="Cosine similarity between reference and test speaker")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence of the speaker verification assessment")
    result: str = Field(..., description="MATCH, MISMATCH, or UNCERTAIN")
    threshold: float = Field(0.70, description="Configured decision threshold")
    explanation: str = Field(..., description="Explainable description of the biometric comparison")
    model_name: str = Field("vocal-tract-filterbank", description="Embedding model used")
    model_version: str = Field("v1.0", description="Model version")
    status: str = Field("OK", description="OK, UNCERTAIN, or UNAVAILABLE")
    is_demo: bool = Field(False, description="Indicates if signal is computed via synthetic demo provider")


class SpeakerVerificationRequest(BaseModel):
    reference_sample_id: Optional[str] = Field(None, description="Enrolled reference profile ID")
    test_transcript: Optional[str] = Field(None, description="Optional spoken text")
