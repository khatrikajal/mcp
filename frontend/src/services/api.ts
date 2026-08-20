/**
 * API Client - Centralized API communication.
 *
 * Features:
 * - Secure token handling
 * - Automatic retry with exponential backoff
 * - Request/response interceptors
 * - Error normalization
 */
import axios, {
  type AxiosInstance,
  type AxiosError,
  type AxiosRequestConfig,
} from "axios";
import type {
  AuthResponse,
  LoginRequest,
  RegisterRequest,
  User,
  Agent,
  Conversation,
  Message,
  ExecutionPlan,
  ApprovalRequest,
  MeetingDelegation,
  DelegationReport,
  DelegationStats,
  InterviewSession,
  InterviewQuestion,
  InterviewReport,
  InterviewStats,
  CreateInterviewRequest,
  AgentMemory,
  UserPreference,
  ConversationSummary,
  MemorySearchResult,
  MemoryStats,
  AgentContext,
  CreateMemoryRequest,
  CreatePreferenceRequest,
  MemorySearchRequest,
  MemoryType,
  PreferenceCategory,
} from "../types";
import { tokenStorage } from "../lib/security";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8001";

// Retry configuration
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000;
const RETRY_STATUS_CODES = [408, 429, 500, 502, 503, 504];

/**
 * API Error class for consistent error handling.
 */
export class ApiError extends Error {
  status: number;
  detail: string;
  code?: string;

  constructor(status: number, detail: string, code?: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
    this.code = code;
  }
}

/**
 * Sleep utility for retry delays.
 */
