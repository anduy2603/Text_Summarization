from __future__ import annotations

"""
BERTScore benchmark: compute Precision / Recall / F1 for all 5 summarization engines.

Reads predicted summaries from existing official detail CSVs (no re-running inference),
joins reference summaries by guid from validation.jsonl, then scores with
bert-base-multilingual-cased (mBERT) — standard for Vietnamese NLP papers.

Prediction sources:
  tfidf, textrank, phobert-extractive  ←  engine_compare_detail_*.csv   (top_k = 2)
  vit5, hybrid                         ←  hybrid_engine_detail_*.csv     (max_sentences = 2)

Both CSVs must already exist in notebooks/results/official/validation/.
Run benchmark_extractive_engines.py and benchmark_hybrid_engine.py first if missing.

Output:
  notebooks/results/official/validation/bertscore_report_{ts}.json
  notebooks/results/official/validation/bertscore_detail_{ts}.csv

Example:
  # Smoke test — 10 samples per engine (fast):
  python scripts/benchmark_bertscore.py --n 10
  # Full official run — all 200 samples:
  python scripts/benchmark_bertscore.py
  # Custom model (e.g. xlm-roberta-base):
  python scripts/benchmark_bertscore.py --model xlm-roberta-base
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from statistics import mean

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "evaluation"), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from evaluation.bertscore_evaluator import BERTSCORE_DEFAULT_MODEL, BertScorer
from scripts.shared.common import build_environment_snapshot
from scripts.shared.io_dataset import load_split

OFFICIAL_DIR = ROOT / "notebooks" / "results" / "official" / "validation"
PROCESSED_DIR = ROOT / "data" / "processed" / "vietnews"
PROTOCOL_VERSION = "phase0_v2"
TARGET_SPLIT = "validation"

ENGINES_EXTRACTIVE = ("tfidf", "textrank", "phobert-extractive")
ENGINES_ABSTRACTIVE = ("vit5", "hybrid")
ALL_ENGINES = ENGINES_EXTRACTIVE + ENGINES_ABSTRACTIVE

# Best top_k from engine_compare benchmark (locked per phase0_v2 protocol)
EXTRACTIVE_TOP_K = 2
ABSTRACTIVE_MAX_SENTENCES = 2


def _most_recent_csv(glob_pattern: str) -> Path:
    """Return the path of the most recent CSV matching glob_pattern (sorted by name)."""
    candidates = sorted(OFFICIAL_DIR.glob(glob_pattern))
    if not candidates:
        raise FileNotFoundError(
            f"No file matching '{glob_pattern}' in {OFFICIAL_DIR}.\n"
            "Run the relevant benchmark script first:\n"
            "  Extractive: python scripts/benchmark_extractive_engines.py\n"
            "  Hybrid/ViT5: python scripts/benchmark_hybrid_engine.py --n 200 --warmup-vit5"
        )
    return candidates[-1]


def load_reference_map() -> dict[str, str]:
    """Return {guid: reference_summary} from validation.jsonl."""
    df, _ = load_split(PROCESSED_DIR, TARGET_SPLIT, PROTOCOL_VERSION)
    return {
        str(row["guid"]): str(row["reference_summary"])
        for row in df.to_dict(orient="records")
        if str(row.get("reference_summary", "")).strip()
    }


def load_predictions(n: int | None) -> pd.DataFrame:
    """
    Load predicted summaries for all 5 engines from the most recent detail CSVs.
    Returns DataFrame with columns: engine, guid, predicted_summary.
    """
    frames: list[pd.DataFrame] = []

    extractive_csv = _most_recent_csv("engine_compare_detail_*.csv")
    print(f"Extractive source : {extractive_csv.name}")
    ext_df = pd.read_csv(extractive_csv, dtype={"guid": str})
    ext_df = ext_df[ext_df["engine"].isin(ENGINES_EXTRACTIVE)].copy()
    if "top_k" in ext_df.columns:
        ext_df = ext_df[ext_df["top_k"] == EXTRACTIVE_TOP_K].copy()
    frames.append(ext_df[["engine", "guid", "predicted_summary"]].copy())

    hybrid_csv = _most_recent_csv("hybrid_engine_detail_*.csv")
    print(f"Hybrid/ViT5 source: {hybrid_csv.name}")
    hyb_df = pd.read_csv(hybrid_csv, dtype={"guid": str})
    hyb_df = hyb_df[hyb_df["engine"].isin(ENGINES_ABSTRACTIVE)].copy()
    frames.append(hyb_df[["engine", "guid", "predicted_summary"]].copy())

    combined = (
        pd.concat(frames, ignore_index=True)
        .dropna(subset=["predicted_summary"])
        .copy()
    )
    combined["predicted_summary"] = combined["predicted_summary"].astype(str)

    if n is not None and n > 0:
        combined = (
            combined.groupby("engine", group_keys=False)
            .apply(lambda g: g.head(n))
            .reset_index(drop=True)
        )

    return combined


def compute_bertscore(
    preds_df: pd.DataFrame,
    ref_map: dict[str, str],
    scorer: BertScorer,
) -> pd.DataFrame:
    """
    Score each engine's predictions against reference summaries.
    Returns a detail DataFrame with bertscore_p / bertscore_r / bertscore_f1 columns.
    """
    result_frames: list[pd.DataFrame] = []

    for engine in ALL_ENGINES:
        group = preds_df[preds_df["engine"] == engine].copy().reset_index(drop=True)
        if group.empty:
            print(f"  [skip] {engine}: no predictions found in detail CSVs")
            continue

        group["reference_summary"] = group["guid"].map(ref_map)
        n_missing = int(group["reference_summary"].isna().sum())
        if n_missing:
            print(f"  [warn] {engine}: {n_missing} guids without reference — skipping those rows")
            group = group.dropna(subset=["reference_summary"]).reset_index(drop=True)
        if group.empty:
            continue

        print(f"\n  [{engine}] scoring {len(group)} samples ...", flush=True)
        scores = scorer.score_pairs(
            predictions=group["predicted_summary"].tolist(),
            references=group["reference_summary"].tolist(),
        )
        group = pd.concat(
            [group.reset_index(drop=True), pd.DataFrame(scores)],
            axis=1,
        )
        result_frames.append(group)

    if not result_frames:
        raise RuntimeError("No BERTScore results were generated.")

    return pd.concat(result_frames, ignore_index=True)


def build_report(detail_df: pd.DataFrame, n_arg: int | None, model_type: str) -> dict:
    summary_rows = []
    for engine in ALL_ENGINES:
        g = detail_df[detail_df["engine"] == engine]
        if g.empty:
            continue
        summary_rows.append(
            {
                "engine": engine,
                "n": len(g),
                "bertscore_p": round(mean(g["bertscore_p"].tolist()), 6),
                "bertscore_r": round(mean(g["bertscore_r"].tolist()), 6),
                "bertscore_f1": round(mean(g["bertscore_f1"].tolist()), 6),
            }
        )

    return {
        "report_schema_version": "bertscore_benchmark_v1",
        "script": "scripts/benchmark_bertscore.py",
        "protocol_version": PROTOCOL_VERSION,
        "target_split": TARGET_SPLIT,
        "bertscore_model": model_type,
        "subset_limit": n_arg,
        "extractive_top_k": EXTRACTIVE_TOP_K,
        "abstractive_max_sentences": ABSTRACTIVE_MAX_SENTENCES,
        "engines": list(ALL_ENGINES),
        "summary_by_engine": summary_rows,
        "environment": build_environment_snapshot(
            ROOT, ["bert-score", "torch", "transformers"]
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute BERTScore for all 5 engines using existing detail CSVs."
    )
    parser.add_argument(
        "--n",
        type=int,
        default=None,
        help="Max samples per engine. Default: all available (~200).",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=BERTSCORE_DEFAULT_MODEL,
        dest="model_type",
        help=f"HuggingFace model for BERTScore. Default: {BERTSCORE_DEFAULT_MODEL}",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        dest="batch_size",
        help="Batch size for BERTScore inference. Default: 32.",
    )
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        help="Device override: 'cpu', 'cuda', 'cuda:0', etc. Default: auto-detect.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=OFFICIAL_DIR,
        dest="out_dir",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("BERTScore Benchmark — 5 Engines")
    print(f"  model      : {args.model_type}")
    print(f"  samples    : {args.n or 'all'} per engine")
    print(f"  batch_size : {args.batch_size}")
    print(f"  device     : {args.device or 'auto'}")
    print("=" * 60)

    ref_map = load_reference_map()
    print(f"\nLoaded {len(ref_map)} references from {TARGET_SPLIT}.jsonl")

    preds_df = load_predictions(args.n)
    print("\nPredictions loaded:")
    for engine, grp in preds_df.groupby("engine"):
        print(f"  {engine:25s} {len(grp):>4} samples")

    scorer = BertScorer(
        model_type=args.model_type,
        batch_size=args.batch_size,
        device=args.device or None,
        verbose=True,
    )

    print(f"\nScoring with {args.model_type} ...")
    detail_df = compute_bertscore(preds_df, ref_map, scorer)

    report = build_report(detail_df, args.n, args.model_type)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    detail_path = out_dir / f"bertscore_detail_{ts}.csv"
    report_path = out_dir / f"bertscore_report_{ts}.json"

    detail_df.to_csv(detail_path, index=False, encoding="utf-8")
    report["detail_csv"] = str(detail_path)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("\n" + "=" * 60)
    print("Saved:")
    print(f"  {report_path}")
    print(f"  {detail_path}")
    print("\nBERTScore Results (F1 ↑ is better):")
    print(f"  {'Engine':<25}  {'P':>7}  {'R':>7}  {'F1':>7}")
    print(f"  {'-'*25}  {'-'*7}  {'-'*7}  {'-'*7}")
    for row in report["summary_by_engine"]:
        print(
            f"  {row['engine']:<25}  {row['bertscore_p']:>7.4f}  "
            f"{row['bertscore_r']:>7.4f}  {row['bertscore_f1']:>7.4f}"
        )
    print("=" * 60)


if __name__ == "__main__":
    main()
