export function newsItemId(url: string): string {
  return url.trim();
}

export function memeItemId(permalink?: string, imageUrl?: string): string {
  const value = (permalink || imageUrl || "").trim();
  return value;
}

export function insightItemId(generatedAt: string): string {
  const date = generatedAt.slice(0, 10);
  return `insight-${date || "unknown"}`;
}
