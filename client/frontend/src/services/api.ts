import axios, { type AxiosInstance, type AxiosError } from "axios";
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
} from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8001";

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: `${API_BASE_URL}/api/v1`,
      headers: {
        "Content-Type": "application/json",
      },
    });

    // Request interceptor to add JWT token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem("access_token");
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor to handle errors
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Token expired or invalid - clear auth and redirect to login
          localStorage.removeItem("access_token");
          localStorage.removeItem("user");
          window.location.href = "/login";
        }
        return Promise.reject(error);
      }
    );
  }

  // Auth endpoints
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>("/auth/login", credentials);
    return response.data;
  }

  async register(data: RegisterRequest): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>("/auth/register", data);
    return response.data;
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.client.get<User>("/auth/me");
    return response.data;
  }

  // Agent endpoints
  async getAgents(): Promise<Agent[]> {
    const response = await this.client.get<Agent[]>("/agents");
    return response.data;
  }

  async getAgent(id: string): Promise<Agent> {
    const response = await this.client.get<Agent>(`/agents/${id}`);
    return response.data;
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

  // Conversation endpoints
  async getConversations(agentId?: string): Promise<Conversation[]> {
    const params = agentId ? { agent_id: agentId } : {};
    const response = await this.client.get<Conversation[]>("/conversations", { params });
    return response.data;
  }

  async getConversation(id: string): Promise<Conversation> {
    const response = await this.client.get<Conversation>(`/conversations/${id}`);
    return response.data;
  }

  async createConversation(data: Partial<Conversation>): Promise<Conversation> {
    const response = await this.client.post<Conversation>("/conversations", data);
    return response.data;
  }

  async getMessages(conversationId: string): Promise<Message[]> {
    const response = await this.client.get<Message[]>(`/conversations/${conversationId}/messages`);
    return response.data;
  }

  async sendMessage(conversationId: string, content: string): Promise<Message> {
    const response = await this.client.post<Message>(`/conversations/${conversationId}/messages`, {
      content,
    });
    return response.data;
  }

  // Planning endpoints
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
    const response = await this.client.get<ExecutionPlan>(`/planning/${planId}`);
    return response.data;
  }

  async getPlansForConversation(conversationId: number): Promise<ExecutionPlan[]> {
    const response = await this.client.get<ExecutionPlan[]>(`/planning/conversation/${conversationId}`);
    return response.data;
  }

  async cancelExecutionPlan(planId: number): Promise<{ message: string }> {
    const response = await this.client.post<{ message: string }>(`/planning/${planId}/cancel`);
    return response.data;
  }

  // Approval endpoints
  async getPendingApprovals(): Promise<ApprovalRequest[]> {
    const response = await this.client.get<ApprovalRequest[]>("/approvals");
    return response.data;
  }

  async getApprovalRequest(approvalId: number): Promise<ApprovalRequest> {
    const response = await this.client.get<ApprovalRequest>(`/approvals/${approvalId}`);
    return response.data;
  }

  async approveRequest(approvalId: number): Promise<ApprovalRequest> {
    const response = await this.client.post<ApprovalRequest>(`/approvals/${approvalId}/approve`);
    return response.data;
  }

  async rejectRequest(approvalId: number, reason?: string): Promise<ApprovalRequest> {
    const response = await this.client.post<ApprovalRequest>(`/approvals/${approvalId}/reject`, {
      reason,
    });
    return response.data;
  }

  async getApprovalsForPlan(planId: number): Promise<ApprovalRequest[]> {
    const response = await this.client.get<ApprovalRequest[]>(`/approvals/plan/${planId}`);
    return response.data;
  }
}

export const api = new ApiClient();
