"""
Comprehensive End-to-End Audit & Verification Script
Verifies frontend HTML routes, backend API contracts, auth flow, analyst overrides, and error handling.
"""
import sys
import json
import urllib.request
import urllib.error
import urllib.parse

BACKEND_BASE = "http://127.0.0.1:8000"
FRONTEND_BASE = "http://127.0.0.1:3000"

def log(msg, status="INFO"):
    symbol = "[OK]" if status == "PASS" else "[FAIL]" if status == "FAIL" else "[INFO]"
    print(f"[{status}] {symbol} {msg}")

def test_frontend_routes():
    print("\n--- 1. AUDITING FRONTEND ROUTES ---")
    routes = [
        "/",
        "/about",
        "/analyze",
        "/dashboard",
        "/demo",
        "/evidence",
        "/live",
        "/login",
        "/result",
        "/speaker",
    ]
    all_passed = True
    for route in routes:
        url = f"{FRONTEND_BASE}{route}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SentinelAudit/1.0"})
            with urllib.request.urlopen(req, timeout=5) as res:
                content = res.read().decode('utf-8', errors='ignore')
                status = res.status
                has_viewport = "viewport" in content
                has_sentinel = "SENTINELVOICE" in content or "SentinelVoice" in content
                if status == 200 and has_viewport:
                    log(f"Route {route} -> HTTP {status} (HTML bytes: {len(content)}, Viewport Meta: OK)", "PASS")
                else:
                    log(f"Route {route} -> HTTP {status} (Unexpected HTML content)", "FAIL")
                    all_passed = False
        except Exception as e:
            log(f"Route {route} failed: {e}", "FAIL")
            all_passed = False
    return all_passed

