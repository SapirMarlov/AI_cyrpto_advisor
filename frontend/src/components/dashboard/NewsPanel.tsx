import AnimatedList from "@/components/AnimatedList";
import { newsItemId } from "@/components/dashboard/itemIds";
import { VoteButtons } from "@/components/dashboard/VoteButtons";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { DashboardSection, NewsData, NewsItem } from "@/services/apiClient";

type NewsPanelProps = {
  section: DashboardSection<NewsData> | undefined;
  loading?: boolean;
};

export function NewsPanel({ section, loading = false }: NewsPanelProps) {
  const items = section?.data?.items ?? [];

  return (
    <Card className="animate-in fade-in h-full duration-300">
      <CardHeader>
        <CardTitle>Market news</CardTitle>
        <CardDescription>
          {section?.stale ? "Showing stale cached headlines." : "Latest headlines for your interests."}
        </CardDescription>
      </CardHeader>
      <CardContent className="pe-1">
        {loading ? <p className="text-muted-foreground text-sm">Loading news…</p> : null}
        {!loading && section?.error ? (
          <p className="text-destructive text-sm" role="alert">
            {section.error.message}
          </p>
        ) : null}
        {!loading && !section?.error && items.length === 0 ? (
          <p className="text-muted-foreground text-sm">No news items right now.</p>
        ) : null}
        {!loading && items.length > 0 ? (
          <AnimatedList
            items={items}
            getItemKey={(item: NewsItem) => item.url}
            enableArrowNavigation={false}
            showGradients
            displayScrollbar
            renderItem={(item: NewsItem, _index, selected) => (
              <article
                className={cn(
                  "space-y-2 rounded-lg border border-transparent px-2 py-2 transition-colors",
                  selected && "border-border bg-muted/40",
                )}
              >
                <a
                  href={item.url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-primary font-medium underline-offset-4 hover:underline"
                >
                  {item.title}
                </a>
                <p className="text-muted-foreground text-xs">
                  {item.source}
                  {item.published_at ? ` · ${item.published_at}` : ""}
                </p>
                <VoteButtons itemId={newsItemId(item.url)} itemType="news" />
              </article>
            )}
          />
        ) : null}
      </CardContent>
    </Card>
  );
}
