import { clearToken, getToken, redirectToLogin } from "./auth";
import type {
  AuditLog,
  Candidate,
  CandidateScore,
  CommunicationLog,
  FinalScorecard,
  HealthResponse,
  HumanDecision,
  InterviewEntry,
  InterviewEvaluation,
  InterviewInviteResponse,
  InterviewMessage,
  InterviewPlan,
  InterviewSession,
  InterviewSessionSummary,
  Job,
  JobCreate,
  JobCriteriaUpdate,
  LiveInterviewTurn,
  LlmCallLog,
  TokenResponse,
  User,
} from "./types";

type FetchLike = typeof fetch;

type RequestOptions = Omit<RequestInit, "body"> & {
  auth?: boolean;
  body?: unknown;
};

type ApiClientOptions = {
  baseUrl?: string;
  fetcher?: FetchLike;
  getToken?: () => string | null;
  onUnauthorized?: () => void;
};

export class ApiError extends Error {
  readonly status: number;
  readonly detail: unknown;

  constructor(status: number, detail: unknown) {
    super(formatApiError(detail, status));
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

export function formatApiError(detail: unknown, status?: number): string {
  if (typeof detail === "string") {
    return detail;
  }
  if (detail && typeof detail === "object" && "detail" in detail) {
    const value = (detail as { detail: unknown }).detail;
    if (typeof value === "string") {
      return value;
    }
    if (Array.isArray(value)) {
      return value
        .map((item) => {
          if (item && typeof item === "object" && "msg" in item) {
            return String((item as { msg: unknown }).msg);
          }
          return JSON.stringify(item);
        })
        .join(", ");
    }
  }
  return status ? `Request failed with status ${status}` : "Request failed.";
}

function resolveBaseUrl(baseUrl?: string): string {
  return (baseUrl ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "");
}

export class ApiClient {
  private readonly baseUrl: string;
  private readonly fetcher: FetchLike;
  private readonly tokenGetter: () => string | null;
  private readonly onUnauthorized?: () => void;

  constructor(options: ApiClientOptions = {}) {
    this.baseUrl = resolveBaseUrl(options.baseUrl);
    this.fetcher = options.fetcher ?? ((input, init) => fetch(input, init));
    this.tokenGetter = options.getToken ?? getToken;
    this.onUnauthorized = options.onUnauthorized;
  }

  async request<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const { auth = true, body, headers, ...init } = options;
    const requestHeaders = new Headers(headers);

    if (auth) {
      const token = this.tokenGetter();
      if (token) {
        requestHeaders.set("Authorization", `Bearer ${token}`);
      }
    }

    let requestBody: BodyInit | undefined;
    if (body instanceof FormData) {
      requestBody = body;
    } else if (body !== undefined) {
      requestHeaders.set("Content-Type", "application/json");
      requestBody = JSON.stringify(body);
    }

    const response = await this.fetcher(`${this.baseUrl}${path}`, {
      ...init,
      headers: requestHeaders,
      body: requestBody,
    });

    if (response.status === 401) {
      clearToken();
      this.onUnauthorized?.();
      throw new ApiError(401, "Authentication required.");
    }

    const contentType = response.headers.get("content-type") ?? "";
    const data = contentType.includes("application/json") ? await response.json() : await response.text();

    if (!response.ok) {
      throw new ApiError(response.status, data);
    }

    return data as T;
  }

  login(email: string, password: string) {
    return this.request<TokenResponse>("/api/v1/auth/login", {
      method: "POST",
      auth: false,
      body: { email, password },
    });
  }

  me() {
    return this.request<User>("/api/v1/auth/me");
  }

  health(path: "" | "/db" | "/llm" = "") {
    return this.request<HealthResponse>(`/health${path}`, { auth: false });
  }

  listJobs() {
    return this.request<Job[]>("/api/v1/jobs");
  }

  getJob(jobId: string) {
    return this.request<Job>(`/api/v1/jobs/${jobId}`);
  }

  createJob(payload: JobCreate) {
    return this.request<Job>("/api/v1/jobs", { method: "POST", body: payload });
  }

  calibrateJob(jobId: string) {
    return this.request<Job>(`/api/v1/jobs/${jobId}/calibrate`, { method: "POST" });
  }

  updateJobCriteria(jobId: string, payload: JobCriteriaUpdate) {
    return this.request<Job>(`/api/v1/jobs/${jobId}/criteria`, { method: "PATCH", body: payload });
  }

  approveCriteria(jobId: string) {
    return this.request<Job>(`/api/v1/jobs/${jobId}/approve-criteria`, { method: "POST" });
  }

  listCandidates(jobId: string) {
    return this.request<Candidate[]>(`/api/v1/jobs/${jobId}/candidates`);
  }

  getCandidate(candidateId: string) {
    return this.request<Candidate>(`/api/v1/candidates/${candidateId}`);
  }

  getLatestCandidateScore(candidateId: string) {
    return this.request<CandidateScore>(`/api/v1/candidates/${candidateId}/score/latest`);
  }

  uploadResume(jobId: string, payload: { name?: string; email?: string; phone?: string; file: File }) {
    const formData = new FormData();
    formData.set("file", payload.file);
    if (payload.name) formData.set("name", payload.name);
    if (payload.email) formData.set("email", payload.email);
    if (payload.phone) formData.set("phone", payload.phone);
    return this.request<Candidate>(`/api/v1/jobs/${jobId}/candidates/upload-resume`, {
      method: "POST",
      body: formData,
    });
  }

  processCandidate(candidateId: string, force = false) {
    return this.request<CandidateScore | Candidate>(`/api/v1/candidates/${candidateId}/process`, {
      method: "POST",
      body: { force },
    });
  }

  shortlistDecision(candidateId: string, decision: HumanDecision, reason: string, comment?: string) {
    return this.request<Candidate>(`/api/v1/candidates/${candidateId}/shortlist-decision`, {
      method: "POST",
      body: { decision, reason, comment: comment || null },
    });
  }

  createInterviewPlan(candidateId: string) {
    return this.request<InterviewSession>(`/api/v1/candidates/${candidateId}/interview-plan`, { method: "POST" });
  }

  getInterview(sessionId: string) {
    return this.request<InterviewSession>(`/api/v1/interviews/${sessionId}`);
  }

  listCandidateInterviews(candidateId: string) {
    return this.request<InterviewSessionSummary[]>(`/api/v1/candidates/${candidateId}/interviews`);
  }

  listJobInterviews(jobId: string) {
    return this.request<InterviewSessionSummary[]>(`/api/v1/jobs/${jobId}/interviews`);
  }

  getInterviewPlan(sessionId: string) {
    return this.request<InterviewPlan>(`/api/v1/interviews/${sessionId}/plan`);
  }

  updateInterviewPlan(sessionId: string, interview_plan_json: InterviewPlan) {
    return this.request<InterviewSession>(`/api/v1/interviews/${sessionId}/plan`, {
      method: "PATCH",
      body: { interview_plan_json },
    });
  }

  sendInterviewInvite(sessionId: string) {
    return this.request<InterviewInviteResponse>(`/api/v1/interviews/${sessionId}/send-invite`, { method: "POST" });
  }

  getTranscript(sessionId: string) {
    return this.request<InterviewMessage[]>(`/api/v1/interviews/${sessionId}/transcript`);
  }

  getInterviewEvaluation(sessionId: string) {
    return this.request<InterviewEvaluation>(`/api/v1/interviews/${sessionId}/evaluation`);
  }

  evaluateInterview(sessionId: string, force = false) {
    const query = force ? "?force=true" : "";
    return this.request<InterviewEvaluation>(`/api/v1/interviews/${sessionId}/evaluate${query}`, { method: "POST" });
  }

  getFinalScorecard(candidateId: string) {
    return this.request<FinalScorecard>(`/api/v1/candidates/${candidateId}/final-scorecard`);
  }

  createFinalScorecard(candidateId: string, force = false) {
    const query = force ? "?force=true" : "";
    return this.request<FinalScorecard>(`/api/v1/candidates/${candidateId}/final-scorecard${query}`, { method: "POST" });
  }

  finalDecision(candidateId: string, decision: HumanDecision, reason: string, comment?: string) {
    return this.request<FinalScorecard | { candidate_id: string; status: string }>(`/api/v1/candidates/${candidateId}/final-decision`, {
      method: "POST",
      body: { decision, reason, comment: comment || null },
    });
  }

  adminLlmUsage() {
    return this.request<LlmCallLog[]>("/api/v1/admin/llm-usage");
  }

  adminAudit() {
    return this.request<AuditLog[]>("/api/v1/admin/audit");
  }

  adminCommunications() {
    return this.request<CommunicationLog[]>("/api/v1/admin/communications");
  }

  interviewEntry(token: string) {
    return this.request<InterviewEntry>(`/api/v1/interview-entry/${token}`, { auth: false });
  }

  sendOtp(token: string) {
    return this.request<{ message: string }>(`/api/v1/interview-entry/${token}/send-otp`, { method: "POST", auth: false });
  }

  verifyOtp(token: string, otp: string) {
    return this.request<{ message: string }>(`/api/v1/interview-entry/${token}/verify-otp`, {
      method: "POST",
      auth: false,
      body: { otp },
    });
  }

  startInterview(token: string) {
    return this.request<LiveInterviewTurn>(`/api/v1/interview-entry/${token}/start`, { method: "POST", auth: false });
  }

  answerInterview(token: string, answer: string, client_session_nonce: string) {
    return this.request<LiveInterviewTurn>(`/api/v1/interview-entry/${token}/answer`, {
      method: "POST",
      auth: false,
      body: { answer, client_session_nonce },
    });
  }

  completeInterview(token: string, client_session_nonce: string) {
    return this.request<{ message: string }>(`/api/v1/interview-entry/${token}/complete`, {
      method: "POST",
      auth: false,
      body: { client_session_nonce },
    });
  }
}

export const api = new ApiClient({ onUnauthorized: redirectToLogin });

export function isCandidateScore(value: Candidate | CandidateScore): value is CandidateScore {
  return "overall_score" in value;
}
