# Đánh giá upload → tóm tắt (luận văn): điều kiện ROUGE và upload tùy ý

Tài liệu này cố định **phạm vi có thể bảo vệ** khi trình bày hệ thống tóm tắt tiếng Việt **đa định dạng** (TXT / DOCX / PDF). Nó bổ sung cho [`notebooks/README.md`](../notebooks/README.md) và các script `eval_multiformat_*`, `eval_real_file_for_guid`.

## 1. Hai chế độ đánh giá (bắt buộc phân biệt trong luận văn)

### 1.1. Có gold VietNews — ROUGE hợp lệ

**Điều kiện:** Bạn có `reference_summary` (gold) của **cùng một bài** VietNews và văn bản nguồn sau ingest **cùng ngữ cảnh** với `article` của bài đó.

**Cách thỏa mãn trong đồ án:**

- **Synthetic multiformat (chính thức, n=200):** Từ trường `article` trong dataset, tạo bytes TXT/DOCX/PDF trong bộ nhớ rồi đọc lại qua cùng pipeline API (`process_from_bytes`) — script [`scripts/eval_multiformat_vietnews_file_formats.py`](../scripts/eval_multiformat_vietnews_file_formats.py) hoặc suite [`scripts/run_multiformat_extractive_suite.py`](../scripts/run_multiformat_extractive_suite.py).
- **File trên đĩa + cùng `guid` (aligned):** File phải **khớp nội dung** `article` của `guid` đó (ví dụ export từ dataset). Khi đó `scripts/demos/eval_real_file_for_guid.py` hoặc notebook `05` §6 so summary với **cùng** `reference_summary` — ROUGE có nghĩa thống kê.

**Câu hỏi luận văn trả lời được:** Với cùng gold, định dạng file và engine extractive có làm lệch ROUGE hay độ trung thành ingest không?

### 1.2. Upload tùy ý (báo ngoài, PDF scan, nội dung khác VietNews)

**Không có** `reference_summary` VietNews tương ứng → **không** báo cáo ROUGE vs gold VietNews cho các file này (tránh sai phương pháp).

**Thay vào đó, trong luận văn có thể:**

- **Ingest:** độ dài, số câu, ký tự thay thế, (nếu có baseline nội bộ) so khớp gần đúng với một bản text tham chiếu do bạn chọn.
- **Chất lượng tóm tắt không gold:** ví dụ độ nén, tỷ lệ lặp, thời gian, **đánh giá người** (Likert: đầy đủ, mạch lạc, trung thành nguồn) trên mẫu nhỏ có kiểm soát.

**Câu hỏi luận văn trả lời được:** Pipeline upload có ổn định kỹ thuật và có thể minh họa qualitative; không nhầm với benchmark ROUGE trên VietNews.

## 2. Ba engine extractive và multiformat

Ba engine đăng ký trong API: `tfidf`, `textrank`, `phobert-extractive`. Để so sánh công bằng trên multiformat, cần **cùng** `n`, `seed`, `protocol`, `article_char_threshold`, `max_sentences` — chạy từng engine (script đơn lặp `--engine` hoặc một lần qua suite script) và khóa artifact CSV/JSON trong `notebooks/results/analysis/`.

## 3. Ma trận nhỏ “file thật aligned × engine” (minh họa)

Với vài `guid`, export `.txt` / `.docx` / `.pdf` từ `article` rồi chạy [`scripts/demos/eval_aligned_real_file_matrix.py`](../scripts/demos/eval_aligned_real_file_matrix.py) trên cả ba engine: minh chứng **upload file thật** (đường dẫn trên đĩa) + ROUGE vs gold **trong điều kiện aligned**.

## 4. Phase 2 (tùy chọn): abstractive — phạm vi tối thiểu

Chỉ xem xét sau khi Phase 1 (mục 1–3) đã **khóa** số liệu và còn thời gian / hội đồng yêu cầu **hai nhóm** phương pháp (extractive vs abstractive).

**Phạm vi gợi ý (tránh nở đề):**

- **Một** engine abstractive (ví dụ ViT5 hoặc mô hình seq2seq tiếng Việt có sẵn), cùng luồng ingest (`ProcessedInput` sau `process_from_bytes`).
- Benchmark **tối thiểu:** cùng subset VietNews (hoặc cùng protocol Phase 0) với TextRank (hoặc engine extractive tốt nhất của bạn); báo cáo ROUGE + thời gian + (nếu có) lỗi hallucination định tính ngắn.
- **Không** thay thế định nghĩa mục 1.1–1.2: upload tùy ý vẫn không tự động có ROUGE VietNews nếu không aligned.

Chi tiết triển khai mã abstractive nằm ngoài Phase 1 của kế hoạch hiện tại; có thể tham chiếu `PLANNED_SUMMARY_ENGINES` trong codebase khi bắt đầu.
