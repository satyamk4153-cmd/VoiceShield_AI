"use client";

import React, { useEffect, useState } from "react";
import { useSpring, useTransform } from "framer-motion";
import { cn, getRiskColor } from "../lib/utils";
import { ShieldAlert, ShieldCheck, AlertTriangle } from "lucide-react";

interface RiskScoreProps {
  score: number;
  level: string;
  decision?: string;
  size?: "sm" | "md" | "lg" | "hero";
  animate?: boolean;
}

export const RiskScore: React.FC<RiskScoreProps> = ({
  score,
  level,
  decision,
  size = "md",
  animate = true,
}) => {
  const spring = useSpring(0, { stiffness: 45, damping: 15 });
  const displayScore = useTransform(spring, (current) => Math.round(current));
  const [renderedValue, setRenderedValue] = useState(0);

  useEffect(() => {
    if (animate) {
      spring.set(score);
    } else {
      spring.jump(score);
    }
    const unsubscribe = displayScore.on("change", (latest) => {
      setRenderedValue(latest);
    });
    return () => unsubscribe();
  }, [score, animate, spring, displayScore]);

  const colors = getRiskColor(score);

  const sizeClasses = {
    sm: "text-2xl font-bold",
    md: "text-4xl font-bold",
    lg: "text-5xl font-extrabold",
    hero: "text-6xl sm:text-7xl font-extrabold",
  };

  const getIcon = () => {
    if (score >= 70) return <ShieldAlert className="h-5 w-5 text-red-600" />;
    if (score >= 40) return <AlertTriangle className="h-5 w-5 text-amber-600" />;
    return <ShieldCheck className="h-5 w-5 text-emerald-600" />;
  };

  return (
    <div className="flex flex-col items-center justify-center text-center p-3">
      <div className="flex items-center gap-1.5 mb-1 text-slate-500">
        {getIcon()}
        <span className="text-xs font-medium uppercase tracking-wider">
          Risk Score
        </span>
      </div>

      <div className="flex items-baseline justify-center">
        <span className={cn("tracking-tight font-sans transition-colors duration-300", sizeClasses[size], colors.text)}>
          {renderedValue}
        </span>
        <span className="text-lg sm:text-xl font-medium text-slate-400 ml-1">/100</span>
      </div>

      <div className="mt-2.5 flex items-center gap-1.5 flex-wrap justify-center">
        <span
          className={cn(
            "rounded px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide border",
            colors.badge
          )}
        >
          {level} Risk
        </span>

        {decision && (
          <span className="rounded bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700 border border-slate-200">
            {decision}
          </span>
        )}
      </div>
    </div>
  );
};
