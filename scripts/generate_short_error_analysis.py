from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(ROOT / "backend"))

from app.services.input import process_from_text
from app.services.summarization.tfidf_summarizer import summarize_with_tfidf


def generate_tfidf_error_analysis_from_report(report_path: Path) -> Path:
    report_payload = json.loads(report_path.read_text(encoding="utf-8"))
    ts = report_path.stem.split("_")[-2] + "_" + report_path.stem.split("_")[-1]
    official_dir = report_path.parent
    detail_path = Path(report_payload["detail_csv"])
    if not detail_path.exists():
        raise FileNotFoundError(f"Detail CSV not found: {detail_path}")

    top_k = int(report_payload.get("official_top_k", report_payload["recommended_top_k_by_weighted_rank"]))
    detail_df = pd.read_csv(detail_path)
    selected_df = detail_df[detail_df["top_k"] == top_k].copy()
    if selected_df.empty:
        raise RuntimeError(f"No rows found for top_k={top_k} in {detail_path}")

    worst = selected_df.nsmallest(
        5,
        "rougeL_f",
    )[
        [
            "guid",
            "rouge1_f",
            "rouge2_f",
            "rougeL_f",
            "compression_ratio",
            "repetition_rate",
            "article_char_len",
            "reference_char_len",
        ]
    ]
    best = selected_df.nlargest(
        5,
        "rougeL_f",
    )[
        [
            "guid",
            "rouge1_f",
            "rouge2_f",
            "rougeL_f",
            "compression_ratio",
            "repetition_rate",
            "article_char_len",
            "reference_char_len",
        ]
    ]

    out_path = official_dir / f"tfidf_phase1_error_analysis_{ts}.md"
    split_path = Path(report_payload["split_path"])
    split_df = pd.DataFrame(
        [json.loads(line) for line in split_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    )
    split_df["guid"] = split_df["guid"].astype(str)
    selected_df["guid"] = selected_df["guid"].astype(str)
    selected_guids = set(selected_df["guid"].tolist())
    split_df = split_df[split_df["guid"].isin(selected_guids)].copy()
    split_lookup = {str(row["guid"]): row for row in split_df.to_dict(orient="records")}

    failure_cases = []
    for _, row in selected_df.nsmallest(3, "rougeL_f").iterrows():
        guid = str(row["guid"])
        source = split_lookup.get(guid)
        if source is None:
            continue
        article = str(source.get("article", ""))
        reference = str(source.get("reference_summary", ""))
        processed = process_from_text(article)
        selected_sentences, _ = summarize_with_tfidf(
            processed.sentences,
            max_sentences=top_k,
            ratio=None,
        )
        predicted = " ".join(sentence.strip() for sentence in selected_sentences if sentence.strip())
        failure_cases.append(
            {
                "guid": guid,
                "rouge1_f": float(row["rouge1_f"]),
                "rouge2_f": float(row["rouge2_f"]),
                "rougeL_f": float(row["rougeL_f"]),
                "article_snippet": article[:500].replace("\n", " "),
                "reference_summary": reference[:500].replace("\n", " "),
                "predicted_summary": predicted[:500].replace("\n", " "),
            }
        )

    lines = [
        f"# TF-IDF Short Error Analysis ({ts})",
        "",
        f"- Selected official `top_k`: `{top_k}`",
        f"- Sample size: `{len(selected_df)}`",
        (
            "- Mean ROUGE-1/2/L: "
            f"`{selected_df['rouge1_f'].mean():.4f}` / "
            f"`{selected_df['rouge2_f'].mean():.4f}` / "
            f"`{selected_df['rougeL_f'].mean():.4f}`"
        ),
        (
            "- ROUGE-L spread (p10 -> p90): "
            f"`{selected_df['rougeL_f'].quantile(0.10):.4f}` -> "
            f"`{selected_df['rougeL_f'].quantile(0.90):.4f}`"
        ),
        f"- Mean compression ratio: `{selected_df['compression_ratio'].mean():.4f}`",
        f"- Mean repetition rate: `{selected_df['repetition_rate'].mean():.4f}`",
        "",
        "## Observations",
        (
            "- Worst samples mostly show very low overlap with references despite low repetition, "
            "suggesting content-selection misses rather than duplication errors."
        ),
        "- Higher-ROUGE samples tend to have moderate compression, indicating `top_k=2` balances compactness and overlap.",
        (
            "- ROUGE-2 remains lower than ROUGE-1/ROUGE-L, which is expected for an extractive baseline "
            "under strict bigram overlap scoring."
        ),
        "",
        "## Worst 5 by ROUGE-L",
        worst.to_markdown(index=False),
        "",
        "## Failure Cases (3 lowest ROUGE-L)",
    ]
    for idx, case in enumerate(failure_cases, start=1):
        lines.extend(
            [
                f"### Case {idx} - guid {case['guid']}",
                (
                    f"- ROUGE-1/2/L: `{case['rouge1_f']:.4f}` / "
                    f"`{case['rouge2_f']:.4f}` / `{case['rougeL_f']:.4f}`"
                ),
                f"- Article snippet: {case['article_snippet']}",
                f"- Reference summary: {case['reference_summary']}",
                f"- Predicted summary: {case['predicted_summary']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Best 5 by ROUGE-L",
            best.to_markdown(index=False),
            "",
        ]
    )
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def main() -> None:
    official_dir = ROOT / "notebooks" / "results" / "official" / "validation"
    report_files = sorted(official_dir.glob("tfidf_phase1_topk_report_*.json"))
    if not report_files:
        raise FileNotFoundError(f"No tfidf report found in {official_dir}")
    latest_report = report_files[-1]
    out_path = generate_tfidf_error_analysis_from_report(latest_report)
    print(out_path)


if __name__ == "__main__":
    main()
