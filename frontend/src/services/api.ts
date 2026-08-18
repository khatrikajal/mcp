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
}

export const api = new ApiClient();
