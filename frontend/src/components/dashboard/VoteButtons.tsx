import { useState } from "react";
import { ThumbsDown, ThumbsUp } from "lucide-react";

import { Button } from "@/components/ui/button";
import { vote, type VoteItemType, type VoteType } from "@/services/apiClient";

type VoteButtonsProps = {
  itemId: string;
  itemType: VoteItemType;
};

export function VoteButtons({ itemId, itemType }: VoteButtonsProps) {
  const [selected, setSelected] = useState<VoteType | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onVote(next: VoteType) {
    if (!itemId || pending) {
      return;
    }

    const previous = selected;
    setSelected(next);
    setError(null);
    setPending(true);

    const result = await vote(itemId, itemType, next);
    setPending(false);

    if (!result.ok) {
      setSelected(previous);
      setError(result.error.message);
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <Button
          type="button"
          size="sm"
          variant={selected === "up" ? "default" : "outline"}
          disabled={pending || !itemId}
          onClick={() => void onVote("up")}
          aria-label="Thumbs up"
        >
          <ThumbsUp />
        </Button>
        <Button
          type="button"
          size="sm"
          variant={selected === "down" ? "default" : "outline"}
          disabled={pending || !itemId}
          onClick={() => void onVote("down")}
          aria-label="Thumbs down"
        >
          <ThumbsDown />
        </Button>
      </div>
      {error ? (
        <p className="text-destructive text-xs" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
