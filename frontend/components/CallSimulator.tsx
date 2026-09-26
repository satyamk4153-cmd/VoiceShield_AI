"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Phone,
  PhoneOff,
  Mic,
  ShieldAlert,
  User,
  Clock,
  Activity,
  RotateCcw,
  Play,
  FileText,
  ArrowRight,
  ShieldCheck,
} from "lucide-react";
import Link from "next/link";
import { DemoScenario, FraudSignal } from "../lib/types";
import { SignalCard } from "../components/SignalCard";
import { WarningBanner } from "../components/WarningBanner";
import { cn } from "../lib/utils";

interface CallSimulatorProps {
  scenario: DemoScenario;
  onComplete?: () => void;
}

export const CallSimulator: React.FC<CallSimulatorProps> = ({ scenario, onComplete }) => {
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(0);
  const [activeSignals, setActiveSignals] = useState<FraudSignal[]>([]);
  const [transcriptLines, setTranscriptLines] = useState<{ time: string; text: string; speaker: string }[]>([]);
  const [currentScore, setCurrentScore] = useState<number>(0);
  const [callEnded, setCallEnded] = useState<boolean>(false);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const timelineEvents = scenario.timeline_events || [];
  const totalDuration = scenario.duration_seconds || (timelineEvents.length > 0 ? Math.max(...timelineEvents.map((e) => e.seconds)) : 16) || 16;
  const callerPhone = scenario.caller_phone || "Line: Inbound PSTN";
  const codec = scenario.codec || "G.711u / 8kHz";
  const channel = scenario.channel || "Narrowband PSTN";
  const warningActions = scenario.warning_actions || [];

  const handleStartSimulation = () => {
    setIsPlaying(true);
    setElapsedSeconds(0);
    setActiveSignals([]);
    setTranscriptLines([]);
    setCurrentScore(0);
    setCallEnded(false);
  };

  const handleReset = () => {
    setIsPlaying(false);
    if (intervalRef.current) clearInterval(intervalRef.current);
    setElapsedSeconds(0);
    setActiveSignals([]);
    setTranscriptLines([]);
    setCurrentScore(0);
    setCallEnded(false);
  };

  // Reset when switching scenarios
  useEffect(() => {
    handleReset();
  }, [scenario.id]);

  useEffect(() => {
    if (isPlaying && !callEnded) {
      intervalRef.current = setInterval(() => {
        setElapsedSeconds((prev) => {
          const next = prev + 1;
          if (next >= totalDuration) {
            setCallEnded(true);
            setIsPlaying(false);
            if (intervalRef.current) clearInterval(intervalRef.current);
            if (onComplete) onComplete();
            return totalDuration;
          }
          return next;
        });
      }, 1000);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isPlaying, callEnded, totalDuration, onComplete]);

  // Evaluate events at specific elapsed seconds
  useEffect(() => {
    timelineEvents.forEach((ev) => {
      if (ev.seconds === elapsedSeconds) {
        if (ev.transcript_segment) {
          setTranscriptLines((prev) => [
            ...prev,
            {
              time: ev.time_offset,
              text: ev.transcript_segment,
              speaker: ev.event_type.includes("INCOMING") || ev.event_type.includes("STATUS") || ev.event_type.includes("CHECK")
                ? "System Telemetry"
                : scenario.caller_claimed,
            },
          ]);
        }

        // Maintain cumulative risk score
        if (typeof ev.risk_accumulated === "number") {
          setCurrentScore((prev) => Math.max(prev, ev.risk_accumulated!));
        }

        if (ev.signal_detected) {
          const foundSig = scenario.signals.find(
            (s) => s.signal_type.includes(ev.signal_detected!) || ev.signal_detected!.includes(s.signal_type)
          );
          if (foundSig) {
            setActiveSignals((prev) => {
              if (prev.some((s) => s.id === foundSig.id)) return prev;
              return [...prev, foundSig];
            });
          } else {
            // Dynamic signal construction from event
            setActiveSignals((prev) => {
              const dynId = `SIG-${ev.signal_detected}-${ev.seconds}`;
              if (prev.some((s) => s.id === dynId)) return prev;
              return [
                ...prev,
                {
                  id: dynId,
                  signal_type: ev.signal_detected!,
                  category: ev.event_type || "TELEMETRY",
                  severity: (ev.severity as any) || "HIGH",
                  confidence: 0.92,
                  description: ev.transcript_segment || `${ev.label} telemetry flagged.`,
                  timestamp: ev.time_offset,
                  risk_contribution: ev.risk_accumulated || 15,
                  detected_phrases: [ev.label],
                },
              ];
            });
          }
        }
      }
    });
  }, [elapsedSeconds, timelineEvents, scenario]);

  const showWarning = warningActions.length > 0 && (currentScore >= 70 || (callEnded && scenario.expected_risk_score >= 70));

  return (
    <div className="space-y-6">
      {/* Simulation Controller Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-50 text-blue-600 border border-blue-100">
            <Phone className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-slate-900 text-sm sm:text-base">{scenario.name}</span>
              <span className="rounded bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-600 border border-slate-200">
                Sandbox Mode
              </span>
            </div>
            <p className="text-xs text-slate-500">
              Claimed Identity: <span className="font-medium text-slate-700">{scenario.caller_claimed}</span> • {callerPhone}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {!isPlaying && !callEnded ? (
            <button
              onClick={handleStartSimulation}
              className="flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-blue-700 transition-colors"
            >
              <Play className="h-3.5 w-3.5 fill-current" />
              <span>Start Live Simulation</span>
            </button>
          ) : (
            <button
              onClick={handleReset}
              className="flex items-center gap-2 rounded-md bg-slate-100 px-3.5 py-2 text-xs font-medium text-slate-700 border border-slate-200 hover:bg-slate-200 transition-colors"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              <span>Reset Simulation</span>
            </button>
          )}

          {callEnded && (
            <Link
              href={`/result?scenario=${encodeURIComponent(scenario.id)}`}
              className="flex items-center gap-1.5 rounded-md bg-emerald-600 px-3.5 py-2 text-xs font-semibold text-white shadow-sm hover:bg-emerald-700 transition-colors"
            >
              <FileText className="h-3.5 w-3.5" />
              <span>View Forensic Report</span>
              <ArrowRight className="h-3 w-3" />
            </Link>
          )}
        </div>
      </div>

      {/* 3-Column Monitoring Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Call Status Card */}
        <div className="lg:col-span-4 space-y-4">
          <div className="rounded-lg border border-slate-200 bg-white p-5 flex flex-col items-center text-center shadow-sm relative">
            <div className="w-full flex items-center justify-between text-xs text-slate-500 mb-4">
              <span className="flex items-center gap-1.5 font-medium">
                <span className={`h-2 w-2 rounded-full ${isPlaying ? "bg-emerald-500 animate-pulse" : "bg-slate-300"}`} />
                {isPlaying ? "Call In Progress" : callEnded ? "Call Concluded" : "Ready to Connect"}
              </span>
              <span className="font-mono text-slate-500">
                00:{elapsedSeconds.toString().padStart(2, "0")} / 00:{totalDuration.toString().padStart(2, "0")}
              </span>
            </div>

            <div className="my-2 relative">
              <div className="h-20 w-20 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center">
                <User className="h-10 w-10 text-slate-400" />
              </div>
              {isPlaying && (
                <div className="absolute -bottom-1 -right-1 h-6 w-6 rounded-full bg-blue-600 flex items-center justify-center text-white text-[10px]">
                  <Mic className="h-3.5 w-3.5" />
                </div>
              )}
            </div>

            <h3 className="text-base font-bold text-slate-900 mt-2">{scenario.caller_claimed}</h3>
            <span className="text-xs text-slate-500 font-mono mt-0.5">{callerPhone}</span>

            {/* Audio Waveform visualization */}
            <div className="mt-5 flex items-center justify-center gap-1 h-7 w-full max-w-[180px]">
              {[35, 65, 85, 40, 75, 95, 55, 30, 80, 90, 40, 70, 85, 45].map((h, i) => (
                <div
                  key={i}
                  className={cn(
                    "w-1 rounded-full transition-all duration-150",
                    isPlaying ? "bg-blue-600" : "bg-slate-200"
                  )}
                  style={{ height: isPlaying ? `${Math.max(20, (h * ((elapsedSeconds % 3) + 1)) / 3)}%` : "20%" }}
                />
              ))}
            </div>

            {/* Disconnect Action */}
            <div className="mt-5 pt-4 border-t border-slate-100 w-full flex justify-center">
              <button
                disabled={!isPlaying}
                onClick={handleReset}
                className="flex items-center gap-1.5 rounded-md bg-red-50 px-4 py-1.5 text-xs font-medium text-red-700 border border-red-200 hover:bg-red-100 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <PhoneOff className="h-3.5 w-3.5" />
                <span>Disconnect Call</span>
              </button>
            </div>
          </div>

          {/* Telephony Acoustic Profile */}
          <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
            <span className="text-xs font-medium text-slate-500 block mb-2">
              Telephony Signal Properties
            </span>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="p-2.5 rounded bg-slate-50 border border-slate-200">
                <span className="text-slate-400 block text-[10px]">Codec</span>
                <span className="text-slate-800 font-semibold">{codec}</span>
              </div>
              <div className="p-2.5 rounded bg-slate-50 border border-slate-200">
                <span className="text-slate-400 block text-[10px]">Acoustic Channel</span>
                <span className="text-slate-800 font-semibold">{channel}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Center: Live Transcript Stream */}
        <div className="lg:col-span-4 flex flex-col h-[480px] rounded-lg border border-slate-200 bg-white shadow-sm overflow-hidden">
          <div className="border-b border-slate-200 px-4 py-3 bg-slate-50 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="h-4 w-4 text-blue-600" />
              <span className="text-xs font-semibold text-slate-900">Speech-to-Text Transcript</span>
            </div>
            <span className="rounded bg-blue-50 px-2 py-0.5 text-[10px] font-medium text-blue-700 border border-blue-200">
              Live Stream
            </span>
          </div>

          <div className="flex-1 p-4 overflow-y-auto space-y-2.5 text-xs">
            {transcriptLines.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center text-slate-400 p-4">
                <Phone className="h-7 w-7 mb-2 text-slate-300" />
                <p>Click &ldquo;Start Live Simulation&rdquo; to stream inbound audio and analyze real-time signals.</p>
              </div>
            ) : (
              transcriptLines.map((line, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="rounded-md bg-slate-50 p-3 border border-slate-200 space-y-1"
                >
                  <div className="flex items-center justify-between text-[11px] text-slate-500">
                    <span className="font-semibold text-blue-700">{line.speaker}</span>
                    <span className="font-mono text-[10px]">{line.time}</span>
                  </div>
                  <p className="text-slate-800 leading-relaxed">{line.text}</p>
                </motion.div>
              ))
            )}
          </div>
        </div>

        {/* Right: Detected Fraud Signals & Risk Score */}
        <div className="lg:col-span-4 flex flex-col h-[480px] space-y-4">
          <div className="flex-1 rounded-lg border border-slate-200 bg-white p-4 shadow-sm flex flex-col overflow-hidden">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-3">
              <div className="flex items-center gap-2">
                <ShieldAlert className="h-4 w-4 text-red-600" />
                <span className="text-xs font-semibold text-slate-900">Detected Signals</span>
              </div>
              <span
                className={cn(
                  "rounded px-2 py-0.5 text-[10px] font-semibold border",
                  activeSignals.length > 0
                    ? "bg-red-50 text-red-700 border-red-200"
                    : "bg-emerald-50 text-emerald-700 border-emerald-200"
                )}
              >
                {activeSignals.length} Flagged
              </span>
            </div>

            <div className="flex-1 overflow-y-auto space-y-2 pr-1">
              <AnimatePresence>
                {activeSignals.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-center text-slate-400">
                    {callEnded && scenario.expected_risk_score < 40 ? (
                      <div className="flex flex-col items-center">
                        <ShieldCheck className="h-8 w-8 text-emerald-500 mb-2" />
                        <span className="text-xs font-medium text-emerald-700">No Threat Signals Detected</span>
                        <span className="text-[11px] text-slate-500 mt-1">Interaction passed all biometric & conversational checks.</span>
                      </div>
                    ) : (
                      <span className="text-xs">Listening for conversational threat cues & spoof anomalies...</span>
                    )}
                  </div>
                ) : (
                  activeSignals.map((sig, i) => (
                    <SignalCard key={sig.id || i} signal={sig} index={i} />
                  ))
                )}
              </AnimatePresence>
            </div>
          </div>

          {/* Running Risk Score */}
          <div className="rounded-lg border border-slate-200 bg-white p-3.5 shadow-sm flex items-center justify-between">
            <div>
              <span className="text-[11px] font-medium text-slate-500 block">
                Calculated Risk Score
              </span>
              <div className="flex items-baseline gap-1">
                <span className="text-2xl font-bold text-slate-900">{currentScore}</span>
                <span className="text-xs text-slate-400">/ 100</span>
              </div>
            </div>
            <div>
              <span
                className={`rounded px-2.5 py-1 text-xs font-semibold uppercase tracking-wide border ${
                  currentScore >= 70
                    ? "bg-red-50 text-red-800 border-red-200"
                    : currentScore >= 40
                    ? "bg-amber-50 text-amber-800 border-amber-200"
                    : "bg-emerald-50 text-emerald-800 border-emerald-200"
                }`}
              >
                {currentScore >= 70 ? "High Risk" : currentScore >= 40 ? "Medium Risk" : "Low Risk"}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Warning Alert Banner (dynamically driven by scenario.warning_actions) */}
      <AnimatePresence>
        {showWarning && (
          <motion.div
            key="call-warning-banner"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
            transition={{ duration: 0.3 }}
          >
            <WarningBanner
              score={currentScore}
              actions={warningActions}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
