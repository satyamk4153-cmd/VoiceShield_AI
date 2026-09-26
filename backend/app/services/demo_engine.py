from datetime import datetime, timezone
from typing import List, Optional
from app.schemas.demo import DemoScenario, DemoTimelineEvent
from app.schemas.fraud import FraudSignal, ContextualSignal
from app.schemas.risk import (
    FinalAnalysisResponse,
    RiskAssessment,
    EvidenceItem,
    VoiceAuthenticityResult,
)
from app.schemas.speaker import SpeakerVerificationResult
from app.schemas.audio import AudioQualityResult


class DemoEngineService:
    @staticmethod
    def get_all_scenarios() -> List[DemoScenario]:
        return [
            # 1. Bank OTP Scam
            DemoScenario(
                id="bank-otp-scam",
                name="Bank OTP Coercion Scam",
                category="AUTHENTICATION_FRAUD",
                description="Caller poses as HDFC Bank Security officer, claims account block within 5 minutes, and demands 6-digit OTP.",
                caller_claimed="HDFC Bank Security Desk",
                caller_phone="+91 (022) 6128-4091",
                duration_seconds=16,
                transcript="Hello, this is officer Rajesh Sharma from HDFC Bank Security Department. We detected an unauthorized transaction attempt of Rs 48,500 on your debit card. Your account will be immediately blocked and frozen within 5 minutes unless you verify your identity. I have just sent a 6-digit OTP verification code to your registered mobile number. Please read out the OTP right now to stop the fraudulent withdrawal.",
                language="English / Hinglish",
                expected_risk_score=94,
                expected_risk_level="HIGH",
                expected_decision="CONFIRMED_FRAUD",
                voice_spoof_prob=0.91,
                speaker_similarity=0.18,
                audio_quality="FAIR",
                telephony_condition="DEGRADED",
                codec="G.711u / 8kHz",
                channel="Narrowband PSTN",
                warning_actions=[
                    "Do not disclose the 6-digit OTP or any authentication credentials.",
                    "Disconnect the interaction immediately.",
                    "Contact HDFC Bank using the official customer care number on your debit card."
                ],
                signals=[
                    FraudSignal(
                        id="SIG-OTP-01",
                        signal_type="OTP_REQUEST",
                        category="AUTHENTICATION",
                        severity="CRITICAL",
                        confidence=0.98,
                        description="Caller demanded high-security 6-digit One-Time Password (OTP) verification code.",
                        timestamp="00:06",
                        risk_contribution=28,
                        detected_phrases=["OTP", "6-digit OTP", "read out the OTP"]
                    ),
                    FraudSignal(
                        id="SIG-OTP-02",
                        signal_type="BANK_IMPERSONATION",
                        category="IMPERSONATION",
                        severity="HIGH",
                        confidence=0.94,
                        description="Caller asserted authority as an official HDFC Bank Security Desk officer.",
                        timestamp="00:02",
                        risk_contribution=22,
                        detected_phrases=["HDFC Bank Security Department", "officer Rajesh Sharma"]
                    ),
                    FraudSignal(
                        id="SIG-OTP-03",
                        signal_type="ACCOUNT_BLOCK_THREAT",
                        category="THREAT",
                        severity="HIGH",
                        confidence=0.92,
                        description="Caller issued coercive threat that bank account will be immediately blocked in 5 mins.",
                        timestamp="00:04",
                        risk_contribution=20,
                        detected_phrases=["account will be immediately blocked", "frozen within 5 minutes"]
                    ),
                    FraudSignal(
                        id="SIG-OTP-04",
                        signal_type="SPEAKER_MISMATCH",
                        category="BIOMETRIC",
                        severity="HIGH",
                        confidence=0.91,
                        description="Acoustic vocal tract embedding failed 1:1 similarity test against enrolled bank agent baseline.",
                        timestamp="00:09",
                        risk_contribution=14,
                        detected_phrases=["Vocal tract spectral mismatch (Cosine: 0.18)"]
                    ),
                    FraudSignal(
                        id="SIG-OTP-05",
                        signal_type="VOICE_SPOOF_ARTIFACTS",
                        category="SYNTHETIC_AUDIO",
                        severity="HIGH",
                        confidence=0.88,
                        description="Phase continuity anomalies and neural vocoder spectral artifacts detected.",
                        timestamp="00:12",
                        risk_contribution=10,
                        detected_phrases=["Neural vocoder synthesis (Spoof: 0.91)"]
                    )
                ],
                timeline_events=[
                    DemoTimelineEvent(
                        id="EVT-OTP-01",
                        seconds=0,
                        time_offset="00:00",
                        event_type="INCOMING_CALL",
                        label="Incoming Call",
                        transcript_segment="[Ring... Inbound Call from HDFC Bank Security Desk +91 (022) 6128-4091]"
                    ),
                    DemoTimelineEvent(
                        id="EVT-OTP-02",
                        seconds=2,
                        time_offset="00:02",
                        event_type="IDENTITY_CLAIM",
                        label="Bank Identity Claim",
                        transcript_segment="Hello, this is officer Rajesh Sharma from HDFC Bank Security Department...",
                        signal_detected="BANK_IMPERSONATION",
                        severity="HIGH",
                        risk_accumulated=22
                    ),
                    DemoTimelineEvent(
                        id="EVT-OTP-03",
                        seconds=4,
                        time_offset="00:04",
                        event_type="ACCOUNT_THREAT",
                        label="Account Block Threat",
                        transcript_segment="We detected an unauthorized Rs 48,500 fraud. Your account will be blocked within 5 minutes...",
                        signal_detected="ACCOUNT_BLOCK_THREAT",
                        severity="HIGH",
                        risk_accumulated=42
                    ),
                    DemoTimelineEvent(
                        id="EVT-OTP-04",
                        seconds=6,
                        time_offset="00:06",
                        event_type="OTP_DEMAND",
                        label="OTP Request",
                        transcript_segment="I have sent a 6-digit OTP code to your phone. Read it out immediately to cancel...",
                        signal_detected="OTP_REQUEST",
                        severity="CRITICAL",
                        risk_accumulated=70
                    ),
                    DemoTimelineEvent(
                        id="EVT-OTP-05",
                        seconds=9,
                        time_offset="00:09",
                        event_type="SPEAKER_CHECK",
                        label="Speaker Mismatch",
                        transcript_segment="[Biometric Voice Comparison vs Bank Baseline Failed: Cosine 0.18 MISMATCH]",
                        signal_detected="SPEAKER_MISMATCH",
                        severity="HIGH",
                        risk_accumulated=84
                    ),
                    DemoTimelineEvent(
                        id="EVT-OTP-06",
                        seconds=12,
                        time_offset="00:12",
                        event_type="SPOOF_CHECK",
                        label="Possible Voice Spoof",
                        transcript_segment="[Spectral phase discontinuities & neural vocoder artifacts: Spoof Prob 0.91]",
                        signal_detected="VOICE_SPOOF_ARTIFACTS",
                        severity="HIGH",
                        risk_accumulated=94
                    ),
                    DemoTimelineEvent(
                        id="EVT-OTP-07",
                        seconds=14,
                        time_offset="00:14",
                        event_type="FINAL_SCORE",
                        label="94/100 HIGH RISK",
                        transcript_segment="CRITICAL ALERT: Confirmed Social Engineering & Impersonation Attack. Score: 94/100",
                        severity="CRITICAL",
                        risk_accumulated=94
                    ),
                    DemoTimelineEvent(
                        id="EVT-OTP-08",
                        seconds=16,
                        time_offset="00:16",
                        event_type="ADVISORY_WARNING",
                        label="Security Warning",
                        transcript_segment="ACTION: DO NOT SHARE OTP. END CALL IMMEDIATELY. CONTACT OFFICIAL BANK HELPLINE.",
                        severity="CRITICAL",
                        risk_accumulated=94
                    )
                ]
            ),

            # 2. Technical Remote Access Scam
            DemoScenario(
                id="technical-remote-access",
                name="E-Commerce / Technical Remote Access Scam",
                category="TECHNICAL_FRAUD",
                description="Caller poses as Amazon customer support offering refund, asks target to install AnyDesk and share remote control code.",
                caller_claimed="Amazon Refund Helpdesk",
                caller_phone="+91 80 4356 7812",
                duration_seconds=15,
                transcript="Namaste sir, this is Rahul Verma from Amazon Customer Care. You have an accidental auto-debit of Rs 14,999 on your order. To initiate instant refund to your bank account, please download AnyDesk app from Google Play Store right now and share the 9-digit remote access code.",
                language="English / Hinglish",
                expected_risk_score=86,
                expected_risk_level="HIGH",
                expected_decision="CONFIRMED_FRAUD",
                voice_spoof_prob=0.82,
                speaker_similarity=0.22,
                audio_quality="GOOD",
                telephony_condition="NORMAL",
                codec="AMR-WB / 16kHz",
                channel="VoLTE Cellular",
                warning_actions=[
                    "Never install remote desktop software (AnyDesk, TeamViewer, QuickSupport) at caller request.",
                    "Do not disclose 9-digit remote access connection codes to anyone.",
                    "Verify order status directly in your official Amazon account app."
                ],
                signals=[
                    FraudSignal(
                        id="SIG-TECH-01",
                        signal_type="TECH_IMPERSONATION",
                        category="IMPERSONATION",
                        severity="HIGH",
                        confidence=0.92,
                        description="Caller impersonated customer support refund representative.",
                        timestamp="00:02",
                        risk_contribution=20,
                        detected_phrases=["Amazon Customer Care", "auto-debit refund"]
                    ),
                    FraudSignal(
                        id="SIG-TECH-02",
                        signal_type="REMOTE_ACCESS_REQUEST",
                        category="TECHNICAL",
                        severity="CRITICAL",
                        confidence=0.96,
                        description="Caller instructed victim to install remote desktop control tool (AnyDesk).",
                        timestamp="00:07",
                        risk_contribution=26,
                        detected_phrases=["AnyDesk", "remote access code"]
                    ),
                    FraudSignal(
                        id="SIG-TECH-03",
                        signal_type="FINANCIAL_EXTORTION",
                        category="FINANCIAL",
                        severity="HIGH",
                        confidence=0.89,
                        description="Fraudulent auto-debit refund lure used to bypass victim skepticism.",
                        timestamp="00:04",
                        risk_contribution=18,
                        detected_phrases=["accidental auto-debit Rs 14,999", "instant refund"]
                    ),
                    FraudSignal(
                        id="SIG-TECH-04",
                        signal_type="VOICE_SPOOF_ARTIFACTS",
                        category="SYNTHETIC_AUDIO",
                        severity="HIGH",
                        confidence=0.82,
                        description="Synthetic acoustic clone artifacts detected in vocoder frequency envelope.",
                        timestamp="00:10",
                        risk_contribution=12,
                        detected_phrases=["Acoustic synthesis detected (Spoof: 0.82)"]
                    ),
                    FraudSignal(
                        id="SIG-TECH-05",
                        signal_type="SPEAKER_MISMATCH",
                        category="BIOMETRIC",
                        severity="HIGH",
                        confidence=0.85,
                        description="Vocal identity failed comparison against official verified customer care baselines.",
                        timestamp="00:13",
                        risk_contribution=10,
                        detected_phrases=["Acoustic mismatch with corporate profile (Cosine: 0.22)"]
                    )
                ],
                timeline_events=[
                    DemoTimelineEvent(
                        id="EVT-TECH-01",
                        seconds=0,
                        time_offset="00:00",
                        event_type="INCOMING_CALL",
                        label="Incoming Call",
                        transcript_segment="[Ring... Incoming Call from Amazon Support Desk +91 80 4356 7812]"
                    ),
                    DemoTimelineEvent(
                        id="EVT-TECH-02",
                        seconds=2,
                        time_offset="00:02",
                        event_type="IDENTITY_CLAIM",
                        label="Support Identity Claim",
                        transcript_segment="Namaste sir, this is Rahul Verma from Amazon Customer Care...",
                        signal_detected="TECH_IMPERSONATION",
                        severity="HIGH",
                        risk_accumulated=20
                    ),
                    DemoTimelineEvent(
                        id="EVT-TECH-03",
                        seconds=4,
                        time_offset="00:04",
                        event_type="FINANCIAL_BAIT",
                        label="Auto-Debit Lure",
                        transcript_segment="You have an accidental auto-debit of Rs 14,999 on your order that needs instant refund...",
                        signal_detected="FINANCIAL_EXTORTION",
                        severity="HIGH",
                        risk_accumulated=38
                    ),
                    DemoTimelineEvent(
                        id="EVT-TECH-04",
                        seconds=7,
                        time_offset="00:07",
                        event_type="REMOTE_ACCESS_DEMAND",
                        label="AnyDesk Installation Demand",
                        transcript_segment="Please download AnyDesk app from Play Store right now and share the 9-digit code...",
                        signal_detected="REMOTE_ACCESS_REQUEST",
                        severity="CRITICAL",
                        risk_accumulated=64
                    ),
                    DemoTimelineEvent(
                        id="EVT-TECH-05",
                        seconds=10,
                        time_offset="00:10",
                        event_type="SPOOF_CHECK",
                        label="Synthetic Audio Scan",
                        transcript_segment="[Synthetic vocoder artifacts detected in carrier frequency: Spoof Prob 0.82]",
                        signal_detected="VOICE_SPOOF_ARTIFACTS",
                        severity="HIGH",
                        risk_accumulated=76
                    ),
                    DemoTimelineEvent(
                        id="EVT-TECH-06",
                        seconds=13,
                        time_offset="00:13",
                        event_type="SPEAKER_CHECK",
                        label="Support Baseline Mismatch",
                        transcript_segment="[Biometric acoustic baseline check failed: Cosine 0.22 MISMATCH]",
                        signal_detected="SPEAKER_MISMATCH",
                        severity="HIGH",
                        risk_accumulated=86
                    ),
                    DemoTimelineEvent(
                        id="EVT-TECH-07",
                        seconds=15,
                        time_offset="00:15",
                        event_type="ADVISORY_WARNING",
                        label="Remote Access Advisory",
                        transcript_segment="HIGH RISK ADVISORY: Do not install AnyDesk or share remote codes. Disconnect call.",
                        severity="CRITICAL",
                        risk_accumulated=86
                    )
                ]
            ),

            # 3. Police / Digital Arrest Impersonation
            DemoScenario(
                id="digital-arrest",
                name="CBI / Telecom Digital Arrest Threat",
                category="COERCION_IMPERSONATION",
                description="Caller claims to be from Cyber Crime Police & TRAI, alleging illegal parcel and digital arrest warrant.",
                caller_claimed="Cyber Crime Branch Delhi",
                caller_phone="+91 11 2341 9900",
                duration_seconds=16,
                transcript="This is Inspector Vikram Rathore from Delhi Police Cyber Crime Branch and TRAI. A parcel containing illegal narcotics and 12 forged SIM cards registered in your name was intercepted at Mumbai Customs. An immediate non-bailable arrest warrant has been issued against you. You are placed under digital arrest right now. Do not disconnect this call or you will be physically detained.",
                language="English / Hindi",
                expected_risk_score=92,
                expected_risk_level="HIGH",
                expected_decision="CONFIRMED_FRAUD",
                voice_spoof_prob=0.88,
                speaker_similarity=0.15,
                audio_quality="FAIR",
                telephony_condition="DEGRADED",
                codec="G.711u / 8kHz",
                channel="Narrowband PSTN",
                warning_actions=[
                    "Indian police, CBI, and customs NEVER conduct 'digital arrest' or interrogate via phone/video calls.",
                    "Do not transfer funds into any 'police verification' escrow accounts.",
                    "End the call and report immediately to cybercrime.gov.in or call National Helpline 1930."
                ],
                signals=[
                    FraudSignal(
                        id="SIG-POL-01",
                        signal_type="POLICE_IMPERSONATION",
                        category="IMPERSONATION",
                        severity="CRITICAL",
                        confidence=0.97,
                        description="Caller asserted fake law enforcement authority and fraudulent customs parcel claims.",
                        timestamp="00:02",
                        risk_contribution=24,
                        detected_phrases=["Delhi Police Cyber Crime", "TRAI", "Customs parcel"]
                    ),
                    FraudSignal(
                        id="SIG-POL-02",
                        signal_type="LEGAL_ARREST_THREAT",
                        category="THREAT",
                        severity="CRITICAL",
                        confidence=0.95,
                        description="Extortion threat with fake arrest warrant and digital custody coercion.",
                        timestamp="00:05",
                        risk_contribution=24,
                        detected_phrases=["arrest warrant", "digital arrest", "do not disconnect"]
                    ),
                    FraudSignal(
                        id="SIG-POL-03",
                        signal_type="COERCIVE_ISOLATION",
                        category="THREAT",
                        severity="HIGH",
                        confidence=0.91,
                        description="Caller demanded victim maintain secrecy and remain isolated on phone line.",
                        timestamp="00:08",
                        risk_contribution=20,
                        detected_phrases=["do not speak to anyone", "physically detained"]
                    ),
                    FraudSignal(
                        id="SIG-POL-04",
                        signal_type="VOICE_SPOOF_ARTIFACTS",
                        category="SYNTHETIC_AUDIO",
                        severity="HIGH",
                        confidence=0.88,
                        description="Acoustic cloning and pitch modulation artifacts detected.",
                        timestamp="00:11",
                        risk_contribution=14,
                        detected_phrases=["Voice clone synthesis (Spoof: 0.88)"]
                    ),
                    FraudSignal(
                        id="SIG-POL-05",
                        signal_type="SPEAKER_MISMATCH",
                        category="BIOMETRIC",
                        severity="HIGH",
                        confidence=0.89,
                        description="No correspondence with verified government authority biometric profiles.",
                        timestamp="00:13",
                        risk_contribution=10,
                        detected_phrases=["Official identity mismatch (Cosine: 0.15)"]
                    )
                ],
                timeline_events=[
                    DemoTimelineEvent(
                        id="EVT-POL-01",
                        seconds=0,
                        time_offset="00:00",
                        event_type="INCOMING_CALL",
                        label="Incoming Call",
                        transcript_segment="[Ring... Inbound Call from Delhi Police Cyber Unit +91 11 2341 9900]"
                    ),
                    DemoTimelineEvent(
                        id="EVT-POL-02",
                        seconds=2,
                        time_offset="00:02",
                        event_type="IDENTITY_CLAIM",
                        label="Police Authority Claim",
                        transcript_segment="This is Inspector Vikram Rathore from Delhi Police Cyber Crime Branch and TRAI...",
                        signal_detected="POLICE_IMPERSONATION",
                        severity="CRITICAL",
                        risk_accumulated=24
                    ),
                    DemoTimelineEvent(
                        id="EVT-POL-03",
                        seconds=5,
                        time_offset="00:05",
                        event_type="ARREST_THREAT",
                        label="Customs Parcel & Arrest Warrant",
                        transcript_segment="An illegal parcel containing narcotics and 12 forged SIMs in your name was intercepted...",
                        signal_detected="LEGAL_ARREST_THREAT",
                        severity="CRITICAL",
                        risk_accumulated=48
                    ),
                    DemoTimelineEvent(
                        id="EVT-POL-04",
                        seconds=8,
                        time_offset="00:08",
                        event_type="ISOLATION_DEMAND",
                        label="Digital Arrest Coercion",
                        transcript_segment="You are placed under digital arrest right now. Do not disconnect this line or you will be detained...",
                        signal_detected="COERCIVE_ISOLATION",
                        severity="HIGH",
                        risk_accumulated=68
                    ),
                    DemoTimelineEvent(
                        id="EVT-POL-05",
                        seconds=11,
                        time_offset="00:11",
                        event_type="SPOOF_CHECK",
                        label="Voice Clone Scan",
                        transcript_segment="[Acoustic cloning and pitch modulation artifacts detected: Spoof Prob 0.88]",
                        signal_detected="VOICE_SPOOF_ARTIFACTS",
                        severity="HIGH",
                        risk_accumulated=82
                    ),
                    DemoTimelineEvent(
                        id="EVT-POL-06",
                        seconds=13,
                        time_offset="00:13",
                        event_type="SPEAKER_CHECK",
                        label="Authority Profile Mismatch",
                        transcript_segment="[No match with verified government acoustic profiles: Cosine 0.15 MISMATCH]",
                        signal_detected="SPEAKER_MISMATCH",
                        severity="HIGH",
                        risk_accumulated=92
                    ),
                    DemoTimelineEvent(
                        id="EVT-POL-07",
                        seconds=16,
                        time_offset="00:16",
                        event_type="ADVISORY_WARNING",
                        label="Digital Arrest Warning",
                        transcript_segment="CRITICAL ADVISORY: Fake Digital Arrest Coercion. End call immediately and report to 1930.",
                        severity="CRITICAL",
                        risk_accumulated=92
                    )
                ]
            ),

            # 4. Lottery / Prize Scam
            DemoScenario(
                id="lottery-scam",
                name="Kaun Banega Crorepati Lottery Scam",
                category="FINANCIAL_SCAM",
                description="Caller claims target won 25 Lakh INR lottery in lucky draw, asks for advance registration fee via personal UPI.",
                caller_claimed="KBC Lottery Department",
                caller_phone="+91 97182 34091",
                duration_seconds=15,
                transcript="Badhai ho! Aapka number KBC lucky draw me 25 Lakh rupaye ka prize jeeta hai. Prize money aapke bank account me transfer karne ke liye bas 5,000 rupaye registration tax fee is personal UPI number par turant bhejiye. Sirf aadhe ghante ka samay hai.",
                language="Hindi / Hinglish",
                expected_risk_score=78,
                expected_risk_level="HIGH",
                expected_decision="LIKELY_FRAUD",
                voice_spoof_prob=0.74,
                speaker_similarity=0.30,
                audio_quality="GOOD",
                telephony_condition="NORMAL",
                codec="AMR / 8kHz",
                channel="GSM Mobile",
                warning_actions=[
                    "Never pay advance fees, registration charges, or taxes to receive lottery winnings.",
                    "Legitimate television programs and lotteries never demand money transfers via personal UPI.",
                    "Block the caller number and report unsolicited prize calls to 1930."
                ],
                signals=[
                    FraudSignal(
                        id="SIG-LOT-01",
                        signal_type="LOTTERY_PRIZE_SCAM",
                        category="SCAM",
                        severity="HIGH",
                        confidence=0.94,
                        description="Unsolicited advance-fee lucky draw lottery scam pattern.",
                        timestamp="00:02",
                        risk_contribution=20,
                        detected_phrases=["25 Lakh lucky draw", "KBC prize"]
                    ),
                    FraudSignal(
                        id="SIG-LOT-02",
                        signal_type="SUSPICIOUS_PAYMENT_REQUEST",
                        category="FINANCIAL",
                        severity="HIGH",
                        confidence=0.92,
                        description="Caller requested advance registration fee payment via personal UPI.",
                        timestamp="00:06",
                        risk_contribution=22,
                        detected_phrases=["personal UPI", "5,000 registration tax"]
                    ),
                    FraudSignal(
                        id="SIG-LOT-03",
                        signal_type="ARTIFICIAL_URGENCY",
                        category="THREAT",
                        severity="MEDIUM",
                        confidence=0.88,
                        description="Artificial 30-minute deadline imposed to pressure victim decision making.",
                        timestamp="00:09",
                        risk_contribution=18,
                        detected_phrases=["aadhe ghante ka samay", "turant bhejiye"]
                    ),
                    FraudSignal(
                        id="SIG-LOT-04",
                        signal_type="VOICE_SPOOF_ARTIFACTS",
                        category="SYNTHETIC_AUDIO",
                        severity="MEDIUM",
                        confidence=0.74,
                        description="Vocoder phase inconsistencies detected in caller voice signal.",
                        timestamp="00:12",
                        risk_contribution=10,
                        detected_phrases=["Moderate synthetic synthesis (Spoof: 0.74)"]
                    ),
                    FraudSignal(
                        id="SIG-LOT-05",
                        signal_type="SPEAKER_MISMATCH",
                        category="BIOMETRIC",
                        severity="MEDIUM",
                        confidence=0.78,
                        description="Biometric speaker profile does not match authorized broadcast personnel.",
                        timestamp="00:14",
                        risk_contribution=8,
                        detected_phrases=["Unverified caller acoustic profile (Cosine: 0.30)"]
                    )
                ],
                timeline_events=[
                    DemoTimelineEvent(
                        id="EVT-LOT-01",
                        seconds=0,
                        time_offset="00:00",
                        event_type="INCOMING_CALL",
                        label="Incoming Call",
                        transcript_segment="[Ring... Incoming Call from KBC Lottery Cell +91 97182 34091]"
                    ),
                    DemoTimelineEvent(
                        id="EVT-LOT-02",
                        seconds=2,
                        time_offset="00:02",
                        event_type="PRIZE_CLAIM",
                        label="Lottery Prize Announcement",
                        transcript_segment="Badhai ho! Aapka number KBC lucky draw me 25 Lakh rupaye ka prize jeeta hai...",
                        signal_detected="LOTTERY_PRIZE_SCAM",
                        severity="HIGH",
                        risk_accumulated=20
                    ),
                    DemoTimelineEvent(
                        id="EVT-LOT-03",
                        seconds=6,
                        time_offset="00:06",
                        event_type="PAYMENT_DEMAND",
                        label="Advance Fee Demand",
                        transcript_segment="Prize money transfer karne ke liye bas 5,000 rupaye registration tax fee is personal UPI par bhejiye...",
                        signal_detected="SUSPICIOUS_PAYMENT_REQUEST",
                        severity="HIGH",
                        risk_accumulated=42
                    ),
                    DemoTimelineEvent(
                        id="EVT-LOT-04",
                        seconds=9,
                        time_offset="00:09",
                        event_type="TIME_PRESSURE",
                        label="Artificial Urgency",
                        transcript_segment="Sirf aadhe ghante ka samay hai, turant payment kijiye nahi toh cancel ho jayega...",
                        signal_detected="ARTIFICIAL_URGENCY",
                        severity="MEDIUM",
                        risk_accumulated=60
                    ),
                    DemoTimelineEvent(
                        id="EVT-LOT-05",
                        seconds=12,
                        time_offset="00:12",
                        event_type="SPOOF_CHECK",
                        label="Voice Authenticity Check",
                        transcript_segment="[Acoustic vocoder phase inconsistencies detected: Spoof Prob 0.74]",
                        signal_detected="VOICE_SPOOF_ARTIFACTS",
                        severity="MEDIUM",
                        risk_accumulated=70
                    ),
                    DemoTimelineEvent(
                        id="EVT-LOT-06",
                        seconds=15,
                        time_offset="00:15",
                        event_type="ADVISORY_WARNING",
                        label="Lottery Fraud Advisory",
                        transcript_segment="HIGH RISK ADVISORY: Unsolicited Lottery Advance-Fee Scam. Do not send any funds via UPI.",
                        severity="HIGH",
                        risk_accumulated=78
                    )
                ]
            ),

            # 5. Legitimate Bank Call
            DemoScenario(
                id="legitimate-bank-call",
                name="Legitimate Card Transaction Confirmation",
                category="LEGITIMATE_INTERACTION",
                description="Official bank agent calling to confirm international transaction. Agent does NOT ask for OTP/PIN, matches enrolled profile.",
                caller_claimed="ICICI Bank Card Protection",
                caller_phone="+91 1800 200 8976 (Toll-Free)",
                duration_seconds=15,
                transcript="Good morning Mr. Verma, this is Priya from ICICI Bank Card Services calling regarding a pending overseas transaction of 120 USD on your credit card ending in 4092. We are calling only to verify if you initiated this charge. Please note we will never ask for your OTP, PIN, or CVV. If you recognize this, simply reply yes, or check your official iMobile banking app.",
                language="English",
                expected_risk_score=8,
                expected_risk_level="LOW",
                expected_decision="BENIGN",
                voice_spoof_prob=0.04,
                speaker_similarity=0.94,
                audio_quality="GOOD",
                telephony_condition="NORMAL",
                codec="G.711u / 8kHz",
                channel="Enterprise SIP Trunk",
                warning_actions=[],
                signals=[],
                timeline_events=[
                    DemoTimelineEvent(
                        id="EVT-LEG-01",
                        seconds=0,
                        time_offset="00:00",
                        event_type="INCOMING_CALL",
                        label="Incoming Call",
                        transcript_segment="[Ring... Inbound Call from ICICI Bank Toll-Free 1800 200 8976]"
                    ),
                    DemoTimelineEvent(
                        id="EVT-LEG-02",
                        seconds=2,
                        time_offset="00:02",
                        event_type="IDENTITY_CLAIM",
                        label="Bank Representative Greeting",
                        transcript_segment="Good morning Mr. Verma, this is Priya from ICICI Bank Card Services...",
                        signal_detected=None,
                        severity=None,
                        risk_accumulated=2
                    ),
                    DemoTimelineEvent(
                        id="EVT-LEG-03",
                        seconds=5,
                        time_offset="00:05",
                        event_type="TRANSACTION_VERIFY",
                        label="Transaction Verification",
                        transcript_segment="Calling regarding a pending overseas transaction of 120 USD on your credit card ending in 4092...",
                        signal_detected=None,
                        severity=None,
                        risk_accumulated=4
                    ),
                    DemoTimelineEvent(
                        id="EVT-LEG-04",
                        seconds=8,
                        time_offset="00:08",
                        event_type="SECURITY_DISCLAIMER",
                        label="Explicit Safety Disclaimer",
                        transcript_segment="Please note we will NEVER ask for your OTP, PIN, or CVV. You can also confirm in your iMobile app...",
                        signal_detected=None,
                        severity=None,
                        risk_accumulated=6
                    ),
                    DemoTimelineEvent(
                        id="EVT-LEG-05",
                        seconds=11,
                        time_offset="00:11",
                        event_type="SPEAKER_MATCH",
                        label="Speaker Biometric Match",
                        transcript_segment="[Acoustic embedding matches enrolled official representative profile: Cosine 0.94 MATCH]",
                        signal_detected=None,
                        severity=None,
                        risk_accumulated=7
                    ),
                    DemoTimelineEvent(
                        id="EVT-LEG-06",
                        seconds=13,
                        time_offset="00:13",
                        event_type="SPOOF_CHECK",
                        label="Voice Authenticity Confirmed",
                        transcript_segment="[Natural human vocal tract harmonics verified: Spoof Prob 0.04 - AUTHENTIC]",
                        signal_detected=None,
                        severity=None,
                        risk_accumulated=8
                    ),
                    DemoTimelineEvent(
                        id="EVT-LEG-07",
                        seconds=15,
                        time_offset="00:15",
                        event_type="BENIGN_STATUS",
                        label="Low Risk Verified",
                        transcript_segment="VERIFIED BENIGN INTERACTION: Authorized representative confirmed. Risk Score: 8/100 LOW.",
                        signal_detected=None,
                        severity=None,
                        risk_accumulated=8
                    )
                ]
            ),

            # 6. Poor Quality Unknown Call (Benign)
            DemoScenario(
                id="poor-quality-benign",
                name="Degraded Telephony Line (Benign)",
                category="TELEPHONY_DEGRADATION",
                description="Low SNR, traffic noise, narrowband GSM audio with benign conversation regarding meeting logistics.",
                caller_claimed="Colleague / Arun",
                caller_phone="+91 98112 55431",
                duration_seconds=14,
                transcript="Hello? Can you hear me? I am stuck in heavy traffic on the highway, network is breaking. Let us meet at 6 PM at the coffee shop near the metro station. See you there.",
                language="English",
                expected_risk_score=14,
                expected_risk_level="LOW",
                expected_decision="BENIGN",
                voice_spoof_prob=0.14,
                speaker_similarity=0.65,
                audio_quality="POOR",
                telephony_condition="HIGHLY_DEGRADED",
                codec="GSM-FR / 8kHz",
                channel="Narrowband Cellular",
                warning_actions=[],
                signals=[],
                timeline_events=[
                    DemoTimelineEvent(
                        id="EVT-DEG-01",
                        seconds=0,
                        time_offset="00:00",
                        event_type="INCOMING_CALL",
                        label="Incoming Call",
                        transcript_segment="[Ring... Inbound Mobile Call from +91 98112 55431]"
                    ),
                    DemoTimelineEvent(
                        id="EVT-DEG-02",
                        seconds=2,
                        time_offset="00:02",
                        event_type="ACOUSTIC_NOTICE",
                        label="Acoustic Line Degradation",
                        transcript_segment="Hello? Can you hear me? I am stuck in heavy traffic on the highway, network is breaking...",
                        signal_detected=None,
                        severity=None,
                        risk_accumulated=6
                    ),
                    DemoTimelineEvent(
                        id="EVT-DEG-03",
                        seconds=6,
                        time_offset="00:06",
                        event_type="BENIGN_LOGISTICS",
                        label="Benign Logistics",
                        transcript_segment="Let us meet at 6 PM at the coffee shop near the metro station. See you there...",
                        signal_detected=None,
                        severity=None,
                        risk_accumulated=9
                    ),
                    DemoTimelineEvent(
                        id="EVT-DEG-04",
                        seconds=9,
                        time_offset="00:09",
                        event_type="TELEPHONY_CHECK",
                        label="Line Quality Assessment",
                        transcript_segment="[Telephony SNR 9.2dB (High Traffic Noise), human vocal phonemes intact: Condition DEGRADED]",
                        signal_detected=None,
                        severity=None,
                        risk_accumulated=12
                    ),
                    DemoTimelineEvent(
                        id="EVT-DEG-05",
                        seconds=12,
                        time_offset="00:12",
                        event_type="INTENT_CHECK",
                        label="Zero Threat Intent",
                        transcript_segment="[Conversational intent analysis: Zero fraud indicators or coercive tactics detected]",
                        signal_detected=None,
                        severity=None,
                        risk_accumulated=14
                    ),
                    DemoTimelineEvent(
                        id="EVT-DEG-06",
                        seconds=14,
                        time_offset="00:14",
                        event_type="FINAL_STATUS",
                        label="Benign Assessment",
                        transcript_segment="BENIGN EVALUATION: Line degraded by environmental traffic noise. No fraud indicators. Score: 14/100.",
                        signal_detected=None,
                        severity=None,
                        risk_accumulated=14
                    )
                ]
            )
        ]

    @classmethod
    def get_scenario_by_id(cls, scenario_id: str) -> Optional[DemoScenario]:
        # Handle canonical IDs and backward-compatible aliases
        alias_map = {
            "customer-care-scam": "technical-remote-access",
            "police-impersonation": "digital-arrest",
            "prize-lottery-scam": "lottery-scam",
            "poor-quality-unknown": "poor-quality-benign",
        }
        resolved_id = alias_map.get(scenario_id, scenario_id)

        scenarios = cls.get_all_scenarios()
        for s in scenarios:
            if s.id == resolved_id:
                return s
        return None

    @classmethod
    def get_scenario_analysis(cls, scenario_id: str) -> Optional[FinalAnalysisResponse]:
        scenario = cls.get_scenario_by_id(scenario_id)
        if not scenario:
            return None

        evidence_items = []
        for i, sig in enumerate(scenario.signals):
            evidence_items.append(
                EvidenceItem(
                    id=f"EVI-{sig.id or i+1}",
                    timestamp=sig.timestamp or "00:05",
                    title=sig.signal_type.replace("_", " ").title(),
                    category=sig.category,
                    severity=sig.severity,
                    explanation=sig.description,
                    contribution_points=sig.risk_contribution
                )
            )

        if not evidence_items and scenario.timeline_events:
            for ev in scenario.timeline_events:
                if ev.signal_detected or (ev.risk_accumulated and ev.risk_accumulated > 0):
                    evidence_items.append(
                        EvidenceItem(
                            id=f"EVI-{ev.id or ev.seconds}",
                            timestamp=ev.time_offset,
                            title=ev.label,
                            category="BEHAVIORAL",
                            severity=ev.severity or "LOW",
                            explanation=ev.transcript_segment,
                            contribution_points=ev.risk_accumulated or 5
                        )
                    )

        contextual_signals = []
        if scenario.expected_risk_score >= 70:
            contextual_signals.append(
                ContextualSignal(
                    name="Urgency & Coercion Pressure",
                    score=0.92,
                    severity="HIGH",
                    description="Caller utilized psychological pressure and immediate threat tactics."
                )
            )
        elif scenario.expected_risk_score >= 40:
            contextual_signals.append(
                ContextualSignal(
                    name="Financial Solicitations",
                    score=0.65,
                    severity="MEDIUM",
                    description="Unverified financial solicitation detected."
                )
            )
        else:
            contextual_signals.append(
                ContextualSignal(
                    name="Routine Inbound Protocol",
                    score=0.08,
                    severity="LOW",
                    description="Interaction adheres to standard verification protocol with no coercive tactics."
                )
            )

        risk_breakdown = {
            "intent_signals": sum(s.risk_contribution for s in scenario.signals),
            "voice_authenticity": int(scenario.voice_spoof_prob * 20),
            "speaker_verification": 15 if scenario.speaker_similarity < 0.45 else 0,
            "telephony_degradation": 10 if scenario.telephony_condition != "NORMAL" else 0
        }

        spk_result = "MATCH" if scenario.speaker_similarity >= 0.70 else ("MISMATCH" if scenario.speaker_similarity < 0.45 else "UNCERTAIN")
        spk_explanation = (
            f"Acoustic speaker embedding cosine similarity {scenario.speaker_similarity:.2f} confirms authorized profile match."
            if spk_result == "MATCH"
            else f"Acoustic speaker embedding failed 1:1 similarity check against claimed baseline (Cosine: {scenario.speaker_similarity:.2f})."
        )

        spoof_class = "POSSIBLE_SPOOF" if scenario.voice_spoof_prob >= 0.70 else ("SUSPICIOUS" if scenario.voice_spoof_prob >= 0.40 else "AUTHENTIC")
        spoof_explanation = (
            f"Neural vocoder artifacts and synthetic phase anomalies detected with {int(scenario.voice_spoof_prob * 100)}% spoof probability."
            if scenario.voice_spoof_prob >= 0.50
            else f"Natural human vocal tract formants verified ({int((1.0 - scenario.voice_spoof_prob) * 100)}% authentic probability)."
        )

        quality_score = 0.85 if scenario.audio_quality == "GOOD" else (0.55 if scenario.audio_quality == "FAIR" else 0.30)

        return FinalAnalysisResponse(
            analysis_id=f"DEMO-{scenario.id}",
            session_id=f"SES-DEMO-{scenario.id}",
            incident_id=f"INC-DEMO-{scenario.id}",
            status="completed",
            created_at=datetime.now(timezone.utc).isoformat(),
            is_demo_data=True,
            provider_used="demo_sandbox",
            transcript=scenario.transcript,
            caller_claimed_identity=scenario.caller_claimed,
            risk=RiskAssessment(
                score=scenario.expected_risk_score,
                level=scenario.expected_risk_level,
                decision=scenario.expected_decision,
                confidence=0.96,
                risk_breakdown=risk_breakdown,
                policy_id="POL-DEMO-BENCHMARK",
                policy_version="v2.1",
                reason_codes=[s.signal_type for s in scenario.signals]
            ),
            voice=VoiceAuthenticityResult(
                authenticity_probability=round(1.0 - scenario.voice_spoof_prob, 2),
                spoof_probability=round(scenario.voice_spoof_prob, 2),
                confidence=0.92,
                classification=spoof_class,
                explanation=spoof_explanation,
                model_name="acoustic-spectral-anti-spoof",
                model_version="v2.4",
                inference_ms=45,
                status="OK",
                is_demo=True
            ),
            speaker=SpeakerVerificationResult(
                similarity=round(scenario.speaker_similarity, 2),
                confidence=0.94,
                result=spk_result,
                threshold=0.70,
                explanation=spk_explanation,
                model_name="ecapa-tdnn-speaker-id",
                model_version="v1.8",
                status="OK",
                is_demo=True
            ),
            audio=AudioQualityResult(
                duration_seconds=float(scenario.duration_seconds),
                sample_rate=8000 if "8kHz" in scenario.codec else 16000,
                channels=1,
                rms_energy=0.12,
                snr_db=9.2 if scenario.telephony_condition == "DEGRADED" else 24.5,
                clipping_ratio=0.001,
                silence_ratio=0.08,
                bandwidth_hz=3400 if "8kHz" in scenario.codec else 7000,
                quality_score=quality_score,
                quality_level=scenario.audio_quality,
                telephony_condition=scenario.telephony_condition,
                quality_notes=[f"Telephony codec: {scenario.codec}", f"Channel: {scenario.channel}"]
            ),
            fraud_signals=scenario.signals,
            contextual_signals=contextual_signals,
            evidence=evidence_items,
            recommended_actions=scenario.warning_actions or ["No adverse risk detected. Standard call handling advised."]
        )

