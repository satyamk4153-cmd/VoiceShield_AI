"use client";

import React from "react";

interface RiskBreakdownProps {
  breakdown: Record<string, number>;
}

export const RiskBreakdown: React.FC<RiskBreakdownProps> = ({ breakdown }) => {
  const entries = Object.entries(breakdown || {});

  if (entries.length === 0) {
    return (
      <div className="text-xs text-slate-500 py-3 text-center">
        No risk point breakdown items available.
      </div>
    );
  }

  return (
    <div className="space-y-2.5">
      {entries.map(([key, points]) => (
        <div key={key} className="space-y-1">
          <div className="flex items-center justify-between text-xs">
            <span className="font-medium text-slate-700 capitalize">{key.replace(/_/g, " ").toLowerCase()}</span>
            <span className="font-semibold text-red-600">+{points} pts</span>
          </div>
          <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden border border-slate-200">
            <div
              className="h-full bg-red-600 rounded-full"
              style={{ width: `${Math.min(100, (points / 30) * 100)}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
};
