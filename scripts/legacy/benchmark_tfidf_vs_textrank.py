"""
Backward-compatible entry point for the Phase 1 multi-engine extractive benchmark.

Prefer running ``scripts/benchmark_extractive_engines.py`` (TF-IDF, TextRank,
PhoBERT-extractive). This module re-exports the same API so older imports and
commands keep working.

Direct CLI path after script reorganization:
``python scripts/legacy/benchmark_tfidf_vs_textrank.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.benchmark_extractive_engines import (
    ARTICLE_CHAR_THRESHOLD,
    ENGINES,
    PROTOCOL_VERSION_EXPECTED,
    SCRIPT_REPORT_PATH,
    SEED,
    TARGET_SPLIT,
    TOP_K_CANDIDATES,
    build_error_analysis,
    load_validation_df,
    main,
    run_benchmark,
    run_compare_pipeline,
)

__all__ = [
    "ARTICLE_CHAR_THRESHOLD",
    "ENGINES",
    "PROTOCOL_VERSION_EXPECTED",
    "SCRIPT_REPORT_PATH",
    "SEED",
    "TARGET_SPLIT",
    "TOP_K_CANDIDATES",
    "build_error_analysis",
    "load_validation_df",
    "main",
    "run_benchmark",
    "run_compare_pipeline",
]

if __name__ == "__main__":
    if any(arg in {"-h", "--help"} for arg in sys.argv[1:]):
        print(
            "Legacy alias for Phase 1 extractive benchmark.\n"
            "Prefer: python scripts/benchmark_extractive_engines.py\n"
            "This alias runs the same benchmark when executed without --help."
        )
        raise SystemExit(0)
    main()
