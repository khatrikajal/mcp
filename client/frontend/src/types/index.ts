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
