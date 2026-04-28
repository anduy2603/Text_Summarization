from __future__ import annotations

import json
import random
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(ROOT / "backend"))
if str(ROOT / "evaluation") not in sys.path:
    sys.path.insert(0, str(ROOT / "evaluation"))

from app.services.input import process_from_text
from app.services.summarization.tfidf_summarizer import summarize_with_tfidf
from evaluation.evaluator import Evaluator
from preprocess import preprocess_and_split
from scripts.shared.common import build_environment_snapshot, build_weighted_selection
from scripts.shared.io_dataset import load_split


def build_qa_artifact(project_root: Path, out_dir: Path, ts: str) -> Path:
    notebook_schema_version = "vietnews_data_qa_v2"
    protocol_expected = "phase0_v2"
    target_split = "validation"
    seed = 42
    preprocess_check_n = 500
    sample_n = 5
    pass_empty_ratio_threshold = 0.001
    acceptable_sentence_mismatch_rate_threshold = 0.01

    random.seed(seed)
    np.random.seed(seed)

    processed_dir = project_root / "data" / "processed" / "vietnews"
    df, manifest = load_split(processed_dir, target_split, protocol_expected)
    protocol_version = str(manifest.get("protocol_version"))

    required_cols = ["guid", "title", "article", "reference_summary", "meta"]
    required_meta_keys = [
        "protocol_version",
        "article_char_len",
        "reference_summary_char_len",
        "article_sentence_count",
        "reference_summary_sentence_count",
    ]

    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    def has_meta_key(meta: object, key: str) -> bool:
        return isinstance(meta, dict) and key in meta

    schema_rows: list[dict] = []
    for col in required_cols:
        null_count = int(df[col].isna().sum())
        empty_count = int((df[col].fillna("").astype(str).str.strip() == "").sum()) if col != "meta" else 0
        schema_rows.append(
            {
                "column": col,
                "dtype": str(df[col].dtype),
                "null_count": null_count,
                "empty_count": empty_count,
                "empty_ratio": (empty_count / len(df)) if len(df) and col != "meta" else 0.0,
            }
        )
    schema_df = pd.DataFrame(schema_rows)
    meta_schema_df = pd.DataFrame(
        [
            {
                "meta_key": key,
                "present_ratio": float(df["meta"].map(lambda m: has_meta_key(m, key)).mean()) if len(df) else 0.0,
            }
            for key in required_meta_keys
        ]
    )

    article_empty_ratio = float(schema_df.loc[schema_df["column"] == "article", "empty_ratio"].iloc[0])
    reference_empty_ratio = float(schema_df.loc[schema_df["column"] == "reference_summary", "empty_ratio"].iloc[0])
    meta_keys_full = bool((meta_schema_df["present_ratio"] == 1.0).all())
    pass_conditions = {
        "required_columns_present": len(missing_cols) == 0,
        "meta_key_coverage_is_100_percent": meta_keys_full,
        "article_empty_ratio_near_zero": article_empty_ratio <= pass_empty_ratio_threshold,
        "reference_summary_empty_ratio_near_zero": reference_empty_ratio <= pass_empty_ratio_threshold,
    }

    check_n = min(preprocess_check_n, len(df))
    check_df = df.sample(n=check_n, random_state=seed).copy()
    article_char_mismatch = 0
    reference_char_mismatch = 0
    article_sentence_mismatch = 0
    reference_sentence_mismatch = 0
    protocol_version_mismatch = 0
    for _, row in check_df.iterrows():
        meta = row.get("meta") or {}
        article_text, article_sents = preprocess_and_split(row.get("article"))
        reference_text, reference_sents = preprocess_and_split(row.get("reference_summary"))
        if len(article_text) != int(meta.get("article_char_len", -1)):
            article_char_mismatch += 1
        if len(reference_text) != int(meta.get("reference_summary_char_len", -1)):
            reference_char_mismatch += 1
        if len(article_sents) != int(meta.get("article_sentence_count", -1)):
            article_sentence_mismatch += 1
        if len(reference_sents) != int(meta.get("reference_summary_sentence_count", -1)):
            reference_sentence_mismatch += 1
        if str(meta.get("protocol_version")) != protocol_version:
            protocol_version_mismatch += 1

    preprocess_check = {
        "sample_size": int(check_n),
        "manifest_protocol_version": protocol_version,
        "article_char_mismatch": int(article_char_mismatch),
        "reference_char_mismatch": int(reference_char_mismatch),
        "article_sentence_mismatch": int(article_sentence_mismatch),
        "reference_sentence_mismatch": int(reference_sentence_mismatch),
        "protocol_version_mismatch": int(protocol_version_mismatch),
    }
    sentence_mismatch_total = article_sentence_mismatch + reference_sentence_mismatch
    sentence_mismatch_rate = (sentence_mismatch_total / (2 * check_n)) if check_n > 0 else 0.0
    preprocess_interpretation = {
        "preprocessing_consistent_strict": (
            article_char_mismatch == 0
            and reference_char_mismatch == 0
            and article_sentence_mismatch == 0
            and reference_sentence_mismatch == 0
            and protocol_version_mismatch == 0
        ),
        "acceptable_for_benchmark": (
            article_char_mismatch == 0
            and reference_char_mismatch == 0
            and protocol_version_mismatch == 0
            and sentence_mismatch_rate <= acceptable_sentence_mismatch_rate_threshold
        ),
        "sentence_mismatch_rate": float(sentence_mismatch_rate),
        "possible_cause_if_nonzero": (
            "Sentence-count mismatches typically indicate sentence-splitting drift or tokenization differences "
            "between the stored metadata and the current preprocessing helper."
            if sentence_mismatch_total > 0
            else "No sentence-count mismatch detected in the sampled audit set."
        ),
        "impact_assessment": (
            "Low impact"
            if sentence_mismatch_rate <= acceptable_sentence_mismatch_rate_threshold
            else "Requires manual inspection"
        ),
    }

    official_export_gate = all(pass_conditions.values()) and preprocess_interpretation["acceptable_for_benchmark"]
    if not official_export_gate:
        raise RuntimeError("QA hard gate did not pass. Official QA artifact export blocked.")

    df["article_char_len"] = df["meta"].map(lambda m: (m or {}).get("article_char_len", 0))
    df["reference_char_len"] = df["meta"].map(lambda m: (m or {}).get("reference_summary_char_len", 0))
    df["article_token_count"] = df["article"].fillna("").astype(str).str.split().str.len()
    df["reference_token_count"] = df["reference_summary"].fillna("").astype(str).str.split().str.len()
    df["article_sentence_count"] = df["meta"].map(lambda m: (m or {}).get("article_sentence_count", 0))
    df["reference_sentence_count"] = df["meta"].map(lambda m: (m or {}).get("reference_summary_sentence_count", 0))
    df["compression_ratio_chars"] = df["reference_char_len"] / df["article_char_len"].clip(lower=1)
    df["compression_ratio_sentences"] = df["reference_sentence_count"] / df["article_sentence_count"].clip(lower=1)

    length_stats = pd.DataFrame(
        [
            {
                "metric": "article_char_len",
                "mean": float(df["article_char_len"].mean()),
                "p50": float(df["article_char_len"].quantile(0.50)),
                "p90": float(df["article_char_len"].quantile(0.90)),
                "p95": float(df["article_char_len"].quantile(0.95)),
                "max": float(df["article_char_len"].max()),
            },
            {
                "metric": "reference_char_len",
                "mean": float(df["reference_char_len"].mean()),
                "p50": float(df["reference_char_len"].quantile(0.50)),
                "p90": float(df["reference_char_len"].quantile(0.90)),
                "p95": float(df["reference_char_len"].quantile(0.95)),
                "max": float(df["reference_char_len"].max()),
            },
            {
                "metric": "article_token_count",
                "mean": float(df["article_token_count"].mean()),
                "p50": float(df["article_token_count"].quantile(0.50)),
                "p90": float(df["article_token_count"].quantile(0.90)),
                "p95": float(df["article_token_count"].quantile(0.95)),
                "max": float(df["article_token_count"].max()),
            },
            {
                "metric": "reference_token_count",
                "mean": float(df["reference_token_count"].mean()),
                "p50": float(df["reference_token_count"].quantile(0.50)),
                "p90": float(df["reference_token_count"].quantile(0.90)),
                "p95": float(df["reference_token_count"].quantile(0.95)),
                "max": float(df["reference_token_count"].max()),
            },
        ]
    )
    sentence_stats = pd.DataFrame(
        [
            {
                "metric": "article_sentence_count",
                "mean": float(df["article_sentence_count"].mean()),
                "p50": float(df["article_sentence_count"].quantile(0.50)),
                "p90": float(df["article_sentence_count"].quantile(0.90)),
                "p95": float(df["article_sentence_count"].quantile(0.95)),
                "max": float(df["article_sentence_count"].max()),
            },
            {
                "metric": "reference_sentence_count",
                "mean": float(df["reference_sentence_count"].mean()),
                "p50": float(df["reference_sentence_count"].quantile(0.50)),
                "p90": float(df["reference_sentence_count"].quantile(0.90)),
                "p95": float(df["reference_sentence_count"].quantile(0.95)),
                "max": float(df["reference_sentence_count"].max()),
            },
        ]
    )
    compression_stats = pd.DataFrame(
        [
            {
                "metric": "compression_ratio_chars",
                "mean": float(df["compression_ratio_chars"].mean()),
                "p50": float(df["compression_ratio_chars"].quantile(0.50)),
                "p90": float(df["compression_ratio_chars"].quantile(0.90)),
                "min": float(df["compression_ratio_chars"].min()),
                "max": float(df["compression_ratio_chars"].max()),
            },
            {
                "metric": "compression_ratio_sentences",
                "mean": float(df["compression_ratio_sentences"].mean()),
                "p50": float(df["compression_ratio_sentences"].quantile(0.50)),
                "p90": float(df["compression_ratio_sentences"].quantile(0.90)),
                "min": float(df["compression_ratio_sentences"].min()),
                "max": float(df["compression_ratio_sentences"].max()),
            },
        ]
    )

    environment_snapshot = build_environment_snapshot(
        project_root,
        package_names=["matplotlib"],
    )
    environment_snapshot.update(
        {
        "pandas_version": pd.__version__,
        "numpy_version": np.__version__,
        }
    )
    config_snapshot = {
        "notebook_schema_version": notebook_schema_version,
        "protocol_version_expected": protocol_expected,
        "target_split": target_split,
        "seed": seed,
        "preprocess_check_n": preprocess_check_n,
        "sample_n": sample_n,
        "pass_empty_ratio_threshold": pass_empty_ratio_threshold,
        "acceptable_sentence_mismatch_rate_threshold": acceptable_sentence_mismatch_rate_threshold,
    }
    conclusion = {
        "data_health": {
            "required_columns_present": len(missing_cols) == 0,
            "meta_key_coverage_is_100_percent": meta_keys_full,
            "article_empty_ratio": article_empty_ratio,
            "reference_summary_empty_ratio": reference_empty_ratio,
            "pass_conditions": pass_conditions,
        },
        "protocol_consistency": {
            "preprocess_check": preprocess_check,
            "interpretation": preprocess_interpretation,
        },
        "distribution_summary": {
            "article_char_len_p50": float(df["article_char_len"].quantile(0.50)),
            "article_char_len_p90": float(df["article_char_len"].quantile(0.90)),
            "reference_char_len_p50": float(df["reference_char_len"].quantile(0.50)),
            "reference_char_len_p90": float(df["reference_char_len"].quantile(0.90)),
            "compression_ratio_chars_mean": float(df["compression_ratio_chars"].mean()),
            "compression_ratio_chars_p90": float(df["compression_ratio_chars"].quantile(0.90)),
        },
    }

    artifact_path = out_dir / f"vietnews_data_check_summary_{target_split}_{ts}.json"
    payload = {
        "report_schema_version": notebook_schema_version,
        "notebook": "01_vietnews_data_check.ipynb",
        "run_purpose": "official_thesis_data_qa",
        "target_split": target_split,
        "rows": int(len(df)),
        "timestamp": ts,
        "protocol_version": protocol_version,
        "manifest_path": str(processed_dir / "dataset_manifest.json"),
        "manifest_global_stats": manifest.get("global_stats", {}),
        "manifest_split_stats": (manifest.get("splits") or {}).get(target_split, {}),
        "environment": environment_snapshot,
        "config_snapshot": config_snapshot,
        "schema": schema_df.to_dict(orient="records"),
        "meta_schema": meta_schema_df.to_dict(orient="records"),
        "pass_conditions": pass_conditions,
        "official_export_gate": official_export_gate,
        "length_stats": length_stats.to_dict(orient="records"),
        "sentence_stats": sentence_stats.to_dict(orient="records"),
        "compression_stats": compression_stats.to_dict(orient="records"),
        "preprocess_check": preprocess_check,
        "preprocess_interpretation": preprocess_interpretation,
        "conclusion": conclusion,
    }
    artifact_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return artifact_path


