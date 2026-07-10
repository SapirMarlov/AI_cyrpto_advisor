import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "@/auth/AuthContext";

function AuthLoading() {
  return (
    <div className="text-muted-foreground flex min-h-[40vh] items-center justify-center p-6 text-sm">
      Checking session…
    </div>
  );
}

export function GuestOnly() {
  const { status, onboardingCompleted } = useAuth();

  if (status === "loading") {
    return <AuthLoading />;
  }

  if (status === "authenticated") {
    return (
      <Navigate
        to={onboardingCompleted ? "/dashboard" : "/onboarding"}
        replace
      />
    );
  }

  return <Outlet />;
}

export function RequireAuth() {
  const { status } = useAuth();

  if (status === "loading") {
    return <AuthLoading />;
  }

  if (status === "unauthenticated") {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}

export function RequireOnboarding() {
  const { status, onboardingCompleted } = useAuth();

  if (status === "loading") {
    return <AuthLoading />;
  }

  if (status === "unauthenticated") {
    return <Navigate to="/login" replace />;
  }

  if (onboardingCompleted) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
}

export function RequireDashboard() {
  const { status, onboardingCompleted } = useAuth();

  if (status === "loading") {
    return <AuthLoading />;
  }

  if (status === "unauthenticated") {
    return <Navigate to="/login" replace />;
  }

  if (!onboardingCompleted) {
    return <Navigate to="/onboarding" replace />;
  }

  return <Outlet />;
}
