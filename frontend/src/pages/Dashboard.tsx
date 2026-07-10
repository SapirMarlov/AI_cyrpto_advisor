import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "@/auth/AuthContext";
import { InsightPanel } from "@/components/dashboard/InsightPanel";
import { MemePanel } from "@/components/dashboard/MemePanel";
import { NewsPanel } from "@/components/dashboard/NewsPanel";
import { PricesPanel } from "@/components/dashboard/PricesPanel";
import { Button } from "@/components/ui/button";
import {
  getDailyDashboard,
  type DailyDashboardData,
} from "@/services/apiClient";

export function DashboardPage() {
  const { logout, user } = useAuth();
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState<DailyDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      const result = await getDailyDashboard();
      if (cancelled) {
        return;
      }
      if (!result.ok) {
        setError(result.error.message);
        setDashboard(null);
        setLoading(false);
        return;
      }
      setDashboard(result.data);
      setLoading(false);
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  async function onLogout() {
    await logout();
    navigate("/login");
  }

  const sections = dashboard?.sections;

  return (
    <main className="animate-in fade-in mx-auto max-w-6xl space-y-6 px-4 pb-8 duration-300">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">AI Crypto Advisor</h1>
          <p className="text-muted-foreground text-sm">
            {user?.email ? `Signed in as ${user.email}` : "Your daily crypto briefing"}
          </p>
        </div>
        <Button type="button" variant="outline" onClick={() => void onLogout()}>
          Log out
        </Button>
      </header>

      {error ? (
        <p className="text-destructive text-sm" role="alert">
          {error}
        </p>
      ) : null}

      <div className="grid gap-4 md:grid-cols-2">
        <NewsPanel section={sections?.news} loading={loading} />
        <PricesPanel section={sections?.prices} loading={loading} />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <InsightPanel
            section={sections?.insight}
            generatedAt={dashboard?.generated_at}
            loading={loading}
          />
        </div>
        <MemePanel section={sections?.meme} loading={loading} />
      </div>
    </main>
  );
}
