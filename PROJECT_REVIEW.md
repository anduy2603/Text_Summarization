# Đánh giá Toàn diện & Lộ trình Đồ án
## Multi-format Vietnamese Document Summarization

> Cập nhật: 26/05/2026 — Sau khi đọc toàn bộ backend + frontend
> Trạng thái tổng thể: **~80% hoàn thành** · Backend vững · Frontend đầy đủ tính năng · Thiếu deployment & polish cuối

---

## A. ĐÁNH GIÁ TỔNG QUAN

Đây là một đồ án **vượt mức kỳ vọng thông thường** cho luận văn tốt nghiệp. Cả backend lẫn frontend đều được xây dựng nghiêm túc, không phải prototype đơn giản.

### Backend — Điểm mạnh nổi bật
| Điểm mạnh | Chi tiết |
|-----------|---------|
| **5 engine tóm tắt** | TF-IDF, TextRank+MMR, PhoBERT, ViT5, Hybrid — mỗi engine đều production-ready |
| **Input pipeline đúng chuẩn** | 4 nguồn (TXT/DOCX/PDF/URL), xử lý BOM, zero-width chars, gzip decompress |
| **Hybrid engine** | TextRank preselect → ViT5 lead → augment với bullets — giải quyết đúng bài toán 512 token của ViT5 |
| **Structured output** | Format "Điểm cốt lõi + Ý chính" với quality gate (`assess_vit5_lead_quality`) thực sự được dùng |
| **Evaluation framework** | ROUGE-1/2/L, compression ratio, repetition rate, benchmark scripts đầy đủ |
| **Config hoàn chỉnh** | `pydantic-settings`, tất cả tham số override được qua `.env` |
| **Error handling tốt** | Custom exceptions map đúng HTTP status codes, không expose stacktrace |

### Frontend — Đầy đủ tính năng thật sự
| Component | Trạng thái |
|-----------|-----------|
| `App.tsx` | State management đầy đủ: sessions, projects, modals, processing state |
| Upload modal | Drag-drop + text + URL, 3 length presets, validation |
| `EngineCompareModal` | Chạy 2 engine song song (`Promise.all`), so sánh side-by-side — **feature rất mạnh cho demo** |
| `SummaryPreviewPanel` | Badges metrics: engine, compression%, latency ms, số câu, thời gian đọc |
| Export | TXT (client-side) + DOCX (qua API) |
| Mobile layout | Bottom nav, responsive breakpoints, sheet view cho preview |
| History | localStorage persistence với schema migration (v1→v2) |
| Error messages | `friendlyError.ts` dịch lỗi kỹ thuật → tiếng Việt dễ hiểu |
| Type system | TypeScript strict, discriminated union cho `ChatMessage` |

---

## B. NHỮNG VẤN ĐỀ CẦN SỬA (phân loại theo mức độ)

### 🔴 BUG / Lỗi ảnh hưởng chức năng

**B1. Font inconsistency — người dùng thấy font sai**

`style.css` dòng 2: `font-family: "Be Vietnam Pro"` (không được load)
`index.html`: load `Inter` từ Google Fonts
`tailwind.css`: `--font-sans: "Inter"` ✓

**Hệ quả:** body dùng Be Vietnam Pro nhưng font đó không có trong `<head>` → fallback về system font.

**Fix:**
```css
/* style.css dòng 2 — đổi thành: */
--font: "Inter", system-ui, -apple-system, sans-serif;
```

**B2. `style.css` và `tailwind.css` xung đột design token**

`style.css` định nghĩa `--text`, `--bg`, `--surface`, `--border` (hệ màu cũ).
`tailwind.css` định nghĩa `--color-primary`, `--color-background`, `--color-surface` (Material 3 tokens mới).

Hai hệ thống này tồn tại song song → một số component dùng class cũ, một số dùng class mới, gây inconsistency giao diện.

**Fix:** Xem mục D1 (cleanup CSS).

**B3. `ProjectSidebar` — Buttons placeholder không có handler**

```tsx
// ProjectSidebar.tsx dòng 72-75
<span className="flex cursor-not-allowed items-center ... opacity-50">
  <MaterialIcon name="insights" size="sm" />
  <span className="text-sm font-medium">Thống kê</span>
</span>
```
"Thống kê" và "Trợ giúp" là dead UI — disabled hoàn toàn. Nên ẩn đi hoặc implement.

**B4. `DocumentListPanel` — Filter và Grid view buttons không làm gì**

