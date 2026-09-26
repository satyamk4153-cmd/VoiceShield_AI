"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Shield, Radio, Activity, Mic, Play, BarChart3, UserCheck, Menu, X, AlertTriangle, LogIn, LogOut, User as UserIcon } from "lucide-react";
import { cn } from "../lib/utils";
import { ApiClient } from "../lib/api";
import { UserResponse } from "../lib/types";

export const Navbar: React.FC = () => {
  const pathname = usePathname();
  const router = useRouter();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [appMode, setAppMode] = useState<string>("connecting");
  const [currentUser, setCurrentUser] = useState<UserResponse | null>(null);

  useEffect(() => {
    async function checkHealthAndAuth() {
      try {
        const health = await ApiClient.getHealth();
        setAppMode(health.app_mode || "production");
      } catch {
        setAppMode("offline");
      }

      // Check current user
      if (ApiClient.isAuthenticated()) {
        const cached = ApiClient.getStoredUser();
        if (cached) {
          setCurrentUser(cached);
        }
        try {
          const profile = await ApiClient.getCurrentUser();
          setCurrentUser(profile);
          ApiClient.setStoredUser(profile);
        } catch {
          // Token expired or invalid
          ApiClient.clearToken();
          setCurrentUser(null);
        }
      } else {
        setCurrentUser(null);
      }
    }
    checkHealthAndAuth();
  }, [pathname]);

  const handleLogout = () => {
    ApiClient.logout();
    setCurrentUser(null);
    router.push("/login");
  };

  const navLinks = [
    { href: "/", label: "Overview", icon: Shield },
    { href: "/live", label: "Live Call SOC", icon: Radio, highlight: true },
    { href: "/analyze", label: "Call Analysis", icon: Mic },
    { href: "/speaker", label: "Speaker Biometrics", icon: UserCheck },
    { href: "/evidence", label: "Incidents & Evidence", icon: Activity },
    { href: "/dashboard", label: "Telemetry", icon: BarChart3 },
    { href: "/demo", label: "Demo Scenarios", icon: Play },
  ];

  const getModeBadge = () => {
    if (appMode === "production") {
      return (
        <span className="inline-flex items-center gap-1.5 rounded border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-mono font-bold tracking-wider text-emerald-400">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
          PRODUCTION
        </span>
      );
    } else if (appMode === "demo") {
      return (
        <span className="inline-flex items-center gap-1.5 rounded border border-amber-500/40 bg-amber-500/10 px-2 py-0.5 text-[10px] font-mono font-bold tracking-wider text-amber-400">
          <AlertTriangle className="h-2.5 w-2.5" />
          DEMO SANDBOX
        </span>
      );
    } else if (appMode === "development") {
      return (
        <span className="inline-flex items-center gap-1.5 rounded border border-sky-500/30 bg-sky-500/10 px-2 py-0.5 text-[10px] font-mono font-bold tracking-wider text-sky-400">
          <span className="h-1.5 w-1.5 rounded-full bg-sky-400" />
          DEVELOPMENT
        </span>
      );
    } else {
      return (
        <span className="inline-flex items-center gap-1.5 rounded border border-rose-500/30 bg-rose-500/10 px-2 py-0.5 text-[10px] font-mono font-bold tracking-wider text-rose-400">
          <span className="h-1.5 w-1.5 rounded-full bg-rose-500 animate-pulse" />
          BACKEND OFFLINE
        </span>
      );
    }
  };

  return (
    <header className="sticky top-0 z-50 border-b border-slate-800 bg-slate-950/90 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-2.5 sm:px-6 lg:px-8">
        {/* Brand */}
        <Link href="/" className="flex items-center space-x-3 group">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-indigo-500/40 bg-indigo-950/60 text-indigo-400 group-hover:border-indigo-400 transition-colors">
            <Shield className="h-4.5 w-4.5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-base font-bold tracking-tight text-slate-100 font-mono">SENTINELVOICE</span>
              {getModeBadge()}
            </div>
            <p className="text-[10px] text-slate-400 font-medium tracking-wide">Multi-Modal Telephony Threat Platform</p>
          </div>
        </Link>

        {/* Desktop Nav */}
        <nav className="hidden lg:flex items-center space-x-1">
          {navLinks.map((link) => {
            const Icon = link.icon;
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "flex items-center space-x-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium transition-all duration-150",
                  isActive
                    ? "bg-slate-800 text-indigo-300 border border-slate-700 font-semibold"
                    : "text-slate-400 hover:bg-slate-900 hover:text-slate-200",
                  link.highlight && !isActive && "text-rose-400 hover:text-rose-300"
                )}
              >
                <Icon className={cn("h-3.5 w-3.5", link.highlight && !isActive ? "text-rose-400" : "")} />
                <span>{link.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Right Auth & CTA */}
        <div className="hidden lg:flex items-center space-x-3">
          {currentUser ? (
            <div className="flex items-center space-x-2 pl-2 border-l border-slate-800">
              <div className="flex items-center space-x-1.5 bg-slate-900/80 border border-slate-800 rounded-md px-2.5 py-1 text-xs">
                <UserIcon className="h-3.5 w-3.5 text-indigo-400" />
                <span className="font-mono text-slate-300 max-w-[120px] truncate">{currentUser.email}</span>
                <span className="text-[9px] uppercase px-1 py-0.2 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  {currentUser.role}
                </span>
              </div>
              <button
                onClick={handleLogout}
                title="Sign out of SOC console"
                className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-900 rounded-md transition-colors cursor-pointer"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <Link
              href="/login"
              className="flex items-center space-x-1.5 rounded-md border border-slate-700 bg-slate-900/80 px-2.5 py-1.5 text-xs font-medium text-slate-300 hover:text-white hover:border-slate-600 transition-colors"
            >
              <LogIn className="h-3.5 w-3.5 text-indigo-400" />
              <span>SOC Login</span>
            </Link>
          )}

          <Link
            href="/live"
            className="flex items-center space-x-2 rounded-md border border-rose-600/50 bg-rose-950/40 px-3 py-1.5 text-xs font-semibold text-rose-300 hover:bg-rose-900/50 transition-colors"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-rose-400 animate-ping" />
            <span>Live Call Monitor</span>
          </Link>
        </div>

        {/* Mobile menu trigger */}
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="lg:hidden rounded-md p-1.5 text-slate-400 hover:bg-slate-900 hover:text-white"
          aria-label="Toggle navigation menu"
        >
          {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="lg:hidden border-b border-slate-800 bg-slate-950 px-4 pt-2 pb-4 space-y-1">
          {navLinks.map((link) => {
            const Icon = link.icon;
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMobileOpen(false)}
                className={cn(
                  "flex items-center space-x-3 rounded-md px-3 py-2 text-sm font-medium",
                  isActive
                    ? "bg-slate-800 text-indigo-300 border border-slate-700"
                    : "text-slate-400 hover:bg-slate-900 hover:text-slate-200"
                )}
              >
                <Icon className="h-4 w-4" />
                <span>{link.label}</span>
              </Link>
            );
          })}

          <div className="pt-2 border-t border-slate-800">
            {currentUser ? (
              <div className="flex items-center justify-between p-2 rounded bg-slate-900 border border-slate-800">
                <div className="flex items-center space-x-2 text-xs text-slate-300">
                  <UserIcon className="h-3.5 w-3.5 text-indigo-400" />
                  <span className="font-mono">{currentUser.email}</span>
                </div>
                <button
                  onClick={() => {
                    handleLogout();
                    setMobileOpen(false);
                  }}
                  className="text-xs text-rose-400 hover:text-rose-300 flex items-center space-x-1"
                >
                  <LogOut className="h-3.5 w-3.5" />
                  <span>Logout</span>
                </button>
              </div>
            ) : (
              <Link
                href="/login"
                onClick={() => setMobileOpen(false)}
                className="flex items-center justify-center space-x-2 w-full py-2 rounded bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 text-xs font-semibold"
              >
                <LogIn className="h-4 w-4" />
                <span>Sign In to Telephony SOC</span>
              </Link>
            )}
          </div>
        </div>
      )}
    </header>
  );
};
