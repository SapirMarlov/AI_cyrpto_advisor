import { Navigate, Route, Routes } from "react-router-dom";

import {
  GuestOnly,
  RequireDashboard,
  RequireOnboarding,
} from "@/auth/guards";
import { DarkVeil } from "@/components/DarkVeil";
import { ThemeToggle } from "@/components/ThemeToggle";
import { DashboardPage } from "@/pages/Dashboard";
import { LoginPage } from "@/pages/Login";
import { OnboardingPage } from "@/pages/Onboarding";
import { SignupPage } from "@/pages/Signup";
import { useTheme } from "@/theme/ThemeProvider";

function AppShell({ children }: { children: React.ReactNode }) {
  const { theme } = useTheme();

  return (
    <div
      className={`text-foreground relative min-h-svh transition-colors duration-300 ${
        theme === "dark" ? "bg-transparent" : "bg-background"
      }`}
    >
      {theme === "dark" ? (
        <div
          className="pointer-events-none fixed inset-0 -z-10"
          aria-hidden="true"
        >
          <DarkVeil
            hueShift={270}
            noiseIntensity={0.015}
            scanlineIntensity={0}
            scanlineFrequency={0}
            speed={0.35}
            warpAmount={0.18}
          />
          <div
            className="absolute inset-0"
            style={{
              background:
                "linear-gradient(180deg, color-mix(in oklab, #A855F7 28%, transparent), color-mix(in oklab, #A855F7 10%, transparent))," +
                "color-mix(in oklab, var(--background) 45%, transparent)",
            }}
          />
        </div>
      ) : null}
      <div className="relative z-10">
        <div className="flex justify-end p-3">
          <ThemeToggle />
        </div>
        {children}
      </div>
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
