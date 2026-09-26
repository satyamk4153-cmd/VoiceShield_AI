# SentinelVoice — Architecture Overview

SentinelVoice is an enterprise-grade AI Fraud Detection Platform engineered to answer the critical question:
> **"Is this phone interaction dangerous?"**
> *(Not merely: "Is this voice synthetic?")*

## 1. High-Level Pipeline

```
TELEPHONY AUDIO / STREAM
           ↓
 1. AUDIO QUALITY ANALYSIS
    (RMS, SNR, clipping, telephony degradation check)
           ↓
 2. VOICE ANTI-SPOOFING
    (Deepfake & synthetic speech probability)
           ↓
 3. SPEAKER VERIFICATION
    (Cosine similarity against claimed reference profile)
           ↓
 4. FRAUD INTENT DETECTION
    (Multi-lingual semantic classification: English, Hindi, Hinglish)
           ↓
 5. CONTEXTUAL FRAUD SIGNALS
    (Urgency, secrecy, authority impersonation, payment coercion)
           ↓
 6. RISK FUSION ENGINE
    (Non-linear weighted fusion + telephony degradation calibration)
           ↓
 7. EXPLAINABLE RISK SCORE (0–100) & DECISION
           ↓
 8. ACTIONABLE USER ADVISORY & SOC MITIGATION
```

---

## 2. Component Topology

### Local / Standard Container Deployment
```
[ User Browser / SOC Analyst ]
               │
               ▼
[ Next.js 14/15 App Router Frontend (Port 3000) ]
  ├── Tailwind CSS + Framer Motion (Cybersecurity SOC UI)
  ├── Recharts (Incident & Risk Analytics)
  └── API Client (REST & Event Streaming)
               │
               ▼
[ FastAPI Backend Engine (Port 8000) ]
  ├── API Layer (/api/health, /api/analyze/*, /api/risk/*, /api/demo/*)
  ├── Security Layer (MIME verification, upload sanitization, zero-audio retention)
  ├── Domain Services (AudioAnalyzer, AntiSpoof, SpeakerVerification, FraudDetector, RiskEngine)
  ├── Provider Layer (DemoProvider, AzureOpenAI, AzureSpeech, AzureLanguage)
  └── Persistence Layer (SQLAlchemy ORM + PostgreSQL / SQLite Fallback)
```

---

## 3. Azure Enterprise Target Architecture

```
                       [ Incoming Calls / Telephony Gateway ]
                                         │
                                         ▼
   [ Azure Static Web Apps ] ────────► [ Azure Container Apps ]
   (Next.js Front-End SOC UI)         (FastAPI AI Microservice Engine)
                                         │
                 ┌───────────────────────┼───────────────────────┐
                 ▼                       ▼                       ▼
      [ Azure AI Speech ]        [ Azure OpenAI ]       [ Azure AI Language ]
      - Real-time STT            - GPT-4o Semantic       - Entity Extraction
      - Voice Profile Features     Intent & Fraud Flow   - Conversation PII Redaction
                 │                       │                       │
                 └───────────────────────┼───────────────────────┘
                                         ▼
                           [ Azure PostgreSQL Flexible ]
                           (Metadata & Security Audit Logs)
                                         │
                                         ▼
                           [ Microsoft Fabric / Power BI ]
                           (Executive Threat Intelligence)
```

---

## 4. Multi-Layer Risk Fusion Model

SentinelVoice computes fraud probability via non-linear weighted fusion:

$$\text{RawRisk} = w_{\text{intent}} \cdot S_{\text{intent}} + w_{\text{context}} \cdot S_{\text{context}} + w_{\text{speaker}} \cdot S_{\text{speaker}} + w_{\text{spoof}} \cdot S_{\text{spoof}} + w_{\text{behavior}} \cdot S_{\text{behavior}}$$

- **Telephony Degradation Adjustment:** If audio quality is degraded, voice spoof confidence is calibrated down to prevent false positives, while conversational fraud intent weight is elevated.
- **Explainable Attribution:** Every signal returns a quantitative percentage contribution to the final risk score.
