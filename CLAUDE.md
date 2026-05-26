# CLAUDE.md — Multi-format Vietnamese Document Summarization

> Hướng dẫn dành cho Claude Code khi làm việc với project này.
> Đọc file này trước khi thực hiện bất kỳ thay đổi nào.

---

## Tên đề tài

**Multi-format Vietnamese Document Summarization using Extractive and Abstractive NLP Methods**

Hệ thống cho phép người dùng upload tài liệu tiếng Việt đa định dạng (TXT, DOCX, PDF, URL) và tự động tóm tắt nội dung bằng nhiều phương pháp NLP khác nhau.

---

## Kiến trúc tổng quan

```
Text_Summarization/
├── backend/                    # FastAPI Python backend (nguồn chính)
│   ├── app/
│   │   ├── api/routes/         # HTTP endpoints (health, summarize)
│   │   ├── core/               # Config (pydantic-settings), Logger
│   │   ├── schemas/            # Pydantic request/response models
│   │   └── services/
│   │       ├── input/          # Pipeline xử lý đầu vào
│   │       │   ├── loaders/    # PDF (PyMuPDF), DOCX (python-docx), TXT, URL (BeautifulSoup)
│   │       │   ├── cleaner.py  # Làm sạch văn bản (ký tự đặc biệt, BOM, zero-width)
│   │       │   ├── normalizer.py  # NFC normalization
│   │       │   ├── sentence_splitter.py   # Tách câu tiếng Việt (regex-based)
│   │       │   └── sentence_candidates.py # Lọc câu cho tóm tắt
│   │       └── summarization/  # Các engine tóm tắt
│   │           ├── tfidf_summarizer.py       # Extractive: TF-IDF
│   │           ├── textrank_summarizer.py    # Extractive: TextRank + MMR + Position bias
│   │           ├── phobert_extractive.py     # Extractive: PhoBERT embeddings (vinai/phobert-base-v2)
│   │           ├── vit5_abstractive.py       # Abstractive: ViT5 (VietAI/vit5-base-vietnews-summarization)
│   │           ├── hybrid_summarizer.py      # Hybrid: TextRank preselect → ViT5 rewrite
│   │           ├── summary_service.py        # Registry & điều phối các engine
│   │           ├── length_policy.py          # Chính sách độ dài output theo tier tài liệu
│   │           ├── summary_quality.py        # Kiểm tra chất lượng ViT5 (mojibake, repetition)
│   │           └── formatter.py             # Build SummarizeResponse
│   └── tests/                  # Integration tests (pytest + httpx)
├── frontend/                   # React/Vite frontend (CHƯA HOÀN THIỆN)
├── evaluation/                 # Framework đánh giá ROUGE
│   ├── evaluator.py            # ROUGE-1/2/L, compression ratio, repetition rate
│   └── preprocess.py
├── scripts/                    # Benchmark, download dataset, analysis
│   ├── benchmark_extractive_engines.py
│   ├── benchmark_abstractive_vit5.py
│   ├── download_vietnews.py
│   └── prepare_dataset.py
├── data/
│   ├── raw/vietnews/           # Dataset VietNews (train/validation/test.jsonl)
│   └── processed/vietnews/
├── notebooks/results/          # Kết quả benchmark chính thức
│   └── official/validation/    # ROUGE scores các engine
└── configs/
    └── phase0_protocol.yaml    # Giao thức thực nghiệm (frozen)
```

---

## API Endpoints

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/engines` | Danh sách engine hỗ trợ |
| POST | `/api/v1/summarize` | Tóm tắt từ text thuần |
| POST | `/api/v1/summarize/file` | Tóm tắt từ file upload (TXT/DOCX/PDF) |
| POST | `/api/v1/summarize/url` | Tóm tắt từ URL |
| POST | `/api/v1/export/docx` | Xuất tóm tắt ra file DOCX |

**Query params chung cho summarize:** `engine`, `max_sentences` (1-20), `ratio` (0-1)

---

## Các Engine Tóm tắt

### Extractive
| Engine | File | Mô tả |
|--------|------|-------|
| `tfidf` | `tfidf_summarizer.py` | TF-IDF sentence scoring, pure Python |
| `textrank` | `textrank_summarizer.py` | PageRank trên similarity graph + MMR + position bias |
| `phobert-extractive` | `phobert_extractive.py` | PhoBERT sentence embeddings, cosine similarity vs doc vector |

### Abstractive
| Engine | File | Mô tả |
|--------|------|-------|
| `vit5` | `vit5_abstractive.py` | VietAI ViT5 seq2seq (fine-tuned trên VietNews) |

### Hybrid (default)
| Engine | File | Mô tả |
|--------|------|-------|
| `hybrid` | `hybrid_summarizer.py` | TextRank preselect → ViT5 lead rewrite → augment |

### Planned (chưa implement)
- `bartpho` — BARTpho abstractive
- `gemini` — Gemini API

---

## Môi trường & Chạy

### Backend
```bash
cd backend
pip install -e ".[dev]"
# Tải model weights lần đầu:
VIT5_ALLOW_DOWNLOAD=1 PHOBERT_ALLOW_DOWNLOAD=1 python -c "from app.services.summarization.vit5_abstractive import _get_vit5_runtime; _get_vit5_runtime()"
# Chạy server:
python run_api.py
# hoặc:
uvicorn app.main:app --reload --port 8000
```

### Tests
```bash
cd backend
pytest tests/ -v
# Chạy test cụ thể:
pytest tests/test_api_summarize.py -v
pytest tests/test_hybrid_summarizer.py -v
```

### Benchmark
```bash
# Extractive engines trên VietNews:
python scripts/benchmark_extractive_engines.py
# Abstractive ViT5:
python scripts/benchmark_abstractive_vit5.py
```

---

## Cấu hình (`.env`)

```env
APP_ENV=dev
LOG_LEVEL=INFO
API_HOST=127.0.0.1
API_PORT=8000

