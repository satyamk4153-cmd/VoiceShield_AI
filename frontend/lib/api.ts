import {
  FinalAnalysisResponse,
  DemoScenario,
  DashboardStats,
  SpeakerVerification,
  IncidentDetail,
  IncidentListResponse,
  SpeakerProfile,
  TokenResponse,
  UserResponse
} from "./types";

function getApiBaseUrl(): string {
  // Always use Next.js rewrites proxy in the browser to avoid CORS and handle 502s properly
  if (typeof window !== "undefined") {
    return "";
  }

  const envUrl = process.env.NEXT_PUBLIC_API_URL;
  if (!envUrl) {
    return "http://localhost:8000";
  }
  
  let url = envUrl.trim();
  if (url && !url.startsWith("http://") && !url.startsWith("https://")) {
    url = `https://${url}`;
  }
  return url.replace(/\/+$/, "");
}

const API_BASE_URL = getApiBaseUrl();

export class ApiClient {
  public static getToken(): string | null {
    if (typeof window !== "undefined") {
      return localStorage.getItem("sentinelvoice_token");
    }
    return null;
  }

  public static setToken(token: string): void {
    if (typeof window !== "undefined") {
      localStorage.setItem("sentinelvoice_token", token);
    }
  }

  public static clearToken(): void {
    if (typeof window !== "undefined") {
      localStorage.removeItem("sentinelvoice_token");
      localStorage.removeItem("sentinelvoice_user");
    }
  }

  public static isAuthenticated(): boolean {
    return !!this.getToken();
  }

  public static getStoredUser(): UserResponse | null {
    if (typeof window !== "undefined") {
      const u = localStorage.getItem("sentinelvoice_user");
      if (u) {
        try {
          return JSON.parse(u);
        } catch (_) {}
      }
    }
    return null;
  }

  public static setStoredUser(user: UserResponse): void {
    if (typeof window !== "undefined") {
      localStorage.setItem("sentinelvoice_user", JSON.stringify(user));
    }
  }

  private static getHeaders(isJson: boolean = true): HeadersInit {
    const headers: Record<string, string> = {};
    if (isJson) {
      headers["Content-Type"] = "application/json";
    }
    const token = this.getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    return headers;
  }

  private static async handleResponse<T>(res: Response): Promise<T> {
    if (!res.ok) {
      if (res.status === 502 || res.status === 503) {
        throw new Error("Backend service is waking up (this can take ~50 seconds). Please try again shortly.");
      }

      let errorMessage = `API Error ${res.status}: ${res.statusText}`;
      try {
        const errorJson = await res.json();
        if (errorJson.detail) {
          errorMessage = typeof errorJson.detail === "string" ? errorJson.detail : JSON.stringify(errorJson.detail);
        } else if (errorJson.message) {
          errorMessage = errorJson.message;
        }
      } catch (_) {}
      throw new Error(errorMessage);
    }
    return res.json();
  }

