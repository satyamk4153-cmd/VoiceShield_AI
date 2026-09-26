"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { PageHeader } from "@/components/PageHeader";
import { GlassCard } from "@/components/GlassCard";
import { RiskScore } from "@/components/RiskScore";
import { AudioQualityCard } from "@/components/AudioQualityCard";
import { SpeakerMatchCard } from "@/components/SpeakerMatchCard";
import { WarningBanner } from "@/components/WarningBanner";
import { FraudSignals } from "@/components/FraudSignals";
import { FinalAnalysisResponse } from "@/lib/types";
import { ApiClient } from "@/lib/api";
import {
  Download,
  Share2,
  ArrowRight,
  Loader2,
  AlertTriangle,
  Search,
  PhoneCall,
  FileText,
} from "lucide-react";

function ResultContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const idFromQuery = searchParams.get("id");
  const scenarioFromQuery = searchParams.get("scenario");

  const [analysisId, setAnalysisId] = useState<string>(idFromQuery || (scenarioFromQuery ? `DEMO-${scenarioFromQuery}` : ""));
  const [searchInput, setSearchInput] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(Boolean(idFromQuery || scenarioFromQuery));
  const [error, setError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<FinalAnalysisResponse | null>(null);

  useEffect(() => {
    if (scenarioFromQuery) {
      fetchScenarioAnalysis(scenarioFromQuery);
    } else if (idFromQuery) {
      setAnalysisId(idFromQuery);
      fetchAnalysis(idFromQuery);
    } else {
      setLoading(false);
    }
  }, [scenarioFromQuery, idFromQuery]);

  const fetchScenarioAnalysis = async (scId: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await ApiClient.getDemoScenarioAnalysis(scId);
      setAnalysis(data);
    } catch (err: any) {
      setError(err.message || `Scenario analysis for '${scId}' could not be generated.`);
      setAnalysis(null);
    } finally {
      setLoading(false);
    }
  };

  const fetchAnalysis = async (targetId: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await ApiClient.getAnalysisById(targetId);
      setAnalysis(data);
    } catch (err: any) {
      setError(err.message || `Analysis record '${targetId}' could not be retrieved from database.`);
      setAnalysis(null);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchInput.trim()) return;
    router.push(`/result?id=${encodeURIComponent(searchInput.trim())}`);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        badge="Forensic Evaluation Report"
        badgeVariant="indigo"
        title="Telephony Security Evaluation Report"
        description="Comprehensive evaluation record covering acoustic anti-spoofing, 1:1 speaker identity baseline, and semantic conversational fraud signals."
      />

      {/* Analysis ID Lookup Bar */}
      <form onSubmit={handleSearch} className="flex gap-2 max-w-xl">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search by Analysis ID (e.g. ANL-...) or Session ID"
            className="w-full rounded-md bg-white border border-slate-300 pl-9 pr-3 py-2 text-xs text-slate-900 placeholder:text-slate-400 focus:border-blue-600 focus:outline-none"
          />
        </div>
        <button
          type="submit"
          className="rounded-md bg-white border border-slate-300 px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-sm"
        >
          Load Report
        </button>
      </form>

      {/* Loading State */}
      {loading && (
        <div className="h-64 flex flex-col items-center justify-center text-center space-y-2">
          <Loader2 className="h-7 w-7 text-blue-600 animate-spin" />
          <p className="text-xs text-slate-500">
            Querying forensic record from storage...
          </p>
        </div>
      )}

      {/* Error Banner */}
      {!loading && error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center space-y-3">
          <AlertTriangle className="h-8 w-8 text-red-600 mx-auto" />
          <div className="space-y-1">
            <h3 className="text-sm font-semibold text-red-900">Record Not Found</h3>
            <p className="text-xs text-red-700 max-w-md mx-auto">{error}</p>
          </div>
          <Link
            href="/analyze"
            className="inline-flex items-center gap-1.5 rounded-md bg-blue-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-blue-700 transition-colors shadow-sm"
          >
            <PhoneCall className="h-3.5 w-3.5" />
            <span>Submit New Audio Analysis</span>
          </Link>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && !analysis && (
        <div className="rounded-lg border border-slate-200 bg-white p-10 text-center space-y-3 shadow-sm">
          <FileText className="h-10 w-10 text-slate-300 mx-auto" />
          <h3 className="text-sm font-semibold text-slate-900">No Analysis Record Selected</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Enter an Analysis ID above or complete a call analysis to review detailed forensic evidence.
          </p>
          <div className="pt-2">
            <Link
              href="/analyze"
              className="inline-flex items-center gap-1.5 rounded-md bg-blue-600 px-4 py-2 text-xs font-semibold text-white hover:bg-blue-700 transition-colors shadow-sm"
            >
              <span>Analyze New Recording</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>
      )}

      {/* Loaded Analysis Report */}
      {!loading && analysis && (
        <div className="space-y-6">
          {/* Header Action Bar */}
          <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-bold text-blue-700">
                  {analysis.analysis_id}
                </span>
                <span className="rounded bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-700 border border-slate-200">
                  Tamper-Evident Report
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Session: {analysis.session_id} • Ingested: {analysis.created_at ? new Date(analysis.created_at).toLocaleString() : "Recent"}
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => {
                  navigator.clipboard.writeText(window.location.href);
                  alert("Report link copied to clipboard.");
                }}
                className="inline-flex items-center gap-1.5 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 transition-colors shadow-sm"
              >
                <Share2 className="h-3.5 w-3.5" />
                <span>Share</span>
              </button>

              <button
                onClick={() => window.print()}
                className="inline-flex items-center gap-1.5 rounded-md bg-blue-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-blue-700 transition-colors shadow-sm"
              >
                <Download className="h-3.5 w-3.5" />
                <span>Print PDF</span>
              </button>
            </div>
          </div>

          {/* Grid View */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left Column: Risk & Audio */}
            <div className="lg:col-span-4 space-y-4">
              <GlassCard className="p-5 flex flex-col items-center justify-center text-center space-y-2">
                <RiskScore
                  score={analysis.risk.score}
                  level={analysis.risk.level}
                  decision={analysis.risk.decision}
                  size="hero"
                />
                <div className="w-full pt-3 border-t border-slate-100 text-xs text-slate-500 flex justify-between">
                  <span>Policy Outcome:</span>
                  <span className="text-slate-900 font-semibold">{analysis.risk.decision}</span>
                </div>
              </GlassCard>

              {analysis.audio && <AudioQualityCard audio={analysis.audio} />}
            </div>

            {/* Right Column: Speaker Verification, Intent, Evidence */}
            <div className="lg:col-span-8 space-y-4">
              {analysis.speaker && <SpeakerMatchCard speaker={analysis.speaker} />}

              {/* Transcript Review Card */}
              {analysis.transcript && (
                <GlassCard className="p-5 space-y-2">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                    <span className="text-xs font-semibold text-slate-700">Call Transcript</span>
                    {analysis.caller_claimed_identity && (
                      <span className="text-xs text-slate-500">
                        Claimed: <strong className="text-slate-900">{analysis.caller_claimed_identity}</strong>
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-700 leading-relaxed font-sans bg-slate-50 p-3 rounded-md border border-slate-200">
                    &ldquo;{analysis.transcript}&rdquo;
                  </p>
                </GlassCard>
              )}

              {/* Signals List */}
              <div className="space-y-2.5">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-700">
                  Extracted Threat Indicators ({analysis.fraud_signals.length})
                </h3>
                <FraudSignals signals={analysis.fraud_signals} />
              </div>

              {analysis.recommended_actions && (
                <WarningBanner score={analysis.risk.score} actions={analysis.recommended_actions} />
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ResultPage() {
  return (
    <Suspense
      fallback={
        <div className="h-64 flex flex-col items-center justify-center text-center space-y-2">
          <Loader2 className="h-7 w-7 text-blue-600 animate-spin" />
          <span className="text-xs text-slate-500">Loading evaluation report...</span>
        </div>
      }
    >
      <ResultContent />
    </Suspense>
  );
}
