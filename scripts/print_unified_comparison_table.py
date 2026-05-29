from __future__ import annotations

"""
Print a unified 5-engine comparison table from official benchmark results.

Reads the latest JSON reports from notebooks/results/official/validation/ and assembles
a single Markdown table covering all engines: TF-IDF, TextRank, PhoBERT, ViT5, Hybrid.

Example:
  python scripts/print_unified_comparison_table.py
  python scripts/print_unified_comparison_table.py --format csv
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_DIR = ROOT / "notebooks" / "results" / "official" / "validation"

# Engine display order and labels
ENGINE_ORDER = ["tfidf", "textrank", "phobert-extractive", "vit5", "hybrid"]
ENGINE_LABELS = {
    "tfidf": "TF-IDF",
    "textrank": "TextRank",
    "phobert-extractive": "PhoBERT",
    "vit5": "ViT5",
    "hybrid": "Hybrid",
}
ENGINE_TYPES = {
    "tfidf": "Extractive",
    "textrank": "Extractive",
    "phobert-extractive": "Extractive",
    "vit5": "Abstractive",
    "hybrid": "Hybrid",
}


def load_latest_report(pattern: str) -> dict | None:
    """Return the most recently created JSON file matching glob pattern."""
    matches = sorted(OFFICIAL_DIR.glob(pattern))
    if not matches:
        return None
    latest = matches[-1]
    return json.loads(latest.read_text(encoding="utf-8"))


def extract_engine_row(data: dict, engine: str) -> dict | None:
    """Extract metric row for a given engine from a report dict."""
    for rec in data.get("summary_by_engine", []):
        if rec.get("engine") == engine:
            return rec
    # Fallback: best_by_engine (extractive report schema)
    best = data.get("best_by_engine", {})
    if engine in best:
        return best[engine]
    return None


def build_table() -> list[dict]:
    rows = []

    # Extractive engines — from engine_compare_report (latest)
    extractive_report = load_latest_report("engine_compare_report_*.json")
    if extractive_report:
        for engine in ("tfidf", "textrank", "phobert-extractive"):
            rec = extract_engine_row(extractive_report, engine)
            if rec:
                rows.append({
                    "engine": engine,
                    "type": ENGINE_TYPES[engine],
                    "n": rec.get("n", extractive_report.get("subset_limit", "?")),
                    "rouge1_f": rec.get("rouge1_f"),
                    "rouge2_f": rec.get("rouge2_f"),
                    "rougeL_f": rec.get("rougeL_f"),
                    "latency_ms": (rec.get("summarizer_core_latency_sec") or 0) * 1000,
                    "compression_pct": (rec.get("compression_ratio") or 0) * 100,
                    "repetition_pct": (rec.get("repetition_rate") or 0) * 100,
                    "source": extractive_report.get("report_schema_version", "extractive"),
                })

    # ViT5 — from vit5_vs_textrank_report (latest in official/)
    vit5_report = load_latest_report("vit5_vs_textrank_report_*.json")
    if vit5_report:
        rec = extract_engine_row(vit5_report, "vit5")
        if rec:
            rows.append({
                "engine": "vit5",
                "type": ENGINE_TYPES["vit5"],
                "n": rec.get("n", vit5_report.get("subset_limit", "?")),
                "rouge1_f": rec.get("rouge1_f"),
                "rouge2_f": rec.get("rouge2_f"),
                "rougeL_f": rec.get("rougeL_f"),
                "latency_ms": (rec.get("summarizer_core_latency_sec") or 0) * 1000,
                "compression_pct": (rec.get("compression_ratio") or 0) * 100,
                "repetition_pct": (rec.get("repetition_rate") or 0) * 100,
                "source": vit5_report.get("report_schema_version", "vit5"),
            })

    # Hybrid — from hybrid_engine_report (latest in official/)
    hybrid_report = load_latest_report("hybrid_engine_report_*.json")
    if hybrid_report:
        rec = extract_engine_row(hybrid_report, "hybrid")
        if rec:
            rows.append({
                "engine": "hybrid",
                "type": ENGINE_TYPES["hybrid"],
                "n": rec.get("n", hybrid_report.get("subset_limit", "?")),
                "rouge1_f": rec.get("rouge1_f"),
                "rouge2_f": rec.get("rouge2_f"),
                "rougeL_f": rec.get("rougeL_f"),
                "latency_ms": (rec.get("summarizer_core_latency_sec") or 0) * 1000,
                "compression_pct": (rec.get("compression_ratio") or 0) * 100,
                "repetition_pct": (rec.get("repetition_rate") or 0) * 100,
                "source": hybrid_report.get("report_schema_version", "hybrid"),
            })

    # Sort by ENGINE_ORDER
    order = {e: i for i, e in enumerate(ENGINE_ORDER)}
    rows.sort(key=lambda r: order.get(r["engine"], 99))
    return rows


def fmt(val: float | None, decimals: int = 4) -> str:
    if val is None:
        return "—"
    return f"{val:.{decimals}f}"


def print_markdown(rows: list[dict]) -> None:
    header = (
        "| Engine | Type | n | ROUGE-1 | ROUGE-2 | ROUGE-L | "
        "Latency (ms) | Compression% | Repetition% |"
    )
    sep = "|--------|------|---|---------|---------|---------|-------------|--------------|-------------|"
    print(header)
    print(sep)
    for r in rows:
        label = ENGINE_LABELS.get(r["engine"], r["engine"])
        lat = f"{r['latency_ms']:.1f}" if r.get("latency_ms") is not None else "—"
        comp = f"{r['compression_pct']:.1f}" if r.get("compression_pct") is not None else "—"
        rep = f"{r['repetition_pct']:.1f}" if r.get("repetition_pct") is not None else "—"
        print(
            f"| {label} | {r['type']} | {r['n']} | "
            f"{fmt(r.get('rouge1_f'))} | {fmt(r.get('rouge2_f'))} | {fmt(r.get('rougeL_f'))} | "
            f"{lat} | {comp} | {rep} |"
        )


def print_csv(rows: list[dict]) -> None:
    import csv
    import io
    buf = io.StringIO()
    fieldnames = [
        "engine", "type", "n", "rouge1_f", "rouge2_f", "rougeL_f",
        "latency_ms", "compression_pct", "repetition_pct",
    ]
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for r in rows:
        writer.writerow(r)
    print(buf.getvalue())


def main() -> None:
    parser = argparse.ArgumentParser(description="Print unified 5-engine comparison table.")
    parser.add_argument(
        "--format",
        choices=["markdown", "csv"],
        default="markdown",
        help="Output format (default: markdown).",
    )
    args = parser.parse_args()

    rows = build_table()
    if not rows:
        print(f"No benchmark results found in {OFFICIAL_DIR}", file=sys.stderr)
        print("Run the following scripts first:", file=sys.stderr)
        print("  python scripts/benchmark_extractive_engines.py", file=sys.stderr)
        print("  python scripts/benchmark_hybrid_engine.py --n 200 --warmup-vit5", file=sys.stderr)
        sys.exit(1)

    missing = [e for e in ENGINE_ORDER if not any(r["engine"] == e for r in rows)]
    if missing:
        print(f"Note: Missing engines: {', '.join(missing)}")
        print(f"      Run the corresponding benchmark scripts to populate all rows.\n")

    if args.format == "csv":
        print_csv(rows)
    else:
        print_markdown(rows)


if __name__ == "__main__":
    main()
