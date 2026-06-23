export type UserRole = "ADMIN" | "RECRUITER" | "HIRING_MANAGER";
export type JobStatus = "DRAFT" | "CRITERIA_GENERATED" | "APPROVED" | "CLOSED";
export type CandidateStatus =
  | "UPLOADED"
  | "PARSED"
  | "SCORED"
  | "NEEDS_REVIEW"
  | "SHORTLISTED"
  | "REJECTED"
  | "INTERVIEW_INVITED"
  | "INTERVIEW_ACTIVE"
  | "INTERVIEW_COMPLETED"
  | "FINAL_REVIEW"
  | "APPROVED"
  | "REJECTED_FINAL";
export type InterviewSessionStatus = "DRAFT" | "INVITED" | "OTP_PENDING" | "ACTIVE" | "COMPLETED" | "EXPIRED" | "CANCELLED";
export type HumanDecision = "APPROVE" | "REJECT" | "HOLD";
export type QuestionType = "FIXED" | "RESUME_VALIDATION" | "SOFT_SKILL" | "KNOCKOUT" | "DYNAMIC" | "FOLLOW_UP";
export type PilotFeedbackType =
  | "RECRUITER_SCORECARD_FEEDBACK"
  | "HIRING_MANAGER_SCORECARD_FEEDBACK"
  | "CANDIDATE_INTERVIEW_FEEDBACK"
  | "BUG_REPORT"
  | "GENERAL_FEEDBACK";

export type User = {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: "bearer";
  user: User;
};

export type HealthResponse = {
  status: string;
  service: string;
};

export type Job = {
  id: string;
  title: string;
  department: string | null;
  seniority: string | null;
  location: string | null;
  employment_type: string | null;
  salary_range: string | null;
  raw_jd: string;
  improved_jd: string | null;
  criteria_json: Array<Record<string, unknown>> | null;
  must_haves_json: string[] | null;
  nice_to_haves_json: string[] | null;
  disqualifiers_json: string[] | null;
  soft_skills_json: string[] | null;
  knockout_areas_json: string[] | null;
  status: JobStatus;
  created_by_id: string | null;
  created_at: string;
  updated_at: string;
};

export type JobCreate = {
  title: string;
  department?: string | null;
  seniority?: string | null;
  location?: string | null;
  employment_type?: string | null;
  salary_range?: string | null;
  raw_jd: string;
};

export type RoleTemplate = {
  template_id: string;
  title: string;
  department: string;
  seniority_examples: string[];
  raw_jd_starter: string;
  suggested_soft_skills: string[];
  suggested_knockout_areas: string[];
  suggested_fixed_interview_questions: string[];
};

export type JobCriteriaUpdate = {
  improved_jd?: string | null;
  criteria_json?: Array<Record<string, unknown>> | null;
  must_haves_json?: string[] | null;
  nice_to_haves_json?: string[] | null;
  disqualifiers_json?: string[] | null;
  soft_skills_json?: string[] | null;
  knockout_areas_json?: string[] | null;
};

export type Candidate = {
  id: string;
  job_id: string;
  name: string | null;
  email: string | null;
  phone: string | null;
  resume_file_path: string | null;
  resume_text: string | null;
  resume_hash: string | null;
  parsed_profile_json: Record<string, unknown> | null;
  enriched_profile_json: Record<string, unknown> | null;
  status: CandidateStatus;
  latest_score?: CandidateScoreSummary | null;
  created_at: string;
  updated_at: string;
};

export type CandidateScoreSummary = {
  id: string;
  overall_score: number;
  recommendation: string;
  confidence: number;
  created_at: string;
};

export type CandidateScore = {
  id: string;
  candidate_id: string;
  job_id: string;
  overall_score: number;
  criteria_scores_json: Array<Record<string, unknown>>;
  strengths_json: string[];
  weaknesses_json: string[];
  risks_json: string[];
  evidence_json: Array<Record<string, unknown>> | Record<string, unknown> | null;
  recommendation: string;
  confidence: number;
  created_at: string;
  updated_at: string;
};

export type InterviewQuestion = {
  type: QuestionType;
  question: string;
  purpose?: string;
  evaluation_criteria?: string;
  weight?: number;
  is_mandatory?: boolean;
};

export type InterviewPlan = {
  questions?: InterviewQuestion[];
  [key: string]: unknown;
};

