"use client";

import React from "react";
import { AlertOctagon, PhoneOff, CheckCircle2, ShieldAlert } from "lucide-react";
import { motion } from "framer-motion";

interface WarningBannerProps {
  score: number;
  actions: string[];
}

export const WarningBanner: React.FC<WarningBannerProps> = ({ score, actions }) => {
  if (score < 40) {
    return (
      <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-emerald-900">
        <div className="flex items-center gap-2.5 mb-1.5">
          <CheckCircle2 className="h-5 w-5 text-emerald-600 flex-shrink-0" />
          <h3 className="text-sm font-semibold text-emerald-900">Call Profile: Low Risk</h3>
        </div>
        <p className="text-xs text-emerald-700">
          No significant fraud indicators or voice anomalies were detected during this interaction.
        </p>
      </div>
    );
  }

  const isCritical = score >= 70;

  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      className={`rounded-lg border p-5 ${
        isCritical
          ? "border-red-200 bg-red-50 text-red-950"
          : "border-amber-200 bg-amber-50 text-amber-950"
      }`}
    >
      <div className="flex items-start gap-3.5">
        <div
          className={`rounded-md p-2 flex-shrink-0 ${
            isCritical ? "bg-red-100 text-red-600" : "bg-amber-100 text-amber-700"
          }`}
        >
          {isCritical ? <PhoneOff className="h-5 w-5" /> : <ShieldAlert className="h-5 w-5" />}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span
              className={`rounded px-2 py-0.5 text-[11px] font-semibold tracking-wide uppercase ${
                isCritical ? "bg-red-200 text-red-900" : "bg-amber-200 text-amber-900"
              }`}
            >
              {isCritical ? "High Risk Detected" : "Elevated Risk Caution"}
            </span>
            <span className="text-xs text-slate-500 font-medium">
              Score: {score}/100
            </span>
          </div>

          <h3 className="text-sm font-bold text-slate-900">
            {isCritical
              ? "Potential Fraud or Impersonation in Progress"
              : "Unverified Call Claim Detected"}
          </h3>

          <p className="text-xs text-slate-600 mt-0.5 leading-relaxed">
            {isCritical
              ? "Suspicious pattern matches high-risk social engineering or unauthorized identity claims."
              : "Review caller claims carefully before sharing sensitive personal or security information."}
          </p>

          {actions && actions.length > 0 && (
            <div className="mt-3 pt-3 border-t border-red-200/60">
              <span className="text-[11px] font-semibold text-slate-700 block mb-1.5">
                Recommended Actions:
              </span>
              <ul className="space-y-1">
                {actions.map((act, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs text-slate-800">
                    <span className="font-semibold text-red-600 flex-shrink-0">{i + 1}.</span>
                    <span>{act}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};
