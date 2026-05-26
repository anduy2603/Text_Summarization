export const DEFAULT_PROJECT_ID = "proj_default";

export type LengthPresetId = "short" | "medium" | "long";
export const LENGTH_PRESETS: { id: LengthPresetId; label: string; sentences: number }[] = [
  { id: "short", label: "Ngắn", sentences: 2 },
  { id: "medium", label: "Vừa", sentences: 4 },
  { id: "long", label: "Chi tiết", sentences: 7 },
];