# Input
INPUT_MAX_FILE_BYTES=10485760    # 10MB
INPUT_ALLOWED_EXTENSIONS=.txt,.docx,.pdf

# Summarization
SUMMARY_ENGINE=hybrid
SUMMARY_MAX_SENTENCES=3

# Models
VIT5_MODEL_NAME=VietAI/vit5-base-vietnews-summarization
PRELOAD_MODELS=true

# Để download model lần đầu (sau đó bỏ):
# VIT5_ALLOW_DOWNLOAD=1
# PHOBERT_ALLOW_DOWNLOAD=1
```

---

## Dataset

- **VietNews**: Vietnamese news summarization dataset
- **Vị trí**: `data/raw/vietnews/{train,validation,test}.jsonl`
- **Tải về**: `python scripts/download_vietnews.py`
- **Chuẩn bị**: `python scripts/prepare_dataset.py`
- **Protocol**: `configs/phase0_protocol.yaml` — KHÔNG thay đổi khi đã chạy baseline

---

## Kết quả Benchmark Hiện tại

Xem: `notebooks/results/official/validation/engine_compare_report_20260427_212348.json`

Thứ tự chất lượng (theo ROUGE-L F1 trên VietNews validation):
1. `phobert-extractive` > `textrank` > `tfidf` (extractive)
2. `hybrid` (production default — TextRank + ViT5)
3. `vit5` (standalone abstractive, bị giới hạn 512 tokens input)

---

## Conventions & Quy ước Code

### Python
- Style: **Black** formatter, **isort** imports
- Type hints: Dùng `from __future__ import annotations` ở đầu file
- Union types: Dùng `X | Y` (Python 3.10+), không dùng `Optional[X]` hay `Union[X, Y]`
- Exceptions: Custom exception classes kế thừa từ `RuntimeError` hoặc `ValueError`
- Engine functions phải trả về `tuple[list[str], dict[str, Any]]` (extractive) hoặc `tuple[str, dict[str, Any]]` (abstractive)

### Thêm Engine Mới
1. Tạo file `backend/app/services/summarization/{name}_summarizer.py`
2. Implement function `summarize_with_{name}(sentences, max_sentences, ratio)` → `tuple[list[str], dict[str, Any]]`
3. Đăng ký trong `summary_service.py` vào registry tương ứng
4. Thêm vào `SUPPORTED_SUMMARY_ENGINES` trong `schemas/common.py`
5. Viết test trong `tests/`

### Input Pipeline
Thứ tự xử lý cố định: `raw bytes/text` → `loader` → `cleaner` → `normalizer` → `sentence_splitter` → `sentence_candidates` → `ProcessedInput`

Không thay đổi thứ tự này — ảnh hưởng đến reproducibility benchmark (phase0_protocol).

---

## Những điều KHÔNG làm

- **Không** thay đổi `configs/phase0_protocol.yaml` sau khi đã chạy baseline
- **Không** thay đổi logic trong `cleaner.py` / `normalizer.py` / `sentence_splitter.py` mà không re-run toàn bộ benchmark
- **Không** dùng `from __future__ import annotations` ở phần cuối file — phải ở dòng đầu
- **Không** mock model weights trong production tests — dùng `PhoBertEngineNotReadyError` / `Vit5EngineNotReadyError` pattern
- **Không** commit file model weights (`.bin`, `.safetensors`) vào git

---

## Lỗi thường gặp

### ViT5 không load
```
Vit5EngineNotReadyError: Unable to load ViT5 model
→ Set VIT5_ALLOW_DOWNLOAD=1 và chạy lại lần đầu để cache model
→ Hoặc: transformers>=5 không tương thích, dùng transformers>=4.46.3,<5.0.0
```

### PhoBERT không load
```
PhoBertEngineNotReadyError: pyvi not installed
→ pip install pyvi
→ Set PHOBERT_ALLOW_DOWNLOAD=1 lần đầu
```

### PDF không extract được text
```
InputLoadError: PDF không chứa văn bản có thể trích xuất
→ PDF là bản scan ảnh → cần OCR (chưa hỗ trợ)
→ Dùng TXT hoặc DOCX thay thế
```

---

## Lộ trình phát triển & Review chi tiết

Xem **`PROJECT_REVIEW.md`** để biết:
- Đánh giá tổng thể từng thành phần (Backend / Frontend / Evaluation / Deployment)
- Danh sách 18 vấn đề cần xử lý (🔴 bug / 🟡 code quality / 🟢 missing feature) kèm vị trí file cụ thể
- **5-Sprint Roadmap** với task list chi tiết
- Checklist hoàn thành đồ án

**Sprint hiện tại: Sprint 1 — Frontend Polish**
Ưu tiên xử lý trước khi sang Sprint 2 (Backend Refactor):
1. Xóa dead CSS trong `frontend/src/style.css` (~300 dòng chat UI cũ)
2. Dedup `ENGINE_LABELS` ra `frontend/src/constants.ts`
3. Wire up các nút placeholder (Filter, Grid view, Notifications, Thống kê)
4. Fix font load: chuyển Google Fonts sang `frontend/public/fonts/` (tránh phụ thuộc mạng)

Sau khi hoàn thành Sprint 1, chuyển sang **Sprint 2 — Backend Refactor** (xem PROJECT_REVIEW.md mục F).
