from typing import List, Dict, Tuple, Optional, Any
from app.schemas.audio import AudioQualityResult
from app.schemas.speaker import SpeakerVerificationResult
from app.schemas.risk import VoiceAuthenticityResult, RiskAssessment, EvidenceItem
from app.schemas.fraud import FraudSignal, ContextualSignal
from app.services.contextual_engine import ContextualEngineService
from app.services.policy_engine import PolicyEngineService, PolicyDecision


class RiskEngineService:
    @staticmethod
    def fuse_risk_assessment(
        fraud_signals: List[FraudSignal],
        contextual_signals: List[ContextualSignal],
        voice_auth: VoiceAuthenticityResult,
        speaker_verif: SpeakerVerificationResult,
        audio_quality: AudioQualityResult,
        policy_config: Optional[Dict[str, Any]] = None
    ) -> Tuple[RiskAssessment, List[EvidenceItem], List[str]]:
        """
        Multi-Modal Calibrated Risk Fusion Engine.
        Synthesizes Acoustic Spoofing + Biometric Speaker Verification + Semantic Intent + Telephony Degradation.
        Delegates final enforcement decisions to PolicyEngineService.
        """
        breakdown: Dict[str, int] = {}
        evidence: List[EvidenceItem] = []
        
        # 1. Semantic Fraud Intent & Impersonation Points
        for sig in fraud_signals:
            breakdown[sig.signal_type] = sig.risk_contribution
            evidence.append(EvidenceItem(
                id=sig.id,
                timestamp=sig.timestamp or "00:04",
                title=f"{sig.signal_type.replace('_', ' ').title()} Detected",
                category=sig.category,
                severity=sig.severity,
                explanation=sig.description,
                contribution_points=sig.risk_contribution
            ))

        # 2. Contextual Psychological Pressure Points
        context_pts = ContextualEngineService.evaluate_context(fraud_signals, contextual_signals)
        if context_pts > 0:
            breakdown["CONTEXTUAL_PRESSURE"] = context_pts
            evidence.append(EvidenceItem(
                id="EVI-CTX-01",
                timestamp="00:05",
                title="Psychological Pressure Tactics",
                category="CONTEXTUAL",
                severity="MEDIUM" if context_pts < 10 else "HIGH",
                explanation=f"High urgency and conversational intimidation detected (Risk Weight: +{context_pts} pts).",
                contribution_points=context_pts
            ))

        # 3. Speaker Verification Contribution
        if speaker_verif.result == "MISMATCH":
            speaker_pts = 14
            breakdown["SPEAKER_MISMATCH"] = speaker_pts
            evidence.append(EvidenceItem(
                id="EVI-SPK-01",
                timestamp="00:08",
                title="Speaker Identity Mismatch",
                category="BIOMETRIC",
                severity="HIGH",
                explanation=f"Acoustic vocal characteristics do not match claimed legitimate organization baseline (Similarity: {speaker_verif.similarity}).",
                contribution_points=speaker_pts
            ))
        elif speaker_verif.result == "MATCH":
            breakdown["SPEAKER_MATCH_DISCOUNT"] = -15
            evidence.append(EvidenceItem(
                id="EVI-SPK-02",
                timestamp="00:08",
                title="Speaker Identity Authenticated",
                category="BIOMETRIC",
                severity="LOW",
                explanation=f"Acoustic vocal tract resonance aligns with enrolled authorized profile (Similarity: {speaker_verif.similarity}).",
                contribution_points=-15
            ))

        # 4. Voice Anti-Spoofing Contribution
        if voice_auth.classification == "POSSIBLE_SPOOF":
            # Calibrated based on telephony condition
            spoof_pts = 10 if audio_quality.telephony_condition == "DEGRADED" else 12
            breakdown["VOICE_SPOOF_ARTIFACTS"] = spoof_pts
            evidence.append(EvidenceItem(
                id="EVI-SPF-02",
                timestamp="00:10",
                title="Synthetic Voice Spoof Detected",
                category="SYNTHETIC_AUDIO",
                severity="HIGH",
                explanation=f"Phase continuity and spectral vocoder synthesis artifacts identified (Spoof Probability: {voice_auth.spoof_probability}).",
                contribution_points=spoof_pts
            ))
        elif voice_auth.classification == "SUSPICIOUS":
            breakdown["VOICE_SPOOF_ARTIFACTS"] = 6
            evidence.append(EvidenceItem(
                id="EVI-SPF-03",
                timestamp="00:10",
                title="Anomalous Voice Acoustics",
                category="SYNTHETIC_AUDIO",
                severity="MEDIUM",
                explanation="Acoustic features display elevated spectral variance.",
                contribution_points=6
            ))

        # 5. Composite Risk Score (Bounded 0-100)
        total_raw = sum(breakdown.values())
        final_score = max(0, min(100, total_raw))

        # 6. Overall Confidence Calculation based on input quality
        input_confidences = [s.confidence for s in fraud_signals] if fraud_signals else [0.9]
        if voice_auth.status == "OK":
            input_confidences.append(voice_auth.confidence)
        if speaker_verif.status == "OK":
            input_confidences.append(speaker_verif.confidence)
        
        overall_confidence = round(float(sum(input_confidences) / len(input_confidences)), 2)

        # 7. Determine Risk Level
        if final_score >= 90:
            risk_level = "CRITICAL"
        elif final_score >= 70:
            risk_level = "HIGH"
        elif final_score >= 40:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # 8. Evaluate Policy via Policy Engine
        policy_decision: PolicyDecision = PolicyEngineService.evaluate_policy(
            risk_score=final_score,
            confidence=overall_confidence,
            fraud_signals=fraud_signals,
            voice_auth=voice_auth,
            speaker_verif=speaker_verif,
            policy_config=policy_config
        )

        # Sort evidence by timestamp
        evidence.sort(key=lambda e: e.timestamp)

        assessment = RiskAssessment(
            score=final_score,
            level=risk_level,
            decision=policy_decision.decision,
            confidence=overall_confidence,
            risk_breakdown=breakdown,
            policy_id=policy_decision.policy_id,
            policy_version=policy_decision.policy_version,
            reason_codes=policy_decision.reason_codes
        )

        return assessment, evidence, policy_decision.actions_required
