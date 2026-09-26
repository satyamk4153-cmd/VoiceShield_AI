"use client";

import React from "react";
import { GlassCard } from "../components/GlassCard";
import { LucideIcon } from "lucide-react";
import { cn } from "../lib/utils";

interface StatCardProps {
  label: string;
  value: string | number;
  change?: string;
  description?: string;
  icon: LucideIcon;
  variant?: "indigo" | "red" | "emerald" | "amber";
}

export const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  change,
  description,
  icon: Icon,
  variant = "indigo",
}) => {
  const variantStyles = {
    indigo: {
      iconBg: "bg-blue-50 text-blue-600 border-blue-100",
      glow: "none" as const,
    },
    red: {
      iconBg: "bg-red-50 text-red-600 border-red-100",
      glow: "none" as const,
    },
    emerald: {
      iconBg: "bg-emerald-50 text-emerald-600 border-emerald-100",
      glow: "none" as const,
    },
    amber: {
      iconBg: "bg-amber-50 text-amber-700 border-amber-100",
      glow: "none" as const,
    },
  };

  const style = variantStyles[variant];

  return (
    <GlassCard glow={style.glow} interactive className="p-4 sm:p-5">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-slate-500">{label}</span>
        <div className={cn("rounded-md p-1.5 border", style.iconBg)}>
          <Icon className="h-4 w-4" />
        </div>
      </div>

      <div className="flex items-baseline gap-2">
        <span className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">{value}</span>
        {change && (
          <span className="text-xs font-medium text-emerald-600">{change}</span>
        )}
      </div>

      {description && <p className="text-xs text-slate-500 mt-1">{description}</p>}
    </GlassCard>
  );
};
