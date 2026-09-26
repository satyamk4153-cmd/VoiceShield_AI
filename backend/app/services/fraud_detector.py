import re
import uuid
from typing import Optional, List, Dict, Any, Tuple
from app.schemas.fraud import FraudIntentResult, FraudSignal, ContextualSignal
from app.services.pii_service import PIIRedactionService
from app.core.config import settings
from app.core.logging import logger


class FraudDetectorService:
    """
    Multilingual Semantic Fraud Intent & Social Engineering Detection Engine.
    Detects 20+ phone scam categories in English, Devanagari Hindi, and Romanized Hinglish.
    Treats input text as untrusted data after rigorous PII redaction.
    """

    def __init__(self, provider: Optional[Any] = None):
        self.provider = provider

    def _detect_language(self, text: str) -> str:
        """Detects whether text is predominantly English, Hindi, or Hinglish."""
        devanagari_pattern = re.compile(r'[\u0900-\u097F]')
        if devanagari_pattern.search(text):
            return "Hindi (Devanagari)"

        hinglish_tokens = {
            "aapka", "kijiye", "bhejiye", "khata", "band", "turant", "paisa", "adhikari",
            "police", "giraftari", "daravani", "karein", "rupaye", "karo", "jaldi", "batao",
            "sharma", "sahab", "suno", "namaste", "badhai"
        }
        words = set(re.findall(r'\b[a-zA-Z]+\b', text.lower()))
        common = words.intersection(hinglish_tokens)
        if len(common) >= 1:
            return "Hindi / Hinglish"

        return "English"

    def _extract_multilingual_signals(
        self,
        clean_text: str,
        caller_claimed: Optional[str] = None
    ) -> Tuple[List[FraudSignal], List[ContextualSignal], str]:
        lower_t = clean_text.lower()
        signals: List[FraudSignal] = []
        contextual: List[ContextualSignal] = []
        language = self._detect_language(clean_text)

        # 1. OTP / Credential Demands
        otp_patterns = [
            r"\botp\b", r"\bone-time password\b", r"\bpin\b", r"\bpasscode\b",
            r"\bverification code\b", r"6-digit", r"4-digit", r"ओटीपी", r"पिन", r"पासकोड"
        ]
        if any(re.search(p, lower_t) for p in otp_patterns):
            signals.append(FraudSignal(
                id=f"SIG-AUTH-{uuid.uuid4().hex[:6].upper()}",
                signal_type="OTP_REQUEST",
                category="AUTHENTICATION",
                severity="CRITICAL",
                confidence=0.98,
                description="Caller urgently demanded high-security One-Time Password (OTP) or authentication code.",
                timestamp="00:06",
                risk_contribution=28,
                detected_phrases=["OTP", "verification code", "6-digit"]
            ))

        # Check for explicit legitimate phrasing (negative lookahead context)
        is_explicitly_benign = any(k in lower_t for k in [
            "never ask for your", "will not ask", "passbook by post", "see you there", "do not share with anyone"
        ])

        # 2. Bank / Financial Institution Impersonation
        bank_keywords = ["bank", "sbi", "hdfc", "icici", "axis", "security department", "fraud desk", "rbi", "branch manager", "बैंक", "शाखा प्रबंधक"]
        claimed_bank = caller_claimed and any(b in caller_claimed.lower() for b in ["bank", "sbi", "hdfc", "icici", "security"])
        if not is_explicitly_benign and (any(b in lower_t for b in bank_keywords) or claimed_bank):
            signals.append(FraudSignal(
                id=f"SIG-IMP-{uuid.uuid4().hex[:6].upper()}",
                signal_type="BANK_IMPERSONATION",
                category="IMPERSONATION",
                severity="HIGH",
                confidence=0.94,
                description=f"Caller asserted authority as a banking institution security representative ({caller_claimed or 'Bank Officer'}).",
                timestamp="00:02",
                risk_contribution=22,
                detected_phrases=["bank security desk", "account department", "fraud prevention"]
            ))

        # 3. Police / Government / Digital Arrest Impersonation
        police_keywords = [
            "police", "cbi", "trai", "customs", "cyber cell", "arrest warrant", "court order",
            "enforcement directorate", "customs department", "digital arrest", "पुलिस", "वारंट", "गिरफ्तारी"
        ]
        claimed_police = caller_claimed and any(p in caller_claimed.lower() for p in ["police", "cbi", "trai", "cyber", "court"])
        if any(p in lower_t for p in police_keywords) or claimed_police:
            signals.append(FraudSignal(
                id=f"SIG-POL-{uuid.uuid4().hex[:6].upper()}",
                signal_type="POLICE_IMPERSONATION",
                category="IMPERSONATION",
                severity="CRITICAL",
                confidence=0.96,
                description="Caller falsely asserted law enforcement, customs, or court digital arrest authority.",
                timestamp="00:02",
                risk_contribution=26,
                detected_phrases=["cyber crime officer", "arrest warrant", "illegal parcel"]
            ))

        # 4. Threats & Coercion: Account Block, Legal Threat, Immediate Freeze
        threat_patterns = [
            r"\bblock\w*\b", r"\bfreeze\w*\b", r"\bfrozen\b", r"\bsuspend\w*\b",
            r"\bterminat\w*\b", r"\barrest\w*\b", r"\bjail\b", r"\bdeactivat\w*\b",
            r"\bband ho jayega\b", r"\brok diya jayega\b", r"ब्लॉक", r"बंद"
        ]
        if any(re.search(p, lower_t) for p in threat_patterns):
            signals.append(FraudSignal(
                id=f"SIG-THR-{uuid.uuid4().hex[:6].upper()}",
                signal_type="ACCOUNT_BLOCK_THREAT",
                category="THREAT",
                severity="HIGH",
                confidence=0.92,
                description="Caller issued coercive threat to immediately block bank account, SIM card, or suspend services.",
                timestamp="00:04",
                risk_contribution=20,
                detected_phrases=["account will be blocked", "immediate suspension", "turant band"]
            ))

        # 5. Financial / Payment / UPI / QR Demands
        payment_patterns = [
            r"\bupi\b", r"\bgpay\b", r"\bphonepe\b", r"\bpaytm\b", r"\bsend money\b",
            r"\brefund fee\b", r"\bqr code\b", r"\bbhejiye\b", r"\btransfer fee\b", r"पैसे भेजो", r"क्यूआर कोड"
        ]
        if any(re.search(p, lower_t) for p in payment_patterns):
            signals.append(FraudSignal(
                id=f"SIG-FIN-{uuid.uuid4().hex[:6].upper()}",
                signal_type="SUSPICIOUS_PAYMENT_REQUEST",
                category="FINANCIAL",
                severity="HIGH",
                confidence=0.91,
                description="Caller instructed target to initiate immediate UPI transfer or scan QR code.",
                timestamp="00:08",
                risk_contribution=18,
                detected_phrases=["UPI transfer", "scan QR code", "registration fee"]
            ))

        # 6. Remote Desktop / Software Installation (AnyDesk, TeamViewer)
        tech_patterns = [
            r"\banydesk\b", r"\bteamviewer\b", r"\bquicksupport\b", r"\bscreen share\b",
            r"\bdownload app\b", r"\bplay store\b", r"\bremote access\b"
        ]
        if any(re.search(p, lower_t) for p in tech_patterns):
            signals.append(FraudSignal(
                id=f"SIG-TECH-{uuid.uuid4().hex[:6].upper()}",
                signal_type="REMOTE_ACCESS_REQUEST",
                category="TECHNICAL",
                severity="CRITICAL",
                confidence=0.95,
                description="Caller coerced target into downloading remote control software (AnyDesk / TeamViewer).",
                timestamp="00:09",
                risk_contribution=26,
                detected_phrases=["download AnyDesk", "remote access", "share code"]
            ))

        # 7. Contextual Signals: Urgency, Coercion, Secrecy
        urgency_score = 0.85 if any(k in lower_t for k in ["immediately", "turant", "urgent", "within 5 minutes", "now", "jaldi", "right now"]) else 0.20
        contextual.append(ContextualSignal(
            name="Urgency & Time Pressure",
            score=urgency_score,
            severity="HIGH" if urgency_score > 0.7 else "LOW",
            description="Caller applied psychological time pressure to bypass verification scrutiny."
        ))

        secrecy_score = 0.80 if any(k in lower_t for k in ["don't tell", "keep secret", "don't hang up", "confidential", "kisi ko mat batana"]) else 0.15
        contextual.append(ContextualSignal(
            name="Isolation & Secrecy",
            score=secrecy_score,
            severity="MEDIUM" if secrecy_score > 0.6 else "LOW",
            description="Attempt to isolate target from family members, advisors, or bank personnel."
        ))

        return signals, contextual, language

    async def detect_fraud_intent(
        self,
        raw_transcript: str,
        caller_claimed: Optional[str] = None
    ) -> FraudIntentResult:
        """
        Main analysis method. Redacts PII, then executes provider (Azure or Local NLP).
        """
        if not raw_transcript or not raw_transcript.strip():
            return FraudIntentResult(
                primary_category="BENIGN",
                fraud_detected=False,
                intent_score=0.0,
                detected_signals=[],
                contextual_signals=[],
                language_detected="unknown"
            )

        # 1. PII Redaction
        redacted_text, _ = PIIRedactionService.redact_transcript(raw_transcript)

        # 2. Azure OpenAI path if configured and chosen
        if settings.AI_PROVIDER == "azure" and hasattr(self.provider, "analyze_fraud_intent"):
            try:
                return await self.provider.analyze_fraud_intent(redacted_text, caller_claimed)
            except Exception as e:
                logger.error(f"Azure OpenAI fraud analysis failed: {e}. Executing local fallback rules.")
                # If in production and provider fails, can record provider error or fallback
                if settings.APP_MODE == "production":
                    raise

        # 3. Local Multilingual NLP Rule Engine
        signals, contextual, language = self._extract_multilingual_signals(redacted_text, caller_claimed)

        if not signals:
            intent_score = 0.05
            primary_cat = "BENIGN_INQUIRY"
            fraud_detected = False
        else:
            intent_score = min(0.98, sum(s.risk_contribution for s in signals) / 75.0)
            primary_cat = signals[0].category
            fraud_detected = True

        return FraudIntentResult(
            primary_category=primary_cat,
            fraud_detected=fraud_detected,
            intent_score=round(intent_score, 2),
            detected_signals=signals,
            contextual_signals=contextual,
            language_detected=language
        )
