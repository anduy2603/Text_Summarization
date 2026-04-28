from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_DIR = ROOT / "notebooks" / "results" / "official" / "validation"

TFIDF_SUMMARY_RE = re.compile(r"^tfidf_phase1_topk_summary_(\d{8}_\d{6})\.csv$")
TFIDF_DETAIL_RE = re.compile(r"^tfidf_phase1_topk_detail_(\d{8}_\d{6})\.csv$")
TFIDF_REPORT_RE = re.compile(r"^tfidf_phase1_topk_report_(\d{8}_\d{6})\.json$")
TFIDF_ERROR_ANALYSIS_RE = re.compile(r"^tfidf_phase1_error_analysis_(\d{8}_\d{6})\.md$")
TEXTRANK_SUMMARY_RE = re.compile(r"^textrank_phase1_topk_summary_(\d{8}_\d{6})\.csv$")
TEXTRANK_DETAIL_RE = re.compile(r"^textrank_phase1_topk_detail_(\d{8}_\d{6})\.csv$")
TEXTRANK_REPORT_RE = re.compile(r"^textrank_phase1_topk_report_(\d{8}_\d{6})\.json$")
TEXTRANK_ERROR_ANALYSIS_RE = re.compile(r"^textrank_phase1_error_analysis_(\d{8}_\d{6})\.md$")
PHOBERT_SUMMARY_RE = re.compile(r"^phobert_phase1_topk_summary_(\d{8}_\d{6})\.csv$")
PHOBERT_DETAIL_RE = re.compile(r"^phobert_phase1_topk_detail_(\d{8}_\d{6})\.csv$")
PHOBERT_REPORT_RE = re.compile(r"^phobert_phase1_topk_report_(\d{8}_\d{6})\.json$")
PHOBERT_ERROR_ANALYSIS_RE = re.compile(r"^phobert_phase1_error_analysis_(\d{8}_\d{6})\.md$")
COMPARE_SUMMARY_RE = re.compile(r"^engine_compare_summary_(\d{8}_\d{6})\.csv$")
COMPARE_DETAIL_RE = re.compile(r"^engine_compare_detail_(\d{8}_\d{6})\.csv$")
COMPARE_REPORT_RE = re.compile(r"^engine_compare_report_(\d{8}_\d{6})\.json$")
QA_RE = re.compile(r"^vietnews_data_check_summary_validation_(\d{8}_\d{6})\.json$")


def collect_runs(official_dir: Path) -> dict[str, dict[str, Path]]:
    runs: dict[str, dict[str, Path]] = {}
    for path in official_dir.glob("*"):
        if not path.is_file():
            continue
        name = path.name
        for key, regex in (
            ("tfidf_summary", TFIDF_SUMMARY_RE),
            ("tfidf_detail", TFIDF_DETAIL_RE),
            ("tfidf_report", TFIDF_REPORT_RE),
            ("tfidf_error_analysis", TFIDF_ERROR_ANALYSIS_RE),
            ("textrank_summary", TEXTRANK_SUMMARY_RE),
            ("textrank_detail", TEXTRANK_DETAIL_RE),
            ("textrank_report", TEXTRANK_REPORT_RE),
            ("textrank_error_analysis", TEXTRANK_ERROR_ANALYSIS_RE),
            ("phobert_summary", PHOBERT_SUMMARY_RE),
            ("phobert_detail", PHOBERT_DETAIL_RE),
            ("phobert_report", PHOBERT_REPORT_RE),
            ("phobert_error_analysis", PHOBERT_ERROR_ANALYSIS_RE),
            ("compare_summary", COMPARE_SUMMARY_RE),
            ("compare_detail", COMPARE_DETAIL_RE),
            ("compare_report", COMPARE_REPORT_RE),
            ("qa_report", QA_RE),
        ):
            match = regex.match(name)
            if match:
                ts = match.group(1)
                runs.setdefault(ts, {})[key] = path
                break
    return runs


def main() -> None:
    if not OFFICIAL_DIR.exists():
        print(f"Official directory not found: {OFFICIAL_DIR}")
        return

    runs = collect_runs(OFFICIAL_DIR)
    if not runs:
        print(f"No official artifacts found in: {OFFICIAL_DIR}")
        return

    latest_ts = sorted(runs.keys())[-1]
    latest = runs[latest_ts]
    print(f"Latest observed timestamp: {latest_ts}")
    print(f"Official directory: {OFFICIAL_DIR}")
    print("")
    groups = {
        "tfidf": ("tfidf_summary", "tfidf_detail", "tfidf_report", "tfidf_error_analysis"),
        "textrank": ("textrank_summary", "textrank_detail", "textrank_report", "textrank_error_analysis"),
        "phobert": ("phobert_summary", "phobert_detail", "phobert_report", "phobert_error_analysis"),
        "engine_compare": ("compare_summary", "compare_detail", "compare_report"),
        "qa": ("qa_report",),
    }

    def latest_for_group(group_keys: tuple[str, ...]) -> tuple[str | None, dict[str, Path]]:
        candidate_ts = [ts for ts in runs if all(key in runs[ts] for key in group_keys)]
        if not candidate_ts:
            return None, {}
        ts = sorted(candidate_ts)[-1]
        return ts, runs[ts]

    print("Latest complete artifacts by group:")
    for label, keys in groups.items():
        ts, data = latest_for_group(keys)
        if ts is None:
            print(f"- {label}: MISSING")
            continue
        print(f"- {label}: {ts}")
        for key in keys:
            print(f"  - {key}: {data[key]}")

    print("")
    print("Artifacts at latest observed timestamp:")
    for key in (
        "tfidf_summary",
        "tfidf_detail",
        "tfidf_report",
        "tfidf_error_analysis",
        "textrank_summary",
        "textrank_detail",
        "textrank_report",
        "textrank_error_analysis",
        "phobert_summary",
        "phobert_detail",
        "phobert_report",
        "phobert_error_analysis",
        "compare_summary",
        "compare_detail",
        "compare_report",
        "qa_report",
    ):
        print(f"- {key}: {latest.get(key, 'MISSING')}")


if __name__ == "__main__":
    main()
