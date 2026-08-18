/**
 * Authentication state store.
 *
 * Uses Zustand for state management with secure token handling.
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User, LoginRequest, RegisterRequest } from "../types";
import { api } from "../services/api";
import { tokenStorage } from "../lib/security";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (credentials: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => void;
  clearError: () => void;
  checkAuth: () => Promise<boolean>;
}

/**
 * Extract error message from various error types.
 */
function extractErrorMessage(error: unknown): string {
  if (!error) {
    return "An unknown error occurred";
  }

  // API Error
  if (typeof error === "object" && error !== null && "detail" in error) {
    return String((error as { detail: string }).detail);
  }

  // Axios error
  if (typeof error === "object" && error !== null) {
    const axiosError = error as {
      response?: { data?: { detail?: string } };
      message?: string;
    };

    if (axiosError.response?.data?.detail) {
      return axiosError.response.data.detail;
    }

    if (axiosError.message) {
      return axiosError.message;
    }
  }

  // Standard Error
  if (error instanceof Error) {
    return error.message;
  }

  return "An unknown error occurred";
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (credentials) => {
        set({ isLoading: true, error: null });

        try {
          const response = await api.login(credentials);

          set({
            user: response.user,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch (error) {
          const message = extractErrorMessage(error);

          set({
            user: null,
            isAuthenticated: false,
            error: message,
            isLoading: false,
          });

          throw error;
        }
      },

      register: async (data) => {
        set({ isLoading: true, error: null });

        try {
          const response = await api.register(data);

          set({
            user: response.user,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch (error) {
          const message = extractErrorMessage(error);

          set({
            user: null,
            isAuthenticated: false,
            error: message,
            isLoading: false,
          });

          throw error;
        }
      },

      logout: () => {
        // Clear token from secure storage
        tokenStorage.clearToken();

        // Clear API client state
        api.logout();

        // Clear store state
        set({
          user: null,
          isAuthenticated: false,
          error: null,
        });
      },

      clearError: () => set({ error: null }),

      /**
       * Check if user is authenticated and token is valid.
       * Used for initial app load and route guards.
       */
      checkAuth: async () => {
        // Check if we have a token
        if (!tokenStorage.hasToken()) {
          set({ isAuthenticated: false, user: null });
          return false;
        }

        // Check if token is expired
        if (tokenStorage.isTokenExpired()) {
          tokenStorage.clearToken();
          set({ isAuthenticated: false, user: null });
          return false;
        }

        // If we have user data in store and token is valid, we're authenticated
        const state = get();
        if (state.user && state.isAuthenticated) {
          return true;
        }

        // Try to fetch current user to validate token
        try {
          const user = await api.getCurrentUser();
          set({ user, isAuthenticated: true });
          return true;
        } catch {
          tokenStorage.clearToken();
          set({ isAuthenticated: false, user: null });
          return false;
        }
      },
    }),
    {
      name: "auth-storage",
      // Only persist user data, not sensitive fields
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
      // Use sessionStorage instead of localStorage for security
      storage: {
        getItem: (name) => {
          const value = sessionStorage.getItem(name);
          return value ? JSON.parse(value) : null;
        },
        setItem: (name, value) => {
          sessionStorage.setItem(name, JSON.stringify(value));
        },
        removeItem: (name) => {
          sessionStorage.removeItem(name);
        },
      },
    }
  )
);
