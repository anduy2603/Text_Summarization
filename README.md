# Multi-format Vietnamese Document Summarization

Hệ thống tóm tắt tài liệu tiếng Việt đa định dạng (TXT, DOCX, PDF, URL) sử dụng các phương pháp NLP extractive và abstractive.

---

## Quickstart

### Option A — Docker (khuyến nghị, không cần cài conda hay model thủ công)

> **Yêu cầu:** Docker Desktop đã chạy, model weights đã cache trên máy (xem mục "Tải model lần đầu" bên dưới).

```bash
# Windows (PowerShell)
$env:HF_HOME = "$env:USERPROFILE\.cache\huggingface"
docker compose up --build

# Linux / Mac
docker compose up --build
```

Mở trình duyệt: **http://localhost:3000**

---

### Option B — Chạy thủ công (conda)

```bash
# 1. Tạo môi trường
conda env create -f backend/environment.yml
conda activate vietsum

# 2. Tải model weights lần đầu (chỉ cần làm một lần, ~1.3 GB)
cd backend
VIT5_ALLOW_DOWNLOAD=1 PHOBERT_ALLOW_DOWNLOAD=1 python -c "
from app.services.summarization.vit5_abstractive import _get_vit5_runtime
from app.services.summarization.phobert_extractive import _get_phobert_runtime
_get_vit5_runtime(); _get_phobert_runtime()
"

# 3. Chạy backend
python run_api.py
# → http://127.0.0.1:8000

# 4. Chạy frontend (terminal mới)
cd ../frontend
npm install
npm run dev
# → http://localhost:5173
```

---

## Tải model lần đầu

Hai model cần tải về HuggingFace cache (~1.3 GB tổng):

| Model | Kích thước | Env var để download |
|-------|-----------|---------------------|
| `VietAI/vit5-base-vietnews-summarization` | ~900 MB | `VIT5_ALLOW_DOWNLOAD=1` |
| `vinai/phobert-base-v2` | ~400 MB | `PHOBERT_ALLOW_DOWNLOAD=1` |

Sau khi cache xong, **không cần set env var nữa** — model sẽ load từ cache offline.

**Vị trí cache:**
- Windows: `%USERPROFILE%\.cache\huggingface\`
- Linux/Mac: `~/.cache/huggingface/`

---

## Cấu hình

Copy file mẫu và chỉnh sửa nếu cần:

```bash
cp backend/.env.example backend/.env
```

Biến quan trọng nhất:

```env
SUMMARY_ENGINE=hybrid          # default engine (tfidf/textrank/phobert-extractive/vit5/hybrid)
SUMMARY_MAX_SENTENCES=3        # số câu tóm tắt mặc định
PRELOAD_MODELS=true            # load ViT5+PhoBERT khi khởi động (tránh cold start)
```

---

## Kết quả Benchmark

**Dataset:** VietNews validation, n=200 bài, `max_sentences=2`, `seed=42`

| Engine | Loại | ROUGE-1 | ROUGE-2 | ROUGE-L | Latency | Repetition |
|--------|------|---------|---------|---------|---------|------------|
| TF-IDF | Extractive | 0.4773 | 0.1400 | 0.2701 | 0.6ms | 1.1% |
| TextRank | Extractive | 0.4981 | 0.2236 | 0.3205 | 2.3ms | 9.9% |
| PhoBERT | Extractive | 0.4759 | 0.2120 | 0.2955 | 644ms | 4.0% |
| ViT5 | Abstractive | **0.5845** | **0.2542** | **0.3670** | 3299ms | **1.6%** |
| Hybrid | Hybrid | 0.4541 | 0.2199 | 0.2901 | 2250ms | 2.6% |

**Ghi chú:** Hybrid có ROUGE thấp hơn ViT5 standalone vì ROUGE đo n-gram overlap — Hybrid paraphrase nội dung từ các câu được TextRank chọn lọc, trong khi ViT5 standalone đọc phần đầu bài (trùng nhiều hơn với reference). Hybrid giải quyết giới hạn 512-token của ViT5 cho tài liệu dài và có repetition thấp hơn TextRank 4×.

---

## API Endpoints

Server chạy tại `http://localhost:8000`:

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/engines` | Danh sách engine |
| POST | `/api/v1/summarize` | Tóm tắt từ text |
| POST | `/api/v1/summarize/file` | Upload TXT/DOCX/PDF |
| POST | `/api/v1/summarize/url` | Tóm tắt từ URL |
| POST | `/api/v1/export/docx` | Xuất DOCX |

**Query params chung:** `engine`, `max_sentences` (1–20), `ratio` (0–1)

---

## Chạy Tests

```bash
cd backend
pytest tests/ -v
```

---

## Chạy Benchmark

```bash
# Extractive engines (TF-IDF, TextRank, PhoBERT):
python scripts/benchmark_extractive_engines.py

# Hybrid engine + ViT5 + TextRank:
python scripts/benchmark_hybrid_engine.py --n 200 --max-sentences 2 --warmup-vit5

# In bảng so sánh 5 engine:
python scripts/print_unified_comparison_table.py
```

---

## Cấu trúc dự án

```
Text_Summarization/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/routes/         # HTTP endpoints
│   │   ├── services/
│   │   │   ├── input/          # Pipeline xử lý đầu vào
│   │   │   └── summarization/  # 5 engine tóm tắt
│   │   └── core/               # Config, Logger
│   ├── tests/                  # pytest integration tests
│   ├── environment.yml         # Conda env definition
│   ├── .env.example            # Template cấu hình
│   └── Dockerfile
├── frontend/                   # React/Vite frontend
│   └── Dockerfile
├── evaluation/                 # ROUGE evaluation framework
├── scripts/                    # Benchmark scripts
├── notebooks/                  # Experiment notebooks
│   └── results/official/       # Locked benchmark results
├── data/                       # VietNews dataset
├── configs/phase0_protocol.yaml
└── docker-compose.yml
```

---

## Phase 0 — Frozen Experiment Protocol

Phase 0 cố định dataset splits, preprocessing, output-length rules, metrics, và seeds để các phương pháp so sánh được với nhau.

- **Protocol file:** `configs/phase0_protocol.yaml`
- **Version hiện tại:** `phase0_v2`
- **Sentence splitting:** regex-only (không dùng tokenizer bên ngoài, đảm bảo reproducibility)
- **Processed data:** `data/processed/vietnews/` (tải về: `python scripts/download_vietnews.py`)
- **Metrics:** `evaluation/evaluator.py` — ROUGE-1/2/L, compression ratio, bigram repetition rate

### Artifact layout (Official)

Kết quả chính thức: `notebooks/results/official/validation/`

| Artifact | Mô tả |
|----------|-------|
| `engine_compare_report_<ts>.json` | Extractive benchmark (TF-IDF, TextRank, PhoBERT) |
| `vit5_vs_textrank_report_<ts>.json` | ViT5 vs TextRank (n=200) |
| `hybrid_engine_report_<ts>.json` | Hybrid + ViT5 + TextRank (n=200) |

Lấy kết quả mới nhất: `python scripts/print_latest_official_run.py`
