"use client";

import React, { useState, useEffect } from "react";
import { PageHeader } from "../../components/PageHeader";
import { DemoPlayer } from "../../components/DemoPlayer";
import { DemoScenario } from "../../lib/types";
import { ApiClient } from "../../lib/api";
import { Info } from "lucide-react";

const CANONICAL_SCENARIOS: DemoScenario[] = [
  {
    id: "bank-otp-scam",
    name: "Bank OTP Coercion Scam",
    category: "AUTHENTICATION_FRAUD",
    description: "Caller poses as HDFC Bank Security officer, claims account block within 5 minutes, and demands 6-digit OTP.",
    caller_claimed: "HDFC Bank Security Desk",
    caller_phone: "+91 (022) 6128-4091",
    duration_seconds: 16,
    transcript: "Hello, this is officer Rajesh Sharma from HDFC Bank Security Department. We detected an unauthorized transaction attempt of Rs 48,500 on your debit card. Your account will be immediately blocked and frozen within 5 minutes unless you verify your identity. I have just sent a 6-digit OTP verification code to your registered mobile number. Please read out the OTP right now to stop the fraudulent withdrawal.",
    language: "English / Hinglish",
    expected_risk_score: 94,
    expected_risk_level: "HIGH",
    expected_decision: "CONFIRMED_FRAUD",
    voice_spoof_prob: 0.91,
    speaker_similarity: 0.18,
    audio_quality: "FAIR",
    telephony_condition: "DEGRADED",
    codec: "G.711u / 8kHz",
    channel: "Narrowband PSTN",
    warning_actions: [
      "Do not disclose the 6-digit OTP or any authentication credentials.",
      "Disconnect the interaction immediately.",
      "Contact HDFC Bank using the official customer care number on your debit card."
    ],
    signals: [],
    timeline_events: [],
  },
  {
    id: "technical-remote-access",
    name: "E-Commerce / Technical Remote Access Scam",
    category: "TECHNICAL_FRAUD",
    description: "Caller poses as Amazon customer support offering refund, asks target to install AnyDesk.",
    caller_claimed: "Amazon Refund Helpdesk",
    caller_phone: "+91 (080) 4129-9400",
    duration_seconds: 16,
    transcript: "Namaste sir, this is from Amazon Customer Care. You have an accidental auto-debit of Rs 14,999 on your order. To initiate instant refund to your bank, please download AnyDesk app from Play Store and share the 9-digit remote access code.",
    language: "English / Hinglish",
    expected_risk_score: 86,
    expected_risk_level: "HIGH",
    expected_decision: "CONFIRMED_FRAUD",
    voice_spoof_prob: 0.82,
    speaker_similarity: 0.22,
    audio_quality: "GOOD",
    telephony_condition: "NORMAL",
    codec: "Opus / 16kHz",
    channel: "VoIP / Cellular",
    warning_actions: [
      "Never install remote desktop software (AnyDesk, TeamViewer) at the request of an inbound caller.",
      "Terminate the call immediately.",
      "Check your official Amazon app under 'Your Orders' to verify any charges."
    ],
    signals: [],
    timeline_events: [],
  },
  {
    id: "digital-arrest",
    name: "CBI / Telecom Digital Arrest Threat",
    category: "COERCION_IMPERSONATION",
    description: "Caller claims to be from Cyber Crime Police & TRAI, alleging illegal parcel and digital arrest warrant.",
    caller_claimed: "Cyber Crime Branch Delhi",
    caller_phone: "+91 (011) 2346-7000",
    duration_seconds: 16,
    transcript: "This is Inspector Vikram Rathore from Delhi Police Cyber Crime Branch and TRAI. A parcel containing illegal substances and 12 SIM cards registered in your name was intercepted at Mumbai Customs. An arrest warrant has been issued against you.",
    language: "English / Hindi",
    expected_risk_score: 92,
    expected_risk_level: "HIGH",
    expected_decision: "CONFIRMED_FRAUD",
    voice_spoof_prob: 0.88,
    speaker_similarity: 0.15,
    audio_quality: "FAIR",
    telephony_condition: "DEGRADED",
    codec: "G.711a / 8kHz",
    channel: "PSTN Interconnect",
    warning_actions: [
      "Law enforcement agencies in India never conduct 'Digital Arrest' or demand Skype/video presence.",
      "Do not transfer funds to any 'safe RBI verification account'.",
      "Report the impersonation attempt immediately to cybercrime.gov.in (National Cyber Crime Portal 1930)."
    ],
    signals: [],
    timeline_events: [],
  },
  {
    id: "lottery-scam",
    name: "Kaun Banega Crorepati Lottery Scam",
    category: "FINANCIAL_SCAM",
    description: "Caller claims target won 25 Lakh INR lottery in lucky draw, asks for advance registration fee via personal UPI.",
    caller_claimed: "KBC Lottery Department",
    caller_phone: "+91 (022) 2854-1920",
    duration_seconds: 16,
    transcript: "Badhai ho! Aapka number KBC lucky draw me 25 Lakh rupaye ka prize jeeta hai. Prize money aapke bank account me transfer karne ke liye bas 5,000 rupaye registration tax fee is personal UPI number par turant bhejiye.",
    language: "Hindi / Hinglish",
    expected_risk_score: 78,
    expected_risk_level: "HIGH",
    expected_decision: "LIKELY_FRAUD",
    voice_spoof_prob: 0.74,
    speaker_similarity: 0.30,
    audio_quality: "GOOD",
    telephony_condition: "NORMAL",
    codec: "AMR-WB / 16kHz",
    channel: "Cellular VoLTE",
    warning_actions: [
      "Legitimate lotteries and game shows never require upfront cash payments or UPI transfers to claim prizes.",
      "Do not send money or scan any UPI QR code sent by the caller.",
      "Block the caller number and report fraudulent UPI handles to your payment app."
    ],
    signals: [],
    timeline_events: [],
  },
  {
    id: "legitimate-bank-call",
    name: "Legitimate Card Transaction Confirmation",
    category: "LEGITIMATE_INTERACTION",
    description: "Official bank agent calling to confirm international transaction. Agent does NOT ask for OTP/PIN, matches enrolled profile.",
    caller_claimed: "ICICI Bank Card Protection",
    caller_phone: "+91 (022) 6757-0000",
    duration_seconds: 16,
    transcript: "Good morning Mr. Verma, this is Priya from ICICI Bank Card Services calling regarding a pending overseas transaction of 120 USD on your credit card ending in 4092. We will never ask for your OTP, PIN, or CVV. If you recognize this, simply reply yes, or check your official iMobile banking app.",
    language: "English",
    expected_risk_score: 8,
    expected_risk_level: "LOW",
    expected_decision: "BENIGN",
    voice_spoof_prob: 0.04,
    speaker_similarity: 0.95,
    audio_quality: "GOOD",
    telephony_condition: "NORMAL",
    codec: "G.722 / 16kHz",
    channel: "High-Definition PBX",
    warning_actions: [],
    signals: [],
    timeline_events: [],
  },
  {
    id: "poor-quality-benign",
    name: "Poor Audio Quality / Non-Fraud Call",
    category: "BENIGN_DEGRADED",
    description: "Legitimate conversational call recorded in heavy ambient street traffic noise. High noise floor, zero fraud cues.",
    caller_claimed: "Colleague / Arun",
    caller_phone: "+91 98450 11223",
    duration_seconds: 14,
    transcript: "Hey, can you hear me? Sorry, I'm standing right next to heavy traffic on MG Road and the bus just passed by. Just wanted to confirm we're still meeting at 4 PM for the team sync. Let me know when you reach.",
    language: "English",
    expected_risk_score: 14,
    expected_risk_level: "LOW",
    expected_decision: "BENIGN",
    voice_spoof_prob: 0.08,
    speaker_similarity: 0.89,
    audio_quality: "POOR",
    telephony_condition: "DEGRADED",
    codec: "G.711u / 8kHz",
    channel: "Noisy Cellular Handset",
    warning_actions: [],
    signals: [],
    timeline_events: [],
  },
];

export default function DemoPage() {
  const [scenarios, setScenarios] = useState<DemoScenario[]>(CANONICAL_SCENARIOS);

  useEffect(() => {
    async function loadScenarios() {
      try {
        const data = await ApiClient.getDemoScenarios();
        if (data && data.length > 0) {
          setScenarios(data);
        }
      } catch (_) {}
    }
    loadScenarios();
  }, []);

  return (
    <div className="space-y-6">
      <PageHeader
        badge="Sandbox Environment"
        badgeVariant="amber"
        title="Evaluated Threat Scenarios"
        description="Explore calibrated benchmark evaluation scenarios covering banking impersonation, remote desktop tools, courier arrests, and legitimate customer service interactions."
      />

      <div className="rounded-lg border border-slate-200 bg-white p-4 text-xs text-slate-600 flex items-start gap-3 shadow-sm">
        <Info className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-slate-900 block">Deterministic Sandbox Isolation:</span>
          <span>
            Scenarios in this catalog allow security teams to benchmark model weights against verified Indian and global telephony fraud patterns without risking production data.
          </span>
        </div>
      </div>

      <DemoPlayer scenarios={scenarios} />
    </div>
  );
}
