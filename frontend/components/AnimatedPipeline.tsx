"use client";

import React from "react";
import { motion } from "framer-motion";
import { PhoneCall, Activity, ShieldCheck, UserCheck, MessageSquareWarning, Flame, Cpu, AlertOctagon, Check } from "lucide-react";
import { cn } from "@/lib/utils";

interface PipelineStep {
  id: string;
  name: string;
  category: string;
  icon: React.ComponentType<{ className?: string }>;
  detail: string;
}

interface AnimatedPipelineProps {
  currentStageIndex?: number;
}

export const AnimatedPipeline: React.FC<AnimatedPipelineProps> = ({
  currentStageIndex = 7,
}) => {
  const steps: PipelineStep[] = [
    {
      id: "audio_in",
      name: "Telephony Audio",
      category: "Inbound Stream",
      icon: PhoneCall,
      detail: "8kHz PSTN / GSM Signal",
    },
    {
      id: "quality",
      name: "Audio Quality",
      category: "Acoustics",
      icon: Activity,
      detail: "SNR & Telephony Check",
    },
    {
      id: "anti_spoof",
      name: "Voice Anti-Spoof",
      category: "Deepfake Check",
      icon: ShieldCheck,
      detail: "Synthetic Artifact Scan",
    },
    {
      id: "speaker",
      name: "Speaker Verification",
      category: "Biometric 1:1",
      icon: UserCheck,
      detail: "Enrolled Profile Comparison",
    },
    {
      id: "intent",
      name: "Fraud Intent",
      category: "Semantic NLP",
      icon: MessageSquareWarning,
      detail: "OTP & Impersonation",
    },
    {
      id: "context",
      name: "Context Signals",
      category: "Behavioral",
      icon: Flame,
      detail: "Urgency & Threat Coercion",
    },
    {
      id: "fusion",
      name: "Risk Fusion",
      category: "Decision Engine",
      icon: Cpu,
      detail: "Multi-Modal Matrix",
    },
    {
      id: "action",
      name: "Advisory Action",
      category: "Policy Outcome",
      icon: AlertOctagon,
      detail: "Action Code & Advisory",
    },
  ];

  return (
    <div className="w-full overflow-x-auto pb-2 pt-1">
      <div className="flex items-center min-w-[880px] justify-between gap-1 relative px-1">
        {steps.map((step, idx) => {
          const Icon = step.icon;
          const isDone = idx <= currentStageIndex;
          const isCurrent = idx === currentStageIndex;

          return (
            <React.Fragment key={step.id}>
              <motion.div
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.04 }}
                className={cn(
                  "flex flex-col items-center text-center p-3 rounded-lg border transition-all w-28 flex-shrink-0 relative bg-white",
                  isDone
                    ? "border-slate-300 shadow-sm"
                    : "border-slate-200 opacity-60",
                  isCurrent && "border-blue-600 bg-blue-50/30 ring-1 ring-blue-600"
                )}
              >
                <div
                  className={cn(
                    "flex h-8 w-8 items-center justify-center rounded-md mb-2 border",
                    isDone ? "bg-blue-50 text-blue-600 border-blue-100" : "bg-slate-50 text-slate-400 border-slate-200"
                  )}
                >
                  <Icon className="h-4 w-4" />
                </div>

                <span className="text-[10px] font-medium text-slate-400 uppercase tracking-wider">
                  {step.category}
                </span>
                <span className="text-xs font-semibold text-slate-900 mt-0.5 leading-tight line-clamp-1">
                  {step.name}
                </span>
                <span className="text-[10px] text-slate-500 mt-0.5 line-clamp-1">
                  {step.detail}
                </span>

                {isDone && (
                  <div className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-emerald-600 text-white shadow-sm">
                    <Check className="h-2.5 w-2.5 stroke-[3]" />
                  </div>
                )}
              </motion.div>

              {idx < steps.length - 1 && (
                <div className="flex-1 flex items-center justify-center">
                  <div
                    className={cn(
                      "h-[2px] w-full transition-colors",
                      idx < currentStageIndex ? "bg-blue-600" : "bg-slate-200"
                    )}
                  />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