export type InterviewSession = {
  id: string;
  job_id: string;
  candidate_id: string;
  mode: "CHAT";
  status: InterviewSessionStatus;
  expires_at: string | null;
  started_at: string | null;
  ended_at: string | null;
  otp_verified_at: string | null;
  interview_plan_json: InterviewPlan | null;
  graph_state_json: Record<string, unknown> | null;
  security_events_json: Array<Record<string, unknown>> | null;
  created_at: string;
  updated_at: string;
};

export type InterviewSessionSummary = {
  id: string;
  job_id: string;
  candidate_id: string;
  mode: "CHAT";
  status: InterviewSessionStatus;
  expires_at: string | null;
  started_at: string | null;
  ended_at: string | null;
  created_at: string;
  question_count: number;
  evaluation_status: "EVALUATED" | "NOT_EVALUATED" | string;
};

export type InterviewInviteResponse = {
  message: string;
  expires_at: string;
};

export type InterviewEntry = {
  session_id: string;
  candidate_id: string;
  job_id: string;
  status: InterviewSessionStatus;
  expires_at: string | null;
  otp_verified: boolean;
};

export type LiveInterviewTurn = {
  status: InterviewSessionStatus;
  current_question_index: number;
  message: string | null;
  completed: boolean;
  client_session_nonce: string | null;
};

export type InterviewMessage = {
  id: string;
  interview_session_id: string;
  role: string;
  content: string;
  question_type: string | null;
  metadata_json: Record<string, unknown> | null;
  created_at: string;
};

export type InterviewEvaluation = {
  id: string;
  interview_session_id: string;
  candidate_id: string;
  job_id: string;
  overall_score: number;
  competency_scores_json: Array<Record<string, unknown>> | Record<string, unknown>;
  soft_skill_scores_json: Array<Record<string, unknown>> | Record<string, unknown>;
  strengths_json: string[];
  weaknesses_json: string[];
  red_flags_json: string[];
  evidence_json: Array<Record<string, unknown>> | Record<string, unknown>;
  missing_evidence_json: string[];
  recommendation: string;
  confidence: number;
  created_at: string;
  updated_at: string;
};

export type FinalScorecard = {
  id: string;
  candidate_id: string;
  job_id: string;
  resume_score: number;
  interview_score: number;
  soft_skill_score: number;
  overall_fit: number;
  risk_level: string;
  evidence_summary_json: Array<Record<string, unknown>> | Record<string, unknown>;
  candidate_fit_narrative: string;
  missing_evidence_json: string[];
  recommendation: string;
  confidence: number;
  created_at: string;
  updated_at: string;
};

export type AuditLog = {
  id: string;
  actor_user_id: string | null;
  entity_type: string;
  entity_id: string;
  action: string;
  metadata_json: Record<string, unknown> | null;
  created_at: string;
};

export type LlmCallLog = {
  id: string;
  task: string;
  model: string;
  input_hash: string;
  input_tokens: number | null;
  output_tokens: number | null;
  latency_ms: number;
  cache_hit: boolean;
  status: string;
  error: string | null;
  raw_response_path: string | null;
  created_at: string;
};

export type CommunicationLog = {
  id: string;
  job_id: string | null;
  candidate_id: string | null;
  interview_session_id: string | null;
  provider: string;
  channel: string;
  recipient: string;
  subject: string;
  body: string;
  status: string;
  metadata_json: Record<string, unknown> | null;
  created_at: string;
};

export type PilotFeedback = {
  id: string;
  user_id: string | null;
  candidate_id: string | null;
  job_id: string | null;
  interview_session_id: string | null;
  feedback_type: string;
  rating: number;
  comment: string | null;
  metadata_json: Record<string, unknown> | null;
  created_at: string;
};

export type PilotFeedbackCreate = {
  candidate_id?: string | null;
  job_id?: string | null;
  interview_session_id?: string | null;
  feedback_type: PilotFeedbackType;
  rating: number;
  comment?: string | null;
  metadata_json?: Record<string, unknown> | null;
};

export type PilotDashboardSummary = {
  jobs_count: number;
  candidates_count: number;
  interviews_completed_count: number;
  feedback_count: number;
  recent_feedback: PilotFeedback[];
  recent_llm_failures: LlmCallLog[];
  recent_audit_events: AuditLog[];
};