def bootstrap_ci_mean(values: pd.Series, n_boot: int, seed: int) -> tuple[float, float]:
    arr = values.dropna().to_numpy(dtype=float)
    if len(arr) == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    boot_means = []
    for _ in range(n_boot):
        sample = rng.choice(arr, size=len(arr), replace=True)
        boot_means.append(float(sample.mean()))
    low, high = np.percentile(boot_means, [2.5, 97.5])
    return float(low), float(high)


def build_tfidf_artifacts(project_root: Path, out_dir: Path, ts: str) -> tuple[Path, Path, Path]:
    notebook_schema_version = "tfidf_phase1_benchmark_v2"
    protocol_expected = "phase0_v2"
    target_split = "validation"
    seed = 42
    bootstrap_samples = 300
    top_k_candidates = [2, 3, 4, 5]
    subset_limit = 200
    article_char_threshold = 1200

    random.seed(seed)
    np.random.seed(seed)
    evaluator = Evaluator(use_stemmer=False)
    processed_dir = project_root / "data" / "processed" / "vietnews"
    df, manifest = load_split(processed_dir, target_split, protocol_expected)
    protocol_version = str(manifest.get("protocol_version"))

    required_cols = ["guid", "title", "article", "reference_summary", "meta"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in processed split: {missing_cols}")

    df["article_char_len"] = df["meta"].map(lambda m: (m or {}).get("article_char_len", 0))
    df["reference_char_len"] = df["meta"].map(lambda m: (m or {}).get("reference_summary_char_len", 0))
    df = df[df["article"].fillna("").str.strip() != ""].copy()
    df = df[df["reference_summary"].fillna("").str.strip() != ""].copy()
    if article_char_threshold is not None:
        df = df[df["article_char_len"] >= article_char_threshold].copy()
    subset_df = df.sample(frac=1.0, random_state=seed).head(subset_limit).copy().reset_index(drop=True)

    def summarize_article(article: str, top_k: int) -> tuple[str, dict, float, str]:
        processed = process_from_text(article)
        t0 = time.perf_counter()
        selected_sentences, engine_meta = summarize_with_tfidf(
            processed.sentences,
            max_sentences=top_k,
            ratio=None,
        )
        summarizer_core_latency_sec = time.perf_counter() - t0
        summary = " ".join(sentence.strip() for sentence in selected_sentences if sentence.strip())
        return summary, engine_meta, summarizer_core_latency_sec, processed.cleaned_text

    records: list[dict] = []
    for top_k in top_k_candidates:
        for row in subset_df.to_dict(orient="records"):
            article = str(row.get("article", ""))
            reference = str(row.get("reference_summary", ""))
            if not article.strip() or not reference.strip():
                continue
            predicted_summary, engine_meta, summarizer_core_latency_sec, cleaned_article = summarize_article(
                article, top_k
            )
            bundle = evaluator.evaluate_one(
                source_text=cleaned_article,
                reference_summary=reference,
                predicted_summary=predicted_summary,
                latency_sec=summarizer_core_latency_sec,
                extra={
                    "guid": row.get("guid"),
                    "top_k": top_k,
                    "article_char_len": row.get("article_char_len"),
                    "reference_char_len": row.get("reference_char_len"),
                    "engine": engine_meta.get("engine", "tfidf"),
                },
            )
            rec = bundle.as_dict()
            rec["summarizer_core_latency_sec"] = rec.pop("latency_sec")
            records.append(rec)

    bench_df = pd.DataFrame(records)
    if bench_df.empty:
        raise RuntimeError("No valid samples are available for benchmarking.")

    metric_columns = [
        "rouge1_f",
        "rouge2_f",
        "rougeL_f",
        "summarizer_core_latency_sec",
        "compression_ratio",
        "repetition_rate",
    ]
    summary_rows: list[dict] = []
    for top_k, group in bench_df.groupby("top_k"):
        row = {"top_k": int(top_k), "n": int(len(group))}
        for metric in metric_columns:
            row[f"{metric}_mean"] = float(group[metric].mean())
            row[f"{metric}_std"] = float(group[metric].std(ddof=1)) if len(group) > 1 else 0.0
            ci_low, ci_high = bootstrap_ci_mean(group[metric], n_boot=bootstrap_samples, seed=seed + int(top_k))
            row[f"{metric}_ci95_low"] = ci_low
            row[f"{metric}_ci95_high"] = ci_high
        summary_rows.append(row)
    summary_df = pd.DataFrame(summary_rows).sort_values("top_k").reset_index(drop=True)

    selection_view_df, recommended_row = build_weighted_selection(
        summary_df,
        metric_columns={
            "rouge1": "rouge1_f_mean",
            "rouge2": "rouge2_f_mean",
            "rougeL": "rougeL_f_mean",
            "compression": "compression_ratio_mean",
            "repetition": "repetition_rate_mean",
            "latency": "summarizer_core_latency_sec_mean",
        },
    )

    best_by_metric = {
        "rouge1_f": int(summary_df.sort_values("rouge1_f_mean", ascending=False).iloc[0]["top_k"]),
        "rouge2_f": int(summary_df.sort_values("rouge2_f_mean", ascending=False).iloc[0]["top_k"]),
        "rougeL_f": int(summary_df.sort_values("rougeL_f_mean", ascending=False).iloc[0]["top_k"]),
        "compression_ratio": int(summary_df.sort_values("compression_ratio_mean", ascending=True).iloc[0]["top_k"]),
        "repetition_rate": int(summary_df.sort_values("repetition_rate_mean", ascending=True).iloc[0]["top_k"]),
        "summarizer_core_latency_sec": int(
            summary_df.sort_values("summarizer_core_latency_sec_mean", ascending=True).iloc[0]["top_k"]
        ),
    }

    environment_snapshot = build_environment_snapshot(
        project_root,
        package_names=["rouge-score", "pydantic"],
    )
    environment_snapshot.update(
        {
        "pandas_version": pd.__version__,
        "numpy_version": np.__version__,
        }
    )
    config_snapshot = {
        "notebook_schema_version": notebook_schema_version,
        "protocol_version_expected": protocol_expected,
        "target_split": target_split,
        "seed": seed,
        "bootstrap_samples": bootstrap_samples,
        "top_k_candidates": top_k_candidates,
        "subset_limit": subset_limit,
        "article_char_threshold": article_char_threshold,
    }

    summary_path = out_dir / f"tfidf_phase1_topk_summary_{ts}.csv"
    detail_path = out_dir / f"tfidf_phase1_topk_detail_{ts}.csv"
    report_path = out_dir / f"tfidf_phase1_topk_report_{ts}.json"
    summary_df.to_csv(summary_path, index=False, encoding="utf-8")
    bench_df.to_csv(detail_path, index=False, encoding="utf-8")

    report_payload = {
        "report_schema_version": notebook_schema_version,
        "notebook": "02_tfidf_experiment.ipynb",
        "protocol_version": protocol_version,
        "target_split": target_split,
        "seed": seed,
        "bootstrap_samples": bootstrap_samples,
        "top_k_candidates": top_k_candidates,
        "article_char_threshold": article_char_threshold,
        "subset_limit": subset_limit,
        "subset_rows": int(len(subset_df)),
        "subset_guid_sample": subset_df["guid"].head(20).tolist(),
        "environment": environment_snapshot,
        "config_snapshot": config_snapshot,
        "recommended_top_k_by_weighted_rank": int(recommended_row["top_k"]),
        "official_top_k": int(recommended_row["top_k"]),
        "official_top_k_rationale": (
            "Locked to weighted-rank winner for this official run. "
            "Update only when a newer official rerun supersedes this artifact."
        ),
        "best_by_metric": best_by_metric,
        "benchmark_notes": {
            "latency_label": "summarizer_core_latency_sec",
            "latency_scope": "Measured around summarize_with_tfidf only; excludes process_from_text",
            "selection_method": "Weighted rank over ROUGE-1/2/L, compression_ratio, repetition_rate, latency",
        },
        "summary_csv": str(summary_path),
        "detail_csv": str(detail_path),
        "manifest_path": str(processed_dir / "dataset_manifest.json"),
        "split_path": str(processed_dir / f"{target_split}.jsonl"),
    }
    report_path.write_text(json.dumps(report_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary_path, detail_path, report_path


def main() -> None:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    official_dir = ROOT / "notebooks" / "results" / "official" / "validation"
    official_dir.mkdir(parents=True, exist_ok=True)
    qa_path = build_qa_artifact(ROOT, official_dir, ts)
    summary_path, detail_path, report_path = build_tfidf_artifacts(ROOT, official_dir, ts)
    print("Generated official artifacts:")
    print(f"- {qa_path}")
    print(f"- {summary_path}")
    print(f"- {detail_path}")
    print(f"- {report_path}")


if __name__ == "__main__":
    main()
