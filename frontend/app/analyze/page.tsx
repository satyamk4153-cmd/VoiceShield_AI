"use client";

import React, { useState } from "react";
import Link from "next/link";
import { PageHeader } from "../../components/PageHeader";
import { GlassCard } from "../../components/GlassCard";
import {
  Upload,
  Mic,
  FileAudio,
  ArrowRight,
  Loader2,
  AlertTriangle,
  ShieldCheck,
  FileText,
} from "lucide-react";
import { ApiClient } from "../../lib/api";
import { FinalAnalysisResponse } from "../../lib/types";
import { RiskScore } from "../../components/RiskScore";
import { FraudSignals } from "../../components/FraudSignals";
import { AudioQualityCard } from "../../components/AudioQualityCard";
import { SpeakerMatchCard } from "../../components/SpeakerMatchCard";
import { WarningBanner } from "../../components/WarningBanner";
import { AnimatedPipeline } from "../../components/AnimatedPipeline";

export default function AnalyzePage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [referenceFile, setReferenceFile] = useState<File | null>(null);
  const [transcript, setTranscript] = useState<string>(
    "Hello Rajesh from HDFC Bank Security. Your debit card was used for 48500 rupees fraud. Your account will be blocked in 5 minutes unless you give me the 6 digit OTP now."
  );
  const [callerClaimed, setCallerClaimed] = useState<string>("HDFC Bank Security Desk");
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [analysisStage, setAnalysisStage] = useState<number>(0);
  const [result, setResult] = useState<FinalAnalysisResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleFileDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleAudioSelection(e.dataTransfer.files[0]);
    }
  };

  const handleAudioSelection = (file: File) => {
    if (file.size > 25 * 1024 * 1024) {
      setErrorMessage("File exceeds maximum allowed upload size of 25MB.");
      return;
    }
    const ext = file.name.split(".").pop()?.toLowerCase();
    if (!["wav", "mp3", "ogg", "m4a", "flac"].includes(ext || "")) {
      setErrorMessage("Unsupported file format. Please upload WAV, MP3, OGG, M4A, or FLAC.");
      return;
    }
    setErrorMessage(null);
    setSelectedFile(file);
  };

  const handleAnalyze = async () => {
    setIsAnalyzing(true);
    setErrorMessage(null);
    setResult(null);
    setAnalysisStage(1);

    try {
      let response: FinalAnalysisResponse;
      if (selectedFile) {
        setAnalysisStage(2);
        const formData = new FormData();
        formData.append("audio_file", selectedFile);
        if (transcript.trim()) formData.append("transcript", transcript.trim());
        if (callerClaimed.trim()) formData.append("caller_claimed", callerClaimed.trim());
        if (referenceFile) formData.append("reference_audio", referenceFile);

        setAnalysisStage(3);
        response = await ApiClient.analyzeAudio(formData);
      } else {
        setAnalysisStage(4);
        response = await ApiClient.analyzeTranscript(transcript.trim(), callerClaimed.trim());
      }

      setAnalysisStage(6);
      setResult(response);
    } catch (err: any) {
      setErrorMessage(err.message || "An unexpected error occurred during security analysis.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        badge="Threat Detection Engine"
        badgeVariant="indigo"
        title="Telephony Threat Analysis"
        description="Submit telephony audio recordings or conversational transcripts to evaluate voice authenticity, 1:1 speaker identity, and conversational fraud indicators."
      />

      {/* Upload and Form Controls */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Audio Dropzone & Reference */}
        <div className="lg:col-span-6 space-y-4">
          <GlassCard className="p-5 space-y-4">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-700 flex items-center gap-2">
              <FileAudio className="h-4 w-4 text-blue-600" />
              1. Audio Recording (Optional if Transcript Provided)
            </h3>

            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleFileDrop}
              className="border-2 border-dashed border-slate-300 hover:border-blue-500 rounded-lg p-6 text-center cursor-pointer transition-colors bg-slate-50/60 relative"
            >
              <input
                type="file"
                accept=".wav,.mp3,.ogg,.m4a,.flac"
                onChange={(e) => e.target.files && handleAudioSelection(e.target.files[0])}
                className="absolute inset-0 opacity-0 cursor-pointer"
              />
              <Upload className="h-7 w-7 text-slate-400 mx-auto mb-2" />
              <p className="text-xs font-semibold text-slate-800">
                {selectedFile ? selectedFile.name : "Drag & drop audio file or click to select"}
              </p>
              <p className="text-[11px] text-slate-500 mt-1">
                Supported formats: WAV, MP3, OGG, M4A, FLAC (Max: 25MB). Auto-transcribed via Speech-to-Text.
              </p>
            </div>

            {selectedFile && (
              <div className="rounded-md bg-slate-50 p-2.5 border border-slate-200 flex items-center justify-between text-xs">
                <span className="text-slate-800 font-medium truncate max-w-[240px]">{selectedFile.name}</span>
                <span className="text-blue-600 font-mono">{(selectedFile.size / (1024 * 1024)).toFixed(2)} MB</span>
              </div>
            )}

            {/* Optional Reference Profile */}
            <div className="pt-2 border-t border-slate-100 space-y-2">
              <label className="text-[11px] font-medium text-slate-600 block">
                Reference Audio Sample for 1:1 Speaker Verification (Optional):
              </label>
              <input
                type="file"
                accept=".wav,.mp3"
                onChange={(e) => e.target.files && setReferenceFile(e.target.files[0])}
                className="text-xs text-slate-600 file:mr-3 file:py-1 file:px-2.5 file:rounded file:border file:border-slate-200 file:text-xs file:font-semibold file:bg-white file:text-slate-700 hover:file:bg-slate-50 cursor-pointer"
              />
            </div>
          </GlassCard>
        </div>

        {/* Right: Transcript Input & Metadata */}
        <div className="lg:col-span-6 space-y-4">
          <GlassCard className="p-5 space-y-4">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-700 flex items-center gap-2">
              <Mic className="h-4 w-4 text-blue-600" />
              2. Transcript & Claimed Identity
            </h3>

            <div className="space-y-1">
              <label className="text-xs font-medium text-slate-700">Claimed Organization or Identity:</label>
              <input
                type="text"
                value={callerClaimed}
                onChange={(e) => setCallerClaimed(e.target.value)}
                placeholder="e.g. HDFC Bank Security Desk, Police Cyber Cell"
                className="w-full rounded-md bg-white border border-slate-300 px-3 py-2 text-xs text-slate-900 focus:border-blue-600 focus:outline-none"
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs font-medium text-slate-700">
                Call Transcript (English / Hindi / Hinglish):
              </label>
              <textarea
                rows={4}
                value={transcript}
                onChange={(e) => setTranscript(e.target.value)}
                placeholder="Enter what the caller said during the interaction..."
                className="w-full rounded-md bg-white border border-slate-300 p-3 text-xs text-slate-900 focus:border-blue-600 focus:outline-none leading-relaxed"
              />
            </div>

            <button
              disabled={isAnalyzing || (!selectedFile && !transcript.trim())}
              onClick={handleAnalyze}
              className="w-full flex items-center justify-center gap-2 rounded-md bg-blue-600 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Processing Threat Pipeline...</span>
                </>
              ) : (
                <>
                  <ShieldCheck className="h-4 w-4" />
                  <span>Execute Threat Analysis</span>
                </>
              )}
            </button>
          </GlassCard>
        </div>
      </div>

      {/* Progress Pipeline */}
      {isAnalyzing && (
        <GlassCard className="p-5">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-600 mb-3 text-center">
            Multi-Modal Analysis In Progress
          </h4>
          <AnimatedPipeline currentStageIndex={analysisStage} />
        </GlassCard>
      )}

      {/* Error Message */}
      {errorMessage && (
        <div className="rounded-md border border-red-200 bg-red-50 p-3.5 text-xs text-red-700 flex items-center gap-2.5">
          <AlertTriangle className="h-4 w-4 text-red-600 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Result Display */}
      {result && (
        <div className="space-y-6 pt-4 border-t border-slate-200">
          <div className="rounded-lg bg-white border border-slate-200 p-4 flex flex-wrap items-center justify-between gap-3 shadow-sm">
            <div className="text-xs">
              <span className="text-slate-500">Evaluation ID: </span>
              <span className="font-mono font-bold text-slate-900">{result.analysis_id}</span>
            </div>
            <div>
              <Link
                href={`/result?id=${result.analysis_id}`}
                className="inline-flex items-center gap-1.5 rounded-md bg-blue-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-blue-700 transition-colors shadow-sm"
              >
                <FileText className="h-3.5 w-3.5" />
                <span>Forensic Summary</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left: Score & Decision */}
            <div className="lg:col-span-4 space-y-4">
              <GlassCard className="p-5 flex flex-col items-center justify-center text-center space-y-2">
                <RiskScore
                  score={result.risk.score}
                  level={result.risk.level}
                  decision={result.risk.decision}
                  size="hero"
                />
                <div className="w-full pt-3 border-t border-slate-100 text-xs text-slate-500 flex justify-between">
                  <span>Policy Determination:</span>
                  <span className="text-slate-900 font-semibold">{result.risk.decision}</span>
                </div>
              </GlassCard>

              {result.audio && <AudioQualityCard audio={result.audio} />}
            </div>

            {/* Right: Speaker, Signals, and Advisory */}
            <div className="lg:col-span-8 space-y-4">
              {result.speaker && <SpeakerMatchCard speaker={result.speaker} />}

              <div className="space-y-2.5">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-700">
                  Extracted Fraud Signals ({result.fraud_signals.length})
                </h3>
                <FraudSignals signals={result.fraud_signals} />
              </div>

              {result.recommended_actions && (
                <WarningBanner score={result.risk.score} actions={result.recommended_actions} />
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
