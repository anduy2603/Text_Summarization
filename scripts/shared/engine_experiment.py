from __future__ import annotations

import random
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
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

try:
    from IPython.display import Markdown as _IPythonMarkdown
    from IPython.display import display as _ipython_display
except ImportError:
    _IPythonMarkdown = None
    _ipython_display = None


def _display(obj: Any) -> None:
    if _ipython_display is not None:
        _ipython_display(obj)
        return

    text = obj.to_string() if hasattr(obj, "to_string") else str(obj)
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "utf-8"
        print(text.encode(encoding, errors="replace").decode(encoding))


def _display_markdown(text: str) -> None:
    if _ipython_display is not None and _IPythonMarkdown is not None:
        _ipython_display(_IPythonMarkdown(text))
        return
    _display(text)


@dataclass(frozen=True)
class EngineExperimentConfig:
    engine: str
    protocol_version: str = "phase0_v2"
    target_split: str = "validation"
    seed: int = 42
    top_k_candidates: tuple[int, ...] = (2, 3, 4, 5)
    subset_limit: int = 200
    article_char_threshold: int | None = 1200
    default_top_k: int = 3
    warmup_engine: bool = True

    def as_metadata(self) -> dict[str, Any]:
        data = asdict(self)
        data["top_k_candidates"] = list(self.top_k_candidates)
        return data


def load_engine_subset(
    config: EngineExperimentConfig,
) -> tuple[pd.DataFrame, str, Path, Path]:
    processed_dir = ROOT / "data" / "processed" / "vietnews"
    df, manifest = load_split(
        processed_dir,
        config.target_split,
        config.protocol_version,
    )
    return load_benchmark_validation_subset(
        df,
        manifest=manifest,
        processed_dir=processed_dir,
        target_split=config.target_split,
        seed=config.seed,
        subset_limit=config.subset_limit,
        article_char_threshold=config.article_char_threshold,
    )


def _join_selected_sentences(selected_sentences: list[str]) -> str:
    return " ".join(sentence.strip() for sentence in selected_sentences if sentence.strip())


def run_engine_smoke_test(
    *,
    engine: str,
    article: str,
    reference_summary: str | None = None,
    top_k: int = 3,
    use_stemmer: bool = False,
) -> dict[str, Any]:
    processed = process_from_text(article)
    t0 = time.perf_counter()
    selected_sentences, engine_meta = summarize_processed_input_raw(
        processed,
        max_sentences=top_k,
        ratio=None,
        engine_name=engine,
    )
    latency_sec = time.perf_counter() - t0
    predicted_summary = _join_selected_sentences(selected_sentences)

    result: dict[str, Any] = {
        "engine": engine,
        "top_k": top_k,
        "input_sentence_count": len(processed.sentences),
        "selected_sentence_count": len(selected_sentences),
        "summarizer_core_latency_sec": latency_sec,
        "predicted_summary": predicted_summary,
        "engine_meta": dict(engine_meta or {}),
    }
    if reference_summary is not None:
        evaluator = Evaluator(use_stemmer=use_stemmer)
        metrics = evaluator.evaluate_one(
            source_text=processed.cleaned_text,
            reference_summary=reference_summary,
            predicted_summary=predicted_summary,
            latency_sec=latency_sec,
            extra={},
        ).as_dict()
        metrics["summarizer_core_latency_sec"] = metrics.pop("latency_sec")
        result.update(metrics)
    return result


def display_engine_smoke_test(
    config: EngineExperimentConfig,
    *,
    top_k: int | None = None,
) -> dict[str, Any]:
    subset_df, _, _, _ = load_engine_subset(config)
    demo_row = subset_df.iloc[0]
    result = run_engine_smoke_test(
        engine=config.engine,
        article=str(demo_row["article"]),
        reference_summary=str(demo_row["reference_summary"]),
        top_k=top_k or config.default_top_k,
    )
    view = {
        "guid": demo_row.get("guid"),
        "engine": result["engine"],
        "top_k": result["top_k"],
        "input_sentence_count": result["input_sentence_count"],
        "selected_sentence_count": result["selected_sentence_count"],
        "rouge1_f": result.get("rouge1_f"),
        "rouge2_f": result.get("rouge2_f"),
        "rougeL_f": result.get("rougeL_f"),
        "summarizer_core_latency_sec": result["summarizer_core_latency_sec"],
        "predicted_summary": result["predicted_summary"],
    }
    _display(pd.DataFrame([view]))
    return result


