"use client";

import React from "react";
import { FraudSignal } from "../lib/types";
import { AlertCircle, KeyRound, Building, Flame, CreditCard, Laptop, Award } from "lucide-react";
import { cn } from "../lib/utils";
import { motion } from "framer-motion";

interface SignalCardProps {
  signal: FraudSignal;
  index?: number;
}

export const SignalCard: React.FC<SignalCardProps> = ({ signal, index = 0 }) => {
  const getCategoryIcon = (cat: string) => {
    switch (cat.toUpperCase()) {
      case "AUTHENTICATION":
        return <KeyRound className="h-4 w-4 text-red-600" />;
      case "IMPERSONATION":
        return <Building className="h-4 w-4 text-blue-600" />;
      case "THREAT":
        return <Flame className="h-4 w-4 text-amber-600" />;
      case "FINANCIAL":
        return <CreditCard className="h-4 w-4 text-amber-700" />;
      case "TECHNICAL":
        return <Laptop className="h-4 w-4 text-sky-600" />;
      case "SCAM":
        return <Award className="h-4 w-4 text-indigo-600" />;
      default:
        return <AlertCircle className="h-4 w-4 text-red-600" />;
    }
  };

  const severityStyles = {
    CRITICAL: "border-red-200 bg-red-50 text-red-700",
    HIGH: "border-red-200 bg-red-50 text-red-700",
    MEDIUM: "border-amber-200 bg-amber-50 text-amber-700",
    LOW: "border-slate-200 bg-slate-50 text-slate-600",
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.2 }}
      className="rounded-lg border border-slate-200 bg-white p-3.5 shadow-sm hover:border-slate-300 transition-colors"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-2.5 min-w-0">
          <div className="rounded-md bg-slate-50 p-1.5 border border-slate-200 flex-shrink-0 mt-0.5">
            {getCategoryIcon(signal.category)}
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-1.5 flex-wrap">
              <h4 className="text-xs font-semibold text-slate-900 capitalize">
                {signal.signal_type.replace(/_/g, " ").toLowerCase()}
              </h4>
              {signal.timestamp && (
                <span className="rounded bg-slate-100 px-1.5 py-0.2 text-[10px] text-slate-500 font-mono">
                  {signal.timestamp}
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">{signal.description}</p>
          </div>
        </div>

        <div className="flex flex-col items-end gap-1 flex-shrink-0">
          <span className={cn("rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase border", severityStyles[signal.severity])}>
            {signal.severity}
          </span>
          <span className="text-xs font-semibold text-red-600">
            +{signal.risk_contribution}
          </span>
        </div>
      </div>

      {signal.detected_phrases && signal.detected_phrases.length > 0 && (
        <div className="mt-2.5 flex flex-wrap items-center gap-1 pt-2 border-t border-slate-100">
          <span className="text-[10px] text-slate-400 font-medium">Evidence:</span>
          {signal.detected_phrases.map((phrase, i) => (
            <span key={i} className="rounded bg-slate-50 px-1.5 py-0.5 text-[10px] text-slate-700 border border-slate-200">
              "{phrase}"
            </span>
          ))}
        </div>
      )}
    </motion.div>
  );
};
