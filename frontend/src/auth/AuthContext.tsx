import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  login as apiLogin,
  logout as apiLogout,
  me,
  signup as apiSignup,
  type User,
} from "@/services/apiClient";

type AuthStatus = "loading" | "authenticated" | "unauthenticated";

type AuthContextValue = {
  user: User | null;
  onboardingCompleted: boolean;
  status: AuthStatus;
  login: (
    email: string,
    password: string,
  ) => Promise<{ ok: true } | { ok: false; message: string }>;
  signup: (
    email: string,
    password: string,
  ) => Promise<{ ok: true } | { ok: false; message: string }>;
  logout: () => Promise<void>;
  refreshMe: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [onboardingCompleted, setOnboardingCompleted] = useState(false);
  const [status, setStatus] = useState<AuthStatus>("loading");

  const refreshMe = useCallback(async () => {
    const result = await me();
    if (result.ok) {
      setUser(result.data.user);
      setOnboardingCompleted(result.data.onboarding_completed);
      setStatus("authenticated");
      return;
    }
    setUser(null);
    setOnboardingCompleted(false);
    setStatus("unauthenticated");
  }, []);

  useEffect(() => {
    void refreshMe();
  }, [refreshMe]);

  const login = useCallback(
    async (email: string, password: string) => {
      const result = await apiLogin(email, password);
      if (!result.ok) {
        return { ok: false as const, message: result.error.message };
      }
      await refreshMe();
      return { ok: true as const };
    },
    [refreshMe],
  );

  const signup = useCallback(
    async (email: string, password: string) => {
      const result = await apiSignup(email, password);
      if (!result.ok) {
        return { ok: false as const, message: result.error.message };
      }
      await refreshMe();
      return { ok: true as const };
    },
    [refreshMe],
  );

  const logout = useCallback(async () => {
    await apiLogout();
    setUser(null);
    setOnboardingCompleted(false);
    setStatus("unauthenticated");
  }, []);

  const value = useMemo(
    () => ({
      user,
      onboardingCompleted,
      status,
      login,
      signup,
      logout,
      refreshMe,
    }),
    [user, onboardingCompleted, status, login, signup, logout, refreshMe],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
