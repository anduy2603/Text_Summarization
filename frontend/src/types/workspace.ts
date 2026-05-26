export type Project = {
  id: string;
  name: string;
  createdAt: number;
};

export type DocumentStatus = "pending" | "processing" | "completed" | "error";

export type DocumentListItem = {
  sessionId: string;
  title: string;
  dateLabel: string;
  formatLabel: string;
  status: DocumentStatus;
  compressionLabel: string | null;
  readMinutes: number | null;
  icon: "description" | "language" | "text_snippet";
};
