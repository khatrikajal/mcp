// User and Organization types
export interface User {
  id: number;
  email: string;
  name: string;
  role: "admin" | "user" | "viewer";
  organization_id: number;
  created_at: string;
}

export interface Organization {
  id: number;
  name: string;
  plan_type: string;
  created_at: string;
}

// Agent types
export interface Agent {
  id: number;
  user_id: number;
  organization_id: number;
  name: string;
  description: string;
  system_instructions: string;
  created_at: string;
  updated_at: string;
}

export interface AgentToolPermission {
  id: number;
  agent_id: number;
  tool_name: string;
  permission_level: "enabled" | "disabled" | "requires_approval";
}

// Conversation types
export interface Conversation {
  id: number;
  user_id: number;
  agent_id: number;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: number;
  conversation_id: number;
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
}

// Auth types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// Planning types
export interface PlanStep {
  step_number: number;
  description: string;
  tool: string;
  arguments: Record<string, any>;
  requires_approval: boolean;
  status?: "pending" | "running" | "completed" | "failed" | "skipped";
  result?: any;
}

export interface ExecutionPlan {
  id: number;
  conversation_id: number;
  user_id: number;
  agent_id: number;
  user_request: string;
  status: "pending" | "running" | "paused" | "completed" | "failed" | "cancelled";
  current_step: number;
  plan: PlanStep[];
  step_results: Array<{
    step_number: number;
    status: string;
    result?: any;
    error?: string;
  }>;
  final_result?: string;
  error_message?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

// Approval types
export interface ApprovalRequest {
  id: number;
  user_id: number;
  agent_id: number;
  tool_name: string;
  tool_arguments: Record<string, any>;
  description: string;
  status: "pending" | "approved" | "rejected" | "expired";
  execution_plan_id?: number;
  step_index?: number;
  approved_at?: string;
  approved_by_user_id?: number;
  rejection_reason?: string;
  expires_at: string;
  created_at: string;
}

// Delegation types
export type MeetingImportance = "critical" | "high" | "medium" | "low";
export type DelegationStatus =
  | "pending"
  | "approved"
  | "rejected"
  | "joining"
  | "joined"
  | "recording"
  | "completed"
  | "failed";

export interface ActionItem {
  task: string;
  assignee: string;
  status: string;
}

export interface MeetingDelegation {
  id: number;
  user_id: number;
  organization_id: number;
  meeting_id: string;
  meeting_title: string;
  meeting_description?: string;
  meeting_start_time: string;
  meeting_end_time: string;
  meeting_location?: string;
  meeting_organizer?: string;
  meeting_attendees: Array<{ email: string; name?: string }>;
  importance: MeetingImportance;
  importance_score: number;
  importance_reasons: string[];
  status: DelegationStatus;
  auto_approved: boolean;
  requires_approval: boolean;
  notetaker_id?: string;
  notetaker_joined_at?: string;
  notetaker_left_at?: string;
  introduction_script?: string;
  report_summary?: string;
  action_items?: ActionItem[];
  decisions?: string[];
  report_sent: boolean;
  report_sent_at?: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
  approved_at?: string;
  completed_at?: string;
}

export interface DelegationReport {
  id: number;
  meeting_title: string;
  meeting_start_time: string;
  meeting_end_time: string;
  meeting_attendees: Array<{ email: string; name?: string }>;
  transcript?: string;
  report?: string;
  report_summary?: string;
  action_items?: ActionItem[];
  decisions?: string[];
  report_sent: boolean;
}

export interface DelegationStats {
  total: number;
  pending: number;
  approved: number;
  completed: number;
  failed: number;
}

// Interview types
export type InterviewType = "technical" | "behavioral" | "hr" | "mixed";
export type InterviewStatus =
  | "scheduled"
  | "preparing"
  | "ready"
  | "in_progress"
  | "analyzing"
  | "completed"
  | "cancelled"
  | "failed";
export type InterviewRecommendation =
  | "strong_hire"
  | "hire"
  | "maybe"
  | "no_hire"
  | "strong_no_hire";

export interface InterviewQuestion {
  id: number;
  question_number: number;
  question_text: string;
  question_type: InterviewType;
  competency?: string;
  difficulty: "easy" | "medium" | "hard";
  weight: number;
  candidate_answer?: string;
  score?: number;
  feedback?: string;
  audio_generated: boolean;
  audio_url?: string;
}

export interface InterviewSession {
  id: number;
  user_id: number;
  organization_id: number;
  candidate_name: string;
  candidate_email: string;
  candidate_phone?: string;
  candidate_resume_url?: string;
  candidate_linkedin?: string;
  position_title: string;
  position_description?: string;
  required_skills: string[];
  interview_type: InterviewType;
  duration_minutes: number;
  scheduled_time: string;
  meeting_url?: string;
  language: string;
  status: InterviewStatus;
  notetaker_id?: string;
  overall_score?: number;
  recommendation?: InterviewRecommendation;
  strengths: string[];
  weaknesses: string[];
  competency_scores: Record<string, number>;
  report_summary?: string;
  report_sent: boolean;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  questions_count: number;
}

export interface InterviewReport {
  interview_id: number;
  candidate_name: string;
  position_title: string;
  overall_score: number;
  recommendation: InterviewRecommendation;
  report: string;
  report_summary: string;
  questions: InterviewQuestion[];
  strengths: string[];
  weaknesses: string[];
  competency_scores: Record<string, number>;
  completed_at?: string;
}

export interface InterviewStats {
  total: number;
  scheduled: number;
  ready: number;
  in_progress: number;
  completed: number;
  cancelled: number;
  average_score: number;
  recommendations: Record<InterviewRecommendation, number>;
}

export interface CreateInterviewRequest {
  candidate_name: string;
  candidate_email: string;
  candidate_phone?: string;
  candidate_resume_url?: string;
  candidate_linkedin?: string;
  position_title: string;
  position_description?: string;
  required_skills: string[];
  interview_type: InterviewType;
  duration_minutes: number;
  scheduled_time: string;
  meeting_url?: string;
  language?: string;
}

// Memory types
export type MemoryType =
  | "preference"
  | "fact"
  | "interaction"
  | "summary"
  | "meeting"
  | "email"
  | "context";

export type PreferenceCategory =
  | "scheduling"
  | "communication"
  | "workflow"
  | "personal"
  | "tool";

export interface AgentMemory {
  id: number;
  agent_id: number;
  user_id: number;
  memory_type: MemoryType;
  key: string;
  content: string;
  summary?: string;
  source?: string;
  source_id?: number;
  importance: number;
  access_count: number;
  last_accessed?: string;
  expires_at?: string;
  created_at: string;
  updated_at: string;
}

export interface UserPreference {
  id: number;
  user_id: number;
  category: PreferenceCategory;
  preference_key: string;
  preference_value: string;
  confidence: number;
  source_type?: string;
  times_confirmed: number;
  times_contradicted: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ConversationSummary {
  id: number;
  conversation_id: number;
  summary: string;
  key_topics: string[];
  key_entities: string[];
  action_items: string[];
  decisions: string[];
  message_count: number;
  time_range_start?: string;
  time_range_end?: string;
  created_at: string;
}

export interface MemorySearchResult {
  memory: AgentMemory;
  similarity: number;
}

export interface MemoryStats {
  total_memories: number;
  by_type: Record<MemoryType, number>;
  average_importance: number;
}

export interface AgentContext {
  memories: Array<{
    type: string;
    key: string;
    content: string;
    importance: number;
  }>;
  preferences: Array<{
    category: string;
    key: string;
    value: string;
    confidence: number;
  }>;
  recent_topics: string[];
}

export interface CreateMemoryRequest {
  agent_id: number;
  memory_type: MemoryType;
  key: string;
  content: string;
  summary?: string;
  source?: string;
  source_id?: number;
  importance?: number;
  expires_in_hours?: number;
}

export interface CreatePreferenceRequest {
  category: PreferenceCategory;
  preference_key: string;
  preference_value: string;
}

export interface MemorySearchRequest {
  query: string;
  agent_id: number;
  memory_types?: MemoryType[];
  top_k?: number;
  threshold?: number;
}

// API Response types
export interface ApiError {
  detail: string;
  status_code: number;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}
