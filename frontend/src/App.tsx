import { Navigate, Route, Routes } from "react-router-dom";

import {
  GuestOnly,
  RequireDashboard,
  RequireOnboarding,
} from "@/auth/guards";
import { ThemeToggle } from "@/components/ThemeToggle";
import { DashboardPage } from "@/pages/Dashboard";
import { LoginPage } from "@/pages/Login";
import { OnboardingPage } from "@/pages/Onboarding";
import { SignupPage } from "@/pages/Signup";

function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-background text-foreground min-h-svh transition-colors duration-300">
      <div className="flex justify-end p-3">
        <ThemeToggle />
      </div>
      {children}
    </div>
  );
}

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route element={<GuestOnly />}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
        </Route>
        <Route element={<RequireOnboarding />}>
          <Route path="/onboarding" element={<OnboardingPage />} />
        </Route>
        <Route element={<RequireDashboard />}>
          <Route path="/dashboard" element={<DashboardPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </AppShell>
  );
}
