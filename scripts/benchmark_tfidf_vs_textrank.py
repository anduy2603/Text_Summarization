"""
Backward-compatible entry point for the Phase 1 multi-engine extractive benchmark.

Prefer running ``scripts/benchmark_extractive_engines.py`` (TF-IDF, TextRank,
PhoBERT-extractive). This module re-exports the same API so older imports and
commands keep working.
"""

from __future__ import annotations

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
    main()
