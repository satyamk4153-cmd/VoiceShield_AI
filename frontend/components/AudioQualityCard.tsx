"use client";

import React from "react";
import { AudioQuality } from "../lib/types";
import { Activity, AlertCircle, CheckCircle2 } from "lucide-react";
import { cn } from "../lib/utils";

interface AudioQualityCardProps {
  audio: AudioQuality;
}

export const AudioQualityCard: React.FC<AudioQualityCardProps> = ({ audio }) => {
  const getQualityBadge = (level: string) => {
    switch (level) {
      case "GOOD":
        return { text: "text-emerald-700", bg: "bg-emerald-50 border-emerald-200", icon: CheckCircle2 };
      case "FAIR":
        return { text: "text-amber-800", bg: "bg-amber-50 border-amber-200", icon: AlertCircle };
      default:
        return { text: "text-red-700", bg: "bg-red-50 border-red-200", icon: AlertCircle };
    }
  };

  const badge = getQualityBadge(audio.quality_level);
  const Icon = badge.icon;

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
        <div className="flex items-center gap-2">
          <Activity className="h-4 w-4 text-blue-600" />
          <h3 className="text-sm font-semibold text-slate-900">Audio & Signal Quality</h3>
        </div>
        <div className={cn("flex items-center gap-1.5 px-2.5 py-0.5 rounded text-xs font-medium border", badge.bg, badge.text)}>
          <Icon className="h-3.5 w-3.5" />
          <span>{audio.quality_level} Quality</span>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 mb-4">
        <div className="rounded-md bg-slate-50 p-2.5 border border-slate-200">
          <span className="text-[10px] text-slate-500 uppercase font-medium">Sample Rate</span>
          <p className="text-sm font-semibold text-slate-900 mt-0.5">{audio.sample_rate} Hz</p>
        </div>

        <div className="rounded-md bg-slate-50 p-2.5 border border-slate-200">
          <span className="text-[10px] text-slate-500 uppercase font-medium">SNR Ratio</span>
          <p className="text-sm font-semibold text-slate-900 mt-0.5">{audio.snr_db} dB</p>
        </div>

        <div className="rounded-md bg-slate-50 p-2.5 border border-slate-200">
          <span className="text-[10px] text-slate-500 uppercase font-medium">Condition</span>
          <p className="text-sm font-semibold text-amber-700 mt-0.5">{audio.telephony_condition}</p>
        </div>

        <div className="rounded-md bg-slate-50 p-2.5 border border-slate-200">
          <span className="text-[10px] text-slate-500 uppercase font-medium">RMS Energy</span>
          <p className="text-sm font-semibold text-slate-900 mt-0.5">{audio.rms_energy}</p>
        </div>
      </div>

      {audio.quality_notes && audio.quality_notes.length > 0 && (
        <div className="rounded-md bg-slate-50 p-3 border border-slate-200">
          <span className="text-xs font-semibold text-slate-700 block mb-1">Signal Observations:</span>
          <ul className="space-y-1">
            {audio.quality_notes.map((note, i) => (
              <li key={i} className="text-xs text-slate-600 flex items-start gap-1.5">
                <span className="text-blue-600 mt-0.5">•</span>
                <span>{note}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
