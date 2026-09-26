import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.demo_engine import DemoEngineService
from app.services.risk_engine import RiskEngineService
from app.schemas.audio import AudioQualityResult
from app.schemas.speaker import SpeakerVerificationResult
from app.schemas.risk import VoiceAuthenticityResult

client = TestClient(app)


def test_bank_otp_scam_exact_94_risk_score():
    """
    CRITICAL DEMO VERIFICATION:
    Verifies that the Bank OTP scam scenario deterministically fuses
    into exact Risk Score = 94 and Risk Level = HIGH via the backend Risk Engine.
    """
    bank_scenario = DemoEngineService.get_scenario_by_id("bank-otp-scam")
    assert bank_scenario is not None
    assert bank_scenario.expected_risk_score == 94
    assert bank_scenario.expected_risk_level == "HIGH"

    # Now verify via actual RiskEngineService execution
    voice_auth = VoiceAuthenticityResult(
        authenticity_probability=0.09,
        spoof_probability=0.91,
        confidence=0.88,
        classification="POSSIBLE_SPOOF",
        explanation="Synthetic voice anomalies detected.",
        is_demo=True
    )
    speaker_verif = SpeakerVerificationResult(
        similarity=0.18,
        confidence=0.91,
        result="MISMATCH",
        explanation="Voice failed cosine similarity against bank baseline.",
        is_demo=True
    )
    audio_quality = AudioQualityResult(
        duration_seconds=15.0,
        sample_rate=8000,
        channels=1,
        rms_energy=0.12,
        snr_db=18.4,
        clipping_ratio=0.01,
        silence_ratio=0.22,
        bandwidth_hz=3400,
        quality_score=0.62,
        quality_level="FAIR",
        telephony_condition="DEGRADED",
        quality_notes=[]
    )

    assessment, evidence, actions = RiskEngineService.fuse_risk_assessment(
        fraud_signals=bank_scenario.signals,
        contextual_signals=[],
        voice_auth=voice_auth,
        speaker_verif=speaker_verif,
        audio_quality=audio_quality
    )

    assert assessment.score == 94, f"Expected 94 but got {assessment.score}"
    assert assessment.level in ["HIGH", "CRITICAL"]
    assert assessment.decision in ["CONFIRMED", "BLOCK_CALL"]
    assert len(actions) >= 2


def test_direct_risk_score_api():
    payload = {
        "intent_score": 0.9,
        "spoof_probability": 0.85,
        "speaker_similarity": 0.2,
        "context_urgency": 0.8,
        "audio_quality_score": 0.6
    }
    response = client.post("/api/risk/score", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["score"] >= 60
    assert data["level"] in ["HIGH", "CRITICAL"]
