"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { PageHeader } from "../../components/PageHeader";
import { StatCard } from "../../components/StatCard";
import { GlassCard } from "../../components/GlassCard";
import { DashboardStats } from "../../lib/types";
import { ApiClient } from "../../lib/api";
import {
  ShieldAlert,
  Cpu,
  UserX,
  PhoneCall,
  AlertTriangle,
  Loader2,
  RefreshCw,
  ArrowRight,
  Activity,
  FileText,
} from "lucide-react";
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from "recharts";

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await ApiClient.getDashboardStats();
      setStats(data);
    } catch (err: any) {
      setError(err.message || "Failed to retrieve telemetry metrics from security backend.");
      setStats(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  return (
    <div className="space-y-6">
      <PageHeader
        badge="SOC Intelligence"
        badgeVariant="indigo"
        title="Operational Security Telemetry"
        description="Persisted telephony risk evaluations, speaker baseline verification results, and incident audit logs."
      />

      {/* Demo Warning Banner if backend returned demo data */}
      {stats?.is_demo_data && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-3.5 text-xs text-amber-900 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-600 flex-shrink-0" />
            <span>
              <strong>Sandbox Environment Active:</strong> Data displayed represents isolated evaluation scenarios. Real telephony streams will populate production storage.
            </span>
          </div>
          <span className="text-[11px] font-semibold text-amber-800 bg-amber-100 px-2 py-0.5 rounded border border-amber-200">
            Sandbox Mode
          </span>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="h-64 flex flex-col items-center justify-center text-center space-y-3">
          <Loader2 className="h-7 w-7 text-blue-600 animate-spin" />
          <p className="text-xs text-slate-500">
            Retrieving operational analytics...
          </p>
        </div>
      )}

      {/* Error State */}
      {!loading && error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center space-y-3">
          <AlertTriangle className="h-8 w-8 text-red-600 mx-auto" />
          <div className="space-y-1">
            <h3 className="text-sm font-semibold text-red-900">Telemetry Ingestion Error</h3>
            <p className="text-xs text-red-700 max-w-md mx-auto">{error}</p>
          </div>
          <button
            onClick={fetchStats}
            className="inline-flex items-center gap-1.5 rounded-md bg-white border border-slate-300 px-3.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-sm"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Retry Query
          </button>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && stats && stats.total_calls_analyzed === 0 && (
        <div className="rounded-lg border border-slate-200 bg-white p-10 text-center space-y-3 shadow-sm">
          <Activity className="h-10 w-10 text-slate-400 mx-auto" />
          <div className="space-y-1">
            <h3 className="text-sm font-semibold text-slate-900">No Telephony Analyses Recorded</h3>
            <p className="text-xs text-slate-500 max-w-md mx-auto">
              No voice stream evaluations have been performed yet. Run a live simulation or analyze a recorded audio file to generate telemetry.
            </p>
          </div>
          <div className="flex items-center justify-center gap-3 pt-2">
            <Link
              href="/analyze"
              className="inline-flex items-center gap-1.5 rounded-md bg-blue-600 px-3.5 py-2 text-xs font-semibold text-white hover:bg-blue-700 transition-colors shadow-sm"
            >
              <PhoneCall className="h-3.5 w-3.5" />
              Analyze Audio
            </Link>
            <Link
              href="/live"
              className="inline-flex items-center gap-1.5 rounded-md border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-sm"
            >
              <Activity className="h-3.5 w-3.5" />
              Live SOC Monitor
            </Link>
          </div>
        </div>
      )}

      {/* Populated Telemetry View */}
      {!loading && !error && stats && stats.total_calls_analyzed > 0 && (
        <>
          {/* 4 Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              label="Calls Evaluated"
              value={stats.total_calls_analyzed.toLocaleString()}
              description="Total verified calls"
              icon={PhoneCall}
              variant="indigo"
            />
            <StatCard
              label="High Risk Flagged"
              value={stats.high_risk_calls.toLocaleString()}
              description={`${((stats.high_risk_calls / stats.total_calls_analyzed) * 100).toFixed(1)}% of total volume`}
              icon={ShieldAlert}
              variant="red"
            />
            <StatCard
              label="Synthetic Audio Suspects"
              value={stats.possible_spoof_calls.toLocaleString()}
              description="Acoustic anti-spoof flags"
              icon={Cpu}
              variant="amber"
            />
            <StatCard
              label="Biometric Mismatches"
              value={stats.speaker_mismatches.toLocaleString()}
              description="1:1 speaker identity failures"
              icon={UserX}
              variant="emerald"
            />
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Risk Distribution */}
            <div className="lg:col-span-5">
              <GlassCard className="p-5 h-full">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
                  <h3 className="text-sm font-semibold text-slate-900">
                    Policy Risk Breakdown
                  </h3>
                  <span className="text-xs text-slate-500 font-medium">
                    Average Score: {stats.average_risk_score.toFixed(1)}/100
                  </span>
                </div>
                <div className="h-60">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={stats.risk_distribution}
                        dataKey="value"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        outerRadius={75}
                        innerRadius={45}
                        paddingAngle={2}
                      >
                        {stats.risk_distribution.map((entry, index) => (
                          <Cell
                            key={`cell-${index}`}
                            fill={
                              entry.name === "LOW"
                                ? "#16A34A"
                                : entry.name === "MEDIUM"
                                ? "#D97706"
                                : entry.name === "HIGH"
                                ? "#DC2626"
                                : entry.color || "#2563EB"
                            }
                          />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "#FFFFFF",
                          borderColor: "#E2E8F0",
                          borderRadius: "6px",
                          fontSize: "12px",
                          color: "#0F172A",
                        }}
                      />
                      <Legend
                        verticalAlign="bottom"
                        wrapperStyle={{ fontSize: "11px", paddingTop: "8px" }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </GlassCard>
            </div>

            {/* Fraud Categories */}
            <div className="lg:col-span-7">
              <GlassCard className="p-5 h-full">
                <div className="border-b border-slate-100 pb-3 mb-4">
                  <h3 className="text-sm font-semibold text-slate-900">
                    Top Flagged Threat Categories
                  </h3>
                </div>
                <div className="h-60">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={stats.fraud_category_distribution}
                      layout="vertical"
                      margin={{ top: 5, right: 20, left: 30, bottom: 5 }}
                    >
                      <XAxis type="number" stroke="#94A3B8" fontSize={11} />
                      <YAxis
                        type="category"
                        dataKey="name"
                        stroke="#64748B"
                        fontSize={11}
                        width={110}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "#FFFFFF",
                          borderColor: "#E2E8F0",
                          borderRadius: "6px",
                          fontSize: "12px",
                          color: "#0F172A",
                        }}
                      />
                      <Bar dataKey="value" fill="#2563EB" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </GlassCard>
            </div>
          </div>

          {/* Recent Security Incidents Activity Table */}
          <GlassCard className="p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-sm font-semibold text-slate-900">
                  Recent Security Incidents
                </h3>
                <p className="text-xs text-slate-500">
                  Logged call interactions flagged by risk fusion policy rules.
                </p>
              </div>
              <Link
                href="/evidence"
                className="inline-flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-700"
              >
                <span>Incident Console</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                    <th className="py-2.5 px-3">Incident ID</th>
                    <th className="py-2.5 px-3">Claimed Caller</th>
                    <th className="py-2.5 px-3">Risk Score</th>
                    <th className="py-2.5 px-3">Severity</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {stats.recent_incidents.map((incident) => {
                    const isHigh = incident.risk_score >= 70;
                    return (
                      <tr key={incident.id} className="hover:bg-slate-50 transition-colors">
                        <td className="py-3 px-3 font-mono font-medium text-slate-900">
                          {incident.id}
                        </td>
                        <td className="py-3 px-3 text-slate-700">
                          {incident.caller_claimed || "Unspecified"}
                        </td>
                        <td className="py-3 px-3">
                          <span
                            className={`font-semibold px-2 py-0.5 rounded text-[11px] border ${
                              isHigh
                                ? "bg-red-50 text-red-700 border-red-200"
                                : "bg-emerald-50 text-emerald-700 border-emerald-200"
                            }`}
                          >
                            {incident.risk_score}/100
                          </span>
                        </td>
                        <td className="py-3 px-3 text-slate-700 font-medium">
                          {incident.risk_level}
                        </td>
                        <td className="py-3 px-3">
                          <span className="text-[11px] px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200 font-medium">
                            {incident.status}
                          </span>
                        </td>
                        <td className="py-3 px-3 text-right">
                          <Link
                            href={`/evidence?incident_id=${incident.id}`}
                            className="inline-flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-700"
                          >
                            <span>Investigate</span>
                            <ArrowRight className="h-3 w-3" />
                          </Link>
                        </td>
                      </tr>
                    );
                  })}
                  {stats.recent_incidents.length === 0 && (
                    <tr>
                      <td colSpan={6} className="py-6 text-center text-xs text-slate-400">
                        No active security incidents recorded.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </GlassCard>
        </>
      )}
    </div>
  );
}