def run_engine_benchmark(
    config: EngineExperimentConfig,
    *,
    use_stemmer: bool = False,
) -> dict[str, Any]:
    random.seed(config.seed)
    evaluator = Evaluator(use_stemmer=use_stemmer)
    subset_df, protocol_version, manifest_path, split_path = load_engine_subset(config)

    records: list[dict[str, Any]] = []
    warmup_done = False
    for top_k in config.top_k_candidates:
        for row in subset_df.to_dict(orient="records"):
            article = str(row.get("article", ""))
            reference = str(row.get("reference_summary", ""))
            if not article.strip() or not reference.strip():
                continue

            processed = process_from_text(article)
            if config.warmup_engine and not warmup_done and config.engine == "phobert-extractive":
                # Warm up model load/first forward pass so benchmark latency excludes cold start.
                summarize_processed_input_raw(
                    processed,
                    max_sentences=config.top_k_candidates[0],
                    ratio=None,
                    engine_name=config.engine,
                )
                warmup_done = True

            t0 = time.perf_counter()
            selected_sentences, engine_meta = summarize_processed_input_raw(
                processed,
                max_sentences=top_k,
                ratio=None,
                engine_name=config.engine,
            )
            latency_sec = time.perf_counter() - t0
            predicted_summary = _join_selected_sentences(selected_sentences)
            bundle = evaluator.evaluate_one(
                source_text=processed.cleaned_text,
                reference_summary=reference,
                predicted_summary=predicted_summary,
                latency_sec=latency_sec,
                extra={
                    "guid": row.get("guid"),
                    "engine": config.engine,
                    "top_k": top_k,
                    "article_char_len": row.get("article_char_len"),
                    "reference_char_len": row.get("reference_char_len"),
                    "selected_sentence_count": len(selected_sentences),
                    "predicted_summary": predicted_summary,
                    "engine_meta": dict(engine_meta or {}),
                },
            )
            rec = bundle.as_dict()
            rec["summarizer_core_latency_sec"] = rec.pop("latency_sec")
            records.append(rec)

    detail_df = pd.DataFrame(records)
    if detail_df.empty:
        raise RuntimeError(f"No benchmark records generated for engine {config.engine!r}.")

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
    selection_df, recommended = build_weighted_selection(summary_df)
    report = {
        "report_schema_version": "single_engine_notebook_experiment_v1",
        "engine": config.engine,
        "protocol_version": protocol_version,
        "target_split": config.target_split,
        "seed": config.seed,
        "top_k_candidates": list(config.top_k_candidates),
        "subset_limit": config.subset_limit,
        "article_char_threshold": config.article_char_threshold,
        "subset_rows": int(len(subset_df)),
        "manifest_path": str(manifest_path),
        "split_path": str(split_path),
        "recommended_top_k_by_weighted_rank": int(recommended["top_k"]),
        "selection_method": "weighted_rank",
        "latency_label": "summarizer_core_latency_sec",
        "latency_scope": "summarize_processed_input_raw only; preprocessing excluded",
        "environment": build_environment_snapshot(ROOT, package_names=["rouge-score"]),
    }
    return {
        "summary_df": summary_df,
        "detail_df": detail_df,
        "subset_df": subset_df,
        "selection_df": selection_df,
        "recommended": recommended,
        "report": report,
    }


def run_and_display_engine_benchmark(config: EngineExperimentConfig) -> dict[str, Any]:
    benchmark = run_engine_benchmark(config)
    _display(benchmark["summary_df"])
    return benchmark


def display_topk_selection(benchmark: dict[str, Any]) -> pd.DataFrame:
    selection_df = benchmark["selection_df"]
    metric_cols = [
        "top_k",
        "n",
        "rouge1_f",
        "rouge2_f",
        "rougeL_f",
        "compression_ratio",
        "repetition_rate",
        "summarizer_core_latency_sec",
        "weighted_rank_score",
    ]
    view = selection_df[metric_cols]
    _display(view)
    return view


def display_metric_trend(benchmark: dict[str, Any]) -> None:
    summary_df = benchmark["summary_df"]
    engine = str(benchmark["report"]["engine"])
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib is not installed; skipping chart.")
        return

    ax = summary_df.plot(
        x="top_k",
        y=["rouge1_f", "rouge2_f", "rougeL_f"],
        marker="o",
        figsize=(8, 4),
        title=f"{engine} ROUGE by top_k",
    )
    ax.set_xlabel("top_k")
    ax.set_ylabel("F1")
    ax.grid(True, alpha=0.25)
    plt.show()


