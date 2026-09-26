"use client";

import React from "react";
import { EvidenceItem } from "../lib/types";
import { motion } from "framer-motion";
import { Clock, ShieldAlert, Cpu, UserX, AlertTriangle, KeyRound } from "lucide-react";

interface EvidenceTimelineProps {
  evidence: EvidenceItem[];
}

export const EvidenceTimeline: React.FC<EvidenceTimelineProps> = ({ evidence }) => {
  const getIcon = (category: string) => {
    switch (category.toUpperCase()) {
      case "AUTHENTICATION":
        return <KeyRound className="h-3.5 w-3.5 text-red-600" />;
      case "BIOMETRIC":
        return <UserX className="h-3.5 w-3.5 text-amber-700" />;
      case "SYNTHETIC_AUDIO":
        return <Cpu className="h-3.5 w-3.5 text-blue-600" />;
      case "THREAT":
        return <ShieldAlert className="h-3.5 w-3.5 text-red-600" />;
      default:
        return <AlertTriangle className="h-3.5 w-3.5 text-slate-600" />;
    }
  };

  return (
    <div className="relative pl-6 space-y-4 before:absolute before:left-[11px] before:top-2 before:bottom-2 before:w-[2px] before:bg-slate-200">
      {evidence.map((item, index) => (
        <motion.div
          key={item.id}
          initial={{ opacity: 0, x: -8 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: index * 0.05, duration: 0.2 }}
          className="relative flex items-start gap-3"
        >
          {/* Node Dot */}
          <div className="absolute -left-[30px] top-1.5 flex h-6 w-6 items-center justify-center rounded-full bg-white border-2 border-blue-600 shadow-sm">
            {getIcon(item.category)}
          </div>

          {/* Card Body */}
          <div className="flex-1 rounded-lg border border-slate-200 bg-white p-3.5 shadow-sm space-y-1.5">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="flex items-center gap-1 rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-mono text-slate-600">
                  <Clock className="h-3 w-3" />
                  {item.timestamp}
                </span>
                <h4 className="text-xs font-semibold text-slate-900">{item.title}</h4>
              </div>

              <div>
                <span className="text-xs font-semibold text-red-600">
                  +{item.contribution_points} Risk Points
                </span>
              </div>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">{item.explanation}</p>

            <div className="pt-1 flex items-center gap-2 text-[10px] text-slate-400">
              <span className="uppercase font-medium">Category:</span>
              <span className="text-slate-600 font-medium">{item.category}</span>
            </div>
          </div>
        </motion.div>
      ))}
    </div>
  );
};
