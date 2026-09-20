# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Vũ Quang Anh

**Nhóm:** gicungduoc
**Ngày:** 19/09/2026

> Báo cáo này ghi nhận kết quả chạy thực tế với corpus học phí đại học trong `data/hocbong_hocphi`, chiến lược `RecursiveChunker(chunk_size=700)`, và 5 query chung trong `benchmark.jsonl`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**

Cosine similarity cao, gần 1, nghĩa là hai vector có hướng gần nhau trong không gian embedding. Với embedding chất lượng tốt, điều này thường biểu thị hai văn bản có ý nghĩa hoặc ngữ cảnh tương tự, không phụ thuộc đáng kể vào độ dài văn bản.

**Ví dụ có độ tương tự CAO:**

- Câu A: Trí tuệ nhân tạo đang thay đổi cách con người làm việc.
- Câu B: AI đang thay đổi cách thức con người lao động.
- Tại sao tương đồng: Hai câu cùng diễn đạt tác động của AI lên công việc; “trí tuệ nhân tạo/AI” và “làm việc/lao động” là các cách diễn đạt gần nghĩa.

**Ví dụ có độ tương tự THẤP:**

- Câu A: Hệ thống máy tính đang tự động cập nhật phần mềm mã nguồn mở để tối ưu hiệu năng phần cứng.
- Câu B: Cá voi xanh bơi trong đại dương và ăn sinh vật phù du.
- Tại sao khác: Chủ đề, thực thể và ngữ cảnh của hai câu không liên quan nhau.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**

Cosine đo góc giữa hai vector nên tập trung vào hướng ngữ nghĩa, ít bị ảnh hưởng bởi độ lớn vector. Khoảng cách Euclid phụ thuộc cả độ dài vector, vì vậy dễ bị lệch khi cách tạo embedding làm chuẩn hoá không đồng nhất.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10.000 ký tự, `chunk_size=500`, `overlap=50`. Bao nhiêu chunks?**

Vị trí bắt đầu mỗi chunk cách nhau `500 - 50 = 450` ký tự. Số chunk là:

```text
ceil((10.000 - 500) / 450) + 1 = ceil(21,11) + 1 = 23 chunks
```

**Nếu overlap tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**

Khi đó bước nhảy là `500 - 100 = 400`, nên số chunk là `ceil((10.000 - 500) / 400) + 1 = 25`. Overlap lớn hơn giúp giữ câu hoặc ý đang nằm ở ranh giới giữa hai chunk, đổi lại số vector, thời gian index và chi phí lưu trữ đều tăng.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk` — hướng tiếp cận:**

Tôi dùng regex `(?<=[.!?])\s+` để tách tại khoảng trắng sau dấu kết câu, đồng thời giữ dấu câu ở cuối câu trước. Hàm loại chuỗi rỗng, xử lý input chỉ có khoảng trắng và gom tối đa `max_sentences_per_chunk` câu; tham số này được chặn tối thiểu là 1 để tránh vòng lặp hoặc chunk rỗng.

**`RecursiveChunker.chunk` / `_split` — hướng tiếp cận:**

Thuật toán ưu tiên lần lượt `\n\n`, `\n`, `. `, khoảng trắng và cuối cùng là chuỗi rỗng. Nếu đoạn đã không dài hơn `chunk_size` thì trả về ngay; nếu không còn separator hữu ích hoặc đến separator rỗng thì cắt cứng theo kích thước. Khi có separator, các phần ngắn được gom lại đến ngưỡng, còn phần quá dài tiếp tục đệ quy với separator có độ ưu tiên thấp hơn.

### Lớp EmbeddingStore

**`add_documents` + `search` — hướng tiếp cận:**

`add_documents` tạo record chuẩn gồm `id`, `content`, `embedding` và `metadata`; ưu tiên ChromaDB nếu khởi tạo được, nếu không dùng list in-memory. `search` embed query, tính dot product với từng vector (mock embedding đã chuẩn hoá) và sắp xếp giảm dần theo score. Với chunk, `metadata['doc_id']` giữ ID tài liệu gốc, còn `Document.id` có dạng `doc_id#chunk_index`.

**`search_with_filter` + `delete_document` — hướng tiếp cận:**

`search_with_filter` lọc metadata **trước** khi tính similarity, nên các slot top-k không bị chiếm bởi tài liệu sai đối tượng. `delete_document` tìm/xoá mọi record có `metadata['doc_id']` bằng ID cần xoá; cách này xoá được toàn bộ chunk của một tài liệu thay vì chỉ một chunk cụ thể.

### Tác tử KnowledgeBaseAgent

**`answer` — hướng tiếp cận:**

Agent lấy tối đa `top_k` kết quả từ store, đánh số từng chunk và ghép chúng vào phần `Context` của prompt. Prompt yêu cầu LLM chỉ dùng evidence được cung cấp; nếu context không có đáp án thì phải nói thông tin không có sẵn. Nhờ vậy, phần sinh câu trả lời được tách khỏi retrieval và có guardrail hạn chế hallucination.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

### Kết Quả Kiểm Thử (Test Results)

Lệnh đã chạy:

```text
python -m unittest tests/test_solution.py -q
----------------------------------------------------------------------
Ran 42 tests in 0.005s

OK
```

Môi trường chạy hiện tại không cài `pytest`, vì vậy tôi dùng trực tiếp unittest runner của file kiểm thử. Đây là cùng 42 test trong `tests/test_solution.py` và tất cả đều pass.

