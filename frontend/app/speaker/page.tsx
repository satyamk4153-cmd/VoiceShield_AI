"use client";

import React, { useState, useEffect } from "react";
import { PageHeader } from "../../components/PageHeader";
import { GlassCard } from "../../components/GlassCard";
import { SpeakerMatchCard } from "../../components/SpeakerMatchCard";
import { SpeakerVerification, SpeakerProfile } from "../../lib/types";
import { ApiClient } from "../../lib/api";
import {
  UserCheck,
  Upload,
  Loader2,
  Info,
  ShieldCheck,
  AlertTriangle,
  Plus,
  RefreshCw,
  UserPlus,
} from "lucide-react";

export default function SpeakerPage() {
  const [profiles, setProfiles] = useState<SpeakerProfile[]>([]);
  const [loadingProfiles, setLoadingProfiles] = useState<boolean>(true);
  const [selectedProfileId, setSelectedProfileId] = useState<string>("");
  const [testAudioFile, setTestAudioFile] = useState<File | null>(null);
  const [testTranscript, setTestTranscript] = useState<string>(
    "Hello, this is officer Rajesh Sharma calling from HDFC Bank Security Department."
  );
  const [verifying, setVerifying] = useState<boolean>(false);
  const [verificationResult, setVerificationResult] = useState<SpeakerVerification | null>(null);
  const [verificationError, setVerificationError] = useState<string | null>(null);

  // New Profile Form
  const [showEnrollModal, setShowEnrollModal] = useState<boolean>(false);
  const [newProfileId, setNewProfileId] = useState<string>("");
  const [newProfileName, setNewProfileName] = useState<string>("");
  const [newProfileAuthority, setNewProfileAuthority] = useState<string>("");
  const [enrollAudioFile, setEnrollAudioFile] = useState<File | null>(null);
  const [consentRecorded, setConsentRecorded] = useState<boolean>(true);
  const [enrolling, setEnrolling] = useState<boolean>(false);
  const [enrollError, setEnrollError] = useState<string | null>(null);

  const fetchProfiles = async () => {
    setLoadingProfiles(true);
    try {
      const data = await ApiClient.listSpeakers();
      setProfiles(data);
      if (data.length > 0 && !selectedProfileId) {
        setSelectedProfileId(data[0].id);
      }
    } catch (err: any) {
      console.error("Failed to load speaker profiles:", err);
    } finally {
      setLoadingProfiles(false);
    }
  };

  useEffect(() => {
    fetchProfiles();
  }, []);

  const handleVerify = async () => {
    setVerifying(true);
    setVerificationError(null);
    setVerificationResult(null);

    try {
      const res = await ApiClient.verifySpeaker(
        selectedProfileId || undefined,
        testAudioFile || undefined,
        testTranscript || undefined
      );
      setVerificationResult(res);
    } catch (err: any) {
      setVerificationError(err.message || "Speaker verification execution failed.");
    } finally {
      setVerifying(false);
    }
  };

  const handleEnrollSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProfileId.trim() || !newProfileName.trim() || !enrollAudioFile) {
      setEnrollError("Please provide Profile ID, Representative Name, and a Reference WAV/MP3 file.");
      return;
    }
    setEnrolling(true);
    setEnrollError(null);

    try {
      await ApiClient.createSpeakerProfile({
        id: newProfileId.trim(),
        name: newProfileName.trim(),
        identity_claimed: newProfileAuthority.trim() || "Official Bank Representative",
        consent_recorded: consentRecorded,
        retention_days: 90,
      });

      await ApiClient.enrollSpeakerAudio(newProfileId.trim(), enrollAudioFile);

      setShowEnrollModal(false);
      setNewProfileId("");
      setNewProfileName("");
      setNewProfileAuthority("");
      setEnrollAudioFile(null);
      await fetchProfiles();
      setSelectedProfileId(newProfileId.trim());
    } catch (err: any) {
      setEnrollError(err.message || "Enrollment failed.");
    } finally {
      setEnrolling(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        badge="Biometric Verification"
        badgeVariant="indigo"
        title="Speaker Biometrics & 1:1 Identity Baselines"
        description="Verify caller vocal harmonics 1:1 against authorized enrolled representative profiles. Enforces zero unconsented profiling and zero raw audio leakage."
      />

      {/* Privacy Notice Alert */}
      <div className="rounded-lg border border-blue-200 bg-blue-50/70 p-4 text-xs text-blue-900 flex items-start gap-3">
        <Info className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
        <div className="space-y-0.5">
          <span className="font-bold text-slate-900 block">Responsible 1:1 Acoustic Authentication:</span>
          <p className="text-slate-600">
            VoiceShield AI only performs 1:1 acoustic comparison against explicitly consented, enrolled organizational profiles. It does not perform open surveillance or unconsented tracking.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Enrolled Profiles List & Management */}
        <div className="lg:col-span-5 space-y-4">
          <GlassCard className="p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-700 flex items-center gap-2">
                <UserCheck className="h-4 w-4 text-blue-600" />
                <span>Enrolled Profiles ({profiles.length})</span>
              </h3>
              <button
                onClick={() => setShowEnrollModal(true)}
                className="inline-flex items-center gap-1 rounded-md bg-blue-600 px-2.5 py-1 text-xs font-semibold text-white hover:bg-blue-700 transition-colors shadow-sm"
              >
                <Plus className="h-3 w-3" />
                <span>Enroll Profile</span>
              </button>
            </div>

            {loadingProfiles && (
              <div className="h-32 flex items-center justify-center">
                <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />
              </div>
            )}

            {!loadingProfiles && profiles.length === 0 && (
              <div className="p-6 text-center rounded-md border border-slate-200 bg-slate-50 text-xs text-slate-500">
                No speaker profiles enrolled yet. Click &quot;Enroll Profile&quot; to register a representative.
              </div>
            )}

            {!loadingProfiles && profiles.length > 0 && (
              <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
                {profiles.map((p) => {
                  const isSelected = selectedProfileId === p.id;
                  return (
                    <div
                      key={p.id}
                      onClick={() => setSelectedProfileId(p.id)}
                      className={`p-3 rounded-md border cursor-pointer transition-all ${
                        isSelected
                          ? "bg-blue-50/60 border-blue-600 shadow-sm"
                          : "bg-white border-slate-200 hover:border-slate-300"
                      }`}
                    >
                      <div className="flex justify-between items-center text-xs mb-1">
                        <span className="font-semibold text-slate-900">{p.name}</span>
                        <span className="font-mono text-blue-700 font-semibold">{p.id}</span>
                      </div>
                      <div className="flex justify-between items-center text-[11px] text-slate-500">
                        <span>{p.identity_claimed}</span>
                        <span>{p.enrollment_count} sample(s)</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </GlassCard>
        </div>

        {/* Right: 1:1 Verification Execution */}
        <div className="lg:col-span-7 space-y-4">
          <GlassCard className="p-5 space-y-4">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-700 flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-emerald-600" />
              1:1 Biometric Verification Test
            </h3>

            <div className="space-y-1">
              <label className="text-xs font-medium text-slate-700">Target Enrolled Baseline:</label>
              <select
                value={selectedProfileId}
                onChange={(e) => setSelectedProfileId(e.target.value)}
                className="w-full rounded-md bg-white border border-slate-300 px-3 py-2 text-xs text-slate-900 focus:border-blue-600 focus:outline-none"
              >
                {profiles.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.id}) — {p.identity_claimed}
                  </option>
                ))}
                {profiles.length === 0 && <option value="">No profiles available</option>}
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-medium text-slate-700">
                Test Audio Sample (Optional if Transcript Provided):
              </label>
              <input
                type="file"
                accept=".wav,.mp3"
                onChange={(e) => e.target.files && setTestAudioFile(e.target.files[0])}
                className="text-xs text-slate-600 file:mr-3 file:py-1 file:px-2.5 file:rounded file:border file:border-slate-200 file:text-xs file:font-semibold file:bg-white file:text-slate-700 hover:file:bg-slate-50 cursor-pointer"
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs font-medium text-slate-700">
                Spoken Test Transcript:
              </label>
              <textarea
                rows={3}
                value={testTranscript}
                onChange={(e) => setTestTranscript(e.target.value)}
                className="w-full rounded-md bg-white border border-slate-300 p-2.5 text-xs text-slate-900 focus:border-blue-600 focus:outline-none leading-relaxed"
              />
            </div>

            <button
              disabled={verifying || (!selectedProfileId && profiles.length === 0)}
              onClick={handleVerify}
              className="w-full flex items-center justify-center gap-2 rounded-md bg-blue-600 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-blue-700 transition-colors disabled:opacity-50 cursor-pointer"
            >
              {verifying ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Computing Acoustic Cosine Distance...</span>
                </>
              ) : (
                <>
                  <UserCheck className="h-4 w-4" />
                  <span>Verify Identity Against Baseline</span>
                </>
              )}
            </button>

            {verificationError && (
              <div className="p-3 rounded-md bg-red-50 border border-red-200 text-xs text-red-700 flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 flex-shrink-0" />
                <span>{verificationError}</span>
              </div>
            )}
          </GlassCard>

          {verificationResult && (
            <div className="space-y-3">
              <SpeakerMatchCard speaker={verificationResult} />
            </div>
          )}
        </div>
      </div>

      {/* Enroll Modal */}
      {showEnrollModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4">
          <div className="w-full max-w-md rounded-lg border border-slate-200 bg-white p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <UserPlus className="h-5 w-5 text-blue-600" />
                <h3 className="text-sm font-bold text-slate-900">Enroll Authorized Speaker Baseline</h3>
              </div>
              <button
                onClick={() => setShowEnrollModal(false)}
                className="text-slate-400 hover:text-slate-600 text-xs font-bold"
              >
                ✕
              </button>
            </div>

            {enrollError && (
              <div className="p-3 rounded-md bg-red-50 border border-red-200 text-xs text-red-700">
                {enrollError}
              </div>
            )}

            <form onSubmit={handleEnrollSubmit} className="space-y-3.5">
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Profile ID
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. SPK-HDFC-SEC-01"
                  value={newProfileId}
                  onChange={(e) => setNewProfileId(e.target.value)}
                  className="w-full bg-white border border-slate-300 rounded-md px-3 py-1.5 text-xs text-slate-900 focus:outline-none focus:border-blue-600"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Representative Full Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Officer Rajesh Sharma"
                  value={newProfileName}
                  onChange={(e) => setNewProfileName(e.target.value)}
                  className="w-full bg-white border border-slate-300 rounded-md px-3 py-1.5 text-xs text-slate-900 focus:outline-none focus:border-blue-600"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Designation / Claimed Authority
                </label>
                <input
                  type="text"
                  placeholder="e.g. HDFC Bank Security Desk Officer"
                  value={newProfileAuthority}
                  onChange={(e) => setNewProfileAuthority(e.target.value)}
                  className="w-full bg-white border border-slate-300 rounded-md px-3 py-1.5 text-xs text-slate-900 focus:outline-none focus:border-blue-600"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Reference Audio Enrollment Sample (WAV / MP3)
                </label>
                <input
                  type="file"
                  required
                  accept=".wav,.mp3"
                  onChange={(e) => e.target.files && setEnrollAudioFile(e.target.files[0])}
                  className="text-xs text-slate-600 file:mr-3 file:py-1 file:px-2.5 file:rounded file:border file:border-slate-200 file:text-xs file:font-semibold file:bg-white file:text-slate-700 hover:file:bg-slate-50 cursor-pointer"
                />
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="consent"
                  checked={consentRecorded}
                  onChange={(e) => setConsentRecorded(e.target.checked)}
                  className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                />
                <label htmlFor="consent" className="text-xs text-slate-600 cursor-pointer">
                  Explicit employee biometric consent recorded & stored
                </label>
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowEnrollModal(false)}
                  className="px-3 py-1.5 rounded-md border border-slate-300 text-slate-700 hover:bg-slate-50 text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={enrolling || !newProfileId.trim() || !newProfileName.trim() || !enrollAudioFile}
                  className="px-4 py-1.5 rounded-md bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-sm flex items-center gap-1.5 disabled:bg-blue-400"
                >
                  {enrolling ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <UserCheck className="h-3.5 w-3.5" />}
                  <span>Enroll Profile</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
