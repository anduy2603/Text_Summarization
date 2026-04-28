from __future__ import annotations

import json
import random
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(ROOT / "backend"))
if str(ROOT / "evaluation") not in sys.path:
    sys.path.insert(0, str(ROOT / "evaluation"))

from app.services.input import process_from_text
from app.services.summarization.summary_service import summarize_processed_input_raw
from evaluation.evaluator import Evaluator
from scripts.shared.common import build_environment_snapshot, build_weighted_selection
from scripts.shared.io_dataset import load_benchmark_validation_subset, load_split

PROTOCOL_VERSION_EXPECTED = "phase0_v2"
TARGET_SPLIT = "validation"
SEED = 42
ENGINES = ["tfidf", "textrank", "phobert-extractive"]
TOP_K_CANDIDATES = [2, 3, 4, 5]
SUBSET_LIMIT = 200
ARTICLE_CHAR_THRESHOLD = 1200


def load_validation_df() -> tuple[pd.DataFrame, str, Path, Path]:
    processed_dir = ROOT / "data" / "processed" / "vietnews"
    df, manifest = load_split(processed_dir, TARGET_SPLIT, PROTOCOL_VERSION_EXPECTED)
    return load_benchmark_validation_subset(
        df,
        manifest=manifest,
        processed_dir=processed_dir,
        target_split=TARGET_SPLIT,
        seed=SEED,
        subset_limit=SUBSET_LIMIT,
        article_char_threshold=ARTICLE_CHAR_THRESHOLD,
    )


def build_error_analysis(
    detail_df: pd.DataFrame,
    split_df: pd.DataFrame,
    engine: str,
    top_k: int,
    out_path: Path,
) -> None:
    focused_df = detail_df[(detail_df["engine"] == engine) & (detail_df["top_k"] == top_k)].copy()
    if focused_df.empty:
        return
    split_df = split_df.copy()
    split_df["guid"] = split_df["guid"].astype(str)
    focused_df["guid"] = focused_df["guid"].astype(str)
    lookup = {row["guid"]: row for row in split_df.to_dict(orient="records")}
    failure_rows = focused_df.nsmallest(3, "rougeL_f")
    lines = [
        f"# {engine.upper()} Short Error Analysis",
        "",
        f"- Official `top_k`: `{top_k}`",
        f"- Sample size: `{len(focused_df)}`",
        (
            "- Mean ROUGE-1/2/L: "
            f"`{focused_df['rouge1_f'].mean():.4f}` / "
            f"`{focused_df['rouge2_f'].mean():.4f}` / "
            f"`{focused_df['rougeL_f'].mean():.4f}`"
        ),
        f"- Mean compression ratio: `{focused_df['compression_ratio'].mean():.4f}`",
        f"- Mean repetition rate: `{focused_df['repetition_rate'].mean():.4f}`",
        "",
        "## Failure Cases (3 lowest ROUGE-L)",
    ]
    for idx, row in enumerate(failure_rows.to_dict(orient="records"), start=1):
        source = lookup.get(str(row["guid"]), {})
        lines.extend(
            [
                f"### Case {idx} - guid {row['guid']}",
                f"- ROUGE-1/2/L: `{row['rouge1_f']:.4f}` / `{row['rouge2_f']:.4f}` / `{row['rougeL_f']:.4f}`",
                f"- Article snippet: {str(source.get('article', ''))[:500].replace(chr(10), ' ')}",
                f"- Reference summary: {str(source.get('reference_summary', ''))[:500].replace(chr(10), ' ')}",
                f"- Predicted summary: {str(row.get('predicted_summary', ''))[:500].replace(chr(10), ' ')}",
                "",
            ]
        )
    out_path.write_text("\n".join(lines), encoding="utf-8")


