import io
import wave
import struct
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import hash_password, create_access_token, decode_access_token
from app.services.pii_service import PIIRedactionService
from app.services.policy_engine import PolicyEngineService
from app.services.anti_spoof import VoiceAntiSpoofModel
from app.services.speaker_verification import SpeakerVerificationModel
from app.schemas.fraud import FraudSignal
from app.schemas.risk import VoiceAuthenticityResult
from app.schemas.speaker import SpeakerVerificationResult
from app.schemas.audio import AudioQualityResult

client = TestClient(app)


# ==============================================================================
# 1. PII Redaction Pipeline Tests (Section 16)
# ==============================================================================

def test_pii_redaction_comprehensive():
    raw_text = (
        "My OTP is 492019 and account number is 100982348123. "
        "Call me back on +91 98230 45678 or email alert@victim.org. "
        "Card: 4532-1234-5678-9012, PAN: ABCDE1234F, Aadhaar: 1234 5678 9012."
    )
    redacted, stats = PIIRedactionService.redact_transcript(raw_text)

    assert "492019" not in redacted
    assert "100982348123" not in redacted
    assert "4532-1234-5678-9012" not in redacted
    assert "alert@victim.org" not in redacted
    assert "ABCDE1234F" not in redacted
    assert "[REDACTED_OTP]" in redacted or "[REDACTED_CARD]" in redacted or "[REDACTED_ACCOUNT]" in redacted
    assert len(stats) >= 3


# ==============================================================================
# 2. Policy Engine Evaluation Tests (Section 21 & Section 96)
# ==============================================================================

def test_policy_engine_block_decision():
    # Critical OTP request with spoofed voice triggers BLOCK_CALL
    fraud_signals = [
        FraudSignal(
            id="SIG-01", signal_type="OTP_REQUEST", category="AUTHENTICATION",
            severity="CRITICAL", confidence=0.98, description="OTP demand",
            timestamp="00:04", risk_contribution=28
        )
    ]
    voice_auth = VoiceAuthenticityResult(
        authenticity_probability=0.1, spoof_probability=0.9, confidence=0.9,
        classification="POSSIBLE_SPOOF", explanation="Vocoder artifacts",
        status="OK", is_demo=False
    )
    speaker_verif = SpeakerVerificationResult(
        similarity=0.2, confidence=0.9, result="MISMATCH",
        threshold=0.70, explanation="Mismatch", status="OK", is_demo=False
    )
    
    decision = PolicyEngineService.evaluate_policy(
        risk_score=92,
        confidence=0.94,
        fraud_signals=fraud_signals,
        voice_auth=voice_auth,
        speaker_verif=speaker_verif
    )

    assert decision.decision == "BLOCK_CALL"
    assert "CRITICAL_SYNTHETIC_OR_IMPERSONATED_OTP_THEFT" in decision.reason_codes
    assert len(decision.actions_required) >= 2


def test_policy_engine_allow_decision():
    # Benign low-risk interaction triggers ALLOW
    decision = PolicyEngineService.evaluate_policy(
        risk_score=15,
        confidence=0.92,
        fraud_signals=[],
        voice_auth=VoiceAuthenticityResult(
            authenticity_probability=0.95, spoof_probability=0.05, confidence=0.9,
            classification="AUTHENTIC", explanation="Natural", status="OK", is_demo=False
        ),
        speaker_verif=SpeakerVerificationResult(
            similarity=0.85, confidence=0.9, result="MATCH",
            threshold=0.70, explanation="Match", status="OK", is_demo=False
        )
    )

    assert decision.decision == "ALLOW"
    assert "RISK_WITHIN_TOLERABLE_BOUNDS" in decision.reason_codes


# ==============================================================================
# 3. Model Abstraction Tests (Section 11 & Section 12)
# ==============================================================================

def test_voice_anti_spoof_model_metadata_and_predict():
    model = VoiceAntiSpoofModel()
    meta = model.metadata()
    assert meta["model_name"] == "SentinelVoice-Spectral-AntiSpoof"
    assert meta["benchmark_target"] == "ASVspoof 2021 / Logical Access"

    # Synthetic test samples
    sr = 16000
    samples = np.sin(2 * np.pi * 440 * np.linspace(0, 1.0, sr)).astype(np.float32)
    pred = model.predict(samples, sr, telephony_condition="NORMAL")
    
    assert "spoof_probability" in pred
    assert "bonafide_probability" in pred
    assert pred["status"] == "OK"
    assert pred["inference_ms"] >= 0


def test_speaker_verification_cosine_similarity():
    model = SpeakerVerificationModel()
    sr = 16000
    samples1 = np.sin(2 * np.pi * 300 * np.linspace(0, 1.0, sr)).astype(np.float32)
    samples2 = np.sin(2 * np.pi * 300 * np.linspace(0, 1.0, sr)).astype(np.float32)
    samples3 = np.sin(2 * np.pi * 800 * np.linspace(0, 1.0, sr)).astype(np.float32)

    emb1 = model.extract_embedding(samples1, sr)
    emb2 = model.extract_embedding(samples2, sr)
    emb3 = model.extract_embedding(samples3, sr)

    sim_identical = model.compute_similarity(emb1, emb2)
    sim_different = model.compute_similarity(emb1, emb3)

    assert sim_identical >= 0.95
    assert sim_different < sim_identical


# ==============================================================================
# 4. Authentication, JWT & RBAC Tests (Section 26 & Section 27)
# ==============================================================================

def test_jwt_token_creation_and_validation():
    data = {"sub": "user-test-123", "email": "analyst@sentinelvoice.internal", "role": "SOC_ANALYST"}
    token = create_access_token(data)
    decoded = decode_access_token(token)
    assert decoded["sub"] == "user-test-123"
    assert decoded["email"] == "analyst@sentinelvoice.internal"


def test_auth_login_endpoint():
    payload = {
        "email": "analyst@sentinelvoice.internal",
        "password": "SentinelAnalyst2026!"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["email"] == "analyst@sentinelvoice.internal"


# ==============================================================================
# 5. Incident Lifecycle & Analyst Override (Section 22 & Section 54)
# ==============================================================================

def test_incident_lifecycle_flow():
    # 1. Trigger an analysis that generates an incident
    payload = {
        "transcript": "Immediate action required. Transfer 50000 INR to UPI address and read out your 6-digit verification code or your account will be frozen by cyber police.",
        "caller_claimed_identity": "Cyber Crime Inspector"
    }
    res = client.post("/api/v1/analyses/transcript", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["risk"]["score"] >= 70
    assert data["incident_id"] is not None

    incident_num = data["incident_id"]

    # 2. Inspect incident
    inc_res = client.get(f"/api/v1/incidents/{incident_num}")
    assert inc_res.status_code == 200
    inc_data = inc_res.json()
    assert inc_data["status"] == "NEW"

    # 3. Add analyst note
    note_payload = {"note_text": "Investigated caller phone; confirmed unauthorized telecom origin."}
    note_res = client.post(f"/api/v1/incidents/{incident_num}/notes", json=note_payload)
    assert note_res.status_code == 200

    # 4. Perform analyst decision override
    override_payload = {
        "new_decision": "BLOCK_CALL",
        "reason": "Confirmed extortion attempt verified with telecom carrier logs."
    }
    over_res = client.post(f"/api/v1/incidents/{incident_num}/override", json=override_payload)
    assert over_res.status_code == 200
    updated_data = over_res.json()
    assert updated_data["decision"] == "BLOCK_CALL"
    assert updated_data["analyst_override_reason"] == override_payload["reason"]
