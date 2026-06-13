from __future__ import annotations

"""
Official test-set benchmark: TF-IDF, TextRank, PhoBERT, ViT5, Hybrid on VietNews test split.

Run ONCE after all hyperparameter decisions are finalized on validation set.
Results go to notebooks/results/official/test/ — these are the final thesis numbers.

Example:
  python scripts/benchmark_test_set.py --n 200 --warmup-vit5
  python scripts/benchmark_test_set.py --n 200 --warmup-vit5 --smoke-test  # 5 mẫu để kiểm tra
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
for p in [ROOT, ROOT / "backend", ROOT / "evaluation"]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from app.services.input import process_from_text
from app.services.summarization.summary_service import summarize_processed_input_raw
from evaluation.evaluator import Evaluator
from scripts.shared.common import build_environment_snapshot
from scripts.shared.io_dataset import load_benchmark_validation_subset

SCRIPT_PATH = "scripts/benchmark_test_set.py"
PROTOCOL_VERSION_EXPECTED = "phase0_v2"
TARGET_SPLIT = "test"
SEED = 42
ENGINES = ["tfidf", "textrank", "phobert-extractive", "vit5", "hybrid"]
ARTICLE_CHAR_THRESHOLD = 1200


def _load_jsonl_safe(path: Path) -> tuple[list[dict], int]:
    """Read JSONL, skip corrupted lines, return (rows, skipped_count)."""
    import json as _json
    rows, skipped = [], 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(_json.loads(line))
        except _json.JSONDecodeError:
            skipped += 1
    return rows, skipped


def load_test_df(subset_limit: int) -> tuple[pd.DataFrame, str, Path, Path]:
    processed_dir = ROOT / "data" / "processed" / "vietnews"
    manifest_path = processed_dir / "dataset_manifest.json"
    split_path = processed_dir / f"{TARGET_SPLIT}.jsonl"

    import json as _json
    manifest = _json.loads(manifest_path.read_text(encoding="utf-8"))
    protocol_version = manifest.get("protocol_version")
    if protocol_version != PROTOCOL_VERSION_EXPECTED:
        raise RuntimeError(f"Protocol mismatch: {protocol_version!r} != {PROTOCOL_VERSION_EXPECTED!r}")

    rows, skipped = _load_jsonl_safe(split_path)
    if skipped:
        print(f"  Warning: skipped {skipped} corrupted line(s) in {split_path.name}", flush=True)

    df = pd.DataFrame(rows)
    return load_benchmark_validation_subset(
        df,
        manifest=manifest,
        processed_dir=processed_dir,
        target_split=TARGET_SPLIT,
        seed=SEED,
        subset_limit=subset_limit,
        article_char_threshold=ARTICLE_CHAR_THRESHOLD,
    )


def run_benchmark(
    *,
    n: int,
    max_sentences: int,
    seed: int,
    warmup_vit5: bool,
) -> tuple[pd.DataFrame, dict]:
    import random
    random.seed(seed)
    evaluator = Evaluator(use_stemmer=False)
    subset_df, protocol_version, manifest_path, split_path = load_test_df(n)
    actual_n = len(subset_df)
    print(f"Loaded {actual_n} samples from {TARGET_SPLIT} set.", flush=True)

    vit5_warmup_done = False
    records: list[dict] = []

    for engine in ENGINES:
        print(f"\n[{engine}] Running {actual_n} samples ...", flush=True)
        for idx, row in enumerate(subset_df.to_dict(orient="records")):
            article = str(row.get("article", ""))
            reference = str(row.get("reference_summary", ""))
            if not article.strip() or not reference.strip():
                continue

            processed = process_from_text(article)

            if engine in ("vit5", "hybrid") and warmup_vit5 and not vit5_warmup_done:
                print("  Warming up ViT5 ...", flush=True)
                summarize_processed_input_raw(
                    processed, max_sentences=max_sentences, ratio=None, engine_name="vit5"
                )
                vit5_warmup_done = True

            t0 = time.perf_counter()
            selected_sentences, engine_meta = summarize_processed_input_raw(
                processed, max_sentences=max_sentences, ratio=None, engine_name=engine
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
            rec["strategy"] = engine_meta.get("strategy", "")
            records.append(rec)

            if (idx + 1) % 20 == 0:
                print(f"  {idx + 1}/{actual_n} done", flush=True)

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
        "report_schema_version": "test_set_benchmark_v1",
        "script": SCRIPT_PATH,
        "protocol_version": protocol_version,
        "target_split": TARGET_SPLIT,
        "seed": seed,
        "subset_limit": n,
        "actual_n": actual_n,
        "article_char_threshold": ARTICLE_CHAR_THRESHOLD,
        "max_sentences": max_sentences,
        "engines": ENGINES,
        "manifest_path": str(manifest_path),
        "split_path": str(split_path),
        "summary_by_engine": summary_df.to_dict(orient="records"),
        "environment": build_environment_snapshot(ROOT, package_names=["rouge-score", "transformers"]),
    }
    return detail_df, report


def main() -> None:
    parser = argparse.ArgumentParser(description="Official test-set benchmark for all engines.")
    parser.add_argument("--n", type=int, default=200)
    parser.add_argument("--max-sentences", type=int, default=2, dest="max_sentences")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--warmup-vit5", action="store_true")
    parser.add_argument("--smoke-test", action="store_true", help="Run 5 samples only (quick check).")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "notebooks" / "results" / "official" / "test",
    )
    args = parser.parse_args()

    n = 5 if args.smoke_test else args.n
    if args.smoke_test:
        print("SMOKE TEST MODE — 5 samples only.", flush=True)

    detail_df, report = run_benchmark(
        n=n,
        max_sentences=args.max_sentences,
        seed=args.seed,
        warmup_vit5=args.warmup_vit5,
    )

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    detail_path = out_dir / f"test_set_detail_{ts}.csv"
    report_path = out_dir / f"test_set_report_{ts}.json"
    detail_df.to_csv(detail_path, index=False, encoding="utf-8")
    report["detail_csv"] = str(detail_path)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== DONE ===")
    print(f"Detail CSV : {detail_path}")
    print(f"Report JSON: {report_path}")
    print("\nSummary:")
    print(json.dumps(report["summary_by_engine"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
