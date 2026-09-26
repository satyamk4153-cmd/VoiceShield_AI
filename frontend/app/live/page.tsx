"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { PageHeader } from "../../components/PageHeader";
import { CallSimulator } from "../../components/CallSimulator";
import { DemoScenario } from "../../lib/types";
import { ApiClient } from "../../lib/api";
import { Loader2, AlertCircle, PhoneCall, ArrowRight, ShieldCheck, RefreshCw } from "lucide-react";
import { cn } from "../../lib/utils";

function LiveSimulationContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const scenarioParam = searchParams.get("scenario");

  const [availableScenarios, setAvailableScenarios] = useState<DemoScenario[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<DemoScenario | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadData() {
      setLoading(true);
      setError(null);

      try {
        const scenarios = await ApiClient.getDemoScenarios();
        if (!isMounted) return;
        setAvailableScenarios(scenarios);

        if (scenarioParam) {
          try {
            const exactScenario = await ApiClient.getDemoScenarioById(scenarioParam);
            if (!isMounted) return;
            setSelectedScenario(exactScenario);
          } catch (e: any) {
            if (!isMounted) return;
            // Check if available locally
            const localMatch = scenarios.find((s) => s.id === scenarioParam);
            if (localMatch) {
              setSelectedScenario(localMatch);
            } else {
              setError(`Benchmark scenario '${scenarioParam}' could not be located in the catalog.`);
              setSelectedScenario(null);
            }
          }
        } else {
          // If no scenario specified in query, pick first scenario or allow user to pick
          if (scenarios.length > 0) {
            setSelectedScenario(scenarios[0]);
          }
        }
      } catch (err: any) {
        if (!isMounted) return;
        setError(err.message || "Failed to load demo scenarios from backend service.");
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    loadData();

    return () => {
      isMounted = false;
    };
  }, [scenarioParam]);

  const handleSelectScenario = (scId: string) => {
    router.push(`/live?scenario=${encodeURIComponent(scId)}`);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        badge="Live Telephony Protection"
        badgeVariant="red"
        title="Live Inbound Call Inspection"
        description="Inspect multi-modal fraud detection in real time as an inbound social engineering call progresses from greeting to warning advisory."
      />

      {loading ? (
        <div className="h-[50vh] flex flex-col items-center justify-center text-center space-y-3 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <Loader2 className="h-7 w-7 text-blue-600 animate-spin" />
          <span className="text-xs text-slate-500">Loading benchmark simulation scenario...</span>
        </div>
      ) : (
        <>
          {/* Scenario Selector Ribbon */}
          <div className="rounded-lg border border-slate-200 bg-white p-3.5 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3 mb-2.5">
              <div className="flex items-center gap-2">
                <PhoneCall className="h-4 w-4 text-blue-600" />
                <span className="text-xs font-semibold text-slate-900">Select Active Threat Scenario:</span>
              </div>
              <Link
                href="/demo"
                className="text-xs text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1"
              >
                <span>View All in Sandbox Catalog</span>
                <ArrowRight className="h-3 w-3" />
              </Link>
            </div>

            <div className="flex flex-wrap gap-2">
              {availableScenarios.map((sc) => {
                const isSelected = selectedScenario?.id === sc.id;
                return (
                  <button
                    key={sc.id}
                    onClick={() => handleSelectScenario(sc.id)}
                    className={cn(
                      "rounded-md px-3 py-1.5 text-xs font-medium border transition-all text-left flex items-center gap-2",
                      isSelected
                        ? "bg-blue-50 text-blue-700 border-blue-300 ring-1 ring-blue-500"
                        : "bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100 hover:text-slate-900"
                    )}
                  >
                    <span
                      className={cn(
                        "h-1.5 w-1.5 rounded-full",
                        sc.expected_risk_score >= 70
                          ? "bg-red-500"
                          : sc.expected_risk_score >= 40
                          ? "bg-amber-500"
                          : "bg-emerald-500"
                      )}
                    />
                    <span>{sc.name}</span>
                    <span className="text-[10px] opacity-75 font-mono">({sc.expected_risk_score}/100)</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Error Banner */}
          {error && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-xs text-red-800 flex items-start gap-3 shadow-sm">
              <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div className="space-y-1">
                <span className="font-semibold block">{error}</span>
                <p className="text-red-700">Please choose one of the verified scenarios above or return to the scenario library.</p>
              </div>
            </div>
          )}

          {/* Simulator view */}
          {selectedScenario && !error && (
            <CallSimulator scenario={selectedScenario} />
          )}
        </>
      )}
    </div>
  );
}

export default function LivePage() {
  return (
    <Suspense
      fallback={
        <div className="h-[50vh] flex flex-col items-center justify-center text-center space-y-3">
          <Loader2 className="h-7 w-7 text-blue-600 animate-spin" />
          <span className="text-xs text-slate-500">Preparing live call simulation environment...</span>
        </div>
      }
    >
      <LiveSimulationContent />
    </Suspense>
  );
}
