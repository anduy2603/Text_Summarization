# Notebook Roles

The notebooks are thesis-facing experiment notebooks. Each engine notebook should stay short,
reproducible, and focused on interpretation.

## Current Structure

- `01_vietnews_data_check.ipynb`: dataset EDA and validation context.
- `02_tfidf_experiment.ipynb`: TF-IDF smoke test, benchmark, metric trend, and qualitative cases.
- `03_textrank_experiment.ipynb`: TextRank smoke test, benchmark, metric trend, and qualitative cases.
- `04_phobert_extractive.ipynb`: PhoBERT-extractive smoke test, benchmark, metric trend, and qualitative cases.
- `05_multiformat_pipeline.ipynb`: multi-format ingest walkthrough (TXT/DOCX/PDF), ingestion fidelity, smoke eval, and charts from official multiformat CSV.

## Multiformat: notebook vs script

| Artifact | Role |
|----------|------|
| `notebooks/05_multiformat_pipeline.ipynb` | See extracted text, diffs, and case studies; run `n=5` smoke only |
| `scripts/eval_multiformat_vietnews_file_formats.py` | Official batch eval (`n=200`), one `--engine`, writes `notebooks/results/analysis/multiformat_*` |
| `scripts/run_multiformat_extractive_suite.py` | Same protocol for **several** extractive engines (`tfidf`, `textrank`, `phobert-extractive`); writes one `multiformat_suite_*__manifest.json` plus per-engine CSV/JSON |
| `scripts/demos/eval_aligned_real_file_matrix.py` | Small **aligned** matrix: export `guid` → `.txt`/`.docx`/`.pdf` on disk, then ROUGE vs gold for each `(format, engine)` |
| `scripts/demos/eval_real_file_for_guid.py` | One real file + VietNews `guid` → ingestion + ROUGE vs gold |
| `scripts/shared/multiformat_experiment.py` | Shared builders, ingestion metrics, `evaluate_real_file_for_guid`, display helpers |
| [`docs/thesis_upload_to_summary_evaluation.md`](../docs/thesis_upload_to_summary_evaluation.md) | Thesis-facing: when ROUGE is valid (aligned) vs arbitrary upload; Phase 2 abstractive scope |

Do not run `n=200` inside the notebook; use the script in terminal for thesis artifacts. For **fair three-engine multiformat comparison**, use `run_multiformat_extractive_suite.py` with the same `n` / `seed` / `protocol` as the single-engine script (or run the single script three times and cite all timestamps in the thesis).

## Notebook Boundaries

Engine notebooks should:

- explain the engine and experiment setup;
- run one smoke test on a fixed VietNews sample;
- run the engine on the fixed validation subset;
- show ROUGE, compression ratio, repetition rate, and latency;
- select `top_k` through the shared weighted-rank method;
- collect good and bad cases for thesis analysis.

Engine notebooks should not:

- duplicate benchmark loops across engines;
- implement dataset-loading protocol details inline;
- export official benchmark artifacts;
- contain large reusable utilities.
- define local helper functions in notebook cells.

Reusable benchmark logic belongs in `scripts/shared/engine_experiment.py`. Official artifact generation
belongs in scripts such as `scripts/benchmark_extractive_engines.py`. Legacy artifact helpers live under
`scripts/legacy/` and should not be used as the main workflow.
