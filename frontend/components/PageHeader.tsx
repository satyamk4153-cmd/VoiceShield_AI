import React from "react";
import { cn } from "@/lib/utils";

interface PageHeaderProps {
  badge?: string;
  badgeVariant?: "indigo" | "red" | "emerald" | "amber";
  title: string;
  description: string;
  action?: React.ReactNode;
  className?: string;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  badge,
  badgeVariant = "indigo",
  title,
  description,
  action,
  className,
}) => {
  const badgeStyles = {
    indigo: "bg-blue-50 text-blue-700 border-blue-200",
    red: "bg-red-50 text-red-700 border-red-200",
    emerald: "bg-emerald-50 text-emerald-700 border-emerald-200",
    amber: "bg-amber-50 text-amber-800 border-amber-200",
  };

  return (
    <div className={cn("flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-5 border-b border-slate-200 mb-6", className)}>
      <div>
        {badge && (
          <span className={cn("inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-xs font-medium border mb-2", badgeStyles[badgeVariant])}>
            <span className="h-1.5 w-1.5 rounded-full bg-current" />
            {badge}
          </span>
        )}
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">{title}</h1>
        <p className="mt-1 text-sm text-slate-500 max-w-2xl">{description}</p>
      </div>
      {action && <div className="flex-shrink-0">{action}</div>}
    </div>
  );
};
