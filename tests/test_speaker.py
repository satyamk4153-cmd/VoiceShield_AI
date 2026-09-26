import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_speaker_verification():
    payload = {
        "reference_sample_id": "SPK-BANK-OFFICIAL-01",
        "test_transcript": "Hello, I am calling from the bank."
    }
    response = client.post("/api/verify/speaker", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "similarity" in data
    assert "confidence" in data
    assert data["result"] in ["MATCH", "MISMATCH", "UNCERTAIN"]
    assert "is_demo" in data
    assert isinstance(data["is_demo"], bool)
