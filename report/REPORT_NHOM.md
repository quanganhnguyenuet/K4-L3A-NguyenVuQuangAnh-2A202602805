# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** Gì cũng được
**Thành viên:** Nguyễn Vũ Quang Anh, Mai Phan Anh Tùng, Dương Minh Hiếu, Vũ Minh Hiếu, Nguyễn Thị Chinh
**Ngày:** 20/09/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Học phí trường Đại học

**Tại sao nhóm chọn chủ đề này?**
Vì thông tin học phí đại học là nhu cầu tra cứu rất lớn của sinh viên và phụ huynh nhưng thường bị phân tán qua nhiều văn bản, quyết định theo từng năm học và hệ đào tạo (chính quy, chất lượng cao, sau đại học). Bộ dữ liệu này có cấu trúc phân tầng rõ rệt (chứa cả bảng biểu số liệu, mốc thời hạn và điều kiện chính sách miễn giảm/hoàn trả), lý tưởng để thử nghiệm truy xuất ngữ nghĩa (semantic search) kết hợp lọc siêu dữ liệu (metadata filter) theo đối tượng (student vs staff).

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Điều chỉnh học phí sau đại học, giảm 5% - Trường Đại học Công Nghệ - Đại học Quốc Gia Hà Nội|https://uet.vnu.edu.vn/dieu-chinh-hoc-phi-sau-dai-hoc-giam-5/ |2026-09-19 / not-stated| 1583 | `doc_id: dieu-chinh-hoc-phi-sau-dai-hoc-giam-5`, `retrieved_at: 2026-09-19`, `document_version: not-stated`, `audience: student` |
| 2 | Báo cáo lộ trình thu học phí các hệ năm học 2026 - 2027| https://ussh.vnu.edu.vn/vi/gioi-thieu/ba-cong-khai/bao-cao-lo-trinh-thu-hoc-phi-cac-he-nam-hoc-2026-2027-19718.html |2026-09-19 / not-stated| 10416 | `doc_id: bao-cao-lo-trinh-thu-hoc-phi-cac-he-nam-hoc-2026-2027-19718`, `retrieved_at: 2026-09-19`, `document_version: not-stated`, `audience: staff` |
| 3 | dinh-muc-hoc-phi-dao-tao-dai-hoc-nam-hoc-2024-2025 | https://uet.edu.vn/dinh-muc-hoc-phi-dao-tao-dai-hoc-nam-hoc-2024-2025/ | 2026-09-19 / not-stated| 6,884 | `doc_id: dinh-muc-hoc-phi-dao-tao-dai-hoc-nam-hoc-2024-2025`, `retrieved_at: 2026-09-19`, `document_version: not-stated`, `audience: student` |
| 4 | gia-han-thoi-gian-nop-hoc-phi-trong-hkii-nam-hoc-2025-2026 | https://uet.edu.vn/gia-han-thoi-gian-nop-hoc-phi-trong-hkii-nam-hoc-2025-2026/ | 2026-09-19 / not-stated| 1259 | `doc_id: gia-han-thoi-gian-nop-hoc-phi-trong-hkii-nam-hoc-2025-2026`, `retrieved_at: 2026-09-19`, `document_version: not-stated`, `audience: student` |
| 5 | hoan-tra-hoc-phi-cho-sinh-vien-thuoc-chuong-trinh-chat-luong-cao-theo-thong-tu-23-2014-tt-bgddt-tot-nghiep-dot-xet-thang-03-nam-2026 | https://uet.edu.vn/hoan-tra-hoc-phi-cho-sinh-vien-thuoc-chuong-trinh-chat-luong-cao-theo-thong-tu-23-2014-tt-bgddt-tot-nghiep-dot-xet-thang-03-nam-2026/ | 2026-09-19 / not-stated| 2845 | `doc_id: hoan-tra-hoc-phi-cho-sinh-vien-thuoc-chuong-trinh-chat-luong-cao-theo-thong-tu-23-2014-tt-bgddt-tot-nghiep-dot-xet-thang-03-nam-2026`, `retrieved_at: 2026-09-19`, `document_version: not-stated`, `audience: student` |
| 6 | neu-tuition-decision-985-2026-2027| "https://fit.neu.edu.vn/post/hoc-phi-neu-nam-hoc-2026-2027-theo-quyet-dinh-985" | 2026-09-19 / not-stated| 3985 |  `doc_id: neu-tuition-decision-985-2026-2027`, `retrieved_at: 2026-09-19`, `document_version: not-stated`, `audience: student` |
| 7 | neu-tuition-fees-2025-2026 | https://fit.neu.edu.vn/post/neu-tuition-fees-2025-2026 | 2026-09-19 / not-stated| 2826 | `doc_id: neu-tuition-fees-2025-2026`, `retrieved_at: 2026-09-19`, `document_version: not-stated`, `audience: student` |
| 8 | tb-ve-viec-thu-hoc-phi-hoc-ky-ii-nam-hoc-2025-2026-chuong-trinh-dao-tao-trinh-do-dai-hoc-29249 | https://usth.edu.vn/tb-ve-viec-thu-hoc-phi-hoc-ky-ii-nam-hoc-2025-2026-chuong-trinh-dao-tao-trinh-do-dai-hoc-29249/ | 2026-09-19 / not-stated | 2190 | `doc_id: tb-ve-viec-thu-hoc-phi-hoc-ky-ii-nam-hoc-2025-2026-chuong-trinh-dao-tao-trinh-do-dai-hoc-29249`, `retrieved_at: 2026-09-19`, `document_version: not-stated`, `audience: student` |
| 9 | thong-bao-quy-dinh-muc-hoc-phi-chinh-thuc-ap-dung-cho-nam-hoc-2026-2027-33107 | https://usth.edu.vn/thong-bao-quy-dinh-muc-hoc-phi-chinh-thuc-ap-dung-cho-nam-hoc-2026-2027-33107/ | 2026-09-19 / not-stated| 1884| `doc_id: thong-bao-quy-dinh-muc-hoc-phi-chinh-thuc-ap-dung-cho-nam-hoc-2026-2027-33107`, `retrieved_at: 2026-09-20`, `document_version: not-stated`, `audience: student |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
|doc_id | string | neu-tuition-fees-2025-2026 | Định danh tài liệu, hỗ trợ hàm `delete_document()` xoá trọn vẹn các chunks thuộc một tài liệu và theo dõi nguồn gốc dữ liệu |
|title | string | Điều chỉnh học phí sau đại học, giảm 5% - Trường Đại học Công Nghệ - Đại học Quốc Gia Hà Nội | Bổ sung ngữ cảnh cấp cao (high-level context) cho chunk khi tìm kiếm, giúp Agent trích dẫn đúng tiêu đề văn bản trong câu trả lời |
|source_url| string | https://uet.vnu.edu.vn/dieu-chinh-hoc-phi-sau-dai-hoc-giam-5/ | Đảm bảo tính kiểm chứng thực tế (Grounding & Traceability), cho phép người dùng đối chiếu trực tiếp với URL văn bản gốc của trường |
|retrieved_at| string | 2026-09-19 | Đánh giá độ mới (data freshness) của tri thức, giúp hệ thống ưu tiên các thông báo thu học phí mới nhất nếu có cập nhật |
|document_version| string | v1.0 | Đánh dấu phiên bản tài liệu, giúp tránh nhầm lẫn số liệu giữa các phiên bản |
|audience | string | student, staff | Phân tách đối tượng áp dụng (sinh viên, cán bộ) giúp Agent đưa ra thông tin chính xác, phù hợp với vai trò người hỏi |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| Thông báo thu học phí học kỳ II năm học 2025–2026 (Hệ đại học)| FixedSizeChunker (`fixed_size`) | 12 | 190.3 | Không (cắt ngang bảng biểu, ngắt giữa từ, giữa câu) |
| Thông báo thu học phí học kỳ II năm học 2025–2026 (Hệ đại học)| SentenceChunker (`by_sentences`) | 5 | 344.6 | Cắt ngang số và heading nhưng giữ nguyên câu |
| Thông báo thu học phí học kỳ II năm học 2025–2026 (Hệ đại học)| RecursiveChunker (`recursive`) | 31 | 54.2 | Có (ưu tiên ngắt theo đoạn `\n\n` và dòng) |
| Thông báo thu học phí học kỳ II năm học 2025–2026 (Hệ đại học)| HeadingChunker (`heading`) | 6 | 286.8 | Có (giữ nguyên vẹn một section) |
| Quy định định mức học phí đào tạo đại học năm học 2024-2025 - Trường Đại học Công Nghệ - Đại học Quốc Gia Hà Nội | FixedSizeChunker (`fixed_size`) | 44 | 197.3 | Không (cắt ngang bảng biểu, ngắt giữa từ, giữa câu) |
| Quy định định mức học phí đào tạo đại học năm học 2024-2025 - Trường Đại học Công Nghệ - Đại học Quốc Gia Hà Nội | SentenceChunker (`by_sentences`) | 8 | 813.4 | Cắt ngang số và heading nhưng giữ nguyên câu |
| Quy định định mức học phí đào tạo đại học năm học 2024-2025 - Trường Đại học Công Nghệ - Đại học Quốc Gia Hà Nội | RecursiveChunker (`recursive`) | 334 | 18.4 | Có (ưu tiên ngắt theo đoạn `\n\n` và dòng) |
t Quy định định mức học phí đào tạo đại học năm học 2024-2025 - Trường Đại học Công Nghệ - Đại học Quốc Gia Hà Nội | HeadingChunker (`heading`) | 1 | 6531.0 | Giữ trọn toàn văn do chỉ có 1 heading, nhưng trunk quá dài, gây loãng ngữ nghĩa |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — Nguyễn Vũ Quang Anh**
- **Loại chiến lược:** RecursiveChunker, `chunk_size=700` ký tự; retrieval dùng TF-IDF unigram + bigram
- **Mô tả & lý do chọn cho chủ đề này:** Tài liệu học phí gồm thông báo, bảng mức thu và quy định có đoạn dài; recursive chunking ưu tiên cắt theo đoạn (`\n\n`), dòng (`\n`) rồi mới đến câu và từ, nên ít làm mất ngữ cảnh hơn cắt theo số ký tự cố định. Ngưỡng 700 đủ để giữ một quy định hoặc một phần bảng kèm điều kiện trong cùng chunk, đồng thời vẫn tránh nạp cả trang có nhiều menu vào một vector. Corpus hiện có hai audience `student` và `staff`; metadata được trải vào từng chunk. Trong benchmark mới nhất trên 89 chunks, chiến lược này trả về tài liệu/evidence liên quan trong top-3 cho 5/5 câu hỏi.
- **Code snippet (nếu custom):**
```python
# Dán mã nguồn (implementation) vào đây
```

