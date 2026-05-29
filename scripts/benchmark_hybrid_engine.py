from __future__ import annotations

"""
Hybrid engine benchmark: TextRank, ViT5, and Hybrid on the same VietNews validation subset.

Extends benchmark_abstractive_vit5.py to include the Hybrid engine (TextRank preselect → ViT5
rewrite) so all three engines can be compared in one run. Output goes to
notebooks/results/official/validation/ to mark it as a locked benchmark result.

Example:
  # Smoke test (5 samples):
  python scripts/benchmark_hybrid_engine.py --n 5 --warmup-vit5
  # Full official run (200 samples, matches other official benchmarks):
  python scripts/benchmark_hybrid_engine.py --n 200 --max-sentences 2 --warmup-vit5
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(ROOT / "backend"))
if str(ROOT / "evaluation") not in sys.path:
    sys.path.insert(0, str(ROOT / "evaluation"))

from app.services.input import process_from_text
from app.services.summarization.summary_service import summarize_processed_input_raw
from evaluation.evaluator import Evaluator
from scripts.benchmark_extractive_engines import load_validation_df
from scripts.shared.common import build_environment_snapshot

SCRIPT_PATH = "scripts/benchmark_hybrid_engine.py"
ENGINES = ("textrank", "vit5", "hybrid")


def run_benchmark(
    *,
    n: int,
    max_sentences: int,
    seed: int,
    article_char_threshold: int | None,
    warmup_vit5: bool,
) -> tuple[pd.DataFrame, dict]:
    import random
    random.seed(seed)
    evaluator = Evaluator(use_stemmer=False)
    subset_df, protocol_version, manifest_path, split_path = load_validation_df()
    subset_df = subset_df.head(n).copy() if n < len(subset_df) else subset_df

    vit5_warmup_done = False
    records: list[dict] = []

    for engine in ENGINES:
        print(f"  Running engine: {engine} ({len(subset_df)} samples) ...", flush=True)
        for row in subset_df.to_dict(orient="records"):
            article = str(row.get("article", ""))
            reference = str(row.get("reference_summary", ""))
            if not article.strip() or not reference.strip():
                continue

            processed = process_from_text(article)

            # Warm up ViT5 (and by extension Hybrid) before timed runs
            if engine in ("vit5", "hybrid") and warmup_vit5 and not vit5_warmup_done:
                summarize_processed_input_raw(
                    processed,
                    max_sentences=max_sentences,
                    ratio=None,
                    engine_name="vit5",
                )
                vit5_warmup_done = True

            t0 = time.perf_counter()
            selected_sentences, engine_meta = summarize_processed_input_raw(
                processed,
                max_sentences=max_sentences,
                ratio=None,
                engine_name=engine,
            )
            latency_sec = time.perf_counter() - t0
            predicted_summary = " ".join(s.strip() for s in selected_sentences if s.strip())

            bundle = evaluator.evaluate_one(
                source_text=processed.cleaned_text,
                reference_summary=reference,
                predicted_summary=predicted_summary,
                latency_sec=latency_sec,
                extra={
                    "guid": row.get("guid"),
                    "engine": engine,
                    "method": engine_meta.get("method", ""),
                    "strategy": engine_meta.get("strategy", ""),
                    "max_sentences": max_sentences,
                    "article_char_len": row.get("article_char_len"),
                    "predicted_summary": predicted_summary,
                },
            )
            rec = bundle.as_dict()
            rec["summarizer_core_latency_sec"] = rec.pop("latency_sec")
            rec["input_truncation"] = engine_meta.get("input_truncation")
            rec["resolved_max_new_tokens"] = engine_meta.get("resolved_max_new_tokens")
            rec["strategy"] = engine_meta.get("strategy", "")
            records.append(rec)

    detail_df = pd.DataFrame(records)
    if detail_df.empty:
        raise RuntimeError("No benchmark records generated.")

    summary_df = (
        detail_df.groupby("engine", as_index=False)
        .agg(
            n=("engine", "count"),
            rouge1_f=("rouge1_f", "mean"),
            rouge2_f=("rouge2_f", "mean"),
            rougeL_f=("rougeL_f", "mean"),
            summarizer_core_latency_sec=("summarizer_core_latency_sec", "mean"),
            compression_ratio=("compression_ratio", "mean"),
            repetition_rate=("repetition_rate", "mean"),
        )
        .sort_values("engine")
        .reset_index(drop=True)
    )

    report = {
        "report_schema_version": "hybrid_engine_benchmark_v1",
        "script": SCRIPT_PATH,
        "protocol_version": protocol_version,
        "target_split": "validation",
        "seed": seed,
        "subset_limit": n,
        "article_char_threshold": article_char_threshold,
        "max_sentences": max_sentences,
        "engines": list(ENGINES),
        "manifest_path": str(manifest_path),
        "split_path": str(split_path),
        "summary_by_engine": summary_df.to_dict(orient="records"),
        "environment": build_environment_snapshot(
            ROOT, package_names=["rouge-score", "transformers"]
        ),
    }
    return detail_df, report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark Hybrid engine vs ViT5 and TextRank on VietNews validation subset."
    )
    parser.add_argument("--n", type=int, default=20, help="Subset size.")
    parser.add_argument("--max-sentences", type=int, default=2, dest="max_sentences")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--article-char-threshold", type=int, default=1200)
    parser.add_argument(
        "--warmup-vit5",
        action="store_true",
        help="Warm up ViT5 before timed runs to exclude model load latency.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "notebooks" / "results" / "official" / "validation",
        help="Output directory for results (default: official/validation).",
    )
    args = parser.parse_args()

    threshold: int | None = args.article_char_threshold
    if threshold is not None and threshold <= 0:
        threshold = None

    print(f"Running hybrid benchmark: n={args.n}, max_sentences={args.max_sentences}, seed={args.seed}")
    detail_df, report = run_benchmark(
        n=args.n,
        max_sentences=args.max_sentences,
        seed=args.seed,
        article_char_threshold=threshold,
        warmup_vit5=args.warmup_vit5,
    )

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    detail_path = out_dir / f"hybrid_engine_detail_{ts}.csv"
    report_path = out_dir / f"hybrid_engine_report_{ts}.json"

    detail_df.to_csv(detail_path, index=False, encoding="utf-8")
    report["detail_csv"] = str(detail_path)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\nSaved:")
    print(f"  {detail_path}")
    print(f"  {report_path}")
    print("\nSummary:")
    print(json.dumps(report["summary_by_engine"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
