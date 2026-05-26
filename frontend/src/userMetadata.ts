/** User-facing labels for backend source_type values. */
const SOURCE_LABELS: Record<string, string> = {
  txt: "TXT",
  docx: "DOCX",
  pdf: "PDF",
  text: "Văn bản",
  url: "URL",
};

export type UserSummaryStats = {
  formatLabel: string | null;
  selectedSentences: number | null;
  sourceSentences: number | null;
  compressionPct: number | null;
  fileName: string | null;
  latencyMs: number | null;
  engineName: string | null;
};

export function formatUserSummaryStats(
  metadata: Record<string, unknown> | null,
  fileName?: string | null,
): UserSummaryStats {
  if (!metadata) {
    return {
      formatLabel: null,
      selectedSentences: null,
      sourceSentences: null,
      compressionPct: null,
      fileName: fileName ?? null,
      latencyMs: null,
      engineName: null,
    };
  }

  const sourceType =
    typeof metadata.source_type === "string" ? metadata.source_type.toLowerCase() : null;
  const formatLabel = sourceType ? (SOURCE_LABELS[sourceType] ?? sourceType.toUpperCase()) : null;

  const selected =
    typeof metadata.selected_sentence_count === "number"
      ? metadata.selected_sentence_count
      : typeof metadata.resolved_target_k === "number"
        ? metadata.resolved_target_k
        : null;

  const sourceSentences =
    typeof metadata.sentence_count === "number" ? metadata.sentence_count : null;

  let compressionPct: number | null = null;
  if (typeof metadata.compression_ratio_chars === "number") {
    compressionPct = Math.round(metadata.compression_ratio_chars * 1000) / 10;
  }

  let resolvedFileName = fileName ?? null;
  const inputMeta = metadata.input_metadata;
  if (!resolvedFileName && inputMeta && typeof inputMeta === "object") {
    const name = (inputMeta as Record<string, unknown>).file_name;
    if (typeof name === "string" && name.trim()) resolvedFileName = name.trim();
  }

  const latencyMs =
    typeof metadata.summarizer_latency_ms === "number"
      ? metadata.summarizer_latency_ms
      : null;

  const engineName =
    typeof metadata.engine === "string" ? metadata.engine : null;

  return {
    formatLabel,
    selectedSentences: selected,
    sourceSentences,
    compressionPct,
    fileName: resolvedFileName,
    latencyMs,
    engineName,
  };
}
