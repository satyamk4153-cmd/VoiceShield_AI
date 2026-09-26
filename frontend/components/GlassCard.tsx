"use client";

import React from "react";
import { cn } from "../lib/utils";
import { motion, HTMLMotionProps } from "framer-motion";

interface GlassCardProps extends HTMLMotionProps<"div"> {
  children: React.ReactNode;
  className?: string;
  glow?: "none" | "red" | "indigo" | "emerald" | "amber";
  interactive?: boolean;
}

export const GlassCard: React.FC<GlassCardProps> = ({
  children,
  className,
  glow = "none",
  interactive = false,
  ...props
}) => {
  // Translate previous glow prop to clean, subtle borders/tint without heavy neon glows
  const borderVariants = {
    none: "border-slate-200",
    red: "border-red-200 bg-red-50/20",
    indigo: "border-blue-200 bg-blue-50/20",
    emerald: "border-emerald-200 bg-emerald-50/20",
    amber: "border-amber-200 bg-amber-50/20",
  };

  return (
    <motion.div
      whileHover={interactive ? { y: -1, transition: { duration: 0.15 } } : undefined}
      className={cn(
        "rounded-lg border bg-white p-5 shadow-sm transition-all duration-150 text-slate-900",
        borderVariants[glow] || "border-slate-200",
        interactive && "hover:border-slate-300 hover:shadow",
        className
      )}
      {...props}
    >
      {children}
    </motion.div>
  );
};
