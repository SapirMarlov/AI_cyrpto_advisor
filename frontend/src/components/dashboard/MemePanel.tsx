import { memeItemId } from "@/components/dashboard/itemIds";
import { VoteButtons } from "@/components/dashboard/VoteButtons";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { DashboardSection, MemeData } from "@/services/apiClient";

type MemePanelProps = {
  section: DashboardSection<MemeData> | undefined;
  loading?: boolean;
};

export function MemePanel({ section, loading = false }: MemePanelProps) {
  const meme = section?.data;
  const itemId = memeItemId(meme?.permalink, meme?.image_url);

  return (
    <Card className="animate-in fade-in h-full duration-300">
      <CardHeader>
        <CardTitle>Meme of the day</CardTitle>
        <CardDescription>
          {section?.stale ? "Showing a stale meme." : "A light moment from crypto culture."}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {loading ? <p className="text-muted-foreground text-sm">Loading meme…</p> : null}
        {!loading && section?.error && !meme?.image_url ? (
          <p className="text-destructive text-sm" role="alert">
            {section.error.message}
          </p>
        ) : null}
        {!loading && !meme?.image_url && !section?.error ? (
          <p className="text-muted-foreground text-sm">No meme available.</p>
        ) : null}
        {!loading && meme?.image_url ? (
          <>
            <img
              src={meme.image_url}
              alt={meme.title || "Crypto meme"}
              className="max-h-72 w-full rounded-lg object-contain"
            />
            {meme.title ? <p className="text-sm font-medium">{meme.title}</p> : null}
            <VoteButtons itemId={itemId} itemType="meme" />
          </>
        ) : null}
      </CardContent>
    </Card>
  );
}
