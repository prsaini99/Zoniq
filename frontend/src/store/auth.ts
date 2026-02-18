import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User } from "@/types";
import { authApi, emailOtpApi, removeToken, getToken } from "@/lib/api";

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
      user: null,
      isLoading: false,
      isAuthenticated: false,
      error: null,
      _hasHydrated: false,

      setUser: (user) =>
        set({
          user,
          isAuthenticated: !!user,
        }),

      setLoading: (isLoading) => set({ isLoading }),

      setError: (error) => set({ error }),

      setHasHydrated: (state) => set({ _hasHydrated: state }),

      clearError: () => set({ error: null }),

      login: async (username, email, password) => {
        set({ isLoading: true, error: null });
        try {
          const response = await authApi.signIn({ username, email, password });
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
      name: "zoniq-auth",
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
      },
    }
  )
);

// Selector hooks for common patterns
export const useUser = () => useAuthStore((state) => state.user);
export const useIsAuthenticated = () => useAuthStore((state) => state.isAuthenticated);
export const useIsAdmin = () => useAuthStore((state) => state.user?.role === "admin");
export const useHasHydrated = () => useAuthStore((state) => state._hasHydrated);