def test_api_contracts_and_auth():
    print("\n--- 2. AUDITING BACKEND API & AUTH CONTRACTS ---")
    all_passed = True

    # Health
    try:
        req = urllib.request.Request(f"{BACKEND_BASE}/api/v1/health")
        with urllib.request.urlopen(req, timeout=5) as res:
            data = json.loads(res.read().decode())
            assert data["status"] == "healthy"
            assert data["service"] == "SentinelVoice"
            log("Health endpoint (/api/v1/health) is operational", "PASS")
    except Exception as e:
        log(f"Health check failed: {e}", "FAIL")
        all_passed = False

    # Invalid Login: Malformed password (< 8 chars) triggers 422
    try:
        req = urllib.request.Request(
            f"{BACKEND_BASE}/api/v1/auth/login",
            data=json.dumps({"email": "unknown@invalid.internal", "password": "short"}).encode(),
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=5)
        log("Short password should have triggered 422 validation error", "FAIL")
        all_passed = False
    except urllib.error.HTTPError as e:
        if e.code == 422:
            log("Pydantic schema validation working: short password properly rejected with HTTP 422", "PASS")
        else:
            log(f"Expected 422, got {e.code}", "FAIL")
            all_passed = False

    # Invalid Login: Well-formed credentials with incorrect password triggers 401
    try:
        req = urllib.request.Request(
            f"{BACKEND_BASE}/api/v1/auth/login",
            data=json.dumps({"email": "unknown@invalid.internal", "password": "WrongPassword2026!"}).encode(),
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=5)
        log("Invalid login should have failed with 401", "FAIL")
        all_passed = False
    except urllib.error.HTTPError as e:
        if e.code == 401:
            log("Invalid login properly rejected with HTTP 401 Unauthorized", "PASS")
        else:
            log(f"Invalid login returned unexpected status {e.code}", "FAIL")
            all_passed = False

    # Valid Login
    token = None
    try:
        req = urllib.request.Request(
            f"{BACKEND_BASE}/api/v1/auth/login",
            data=json.dumps({"email": "soc_analyst@sentinelvoice.internal", "password": "AnalystSecure2026!"}).encode(),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as res:
            data = json.loads(res.read().decode())
            token = data["access_token"]
            assert data["role"] == "SOC_ANALYST"
            assert data["email"] == "soc_analyst@sentinelvoice.internal"
            log(f"Analyst login successful -> Token issued (role: {data['role']}, expires_in: {data['expires_in']}s)", "PASS")
    except Exception as e:
        log(f"Analyst login failed: {e}", "FAIL")
        all_passed = False

    # Verify Current User Profile (/api/v1/auth/me)
    if token:
        try:
            req = urllib.request.Request(
                f"{BACKEND_BASE}/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            with urllib.request.urlopen(req, timeout=5) as res:
                data = json.loads(res.read().decode())
                assert data["email"] == "soc_analyst@sentinelvoice.internal"
                assert data["role"] == "SOC_ANALYST"
                log(f"Current user profile retrieved (/api/v1/auth/me) -> {data['full_name']} ({data['role']})", "PASS")
        except Exception as e:
            log(f"Current user profile failed: {e}", "FAIL")
            all_passed = False

    # Dashboard Telemetry (/api/v1/dashboard/stats)
    try:
        req = urllib.request.Request(f"{BACKEND_BASE}/api/v1/dashboard/stats")
        with urllib.request.urlopen(req, timeout=5) as res:
            data = json.loads(res.read().decode())
            assert "total_calls_analyzed" in data
            assert "high_risk_calls" in data
            assert "recent_incidents" in data
            log(f"Dashboard telemetry verified (Total calls: {data['total_calls_analyzed']}, High risk: {data['high_risk_calls']}, Recent incidents: {len(data['recent_incidents'])})", "PASS")
    except Exception as e:
        log(f"Dashboard stats failed: {e}", "FAIL")
        all_passed = False

    # Real-Time Transcript Analysis (/api/v1/analyses/transcript)
    analysis_id = None
    try:
        sample_transcript = "URGENT: This is Inspector Verma from Crime Branch. Your bank account is flagged for illegal terror funding. Share your SBI netbanking OTP immediately or police will seize your property."
        auth_header = {"Authorization": f"Bearer {token}"} if token else {}
        req = urllib.request.Request(
            f"{BACKEND_BASE}/api/v1/analyses/transcript",
            data=json.dumps({"transcript": sample_transcript, "caller_claimed_identity": "Police Inspector Verma"}).encode(),
            headers={"Content-Type": "application/json", **auth_header}
        )
        with urllib.request.urlopen(req, timeout=5) as res:
            data = json.loads(res.read().decode())
            analysis_id = data.get("analysis_id")
            risk_score = data["risk"]["score"]
            policy_decision = data["risk"]["decision"]
            assert risk_score >= 80, f"Expected risk score >= 80, got {risk_score}"
            assert data["risk"]["level"] in ("HIGH", "CRITICAL")
            assert policy_decision in ("BLOCK_CALL", "ANALYST_REVIEW", "CHALLENGE")
            log(f"Transcript threat analysis succeeded -> Risk Score: {risk_score}/100, Decision: {policy_decision}, Signals: {len(data['fraud_signals'])}, Incident: {data.get('incident_id')}", "PASS")
    except Exception as e:
        log(f"Transcript analysis failed: {e}", "FAIL")
        all_passed = False

    # Incident Management & Analyst Override
    try:
        req = urllib.request.Request(f"{BACKEND_BASE}/api/v1/incidents?page=1&page_size=5")
        with urllib.request.urlopen(req, timeout=5) as res:
            data = json.loads(res.read().decode())
            items = data.get("items", [])
            log(f"Incidents list retrieved -> {len(items)} items found (total in DB: {data.get('total')})", "PASS")
            if items and token:
                first_inc = items[0]
                inc_id = first_inc["id"]
                # Test analyst override
                override_req = urllib.request.Request(
                    f"{BACKEND_BASE}/api/v1/incidents/{inc_id}/override",
                    data=json.dumps({
                        "new_decision": "BLOCK_CALL",
                        "reason": "SOC forensic verification confirmed extortion intent and fraudulent impersonation."
                    }).encode(),
                    headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
                )
                with urllib.request.urlopen(override_req, timeout=5) as override_res:
                    override_data = json.loads(override_res.read().decode())
                    assert override_data["analyst_override_decision"] == "BLOCK_CALL"
                    assert "forensic verification" in override_data["analyst_override_reason"]
                    log(f"Analyst override applied to incident {inc_id[:8]} -> Overridden to {override_data['analyst_override_decision']}", "PASS")
    except Exception as e:
        log(f"Incident workflow failed: {e}", "FAIL")
        all_passed = False

    # Speaker Biometrics (/api/v1/speakers)
    try:
        req = urllib.request.Request(f"{BACKEND_BASE}/api/v1/speakers")
        with urllib.request.urlopen(req, timeout=5) as res:
            data = json.loads(res.read().decode())
            assert isinstance(data, list)
            log(f"Speaker profiles retrieved -> {len(data)} profiles enrolled", "PASS")
    except Exception as e:
        log(f"Speaker profiles failed: {e}", "FAIL")
        all_passed = False

    # Demo Scenarios Sandbox (/api/v1/demo/scenarios)
    try:
        req = urllib.request.Request(f"{BACKEND_BASE}/api/v1/demo/scenarios")
        with urllib.request.urlopen(req, timeout=5) as res:
            data = json.loads(res.read().decode())
            assert len(data) >= 4
            log(f"Demo scenarios loaded -> {len(data)} realistic fraud scenarios ready for evaluation", "PASS")
    except Exception as e:
        log(f"Demo scenarios failed: {e}", "FAIL")
        all_passed = False

    return all_passed

if __name__ == "__main__":
    fe_ok = test_frontend_routes()
    be_ok = test_api_contracts_and_auth()
    if fe_ok and be_ok:
        print("\n=======================================================")
        print("ALL END-TO-END VERIFICATION PASSES COMPLETED: 100% PASS")
        print("=======================================================\n")
        sys.exit(0)
    else:
        print("\n=======================================================")
        print("VERIFICATION DETECTED FAILURES - INSPECT LOGS ABOVE")
        print("=======================================================\n")
        sys.exit(1)
