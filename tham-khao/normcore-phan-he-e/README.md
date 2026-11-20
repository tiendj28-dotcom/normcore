# Normcore – Phân hệ E: bộ tài liệu phân tích nghiệp vụ (13/11/2026)

> **Bản nháp, không dùng để xây dựng.** Bộ này viết độc lập với bộ tài liệu chính A–D ở `claude/docs/` nên trùng mã yêu cầu (FR-SVC, FR-AI, FR-AUD, NFR, IF) và trùng chức năng DocType (`CLS` so với `NC`). Ngày 13/11/2026 chủ dự án quyết định hợp nhất Phân hệ E vào bộ A–D và làm cùng R1. Bộ này là tài liệu nguồn cho bản sửa đổi SRS 1.1; phương án hợp nhất ở `claude/docs/phan-he-e-hop-nhat.md`.

Bản để đọc và bình luận: doc nhiều tab “Normcore – Phân hệ E: Bộ tài liệu phân tích nghiệp vụ bàn giao dev” (https://claude.ai/artifact/Bp4sSXRJed4CF8vzmkNvNB). Các tệp Markdown trong thư mục này là bản đưa vào `docs/` của repo Normcore.

| Tệp | Nội dung | Quy mô |
| :-- | :-- | :-- |
| srs.md | Đặc tả yêu cầu, cú pháp EARS, khuôn ISO 29148 | 123 FR trong 18 nhóm, 20 NFR, 8 giao diện ngoài, 10 câu hỏi mở |
| use-cases.md | Đặc tả use case, có sơ đồ Mermaid | 15 use case |
| data-model.md | Đặc tả DocType, ma trận quyền, luồng trạng thái | 35 DocType, 8 vai trò, 2 workflow |
| calculation-rules.md | Công thức, quy tắc kiểm tra, vector kiểm thử | 16 QT, 17 KT, 16 TV, 17 khoản mục chi phí |
| test-scenarios.md | Kịch bản nghiệm thu Cho – Khi – Thì | 50 kịch bản |
| implementation-plan.md | Kế hoạch sơ bộ, Definition of Done, mẫu As-Built | 8 epic, 6 mốc |
| rtm.md | Ma trận truy vết | 143 dòng |
| scripts-vectors.py | Mã sinh giá trị kỳ vọng của vector kiểm thử | – |
| scripts-build-rtm.py | Mã sinh RTM và kiểm tra chéo mã yêu cầu | Đường dẫn trong mã cần sửa theo repo |

## Trạng thái
- SRS bản 1.0, dựng từ tài liệu ý tưởng Phân hệ E bằng skill requirements-engineering (agentic-sdlc-kit). Chưa qua phỏng vấn người dùng bệnh viện; chủ sản phẩm chưa rà soát.
- Kiểm tra chéo ngày 13/11/2026: không có mã trùng; mọi FR có use case và epic; mọi FR mức M có kịch bản kiểm thử; mọi tham chiếu QT, KT, TV đều tồn tại.
- Chưa có kịch bản cho 4 FR mức C và 7 FR mức S (liệt kê ở test-scenarios.md mục 6).

## Giả định chính (chi tiết ở SRS mục 2.6 và Phụ lục B)
Normcore chạy độc lập trên Frappe v15, liên kết ERPNext tùy chọn; kịch bản sản lượng mặc định là thực tế 12 tháng; VAT đầu vào tính vào chi phí; bản đầu nhập liệu bằng tệp; hệ số cấp 5 nhập tay khi Phân hệ C chưa có.

## Việc tiếp theo
Thay cho chuỗi bước riêng của bộ này: chủ dự án xác nhận 11 điểm xung đột ở `claude/docs/phan-he-e-hop-nhat.md` mục 6, sau đó chạy requirements-engineering ở chế độ sửa đổi trên `claude/docs/srs.md` để lên bản 1.1, không đổi và không tái sử dụng mã đã cấp.
