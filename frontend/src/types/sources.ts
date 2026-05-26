import type { UserSummaryStats } from "../userMetadata";

export type SourceKind = "file" | "text" | "url";

export type SourceStatus = "ready" | "summarizing" | "summarized" | "error";

export type SourceItem = {
  id: string;
  kind: SourceKind;
  title: string;
  createdAt: number;
  status: SourceStatus;
  preview: string;
  errorMessage?: string;
  file?: File;
  text?: string;
  url?: string;
  lastSummary?: string;
  lastStats?: UserSummaryStats | null;
};
