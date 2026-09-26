from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.schemas.fraud import FraudSignal
from app.schemas.speaker import SpeakerVerificationResult
from app.schemas.risk import VoiceAuthenticityResult


class PolicyDecision(BaseModel):
    decision: str = Field(..., description="ALLOW, STEP_UP_REQUIRED, ANALYST_REVIEW, BLOCK_CALL, or ESCALATE")
    risk_score: int
    confidence: float
    policy_id: str
    policy_version: str
    reason_codes: List[str]
    contributing_signals: List[str]
    actions_required: List[str]


class PolicyEngineService:
    """
    Decoupled Policy & Enforcement Decision Engine.
    Separates statistical ML risk scoring from organizational security policies.
    Guarantees reproducible, deterministic policy decisions based on signal inputs.
    """

    DEFAULT_POLICY_ID = "POL-ENTERPRISE-DEFENSE-V1"
    DEFAULT_POLICY_VERSION = "1.2.0"

    @classmethod
    def evaluate_policy(
        cls,
        risk_score: int,
        confidence: float,
        fraud_signals: List[FraudSignal],
        voice_auth: VoiceAuthenticityResult,
        speaker_verif: SpeakerVerificationResult,
        policy_config: Optional[Dict[str, Any]] = None
    ) -> PolicyDecision:
        """
        Evaluates risk score and signal constellation against configured policy thresholds.
        """
        cfg = policy_config or {}
        min_block = cfg.get("min_score_block", 85)
        min_review = cfg.get("min_score_review", 65)
        min_step_up = cfg.get("min_score_step_up", 40)

        reason_codes: List[str] = []
        actions: List[str] = []
        signal_types = [s.signal_type for s in fraud_signals]

        # Rule 1: Immediate Block conditions
        is_critical_otp_theft = "OTP_REQUEST" in signal_types and (
            voice_auth.classification == "POSSIBLE_SPOOF" or speaker_verif.result == "MISMATCH"
        )
        is_digital_arrest_extortion = "POLICE_IMPERSONATION" in signal_types and "ACCOUNT_BLOCK_THREAT" in signal_types

        if risk_score >= min_block or is_critical_otp_theft or is_digital_arrest_extortion:
            decision = "BLOCK_CALL"
            if is_critical_otp_theft:
                reason_codes.append("CRITICAL_SYNTHETIC_OR_IMPERSONATED_OTP_THEFT")
            if is_digital_arrest_extortion:
                reason_codes.append("DIGITAL_ARREST_COERCION_ATTEMPT")
            if risk_score >= min_block:
                reason_codes.append("AGGREGATE_RISK_EXCEEDS_BLOCK_THRESHOLD")

            actions.append("TERMINATE CALL OR DISCONNECT CALLER IMMEDIATELY")
            actions.append("DO NOT DISCLOSE ONE-TIME PASSWORDS OR PAYMENT DETAILS")
            actions.append("FLAG CALLER PHONE IN TELEPHONY DENYLIST")
            actions.append("DISPATCH SOC AUTOMATED INCIDENT REPORT")

        # Rule 2: Analyst Review conditions
        elif risk_score >= min_review or speaker_verif.result == "MISMATCH" or "BANK_IMPERSONATION" in signal_types:
            decision = "ANALYST_REVIEW"
            if speaker_verif.result == "MISMATCH":
                reason_codes.append("SPEAKER_BIOMETRIC_PROFILE_MISMATCH")
            if "BANK_IMPERSONATION" in signal_types:
                reason_codes.append("UNVERIFIED_FINANCIAL_INSTITUTION_REPRESENTATIVE")
            if risk_score >= min_review:
                reason_codes.append("AGGREGATE_RISK_EXCEEDS_REVIEW_THRESHOLD")

            actions.append("HOLD TRANSACTION PENDING MANUAL SOC OPERATOR INSPECTION")
            actions.append("OUT-OF-BAND CONTACT VIA CUSTOMER REGISTERED PHONE")

        # Rule 3: Step-up Verification conditions
        elif risk_score >= min_step_up or "SUSPICIOUS_PAYMENT_REQUEST" in signal_types or voice_auth.classification == "SUSPICIOUS":
            decision = "STEP_UP_REQUIRED"
            if "SUSPICIOUS_PAYMENT_REQUEST" in signal_types:
                reason_codes.append("EXTERNAL_PAYMENT_TRANSFER_REQUESTED")
            if voice_auth.classification == "SUSPICIOUS":
                reason_codes.append("ELEVATED_ACOUSTIC_SPECTRAL_VARIANCE")
            if risk_score >= min_step_up:
                reason_codes.append("ELEVATED_INTERACTION_RISK_SCORE")

            actions.append("REQUEST OUT-OF-BAND MULTI-FACTOR AUTHENTICATION (PUSH / IN-APP)")
            actions.append("CHALLENGE CALLER WITH MUTUAL AUTHENTICATION SECRET")

        # Rule 4: Allow / Routine Monitoring
        else:
            decision = "ALLOW"
            reason_codes.append("RISK_WITHIN_TOLERABLE_BOUNDS")
            actions.append("CONTINUE ROUTINE CALL SURVEILLANCE")

        return PolicyDecision(
            decision=decision,
            risk_score=risk_score,
            confidence=confidence,
            policy_id=cfg.get("policy_id", cls.DEFAULT_POLICY_ID),
            policy_version=cfg.get("policy_version", cls.DEFAULT_POLICY_VERSION),
            reason_codes=reason_codes,
            contributing_signals=signal_types,
            actions_required=actions
        )