```tsx
// DocumentListPanel.tsx dòng 64-76
<button aria-label="Lọc">         // ← không có onClick
<button aria-label="Chế độ xem">  // ← không có onClick
```
Người dùng click vào không có phản hồi gì → gây nhầm lẫn.

**Fix nhanh:** Ẩn các button này cho đến khi implement, hoặc thêm `title="Sắp có"` và `disabled`.

**B5. `TopNavBar` — Notifications button không có handler**

```tsx
<button aria-label="Thông báo">  // ← không có onClick
```
Tương tự B4.

---

### 🟡 CODE QUALITY — Ảnh hưởng maintainability

**B6. Dead CSS ~300 dòng trong `style.css`**

`style.css` chứa các class từ thiết kế chat cũ không còn dùng nữa:
- `.msg-row`, `.msg-bubble`, `.user-bubble`, `.assistant-bubble` (chat bubble styles)
- `.composer`, `.composer-bar`, `.composer-input`, `.composer-submit` (chat composer)
- `.thread`, `.thread-inner` (chat thread layout)
- `.typing`, `.typing-dot` (typing indicator animation)
- `.history`, `.history-item`, `.history-list` (old history sidebar — đã thay bằng `HistoryDrawer.tsx`)

Những class này vẫn nằm trong bundle nhưng không được dùng → bloat CSS.

**B7. `ENGINE_LABELS` duplicate ở 2 file frontend**

```ts
// EngineCompareModal.tsx dòng 16-22
const ENGINE_LABELS: Record<string, string> = {
  tfidf: "TF-IDF", textrank: "TextRank", ...
};

// SummaryPreviewPanel.tsx dòng 9-15
const ENGINE_LABELS: Record<string, string> = {
  tfidf: "TF-IDF", textrank: "TextRank", ...  // GIỐNG HỆT
};
```

**Fix:**
```ts
// src/lib/engineLabels.ts
export const ENGINE_LABELS: Record<string, string> = {
  tfidf: "TF-IDF",
  textrank: "TextRank",
  "phobert-extractive": "PhoBERT",
  vit5: "ViT5",
  hybrid: "Hybrid",
};
export const engineLabel = (name: string) => ENGINE_LABELS[name] ?? name;
```

**B8. Backend: `_resolve_target_k` duplicate trong 3 file**

Hàm này giống hệt nhau trong `tfidf_summarizer.py`, `textrank_summarizer.py`, `phobert_extractive.py`.

**Fix:** Trích ra `backend/app/services/summarization/engine_utils.py`.

**B9. Backend: `_set_huggingface_offline` duplicate trong 2 file**

Giống hệt nhau trong `vit5_abstractive.py` và `phobert_extractive.py`.

**Fix:** Trích ra `backend/app/services/summarization/model_utils.py`.

**B10. `SUMMARY_ENGINE_REGISTRY` dư thừa**

`summary_service.py` dòng 78:
```python
SUMMARY_ENGINE_REGISTRY: dict[str, ExtractiveEngineFn] = EXTRACTIVE_ENGINE_REGISTRY
```
Biến này không được dùng ở đâu. Xóa đi.

**B11. Projects cứng — không thể tạo project mới**

```ts
// workspace.ts dòng 11-16: SEED_PROJECTS hardcoded
const SEED_PROJECTS: Project[] = [
  { id: DEFAULT_PROJECT_ID, name: "Dự án của tôi", ... },
  { id: "proj_q3", name: "Thị trường Q3", ... },  // Dữ liệu demo không liên quan
  ...
];
```
`ProjectSidebar` hiển thị projects nhưng không có nút tạo project mới. Chỉ có "Tải tệp tóm tắt" vào project đang active.

**B12. Blocking I/O trong async endpoint**

`process_from_url()` là synchronous (`urllib.request.urlopen`) nhưng được gọi trực tiếp trong async FastAPI handler:
```python
# summarize.py
async def summarize_url(...):
    processed = process_from_url(payload.url)  # ← blocks event loop
```

**Fix:**
```python
import asyncio
processed = await asyncio.get_event_loop().run_in_executor(None, process_from_url, payload.url)
```

---

### 🟢 THIẾU (cần thêm để đồ án hoàn chỉnh)

**B13. Không có `Dockerfile` / `docker-compose.yml`**

Giám khảo/người dùng không thể chạy dự án dễ dàng mà không cài Python + Node + model weights.