def run_benchmark() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    random.seed(SEED)
    evaluator = Evaluator(use_stemmer=False)
    subset_df, protocol_version, manifest_path, split_path = load_validation_df()
    rows = [json.loads(line) for line in split_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    split_df = pd.DataFrame(rows)
    warmup_done: set[str] = set()
    records: list[dict] = []
    for engine in ENGINES:
        for top_k in TOP_K_CANDIDATES:
            for row in subset_df.to_dict(orient="records"):
                article = str(row.get("article", ""))
                reference = str(row.get("reference_summary", ""))
                if not article.strip() or not reference.strip():
                    continue
                processed = process_from_text(article)
                if engine == "phobert-extractive" and engine not in warmup_done:
                    # Warm up model load/first forward pass so latency excludes one-time cold start.
                    summarize_processed_input_raw(
                        processed,
                        max_sentences=TOP_K_CANDIDATES[0],
                        ratio=None,
                        engine_name=engine,
                    )
                    warmup_done.add(engine)
                t0 = time.perf_counter()
                selected_sentences, engine_meta = summarize_processed_input_raw(
                    processed,
                    max_sentences=top_k,
                    ratio=None,
                    engine_name=engine,
                )
                latency_sec = time.perf_counter() - t0
                predicted_summary = " ".join(sentence.strip() for sentence in selected_sentences if sentence.strip())
                bundle = evaluator.evaluate_one(
                    source_text=processed.cleaned_text,
                    reference_summary=reference,
                    predicted_summary=predicted_summary,
                    latency_sec=latency_sec,
                    extra={
                        "guid": row.get("guid"),
                        "engine": engine,
                        "top_k": top_k,
                        "article_char_len": row.get("article_char_len"),
                        "reference_char_len": row.get("reference_char_len"),
                        "predicted_summary": predicted_summary,
                    },
                )
                rec = bundle.as_dict()
                rec["summarizer_core_latency_sec"] = rec.pop("latency_sec")
                records.append(rec)

    detail_df = pd.DataFrame(records)
    if detail_df.empty:
        raise RuntimeError("No benchmark records generated.")

    summary_df = (
        detail_df.groupby(["engine", "top_k"], as_index=False)
        .agg(
            n=("top_k", "count"),
            rouge1_f=("rouge1_f", "mean"),
            rouge2_f=("rouge2_f", "mean"),
            rougeL_f=("rougeL_f", "mean"),
            summarizer_core_latency_sec=("summarizer_core_latency_sec", "mean"),
            compression_ratio=("compression_ratio", "mean"),
            repetition_rate=("repetition_rate", "mean"),
        )
        .sort_values(["engine", "top_k"])
        .reset_index(drop=True)
    )

    best_rows = []
    for engine in ENGINES:
        engine_summary = summary_df[summary_df["engine"] == engine].copy()
        if engine_summary.empty:
            continue
        _, recommended = build_weighted_selection(engine_summary)
        best_rows.append(
            {
                "engine": engine,
                "top_k": int(recommended["top_k"]),
                "rouge1_f": float(recommended["rouge1_f"]),
                "rouge2_f": float(recommended["rouge2_f"]),
                "rougeL_f": float(recommended["rougeL_f"]),
                "compression_ratio": float(recommended["compression_ratio"]),
                "repetition_rate": float(recommended["repetition_rate"]),
                "summarizer_core_latency_sec": float(recommended["summarizer_core_latency_sec"]),
                "weighted_rank_score": float(recommended["weighted_rank_score"]),
            }
        )
    best_by_engine = {
        row["engine"]: {
            "top_k": int(row["top_k"]),
            "rouge1_f": float(row["rouge1_f"]),
            "rouge2_f": float(row["rouge2_f"]),
            "rougeL_f": float(row["rougeL_f"]),
            "compression_ratio": float(row["compression_ratio"]),
            "repetition_rate": float(row["repetition_rate"]),
            "summarizer_core_latency_sec": float(row["summarizer_core_latency_sec"]),
            "weighted_rank_score": float(row["weighted_rank_score"]),
        }
        for row in best_rows
    }

    environment = build_environment_snapshot(
        ROOT,
        package_names=["rouge-score"],
    )
    environment.update(
        {
        "pandas_version": pd.__version__,
        }
    )
    report = {
        "report_schema_version": "engine_compare_v1",
        "notebook_or_script": "scripts/benchmark_tfidf_vs_textrank.py",
        "protocol_version": protocol_version,
        "target_split": TARGET_SPLIT,
        "seed": SEED,
        "engines": ENGINES,
        "top_k_candidates": TOP_K_CANDIDATES,
        "subset_limit": SUBSET_LIMIT,
        "article_char_threshold": ARTICLE_CHAR_THRESHOLD,
        "subset_rows": int(len(subset_df)),
        "subset_guid_sample": subset_df["guid"].head(20).tolist(),
        "manifest_path": str(manifest_path),
        "split_path": str(split_path),
        "best_by_engine": best_by_engine,
        "environment": environment,
        "selection_method": "weighted_rank",
    }
    return summary_df, detail_df, split_df, report


def run_compare_pipeline(out_dir: Path, ts: str) -> list[Path]:
    summary_df, detail_df, split_df, report = run_benchmark()
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_path = out_dir / f"engine_compare_summary_{ts}.csv"
    detail_path = out_dir / f"engine_compare_detail_{ts}.csv"
    report_path = out_dir / f"engine_compare_report_{ts}.json"
    summary_df.to_csv(summary_path, index=False, encoding="utf-8")
    detail_df.to_csv(detail_path, index=False, encoding="utf-8")
    report["summary_csv"] = str(summary_path)
    report["detail_csv"] = str(detail_path)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    per_engine_paths: list[Path] = []
    for engine in ENGINES:
        engine_summary = summary_df[summary_df["engine"] == engine].copy().reset_index(drop=True)
        engine_detail = detail_df[detail_df["engine"] == engine].copy().reset_index(drop=True)
        if engine_summary.empty or engine_detail.empty:
            continue
        _, recommended = build_weighted_selection(engine_summary)
        top_k = int(recommended["top_k"])
        engine_prefix = engine.replace("-extractive", "")
        engine_summary_path = out_dir / f"{engine_prefix}_phase1_topk_summary_{ts}.csv"
        engine_detail_path = out_dir / f"{engine_prefix}_phase1_topk_detail_{ts}.csv"
        engine_report_path = out_dir / f"{engine_prefix}_phase1_topk_report_{ts}.json"
        engine_error_path = out_dir / f"{engine_prefix}_phase1_error_analysis_{ts}.md"
        engine_summary.to_csv(engine_summary_path, index=False, encoding="utf-8")
        engine_detail.to_csv(engine_detail_path, index=False, encoding="utf-8")
        engine_report = {
            "report_schema_version": f"{engine_prefix}_phase1_benchmark_v1",
            "notebook_or_script": "scripts/benchmark_tfidf_vs_textrank.py",
            "protocol_version": report["protocol_version"],
            "target_split": TARGET_SPLIT,
            "seed": SEED,
            "top_k_candidates": TOP_K_CANDIDATES,
            "subset_limit": SUBSET_LIMIT,
            "article_char_threshold": ARTICLE_CHAR_THRESHOLD,
            "subset_rows": int(len(engine_detail["guid"].unique())),
            "environment": report["environment"],
            "recommended_top_k_by_weighted_rank": top_k,
            "official_top_k": top_k,
            "official_top_k_rationale": (
                "Locked to weighted-rank winner using the shared extractive protocol "
                "(ROUGE-1/2/L, compression_ratio, repetition_rate, latency)."
            ),
            "benchmark_notes": {
                "latency_label": "summarizer_core_latency_sec",
                "latency_scope": f"Measured around summarize_processed_input_raw(engine='{engine}') only",
                "selection_method": "Weighted rank over ROUGE-1/2/L, compression_ratio, repetition_rate, latency",
            },
            "summary_csv": str(engine_summary_path),
            "detail_csv": str(engine_detail_path),
            "manifest_path": report["manifest_path"],
            "split_path": report["split_path"],
        }
        if engine == "phobert-extractive":
            engine_report["benchmark_notes"]["sentence_segmentation"] = "pyvi-vitokenizer"
            engine_report["benchmark_notes"]["segmentation_required"] = True
        engine_report_path.write_text(json.dumps(engine_report, ensure_ascii=False, indent=2), encoding="utf-8")
        build_error_analysis(
            detail_df=engine_detail,
            split_df=split_df,
            engine=engine,
            top_k=top_k,
            out_path=engine_error_path,
        )
        per_engine_paths.extend(
            [
                engine_summary_path,
                engine_detail_path,
                engine_report_path,
                engine_error_path,
            ]
        )

    print("Saved:")
    print(summary_path)
    print(detail_path)
    print(report_path)
    for path in per_engine_paths:
        print(path)
    return [
        summary_path,
        detail_path,
        report_path,
        *per_engine_paths,
    ]


def main() -> None:
    out_dir = ROOT / "notebooks" / "results" / "official" / "validation"
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_compare_pipeline(out_dir=out_dir, ts=ts)


if __name__ == "__main__":
    main()
