export type AppMode = "production" | "development" | "demo";

export interface AudioQuality {
  duration_seconds: number;
  sample_rate: number;
  channels: number;
  rms_energy: number;
  snr_db: number;
  clipping_ratio: number;
  silence_ratio: number;
  bandwidth_hz: number;
  quality_score: number;
  quality_level: "GOOD" | "FAIR" | "POOR";
  telephony_condition: "NORMAL" | "DEGRADED" | "HIGHLY_DEGRADED";
  quality_notes: string[];
}

export interface VoiceAuthenticity {
  authenticity_probability: number;
  spoof_probability: number;
  confidence: number;
  classification: "AUTHENTIC" | "POSSIBLE_SPOOF" | "SUSPICIOUS" | "UNCERTAIN" | "UNAVAILABLE";
  explanation: string;
  model_name?: string;
  model_version?: string;
  inference_ms?: number;
  status?: string;
  is_demo: boolean;
}

export interface SpeakerVerification {
  similarity: number;
  confidence: number;
  result: "MATCH" | "MISMATCH" | "UNCERTAIN";
  threshold?: number;
  explanation: string;
  model_name?: string;
  model_version?: string;
  status?: string;
  is_demo: boolean;
}

export interface FraudSignal {
  id: string;
  signal_type: string;
  category: "AUTHENTICATION" | "IMPERSONATION" | "THREAT" | "FINANCIAL" | "TECHNICAL" | "SCAM" | string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  confidence: number;
  description: string;
  timestamp?: string;
  risk_contribution: number;
  detected_phrases?: string[];
}

export interface ContextualSignal {
  name: string;
  score: number;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  description: string;
}

export interface RiskAssessment {
  score: number;
  level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  decision: "ALLOW" | "STEP_UP_REQUIRED" | "ANALYST_REVIEW" | "BLOCK_CALL" | "CONFIRMED" | "LIKELY" | "SUSPICIOUS" | "UNCERTAIN" | "BENIGN";
  confidence: number;
  risk_breakdown: Record<string, number>;
  policy_id?: string;
  policy_version?: string;
  reason_codes?: string[];
}

export interface EvidenceItem {
  id: string;
  timestamp?: string;
  timestamp_offset?: string;
  title: string;
  category: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  explanation: string;
  contribution_points: number;
}

export interface FinalAnalysisResponse {
  analysis_id: string;
  session_id?: string;
  incident_id?: string;
  status: string;
  created_at: string;
  is_demo_data: boolean;
  provider_used: string;
  transcript?: string;
  caller_claimed_identity?: string;
  risk: RiskAssessment;
  voice: VoiceAuthenticity;
  speaker: SpeakerVerification;
  audio: AudioQuality;
  fraud_signals: FraudSignal[];
  contextual_signals: ContextualSignal[];
  evidence: EvidenceItem[];
  recommended_actions: string[];
}

export interface IncidentNote {
  id: string;
  author_id?: string;
  author_name: string;
  note_text: string;
  created_at: string;
}

export interface IncidentEvent {
  id: string;
  event_type: string;
  label: string;
  timestamp_offset: string;
  description: string;
  severity: string;
  created_at: string;
}

export interface IncidentDetail {
  id: string;
  incident_number: string;
  organization_id: string;
  session_id?: string;
  analysis_id?: string;
  title: string;
  status: "NEW" | "UNDER_INVESTIGATION" | "RESOLVED" | "FALSE_POSITIVE" | "ESCALATED";
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  risk_score: number;
  decision: string;
  caller_claimed?: string;
  assigned_to?: string;
  assignee_name?: string;
  flags: string[];
  analyst_override_decision?: string;
  analyst_override_reason?: string;
  analyst_override_by?: string;
  created_at: string;
  updated_at: string;
  resolved_at?: string;
  timeline_events: IncidentEvent[];
  notes: IncidentNote[];
  evidence_items: EvidenceItem[];
}

export interface IncidentListResponse {
  items: IncidentDetail[];
  total: number;
  page: number;
  page_size: number;
}

export type IncidentListItem = IncidentDetail;

export interface SpeakerProfile {
  id: string;
  organization_id: string;
  name: string;
  identity_claimed: string;
  consent_recorded: boolean;
  retention_days: number;
  is_active: boolean;
  enrollment_count: number;
  created_at: string;
}

export interface DemoTimelineEvent {
  id?: string;
  seconds: number;
  time_offset: string;
  event_type: string;
  label: string;
  transcript_segment: string;
  signal_detected?: string;
  severity?: string;
  risk_accumulated?: number;
}

export interface DemoScenario {
  id: string;
  name: string;
  category: string;
  description: string;
  caller_claimed: string;
  caller_phone?: string;
  duration_seconds?: number;
  codec?: string;
  channel?: string;
  transcript: string;
  language: string;
  expected_risk_score: number;
  expected_risk_level: string;
  expected_decision: string;
  voice_spoof_prob: number;
  speaker_similarity: number;
  audio_quality: string;
  telephony_condition: string;
  signals: FraudSignal[];
  timeline_events: DemoTimelineEvent[];
  warning_actions?: string[];
  is_synthetic?: boolean;
  is_demo?: boolean;
}

export interface DistributionPoint {
  name: string;
  value: number;
  color: string;
}

export interface IncidentSummary {
  id: string;
  timestamp: string;
  title: string;
  risk_score: number;
  risk_level: string;
  caller_claimed: string;
  flags: string[];
  status?: string;
}

export interface DashboardStats {
  is_demo_data: boolean;
  total_calls_analyzed: number;
  high_risk_calls: number;
  possible_spoof_calls: number;
  speaker_mismatches: number;
  average_risk_score: number;
  risk_distribution: DistributionPoint[];
  fraud_category_distribution: DistributionPoint[];
  signal_frequencies: DistributionPoint[];
  recent_incidents: IncidentSummary[];
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user_id: string;
  email: string;
  role: string;
  organization_id: string;
  organization_slug: string;
}

export interface UserResponse {
  id: string;
  email: string;
  full_name: string;
  role: string;
  organization_id: string;
  is_active: boolean;
  created_at: string;
}

