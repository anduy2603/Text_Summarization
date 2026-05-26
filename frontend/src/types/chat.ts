import type { UserSummaryStats } from "../userMetadata";

export type ChatMessage =
  | {
      id: string;
      role: "user";
      kind: "action";
      content: string;
    }
  | {
      id: string;
      role: "user";
      kind: "text";
      content: string;
    }
  | {
      id: string;
      role: "user";
      kind: "file";
      fileName: string;
    }
  | {
      id: string;
      role: "user";
      kind: "url";
      url: string;
    }
  | {
      id: string;
      role: "assistant";
      content: string;
      stats: UserSummaryStats | null;
      sourceTitle?: string;
    }
  | {
      id: string;
      role: "system";
      content: string;
      tone: "error";
    };
