import {
  summarizeFile,
  summarizeText,
  summarizeUrl,
  type SummarizeOptions,
} from "../api";
import { formatUserSummaryStats } from "../userMetadata";
import { isHttpUrl } from "./inputDetect";

export type SummarizeInputResult =
  | {
      ok: true;
      summary: string;
      metadata: Record<string, unknown>;
      stats: ReturnType<typeof formatUserSummaryStats>;
    }
  | { ok: false; error: string };

export async function summarizeFromFile(
  file: File,
  options: SummarizeOptions,
): Promise<SummarizeInputResult> {
  const result = await summarizeFile(file, options);
  if ("error" in result) return { ok: false, error: result.error };
  return {
    ok: true,
    summary: result.summary,
    metadata: result.metadata ?? {},
    stats: formatUserSummaryStats(result.metadata ?? {}, file.name),
  };
}

export async function summarizeFromText(
  text: string,
  options: SummarizeOptions,
): Promise<SummarizeInputResult> {
  const result = await summarizeText({ text, ...options });
  if ("error" in result) return { ok: false, error: result.error };
  return {
    ok: true,
    summary: result.summary,
    metadata: result.metadata ?? {},
    stats: formatUserSummaryStats(result.metadata ?? {}),
  };
}

export async function summarizeFromUrl(
  url: string,
  options: SummarizeOptions,
): Promise<SummarizeInputResult> {
  const result = await summarizeUrl(url, options);
  if ("error" in result) return { ok: false, error: result.error };
  return {
    ok: true,
    summary: result.summary,
    metadata: result.metadata ?? {},
    stats: formatUserSummaryStats(result.metadata ?? {}),
  };
}

export async function summarizeUserMessage(
  input: { file?: File | null; text?: string },
  options: SummarizeOptions,
): Promise<SummarizeInputResult> {
  if (input.file) return summarizeFromFile(input.file, options);
  const text = (input.text ?? "").trim();
  if (!text) return { ok: false, error: "Vui lòng nhập văn bản hoặc chọn tệp." };
  if (isHttpUrl(text)) return summarizeFromUrl(text, options);
  return summarizeFromText(text, options);
}
