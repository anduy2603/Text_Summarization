import type { ChatMessage } from "./chat";
import type { SummaryDocumentRecord } from "./documentRecord";

export type ChatSession = {
  id: string;
  title: string;
  /** Xem trước: thường là đoạn tóm tắt gần nhất */
  preview: string;
  projectId?: string;
  createdAt: number;
  updatedAt: number;
  /** Metadata tài liệu chuẩn hóa (không lưu nội dung nguồn dài). */
  document?: SummaryDocumentRecord;
  messages: ChatMessage[];
};
