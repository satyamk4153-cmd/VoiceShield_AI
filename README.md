# 🛡️ SentinelVoice — Enterprise AI Telephony Fraud & Deepfake Detection Platform

> **«Don't Just Detect a Fake Voice. Detect the Fraud.»**  
> *Core Mandate: "Is this phone interaction dangerous?" — not merely "Is this voice synthetic?"*

[![License: MIT](https://img.shields.io/badge/License-MIT-indigo.svg)](LICENSE)
[![Backend: FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Frontend: Next.js 14](https://img.shields.io/badge/Frontend-Next.js%2014-black.svg)](https://nextjs.org/)
[![Database: PostgreSQL + Alembic](https://img.shields.io/badge/Database-PostgreSQL%20%2B%20Alembic-336791.svg)](DEPLOYMENT.md)
[![Cloud Target: Microsoft Azure](https://img.shields.io/badge/Target-Microsoft%20Azure-0078D4.svg)](DEPLOYMENT.md)
[![Tests: 29 Passing](https://img.shields.io/badge/Tests-29%20Passed-brightgreen.svg)](tests/)

---

## 📖 1. Problem & Threat Landscape

With the proliferation of zero-shot neural voice cloning and generative AI, telephone scams have grown exponentially. Scammers clone voices of family members, bank representatives, or law enforcement officers to execute high-value fraud.

### Why Detecting Only Synthetic Voices Fails
1. **Real Voices in Social Engineering**: Traditional human scammers frequently conduct devastating scams without using deepfakes (e.g. OTP theft, digital arrest extortion). Pure deepfake detectors flag these calls as "authentic".
2. **Telephony Audio Degradation**: Standard 8kHz PSTN/GSM telephony lines compress audio and introduce phase artifacts, causing classical acoustic models to issue false positive spoof alerts on legitimate phone calls.

---

## 🚀 2. The SentinelVoice Solution & Architecture

SentinelVoice fuses multi-modal signals into an explainable, calibrated risk score (0–100) governed by a deterministic Policy Engine:

```
TELEPHONY AUDIO STREAM
            ↓
 1. AUDIO QUALITY & VAD (True SNR dB, RMS, clipping, 8kHz PSTN detection)
            ↓
 2. VOICE ANTI-SPOOFING (Neural vocoder phase & spectral flatness anomalies)
            ↓
 3. 1:1 SPEAKER VERIFICATION (128-D acoustic filterbank vs. consented baseline)
            ↓
 4. SPEECH-TO-TEXT & PII REDACTION (Azure Speech / Local STT + multilingual tokenization)
            ↓
 5. FRAUD INTENT DETECTION (OTP theft, impersonation, coercive threats in EN/HI/Hinglish)
            ↓
 6. CONTEXTUAL BEHAVIORAL SIGNALS (Urgency, secrecy, financial pressure)
            ↓
 7. MULTI-MODAL CALIBRATED RISK FUSION MATRIX
            ↓
 8. DETERMINISTIC POLICY ENGINE (ALLOW | STEP_UP_REQUIRED | ANALYST_REVIEW | BLOCK_CALL)
            ↓
 9. SOC INCIDENT MANAGEMENT & AUDIT LOGGING
```

---

## 📚 3. Complete Technical Documentation

- **[System Architecture](ARCHITECTURE.md)**: Deep dive into subsystem boundaries, pipeline flow, and state machines.
- **[Security Policy & Controls](SECURITY.md)**: RBAC, tenant isolation, prompt injection defense, and input validation.
- **[Privacy & Responsible AI](PRIVACY.md)**: Zero raw audio retention, PII tokenization, and biometric consent lifecycle.
- **[STRIDE Threat Model](THREAT_MODEL.md)**: Threat actors, attack vectors, mitigations, and boundary analysis.
- **[Deployment & Cloud Runbook](DEPLOYMENT.md)**: Docker Compose, PostgreSQL migrations, and Azure Enterprise setup.
- **[AI/ML Evaluation & Benchmarks](MODEL_EVALUATION.md)**: ASVspoof benchmarks, acoustic phase analysis, and telephony calibration.
- **[REST & WebSocket API Guide](API.md)**: Complete API v1 schema and WebSocket streaming protocol.

---

## 🛠️ 4. Technology Stack

- **Frontend**: Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, Framer Motion, Lucide React, Recharts.
- **Backend Engine**: Python 3.11/3.12, FastAPI, Pydantic v2, SQLAlchemy ORM, Alembic migrations.
- **Database & Cache**: PostgreSQL 15+ (Production requirement), Redis 7+ (Session streaming & rate limiting).
- **Audio DSP & AI Models**: NumPy, SciPy, Waveform filterbanks, Phase variance analysis, Spectral flatness, 128-D acoustic embeddings.
- **Cloud Integrations**: Microsoft Azure (Azure Container Apps, Azure OpenAI GPT-4o with strict JSON schema, Azure AI Speech, Key Vault).

---

## 📂 5. Project Directory Structure

```
sentinelvoice/
├── ARCHITECTURE.md            # System architecture & pipeline specifications
├── SECURITY.md                # Security policy, RBAC & defensive controls
├── PRIVACY.md                 # Zero raw audio retention & PII redaction rules
├── THREAT_MODEL.md            # STRIDE threat model & boundary analysis
├── DEPLOYMENT.md              # Deployment guide, Alembic & Azure architecture
├── MODEL_EVALUATION.md        # AI/ML evaluation metrics & benchmarks
├── API.md                     # Complete REST & WebSocket API specification
├── docker-compose.yml         # Hardened multi-container orchestration (Postgres, Redis, API, UI)
│
├── backend/
│   ├── Dockerfile             # Hardened slim container with non-root user & healthchecks
│   ├── requirements.txt       # Deterministic Python dependencies
│   ├── alembic/               # Relational database migration scripts
│   ├── .env.production.example# Fail-fast production environment template
│   └── app/
│       ├── main.py            # FastAPI entrypoint with security middleware & health probes
│       ├── api/               # Versioned API routes (/api/v1/*) & deps
│       ├── core/              # Config validation, logging, security & ephemeral files
│       ├── schemas/           # Strict Pydantic schemas (Risk, Audio, Speaker, Fraud, Incident)
│       ├── services/          # Decoupled domain engines (AntiSpoof, Speaker, Fraud, Risk, Policy)
│       ├── providers/         # Real Azure OpenAI, Azure Speech, Local STT & Demo Sandbox
│       ├── db/                # PostgreSQL models and relational repositories
│       └── utils/             # Audio DSP waveform utilities & multilingual PII masking
│
├── frontend/
│   ├── Dockerfile             # Multi-stage standalone runner with non-root user
│   ├── package.json
│   ├── app/                   # Next.js App Router (/live, /analyze, /result, /evidence, /speaker, /dashboard, /demo)
│   ├── components/            # Professional SOC components (Navbar, RiskScore, EvidenceTimeline)
│   └── lib/                   # Typed API client & data interfaces
│
└── tests/
    ├── conftest.py            # Shared database & session test fixtures
    ├── test_health.py         # System health & operational checks
    ├── test_audio.py          # Audio validation & waveform parsing
    ├── test_fraud.py          # Multilingual semantic intent tests
    ├── test_speaker.py        # 1:1 Biometric speaker comparison tests
    ├── test_risk.py           # Multi-modal risk fusion verification
    ├── test_demo.py           # Synthetic scenario suite validation
    ├── test_production_hardening.py # PII, policy engine, JWT, and model checks
    └── test_security_hardening.py   # STRIDE security, corrupt audio, tenant isolation & prompt injection
```

---

## ⚡ 6. Quick Start & Execution

### Running via Docker Compose (PostgreSQL, Redis, Backend, Frontend)
```bash
docker-compose up --build -d
```
- **Frontend SOC Console**: `http://localhost:3000`
- **Backend API & OpenAPI Docs**: `http://localhost:8000/docs`
- **Health Readiness Probe**: `http://localhost:8000/health/ready`

### Running Backend Locally
```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate | Linux: source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Running Frontend Locally
```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 7. Automated Test Suite

SentinelVoice includes a rigorous test suite of unit, integration, and security tests:

```bash
python -m pytest tests/ -v
```

All 29 tests execute across:
- ✅ Health liveness and database readiness probes
- ✅ Audio file validation, MIME check, and corrupt audio rejection (400/415)
- ✅ Path traversal prevention during file uploads
- ✅ Multilingual fraud intent detection (English, Hindi, Hinglish)
- ✅ 1:1 Biometric speaker verification and cosine distance thresholding
- ✅ Multi-modal non-linear calibrated risk scoring (Exact 94/100 Bank OTP test)
- ✅ PII redaction across OTPs, cards, PAN, and Aadhaar identifiers
- ✅ Policy engine deterministic enforcement (`ALLOW`, `STEP_UP_REQUIRED`, `BLOCK_CALL`)
- ✅ Cryptographic JWT creation, verification, and signature forgery rejection (401)
- ✅ Full SOC incident lifecycle (Creation, timeline events, evidence items, notes, status update)
- ✅ Multi-tenant isolation boundary enforcement (Cross-tenant query rejection)
- ✅ LLM prompt injection defense with defensive XML encapsulation (`<TRANSCRIPT_DATA>`)

---

## 🔒 8. Responsible AI & Operational Ethics

1. **Zero Raw Audio Retention**: Temporary audio files reside in ephemeral volatile memory only during feature extraction and are wiped immediately via secure system primitives. No raw caller audio is stored permanently.
2. **Deterministic Policy Enforcement**: AI models generate calibrated risk signals and intent classifications; they never execute uncontrolled or irreversible actions directly. The deterministic Policy Engine governs access control.
3. **1:1 Biometric Authentication Only**: SentinelVoice strictly evaluates 1:1 similarity against consented authorized profiles and never performs unconsented open-world surveillance.
4. **"Risk Signals, Not Absolute Truth"**: SentinelVoice provides probabilistic risk indices to empower human operators, fraud investigators, and bank security desks.
