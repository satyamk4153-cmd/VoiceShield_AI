import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_demo_scenarios():
    response = client.get("/api/demo/scenarios")
    assert response.status_code == 200
    scenarios = response.json()
    assert len(scenarios) == 6
    
    ids = [s["id"] for s in scenarios]
    assert "bank-otp-scam" in ids
    assert ("technical-remote-access" in ids or "customer-care-scam" in ids)
    assert ("digital-arrest" in ids or "police-impersonation" in ids)
    assert ("lottery-scam" in ids or "prize-lottery-scam" in ids)
    assert "legitimate-bank-call" in ids
    assert ("poor-quality-benign" in ids or "poor-quality-unknown" in ids)

    # Ensure all scenarios have distinct non-leaking properties
    names = set(s["name"] for s in scenarios)
    callers = set(s["caller_claimed"] for s in scenarios)
    transcripts = set(s["transcript"] for s in scenarios)
    assert len(names) == 6
    assert len(callers) == 6
    assert len(transcripts) == 6


def test_get_single_demo_scenario():
    # Canonical IDs
    canonical_cases = [
        ("bank-otp-scam", 94, "HIGH", "HDFC Bank Security Desk"),
        ("technical-remote-access", 86, "HIGH", "Amazon Refund Helpdesk"),
        ("digital-arrest", 92, "HIGH", "Cyber Crime Branch Delhi"),
        ("lottery-scam", 78, "HIGH", "KBC Lottery Department"),
        ("legitimate-bank-call", 8, "LOW", "ICICI Bank Card Protection"),
        ("poor-quality-benign", 14, "LOW", "Colleague / Arun"),
    ]
    for sc_id, score, level, caller in canonical_cases:
        response = client.get(f"/api/demo/scenarios/{sc_id}")
        assert response.status_code == 200, f"Failed for {sc_id}"
        data = response.json()
        assert data["expected_risk_score"] == score
        assert data["expected_risk_level"] == level
        assert data["caller_claimed"] == caller
        assert len(data["timeline_events"]) >= 4

    # Alias IDs backward compatibility
    alias_cases = [
        ("customer-care-scam", 86),
        ("police-impersonation", 92),
        ("prize-lottery-scam", 78),
        ("poor-quality-unknown", 14),
    ]
    for alias_id, expected_score in alias_cases:
        res = client.get(f"/api/demo/scenarios/{alias_id}")
        assert res.status_code == 200
        assert res.json()["expected_risk_score"] == expected_score


def test_demo_scenario_analysis():
    # Verify exact scenario analysis generation for legitimate call vs scam
    legit_res = client.get("/api/demo/scenarios/legitimate-bank-call/analysis")
    assert legit_res.status_code == 200
    legit_data = legit_res.json()
    assert legit_data["risk"]["score"] == 8
    assert legit_data["risk"]["decision"] in ("BENIGN", "ALLOW")
    assert legit_data["is_demo_data"] is True
    assert "ICICI" in legit_data["transcript"]
    assert len(legit_data["fraud_signals"]) == 0

    otp_res = client.get("/api/demo/scenarios/bank-otp-scam/analysis")
    assert otp_res.status_code == 200
    otp_data = otp_res.json()
    assert otp_data["risk"]["score"] == 94
    assert otp_data["risk"]["decision"] == "CONFIRMED_FRAUD"
    assert "HDFC" in otp_data["transcript"]


def test_get_invalid_demo_scenario():
    response = client.get("/api/demo/scenarios/non-existent-id")
    assert response.status_code == 404


def test_dashboard_stats_endpoint():
    response = client.get("/api/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert "is_demo_data" in data
    assert data["total_calls_analyzed"] >= 0
    assert len(data["risk_distribution"]) >= 3
    assert len(data["recent_incidents"]) >= 1

