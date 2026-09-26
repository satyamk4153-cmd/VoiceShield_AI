# SentinelVoice — Responsible AI Principles & Limitations

## 1. Core Principles

### "Risk Signals, Not Absolute Truth"
SentinelVoice generates probabilistic risk indices to empower human operators, bank security desks, and end-users. No AI system can guarantee 100% detection of zero-day synthetic audio or social engineering techniques.

### Explainability Over Black-Box Verdicts
Every risk score (e.g. 94/100 HIGH) is accompanied by a granular breakdown of contributing factors (e.g., +28% OTP demand, +22% Impersonation claim, +18% Speaker mismatch, +16% Acoustic anomaly, +10% Coercive urgency).

### Biometric Distinction
Speaker verification in SentinelVoice evaluates **1:1 similarity** against an explicitly authorized reference sample. It does **not** conduct 1:N open-set facial/voice identification or unconsented surveillance.

---

## 2. Limitations & Failure Modes

1. **Acoustic Noise in Telephony**: Standard 8kHz GSM/PSTN audio compresses high-frequency harmonics, creating natural artifacts that can mimic voice synthesis. SentinelVoice explicitly incorporates audio quality scoring to prevent false spoof alerts on poor phone lines.
2. **Consent & Regulatory Compliance**: Live recording analysis requires two-party or one-party consent in accordance with regional telecommunication laws.
3. **Demo Provider Transparency**: When running in offline Demo mode (`AI_PROVIDER=demo`), results are deterministically generated from synthetic reference scenarios and clearly labeled with `[SYNTHETIC DEMO DATA]`.
