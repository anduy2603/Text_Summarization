from __future__ import annotations

"""
Minimal abstractive benchmark: ViT5 vs TextRank extractive baseline on the same VietNews subset.

Uses one length setting (max_sentences=2 for extractive; token budget mapped for ViT5).
Writes comparison CSV/JSON under notebooks/results/analysis/ (or --out-dir).

Example:
  python scripts/benchmark_abstractive_vit5.py --n 20 --max-sentences 2 --warmup-vit5
  python scripts/benchmark_abstractive_vit5.py --n 200 --max-sentences 2 --warmup-vit5
"""

import argparse
import json
import random
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

SCRIPT_PATH = "scripts/benchmark_abstractive_vit5.py"
EXTRACTIVE_BASELINE = "textrank"
ABSTRACTIVE_ENGINE = "vit5"
ENGINES = (EXTRACTIVE_BASELINE, ABSTRACTIVE_ENGINE)


def run_benchmark(
    *,
    n: int,
    max_sentences: int,
    seed: int,
    article_char_threshold: int | None,
    warmup_vit5: bool,
) -> tuple[pd.DataFrame, dict]:
    random.seed(seed)
    evaluator = Evaluator(use_stemmer=False)
    subset_df, protocol_version, manifest_path, split_path = load_validation_df()
    subset_df = subset_df.head(n).copy() if n < len(subset_df) else subset_df

    vit5_warmup_done = False
    records: list[dict] = []

    for engine in ENGINES:
        for row in subset_df.to_dict(orient="records"):
            article = str(row.get("article", ""))
            reference = str(row.get("reference_summary", ""))
            if not article.strip() or not reference.strip():
                continue

            processed = process_from_text(article)
            if engine == ABSTRACTIVE_ENGINE and warmup_vit5 and not vit5_warmup_done:
                summarize_processed_input_raw(
                    processed,
                    max_sentences=max_sentences,
                    ratio=None,
                    engine_name=engine,
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
                    "method": engine_meta.get("method", "extractive"),
                    "max_sentences": max_sentences,
                    "article_char_len": row.get("article_char_len"),
                    "predicted_summary": predicted_summary,
                },
            )
            rec = bundle.as_dict()
            rec["summarizer_core_latency_sec"] = rec.pop("latency_sec")
            rec["input_truncation"] = engine_meta.get("input_truncation")
            rec["resolved_max_new_tokens"] = engine_meta.get("resolved_max_new_tokens")
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
        "report_schema_version": "abstractive_vs_extractive_v1",
        "script": SCRIPT_PATH,
        "protocol_version": protocol_version,
        "target_split": "validation",
        "seed": seed,
        "subset_limit": n,
        "article_char_threshold": article_char_threshold,
        "max_sentences": max_sentences,
        "extractive_baseline_engine": EXTRACTIVE_BASELINE,
        "abstractive_engine": ABSTRACTIVE_ENGINE,
        "manifest_path": str(manifest_path),
        "split_path": str(split_path),
        "summary_by_engine": summary_df.to_dict(orient="records"),
        "environment": build_environment_snapshot(ROOT, package_names=["rouge-score", "transformers"]),
    }
    return detail_df, report


def main() -> None:
    parser = argparse.ArgumentParser(description="ViT5 abstractive vs TextRank on VietNews subset.")
    parser.add_argument("--n", type=int, default=20, help="Subset size (same sampling as Phase 1).")
    parser.add_argument("--max-sentences", type=int, default=2, dest="max_sentences")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--article-char-threshold", type=int, default=1200)
    parser.add_argument("--warmup-vit5", action="store_true", help="Warm up ViT5 load before timed runs.")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "notebooks" / "results" / "analysis",
    )
    args = parser.parse_args()

    threshold: int | None = args.article_char_threshold
    if threshold is not None and threshold <= 0:
        threshold = None

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
    detail_path = out_dir / f"vit5_vs_textrank_detail_{ts}.csv"
    report_path = out_dir / f"vit5_vs_textrank_report_{ts}.json"
    detail_df.to_csv(detail_path, index=False, encoding="utf-8")
    report["detail_csv"] = str(detail_path)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Saved:")
    print(detail_path)
    print(report_path)
    print(json.dumps(report["summary_by_engine"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
