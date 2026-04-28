from __future__ import annotations

import platform
import subprocess
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import pandas as pd


def safe_version(package_name: str) -> str | None:
    try:
        return version(package_name)
    except PackageNotFoundError:
        return None


def safe_git_commit(repo_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except Exception:
        return None


def is_git_dirty(repo_root: Path) -> bool | None:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
        return bool(result.stdout.strip())
    except Exception:
        return None


def build_environment_snapshot(repo_root: Path, package_names: list[str]) -> dict:
    snapshot = {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "git_commit": safe_git_commit(repo_root),
        "git_dirty": is_git_dirty(repo_root),
    }
    for package_name in package_names:
        key = f"{package_name.replace('-', '_')}_version"
        snapshot[key] = safe_version(package_name)
    return snapshot


def build_weighted_selection(
    summary_df: pd.DataFrame,
    metric_columns: dict[str, str] | None = None,
) -> tuple[pd.DataFrame, dict]:
    columns = metric_columns or {
        "rouge1": "rouge1_f",
        "rouge2": "rouge2_f",
        "rougeL": "rougeL_f",
        "compression": "compression_ratio",
        "repetition": "repetition_rate",
        "latency": "summarizer_core_latency_sec",
    }
    selection_view_df = summary_df.copy()
    selection_view_df["rank_rouge1"] = selection_view_df[columns["rouge1"]].rank(ascending=False, method="min")
    selection_view_df["rank_rouge2"] = selection_view_df[columns["rouge2"]].rank(ascending=False, method="min")
    selection_view_df["rank_rougeL"] = selection_view_df[columns["rougeL"]].rank(ascending=False, method="min")
    selection_view_df["rank_compression"] = selection_view_df[columns["compression"]].rank(
        ascending=True,
        method="min",
    )
    selection_view_df["rank_repetition"] = selection_view_df[columns["repetition"]].rank(
        ascending=True,
        method="min",
    )
    selection_view_df["rank_latency"] = selection_view_df[columns["latency"]].rank(ascending=True, method="min")
    selection_view_df["weighted_rank_score"] = (
        0.30 * selection_view_df["rank_rouge1"]
        + 0.20 * selection_view_df["rank_rouge2"]
        + 0.25 * selection_view_df["rank_rougeL"]
        + 0.15 * selection_view_df["rank_compression"]
        + 0.05 * selection_view_df["rank_repetition"]
        + 0.05 * selection_view_df["rank_latency"]
    )
    selection_view_df = selection_view_df.sort_values(
        ["weighted_rank_score", columns["rouge1"]],
        ascending=[True, False],
    ).reset_index(drop=True)
    return selection_view_df, selection_view_df.iloc[0].to_dict()