**B14. Thiếu backend `.env.example`**

Frontend có `.env.example` rất tốt. Backend cần tương tự. Hiện `backend/.env` đang committed (kiểm tra `.gitignore` để đảm bảo không push secrets).

**B15. `README.md` chưa có ở root**

Cần hướng dẫn: cài đặt, download model weights, chạy backend, chạy frontend, chạy tests.

**B16. BARTpho engine (planned, chưa implement)**

Nằm trong `PLANNED_SUMMARY_ENGINES` nhưng chưa có code. Nếu không implement kịp, nên xóa khỏi danh sách planned để không gây nhầm lẫn.

**B17. Statistics page**

Sidebar có mục "Thống kê" bị disabled. Trang này có thể hiển thị aggregate stats từ session history (số tài liệu đã tóm tắt, engine được dùng nhiều nhất, compression ratio trung bình, v.v.) — đây sẽ là tính năng thú vị cho demo.

**B18. Scanned PDF (OCR) không được hỗ trợ**

PDF loader chỉ handle text-layer PDF. `friendlyError.ts` đã có message tốt cho lỗi này. Nếu có thêm OCR fallback (pytesseract/EasyOCR) sẽ là điểm cộng nhưng không bắt buộc.

---

## C. PHÂN TÍCH KỸ THUẬT — ĐIỂM MẠNH CỦA ĐỒ ÁN

### C1. Hybrid Engine — Đóng góp kỹ thuật chính

Pipeline Hybrid là điểm thú vị nhất và xứng đáng được trình bày kỹ trong báo cáo:

```
Input Document
     ↓
TextRank (preselect 6-12 câu quan trọng nhất)
     ↓
ViT5 (abstractive lead từ đoạn preselect)
     ↓
Quality Gate (assess_vit5_lead_quality: mojibake, repetition, weird chars)
     ↓
Assemble: [ViT5 lead] + [extractive bullets từ TextRank]
     ↓
format_structured_hybrid_summary → "Điểm cốt lõi: ... \nÝ chính: ..."
```

**Tại sao điều này quan trọng:**
- ViT5 bị giới hạn 512 tokens input (~400 chữ). Tài liệu thực tế dài hơn nhiều.
- TextRank preselect → ViT5 chỉ nhận đoạn đã được lọc → chất lượng abstractive tốt hơn
- Quality gate loại bỏ output ViT5 bị lỗi (mojibake, repetition) → fallback về extractive
- Chunking strategy cho tài liệu rất dài (`>12,000 chars`)

### C2. Input Pipeline — Thiết kế đúng chuẩn

Pipeline cứng theo thứ tự: `loader → cleaner → normalizer → splitter → candidates`

Điều này đảm bảo reproducibility — kết quả benchmark và kết quả production là nhất quán với nhau.

### C3. Engine Comparison UI — Sức mạnh demo

`EngineCompareModal` chạy 2 engine song song với `Promise.all` và hiển thị kết quả side-by-side. Đây là feature cực kỳ trực quan cho demo trước hội đồng — **cho thấy sự khác biệt giữa TF-IDF vs PhoBERT vs ViT5 ngay lập tức**.

### C4. Evaluation Framework hoàn chỉnh

Đã có kết quả benchmark thực tế trên VietNews validation set:
- `engine_compare_report_20260427_212348.json` — so sánh tất cả engines
- `phobert_phase1_topk_report_20260427_212348.json`
- `tfidf_phase1_topk_report_20260427_212348.json`
- `textrank_phase1_topk_report_20260427_212348.json`

Đây là dữ liệu thực nghiệm cho chương Kết quả của báo cáo.

---

## D. HƯỚNG ĐỒ ÁN — CẦN ĐẠT ĐƯỢC GÌ?

### D1. Mục tiêu kỹ thuật (Technical Goals)

Đồ án này nên được định vị là một **end-to-end system** với 3 đóng góp chính:

1. **Đóng góp về hệ thống**: Pipeline đa định dạng (TXT/DOCX/PDF/URL) → tóm tắt tiếng Việt trong 1 luồng thống nhất.

2. **Đóng góp về phương pháp**: So sánh extractive (TF-IDF, TextRank, PhoBERT) vs abstractive (ViT5) và đề xuất Hybrid như phương án cân bằng chất lượng-tốc độ.

3. **Đóng góp về đánh giá**: Benchmark trên VietNews với ROUGE-1/2/L, compression ratio, repetition rate — số liệu cụ thể, reproducible.