def build_engine_interpretation(benchmark: dict[str, Any]) -> str:
    summary_df = benchmark["summary_df"].copy()
    recommended = benchmark["recommended"]
    report = benchmark["report"]
    engine = str(report["engine"])
    recommended_top_k = int(recommended["top_k"])
    recommended_row = summary_df[summary_df["top_k"] == recommended_top_k].iloc[0]
    best_quality_row = summary_df.sort_values("rougeL_f", ascending=False).iloc[0]
    fastest_row = summary_df.sort_values("summarizer_core_latency_sec", ascending=True).iloc[0]
    lowest_repetition_row = summary_df.sort_values("repetition_rate", ascending=True).iloc[0]

    lines = [
        "### Result Interpretation",
        "",
        (
            f"- Recommended `top_k`: `{recommended_top_k}` by weighted rank. "
            "This is the setting to carry into the thesis unless a later official run supersedes it."
        ),
        (
            "- Recommended-setting quality: "
            f"ROUGE-1 `{recommended_row['rouge1_f']:.4f}`, "
            f"ROUGE-2 `{recommended_row['rouge2_f']:.4f}`, "
            f"ROUGE-L `{recommended_row['rougeL_f']:.4f}`."
        ),
        (
            "- Recommended-setting behavior: "
            f"compression ratio `{recommended_row['compression_ratio']:.4f}`, "
            f"repetition rate `{recommended_row['repetition_rate']:.4f}`, "
            f"core latency `{recommended_row['summarizer_core_latency_sec']:.4f}s`."
        ),
        (
            f"- Best ROUGE-L appears at `top_k={int(best_quality_row['top_k'])}` "
            f"with ROUGE-L `{best_quality_row['rougeL_f']:.4f}`."
        ),
        (
            f"- Fastest setting is `top_k={int(fastest_row['top_k'])}` "
            f"with latency `{fastest_row['summarizer_core_latency_sec']:.4f}s`."
        ),
        (
            f"- Lowest repetition setting is `top_k={int(lowest_repetition_row['top_k'])}` "
            f"with repetition rate `{lowest_repetition_row['repetition_rate']:.4f}`."
        ),
        "",
    ]

    if int(best_quality_row["top_k"]) != recommended_top_k:
        lines.append(
            "The weighted-rank winner is not the pure ROUGE-L winner, so the report should describe this as a "
            "quality-versus-cost trade-off rather than only choosing the highest ROUGE score."
        )
    else:
        lines.append(
            "The weighted-rank winner also matches the best ROUGE-L setting, so this engine has a clear preferred "
            "`top_k` under the current protocol."
        )

    engine_notes = {
        "tfidf": (
            "For TF-IDF, emphasize that this is the lexical baseline: strong latency and simple explainability are "
            "expected, while weak cases usually come from missing semantic importance or selecting keyword-heavy "
            "sentences that are not summary-worthy."
        ),
        "textrank": (
            "For TextRank, focus on whether graph centrality improves ROUGE compared with TF-IDF and whether the "
            "selected sentences repeat central ideas. Latency should be discussed as the cost of pairwise sentence "
            "similarity and PageRank."
        ),
        "phobert-extractive": (
            "For PhoBERT-extractive, interpret quality together with runtime. A contextual Vietnamese model is only "
            "worth keeping in the system if the quality gain justifies model load, dependency, and latency costs."
        ),
    }
    note = engine_notes.get(engine)
    if note:
        lines.extend(["", note])
    return "\n".join(lines)


def display_engine_interpretation(benchmark: dict[str, Any]) -> str:
    interpretation = build_engine_interpretation(benchmark)
    _display_markdown(interpretation)
    return interpretation


def build_case_table(
    detail_df: pd.DataFrame,
    subset_df: pd.DataFrame,
    *,
    top_k: int,
    mode: str = "worst",
    n: int = 3,
    article_chars: int = 500,
    summary_chars: int = 400,
) -> pd.DataFrame:
    if mode not in {"best", "worst"}:
        raise ValueError("mode must be 'best' or 'worst'.")

    focused = detail_df[detail_df["top_k"] == top_k].copy()
    if focused.empty:
        return pd.DataFrame()
    focused["guid"] = focused["guid"].astype(str)

    source = subset_df.copy()
    source["guid"] = source["guid"].astype(str)
    merged = focused.merge(
        source[["guid", "article", "reference_summary"]],
        on="guid",
        how="left",
    )
    ordered = merged.nlargest(n, "rougeL_f") if mode == "best" else merged.nsmallest(n, "rougeL_f")
    out = ordered[
        [
            "guid",
            "top_k",
            "rouge1_f",
            "rouge2_f",
            "rougeL_f",
            "compression_ratio",
            "repetition_rate",
            "summarizer_core_latency_sec",
            "article",
            "reference_summary",
            "predicted_summary",
        ]
    ].copy()
    out["article"] = out["article"].fillna("").astype(str).str.slice(0, article_chars)
    out["reference_summary"] = out["reference_summary"].fillna("").astype(str).str.slice(0, summary_chars)
    out["predicted_summary"] = out["predicted_summary"].fillna("").astype(str).str.slice(0, summary_chars)
    return out.reset_index(drop=True)


def display_engine_cases(
    benchmark: dict[str, Any],
    *,
    n: int = 3,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    recommended_top_k = int(benchmark["recommended"]["top_k"])
    best_cases = build_case_table(
        benchmark["detail_df"],
        benchmark["subset_df"],
        top_k=recommended_top_k,
        mode="best",
        n=n,
    )
    worst_cases = build_case_table(
        benchmark["detail_df"],
        benchmark["subset_df"],
        top_k=recommended_top_k,
        mode="worst",
        n=n,
    )
    print("Best cases")
    _display(best_cases)
    print("Worst cases")
    _display(worst_cases)
    return best_cases, worst_cases


def display_experiment_report(benchmark: dict[str, Any]) -> dict[str, Any]:
    report = benchmark["report"]
    _display(pd.DataFrame([report]).T.rename(columns={0: "value"}))
    return report
