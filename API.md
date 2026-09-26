# SentinelVoice — REST & WebSocket API Specification

> Base URLs:
> - Production: `https://api.sentinelvoice.internal/api/v1`
> - Local Development: `http://localhost:8000/api/v1`

---

## 1. Authentication

SentinelVoice uses standard Bearer JWT authentication:
```http
Authorization: Bearer <JWT_TOKEN>
```

### `POST /api/v1/auth/login`
Authenticates a SOC analyst or administrator.
- **Request**:
  ```json
  {
    "email": "analyst@sentinelvoice.internal",
    "password": "SentinelAnalyst2026!"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "expires_in": 86400,
    "user": {
      "id": "user-default-analyst",
      "email": "analyst@sentinelvoice.internal",
      "full_name": "SOC Lead Analyst",
      "role": "ADMIN",
      "organization_id": "org-default-01"
    }
  }
  ```

---

## 2. Health & Readiness Probes

### `GET /health/live`
Kubernetes liveness probe. Returns `{"status": "LIVE"}`.

### `GET /health/ready`
Kubernetes readiness probe. Verifies database connectivity. Returns `{"status": "READY", "database": "CONNECTED"}`.

### `GET /api/v1/health`
Detailed operational telemetry and configuration status.

---

## 3. Telephony Threat Analysis

### `POST /api/v1/analyses/audio`
Uploads a telephony audio recording for multi-modal analysis (Audio DSP, Anti-Spoofing, Biometric Verification, STT, and Fraud Intent).
- **Content-Type**: `multipart/form-data`
- **Fields**:
  - `audio_file`: Audio recording file (WAV, MP3, OGG, M4A, FLAC; max 25MB)
  - `transcript` *(optional)*: Transcript text (if omitted, Speech-to-Text executes)
  - `caller_claimed` *(optional)*: Claimed authority / identity
  - `reference_audio` *(optional)*: Enrolled speaker reference sample
- **Response (200 OK)**: Full `FinalAnalysisResponse` JSON schema.

### `POST /api/v1/analyses/transcript`
Evaluates a conversational transcript for multilingual social engineering signals.
- **Request**:
  ```json
  {
    "transcript": "Hello Rajesh from HDFC Bank. Send 6-digit OTP now or account will be blocked.",
    "caller_claimed_identity": "HDFC Bank Security Desk"
  }
  ```

### `GET /api/v1/analyses/{analysis_id}`
Retrieves a persisted analysis record by its unique ID. Returns 404 if not found.

---

## 4. SOC Incident Management

### `GET /api/v1/incidents`
Lists security incidents with pagination and filtering.
- **Query Parameters**:
  - `status`: `OPEN | INVESTIGATING | CONFIRMED_FRAUD | RESOLVED | FALSE_POSITIVE`
  - `severity`: `CRITICAL | HIGH | MEDIUM | LOW`
  - `page`: default 1
  - `page_size`: default 50

### `GET /api/v1/incidents/{incident_id}`
Retrieves complete incident forensic dossier, including chronological event timeline, derived evidence items, and analyst investigation notes.

### `PATCH /api/v1/incidents/{incident_id}/status`
Updates incident status and assignee.

### `POST /api/v1/incidents/{incident_id}/notes`
Appends an investigation note to the incident timeline.

### `POST /api/v1/incidents/{incident_id}/override`
Executes an auditable policy decision override.
- **Request**:
  ```json
  {
    "new_decision": "ALLOW",
    "reason": "Caller verified via physical hardware token. Narrowband GSM noise caused false spoof elevation."
  }
  ```

---

## 5. Biometric Speaker Verification

### `GET /api/v1/speakers`
Lists all enrolled representative profiles scoped to the user's organization.

### `POST /api/v1/speakers`
Registers a new speaker profile with explicit biometric consent.

### `POST /api/v1/speakers/{profile_id}/enroll`
Uploads reference audio to extract and enroll a 128-dimensional vocal tract baseline.

### `POST /api/v1/verify/speaker`
Executes 1:1 cosine similarity verification between test caller audio and an enrolled profile.

---

## 6. Real-Time WebSocket Streaming

### `WebSocket /api/v1/stream/{sessionId}`
Bidirectional real-time telephony streaming channel:
- **Client → Server**: Audio chunks (binary PCM / WAV frames) or JSON control messages.
- **Server → Client**: Live streaming events:
  - `SESSION_STARTED`
  - `AUDIO_RECEIVED`
  - `AUDIO_QUALITY_UPDATED`
  - `TRANSCRIPT_PARTIAL`
  - `TRANSCRIPT_FINAL`
  - `SPOOF_SCORE_UPDATED`
  - `SPEAKER_SCORE_UPDATED`
  - `FRAUD_SIGNAL_DETECTED`
  - `RISK_UPDATED`
  - `POLICY_EVALUATED`
