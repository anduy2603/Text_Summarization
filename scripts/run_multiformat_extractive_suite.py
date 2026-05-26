from __future__ import annotations

"""
Run VietNews multiformat eval for multiple extractive engines with identical protocol.

Writes one manifest JSON plus per-engine detail CSV + report JSON under the same
suite timestamp (thesis-friendly: fair comparison across engines).

Example (official-sized run; long on CPU with phobert-extractive):

  python scripts/run_multiformat_extractive_suite.py --n 200 --max-sentences 2 \\
    --seed 42 --article-char-threshold 1200 --warmup-engine

Quick smoke:

  python scripts/run_multiformat_extractive_suite.py --n 3 --engines textrank,tfidf
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

SCRIPT_SINGLE = "scripts/eval_multiformat_vietnews_file_formats.py"
SCRIPT_SUITE = "scripts/run_multiformat_extractive_suite.py"
PROTOCOL_DEFAULT = "phase0_v2"
SPLIT_DEFAULT = "validation"
DEFAULT_ENGINES = ("tfidf", "textrank", "phobert-extractive")


def _parse_engines(s: str) -> tuple[str, ...]:
    parts = [p.strip().lower() for p in s.split(",") if p.strip()]
    if not parts:
        raise SystemExit("No engines after --engines")
    return tuple(parts)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run multiformat VietNews eval for several extractive engines with one suite id.",
    )
    parser.add_argument("--n", type=int, default=20)
    parser.add_argument(
        "--engines",
        type=str,
        default=",".join(DEFAULT_ENGINES),
        help=f"Comma-separated engines (default: {','.join(DEFAULT_ENGINES)})",
    )
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
    parser.add_argument(
        "--suite-id",
        type=str,
        default=None,
        help="Optional fixed id (default: timestamp multiformat_suite_YYYYMMDD_HHMMSS)",
    )
    args = parser.parse_args()

    engines = _parse_engines(args.engines)
    threshold: int | None = args.article_char_threshold
    if threshold is not None and threshold <= 0:
        threshold = None

    suite_ts = args.suite_id or datetime.now().strftime("%Y%m%d_%H%M%S")
    suite_prefix = f"multiformat_suite_{suite_ts}"
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    runs: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []

    for engine in engines:
        try:
            detail_df, report = run_multiformat_eval(
                n=args.n,
                engine=engine,
                max_sentences=args.max_sentences,
                seed=args.seed,
                protocol_version=args.protocol,
                target_split=args.split,
                article_char_threshold=threshold,
                warmup_engine=args.warmup_engine,
                script_path=SCRIPT_SUITE,
            )
            safe = engine.replace("/", "_")
            csv_path = out_dir / f"{suite_prefix}__{safe}__detail.csv"
            json_path = out_dir / f"{suite_prefix}__{safe}__report.json"
            detail_df.to_csv(csv_path, index=False, encoding="utf-8")
            report["detail_csv"] = str(csv_path)
            json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            runs.append(
                {
                    "engine": engine,
                    "detail_csv": str(csv_path),
                    "report_json": str(json_path),
                }
            )
            print(f"OK {engine}: {csv_path}")
        except Exception as exc:  # pragma: no cover - surface all engines
            errors.append({"engine": engine, "error": f"{type(exc).__name__}: {exc}"})
            print(f"FAIL {engine}: {exc}", file=sys.stderr)

    manifest = {
        "suite_schema": "multiformat_extractive_suite_v1",
        "suite_id": suite_ts,
        "script": SCRIPT_SUITE,
        "protocol_version": args.protocol,
        "target_split": args.split,
        "n": args.n,
        "seed": args.seed,
        "max_sentences": args.max_sentences,
        "article_char_threshold": threshold,
        "warmup_engine": args.warmup_engine,
        "engines_requested": list(engines),
        "runs": runs,
        "errors": errors,
    }
    manifest_path = out_dir / f"{suite_prefix}__manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Manifest:", manifest_path)
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
