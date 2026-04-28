# Text_Summarization

## Phase 0 - Frozen Experiment Protocol

Phase 0 fixes dataset splits, preprocessing, output-length rules, metrics, and seeds so later methods stay comparable.

- **Protocol file:** `configs/phase0_protocol.yaml`
- **Current protocol version:** `phase0_v2`
- **Sentence splitting policy for Phase 0/1:** regex-only, to avoid environment-dependent drift from optional tokenizers
- **Raw VietNews:** `data/raw/vietnews/` (see `data/raw/vietnews/README.md`; large files stay gitignored)
- **Prepare processed JSONL + manifest:** `python scripts/prepare_dataset.py` (writes `data/processed/vietnews/` and `dataset_manifest.json`)
- **Download from Hugging Face (optional):** `python scripts/download_vietnews.py`
- **Metrics implementation:** `evaluation/evaluator.py` (ROUGE-1/2/L, latency, compression ratio, bigram repetition rate)
- **Notebook:** `notebooks/01_vietnews_data_check.ipynb`

## Phase 1 Baselines (Extractive)

This section tracks official artifact layouts for both extractive engines currently supported in backend:

- `tfidf`
- `textrank`

### Official Artifact Layout

- Official outputs: `notebooks/results/official/validation/`
- Legacy/superseded outputs: `notebooks/results/deprecated/`
- Reserved archive bucket: `notebooks/results/archive/`

### Current Benchmark Configuration

- TF-IDF notebook: `notebooks/02_tfidf_experiment.ipynb`
- TextRank benchmark script: `scripts/benchmark_tfidf_vs_textrank.py`
- Split: `validation`
- Protocol: `phase0_v2`
- Top-k candidates: `[2, 3, 4, 5]`
- Subset limit: `200`
- Article threshold: `article_char_len >= 1200`
- Report schemas:
  - TF-IDF: `tfidf_phase1_benchmark_v2`
  - TextRank: `textrank_phase1_benchmark_v1`

### Official Benchmark Outputs (Validation)

- Official benchmark directory: `notebooks/results/official/validation/`
- Expected TF-IDF artifact naming:
  - `tfidf_phase1_topk_summary_<timestamp>.csv`
  - `tfidf_phase1_topk_detail_<timestamp>.csv`
  - `tfidf_phase1_topk_report_<timestamp>.json`
  - `tfidf_phase1_error_analysis_<timestamp>.md`
- Expected TextRank artifact naming:
  - `textrank_phase1_topk_summary_<timestamp>.csv`
  - `textrank_phase1_topk_detail_<timestamp>.csv`
  - `textrank_phase1_topk_report_<timestamp>.json`
  - `textrank_phase1_error_analysis_<timestamp>.md`
- Expected engine comparison artifact naming:
  - `engine_compare_summary_<timestamp>.csv`
  - `engine_compare_detail_<timestamp>.csv`
  - `engine_compare_report_<timestamp>.json`
- Expected data QA artifact naming:
  - `vietnews_data_check_summary_validation_<timestamp>.json`
- To identify the latest official run, use the most recent timestamp shared by the summary/detail/report trio in `official/validation/`.
- Quick helper: `python scripts/print_latest_official_run.py`

### Benchmark Notes

- `recommended_top_k_by_weighted_rank = 2` (from report).
- Official `top_k` used in thesis reporting is locked to `2` (unless a new official rerun supersedes it).
- Latency label is `summarizer_core_latency_sec`.
- Latency scope is summarizer-core only (`summarize_with_tfidf`), excluding `process_from_text`.
- Weighted selection uses ROUGE-1/2/L, compression ratio, repetition rate, and latency.

## Evaluator Metrics

The canonical implementation is `evaluation/evaluator.py`:

- ROUGE: `rouge1_f`, `rouge2_f`, `rougeL_f`
- Compression: `compression_ratio = len(summary_chars) / len(source_chars)`
- Repetition: `repetition_rate` as bigram repetition by default (`n=2`)
- Latency: `latency_sec` in evaluator; benchmark notebook renames this field to `summarizer_core_latency_sec` for clarity

## Data QA Status

- Data QA notebook: `notebooks/01_vietnews_data_check.ipynb`
- Target split: `validation`
- Hard gate requires both:
  - schema/data pass conditions
  - `acceptable_for_benchmark = true` in protocol consistency
- If the gate fails, official QA JSON export is intentionally blocked.
