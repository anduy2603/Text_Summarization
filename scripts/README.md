# Scripts Catalog

Thu muc `scripts/` khong phai la runtime chinh cho nguoi dung. Runtime chinh cua he thong la `frontend/` va `backend/`.

Vai tro cua `scripts/` la:

- chuan bi dataset;
- chay benchmark thuc nghiem;
- tao artifact CSV/JSON/MD cho luan van;
- kiem tra pipeline da dinh dang TXT/DOCX/PDF;
- cung cap demo co kiem soat cho file that aligned voi VietNews.

## Workflow Chinh Cho Do An

Day la workflow nen trinh bay trong luan van va README chinh.

1. Chuan bi dataset VietNews:

```powershell
python scripts/prepare_dataset.py
```

2. Kiem tra benchmark extractive Phase 1:

```powershell
python scripts/benchmark_extractive_engines.py
```

3. Kiem tra artifact official moi nhat:

```powershell
python scripts/print_latest_official_run.py
```

4. Danh gia da dinh dang TXT/DOCX/PDF cho cac engine extractive:

```powershell
python scripts/run_multiformat_extractive_suite.py --n 200 --max-sentences 2 --seed 42 --article-char-threshold 1200 --warmup-engine
```

Neu chi muon chay mot engine:

```powershell
python scripts/eval_multiformat_vietnews_file_formats.py --n 200 --engine textrank --max-sentences 2
```

## Official / Thesis Scripts

Nhung script nay nen duoc xem la pipeline chinh cua phan thuc nghiem.

| Script | Muc dich | Khi nao dung | Output chinh |
|---|---|---|---|
| `download_vietnews.py` | Tai raw VietNews tu Hugging Face | Chi dung khi chua co `data/raw/vietnews/*.jsonl` | `data/raw/vietnews/train.jsonl`, `validation.jsonl`, `test.jsonl`, `source_metadata.json` |
| `prepare_dataset.py` | Ap dung Phase 0 preprocessing va tao processed split | Dung truoc moi benchmark neu raw/protocol thay doi | `data/processed/vietnews/*.jsonl`, `dataset_manifest.json` |
| `benchmark_extractive_engines.py` | Benchmark TF-IDF, TextRank, PhoBERT-extractive tren cung subset VietNews | Script chinh cho Phase 1 extractive | `engine_compare_*`, `tfidf_*`, `textrank_*`, `phobert_*` trong `notebooks/results/official/validation/` |
| `benchmark_abstractive_vit5.py` | So sanh ViT5 (abstractive) vs TextRank tren cung subset | Sau Phase 1 extractive; can `transformers>=4.46,<5` va `VIT5_ALLOW_DOWNLOAD=1` lan dau | `vit5_vs_textrank_detail_*`, `vit5_vs_textrank_report_*` trong `notebooks/results/analysis/` |
| `eval_multiformat_vietnews_file_formats.py` | Danh gia mot engine tren `text_baseline`, TXT, DOCX, PDF | Khi can xem rieng mot engine tren multiformat | `multiformat_vietnews_files_detail_*`, `multiformat_vietnews_files_report_*` trong `notebooks/results/analysis/` |
| `run_multiformat_extractive_suite.py` | Chay multiformat cho nhieu engine voi cung protocol | Script chinh cho phan TXT/DOCX/PDF trong luan van | `multiformat_suite_*__manifest.json` va per-engine CSV/JSON |
| `print_latest_official_run.py` | Liet ke artifact official moi nhat va file con thieu | Dung truoc khi cite ket qua vao luan van | In duong dan artifact ra terminal |

## Demo / Case-Study Scripts

Nhung script nay huu ich khi can minh hoa upload file that, nhung khong phai pipeline benchmark chinh.

| Script | Muc dich | Khi nao dung | Ghi chu |
|---|---|---|---|
| `demos/eval_real_file_for_guid.py` | Danh gia mot file that tren dia voi mot `guid` VietNews | Khi file upload co noi dung aligned voi `article` cua `guid` | ROUGE chi hop le neu file that khop voi bai VietNews cung `guid` |
| `demos/eval_aligned_real_file_matrix.py` | Export mot `guid` thanh TXT/DOCX/PDF roi danh gia theo ma tran format x engine | Dung lam demo thesis cho "file that tren o dia" | Phu hop de minh hoa pipeline upload co kiem soat |

Vi du:

```powershell
python scripts/demos/eval_aligned_real_file_matrix.py --guid 6131 --samples-dir data/samples/multiformat
python scripts/demos/eval_real_file_for_guid.py --guid 6131 --file data/samples/multiformat/6131.docx
```

## Shared Modules

Nhung file nay khong nen chay truc tiep. Chung la helper duoc script va notebook import lai.

| Module | Muc dich |
|---|---|
| `shared/common.py` | Environment snapshot, git metadata, weighted-rank selection |
| `shared/io_dataset.py` | Load processed VietNews, chon validation subset theo protocol |
| `shared/engine_experiment.py` | Helper cho notebook engine: smoke test, benchmark, case table, interpretation |
| `shared/multiformat_experiment.py` | Tao TXT/DOCX/PDF synthetic, ingest fidelity, multiformat eval, real-file aligned eval |

## Legacy / Compatibility Scripts

Nhung script nay nen giu de tranh vo command cu, nhung khong nen xem la workflow chinh trong luan van.

| Script | Trang thai khuyen nghi | Ly do |
|---|---|---|
| `legacy/benchmark_tfidf_vs_textrank.py` | Legacy alias | Da re-export sang `benchmark_extractive_engines.py`; khong can cite trong luan van |
| `legacy/generate_official_validation_artifacts.py` | Legacy/specialized | Tao QA + TF-IDF artifact rieng; workflow hien tai nen dung `benchmark_extractive_engines.py` cho multi-engine |
| `legacy/generate_short_error_analysis.py` | Legacy helper | Benchmark chinh da co logic error analysis per-engine |
| `legacy/run_official_benchmark.py` | Compatibility runner | Gom QA/TF-IDF/compare, nhung de tranh nham lan nen uu tien command rieng ro rang o workflow chinh |

## Cach Trinh Bay Trong Do An

Nen mo ta ngan gon:

- `backend/` va `frontend/` la he thong cho nguoi dung upload tai lieu va nhan summary.
- `scripts/` la cong cu thuc nghiem de chung minh lua chon ky thuat.
- Dataset VietNews dung de danh gia vi co `reference_summary`.
- File upload bat ky cua user khong co gold summary nen khong dung ROUGE VietNews; chi dung metric khong gold va danh gia thu cong.