**Thành viên 2 — Mai Phan Anh Tùng**
- **Loại chiến lược:** HeadingChunker + RecursiveChunker (tách theo heading, chunk_size=500)
- **Mô tả & lý do chọn:** Văn bản học phí và thông báo của trường được soạn theo mục: Điều 1., 2. Mức học phí…, tiêu đề có emoji. Mỗi mục thường là một bảng mức phí hoặc một quy trình trọn vẹn.
Chunker tách trước mỗi dòng heading, mỗi section là một chunk. Section dài hơn 500 ký tự thì hạ xuống RecursiveChunker, và tiêu đề được gắn lại vào từng mảnh con.
Kết quả: bảng học phí và 4 bước nộp học phí qua ERP của USTH nằm trọn trong một chunk.
- **Code snippet (nếu custom):**

**Thành viên 3 — Dương Minh Hiếu**
- **Loại chiến lược:** HeadingChunker
- **Mô tả & lý do chọn:** Lý do chọn chiến lược heading là vì tài liệu có cấu trúc rõ theo từng mục và tiêu đề, nên chunk theo section giúp giữ ngữ cảnh chính xác hơn so với cắt theo kích thước đều. Với các câu hỏi về mức học phí, thời hạn, thanh toán hoặc học bổng, thông tin cần tìm thường nằm trong một mục riêng, nên heading chunking giúp giữ đúng chủ đề và dễ truy xuất hơn. Tuy nhiên, khi dùng mock embedding, chunk theo heading vẫn có thể bị nhầm giữa các section cùng chủ đề vì cosine không hiểu ngữ nghĩa.
- **Code snippet (nếu custom):**
```python
class HeadingChunker:
    def __init__(self, chunk_size=500):
        self.chunk_size = chunk_size

    def chunk(self, text):
        headings = []
        body = []
        for line in text.splitlines():
            if line.startswith("#"):
                flush()
                headings.append(line.strip())
            else:
                body.append(line)
        return [("\n".join(headings) + "\n\n" + "\n".join(body)).strip()]
```

