from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_VALIDATION = ROOT / "data" / "processed" / "vietnews" / "validation.jsonl"


@pytest.mark.skipif(not _VALIDATION.is_file(), reason="VietNews validation split not present")
def test_run_multiformat_eval_includes_summary_engine_column() -> None:
    from scripts.shared.multiformat_experiment import run_multiformat_eval

    df, report = run_multiformat_eval(
        n=1,
        engine="textrank",
        max_sentences=2,
        seed=42,
        protocol_version="phase0_v2",
        target_split="validation",
        article_char_threshold=1200,
        warmup_engine=False,
        script_path="scripts/eval_multiformat_vietnews_file_formats.py",
    )
    assert "summary_engine" in df.columns
    ok = df[df["status"] == "ok"]
    if not ok.empty:
        assert (ok["summary_engine"] == "textrank").all()
    assert report["engine"] == "textrank"
