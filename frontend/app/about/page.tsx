"use client";

import React from "react";
import { PageHeader } from "../../components/PageHeader";
import { GlassCard } from "../../components/GlassCard";
import { Shield, Lock, AlertTriangle, Sparkles, Compass } from "lucide-react";

export default function AboutPage() {
  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      <PageHeader
        badge="Mission & Principles"
        badgeVariant="indigo"
        title="About VoiceShield AI"
        description="Protecting voice communications and enterprise contact centers from synthetic deepfakes and conversational fraud."
      />

      {/* Core Question Answered */}
      <GlassCard className="p-6 text-center space-y-3">
        <span className="text-xs uppercase tracking-widest text-blue-700 font-semibold">
          Core Problem Solved
        </span>
        <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 italic">
          “Is this phone interaction dangerous?”
        </h2>
        <p className="text-xs sm:text-sm text-slate-600 max-w-xl mx-auto leading-relaxed">
          We do not merely inspect whether a voice waveform is synthetic. VoiceShield AI fuses conversational intent, acoustic harmonics, 1:1 speaker identity, and psychological urgency into actionable cyber-defense.
        </p>
      </GlassCard>

      {/* Grid of Principles */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <GlassCard className="p-5 space-y-2">
          <div className="flex items-center gap-2 text-blue-600 mb-1">
            <Sparkles className="h-4 w-4" />
            <h3 className="text-sm font-semibold text-slate-900">Defense-in-Depth Beyond Voice Detection</h3>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed">
            Conventional tools only check if audio is AI-generated. VoiceShield AI detects when human scammers use real voices with social engineering, and when AI cloned voices are disguised with telephony noise.
          </p>
        </GlassCard>

        <GlassCard className="p-5 space-y-2">
          <div className="flex items-center gap-2 text-emerald-600 mb-1">
            <Lock className="h-4 w-4" />
            <h3 className="text-sm font-semibold text-slate-900">Zero-Retention Audio Privacy</h3>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed">
            Inbound audio is evaluated in volatile memory during feature extraction and purged immediately after feature derivation. No raw audio is retained without explicit enterprise audit consent.
          </p>
        </GlassCard>
      </div>

      {/* Responsible AI & Limitations */}
      <GlassCard className="p-6 space-y-3">
        <div className="flex items-center gap-2 text-amber-700 border-b border-slate-100 pb-3">
          <AlertTriangle className="h-4 w-4" />
          <h3 className="text-sm font-semibold text-slate-900">Responsible AI & Telephony Constraints</h3>
        </div>

        <div className="space-y-3 text-xs text-slate-600 leading-relaxed">
          <p className="p-3 rounded-md bg-amber-50 border border-amber-200 font-medium text-amber-900">
            VoiceShield AI provides risk signals and evidence for analyst adjudication, not absolute deterministic truth.
          </p>
          <ul className="space-y-1.5 list-disc list-inside text-slate-600">
            <li>Zero-day deepfakes and evolving conversational manipulation require human-in-the-loop oversight.</li>
            <li>Narrowband PSTN/GSM audio naturally introduces spectral distortion that our models explicitly account for.</li>
            <li>Biometric speaker verification is strictly 1:1 against enrolled organizational profiles, never used for unconsented mass surveillance.</li>
          </ul>
        </div>
      </GlassCard>
    </div>
  );
}