**Thành viên 4 — Vũ Minh Hiếu**
- **Loại chiến lược:** RecursiveChunker, chunk_size = 500-700
- **Mô tả & lý do chọn:** Thuật toán cắt theo đoạn `\n\n` trước, nếu đoạn văn vẫn vượt quá `chunk_size` thì sẽ cắt tiếp theo từng dòng `\n`, cuối cùng là theo dấu câu (. ) và khoảng trắng ( ). Lý do chọn là để tránh hiện tượng cắt đứt số liệu biểu phí và tối ưu tương đồng ngữ nghĩa.
- **Code snippet (nếu custom):**

**Thành viên 5 — Nguyễn Thị Chinh**
- **Loại chiến lược:** SentenceChunker 
- **Mô tả & lý do chọn:** Tách văn bản dựa trên các dấu kết thúc câu (. ! ?), sau đó gom từ 2-3 câu liền kề thành 1 chunk hoàn chỉnh. Lý do chọn là vì các quy định về học phí, điều kiện miễn giảm, chính sách hoàn trả và thời hạn nộp thường được diễn đạt trọn vẹn theo từng câu quy chuẩn. Việc phân tách theo câu giúp bảo toàn ngữ nghĩa và tránh hiện tượng cắt ngang số liệu, công thức, hoặc các quy định quan trọng.
- **Code snippet (nếu custom):**

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Nguyễn Vũ Quang Anh | Recursive | 5/10 | Kích thước chunk rộng (700 ký tự) giúp bao quát đủ ngữ cảnh | Các đoạn văn bản bị chia nhỏ do các mục thông báo được cách dòng theo format  `\n\n` |
| Mai Phan Anh Tùng | Heading + Recursive | 7/10 | Kế thừa tiêu đề cấp trên cho mọi chunk con, duy trì ngữ cảnh toàn văn bản | Dễ sinh ra các chunk con quá ngắn nhưng chứa toàn bộ tiêu đề |
| Dương Minh Hiếu | Heading | 8/10 | Giữ trọn vẹn tiêu đề mục theo từng heading lớn | Chỉ xử lý được các văn bản có cấu trúc heading rõ ràng, không hiệu quả với văn bản phi cấu trúc |
| Vũ Minh Hiếu | Recursive | 5/10 | Cắt đoạn theo phân cấp (`\n\n`, `\n`) bảo toàn được khối thông báo ngắn và quy trình nộp tiền | Các đoạn văn bản bị chia nhỏ do các mục thông báo được cách dòng theo format  `\n\n` |
| Nguyễn Thị Chinh | Sentence | 9/10 | Có lợi ở những câu quy chế độc lập | Cắt ngang bảng |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
Phụ thuộc vào cấu trúc của tài liệu và loại query, mỗi chiến lược sẽ có ưu nhược điểm riêng. Tuy nhiên, đối với chủ đề học phí có nhiều thông tin dạng quy chế, bảng biểu và danh sách, SentenceChunker là tốt nhất vì giữ được toàn vẹn ngữ nghĩa của từng câu, tránh hiện tượng cắt ngang thông tin quan trọng như thời hạn, mức phí hay điều kiện hoàn trả. Trong khi các phương pháp khác dễ bị split chunk ở các bảng biểu phức tạp hoặc các mục dài, SentenceChunker đảm bảo từng chunk đều là một câu hoàn chỉnh, giúp tối ưu hóa khả năng truy xuất và trả lời chính xác.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Trường Đại học Công Nghệ gia hạn nộp học phí học kỳ II năm học 2025-2026 đến khi nào? | 26/05/2026 | Nhà trường gia hạn thời gian nộp học phí cho các sinh viên có tên trong danh sách nói trên đến hết ngày 26/5/2026. |
| 2 | Hướng dẫn đóng học phí học kỳ II năm 2025-2026 qua hệ thống ERP của sinh viên USTH | Đăng nhập hệ thống ERP: https://erp.usth.edu.vn/students -> Chọn mục Học phí, tra cứu hóa đơn -> Kiểm tra mức học phí phải nộp -> Quét mã QR để hoàn tất thanh toán -> Thanh toán được xác nhận khi trạng thái hóa đơn chuyển sang “Đã đóng”. | Sinh viên nộp học phí bằng hình thức chuyển khoản qua mã QR hiển thị trên hệ thống ERP của Nhà trường; Các bước thực hiện: Đăng nhập hệ thống ERP: https://erp.usth.edu.vn/students; Chọn mục Học phí, tra cứu hóa đơn; Kiểm tra mức học phí phải nộp; Quét mã QR để hoàn tất thanh toán; Thanh toán được xác nhận khi trạng thái hóa đơn chuyển sang “Đã đóng”. |
| 3 | Đối với các khoá 2021 trở về trước thì học bằng kép ở Trường Đại học Công Nghệ năm học 2024-2025 hết bao nhiêu tiền 1 tín chỉ? | 450.000 đồng/tín chỉ| Định mức học phí đào tạo đại học các khoá tuyển sinh từ năm 2021 trở về trước là:... Định mức học phí chương trình đào tạo bằng kép là: 450.000 đồng/tín chỉ, áp dụng cho các hình thức: học lần đầu, học lại, học cải thiện điểm, học tự chọn tự do.  |
| 4 | Chương trình định hướng ứng dụng POHE của NEU năm học 2025-2026 có học phí bao nhiêu?| Khoảng 45 — 55 triệu đồng/năm | Mức học phí theo chương trình POHE (định hướng ứng dụng) Khoảng 45 — 55 triệu đồng/năm |
| 5 | Theo lộ trình được duyệt thì mức thu học phí đối với sinh viên quốc tế là bao nhiêu? ({"audience": "staff"}) | 45.000.000đ/năm học/SV | 1.2. Đối với sinh viên quốc tế (không phải diện hiệp định) Mức thu: 45.000.000đ/năm học/SV. |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Trường Đại học Công Nghệ gia hạn nộp học phí học kỳ II năm học 2025-2026 đến khi nào? | SentenceChunker / RecursiveChunker | Đúng | |
| 2 | Hướng dẫn đóng học phí học kỳ II năm 2025-2026 qua hệ thống ERP của sinh viên USTH | HeadingChunker | Đúng | |
| 3 | Đối với các khoá 2021 trở về trước thì học bằng kép ở Trường Đại học Công Nghệ năm học 2024-2025 hết bao nhiêu tiền 1 tín chỉ? | RecursiveChunker | Đúng | |
| 4 | Chương trình định hướng ứng dụng POHE của NEU năm học 2025-2026 có học phí bao nhiêu? | SentenceChunker / RecursiveChunker | Đúng | |
| 5 | Theo lộ trình được duyệt thì mức thu học phí đối với sinh viên quốc tế là bao nhiêu? | RecursiveChunker + Metadata Filter | Đúng | |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
Có. Khi tìm kiếm mức học phí sinh viên quốc tế mà không lọc metadata, công cụ truy xuất bị nhiễu bởi văn bản của Trường Đại học Công Nghệ (`audience: student`). Khi áp dụng `metadata_filter={"audience": "staff"}`, toàn bộ tài liệu sinh viên bị loại bỏ, giúp hệ thống định vị chính xác Báo cáo lộ trình nội bộ của USSH.
---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
1. Việc chia nhỏ tài liệu thành các mục nhỏ (chunking) có vai trò quyết định chất lượng truy xuất. Mỗi chiến lược có ưu nhược điểm riêng: 
    - Strategy fixed_size: Chia đều các phần nhỏ nhưng dễ làm mất tính toàn vẹn của các bảng số liệu và câu quy định. 
    - Strategy heading: Phù hợp với các tài liệu có cấu trúc rõ ràng theo tiêu đề, giúp giữ nguyên nội dung từng mục.
    - Strategy recursive: Kết hợp được tính linh hoạt của việc cắt theo cấu trúc đoạn/câu với kích thước cố định, tối ưu hóa việc giữ ngữ cảnh. 
    - Strategy by_sentences: Phù hợp với nội dung văn bản, nhưng có thể cắt ngang bảng biểu hoặc tiêu đề.

2. Lọc dữ liệu (metadata) giúp giảm nhiễu và cải thiện độ chính xác, đặc biệt với các câu hỏi yêu cầu thông tin cụ thể theo đối tượng hoặc thời gian.

3. Kết hợp các phương pháp chunking phù hợp + metadata để tối ưu hóa chất lượng truy xuất.

**Bài học rút ra khi so sánh trong nhóm:**
Khi so sánh các chiến lược chunking với cùng tài liệu và bộ câu hỏi, nhóm nhận thấy:
- Việc cắt các đoạn văn bản quá ngắn hoặc quá dài sẽ làm giảm chất lượng truy xuất. 
- Việc cắt các đoạn văn bản theo cấu trúc đoạn/câu sẽ giúp giữ nguyên ngữ cảnh, tăng cường độ chính xác của thông tin được truy xuất.
- Việc sử dụng metadata giúp giảm nhiễu và cải thiện độ chính xác của thông tin được truy xuất.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
Nếu làm lại, nhóm sẽ chọn các file dữ liệu có metadata đầy đủ hơn. 

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |
