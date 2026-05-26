from __future__ import annotations

import difflib
import sys
import time
from dataclasses import asdict, dataclass
from io import BytesIO
from pathlib import Path
from typing import Any, Callable

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(ROOT / "backend"))
if str(ROOT / "evaluation") not in sys.path:
    sys.path.insert(0, str(ROOT / "evaluation"))

from docx import Document

from app.schemas.input import ProcessedInput
from app.services.input import InputLoadError, InputValidationError, process_from_bytes, process_from_text
from app.services.summarization.summary_service import (
    SummaryEngineNotReadyError,
    summarize_processed_input_raw,
)
from evaluation.evaluator import Evaluator
from scripts.shared.io_dataset import load_benchmark_validation_subset, load_split

try:
    from IPython.display import Markdown as _IPythonMarkdown
    from IPython.display import display as _ipython_display
except ImportError:
    _IPythonMarkdown = None
    _ipython_display = None

REPORT_SCHEMA_V2 = "multiformat_vietnews_file_formats_v2"
BASELINE_FORMAT = "text_baseline"
FORMAT_LABELS = (BASELINE_FORMAT, "file_txt", "file_docx", "file_pdf")

FORMAT_LOADER_LABELS: dict[str, str] = {
    BASELINE_FORMAT: "process_from_text (paste / API text)",
    "file_txt": "load_txt_bytes → chardet decode",
    "file_docx": "load_docx_bytes → paragraphs + tables",
    "file_pdf": "load_pdf_bytes → PyMuPDF page.get_text",
}

PDF_ENCODING_NOTE = (
    "Synthetic PDFs use Base-14 Helvetica; Vietnamese tone marks may be substituted "
    "in extracted text. Prefer TXT/DOCX rows for strict parity; use PDF for pipeline stress."
)


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
class MultiformatEvalConfig:
    engine: str = "textrank"
    protocol_version: str = "phase0_v2"
    target_split: str = "validation"
    seed: int = 42
    subset_limit: int = 20
    max_sentences: int = 2
    article_char_threshold: int | None = 1200
    warmup_engine: bool = False

    def as_metadata(self) -> dict[str, Any]:
        return asdict(self)


def build_txt_bytes(text: str) -> bytes:
    return text.encode("utf-8")


def build_docx_bytes(text: str) -> bytes:
    buf = BytesIO()
    doc = Document()
    doc.add_paragraph(text)
    doc.save(buf)
    return buf.getvalue()


def build_pdf_bytes(text: str) -> bytes:
    import fitz

    doc = fitz.open()
    w, h = fitz.paper_size("a4")
    rect = fitz.Rect(50, 50, w - 50, h - 50)
    chunk_size = 2400
    for i in range(0, len(text), chunk_size):
        chunk = text[i : i + chunk_size]
        page = doc.new_page(width=w, height=h)
        page.insert_textbox(rect, chunk, fontname="helv", fontsize=10)
    return doc.tobytes()


def count_replacement_chars(text: str) -> int:
    if not text:
        return 0
    bad = 0
    for ch in text:
        if ch == "\ufffd":
            bad += 1
        elif ord(ch) < 32 and ch not in "\n\t":
            bad += 1
    return bad


def compute_ingestion_fidelity(
    baseline: ProcessedInput,
    candidate: ProcessedInput,
    *,
    evaluator: Evaluator | None = None,
) -> dict[str, Any]:
    base_text = baseline.cleaned_text
    cand_text = candidate.cleaned_text
    base_len = len(base_text)
    cand_len = len(cand_text)
    char_ratio = (cand_len / base_len) if base_len else (1.0 if cand_len == 0 else 0.0)

    ev = evaluator or Evaluator(use_stemmer=False)
    ingest_rouge = ev.compute_rouge(base_text, cand_text)

    return {
        "ingest_exact_match": base_text == cand_text,
        "ingest_char_len_ratio": float(char_ratio),
        "ingest_sentence_count_delta": abs(len(candidate.sentences) - len(baseline.sentences)),
        "ingest_rougeL_f": float(ingest_rouge["rougeL_f"]),
        "ingest_replacement_char_count": count_replacement_chars(cand_text),
    }


def baseline_ingestion_metrics() -> dict[str, Any]:
    return {
        "ingest_exact_match": True,
        "ingest_char_len_ratio": 1.0,
        "ingest_sentence_count_delta": 0,
        "ingest_rougeL_f": 1.0,
        "ingest_replacement_char_count": 0,
    }


def make_format_factories(article: str) -> list[tuple[str, Callable[[], tuple[str, ProcessedInput]]]]:
    return [
        (BASELINE_FORMAT, lambda: ("inline", process_from_text(article))),
        ("file_txt", lambda: ("sample.txt", process_from_bytes("sample.txt", build_txt_bytes(article)))),
        ("file_docx", lambda: ("sample.docx", process_from_bytes("sample.docx", build_docx_bytes(article)))),
        ("file_pdf", lambda: ("sample.pdf", process_from_bytes("sample.pdf", build_pdf_bytes(article)))),
    ]


def evaluate_article_all_formats(
    article: str,
    reference: str,
    *,
    engine: str,
    max_sentences: int,
    include_latency: bool = True,
) -> pd.DataFrame:
    """
    Single-article experiment: extraction fidelity + summary ROUGE vs gold for every format.
    Intended for notebook inspection (not batch n=200).
    """
    evaluator = Evaluator(use_stemmer=False)
    baseline_processed: ProcessedInput | None = None
    baseline_rouge_l: float | None = None
    rows: list[dict[str, Any]] = []

    for label, factory in make_format_factories(article):
        t0 = time.perf_counter() if include_latency else 0.0
        _fname, processed = factory()
        ingest_lat = (time.perf_counter() - t0) if include_latency else None

        if label == BASELINE_FORMAT:
            baseline_processed = processed
            ingest = baseline_ingestion_metrics()
        else:
            assert baseline_processed is not None
            ingest = compute_ingestion_fidelity(baseline_processed, processed, evaluator=evaluator)

        t1 = time.perf_counter()
        pred = _predict_summary(processed, engine=engine, max_sentences=max_sentences)
        sum_lat = time.perf_counter() - t1
        bundle = evaluator.evaluate_one(
            source_text=processed.cleaned_text,
            reference_summary=reference,
            predicted_summary=pred,
            latency_sec=sum_lat,
            extra={},
        )
        d = bundle.as_dict()
        rouge_l = float(d["rougeL_f"])
        if label == BASELINE_FORMAT:
            baseline_rouge_l = rouge_l
            delta = 0.0
        elif baseline_rouge_l is not None:
            delta = rouge_l - baseline_rouge_l
        else:
            delta = None

        meta = processed.metadata or {}
        rows.append(
            {
                "format": label,
                "loader": FORMAT_LOADER_LABELS.get(label, label),
                "source_type": processed.source_type,
                "cleaned_text": processed.cleaned_text,
                "raw_char_length": meta.get("raw_char_length"),
                "cleaned_char_length": len(processed.cleaned_text),
                "sentence_count": len(processed.sentences),
                "ingest_latency_sec": ingest_lat,
                "summarize_latency_sec": sum_lat,
                **ingest,
                "rouge1_f": d["rouge1_f"],
                "rouge2_f": d["rouge2_f"],
                "rougeL_f": rouge_l,
                "rougeL_delta_vs_baseline": delta,
                "compression_ratio": d["compression_ratio"],
                "repetition_rate": d["repetition_rate"],
                "predicted_summary": pred,
                "reference_summary": reference,
            }
        )

    return pd.DataFrame(rows)


def process_article_all_formats(
    article: str,
    *,
    include_latency: bool = True,
) -> dict[str, dict[str, Any]]:
    """Run ingest pipeline for all formats on one article (notebook walkthrough)."""
    baseline_processed: ProcessedInput | None = None
    evaluator = Evaluator(use_stemmer=False)
    out: dict[str, dict[str, Any]] = {}

    for label, factory in make_format_factories(article):
        t0 = time.perf_counter() if include_latency else 0.0
        _fname, processed = factory()
        ingest_lat = (time.perf_counter() - t0) if include_latency else None

        if label == BASELINE_FORMAT:
            baseline_processed = processed
            ingest = baseline_ingestion_metrics()
        else:
            assert baseline_processed is not None
            ingest = compute_ingestion_fidelity(baseline_processed, processed, evaluator=evaluator)

        meta = processed.metadata or {}
        out[label] = {
            "source_type": processed.source_type,
            "cleaned_text": processed.cleaned_text,
            "sentence_count": len(processed.sentences),
            "sentences_preview": processed.sentences[:3],
            "raw_char_length": meta.get("raw_char_length"),
            "cleaned_char_length": meta.get("cleaned_char_length"),
            "normalized_char_length": meta.get("normalized_char_length"),
            "ingest_latency_sec": ingest_lat,
            **ingest,
        }
    return out


def _predict_summary(processed: ProcessedInput, *, engine: str, max_sentences: int) -> str:
    selected, _ = summarize_processed_input_raw(
        processed,
        max_sentences=max_sentences,
        ratio=None,
        engine_name=engine,
    )
    return " ".join(s.strip() for s in selected if s.strip())


def _error_row_fields() -> dict[str, Any]:
    return {
        "status": "error",
        "rouge1_f": None,
        "rouge2_f": None,
        "rougeL_f": None,
        "rougeL_delta_vs_baseline": None,
        "compression_ratio": None,
        "repetition_rate": None,
        "cleaned_char_len": None,
        "sentence_count": None,
        "ingest_latency_sec": None,
        "summarize_latency_sec": None,
        "ingest_exact_match": None,
        "ingest_char_len_ratio": None,
        "ingest_sentence_count_delta": None,
        "ingest_rougeL_f": None,
        "ingest_replacement_char_count": None,
        "predicted_summary": "",
    }


def _run_one_format(
    *,
    label: str,
    processed: ProcessedInput,
    reference: str,
    evaluator: Evaluator,
    engine: str,
    max_sentences: int,
    ingest_latency: float,
    ingestion: dict[str, Any],
    baseline_rougeL: float | None,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    pred = _predict_summary(processed, engine=engine, max_sentences=max_sentences)
    sum_lat = time.perf_counter() - t0
    bundle = evaluator.evaluate_one(
        source_text=processed.cleaned_text,
        reference_summary=reference,
        predicted_summary=pred,
        latency_sec=sum_lat,
        extra={},
    )
    d = bundle.as_dict()
    rouge_l = float(d["rougeL_f"])
    if label == BASELINE_FORMAT:
        delta = 0.0
    elif baseline_rougeL is not None:
        delta = rouge_l - baseline_rougeL
    else:
        delta = None

    return {
        "format": label,
        "status": "ok",
        "error": "",
        "rouge1_f": d["rouge1_f"],
        "rouge2_f": d["rouge2_f"],
        "rougeL_f": rouge_l,
        "rougeL_delta_vs_baseline": delta,
        "compression_ratio": d["compression_ratio"],
        "repetition_rate": d["repetition_rate"],
        "cleaned_char_len": len(processed.cleaned_text),
        "sentence_count": len(processed.sentences),
        "ingest_latency_sec": ingest_latency,
        "summarize_latency_sec": sum_lat,
        "predicted_summary": pred,
        **ingestion,
    }


def _aggregate_by_format(out_df: pd.DataFrame) -> dict[str, dict[str, Any]]:
    ok = out_df["status"] == "ok"
    by_format: dict[str, dict[str, Any]] = {}

    for fmt in out_df["format"].unique():
        sub = out_df[(out_df["format"] == fmt) & ok]
        if sub.empty:
            by_format[str(fmt)] = {"n_ok": 0}
            continue

        agg: dict[str, Any] = {
            "n_ok": int(len(sub)),
            "mean_rougeL_f": float(sub["rougeL_f"].mean()),
            "mean_rouge1_f": float(sub["rouge1_f"].mean()),
            "mean_rouge2_f": float(sub["rouge2_f"].mean()),
            "mean_compression_ratio": float(sub["compression_ratio"].mean()),
            "mean_repetition_rate": float(sub["repetition_rate"].mean()),
            "mean_cleaned_char_len": float(sub["cleaned_char_len"].mean()),
            "mean_ingest_rougeL_f": float(sub["ingest_rougeL_f"].mean()),
            "pct_exact_match": float(sub["ingest_exact_match"].mean() * 100.0),
            "mean_ingest_char_len_ratio": float(sub["ingest_char_len_ratio"].mean()),
            "mean_ingest_replacement_char_count": float(sub["ingest_replacement_char_count"].mean()),
        }
        if fmt != BASELINE_FORMAT and "rougeL_delta_vs_baseline" in sub.columns:
            delta = sub["rougeL_delta_vs_baseline"].dropna()
            if not delta.empty:
                agg["mean_rougeL_delta_vs_baseline"] = float(delta.mean())
        by_format[str(fmt)] = agg

    return by_format


def run_multiformat_eval(
    *,
    n: int,
    engine: str,
    max_sentences: int,
    seed: int,
    protocol_version: str,
    target_split: str,
    article_char_threshold: int | None,
    warmup_engine: bool,
    script_path: str = "scripts/eval_multiformat_vietnews_file_formats.py",
) -> tuple[pd.DataFrame, dict[str, Any]]:
    processed_dir = ROOT / "data" / "processed" / "vietnews"
    df, manifest = load_split(processed_dir, target_split, protocol_version)
    subset_df, manifest_protocol, manifest_path, split_path = load_benchmark_validation_subset(
        df,
        manifest=manifest,
        processed_dir=processed_dir,
        target_split=target_split,
        seed=seed,
        subset_limit=n,
        article_char_threshold=article_char_threshold,
    )

    evaluator = Evaluator(use_stemmer=False)
    rows: list[dict] = []
    engine_warmup_done = False

    for row in subset_df.to_dict(orient="records"):
        article = str(row.get("article", ""))
        reference = str(row.get("reference_summary", ""))
        guid = row.get("guid", "")

        base = {"guid": guid, "article_char_len": len(article), "summary_engine": engine}

        if not article.strip() or not reference.strip():
            rows.append({**base, "format": "skipped", "status": "skipped_empty", "error": ""})
            continue

        if warmup_engine and not engine_warmup_done:
            pw = process_from_text(article)
            summarize_processed_input_raw(pw, max_sentences=max_sentences, ratio=None, engine_name=engine)
            engine_warmup_done = True

        baseline_processed: ProcessedInput | None = None
        baseline_rougeL: float | None = None

        for label, factory in make_format_factories(article):
            row_out = {**base}
            try:
                t0 = time.perf_counter()
                _fname, processed = factory()
                ingest_lat = time.perf_counter() - t0

                if label == BASELINE_FORMAT:
                    baseline_processed = processed
                    ingestion = baseline_ingestion_metrics()
                else:
                    if baseline_processed is None:
                        baseline_processed = process_from_text(article)
                    ingestion = compute_ingestion_fidelity(
                        baseline_processed,
                        processed,
                        evaluator=evaluator,
                    )

                metrics = _run_one_format(
                    label=label,
                    processed=processed,
                    reference=reference,
                    evaluator=evaluator,
                    engine=engine,
                    max_sentences=max_sentences,
                    ingest_latency=ingest_lat,
                    ingestion=ingestion,
                    baseline_rougeL=baseline_rougeL,
                )
                if label == BASELINE_FORMAT:
                    baseline_rougeL = float(metrics["rougeL_f"])
                row_out.update(metrics)
            except (
                SummaryEngineNotReadyError,
                InputValidationError,
                InputLoadError,
                ValueError,
                OSError,
            ) as exc:
                row_out.update({"format": label, "error": str(exc), **_error_row_fields()})
            except Exception as exc:  # pragma: no cover
                row_out.update(
                    {
                        "format": label,
                        "error": f"{type(exc).__name__}: {exc}",
                        **_error_row_fields(),
                    }
                )
            rows.append(row_out)

    out_df = pd.DataFrame(rows)
    ok = out_df["status"] == "ok"

    report: dict[str, Any] = {
        "report_schema": REPORT_SCHEMA_V2,
        "script": script_path,
        "protocol_version": manifest_protocol,
        "target_split": target_split,
        "manifest_path": str(manifest_path),
        "split_path": str(split_path),
        "n_requested": n,
        "seed": seed,
        "engine": engine,
        "max_sentences": max_sentences,
        "article_char_threshold": article_char_threshold,
        "subset_rows": int(len(subset_df)),
        "by_format": _aggregate_by_format(out_df),
        "pdf_encoding_note": PDF_ENCODING_NOTE,
        "rows_total": int(len(out_df)),
        "rows_ok": int(ok.sum()),
        "rows_error": int((out_df["status"] == "error").sum()),
    }

    return out_df, report


def export_vietnews_article_files(
    guid: str,
    out_dir: str | Path,
    *,
    prefix: str | None = None,
) -> dict[str, Path]:
    """Write synthetic .txt / .docx / .pdf from VietNews article (same as eval script)."""
    record = load_vietnews_record_by_guid(guid)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stem = prefix or str(guid)
    paths = {
        "txt": out / f"{stem}.txt",
        "docx": out / f"{stem}.docx",
        "pdf": out / f"{stem}.pdf",
    }
    paths["txt"].write_bytes(build_txt_bytes(record["article"]))
    paths["docx"].write_bytes(build_docx_bytes(record["article"]))
    paths["pdf"].write_bytes(build_pdf_bytes(record["article"]))
    return paths


def load_vietnews_record_by_guid(
    guid: str,
    *,
    target_split: str = "validation",
    protocol_version: str = "phase0_v2",
) -> dict[str, Any]:
    """Load article + gold reference_summary for one VietNews guid."""
    processed_dir = ROOT / "data" / "processed" / "vietnews"
    df, _manifest = load_split(processed_dir, target_split, protocol_version)
    matches = df[df["guid"].astype(str) == str(guid)]
    if matches.empty:
        raise ValueError(
            f"guid {guid!r} not found in split {target_split!r} "
            f"(protocol {protocol_version!r})."
        )
    row = matches.iloc[0]
    return {
        "guid": row["guid"],
        "article": str(row["article"]),
        "reference_summary": str(row["reference_summary"]),
    }


def evaluate_real_file_for_guid(
    guid: str,
    file_path: str | Path,
    *,
    engine: str = "textrank",
    max_sentences: int = 2,
    target_split: str = "validation",
    protocol_version: str = "phase0_v2",
) -> dict[str, Any]:
    """
    Evaluate a real file on disk against VietNews gold for the same guid.

    Compares:
      - text_baseline (process_from_text(article))
      - real_file (process_from_bytes(file_path))

    Returns extraction fidelity + summary ROUGE for both branches.
    """
    record = load_vietnews_record_by_guid(
        guid,
        target_split=target_split,
        protocol_version=protocol_version,
    )
    article = record["article"]
    gold = record["reference_summary"]
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    evaluator = Evaluator(use_stemmer=False)

    baseline = process_from_text(article)
    t0 = time.perf_counter()
    real = process_from_bytes(path.name, path.read_bytes())
    ingest_lat = time.perf_counter() - t0
    ingestion = compute_ingestion_fidelity(baseline, real, evaluator=evaluator)

    t1 = time.perf_counter()
    baseline_pred = _predict_summary(baseline, engine=engine, max_sentences=max_sentences)
    baseline_sum_lat = time.perf_counter() - t1
    baseline_bundle = evaluator.evaluate_one(
        source_text=baseline.cleaned_text,
        reference_summary=gold,
        predicted_summary=baseline_pred,
        latency_sec=baseline_sum_lat,
        extra={},
    )
    bd = baseline_bundle.as_dict()

    t2 = time.perf_counter()
    real_pred = _predict_summary(real, engine=engine, max_sentences=max_sentences)
    real_sum_lat = time.perf_counter() - t2
    real_bundle = evaluator.evaluate_one(
        source_text=real.cleaned_text,
        reference_summary=gold,
        predicted_summary=real_pred,
        latency_sec=real_sum_lat,
        extra={},
    )
    rd = real_bundle.as_dict()
    baseline_rouge_l = float(bd["rougeL_f"])
    real_rouge_l = float(rd["rougeL_f"])

    return {
        "guid": guid,
        "file_path": str(path.resolve()),
        "file_name": path.name,
        "source_type": real.source_type,
        "engine": engine,
        "max_sentences": max_sentences,
        "article_char_len": len(article),
        "gold_char_len": len(gold),
        "ingest_latency_sec": ingest_lat,
        **ingestion,
        "baseline_cleaned_char_len": len(baseline.cleaned_text),
        "real_cleaned_char_len": len(real.cleaned_text),
        "baseline_sentence_count": len(baseline.sentences),
        "real_sentence_count": len(real.sentences),
        "baseline_cleaned_text": baseline.cleaned_text,
        "real_cleaned_text": real.cleaned_text,
        "baseline_predicted_summary": baseline_pred,
        "real_predicted_summary": real_pred,
        "reference_summary": gold,
        "baseline_rouge1_f": bd["rouge1_f"],
        "baseline_rouge2_f": bd["rouge2_f"],
        "baseline_rougeL_f": baseline_rouge_l,
        "real_rouge1_f": rd["rouge1_f"],
        "real_rouge2_f": rd["rouge2_f"],
        "real_rougeL_f": real_rouge_l,
        "rougeL_delta_real_vs_baseline_summary": real_rouge_l - baseline_rouge_l,
        "baseline_compression_ratio": bd["compression_ratio"],
        "real_compression_ratio": rd["compression_ratio"],
        "baseline_repetition_rate": bd["repetition_rate"],
        "real_repetition_rate": rd["repetition_rate"],
    }


def display_real_file_evaluation(result: dict[str, Any], *, preview_chars: int = 600) -> None:
    """Pretty-print evaluate_real_file_for_guid output in a notebook."""
    _display_markdown(
        f"### Real file `{result.get('file_name')}` — guid `{result.get('guid')}`\n"
        f"- Path: `{result.get('file_path')}`\n"
        f"- Source type: `{result.get('source_type')}` | Engine: `{result.get('engine')}` "
        f"| top_k: `{result.get('max_sentences')}`"
    )

    summary_rows = [
        {
            "branch": "text_baseline (article in RAM)",
            "cleaned_chars": result.get("baseline_cleaned_char_len"),
            "sentences": result.get("baseline_sentence_count"),
            "rouge1_f": result.get("baseline_rouge1_f"),
            "rouge2_f": result.get("baseline_rouge2_f"),
            "rougeL_f": result.get("baseline_rougeL_f"),
        },
        {
            "branch": f"real_file ({result.get('file_name')})",
            "cleaned_chars": result.get("real_cleaned_char_len"),
            "sentences": result.get("real_sentence_count"),
            "rouge1_f": result.get("real_rouge1_f"),
            "rouge2_f": result.get("real_rouge2_f"),
            "rougeL_f": result.get("real_rougeL_f"),
        },
    ]
    _display(pd.DataFrame(summary_rows))

    _display_markdown("#### Ingestion (real file vs text baseline)")
    _display(
        pd.DataFrame(
            [
                {
                    "ingest_exact_match": result.get("ingest_exact_match"),
                    "ingest_char_len_ratio": result.get("ingest_char_len_ratio"),
                    "ingest_sentence_count_delta": result.get("ingest_sentence_count_delta"),
                    "ingest_rougeL_f": result.get("ingest_rougeL_f"),
                    "ingest_replacement_char_count": result.get("ingest_replacement_char_count"),
                    "ingest_latency_sec": result.get("ingest_latency_sec"),
                }
            ]
        )
    )

    if not result.get("ingest_exact_match"):
        display_ingestion_diff(
            str(result.get("baseline_cleaned_text", "")),
            str(result.get("real_cleaned_text", "")),
            format_label=str(result.get("file_name", "real_file")),
        )

    _display_markdown(
        f"#### Summary ROUGE vs gold — Δ real vs baseline = "
        f"{float(result.get('rougeL_delta_real_vs_baseline_summary', 0.0)):+.4f}"
    )

    gold = str(result.get("reference_summary", ""))
    for branch, pred_key in (
        ("baseline", "baseline_predicted_summary"),
        ("real_file", "real_predicted_summary"),
    ):
        pred = str(result.get(pred_key, ""))
        r_l = result.get("baseline_rougeL_f") if branch == "baseline" else result.get("real_rougeL_f")
        _display_markdown(f"**{branch}** — ROUGE-L={float(r_l):.4f}\n```\n{pred[:preview_chars]}\n```")

    if gold:
        _display_markdown(
            f"**Gold reference ({len(gold)} chars):**\n```\n{gold[:preview_chars]}\n```"
        )


def load_multiformat_subset(config: MultiformatEvalConfig) -> pd.DataFrame:
    processed_dir = ROOT / "data" / "processed" / "vietnews"
    df, manifest = load_split(processed_dir, config.target_split, config.protocol_version)
    subset_df, _, _, _ = load_benchmark_validation_subset(
        df,
        manifest=manifest,
        processed_dir=processed_dir,
        target_split=config.target_split,
        seed=config.seed,
        subset_limit=config.subset_limit,
        article_char_threshold=config.article_char_threshold,
    )
    return subset_df


def find_latest_multiformat_artifacts(analysis_dir: Path | None = None) -> tuple[Path | None, Path | None]:
    base = analysis_dir or (ROOT / "notebooks" / "results" / "analysis")
    if not base.exists():
        return None, None
    reports = sorted(base.glob("multiformat_vietnews_files_report_*.json"), reverse=True)
    if not reports:
        return None, None
    latest_report = reports[0]
    stem = latest_report.stem.replace("_report_", "_detail_")
    detail = base / f"{stem}.csv"
    if not detail.exists():
        detail = None
    return detail if detail and detail.exists() else None, latest_report


def display_extraction_table(experiment_df: pd.DataFrame) -> None:
    """Extraction / ingest metrics per file format (one article)."""
    cols = [
        "format",
        "loader",
        "source_type",
        "cleaned_char_length",
        "sentence_count",
        "ingest_exact_match",
        "ingest_char_len_ratio",
        "ingest_sentence_count_delta",
        "ingest_rougeL_f",
        "ingest_replacement_char_count",
        "ingest_latency_sec",
    ]
    show = [c for c in cols if c in experiment_df.columns]
    _display(experiment_df[show])


def display_extracted_text_per_format(
    experiment_df: pd.DataFrame,
    *,
    max_chars: int = 800,
) -> None:
    """Show cleaned text after each loader (what the summarizer actually sees)."""
    for _, row in experiment_df.iterrows():
        fmt = row["format"]
        loader = row.get("loader", "")
        text = ""
        if "cleaned_text" in experiment_df.columns:
            text = str(row.get("cleaned_text", ""))
        _display_markdown(f"### `{fmt}` — {loader}")
        if not text and fmt in FORMAT_LABELS:
            _display_markdown("_No cleaned_text column; re-run evaluate_article_all_formats._")
            continue
        if len(text) > max_chars:
            snippet = text[:max_chars] + "…"
        else:
            snippet = text
        _display_markdown(f"```\n{snippet}\n```")


def display_extracted_text_from_pipeline(
    pipeline_by_format: dict[str, dict[str, Any]],
    *,
    max_chars: int = 800,
) -> None:
    for fmt in FORMAT_LABELS:
        if fmt not in pipeline_by_format:
            continue
        data = pipeline_by_format[fmt]
        loader = FORMAT_LOADER_LABELS.get(fmt, fmt)
        text = data.get("cleaned_text", "")
        _display_markdown(
            f"### `{fmt}` — {loader}\n"
            f"- chars: {len(text)} | sentences: {data.get('sentence_count')} | "
            f"ingest ROUGE-L vs baseline: {data.get('ingest_rougeL_f'):.4f} | "
            f"exact match: {data.get('ingest_exact_match')}"
        )
        snippet = text[:max_chars] + ("…" if len(text) > max_chars else "")
        _display_markdown(f"```\n{snippet}\n```")


def display_summary_evaluation_table(experiment_df: pd.DataFrame) -> None:
    """Summary quality (ROUGE vs gold) per format."""
    cols = [
        "format",
        "rouge1_f",
        "rouge2_f",
        "rougeL_f",
        "rougeL_delta_vs_baseline",
        "compression_ratio",
        "repetition_rate",
        "summarize_latency_sec",
    ]
    show = [c for c in cols if c in experiment_df.columns]
    _display(experiment_df[show])


def display_summary_vs_gold(
    experiment_df: pd.DataFrame,
    *,
    max_chars: int = 600,
) -> None:
    """Side-by-side predicted summary and gold reference per format."""
    for _, row in experiment_df.iterrows():
        fmt = row["format"]
        pred = str(row.get("predicted_summary", ""))
        gold = str(row.get("reference_summary", ""))
        r_l = float(row.get("rougeL_f", 0.0))
        delta = row.get("rougeL_delta_vs_baseline")
        delta_str = ""
        if fmt != BASELINE_FORMAT and delta is not None and pd.notna(delta):
            delta_str = f" (Δ vs baseline={float(delta):+.4f})"
        _display_markdown(f"### Summary `{fmt}` — ROUGE-L={r_l:.4f}{delta_str}")
        _display_markdown(
            f"**Predicted ({len(pred)} chars):**\n```\n{pred[:max_chars]}"
            + ("…\n```" if len(pred) > max_chars else "\n```")
        )
        if fmt == BASELINE_FORMAT:
            _display_markdown(
                f"**Gold reference ({len(gold)} chars):**\n```\n{gold[:max_chars]}"
                + ("…\n```" if len(gold) > max_chars else "\n```")
            )


def display_pipeline_walkthrough(
    pipeline_by_format: dict[str, dict[str, Any]],
    *,
    preview_chars: int = 400,
) -> None:
    rows = []
    for fmt, data in pipeline_by_format.items():
        text = data.get("cleaned_text", "")
        preview = text[:preview_chars] + ("…" if len(text) > preview_chars else "")
        rows.append(
            {
                "format": fmt,
                "source_type": data.get("source_type"),
                "sentences": data.get("sentence_count"),
                "cleaned_chars": len(text),
                "ingest_rougeL_f": data.get("ingest_rougeL_f"),
                "exact_match": data.get("ingest_exact_match"),
                "replacement_chars": data.get("ingest_replacement_char_count"),
                "preview": preview,
            }
        )
    _display(pd.DataFrame(rows))


def display_ingestion_diff(
    baseline_text: str,
    candidate_text: str,
    *,
    format_label: str,
    context_lines: int = 2,
) -> None:
    diff = list(
        difflib.unified_diff(
            baseline_text.splitlines(),
            candidate_text.splitlines(),
            fromfile=BASELINE_FORMAT,
            tofile=format_label,
            lineterm="",
            n=context_lines,
        )
    )
    if not diff:
        _display_markdown(f"**{format_label}**: identical to baseline after ingest.")
        return
    body = "\n".join(diff[:80])
    if len(diff) > 80:
        body += "\n… (truncated)"
    _display_markdown(f"```diff\n{body}\n```")


def display_multiformat_summary_table(detail_df: pd.DataFrame) -> None:
    ok = detail_df[detail_df["status"] == "ok"].copy()
    if ok.empty:
        _display("No successful rows.")
        return
    cols = [
        "format",
        "n_ok",
        "mean_ingest_rougeL_f",
        "pct_exact_match",
        "mean_rougeL_f",
        "mean_rougeL_delta_vs_baseline",
    ]
    agg_rows = []
    for fmt, sub in ok.groupby("format"):
        row = {"format": fmt, "n_ok": len(sub)}
        row["mean_ingest_rougeL_f"] = sub["ingest_rougeL_f"].mean()
        row["pct_exact_match"] = sub["ingest_exact_match"].mean() * 100.0
        row["mean_rougeL_f"] = sub["rougeL_f"].mean()
        delta = sub["rougeL_delta_vs_baseline"].dropna()
        row["mean_rougeL_delta_vs_baseline"] = delta.mean() if not delta.empty else None
        agg_rows.append(row)
    summary = pd.DataFrame(agg_rows)
    show = [c for c in cols if c in summary.columns or c == "n_ok"]
    _display(summary[show] if show else summary)


def display_format_charts(detail_df: pd.DataFrame) -> None:
    ok = detail_df[detail_df["status"] == "ok"]
    if ok.empty:
        _display("No data to chart.")
        return
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        _display("matplotlib not installed; showing table only.")
        display_multiformat_summary_table(detail_df)
        return

    by_fmt = ok.groupby("format").agg(
        ingest_rougeL=("ingest_rougeL_f", "mean"),
        summary_rougeL=("rougeL_f", "mean"),
        summary_delta=("rougeL_delta_vs_baseline", "mean"),
    ).reset_index()

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    formats = by_fmt["format"].tolist()
    x = range(len(formats))

    axes[0].bar(x, by_fmt["ingest_rougeL"], color="steelblue")
    axes[0].set_xticks(list(x))
    axes[0].set_xticklabels(formats, rotation=20, ha="right")
    axes[0].set_ylim(0, 1.05)
    axes[0].set_title("Mean ingestion ROUGE-L vs baseline")
    axes[0].set_ylabel("ROUGE-L")

    axes[1].bar(x, by_fmt["summary_rougeL"], color="seagreen", label="summary ROUGE-L")
    if by_fmt["summary_delta"].notna().any():
        axes[1].bar(
            [i + 0.35 for i in x],
            by_fmt["summary_delta"].fillna(0),
            width=0.35,
            color="coral",
            label="delta vs baseline",
        )
    axes[1].set_xticks(list(x))
    axes[1].set_xticklabels(formats, rotation=20, ha="right")
    axes[1].set_title("Summary quality by format")
    axes[1].legend(fontsize=8)

    plt.tight_layout()
    _display(fig)
    plt.close(fig)
