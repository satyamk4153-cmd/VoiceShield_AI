"use client";

import React, { useState } from "react";
import { DemoScenario } from "../lib/types";
import { GlassCard } from "../components/GlassCard";
import { Play, ArrowRight } from "lucide-react";
import { cn } from "../lib/utils";
import Link from "next/link";

interface DemoPlayerProps {
  scenarios: DemoScenario[];
  onSelectScenario?: (scenario: DemoScenario) => void;
}

export const DemoPlayer: React.FC<DemoPlayerProps> = ({ scenarios, onSelectScenario }) => {
  const [selectedId, setSelectedId] = useState<string>(scenarios[0]?.id || "bank-otp-scam");

  const selected = scenarios.find((s) => s.id === selectedId) || scenarios[0];

  const getScoreBadge = (score: number) => {
    if (score >= 70) {
      return "border-red-200 bg-red-50 text-red-700";
    }
    if (score >= 40) {
      return "border-amber-200 bg-amber-50 text-amber-800";
    }
    return "border-emerald-200 bg-emerald-50 text-emerald-700";
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {scenarios.map((sc) => {
          const isSelected = sc.id === selectedId;

          return (
            <div
              key={sc.id}
              onClick={() => {
                setSelectedId(sc.id);
                if (onSelectScenario) onSelectScenario(sc);
              }}
              className={cn(
                "rounded-lg border p-4 cursor-pointer transition-all shadow-sm bg-white",
                isSelected
                  ? "border-blue-600 ring-1 ring-blue-600 bg-blue-50/20"
                  : "border-slate-200 hover:border-slate-300"
              )}
            >
              <div className="flex items-start justify-between gap-2 mb-2">
                <span className="rounded bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-600 border border-slate-200">
                  {sc.category.replace(/_/g, " ")}
                </span>
                <span className={cn("rounded px-2 py-0.5 text-xs font-semibold border", getScoreBadge(sc.expected_risk_score))}>
                  {sc.expected_risk_score}/100 {sc.expected_risk_level}
                </span>
              </div>

              <h4 className="text-sm font-semibold text-slate-900 mb-1">{sc.name}</h4>
              <p className="text-xs text-slate-500 line-clamp-2 leading-relaxed mb-3">
                {sc.description}
              </p>

              <div className="flex items-center justify-between pt-2.5 border-t border-slate-100 text-xs">
                <span className="text-slate-500 truncate max-w-[170px]">
                  Claimed: <span className="text-slate-800 font-medium">{sc.caller_claimed}</span>
                </span>
                <span className="text-blue-600 font-semibold flex items-center gap-1">
                  Select <ArrowRight className="h-3 w-3" />
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Selected Scenario Detailed Panel */}
      {selected && (
        <div className="rounded-lg border border-slate-200 bg-white p-5 sm:p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 pb-4 mb-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Scenario Overview
                </span>
                <span className="rounded bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-600 border border-slate-200">
                  Pre-configured Sandbox
                </span>
              </div>
              <h3 className="text-lg font-bold text-slate-900 mt-1">{selected.name}</h3>
            </div>

            <div className="flex items-center gap-3">
              <Link
                href={`/live?scenario=${encodeURIComponent(selected.id)}`}
                className="flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-blue-700 transition-colors"
              >
                <Play className="h-3.5 w-3.5 fill-current" />
                <span>Simulate Call In SOC</span>
              </Link>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <span className="text-xs font-semibold text-slate-700 block mb-1">
                Scenario Dialogue Script:
              </span>
              <div className="rounded-md bg-slate-50 p-3.5 border border-slate-200 text-xs text-slate-800 leading-relaxed font-sans">
                &ldquo;{selected.transcript}&rdquo;
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="p-2.5 rounded bg-slate-50 border border-slate-200">
                <span className="text-slate-400 block text-[10px] font-medium uppercase">Expected Risk</span>
                <span className="font-bold text-red-600 mt-0.5 block">{selected.expected_risk_score}/100</span>
              </div>
              <div className="p-2.5 rounded bg-slate-50 border border-slate-200">
                <span className="text-slate-400 block text-[10px] font-medium uppercase">Voice Spoof Prob</span>
                <span className="font-bold text-slate-800 mt-0.5 block">{(selected.voice_spoof_prob * 100).toFixed(0)}%</span>
              </div>
              <div className="p-2.5 rounded bg-slate-50 border border-slate-200">
                <span className="text-slate-400 block text-[10px] font-medium uppercase">Speaker Match</span>
                <span className="font-bold text-slate-800 mt-0.5 block">{(selected.speaker_similarity * 100).toFixed(0)}%</span>
              </div>
              <div className="p-2.5 rounded bg-slate-50 border border-slate-200">
                <span className="text-slate-400 block text-[10px] font-medium uppercase">Primary Threat</span>
                <span className="font-bold text-slate-800 mt-0.5 block truncate">{selected.category}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
