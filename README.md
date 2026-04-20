# Text_Summarization

## Phase 0 — Frozen experiment protocol

Phase 0 fixes dataset splits, preprocessing, output-length rules, metrics, and seeds so later methods stay comparable.

- **Protocol file:** `configs/phase0_protocol.yaml`
- **Raw VietNews:** `data/raw/vietnews/` (see `data/raw/vietnews/README.md`; large files stay gitignored)
- **Prepare processed JSONL + manifest:** `python scripts/prepare_dataset.py` (writes `data/processed/vietnews/` and `dataset_manifest.json`)
- **Download from Hugging Face (optional):** `python scripts/download_vietnews.py`
- **Metrics implementation:** `evaluation/evaluator.py` (ROUGE-1/2/L, latency, compression ratio, bigram repetition rate)
- **Notebook:** `notebooks/01_vietnews_data_check.ipynb`

## Phase 1 Baseline (Extractive TF-IDF)

This section records the completed Phase 1 baseline for the thesis pipeline.

### Dataset

- Source: VietNews (local file) `data/raw/vietnews/train.jsonl`
- Sample size used in this run: 300 articles
- Long-news subset for evaluation: 120 articles (`article_chars >= 1200`)
- Notebook: `notebooks/tfidf_experiments.ipynb`
- Artifacts:
  - `notebooks/results/tfidf_vietnews_eval_20260415_023920.json`
  - `notebooks/results/tfidf_phase1_topk_summary_20260415_023921.csv`
  - `notebooks/results/tfidf_phase1_topk_report_20260415_023921.json`

### Protocol

1. For each article:
   - Run preprocessing with backend pipeline: `process_from_text(article)`.
   - Generate extractive summary with TF-IDF sentence ranking.
2. Evaluate with ROUGE:
   - Metrics: `ROUGE-1`, `ROUGE-2`, `ROUGE-L`
   - Library: `rouge-score`
   - Config: `use_stemmer=False`
3. Hyperparameter sweep:
   - `top_k in [2, 3, 4, 5]`
   - Compare mean ROUGE scores across the same long-news subset.

### ROUGE Results (Mean on 120 long-news articles)

| top_k | ROUGE-1 | ROUGE-2 | ROUGE-L | avg_summary_chars |
|------:|--------:|--------:|--------:|------------------:|
| 2 | 0.4815 | 0.1384 | 0.2750 | 249.05 |
| 3 | 0.4677 | 0.1589 | 0.2703 | 390.75 |
| 4 | 0.4225 | 0.1733 | 0.2571 | 548.58 |
| 5 | 0.3743 | 0.1814 | 0.2398 | 700.61 |

### Best Hyperparameter

- Selected `best_top_k = 2` (from `tfidf_phase1_topk_report_20260415_023921.json`)
- Best mean scores:
  - `ROUGE-1 = 0.4815`
  - `ROUGE-2 = 0.1384`
  - `ROUGE-L = 0.2750`

### Conclusion (Phase 1)

- Phase 1 baseline extractive summarization is completed with a reproducible TF-IDF benchmark.
- The project now has:
  - a working backend extraction pipeline,
  - evaluation on real VietNews long articles,
  - and a selected baseline setting (`top_k=2`) for next-phase comparisons (TextRank, abstractive models).