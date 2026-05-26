from __future__ import annotations

"""
Aligned real-file matrix: export VietNews article to .txt/.docx/.pdf, then for each
(engine, format) run evaluate_real_file_for_guid (ROUGE vs gold valid only because
files match dataset article).

Example:

  python scripts/demos/eval_aligned_real_file_matrix.py --guid 6131 \\
    --samples-dir data/samples/multiformat --out-dir notebooks/results/analysis
"""

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.shared.multiformat_experiment import (
    evaluate_real_file_for_guid,
    export_vietnews_article_files,
)

DEFAULT_ENGINES = ("tfidf", "textrank", "phobert-extractive")
FORMATS = ("txt", "docx", "pdf")


def _parse_csv(s: str) -> tuple[str, ...]:
    return tuple(p.strip().lower() for p in s.split(",") if p.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description="Aligned guid × format × engine matrix (real paths).")
    parser.add_argument("--guid", type=str, required=True)
    parser.add_argument("--samples-dir", type=Path, default=ROOT / "data" / "samples" / "multiformat")
    parser.add_argument("--engines", type=str, default=",".join(DEFAULT_ENGINES))
    parser.add_argument("--formats", type=str, default=",".join(FORMATS))
    parser.add_argument("--max-sentences", type=int, default=2, dest="max_sentences")
    parser.add_argument("--split", type=str, default="validation")
    parser.add_argument("--protocol", type=str, default="phase0_v2")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "notebooks" / "results" / "analysis",
    )
    parser.add_argument("--no-export", action="store_true", help="Skip export; expect files already present.")
    args = parser.parse_args()

    engines = _parse_csv(args.engines)
    fmts = _parse_csv(args.formats)
    for f in fmts:
        if f not in FORMATS:
            raise SystemExit(f"Unknown format {f!r}; choose from {FORMATS}")

    samples_dir = Path(args.samples_dir)
    samples_dir.mkdir(parents=True, exist_ok=True)

    if not args.no_export:
        export_vietnews_article_files(args.guid, samples_dir)

    rows: list[dict[str, object]] = []
    errors: list[dict[str, str]] = []

    for fmt in fmts:
        path = samples_dir / f"{args.guid}.{fmt}"
        if not path.is_file():
            errors.append({"format": fmt, "error": f"missing file {path}"})
            continue
        for engine in engines:
            try:
                r = evaluate_real_file_for_guid(
                    args.guid,
                    path,
                    engine=engine,
                    max_sentences=args.max_sentences,
                    target_split=args.split,
                    protocol_version=args.protocol,
                )
                rows.append(
                    {
                        "guid": args.guid,
                        "file_format": fmt,
                        "file_path": str(path.resolve()),
                        "summary_engine": engine,
                        "ingest_rougeL_f": r.get("ingest_rougeL_f"),
                        "ingest_exact_match": r.get("ingest_exact_match"),
                        "baseline_rougeL_f": r.get("baseline_rougeL_f"),
                        "real_rougeL_f": r.get("real_rougeL_f"),
                        "rougeL_delta_real_vs_baseline_summary": r.get(
                            "rougeL_delta_real_vs_baseline_summary"
                        ),
                        "baseline_predicted_summary": r.get("baseline_predicted_summary"),
                        "real_predicted_summary": r.get("real_predicted_summary"),
                    }
                )
            except Exception as exc:
                errors.append({"format": fmt, "engine": engine, "error": f"{type(exc).__name__}: {exc}"})

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"aligned_real_file_matrix_{args.guid}"
    csv_path = out_dir / f"{stem}.csv"
    json_path = out_dir / f"{stem}.json"

    fieldnames = list(rows[0].keys()) if rows else [
        "guid",
        "file_format",
        "file_path",
        "summary_engine",
        "ingest_rougeL_f",
        "ingest_exact_match",
        "baseline_rougeL_f",
        "real_rougeL_f",
        "rougeL_delta_real_vs_baseline_summary",
        "baseline_predicted_summary",
        "real_predicted_summary",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    json_path.write_text(
        json.dumps({"rows": rows, "errors": errors}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(csv_path)
    print(json_path)
    if errors:
        print(json.dumps(errors, ensure_ascii=False, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
