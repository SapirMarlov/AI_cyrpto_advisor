import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { DashboardSection, PricesData } from "@/services/apiClient";

type PricesPanelProps = {
  section: DashboardSection<PricesData> | undefined;
  loading?: boolean;
};

function formatUsd(value: number | null | undefined) {
  if (value == null || Number.isNaN(value)) {
    return "—";
  }
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(value);
}

function formatChange(value: number | null | undefined) {
  if (value == null || Number.isNaN(value)) {
    return "—";
  }
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}%`;
}

export function PricesPanel({ section, loading = false }: PricesPanelProps) {
  const prices = section?.data?.prices ?? {};
  const entries = Object.entries(prices);

  return (
    <Card className="animate-in fade-in h-full duration-300">
      <CardHeader>
        <CardTitle>Coin prices</CardTitle>
        <CardDescription>
          {section?.stale ? "Showing stale cached prices." : "Spot prices for your watchlist."}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {loading ? <p className="text-muted-foreground text-sm">Loading prices…</p> : null}
        {!loading && section?.error ? (
          <p className="text-destructive text-sm" role="alert">
            {section.error.message}
          </p>
        ) : null}
        {!loading && !section?.error && entries.length === 0 ? (
          <p className="text-muted-foreground text-sm">No price data available.</p>
        ) : null}
        {!loading
          ? entries.map(([coin, quote]) => (
              <div
                key={coin}
                className="flex items-center justify-between gap-3 border-b border-border py-2 last:border-0"
              >
                <span className="font-medium capitalize">{coin}</span>
                <div className="text-right text-sm">
                  <div>{formatUsd(quote.usd)}</div>
                  <div className="text-muted-foreground">{formatChange(quote.change_24h)}</div>
                </div>
              </div>
            ))
          : null}
      </CardContent>
    </Card>
  );
}
