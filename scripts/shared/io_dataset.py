from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def load_split(processed_dir: Path, target_split: str, protocol_expected: str) -> tuple[pd.DataFrame, dict]:
    manifest_path = processed_dir / "dataset_manifest.json"
    split_path = processed_dir / f"{target_split}.jsonl"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    if not split_path.exists():
        raise FileNotFoundError(f"Processed split not found: {split_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    protocol_version = manifest.get("protocol_version")
    if protocol_version != protocol_expected:
        raise RuntimeError(
            f"Protocol version mismatch: expected {protocol_expected!r}, got {protocol_version!r}"
        )

    rows = [json.loads(line) for line in split_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError("Processed split is empty.")
    return df, manifest


def load_benchmark_validation_subset(
    df: pd.DataFrame,
    *,
    manifest: dict,
    processed_dir: Path,
    target_split: str,
    seed: int,
    subset_limit: int,
    article_char_threshold: int | None,
    required_cols: list[str] | None = None,
) -> tuple[pd.DataFrame, str, Path, Path]:
    cols = required_cols or ["guid", "article", "reference_summary", "meta"]
    missing_cols = [col for col in cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    protocol_version = str(manifest.get("protocol_version"))
    manifest_path = processed_dir / "dataset_manifest.json"
    split_path = processed_dir / f"{target_split}.jsonl"

    out = df.copy()
    out["article_char_len"] = out["meta"].map(lambda m: (m or {}).get("article_char_len", 0))
    out["reference_char_len"] = out["meta"].map(lambda m: (m or {}).get("reference_summary_char_len", 0))
    out = out[out["article"].fillna("").str.strip() != ""].copy()
    out = out[out["reference_summary"].fillna("").str.strip() != ""].copy()
    if article_char_threshold is not None:
        out = out[out["article_char_len"] >= article_char_threshold].copy()
    subset_df = out.sample(frac=1.0, random_state=seed).head(subset_limit).copy().reset_index(drop=True)
    return subset_df, protocol_version, manifest_path, split_path
