"use client";

import React from "react";
import { FraudSignal } from "../lib/types";
import { SignalCard } from "../components/SignalCard";
import { ShieldCheck } from "lucide-react";

interface FraudSignalsProps {
  signals: FraudSignal[];
}

export const FraudSignals: React.FC<FraudSignalsProps> = ({ signals }) => {
  if (!signals || signals.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-lg border border-slate-200 bg-white p-8 text-center shadow-sm">
        <ShieldCheck className="h-8 w-8 text-emerald-600 mb-2" />
        <h4 className="text-sm font-semibold text-slate-900">No Conversational Fraud Signals Detected</h4>
        <p className="text-xs text-slate-500 mt-1 max-w-sm">
          No OTP solicitations, authority impersonation, financial extortion, or coercive pressure tactics identified.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2.5">
      {signals.map((sig, index) => (
        <SignalCard key={sig.id} signal={sig} index={index} />
      ))}
    </div>
  );
};
