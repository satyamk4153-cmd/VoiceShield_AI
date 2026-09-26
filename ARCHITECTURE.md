# SentinelVoice — Production System Architecture

> Canonical Name: **SentinelVoice**  
> Operational Directive: Telephony Voice Authenticity, Biometric Verification, and Multi-Modal Fraud Prevention.

---

## 1. Logical Architecture

The platform separates detection, verification, risk calculation, policy enforcement, investigation, and audit into clear boundaries:

```
CLIENT / TELEPHONY / AUDIO STREAM
        ↓
SECURE INGESTION & DECODER ISOLATION
  (MIME check, magic bytes [RIFF/ID3/OggS/fLaC], 25MB limit, ephemeral disk cleanup)
        ↓
AUDIO QUALITY & VAD (DSP ENGINE)
  (RMS, speech ratio VAD, True SNR dB, clipping ratio, 8kHz PSTN degradation detection)
        ↓
VOICE ANTI-SPOOF / DEEPFAKE MODEL
  (VoiceAntiSpoofModel: Spectral flatness, phase variance, vocoder artifacts)
        ↓
1:1 BIOMETRIC SPEAKER VERIFICATION
  (SpeakerVerificationService: 128-D acoustic filterbank embedding, cosine similarity)
        ↓
SPEECH-TO-TEXT & PII REDACTION
  (Azure Speech / Local STT + multilingual PII tokenization [OTP, PAN, Aadhaar, Cards])
        ↓
MULTILINGUAL FRAUD INTENT CLASSIFICATION
  (FraudDetectorService: English, Hindi, Hinglish semantic intent & pressure analysis)
        ↓
CONTEXTUAL BEHAVIORAL SIGNALS
  (Urgency, secrecy demands, financial ultimatum, authority impersonation)
        ↓
CALIBRATED MULTI-MODAL RISK FUSION
  (Non-linear calibrated risk scoring with telephony degradation compensation)
        ↓
DETERMINISTIC POLICY ENGINE
  (Rule-based evaluation: ALLOW | STEP_UP_REQUIRED | ANALYST_REVIEW | BLOCK_CALL)
        ↓
INCIDENT WORKFLOW & SOC CONSOLE
  (Incident creation, chronological timeline, derived evidence, analyst overrides, notes)
        ↓
IMMUTABLE AUDIT LOGGING & TELEMETRY
  (AuditLog repository, redacted structured JSON logging, Prometheus/Promtail ready)
```

---

## 2. Decoupled Subsystems

| Layer | Responsibility | Status |
|---|---|---|
| **1. Audio DSP** | Decodes WAV/MP3/OGG/FLAC, calculates SNR in dB, RMS, clipping, VAD speech percentage, and detects degraded PSTN telephony profiles. | **IMPLEMENTED** |
| **2. Anti-Spoof Detection** | Genuine `VoiceAntiSpoofModel` analyzing spectral boundary discontinuities, phase variance, and vocoder artifacts. Exposes `health()`, `predict()`, and `metadata()`. | **IMPLEMENTED** |
| **3. 1:1 Speaker Verification** | Compares caller audio strictly against consented database-enrolled acoustic profiles via 128-dimensional vocal tract embeddings. Zero open-set biometric surveillance. | **IMPLEMENTED** |
| **4. Speech-to-Text** | Azure Speech provider + local fallback. Zero fake transcripts in production path. | **IMPLEMENTED** |
| **5. Privacy & PII Pipeline** | Redacts and masks credit cards, bank accounts, Aadhaar, PAN, emails, and OTPs prior to LLM or persistence. | **IMPLEMENTED** |
| **6. Fraud Classifier** | Identifies 20+ fraud types in English, Hindi, and Hinglish. Supports Azure OpenAI GPT-4o with strict structured schemas and prompt injection protection (`<TRANSCRIPT_DATA>`). | **IMPLEMENTED** |
| **7. Risk Engine** | Non-linear multi-modal calibrated risk fusion. Combines acoustic spoof, biometric similarity, fraud intent, and behavioral coercion. | **IMPLEMENTED** |
| **8. Policy Engine** | Decoupled deterministic rule engine. Business policy is separated from AI models. Enforces `ALLOW`, `STEP_UP_REQUIRED`, `ANALYST_REVIEW`, `BLOCK_CALL`. | **IMPLEMENTED** |
| **9. Incident Management** | Full SOC lifecycle: Incident creation, chronological event timelines, derived evidence items, analyst notes, and auditable decision overrides. | **IMPLEMENTED** |
| **10. Persistence & Multi-Tenancy** | PostgreSQL with Alembic migrations. Tenant-scoped database queries (`organization_id`). Fail-fast startup in production mode. | **IMPLEMENTED** |
| **11. Streaming Transport** | WebSocket session manager (`/api/v1/stream/{sessionId}`) handling chunked audio, incremental partial transcripts, live spoof updates, and live policy decisions. | **IMPLEMENTED** |
| **12. Telephony Connectors** | Abstract telephony adapter interface designed for SIP trunking and Azure Communication Services. | **PARTIALLY IMPLEMENTED (Interface & Mock Provider; Direct SIP hardware gateway is FUTURE)** |

---

## 3. Threat Intelligence Decision Hierarchy

Final enforcement decisions are governed by the Policy Engine, not directly by AI models:
- **LOW RISK (< 40)**: `ALLOW` — Interaction proceeds with background monitoring.
- **MEDIUM RISK (40–69)**: `STEP_UP_REQUIRED` — Interaction requires secondary out-of-band verification (e.g. mobile push notification, banking app challenge).
- **HIGH RISK (70–89)**: `ANALYST_REVIEW` — Immediate SOC escalation; transaction hold.
- **CRITICAL THREAT (≥ 90 or High-Risk Combination)**: `BLOCK_CALL` — Immediate termination of telephony session or automated financial lockout.
