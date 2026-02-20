/*
 * auth.ts — Zustand store for authentication state management.
 * Persists user data and authentication status to localStorage via
 * zustand/persist. Provides actions for login, registration, email OTP
 * verification, logout, and profile fetching. Also exports convenience
 * selector hooks for common auth checks.
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User } from "@/types";
import { authApi, emailOtpApi, removeToken, getToken } from "@/lib/api";

// Shape of the authentication store: state fields and action methods
interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  error: string | null;
  _hasHydrated: boolean;

  // Actions
  setUser: (user: User | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setHasHydrated: (state: boolean) => void;
  login: (username: string, email: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string, emailOtpCode: string, phone?: string) => Promise<void>;
  loginWithEmailOTP: (email: string, code: string) => Promise<void>;
  logout: () => Promise<void>;
  fetchProfile: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // ---- Initial state ----
      user: null,
      isLoading: false,
      isAuthenticated: false,
      error: null,
      _hasHydrated: false, // Tracks whether persisted state has been rehydrated from localStorage

      // Sets the user and derives isAuthenticated from whether user is non-null
      setUser: (user) =>
        set({
          user,
          isAuthenticated: !!user,
        }),

      // Toggles the global loading indicator
      setLoading: (isLoading) => set({ isLoading }),

      // Sets an error message to display in the UI
      setError: (error) => set({ error }),

      // Marks rehydration as complete (called by persist middleware's onRehydrateStorage)
      setHasHydrated: (state) => set({ _hasHydrated: state }),

      // Clears any current error message
      clearError: () => set({ error: null }),

      // Authenticates a user with username/email/password credentials
      login: async (username, email, password) => {
        set({ isLoading: true, error: null });
        try {
          const response = await authApi.signIn({ username, email, password });
          // Build user object from the authorized account response
          const user: User = {
            id: response.id,
            ...response.authorizedAccount,
          };
          set({ user, isAuthenticated: true, isLoading: false });
        } catch (error: unknown) {
          const message =
            error instanceof Error
              ? error.message
              : "Login failed. Please check your credentials.";
          set({ error: message, isLoading: false });
          throw error;
        }
      },

      // Registers a new user (requires a pre-verified email OTP code)
      register: async (username, email, password, emailOtpCode, phone?) => {
        set({ isLoading: true, error: null });
        try {
          const response = await authApi.signUp({ username, email, password, emailOtpCode, phone });
          const user: User = {
            id: response.id,
            ...response.authorizedAccount,
          };
          set({ user, isAuthenticated: true, isLoading: false });
        } catch (error: unknown) {
          const message =
            error instanceof Error ? error.message : "Registration failed.";
          set({ error: message, isLoading: false });
          throw error;
        }
      },

      // Authenticates a user via email OTP (passwordless login)
      loginWithEmailOTP: async (email, code) => {
        set({ isLoading: true, error: null });
        try {
          const response = await emailOtpApi.verify(email, code);
          const user: User = {
            id: response.id,
            ...response.authorizedAccount,
          };
          set({ user, isAuthenticated: true, isLoading: false });
        } catch (error: unknown) {
          const message =
            error instanceof Error ? error.message : "Email OTP verification failed.";
          set({ error: message, isLoading: false });
          throw error;
        }
      },

      // Logs the user out: calls the server, removes the token, resets state, and redirects to home
      logout: async () => {
        set({ isLoading: true });
        try {
          await authApi.signOut();
        } catch {
          // Ignore logout errors
        } finally {
          removeToken();
          set({ user: null, isAuthenticated: false, isLoading: false });
          // Full page redirect to ensure proper state reset
          if (typeof window !== "undefined") {
            window.location.href = "/";
          }
        }
      },

      // Fetches the user's profile from the server using the stored token.
      // Clears auth state if the token is missing or the request fails.
      fetchProfile: async () => {
        const token = getToken();
        if (!token) {
          set({ user: null, isAuthenticated: false });
          return;
        }

        set({ isLoading: true });
        try {
          const user = await authApi.getProfile();
          set({ user, isAuthenticated: true, isLoading: false });
        } catch {
          removeToken();
          set({ user: null, isAuthenticated: false, isLoading: false });
        }
      },
    }),
    {
      name: "zoniq-auth", // localStorage key for persisted auth state
      // Only persist user and isAuthenticated — not loading/error/transient state
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
      // Called once localStorage data has been rehydrated into the store
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
      },
    }
  )
);

// ---- Convenience selector hooks ----

// Returns the current user object (or null)
export const useUser = () => useAuthStore((state) => state.user);

// Returns whether the user is authenticated
export const useIsAuthenticated = () => useAuthStore((state) => state.isAuthenticated);

// Returns whether the current user has admin privileges
export const useIsAdmin = () => useAuthStore((state) => state.user?.role === "admin");

// Returns whether the persisted state has finished rehydrating from localStorage
export const useHasHydrated = () => useAuthStore((state) => state._hasHydrated);
