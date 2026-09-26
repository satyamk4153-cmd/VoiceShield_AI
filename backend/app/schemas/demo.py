from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.fraud import FraudSignal


class DemoTimelineEvent(BaseModel):
    id: Optional[str] = None
    time_offset: str = Field(..., description="E.g. 00:02")
    seconds: int = Field(..., description="Seconds into the call")
    event_type: str = Field(..., description="E.g. INCOMING_CALL, IDENTITY_CLAIM, THREAT, OTP_DEMAND")
    label: str = Field(..., description="Brief label")
    transcript_segment: str = Field(..., description="Spoken words or system telemetry at this stage")
    signal_detected: Optional[str] = None
    severity: Optional[str] = None
    risk_accumulated: Optional[int] = Field(None, description="Running cumulative risk score (0-100)")


class DemoScenario(BaseModel):
    id: str
    name: str
    category: str
    description: str
    caller_claimed: str
    caller_phone: str = "+91 (022) 6128-4091"
    duration_seconds: int = 16
    transcript: str
    language: str = "English"
    expected_risk_score: int
    expected_risk_level: str
    expected_decision: str
    voice_spoof_prob: float = 0.5
    speaker_similarity: float = 0.5
    audio_quality: str = "FAIR"
    telephony_condition: str = "NORMAL"
    codec: str = "G.711u / 8kHz"
    channel: str = "Narrowband PSTN"
    warning_actions: List[str] = Field(default_factory=list)
    signals: List[FraudSignal] = Field(default_factory=list)
    timeline_events: List[DemoTimelineEvent] = Field(default_factory=list)
    is_synthetic: bool = True
    is_demo: bool = True
