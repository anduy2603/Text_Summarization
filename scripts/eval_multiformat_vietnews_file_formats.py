from __future__ import annotations

"""
End-to-end multi-format evaluation on VietNews.

For each article + reference_summary in a validation subset:
  1) Baseline: process_from_text(article) -> summarize -> ROUGE vs gold
  2) TXT / DOCX / PDF: synthetic files -> process_from_bytes -> summarize -> ROUGE vs gold

Also measures ingestion fidelity (cleaned_text vs text baseline) per format.

For **several extractive engines** with one suite manifest, use
`scripts/run_multiformat_extractive_suite.py` (same `n` / `seed` / protocol for each engine).

Requires: prepared VietNews under data/processed/vietnews/, conda env with python-docx, pymupdf.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.shared.multiformat_experiment import run_multiformat_eval

SCRIPT_PATH = "scripts/eval_multiformat_vietnews_file_formats.py"
PROTOCOL_DEFAULT = "phase0_v2"
SPLIT_DEFAULT = "validation"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="VietNews multi-format file ingest + summarize + ROUGE vs gold.",
    )
    parser.add_argument("--n", type=int, default=20, help="Subset size (same sampling as Phase 1 benchmark).")
    parser.add_argument("--engine", type=str, default="textrank")
    parser.add_argument("--max-sentences", type=int, default=2, dest="max_sentences")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--protocol", type=str, default=PROTOCOL_DEFAULT)
    parser.add_argument("--split", type=str, default=SPLIT_DEFAULT)
    parser.add_argument("--article-char-threshold", type=int, default=1200)
    parser.add_argument("--warmup-engine", action="store_true")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "notebooks" / "results" / "analysis",
    )
    args = parser.parse_args()

    threshold: int | None = args.article_char_threshold
    if threshold is not None and threshold <= 0:
        threshold = None

    detail_df, report = run_multiformat_eval(
        n=args.n,
        engine=args.engine.strip().lower(),
        max_sentences=args.max_sentences,
        seed=args.seed,
        protocol_version=args.protocol,
        target_split=args.split,
        article_char_threshold=threshold,
        warmup_engine=args.warmup_engine,
        script_path=SCRIPT_PATH,
    )

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"multiformat_vietnews_files_detail_{ts}.csv"
    json_path = out_dir / f"multiformat_vietnews_files_report_{ts}.json"

    detail_df.to_csv(csv_path, index=False, encoding="utf-8")
    report["detail_csv"] = str(csv_path)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Saved:")
    print(csv_path)
    print(json_path)
    print(json.dumps(report.get("by_format", {}), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