  // Authentication
  static async login(email: string, password: string): Promise<TokenResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await this.handleResponse<TokenResponse>(res);
    this.setToken(data.access_token);
    // Fetch profile to cache user info
    try {
      const profile = await this.getCurrentUser();
      this.setStoredUser(profile);
    } catch (_) {}
    return data;
  }

  static async getCurrentUser(): Promise<UserResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
      headers: this.getHeaders(true),
      cache: "no-store",
    });
    return this.handleResponse<UserResponse>(res);
  }

  static logout(): void {
    this.clearToken();
  }

  // Health
  static async getHealth(): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/api/v1/health`, { cache: "no-store" });
    return this.handleResponse(res);
  }

  // Dashboard Telemetry
  static async getDashboardStats(): Promise<DashboardStats> {
    const res = await fetch(`${API_BASE_URL}/api/v1/dashboard/stats`, {
      headers: this.getHeaders(),
      cache: "no-store",
    });
    return this.handleResponse<DashboardStats>(res);
  }

  // Analyses
  static async analyzeTranscript(transcript: string, callerClaimed?: string): Promise<FinalAnalysisResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/analyses/transcript`, {
      method: "POST",
      headers: this.getHeaders(true),
      body: JSON.stringify({
        transcript,
        caller_claimed_identity: callerClaimed,
      }),
    });
    return this.handleResponse<FinalAnalysisResponse>(res);
  }

  static async analyzeAudio(formData: FormData): Promise<FinalAnalysisResponse> {
    const headers = this.getHeaders(false);
    const res = await fetch(`${API_BASE_URL}/api/v1/analyses/audio`, {
      method: "POST",
      headers,
      body: formData,
    });
    return this.handleResponse<FinalAnalysisResponse>(res);
  }

  static async getAnalysisById(analysisId: string): Promise<FinalAnalysisResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/analyses/${analysisId}`, {
      headers: this.getHeaders(),
      cache: "no-store",
    });
    return this.handleResponse<FinalAnalysisResponse>(res);
  }

  // Incidents
  static async listIncidents(params?: { status?: string; severity?: string; page?: number; pageSize?: number }): Promise<IncidentListResponse> {
    const query = new URLSearchParams();
    if (params?.status) query.set("status", params.status);
    if (params?.severity) query.set("severity", params.severity);
    if (params?.page) query.set("page", String(params.page));
    if (params?.pageSize) query.set("page_size", String(params.pageSize));

    const res = await fetch(`${API_BASE_URL}/api/v1/incidents?${query.toString()}`, {
      headers: this.getHeaders(),
      cache: "no-store",
    });
    return this.handleResponse<IncidentListResponse>(res);
  }

  static async getIncidentById(incidentId: string): Promise<IncidentDetail> {
    const res = await fetch(`${API_BASE_URL}/api/v1/incidents/${incidentId}`, {
      headers: this.getHeaders(),
      cache: "no-store",
    });
    return this.handleResponse<IncidentDetail>(res);
  }

  static async updateIncidentStatus(incidentId: string, status: string, assignedTo?: string): Promise<IncidentDetail> {
    const res = await fetch(`${API_BASE_URL}/api/v1/incidents/${incidentId}/status`, {
      method: "PATCH",
      headers: this.getHeaders(true),
      body: JSON.stringify({ status, assigned_to: assignedTo }),
    });
    return this.handleResponse<IncidentDetail>(res);
  }

  static async addIncidentNote(incidentId: string, noteText: string): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/api/v1/incidents/${incidentId}/notes`, {
      method: "POST",
      headers: this.getHeaders(true),
      body: JSON.stringify({ note_text: noteText }),
    });
    return this.handleResponse(res);
  }

  static async overrideIncidentDecision(incidentId: string, newDecision: string, reason: string): Promise<IncidentDetail> {
    const res = await fetch(`${API_BASE_URL}/api/v1/incidents/${incidentId}/override`, {
      method: "POST",
      headers: this.getHeaders(true),
      body: JSON.stringify({ new_decision: newDecision, reason }),
    });
    return this.handleResponse<IncidentDetail>(res);
  }

  // Speakers
  static async listSpeakers(): Promise<SpeakerProfile[]> {
    const res = await fetch(`${API_BASE_URL}/api/v1/speakers`, {
      headers: this.getHeaders(),
      cache: "no-store",
    });
    return this.handleResponse<SpeakerProfile[]>(res);
  }

  static async createSpeakerProfile(profile: { id: string; name: string; identity_claimed: string; consent_recorded?: boolean; retention_days?: number }): Promise<SpeakerProfile> {
    const res = await fetch(`${API_BASE_URL}/api/v1/speakers`, {
      method: "POST",
      headers: this.getHeaders(true),
      body: JSON.stringify(profile),
    });
    return this.handleResponse<SpeakerProfile>(res);
  }

  static async enrollSpeakerAudio(profileId: string, audioFile: File): Promise<{ status: string; profile_id: string; enrollment_id: string; duration_seconds: number; model_version: string }> {
    const formData = new FormData();
    formData.append("audio_file", audioFile);
    const headers = this.getHeaders(false);
    const res = await fetch(`${API_BASE_URL}/api/v1/speakers/${profileId}/enroll`, {
      method: "POST",
      headers,
      body: formData,
    });
    return this.handleResponse(res);
  }

  static async verifySpeaker(referenceSampleId?: string, testAudioFile?: File, testTranscript?: string): Promise<SpeakerVerification> {
    if (testAudioFile) {
      const formData = new FormData();
      if (referenceSampleId) formData.append("reference_sample_id", referenceSampleId);
      formData.append("test_audio", testAudioFile);
      if (testTranscript) formData.append("test_transcript", testTranscript);
      
      const res = await fetch(`${API_BASE_URL}/api/v1/verify/speaker`, {
        method: "POST",
        headers: this.getHeaders(false),
        body: formData,
      });
      return this.handleResponse<SpeakerVerification>(res);
    } else {
      const res = await fetch(`${API_BASE_URL}/api/v1/verify/speaker`, {
        method: "POST",
        headers: this.getHeaders(true),
        body: JSON.stringify({
          reference_sample_id: referenceSampleId,
          test_transcript: testTranscript,
        }),
      });
      return this.handleResponse<SpeakerVerification>(res);
    }
  }

  // Demo Scenarios (Isolated demo sandbox)
  static async getDemoScenarios(): Promise<DemoScenario[]> {
    const res = await fetch(`${API_BASE_URL}/api/v1/demo/scenarios`, { cache: "no-store" });
    return this.handleResponse<DemoScenario[]>(res);
  }

  static async getDemoScenarioById(id: string): Promise<DemoScenario> {
    const res = await fetch(`${API_BASE_URL}/api/v1/demo/scenarios/${id}`, { cache: "no-store" });
    return this.handleResponse<DemoScenario>(res);
  }

  static async getDemoScenarioAnalysis(id: string): Promise<FinalAnalysisResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/demo/scenarios/${id}/analysis`, { cache: "no-store" });
    return this.handleResponse<FinalAnalysisResponse>(res);
  }
}

