"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { PageHeader } from "../../components/PageHeader";
import { GlassCard } from "../../components/GlassCard";
import { EvidenceTimeline } from "../../components/EvidenceTimeline";
import { IncidentListItem, IncidentDetail } from "../../lib/types";
import { ApiClient } from "../../lib/api";
import {
  Filter,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  Send,
  RefreshCw,
  Scale,
  MessageSquare,
  ArrowRight,
  User,
  Clock,
  ShieldAlert,
} from "lucide-react";

function EvidenceContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const requestedIncidentId = searchParams.get("incident_id");

  const [incidents, setIncidents] = useState<IncidentListItem[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<IncidentDetail | null>(null);
  const [loadingList, setLoadingList] = useState<boolean>(true);
  const [loadingDetail, setLoadingDetail] = useState<boolean>(false);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [severityFilter, setSeverityFilter] = useState<string>("ALL");
  const [error, setError] = useState<string | null>(null);

  // Note form state
  const [newNote, setNewNote] = useState<string>("");
  const [submittingNote, setSubmittingNote] = useState<boolean>(false);

  // Override form state
  const [showOverrideModal, setShowOverrideModal] = useState<boolean>(false);
  const [overrideDecision, setOverrideDecision] = useState<string>("ALLOW");
  const [overrideReason, setOverrideReason] = useState<string>("");
  const [submittingOverride, setSubmittingOverride] = useState<boolean>(false);

  const fetchIncidents = async () => {
    setLoadingList(true);
    setError(null);
    try {
      const params: any = {};
      if (statusFilter !== "ALL") params.status = statusFilter;
      if (severityFilter !== "ALL") params.severity = severityFilter;
      const res = await ApiClient.listIncidents(params);
      setIncidents(res.items);

      if (res.items.length > 0) {
        const targetId = requestedIncidentId && res.items.some((i) => i.id === requestedIncidentId)
          ? requestedIncidentId
          : res.items[0].id;
        loadIncidentDetail(targetId);
      } else {
        setSelectedIncident(null);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load incidents from database.");
    } finally {
      setLoadingList(false);
    }
  };

  const loadIncidentDetail = async (incidentId: string) => {
    setLoadingDetail(true);
    try {
      const detail = await ApiClient.getIncidentById(incidentId);
      setSelectedIncident(detail);
    } catch (err: any) {
      setError(err.message || `Failed to retrieve incident details for ${incidentId}`);
    } finally {
      setLoadingDetail(false);
    }
  };

  useEffect(() => {
    fetchIncidents();
  }, [statusFilter, severityFilter]);

  useEffect(() => {
    if (requestedIncidentId && requestedIncidentId !== selectedIncident?.id) {
      loadIncidentDetail(requestedIncidentId);
    }
  }, [requestedIncidentId]);

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedIncident || !newNote.trim()) return;

    setSubmittingNote(true);
    try {
      await ApiClient.addIncidentNote(selectedIncident.id, newNote.trim());
      setNewNote("");
      await loadIncidentDetail(selectedIncident.id);
    } catch (err: any) {
      alert(`Failed to add audit note: ${err.message}`);
    } finally {
      setSubmittingNote(false);
    }
  };

  const handleOverrideSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedIncident || !overrideReason.trim()) return;

    setSubmittingOverride(true);
    try {
      await ApiClient.overrideIncidentDecision(selectedIncident.id, overrideDecision, overrideReason.trim());
      setShowOverrideModal(false);
      setOverrideReason("");
      await loadIncidentDetail(selectedIncident.id);
      await fetchIncidents();
    } catch (err: any) {
      alert(`Decision override rejected: ${err.message}`);
    } finally {
      setSubmittingOverride(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        badge="SOC Investigation Console"
        badgeVariant="indigo"
        title="Security Incidents & Forensic Evidence"
        description="Inspect chronological call timelines, examine derived evidence items, log audit notes, and execute auditable policy decision overrides."
      />

      {/* Filter and Control Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-white border border-slate-200 p-3 rounded-lg text-xs shadow-sm">
        <div className="flex flex-wrap items-center gap-1.5">
          <Filter className="h-3.5 w-3.5 text-slate-400 mr-1" />
          <span className="text-slate-500 font-medium">Status:</span>
          {["ALL", "OPEN", "INVESTIGATING", "CONFIRMED_FRAUD", "RESOLVED"].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-2.5 py-1 rounded text-xs transition-colors font-medium ${
                statusFilter === st
                  ? "bg-blue-600 text-white"
                  : "bg-slate-50 text-slate-600 hover:bg-slate-100 border border-slate-200"
              }`}
            >
              {st.replace(/_/g, " ")}
            </button>
          ))}
        </div>

        <button
          onClick={fetchIncidents}
          className="flex items-center gap-1.5 px-3 py-1 rounded bg-slate-50 border border-slate-200 text-slate-700 hover:bg-slate-100 transition-colors"
        >
          <RefreshCw className="h-3 w-3" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Main Split Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Incidents Queue */}
        <div className="lg:col-span-4 space-y-3">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-700 flex items-center justify-between">
            <span>Incident Queue ({incidents.length})</span>
          </h3>

          {loadingList && (
            <div className="h-64 flex flex-col items-center justify-center text-center space-y-2">
              <Loader2 className="h-6 w-6 text-blue-600 animate-spin" />
              <span className="text-xs text-slate-500">Loading incidents...</span>
            </div>
          )}

          {!loadingList && incidents.length === 0 && (
            <div className="p-8 text-center rounded-lg border border-slate-200 bg-white space-y-2 shadow-sm">
              <CheckCircle2 className="h-8 w-8 text-slate-400 mx-auto" />
              <p className="text-xs text-slate-500">No matching incidents in current view.</p>
            </div>
          )}

          {!loadingList && incidents.length > 0 && (
            <div className="space-y-2 max-h-[750px] overflow-y-auto pr-1">
              {incidents.map((inc) => {
                const isSelected = selectedIncident?.id === inc.id;
                const isHigh = inc.risk_score >= 70;
                return (
                  <div
                    key={inc.id}
                    onClick={() => {
                      router.push(`/evidence?incident_id=${inc.id}`, { scroll: false });
                      loadIncidentDetail(inc.id);
                    }}
                    className={`p-3.5 rounded-lg border cursor-pointer transition-all ${
                      isSelected
                        ? "bg-blue-50/50 border-blue-600 shadow-sm"
                        : "bg-white border-slate-200 hover:border-slate-300"
                    }`}
                  >
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="font-mono font-semibold text-slate-900">{inc.id}</span>
                      <span
                        className={`px-1.5 py-0.2 rounded font-semibold text-[11px] border ${
                          isHigh
                            ? "bg-red-50 text-red-700 border-red-200"
                            : "bg-emerald-50 text-emerald-700 border-emerald-200"
                        }`}
                      >
                        {inc.risk_score}/100
                      </span>
                    </div>
                    <p className="text-xs text-slate-800 font-semibold truncate mb-1">
                      {inc.title}
                    </p>
                    <div className="flex items-center justify-between text-[11px] text-slate-500">
                      <span>{inc.caller_claimed || "Unknown Caller"}</span>
                      <span className="uppercase font-medium">{inc.status.replace(/_/g, " ")}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Column: Detailed Investigation View */}
        <div className="lg:col-span-8">
          {loadingDetail && (
            <div className="h-96 flex flex-col items-center justify-center text-center space-y-2">
              <Loader2 className="h-7 w-7 text-blue-600 animate-spin" />
              <span className="text-xs text-slate-500">Retrieving incident audit trail...</span>
            </div>
          )}

          {!loadingDetail && !selectedIncident && (
            <div className="p-12 text-center rounded-lg border border-slate-200 bg-white shadow-sm space-y-2">
              <ShieldAlert className="h-10 w-10 text-slate-300 mx-auto" />
              <h4 className="text-sm font-semibold text-slate-800">No Incident Selected</h4>
              <p className="text-xs text-slate-500">Select an item from the queue to inspect forensic evidence.</p>
            </div>
          )}

          {!loadingDetail && selectedIncident && (
            <div className="space-y-6">
              {/* Header Box */}
              <GlassCard className="p-5 space-y-4">
                <div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-100 pb-3">
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-xs font-mono font-bold text-blue-600">{selectedIncident.id}</span>
                      <span className="rounded bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-700 border border-slate-200">
                        {selectedIncident.status.replace(/_/g, " ")}
                      </span>
                      <span
                        className={`rounded px-2 py-0.5 text-[11px] font-semibold uppercase border ${
                          selectedIncident.risk_score >= 70
                            ? "bg-red-50 text-red-700 border-red-200"
                            : "bg-emerald-50 text-emerald-700 border-emerald-200"
                        }`}
                      >
                        {selectedIncident.severity} ({selectedIncident.risk_score}/100)
                      </span>
                    </div>
                    <h2 className="text-lg font-bold text-slate-900 mt-1">{selectedIncident.title}</h2>
                  </div>

                  <button
                    onClick={() => setShowOverrideModal(true)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-white border border-slate-300 hover:bg-slate-50 text-xs font-semibold text-slate-700 transition-colors shadow-sm"
                  >
                    <Scale className="h-3.5 w-3.5 text-blue-600" />
                    <span>Decision Override</span>
                  </button>
                </div>

                {/* Metadata Row */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                  <div className="p-2.5 rounded bg-slate-50 border border-slate-200">
                    <span className="text-slate-500 block text-[10px] uppercase font-medium">Claimed Caller</span>
                    <span className="font-semibold text-slate-900 mt-0.5 block truncate">
                      {selectedIncident.caller_claimed || "Unspecified"}
                    </span>
                  </div>
                  <div className="p-2.5 rounded bg-slate-50 border border-slate-200">
                    <span className="text-slate-500 block text-[10px] uppercase font-medium">Assigned Analyst</span>
                    <span className="font-semibold text-slate-900 mt-0.5 block truncate">
                      {selectedIncident.assigned_to || "Unassigned"}
                    </span>
                  </div>
                  <div className="p-2.5 rounded bg-slate-50 border border-slate-200">
                    <span className="text-slate-500 block text-[10px] uppercase font-medium">Policy Action</span>
                    <span className="font-semibold text-slate-900 mt-0.5 block">
                      {selectedIncident.decision}
                    </span>
                  </div>
                  <div className="p-2.5 rounded bg-slate-50 border border-slate-200">
                    <span className="text-slate-500 block text-[10px] uppercase font-medium">Logged Timestamp</span>
                    <span className="font-mono text-slate-900 mt-0.5 block text-[11px] truncate">
                      {selectedIncident.created_at ? new Date(selectedIncident.created_at).toLocaleString() : "Recent"}
                    </span>
                  </div>
                </div>

                <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
                  <span className="text-slate-500">Related Telephony Evaluation ID:</span>
                  <Link
                    href={`/result?id=${selectedIncident.analysis_id}`}
                    className="font-mono font-medium text-blue-600 hover:text-blue-700 flex items-center gap-1"
                  >
                    <span>{selectedIncident.analysis_id}</span>
                    <ArrowRight className="h-3 w-3" />
                  </Link>
                </div>
              </GlassCard>

              {/* Forensic Evidence Timeline */}
              <div className="space-y-3">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-700">
                  Forensic Evidence Timeline ({selectedIncident.evidence_items.length} Points)
                </h3>
                <EvidenceTimeline evidence={selectedIncident.evidence_items} />
              </div>

              {/* Analyst Notes Section */}
              <GlassCard className="p-5 space-y-4">
                <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
                  <MessageSquare className="h-4 w-4 text-blue-600" />
                  <h3 className="text-sm font-semibold text-slate-900">
                    Analyst Investigation Audit Notes ({selectedIncident.notes?.length || 0})
                  </h3>
                </div>

                {/* Existing Notes */}
                <div className="space-y-2.5 max-h-56 overflow-y-auto">
                  {(!selectedIncident.notes || selectedIncident.notes.length === 0) ? (
                    <p className="text-xs text-slate-400 italic">No notes logged yet for this incident.</p>
                  ) : (
                    selectedIncident.notes.map((note) => (
                      <div key={note.id} className="p-3 rounded-md bg-slate-50 border border-slate-200 space-y-1">
                        <div className="flex items-center justify-between text-[11px] text-slate-500">
                          <span className="font-semibold text-slate-900">{note.author_name || (note as any).analyst_name || "Analyst"}</span>
                          <span className="font-mono text-[10px]">
                            {note.created_at ? new Date(note.created_at).toLocaleTimeString() : ""}
                          </span>
                        </div>
                        <p className="text-xs text-slate-700 leading-relaxed">{note.note_text}</p>
                      </div>
                    ))
                  )}
                </div>

                {/* Add Note Form */}
                <form onSubmit={handleAddNote} className="pt-2 flex gap-2">
                  <input
                    type="text"
                    required
                    value={newNote}
                    onChange={(e) => setNewNote(e.target.value)}
                    placeholder="Log analyst observation or incident verification note..."
                    className="flex-1 bg-white border border-slate-300 rounded-md px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-blue-600"
                    disabled={submittingNote}
                  />
                  <button
                    type="submit"
                    disabled={submittingNote || !newNote.trim()}
                    className="px-3.5 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-md text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-sm"
                  >
                    {submittingNote ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Send className="h-3.5 w-3.5" />}
                    <span>Add Note</span>
                  </button>
                </form>
              </GlassCard>
            </div>
          )}
        </div>
      </div>

      {/* Decision Override Modal */}
      {showOverrideModal && selectedIncident && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4">
          <div className="w-full max-w-md rounded-lg border border-slate-200 bg-white p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <Scale className="h-5 w-5 text-blue-600" />
                <h3 className="text-sm font-bold text-slate-900">Execute Policy Decision Override</h3>
              </div>
              <button
                onClick={() => setShowOverrideModal(false)}
                className="text-slate-400 hover:text-slate-600 text-xs font-bold"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-slate-600">
              Overrides are recorded permanently in the tamper-evident audit log along with analyst credentials and justification.
            </p>

            <form onSubmit={handleOverrideSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  New Policy Decision
                </label>
                <select
                  value={overrideDecision}
                  onChange={(e) => setOverrideDecision(e.target.value)}
                  className="w-full bg-white border border-slate-300 rounded-md p-2 text-xs text-slate-900 focus:outline-none focus:border-blue-600"
                >
                  <option value="ALLOW">ALLOW (False Positive - Cleared by Analyst)</option>
                  <option value="BLOCK">BLOCK (Confirmed Malicious - Terminate Line)</option>
                  <option value="STEP_UP_AUTH">STEP_UP_AUTH (Require Secondary Biometric Verification)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Mandatory Security Justification:
                </label>
                <textarea
                  required
                  rows={3}
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                  placeholder="Provide audit rationale for overriding the automated risk engine recommendation..."
                  className="w-full bg-white border border-slate-300 rounded-md p-2.5 text-xs text-slate-900 focus:outline-none focus:border-blue-600 leading-relaxed"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowOverrideModal(false)}
                  className="px-3.5 py-1.5 rounded-md border border-slate-300 text-slate-700 hover:bg-slate-50 text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingOverride || !overrideReason.trim()}
                  className="px-4 py-1.5 rounded-md bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-sm flex items-center gap-1.5 disabled:bg-blue-400"
                >
                  {submittingOverride ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Scale className="h-3.5 w-3.5" />}
                  <span>Confirm Override</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default function EvidencePage() {
  return (
    <Suspense
      fallback={
        <div className="h-64 flex flex-col items-center justify-center text-center space-y-2">
          <Loader2 className="h-7 w-7 text-blue-600 animate-spin" />
          <span className="text-xs text-slate-500">Loading incident investigation console...</span>
        </div>
      }
    >
      <EvidenceContent />
    </Suspense>
  );
}
