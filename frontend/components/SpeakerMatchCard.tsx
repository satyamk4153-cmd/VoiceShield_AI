"use client";

import React from "react";
import { SpeakerVerification } from "@/lib/types";
import { UserCheck, UserX, HelpCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface SpeakerMatchCardProps {
  speaker: SpeakerVerification;
}

export const SpeakerMatchCard: React.FC<SpeakerMatchCardProps> = ({ speaker }) => {
  const getResultBadge = () => {
    switch (speaker.result) {
      case "MATCH":
        return {
          text: "text-emerald-700",
          bg: "bg-emerald-50 border-emerald-200",
          icon: UserCheck,
          label: "Verified Speaker Match",
        };
      case "MISMATCH":
        return {
          text: "text-red-700",
          bg: "bg-red-50 border-red-200",
          icon: UserX,
          label: "Speaker Mismatch Detected",
        };
      default:
        return {
          text: "text-amber-800",
          bg: "bg-amber-50 border-amber-200",
          icon: HelpCircle,
          label: "Inconclusive Baseline",
        };
    }
  };

  const badge = getResultBadge();
  const Icon = badge.icon;

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
        <div className="flex items-center gap-2">
          <Icon className={cn("h-4 w-4", badge.text)} />
          <h3 className="text-sm font-semibold text-slate-900">1:1 Speaker Verification</h3>
        </div>
        <div className={cn("flex items-center gap-1.5 px-2.5 py-0.5 rounded text-xs font-medium border", badge.bg, badge.text)}>
          <span>{badge.label}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
        <div className="rounded-md bg-slate-50 p-3 border border-slate-200">
          <div className="flex justify-between items-center mb-1">
            <span className="text-[11px] text-slate-500 font-medium">Acoustic Similarity</span>
            <span className="text-xs font-bold text-slate-900">{(speaker.similarity * 100).toFixed(1)}%</span>
          </div>
          <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden mt-2">
            <div
              className={cn("h-full rounded-full", speaker.similarity > 0.7 ? "bg-emerald-600" : "bg-red-600")}
              style={{ width: `${Math.min(100, speaker.similarity * 100)}%` }}
            />
          </div>
        </div>

        <div className="rounded-md bg-slate-50 p-3 border border-slate-200">
          <div className="flex justify-between items-center mb-1">
            <span className="text-[11px] text-slate-500 font-medium">Verification Confidence</span>
            <span className="text-xs font-bold text-slate-900">{(speaker.confidence * 100).toFixed(0)}%</span>
          </div>
          <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden mt-2">
            <div
              className="h-full bg-blue-600 rounded-full"
              style={{ width: `${Math.min(100, speaker.confidence * 100)}%` }}
            />
          </div>
        </div>
      </div>

      <p className="text-xs text-slate-600 bg-slate-50 p-3 rounded-md border border-slate-200 leading-relaxed">
        {speaker.explanation}
      </p>
    </div>
  );
};
