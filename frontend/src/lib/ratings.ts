const RATINGS_KEY = "vietsum_ratings_v1";

export type Rating = "up" | "down";

function loadRatings(): Record<string, Rating> {
  try {
    const raw = localStorage.getItem(RATINGS_KEY);
    if (!raw) return {};
    return JSON.parse(raw) as Record<string, Rating>;
  } catch {
    return {};
  }
}

export function getRating(sessionId: string): Rating | null {
  return loadRatings()[sessionId] ?? null;
}

export function setRating(sessionId: string, rating: Rating | null): void {
  try {
    const all = loadRatings();
    if (rating === null) {
      delete all[sessionId];
    } else {
      all[sessionId] = rating;
    }
    localStorage.setItem(RATINGS_KEY, JSON.stringify(all));
  } catch {
    /* ignore */
  }
}

export function getAllRatings(): Record<string, Rating> {
  return loadRatings();
}

export function ratingsSummary(): { up: number; down: number; total: number } {
  const all = loadRatings();
  const values = Object.values(all);
  const up = values.filter((v) => v === "up").length;
  const down = values.filter((v) => v === "down").length;
  return { up, down, total: up + down };
}
