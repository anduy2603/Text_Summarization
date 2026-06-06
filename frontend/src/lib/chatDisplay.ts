import type { UserSummaryStats } from "../userMetadata";

export function formatStatsLine(stats: UserSummaryStats | null): string | null {
  if (!stats) return null;
  const parts: string[] = [];
  if (stats.fileName) parts.push(`Tệp: ${stats.fileName}`);
  if (stats.formatLabel) parts.push(`Định dạng: ${stats.formatLabel}`);
  if (stats.selectedSentences != null && stats.sourceSentences != null) {
    parts.push(`${stats.selectedSentences}/${stats.sourceSentences} câu`);
  }
  if (stats.compressionPct != null) parts.push(`Nén ~${stats.compressionPct}%`);
  return parts.length > 0 ? parts.join(" · ") : null;
}

export function newChatId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}