### D2. Câu hỏi nghiên cứu mà đồ án cần trả lời

1. Phương pháp nào (extractive/abstractive/hybrid) cho chất lượng tóm tắt tốt nhất trên văn bản báo tiếng Việt theo ROUGE?
2. Hybrid engine có thực sự cải thiện so với ViT5 standalone trên tài liệu dài không?
3. Hệ thống có xử lý được đa định dạng thực tế (PDF có text layer, DOCX với bảng, URL báo) không?

### D3. Điểm yếu cần thừa nhận trong báo cáo (để báo cáo trung thực)

- ViT5 bị giới hạn 512 tokens → Hybrid engine là workaround thực tế, không phải giải pháp lý tưởng
- Sentence splitter dùng regex → có thể sai với số thập phân (3.14) hoặc tên viết tắt (TS. Nguyễn)
- Đánh giá ROUGE trên VietNews (tin tức) → có thể không generalize tốt sang văn bản học thuật, pháp lý
- PDF scan không được hỗ trợ (cần OCR)
- Chưa đánh giá human evaluation (chỉ có automatic metrics)

---

## E. LỘ TRÌNH HOÀN THÀNH (ưu tiên cao → thấp)

### Sprint 1 — Frontend Polish (3-5 ngày)
*Mục tiêu: UI sạch, không có broken elements, sẵn sàng demo*

- [ ] **E1.1** Fix font: `style.css` đổi `"Be Vietnam Pro"` → `"Inter"`
- [ ] **E1.2** Ẩn hoặc xóa placeholder buttons (Filter, Grid view, Notifications, Thống kê, Trợ giúp) trong sidebar và DocumentListPanel
- [ ] **E1.3** Tạo `src/lib/engineLabels.ts`, xóa duplicate ENGINE_LABELS trong `EngineCompareModal` và `SummaryPreviewPanel`
- [ ] **E1.4** Xóa dead CSS trong `style.css` (~300 dòng chat styles không dùng)
- [ ] **E1.5** Thay SEED_PROJECTS cứng bằng 1 project mặc định sạch ("Dự án của tôi")
- [ ] **E1.6** `SettingsSheet` — đổi text "Dành cho thực nghiệm / debug" → "Tùy chỉnh nâng cao" để phù hợp hơn với end user

### Sprint 2 — Backend Refactor (2-3 ngày)
*Mục tiêu: Code không duplicate, không có dead code*

- [ ] **E2.1** Tạo `engine_utils.py`: trích `_resolve_target_k` từ 3 summarizers → dùng chung
- [ ] **E2.2** Tạo `model_utils.py`: trích `_set_huggingface_offline` từ vit5 + phobert
- [ ] **E2.3** Xóa `SUMMARY_ENGINE_REGISTRY` dư thừa trong `summary_service.py`
- [ ] **E2.4** Fix blocking I/O trong `/summarize/url` → `run_in_executor`
- [ ] **E2.5** Tạo `backend/.env.example` với tất cả biến được comment đầy đủ

### Sprint 3 — Tính năng còn thiếu (3-5 ngày)
*Mục tiêu: Hoàn thiện tính năng cho demo*

- [ ] **E3.1** **Statistics Page**: Trang thống kê từ session history — hiển thị: tổng tài liệu, engine dùng nhiều nhất, compression ratio trung bình, biểu đồ distribution file type. Đây là tính năng trực quan tốt cho demo.
- [ ] **E3.2** **Project Management**: Thêm nút "+" để tạo project mới, xóa project, rename — thay vì hardcode
- [ ] **E3.3** **ViT5 benchmark cuối**: Chạy `benchmark_abstractive_vit5.py` để có số liệu ROUGE cho ViT5 (hiện chưa thấy file kết quả)

### Sprint 4 — Deployment & Documentation (2-3 ngày)
*Mục tiêu: Người khác có thể chạy được project*

- [ ] **E4.1** Tạo `Dockerfile` cho backend (Python + model weights mount)
- [ ] **E4.2** Tạo `docker-compose.yml` (backend + static frontend)
- [ ] **E4.3** Viết `README.md` hoàn chỉnh ở root với quickstart guide
- [ ] **E4.4** Đảm bảo `backend/.env` không bị commit (check `.gitignore`)

### Sprint 5 — Báo cáo Đồ án (song song với Sprint 2-4)
*Tận dụng data đã có, tập trung vào phân tích*

