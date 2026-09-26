import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_transcript_analysis_otp_and_threat():
    payload = {
        "transcript": "Your SBI account will be blocked within 5 minutes. Tell me your 6 digit OTP immediately to verify.",
        "caller_claimed_identity": "SBI Bank"
    }
    response = client.post("/api/analyze/transcript", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["risk"]["score"] >= 70
    assert data["risk"]["level"] == "HIGH"
    
    signal_types = [s["signal_type"] for s in data["fraud_signals"]]
    assert "OTP_REQUEST" in signal_types
    assert "BANK_IMPERSONATION" in signal_types
    assert "ACCOUNT_BLOCK_THREAT" in signal_types


def test_transcript_analysis_hinglish():
    payload = {
        "transcript": "Aapka khata turant band ho jayega agar aapne OTP nahi bataya. 5000 rupaye bhejiye.",
        "caller_claimed_identity": "Police Officer"
    }
    response = client.post("/api/analyze/transcript", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["risk"]["level"] in ["HIGH", "CRITICAL"]


def test_transcript_analysis_benign():
    payload = {
        "transcript": "Good morning, we are calling to confirm if you received your new bank passbook by post. We will never ask for your password.",
        "caller_claimed_identity": "ICICI Official"
    }
    response = client.post("/api/analyze/transcript", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["risk"]["score"] < 40
    assert data["risk"]["level"] == "LOW"