const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: `${API_BASE_URL}/api/v1`,
      headers: {
        "Content-Type": "application/json",
      },
      timeout: 30000, // 30 second timeout
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    // Request interceptor to add JWT token
    this.client.interceptors.request.use(
      (config) => {
        const token = tokenStorage.getToken();

        if (token) {
          // Check if token is expired
          if (tokenStorage.isTokenExpired()) {
            tokenStorage.clearToken();
            window.location.href = "/login";
            return Promise.reject(new Error("Token expired"));
          }

          config.headers.Authorization = `Bearer ${token}`;
        }

        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const status = error.response?.status;

        // Handle 401 Unauthorized
        if (status === 401) {
          tokenStorage.clearToken();
          window.location.href = "/login";
          return Promise.reject(
            new ApiError(401, "Session expired. Please login again.")
          );
        }

        // Handle rate limiting
        if (status === 429) {
          const retryAfter =
            error.response?.headers?.["retry-after"] || "60";
          return Promise.reject(
            new ApiError(
              429,
              `Rate limit exceeded. Please wait ${retryAfter} seconds.`
            )
          );
        }

        // Normalize error response
        const detail =
          (error.response?.data as { detail?: string })?.detail ||
          error.message ||
          "An error occurred";

        return Promise.reject(new ApiError(status || 500, detail));
      }
    );
  }

  /**
   * Make a request with automatic retry.
   */
  private async requestWithRetry<T>(
    config: AxiosRequestConfig,
    retries = MAX_RETRIES
  ): Promise<T> {
    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        const response = await this.client.request<T>(config);
        return response.data;
      } catch (error) {
        lastError = error as Error;

        // Check if we should retry
        if (error instanceof ApiError && RETRY_STATUS_CODES.includes(error.status)) {
          if (attempt < retries) {
            const delay = RETRY_DELAY * Math.pow(2, attempt);
            await sleep(delay);
            continue;
          }
        }

        throw error;
      }
    }

    throw lastError;
  }

  // ==========================================================================
  // Auth endpoints
  // ==========================================================================

  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>(
      "/auth/login",
      credentials
    );

    // Store token securely
    tokenStorage.setToken(response.data.access_token);

    return response.data;
  }

  async register(data: RegisterRequest): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>(
      "/auth/register",
      data
    );

    // Store token securely
    tokenStorage.setToken(response.data.access_token);

    return response.data;
  }

  async getCurrentUser(): Promise<User> {
    return this.requestWithRetry<User>({ method: "GET", url: "/auth/me" });
  }

  logout(): void {
    tokenStorage.clearToken();
  }

  // ==========================================================================
  // Agent endpoints
  // ==========================================================================

  async getAgents(): Promise<Agent[]> {
    return this.requestWithRetry<Agent[]>({ method: "GET", url: "/agents" });
  }

  async getAgent(id: string): Promise<Agent> {
    return this.requestWithRetry<Agent>({
      method: "GET",
      url: `/agents/${id}`,
    });
  }

  async createAgent(data: Partial<Agent>): Promise<Agent> {
    const response = await this.client.post<Agent>("/agents", data);
    return response.data;
  }

  async updateAgent(id: string, data: Partial<Agent>): Promise<Agent> {
    const response = await this.client.put<Agent>(`/agents/${id}`, data);
    return response.data;
  }

  async deleteAgent(id: string): Promise<void> {
    await this.client.delete(`/agents/${id}`);
  }

  // ==========================================================================
  // Conversation endpoints
  // ==========================================================================

  async getConversations(agentId?: string): Promise<Conversation[]> {
    const params = agentId ? { agent_id: agentId } : {};
    return this.requestWithRetry<Conversation[]>({
      method: "GET",
      url: "/conversations",
      params,
    });
  }

  async getConversation(id: string): Promise<Conversation> {
    return this.requestWithRetry<Conversation>({
      method: "GET",
      url: `/conversations/${id}`,
    });
  }

  async createConversation(data: Partial<Conversation>): Promise<Conversation> {
    const response = await this.client.post<Conversation>(
      "/conversations",
      data
    );
    return response.data;
  }

  async deleteConversation(id: string): Promise<void> {
    await this.client.delete(`/conversations/${id}`);
  }

  async getMessages(conversationId: string): Promise<Message[]> {
    return this.requestWithRetry<Message[]>({
      method: "GET",
      url: `/conversations/${conversationId}/messages`,
    });
  }

  async sendMessage(conversationId: string, content: string): Promise<Message> {
    const response = await this.client.post<Message>(
      `/conversations/${conversationId}/messages`,
      { content }
    );
    return response.data;
  }

  // ==========================================================================
  // Planning endpoints
  // ==========================================================================

  async createExecutionPlan(
    conversationId: number,
    agentId: number,
    userRequest: string
  ): Promise<ExecutionPlan> {
    const response = await this.client.post<ExecutionPlan>("/planning", {
      conversation_id: conversationId,
      agent_id: agentId,
      user_request: userRequest,
    });
    return response.data;
  }

  async getExecutionPlan(planId: number): Promise<ExecutionPlan> {
    return this.requestWithRetry<ExecutionPlan>({
      method: "GET",
      url: `/planning/${planId}`,
    });
  }

  async getPlansForConversation(
    conversationId: number
  ): Promise<ExecutionPlan[]> {
    return this.requestWithRetry<ExecutionPlan[]>({
      method: "GET",
      url: `/planning/conversation/${conversationId}`,
    });
  }

  async cancelExecutionPlan(planId: number): Promise<{ message: string }> {
    const response = await this.client.post<{ message: string }>(
      `/planning/${planId}/cancel`
    );
    return response.data;
  }

  // ==========================================================================
  // Approval endpoints
  // ==========================================================================

  async getPendingApprovals(): Promise<ApprovalRequest[]> {
    return this.requestWithRetry<ApprovalRequest[]>({
      method: "GET",
      url: "/approvals",
    });
  }

  async getApprovalRequest(approvalId: number): Promise<ApprovalRequest> {
    return this.requestWithRetry<ApprovalRequest>({
      method: "GET",
      url: `/approvals/${approvalId}`,
    });
  }

  async approveRequest(approvalId: number): Promise<ApprovalRequest> {
    const response = await this.client.post<ApprovalRequest>(
      `/approvals/${approvalId}/approve`
    );
    return response.data;
  }

  async rejectRequest(
    approvalId: number,
    reason?: string
  ): Promise<ApprovalRequest> {
    const response = await this.client.post<ApprovalRequest>(
      `/approvals/${approvalId}/reject`,
      { reason }
    );
    return response.data;
  }

  async getApprovalsForPlan(planId: number): Promise<ApprovalRequest[]> {
    return this.requestWithRetry<ApprovalRequest[]>({
      method: "GET",
      url: `/approvals/plan/${planId}`,
    });
  }

  // ==========================================================================
  // Delegation endpoints
  // ==========================================================================

  async getDelegations(params?: {
    status?: string;
    importance?: string;
    limit?: number;
    offset?: number;
  }): Promise<MeetingDelegation[]> {
    return this.requestWithRetry<MeetingDelegation[]>({
      method: "GET",
      url: "/delegations",
      params,
    });
  }

  async getUpcomingDelegations(minutesAhead: number = 60): Promise<MeetingDelegation[]> {
    return this.requestWithRetry<MeetingDelegation[]>({
      method: "GET",
      url: "/delegations/upcoming",
      params: { minutes_ahead: minutesAhead },
    });
  }

  async getPendingDelegations(): Promise<MeetingDelegation[]> {
    return this.requestWithRetry<MeetingDelegation[]>({
      method: "GET",
      url: "/delegations/pending",
    });
  }

  async getDelegationStats(): Promise<DelegationStats> {
    return this.requestWithRetry<DelegationStats>({
      method: "GET",
      url: "/delegations/stats",
    });
  }

  async getDelegation(delegationId: number): Promise<MeetingDelegation> {
    return this.requestWithRetry<MeetingDelegation>({
      method: "GET",
      url: `/delegations/${delegationId}`,
    });
  }

  async getDelegationReport(delegationId: number): Promise<DelegationReport> {
    return this.requestWithRetry<DelegationReport>({
      method: "GET",
      url: `/delegations/${delegationId}/report`,
    });
  }

  async approveDelegation(delegationId: number): Promise<MeetingDelegation> {
    const response = await this.client.post<MeetingDelegation>(
      `/delegations/${delegationId}/approve`
    );
    return response.data;
  }

  async rejectDelegation(
    delegationId: number,
    reason?: string
  ): Promise<MeetingDelegation> {
    const response = await this.client.post<MeetingDelegation>(
      `/delegations/${delegationId}/reject`,
      { reason }
    );
    return response.data;
  }

  async joinMeeting(delegationId: number): Promise<MeetingDelegation> {
    const response = await this.client.post<MeetingDelegation>(
      `/delegations/${delegationId}/join`
    );
    return response.data;
  }

  async completeDelegation(delegationId: number): Promise<MeetingDelegation> {
    const response = await this.client.post<MeetingDelegation>(
      `/delegations/${delegationId}/complete`
    );
    return response.data;
  }

  async sendDelegationReport(delegationId: number): Promise<{ message: string }> {
    const response = await this.client.post<{ message: string }>(
      `/delegations/${delegationId}/send-report`
    );
    return response.data;
  }

  async processMeetings(lookAheadHours: number = 24): Promise<MeetingDelegation[]> {
    const response = await this.client.post<MeetingDelegation[]>(
      "/delegations/process-meetings",
      { look_ahead_hours: lookAheadHours }
    );
    return response.data;
  }

  async deleteDelegation(delegationId: number): Promise<void> {
    await this.client.delete(`/delegations/${delegationId}`);
  }

  // ==========================================================================
  // Interview endpoints
  // ==========================================================================

  async getInterviews(params?: {
    status_filter?: string;
    limit?: number;
  }): Promise<InterviewSession[]> {
    return this.requestWithRetry<InterviewSession[]>({
      method: "GET",
      url: "/interviews",
      params,
    });
  }

  async getUpcomingInterviews(hoursAhead: number = 24): Promise<InterviewSession[]> {
    return this.requestWithRetry<InterviewSession[]>({
      method: "GET",
      url: "/interviews/upcoming",
      params: { hours_ahead: hoursAhead },
    });
  }

  async getInterviewStats(): Promise<InterviewStats> {
    return this.requestWithRetry<InterviewStats>({
      method: "GET",
      url: "/interviews/stats",
    });
  }

  async getInterview(interviewId: number): Promise<InterviewSession> {
    return this.requestWithRetry<InterviewSession>({
      method: "GET",
      url: `/interviews/${interviewId}`,
    });
  }

  async createInterview(data: CreateInterviewRequest): Promise<InterviewSession> {
    const response = await this.client.post<InterviewSession>("/interviews", data);
    return response.data;
  }

  async updateInterview(
    interviewId: number,
    data: Partial<CreateInterviewRequest>
  ): Promise<InterviewSession> {
    const response = await this.client.put<InterviewSession>(
      `/interviews/${interviewId}`,
      data
    );
    return response.data;
  }

  async cancelInterview(interviewId: number): Promise<void> {
    await this.client.delete(`/interviews/${interviewId}`);
  }

  async generateQuestions(
    interviewId: number,
    numQuestions: number = 8
  ): Promise<InterviewQuestion[]> {
    const response = await this.client.post<InterviewQuestion[]>(
      `/interviews/${interviewId}/generate-questions`,
      { num_questions: numQuestions }
    );
    return response.data;
  }

  async getInterviewQuestions(interviewId: number): Promise<InterviewQuestion[]> {
    return this.requestWithRetry<InterviewQuestion[]>({
      method: "GET",
      url: `/interviews/${interviewId}/questions`,
    });
  }

  async startInterview(interviewId: number): Promise<{
    status: string;
    interview_id: number;
    notetaker_id?: string;
    intro_audio_duration: number;
    question_audio_files: string[];
    total_questions: number;
  }> {
    const response = await this.client.post(`/interviews/${interviewId}/start`);
    return response.data;
  }

  async endInterview(interviewId: number): Promise<{
    overall_score: number;
    recommendation: string;
    competency_scores: Record<string, number>;
    strengths: string[];
    weaknesses: string[];
    report_summary?: string;
  }> {
    const response = await this.client.post(`/interviews/${interviewId}/end`);
    return response.data;
  }

  async getInterviewReport(interviewId: number): Promise<InterviewReport> {
    return this.requestWithRetry<InterviewReport>({
      method: "GET",
      url: `/interviews/${interviewId}/report`,
    });
  }

  async sendInterviewReport(
    interviewId: number,
    recipients: string[]
  ): Promise<{ status: string; recipients: string[]; sent_at: string }> {
    const response = await this.client.post(
      `/interviews/${interviewId}/send-report`,
      recipients
    );
    return response.data;
  }

  async generateInterviewAudio(interviewId: number): Promise<{
    status: string;
    audio_files: string[];
    count: number;
  }> {
    const response = await this.client.post(
      `/interviews/${interviewId}/generate-audio`
    );
    return response.data;
  }

  // ==========================================================================
  // Memory endpoints
  // ==========================================================================

  async createMemory(data: CreateMemoryRequest): Promise<AgentMemory> {
    const response = await this.client.post<AgentMemory>("/memory", data);
    return response.data;
  }

  async getAgentMemories(
    agentId: number,
    params?: {
      memory_type?: MemoryType;
      limit?: number;
    }
  ): Promise<AgentMemory[]> {
    return this.requestWithRetry<AgentMemory[]>({
      method: "GET",
      url: `/memory/agent/${agentId}`,
      params,
    });
  }

  async getMemory(memoryId: number): Promise<AgentMemory> {
    return this.requestWithRetry<AgentMemory>({
      method: "GET",
      url: `/memory/${memoryId}`,
    });
  }

  async updateMemory(
    memoryId: number,
    data: {
      content?: string;
      summary?: string;
      importance?: number;
    }
  ): Promise<AgentMemory> {
    const response = await this.client.patch<AgentMemory>(
      `/memory/${memoryId}`,
      data
    );
    return response.data;
  }

  async deleteMemory(memoryId: number): Promise<void> {
    await this.client.delete(`/memory/${memoryId}`);
  }

  async searchMemories(data: MemorySearchRequest): Promise<MemorySearchResult[]> {
    const response = await this.client.post<MemorySearchResult[]>(
      "/memory/search",
      data
    );
    return response.data;
  }

  async getAgentContext(
    agentId: number,
    maxMemories: number = 10
  ): Promise<AgentContext> {
    return this.requestWithRetry<AgentContext>({
      method: "GET",
      url: `/memory/agent/${agentId}/context`,
      params: { max_memories: maxMemories },
    });
  }

  async getMemoryStats(agentId: number): Promise<MemoryStats> {
    return this.requestWithRetry<MemoryStats>({
      method: "GET",
      url: `/memory/agent/${agentId}/stats`,
    });
  }

  // Preferences
  async createPreference(data: CreatePreferenceRequest): Promise<UserPreference> {
    const response = await this.client.post<UserPreference>(
      "/memory/preferences",
      data
    );
    return response.data;
  }

  async getPreferences(params?: {
    category?: PreferenceCategory;
    min_confidence?: number;
  }): Promise<UserPreference[]> {
    return this.requestWithRetry<UserPreference[]>({
      method: "GET",
      url: "/memory/preferences",
      params,
    });
  }

  async deletePreference(preferenceId: number): Promise<void> {
    await this.client.delete(`/memory/preferences/${preferenceId}`);
  }

  // Summarization
  async summarizeConversation(
    conversationId: number,
    force: boolean = false
  ): Promise<ConversationSummary> {
    const response = await this.client.post<ConversationSummary>(
      `/memory/conversations/${conversationId}/summarize`,
      {},
      { params: { force } }
    );
    return response.data;
  }

  async getConversationSummary(conversationId: number): Promise<ConversationSummary> {
    return this.requestWithRetry<ConversationSummary>({
      method: "GET",
      url: `/memory/conversations/${conversationId}/summary`,
    });
  }

  async getUserSummaries(params?: {
    agent_id?: number;
    limit?: number;
  }): Promise<ConversationSummary[]> {
    return this.requestWithRetry<ConversationSummary[]>({
      method: "GET",
      url: "/memory/summaries",
      params,
    });
  }

  async learnFromConversation(conversationId: number): Promise<{
    conversation_id: number;
    messages_processed: number;
    preferences_extracted: Array<{ key: string; value: string }>;
  }> {
    const response = await this.client.post(
      `/memory/learn/conversation/${conversationId}`
    );
    return response.data;
  }

  async cleanupExpiredMemories(): Promise<{ deleted_count: number }> {
    const response = await this.client.post("/memory/cleanup/expired");
    return response.data;
  }

  // ==========================================================================
  // Analytics endpoints
  // ==========================================================================

  async getDashboardSummary(): Promise<{
    total_agents: number;
    total_conversations: number;
    total_messages: number;
    active_users_today: number;
    pending_approvals: number;
    meetings_this_week: number;
    interviews_this_week: number;
    security_alerts_24h: number;
  }> {
    return this.requestWithRetry({
      method: "GET",
      url: "/analytics/dashboard",
    });
  }

  async getAnalyticsMetrics(params?: {
    start_date?: string;
    end_date?: string;
  }): Promise<{
    date_range: { start: string; end: string };
    events_by_category: Record<string, number>;
    active_users: number;
    top_agents: Array<{ name: string; usage: number }>;
  }> {
    return this.requestWithRetry({
      method: "GET",
      url: "/analytics/metrics",
      params,
    });
  }

  async getDailyActivity(days: number = 30): Promise<
    Array<{
      date: string;
      event_count: number;
      unique_users: number;
    }>
  > {
    return this.requestWithRetry({
      method: "GET",
      url: "/analytics/daily-activity",
      params: { days },
    });
  }

  async getToolUsageStats(days: number = 30): Promise<
    Array<{
      tool_name: string;
      execution_count: number;
      success_count: number;
      success_rate: number;
    }>
  > {
    return this.requestWithRetry({
      method: "GET",
      url: "/analytics/tool-usage",
      params: { days },
    });
  }

  async getSecurityAlerts(params?: {
    hours?: number;
    min_threat_level?: string;
    limit?: number;
  }): Promise<
    Array<{
      id: number;
      event_type: string;
      threat_level: string;
      description?: string;
      ip_address?: string;
      user_id?: number;
      created_at: string;
    }>
  > {
    return this.requestWithRetry({
      method: "GET",
      url: "/analytics/security-alerts",
      params,
    });
  }

  async getFailedLoginPatterns(params?: {
    hours?: number;
    min_count?: number;
  }): Promise<
    Array<{
      ip_address: string;
      attempt_count: number;
    }>
  > {
    return this.requestWithRetry({
      method: "GET",
      url: "/analytics/failed-logins",
      params,
    });
  }

  async getUserActivity(
    userId: number,
    params?: {
      start_date?: string;
      end_date?: string;
      event_types?: string[];
      limit?: number;
    }
  ): Promise<
    Array<{
      id: number;
      event_type: string;
      action: string;
      resource_type?: string;
      resource_id?: number;
      description?: string;
      ip_address?: string;
      created_at: string;
    }>
  > {
    return this.requestWithRetry({
      method: "GET",
      url: `/analytics/user-activity/${userId}`,
      params,
    });
  }

  async exportAnalytics(params?: {
    start_date?: string;
    end_date?: string;
    format?: "json" | "csv";
  }): Promise<unknown> {
    return this.requestWithRetry({
      method: "GET",
      url: "/analytics/export",
      params,
    });
  }

  // ==========================================================================
  // Security endpoints
  // ==========================================================================

  async checkPromptInjection(
    text: string,
    useLlm: boolean = true
  ): Promise<{
    is_injection: boolean;
    threat_level: string;
    detected_patterns: string[];
  }> {
    const response = await this.client.post("/security/check-prompt", {
      text,
      use_llm: useLlm,
    });
    return response.data;
  }

  async getRateLimitStatus(
    action: string,
    toolName?: string
  ): Promise<{
    action: string;
    tool_name?: string;
    limit: number;
    current: number;
    remaining: number;
    is_allowed: boolean;
  }> {
    return this.requestWithRetry({
      method: "GET",
      url: "/security/rate-limit-status",
      params: { action, tool_name: toolName },
    });
  }

  async getPermissions(category?: string): Promise<
    Array<{
      id: number;
      name: string;
      description?: string;
      category: string;
    }>
  > {
    return this.requestWithRetry({
      method: "GET",
      url: "/security/permissions",
      params: { category },
    });
  }

  async getRoles(): Promise<
    Array<{
      id: number;
      name: string;
      description?: string;
      is_system_role: boolean;
      permission_count: number;
      user_count: number;
    }>
  > {
    return this.requestWithRetry({
      method: "GET",
      url: "/security/roles",
    });
  }

  async createRole(data: {
    name: string;
    description?: string;
    permission_names: string[];
  }): Promise<{
    id: number;
    name: string;
    description?: string;
    is_system_role: boolean;
    permission_count: number;
    user_count: number;
  }> {
    const response = await this.client.post("/security/roles", data);
    return response.data;
  }

  async updateRole(
    roleId: number,
    data: {
      name?: string;
      description?: string;
      permission_names?: string[];
    }
  ): Promise<{
    id: number;
    name: string;
    description?: string;
    is_system_role: boolean;
    permission_count: number;
    user_count: number;
  }> {
    const response = await this.client.put(`/security/roles/${roleId}`, data);
    return response.data;
  }

  async deleteRole(roleId: number): Promise<void> {
    await this.client.delete(`/security/roles/${roleId}`);
  }

  async getUserPermissions(userId: number): Promise<{
    user_id: number;
    permissions: string[];
    roles: string[];
  }> {
    return this.requestWithRetry({
      method: "GET",
      url: `/security/users/${userId}/permissions`,
    });
  }

  async assignRoleToUser(
    userId: number,
    roleId: number
  ): Promise<{
    status: string;
    user_id: number;
    role_id: number;
    created_at: string;
  }> {
    const response = await this.client.post(`/security/users/${userId}/roles`, {
      role_id: roleId,
    });
    return response.data;
  }

  async removeRoleFromUser(userId: number, roleId: number): Promise<void> {
    await this.client.delete(`/security/users/${userId}/roles/${roleId}`);
  }

  async getPermissionReport(): Promise<{
    total_roles: number;
    roles: Array<{
      id: number;
      name: string;
      description?: string;
      is_system_role: boolean;
      user_count: number;
      permission_count: number;
      permissions: string[];
    }>;
  }> {
    return this.requestWithRetry({
      method: "GET",
      url: "/security/permission-report",
    });
  }
}

export const api = new ApiClient();
