"use client";

import React from "react";
import Link from "next/link";
import {
  Shield,
  Radio,
  Mic,
  Cpu,
  Lock,
  ArrowRight,
  UserCheck,
  Flame,
  Layers,
  FileCheck,
  PhoneCall,
  CheckCircle2,
} from "lucide-react";
import { GlassCard } from "../components/GlassCard";
import { AnimatedPipeline } from "../components/AnimatedPipeline";
import { Logo } from "../components/Logo";

export default function HomePage() {
  const capabilities = [
    {
      title: "Voice Anti-Spoofing",
      description: "Detects neural vocoder phase artifacts, synthetic audio splices, and cloned voice signatures in real time.",
      icon: Cpu,
    },
    {
      title: "1:1 Speaker Verification",
      description: "Compares inbound acoustic embeddings against verified reference samples to confirm authorized caller identity.",
      icon: UserCheck,
    },
    {
      title: "Fraud Intent Analysis",
      description: "Analyzes conversational patterns in English, Hindi, and Hinglish for OTP solicitation, authority intimidation, and bank impersonation.",
      icon: Mic,
    },
    {
      title: "Behavioral Context Evaluation",
      description: "Detects psychological pressure tactics including artificial deadlines, secrecy demands, and threat escalation.",
      icon: Flame,
    },
    {
      title: "Multi-Modal Decision Matrix",
      description: "Synthesizes acoustic, biometric, semantic, and telephony signals into clear, explainable risk determinations.",
      icon: Layers,
    },
    {
      title: "Zero-Retention Privacy",
      description: "Real-time stream evaluation with ephemeral processing. Raw telephony audio is never retained without explicit audit consent.",
      icon: Lock,
    },
  ];

  const quickActions = [
    {
      title: "Live Call Protection",
      description: "Monitor simulated or live telephony streams with instantaneous risk scoring and step-by-step transcript inspection.",
      href: "/live",
      icon: Radio,
      badge: "Interactive Demo",
      buttonText: "Launch Live SOC Monitor",
      primary: true,
    },
    {
      title: "Analyze Audio or Transcript",
      description: "Upload a recorded call file (WAV, MP3, FLAC) or paste conversational dialogue to generate a comprehensive threat breakdown.",
      href: "/analyze",
      icon: PhoneCall,
      buttonText: "Run Threat Analysis",
    },
    {
      title: "Security Incident Console",
      description: "Investigate flagged telephony events, review analyst notes, examine forensic evidence, or record formal decision overrides.",
      href: "/evidence",
      icon: FileCheck,
      buttonText: "View Incidents",
    },
  ];

  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <section className="text-center max-w-3xl mx-auto pt-4 pb-2 space-y-4">
        <div className="inline-flex items-center gap-2 rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700">
          <Shield className="h-3.5 w-3.5" />
          <span>Telephony Threat Intelligence Platform</span>
        </div>

        <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-slate-900 leading-tight">
          Protecting voice communications from synthetic fraud and impersonation.
        </h1>

        <p className="text-base sm:text-lg text-slate-600 leading-relaxed max-w-2xl mx-auto">
          VoiceShield AI combines acoustic anti-spoofing, 1:1 speaker verification, and multilingual intent classification to identify fraudulent calls before harm occurs.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-3 pt-3">
          <Link
            href="/live"
            className="flex items-center gap-2 rounded-md bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 transition-colors"
          >
            <Radio className="h-4 w-4" />
            <span>Simulate Bank Scam Call</span>
            <ArrowRight className="h-4 w-4" />
          </Link>

          <Link
            href="/analyze"
            className="flex items-center gap-2 rounded-md bg-white border border-slate-300 px-5 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors shadow-sm"
          >
            <Mic className="h-4 w-4 text-slate-500" />
            <span>Analyze File / Text</span>
          </Link>
        </div>
      </section>

      {/* Quick Access Action Cards */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {quickActions.map((qa) => {
          const Icon = qa.icon;
          return (
            <div
              key={qa.title}
              className={`rounded-lg border p-6 flex flex-col justify-between transition-all ${
                qa.primary
                  ? "bg-blue-50/50 border-blue-200 shadow-sm"
                  : "bg-white border-slate-200 shadow-sm hover:border-slate-300"
              }`}
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div
                    className={`rounded-md p-2 border ${
                      qa.primary
                        ? "bg-blue-600 text-white border-blue-600"
                        : "bg-slate-100 text-slate-700 border-slate-200"
                    }`}
                  >
                    <Icon className="h-5 w-5" />
                  </div>
                  {qa.badge && (
                    <span className="rounded bg-blue-100 px-2 py-0.5 text-[11px] font-semibold text-blue-800">
                      {qa.badge}
                    </span>
                  )}
                </div>

                <h2 className="text-base font-semibold text-slate-900">{qa.title}</h2>
                <p className="text-xs text-slate-600 leading-relaxed">{qa.description}</p>
              </div>

              <div className="pt-5 mt-4 border-t border-slate-100">
                <Link
                  href={qa.href}
                  className={`inline-flex items-center gap-1.5 text-xs font-semibold ${
                    qa.primary ? "text-blue-700 hover:text-blue-800" : "text-slate-700 hover:text-slate-900"
                  }`}
                >
                  <span>{qa.buttonText}</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </div>
            </div>
          );
        })}
      </section>

      {/* Multi-Layer Pipeline Flowchart */}
      <section className="space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Multi-Modal Threat Inspection Pipeline</h2>
            <p className="text-xs text-slate-500">
              Each inbound voice stream passes through sequential acoustic, biometric, and semantic security layers.
            </p>
          </div>
          <Link href="/demo" className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1">
            <span>Explore Sandbox Scenarios</span>
            <ArrowRight className="h-3 w-3" />
          </Link>
        </div>

        <GlassCard className="p-4 sm:p-6">
          <AnimatedPipeline currentStageIndex={7} />
        </GlassCard>
      </section>

      {/* Security Capabilities Grid */}
      <section className="space-y-4">
        <div>
          <h2 className="text-lg font-bold text-slate-900">Core Security Modules</h2>
          <p className="text-xs text-slate-500">
            Engineered specifically for telephony infrastructure and contact-center environments.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {capabilities.map((cap) => {
            const Icon = cap.icon;
            return (
              <div
                key={cap.title}
                className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm space-y-2 hover:border-slate-300 transition-colors"
              >
                <div className="rounded-md bg-slate-50 border border-slate-200 p-2 w-fit text-blue-600">
                  <Icon className="h-5 w-5" />
                </div>
                <h3 className="text-sm font-semibold text-slate-900">{cap.title}</h3>
                <p className="text-xs text-slate-600 leading-relaxed">{cap.description}</p>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
