# SentinelVoice — Privacy Architecture & Data Protection

> Canonical Product: **SentinelVoice**  
> Operational Guarantee: Privacy by Design & Zero Raw Audio Retention.

---

## 1. Core Privacy Tenets

1. **Zero Raw Audio Retention**: SentinelVoice operates on an ephemeral analysis model. Audio streams and uploaded recordings are analyzed in volatile memory or isolated ephemeral disk spaces and deleted immediately upon feature extraction. Raw voice recordings are **never permanently stored** in production by default.
2. **Derived Evidence Artifacts**: In place of raw recordings, SentinelVoice retains only derived mathematical artifacts: acoustic SNR metrics, 128-dimensional vocal tract feature vectors, tokenized transcript segments, and timestamped forensic event logs.
3. **No Biometric Surveillance**: Speaker verification is strictly constrained to **1:1 similarity matching** against explicitly consented representative profiles. SentinelVoice rejects 1:N open-set facial or voice identification.

---

## 2. PII Detection & Tokenization Pipeline

Before any transcript segment is persisted, evaluated by an LLM, or displayed in the SOC console, it passes through the `PIIRedactionService`:

```
Raw Speech Transcript
        ↓
Regex & Semantic Entity Matchers
        ├── One-Time Passwords (4-8 digit OTPs, "OTP is 482901")
        ├── Credit & Debit Card Numbers (16 digits, Luhn formatting)
        ├── Indian Aadhaar Identification (12-digit UIDAI patterns)
        ├── Permanent Account Numbers (PAN: 5 letters + 4 digits + 1 letter)
        ├── Bank Account Numbers (9-18 digit account sequences)
        ├── E-mail Addresses
        └── Phone Numbers (+91 / standard 10-digit mobile numbers)
        ↓
Tokenized Privacy-Preserving Output
  ("Your card ending in [CARD_TOKEN] was charged. Your OTP is [OTP_TOKEN]")
```

---

## 3. Biometric Governance & Consent Lifecycle

Speaker verification requires handling acoustic voiceprints, which constitute sensitive biometric information. SentinelVoice enforces:
- **Consent Recording**: `consent_recorded: boolean` and `consent_timestamp` are required attributes on `SpeakerProfile` records.
- **Configurable Retention Windows**: Profiles enforce a `retention_days` limit (default 90–365 days).
- **Cryptographic Storage**: Embedding vectors are stored as mathematical arrays (128 normalized float coefficients) rather than raw voice templates. A voice embedding cannot be reversed into the original audio.
- **Right to Erasure (Deletion APIs)**: Authorized administrators can delete speaker profiles (`DELETE /api/v1/speakers/{id}`), which triggers a cascade deletion of all enrolled acoustic vectors.

---

## 4. Compliance Readiness

| Regulation | Technical Controls Provided | Status |
|---|---|---|
| **India Digital Personal Data Protection Act (DPDP Act 2023)** | Explicit consent logging, purposeful data minimization, ephemeral audio destruction, PII tokenization for Indian identifiers (Aadhaar, PAN). | **SUPPORTED** |
| **EU General Data Protection Regulation (GDPR)** | Data minimization (Art. 5), Right to Erasure (Art. 17), Security of processing (Art. 32), Pseudonymization via tokenization. | **SUPPORTED** |
| **PCI-DSS (Payment Security)** | Automatic redaction of PANs and CVVs from telephony transcripts; raw payment credentials are never logged or stored. | **SUPPORTED** |

> *Note on Certification Claims: SentinelVoice provides the technical controls necessary to achieve compliance with DPDP, GDPR, and PCI-DSS. Formal certification requires an organization-level third-party audit of infrastructure and operations.*
