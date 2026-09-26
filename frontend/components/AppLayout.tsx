"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Shield,
  Radio,
  Mic,
  UserCheck,
  FileText,
  BarChart3,
  PlayCircle,
  Menu,
  X,
  LogIn,
  LogOut,
  User as UserIcon,
  AlertTriangle,
} from "lucide-react";
import { Logo } from "../components/Logo";
import { ApiClient } from "../lib/api";
import { UserResponse } from "../lib/types";

interface AppLayoutProps {
  children: React.ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const pathname = usePathname();
  const router = useRouter();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
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

      if (ApiClient.isAuthenticated()) {
        const cached = ApiClient.getStoredUser();
        if (cached) setCurrentUser(cached);
        try {
          const profile = await ApiClient.getCurrentUser();
          setCurrentUser(profile);
          ApiClient.setStoredUser(profile);
        } catch {
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

  const navItems = [
    { href: "/", label: "Overview", icon: Shield },
    { href: "/live", label: "Live Protection", icon: Radio, badge: "Live" },
    { href: "/analyze", label: "Analyze Audio", icon: Mic },
    { href: "/speaker", label: "Speaker Profiles", icon: UserCheck },
    { href: "/evidence", label: "Security Incidents", icon: FileText },
    { href: "/dashboard", label: "Operational Metrics", icon: BarChart3 },
    { href: "/demo", label: "Scenarios Sandbox", icon: PlayCircle },
  ];

  const getModeTag = () => {
    if (appMode === "production") {
      return (
        <span className="inline-flex items-center gap-1.5 rounded px-2 py-0.5 text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-600" />
          Production
        </span>
      );
    }
    if (appMode === "demo") {
      return (
        <span className="inline-flex items-center gap-1.5 rounded px-2 py-0.5 text-[11px] font-medium bg-amber-50 text-amber-800 border border-amber-200">
          <AlertTriangle className="h-3 w-3 text-amber-600" />
          Demo Sandbox
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 rounded px-2 py-0.5 text-[11px] font-medium bg-slate-100 text-slate-600 border border-slate-200">
        <span className="h-1.5 w-1.5 rounded-full bg-slate-400" />
        Backend Connecting
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-slate-900 flex flex-col md:flex-row">
      {/* Mobile Top Header */}
      <header className="md:hidden sticky top-0 z-40 bg-white border-b border-slate-200 px-4 py-3 flex items-center justify-between">
        <Link href="/" className="flex items-center">
          <Logo size="sm" showTagline={false} />
        </Link>
        <div className="flex items-center gap-2">
          {getModeTag()}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-1.5 text-slate-600 hover:text-slate-900 rounded-md hover:bg-slate-100"
            aria-label="Toggle Navigation"
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </header>

      {/* Sidebar Navigation (Desktop) */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-slate-200 flex flex-col transform transition-transform duration-200 ease-in-out md:static md:translate-x-0 ${
          mobileMenuOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Brand Area */}
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <Link href="/" onClick={() => setMobileMenuOpen(false)}>
            <Logo size="md" showTagline={true} />
          </Link>
          <button
            onClick={() => setMobileMenuOpen(false)}
            className="md:hidden p-1 text-slate-400 hover:text-slate-600"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Navigation Links */}
        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          <div className="px-3 py-1.5 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Platform Navigation
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileMenuOpen(false)}
                className={`flex items-center justify-between px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-blue-50 text-blue-700 font-semibold"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Icon className={`h-4 w-4 ${isActive ? "text-blue-600" : "text-slate-400"}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-blue-100 text-blue-700">
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Footer Area: Mode & Auth */}
        <div className="p-4 border-t border-slate-100 bg-slate-50/50 space-y-3">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-500 font-medium">Environment</span>
            {getModeTag()}
          </div>

          {currentUser ? (
            <div className="flex items-center justify-between p-2 rounded-md bg-white border border-slate-200">
              <div className="flex items-center gap-2 min-w-0">
                <div className="w-7 h-7 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center flex-shrink-0">
                  <UserIcon className="h-3.5 w-3.5" />
                </div>
                <div className="min-w-0">
                  <p className="text-xs font-medium text-slate-900 truncate">
                    {currentUser.email}
                  </p>
                  <p className="text-[10px] text-slate-400 capitalize">
                    {currentUser.role}
                  </p>
                </div>
              </div>
              <button
                onClick={handleLogout}
                title="Sign out"
                className="p-1 text-slate-400 hover:text-red-600 rounded hover:bg-slate-50 transition-colors"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <Link
              href="/login"
              onClick={() => setMobileMenuOpen(false)}
              className="flex items-center justify-center gap-2 w-full py-2 px-3 rounded-md bg-white border border-slate-200 text-xs font-medium text-slate-700 hover:bg-slate-50 hover:text-slate-900 transition-colors shadow-sm"
            >
              <LogIn className="h-3.5 w-3.5 text-blue-600" />
              <span>Analyst Sign In</span>
            </Link>
          )}

          <p className="text-[11px] text-slate-400 text-center">
            VoiceShield AI • v2.4 Enterprise
          </p>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
          {children}
        </main>

        <footer className="border-t border-slate-200 bg-white py-4 text-xs text-slate-500">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-slate-700">VoiceShield AI</span>
              <span>— Protect every voice.</span>
            </div>
            <p className="text-slate-400">
              Enterprise Voice Threat Intelligence & Authentication. Zero audio stored permanently.
            </p>
          </div>
        </footer>
      </div>
    </div>
  );
};