**Số lượng bài test vượt qua (pass):** **42 / 42**

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Điểm thực tế dưới đây được tính bằng `compute_similarity(_mock_embed(A), _mock_embed(B))`. Tôi coi score từ 0,5 trở lên là cao.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Artificial intelligence changes how people work. | AI is changing the way people work. | Cao | -0,0136 | Không |
| 2 | Tuition fee deadline is 26 May. | Blue whales eat plankton in the ocean. | Thấp | 0,1108 | Có |
| 3 | Students pay tuition through the ERP QR code. | The ERP QR code is used for tuition payment. | Cao | 0,1926 | Không |
| 4 | A scholarship supports eligible students. | The database server was restarted overnight. | Thấp | -0,0133 | Có |
| 5 | Tuition is calculated by registered credits. | Course registration determines the number of credits. | Cao | 0,0048 | Không |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

Cặp 1 và 3 gần như cùng nghĩa nhưng score rất thấp, trong khi cặp 2 khác hẳn chủ đề lại có score dương. Điều này xác nhận `_mock_embed` là vector giả ngẫu nhiên quyết định bởi MD5, không mã hoá ngữ nghĩa; vì vậy nó phù hợp để test cấu trúc code nhưng không phù hợp để đánh giá retrieval thực tế.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Tôi chạy `python bench.py` với `RecursiveChunker(chunk_size=700)` và backend `TF-IDF unigram + bigram`. Corpus có 11 `doc_id` nguồn và 89 chunks, gồm 10 tài liệu `student` và một báo cáo USSH `staff`. Bộ 5 query/gold answer được đọc từ `benchmark.jsonl`, nên trùng bộ câu hỏi chung của nhóm. Score là cosine/dot product của vector TF-IDF đã chuẩn hoá; kết quả được kiểm tra thêm bằng `doc_id` và gold-evidence span trong chunk.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời grounded từ top-3 (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | SV Việt Nam chương trình đơn bằng USTH đóng bao nhiêu, hạn đóng và hậu quả trễ hạn? | `usth-tuition-semester-2-2025-2026#2`: bảng nêu chương trình đơn bằng là 28,0 triệu đồng/học kỳ. Chunk #1 cùng top-3 nêu thời hạn. | 0,3003 | Có | 28,0 triệu đồng/học kỳ; đóng 23/01–05/02/2026; trễ hạn không được tham gia học phần học kỳ II. |
| 2 | SV NEU khóa 68 và khóa 66 đăng ký 15 tín chỉ phải đóng bao nhiêu? | `neu-tuition-decision-985-2026-2027#2`: quy định học phí NEU 2026-2027 theo Quyết định 985; top-3 chứa hai mức theo khoá. | 0,2668 | Có | Khóa 68: 13.200.000 đồng; khóa 66: 11.550.000 đồng. |
| 3 | Học phí Kỹ thuật phần mềm tiếng Anh NEU 2026-2027 và mức tăng? | `neu-tuition-decision-985-2026-2027#7`: nêu trực tiếp “Kỹ thuật phần mềm tăng từ 50 lên 53 triệu đồng”. | 0,2432 | Có | 53 triệu đồng/năm, tăng 3 triệu đồng, tương đương 6%. |
| 4 | UET gia hạn nộp học phí đến ngày nào, hạn gốc và đối tượng áp dụng? | `uet-tuition-payment-extension-2025-2026#0`; chunk #1 cùng top-3 nêu sinh viên trong danh sách được gia hạn đến 26/5/2026. | 0,3629 | Có | Hạn gốc 20/5; gia hạn hết 26/5 cho SV trong danh sách chưa hoàn thành nghĩa vụ tính đến 21/5. |
| 5 | Học phí một tín chỉ chương trình chuẩn HUST 2024-2025 là bao nhiêu? | `hust-tuition-2024-2025#1`: thông báo HUST; bảng học phí được dẫn bằng link “xem tại đây”, không có số tiền trong corpus. | 0,2992 | Có | Không đủ thông tin trong dữ liệu để nêu số tiền một tín chỉ. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **5 / 5**

### Phân tích failure case và hướng cải thiện

Lần chạy với `_mock_embed` trước đó cho 0/5 vì vector được sinh giả ngẫu nhiên từ MD5, nên không phản ánh nội dung query. Tôi thay bằng TF-IDF fit trên toàn bộ 89 chunks; unigram giữ các thực thể/số liệu như `NEU`, `USTH`, `26/5/2026`, còn bigram giúp phân biệt các cụm như `kỹ thuật phần mềm` và `học phí tín chỉ`. Nhờ vậy tài liệu gold xuất hiện trong top-3 của cả 5 câu, trong đó query 3 và query 4 trả đúng tài liệu ở top-1.

Ở query 1, benchmark chạy cả không lọc và `metadata_filter={"audience": "student"}`. Hai danh sách top-3 giống nhau vì các kết quả tốt nhất vốn đều có audience `student`; filter được áp dụng đúng trước search nhưng chưa tạo lợi ích đo được với nhãn hiện tại. Corpus còn có `hust-tuition.md` trùng nội dung với `hust-tuition-2024-2025.md`; cần loại bản trùng và bổ sung metadata `university`, `academic_year`, `notice_type` để tăng độ đa dạng. TF-IDF là baseline tốt cho fact lookup, nhưng sentence-transformer đa ngôn ngữ hoặc embedding API vẫn là bước tiếp theo để xử lý paraphrase tốt hơn.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**

Điều quan trọng nhất là không đánh giá RAG chỉ bằng việc code chạy hay một score cao: phải mở chunk, đối chiếu với gold evidence và ghi nhận failure case. Tôi cũng rút ra rằng thay backend embedding có ảnh hưởng lớn hơn việc chỉ tinh chỉnh `chunk_size`; tuy nhiên metadata vẫn cần đủ phân biệt để filter tạo thêm giá trị.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
