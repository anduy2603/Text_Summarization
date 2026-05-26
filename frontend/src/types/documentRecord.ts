/**
 * Compact persisted document summary (Phase 2).
 * Does not store full source article text.
 */
export type SummaryDocumentRecord = {
  filename: string | null;
  fileType: string;
  summary: string;
  sourceSentenceCount: number | null;
  selectedSentenceCount: number | null;
  createdAt: number;
};
