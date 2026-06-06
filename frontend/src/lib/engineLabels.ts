export const ENGINE_LABELS: Record<string, string> = {
  tfidf: "TF-IDF",
  textrank: "TextRank",
  "phobert-extractive": "PhoBERT",
  vit5: "ViT5",
  hybrid: "Hybrid",
};

export function engineLabel(name: string): string {
  return ENGINE_LABELS[name] ?? name;
}
