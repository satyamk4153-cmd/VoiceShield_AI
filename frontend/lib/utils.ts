import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatSeconds(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
}

export function getRiskColor(score: number): {
  text: string;
  bg: string;
  border: string;
  badge: string;
} {
  if (score >= 85) {
    return {
      text: "text-red-700",
      bg: "bg-red-50",
      border: "border-red-200",
      badge: "bg-red-100 text-red-800 border-red-200",
    };
  }
  if (score >= 70) {
    return {
      text: "text-red-600",
      bg: "bg-red-50",
      border: "border-red-200",
      badge: "bg-red-100 text-red-800 border-red-200",
    };
  }
  if (score >= 40) {
    return {
      text: "text-amber-700",
      bg: "bg-amber-50",
      border: "border-amber-200",
      badge: "bg-amber-100 text-amber-800 border-amber-200",
    };
  }
  return {
    text: "text-emerald-700",
    bg: "bg-emerald-50",
    border: "border-emerald-200",
    badge: "bg-emerald-100 text-emerald-800 border-emerald-200",
  };
}
