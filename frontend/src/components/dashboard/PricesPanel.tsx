import { useEffect, useMemo, useState } from "react";
import { ChartColumn, List } from "lucide-react";
import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from "recharts";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import type { DashboardSection, PriceQuote, PricesData } from "@/services/apiClient";
import { cn } from "@/lib/utils";

type PricesPanelProps = {
  section: DashboardSection<PricesData> | undefined;
  loading?: boolean;
};

type ViewMode = "list" | "chart";

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

function sparklineToSeries(sparkline: number[] | null | undefined) {
  if (!sparkline?.length) {
    return [];
  }
  const step = Math.max(1, Math.ceil(sparkline.length / 48));
  const sampled: number[] = [];
  for (let i = 0; i < sparkline.length; i += step) {
    sampled.push(sparkline[i]);
  }
  const last = sparkline[sparkline.length - 1];
  if (sampled[sampled.length - 1] !== last) {
    sampled.push(last);
  }
  return sampled.map((price, index) => {
    const t = sampled.length === 1 ? 1 : index / (sampled.length - 1);
    const daysAgo = Math.round(7 * (1 - t));
    return {
      day: daysAgo === 0 ? "now" : `${daysAgo}d`,
      price,
    };
  });
}

function changeTone(value: number | null | undefined) {
  if (value == null || Number.isNaN(value) || value === 0) {
    return "text-muted-foreground";
  }
  return value > 0 ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400";
}

function PricesChartView({
  entries,
}: {
  entries: [string, PriceQuote][];
}) {
  const [selectedCoin, setSelectedCoin] = useState(entries[0]?.[0] ?? "");

  useEffect(() => {
    if (!entries.some(([coin]) => coin === selectedCoin)) {
      setSelectedCoin(entries[0]?.[0] ?? "");
    }
  }, [entries, selectedCoin]);

  const quote = entries.find(([coin]) => coin === selectedCoin)?.[1];
  const series = useMemo(
    () => sparklineToSeries(quote?.sparkline_7d),
    [quote?.sparkline_7d],
  );
  const isUp = (quote?.change_24h ?? 0) >= 0;
  const stroke = isUp ? "#059669" : "#e11d48";

  const chartConfig = {
    price: {
      label: "Price (USD)",
      color: stroke,
    },
  } satisfies ChartConfig;

  return (
    <div className="space-y-3">
      <ToggleGroup
        type="single"
        variant="outline"
        size="sm"
        value={selectedCoin}
        onValueChange={(value) => {
          if (value) {
            setSelectedCoin(value);
          }
        }}
        className="flex max-w-full flex-wrap"
        aria-label="Select coin"
      >
        {entries.map(([coin]) => (
          <ToggleGroupItem key={coin} value={coin} className="capitalize">
            {coin}
          </ToggleGroupItem>
        ))}
      </ToggleGroup>

      <div className="flex items-end justify-between gap-3">
        <div>
          <p className="text-muted-foreground text-xs uppercase tracking-wide">
            7-day price
          </p>
          <p className="text-2xl font-semibold tabular-nums">
            {formatUsd(quote?.usd)}
          </p>
        </div>
        <p className={cn("text-sm font-medium tabular-nums", changeTone(quote?.change_24h))}>
          {formatChange(quote?.change_24h)} 24h
        </p>
      </div>

      {series.length > 1 ? (
        <ChartContainer config={chartConfig} className="aspect-[16/9] w-full">
          <AreaChart data={series} margin={{ left: 4, right: 4, top: 8, bottom: 0 }}>
            <defs>
              <linearGradient id={`fill-${selectedCoin}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={stroke} stopOpacity={0.35} />
                <stop offset="95%" stopColor={stroke} stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid vertical={false} strokeDasharray="3 3" />
            <XAxis
              dataKey="day"
              tickLine={false}
              axisLine={false}
              tickMargin={8}
              minTickGap={24}
            />
            <YAxis
              tickLine={false}
              axisLine={false}
              tickMargin={4}
              width={56}
              domain={["auto", "auto"]}
              tickFormatter={(value: number) =>
                value >= 1000 ? `${(value / 1000).toFixed(1)}k` : value.toFixed(0)
              }
            />
            <ChartTooltip
              content={
                <ChartTooltipContent
                  formatter={(value) => formatUsd(Number(value))}
                />
              }
            />
            <Area
              type="monotone"
              dataKey="price"
              stroke={stroke}
              strokeWidth={2}
              fill={`url(#fill-${selectedCoin})`}
              isAnimationActive={false}
            />
          </AreaChart>
        </ChartContainer>
      ) : (
        <p className="text-muted-foreground text-sm">
          Chart data is unavailable for this coin right now.
        </p>
      )}
    </div>
  );
}

export function PricesPanel({ section, loading = false }: PricesPanelProps) {
  const [view, setView] = useState<ViewMode>("list");
  const prices = section?.data?.prices ?? {};
  const entries = Object.entries(prices);
  const hasData = !loading && !section?.error && entries.length > 0;

  return (
    <Card className="animate-in fade-in h-full duration-300">
      <CardHeader className="flex flex-row items-start justify-between gap-3 space-y-0">
        <div className="space-y-1.5">
          <CardTitle>Coin prices</CardTitle>
          <CardDescription>
            {section?.stale
              ? "Showing stale cached prices."
              : view === "chart"
                ? "7-day chart for your watchlist."
                : "Spot prices for your watchlist."}
          </CardDescription>
        </div>
        {hasData ? (
          <ToggleGroup
            type="single"
            variant="outline"
            size="sm"
            value={view}
            onValueChange={(value) => {
              if (value === "list" || value === "chart") {
                setView(value);
              }
            }}
            aria-label="Price view mode"
          >
            <ToggleGroupItem value="list" aria-label="List view">
              <List />
              <span className="sr-only sm:not-sr-only sm:ml-1">List</span>
            </ToggleGroupItem>
            <ToggleGroupItem value="chart" aria-label="Chart view">
              <ChartColumn />
              <span className="sr-only sm:not-sr-only sm:ml-1">Chart</span>
            </ToggleGroupItem>
          </ToggleGroup>
        ) : null}
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
        {hasData && view === "list"
          ? entries.map(([coin, quote]) => (
              <div
                key={coin}
                className="flex items-center justify-between gap-3 border-b border-border py-2 last:border-0"
              >
                <span className="font-medium capitalize">{coin}</span>
                <div className="text-right text-sm">
                  <div className="tabular-nums">{formatUsd(quote.usd)}</div>
                  <div className={cn("tabular-nums", changeTone(quote.change_24h))}>
                    {formatChange(quote.change_24h)}
                  </div>
                </div>
              </div>
            ))
          : null}
        {hasData && view === "chart" ? <PricesChartView entries={entries} /> : null}
      </CardContent>
    </Card>
  );
}