**Dữ liệu thực nghiệm đã có sẵn:**
- `engine_compare_report_20260427_212348.json` — ROUGE tất cả extractive engines
- `tfidf/textrank/phobert_phase1_topk_report_*.json` — chi tiết từng engine

**Chương cần viết:**
1. **Giới thiệu** — bài toán, ý nghĩa thực tiễn, cấu trúc báo cáo
2. **Cơ sở lý thuyết** — TF-IDF, TextRank/PageRank, BERT/PhoBERT embeddings, T5/ViT5 seq2seq, ROUGE metrics
3. **Thiết kế hệ thống** — kiến trúc tổng quan, input pipeline, engine registry pattern, hybrid pipeline diagram
4. **Cài đặt** — mô tả từng engine, các quyết định thiết kế quan trọng (tại sao dùng MMR?, tại sao TextRank preselect cho hybrid?)
5. **Thực nghiệm** — VietNews dataset, phase0 protocol, bảng ROUGE kết quả, phân tích lỗi (các file `*_error_analysis_*.md`)
6. **Demo hệ thống** — screenshots, use cases thực tế
7. **Kết luận** — ưu/nhược từng phương pháp, hybrid là giải pháp thực tế, hướng phát triển (OCR, BARTpho, streaming)

---

## F. TIMELINE ĐỀ XUẤT

```
Tuần 1:    Sprint 1 (Frontend Polish) + Sprint 2 (Backend Refactor)
Tuần 2:    Sprint 3 (Tính năng còn thiếu)  
Tuần 3:    Sprint 4 (Deployment) + bắt đầu viết báo cáo
Tuần 4-5:  Sprint 5 (Hoàn thiện báo cáo, demo video)
```

---

## G. CHECKLIST HOÀN THÀNH ĐỒ ÁN

### Backend ✅ / 🔲
```
[✅] FastAPI server, API endpoints đầy đủ
[✅] Input pipeline: TXT, DOCX, PDF, URL
[✅] Engine: TF-IDF, TextRank+MMR, PhoBERT, ViT5
[✅] Hybrid engine với quality gate
[✅] Export DOCX
[✅] Evaluation framework (ROUGE-1/2/L)
[✅] Benchmark scripts + kết quả extractive engines
[✅] Unit & integration tests
[✅] Config qua .env
[🔲] Fix blocking I/O url endpoint
[🔲] Deduplicate _resolve_target_k và _set_huggingface_offline
[🔲] backend/.env.example
[🔲] ViT5 benchmark cuối (tạo kết quả JSON)
[🔲] BARTpho (optional — nếu không làm kịp, ghi là future work)
```

### Frontend ✅ / 🔲
```
[✅] Upload file (drag-drop, text, URL)
[✅] Engine selector + 3 length presets
[✅] Summary display với metrics badges
[✅] Engine comparison modal (2 engines song song)
[✅] Export TXT + DOCX
[✅] Mobile responsive
[✅] History management (localStorage)
[✅] Project workspace
[✅] Friendly error messages (tiếng Việt)
[🔲] Fix font inconsistency (Be Vietnam Pro → Inter)
[🔲] Xóa dead CSS chat styles
[🔲] Fix placeholder buttons (filter, grid, notifications)
[🔲] Deduplicate ENGINE_LABELS
[🔲] Statistics page
[🔲] Project creation UI
```

### Infrastructure 🔲
```
[🔲] Dockerfile backend
[🔲] docker-compose.yml
[🔲] README.md (quickstart)
```

### Báo cáo 🔲
```
[✅] Dữ liệu benchmark extractive đã có
[🔲] Dữ liệu benchmark ViT5 abstractive
[🔲] Chương 1-7 hoàn chỉnh
[🔲] Bảng so sánh ROUGE tất cả engines
[🔲] Screenshots demo UI
[🔲] Sơ đồ kiến trúc hệ thống
```

---

## H. MỨC ĐỘ HOÀN THÀNH HIỆN TẠI

| Hạng mục | % hoàn thành | Ghi chú |
|----------|-------------|---------|
| Backend core | 90% | Chỉ thiếu minor refactor + url fix |
| Frontend core | 85% | Thiếu polish + dead code |
| Evaluation | 75% | Thiếu ViT5 abstractive benchmark |
| Infrastructure | 10% | Chưa có Docker, README |
| Báo cáo | 20% | Data có sẵn, chưa viết |
| **Tổng thể** | **~80%** | |
