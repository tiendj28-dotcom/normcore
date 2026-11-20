GIAI ĐOẠN: RELEASE — {{RELEASE}}

Đọc `CLAUDE.md`, `docs/implementation-plan.md` mục 1 (phạm vi và "kết quả trình diễn được" của {{RELEASE}}), `docs/test-cases.md` phần kịch bản đầu cuối E2E.

1. Kiểm mọi FEAT thuộc {{RELEASE}} có `DONE` hoặc `BLOCKED`. Liệt kê FEAT BLOCKED.
2. Tạo nhánh `release/{{RELEASE_LOWER}}` từ `develop`. Trên site sạch: chạy toàn bộ kiểm thử, golden, quét quy ước, độ phủ, `build_rtm.py`.
3. Viết và chạy test tự động cho các kịch bản E2E thuộc {{RELEASE}} (E2E-01…E2E-04 tùy phạm vi) trong `normcore/tests/e2e/`, dùng dữ liệu `normcore/demo/`. E2E nào cần FEAT BLOCKED thì ghi "không chạy được — chờ FEAT-xxx".
4. Kiểm NFR đo được ở mức site test: thời gian lần tính giá, bản dịch đủ (không còn chuỗi tiếng Anh trên giao diện), quyền NC Auditor, sao lưu và khôi phục thử một lần trên staging (NFR-AVL-002).
5. Viết `docs/releases/{{RELEASE}}.md`: phạm vi, FEAT DONE/BLOCKED, kết quả E2E, NFR, ASM đang áp dụng, DEF đang mở, hướng dẫn cài đặt và cấu hình.
6. Merge `release/{{RELEASE_LOWER}}` vào `main` (không force), tag `{{TAG}}`, merge ngược vào `develop`.
7. Chỉ khi biến môi trường `AUTO_DEPLOY_PROD` là `true`: chạy workflow deploy production và smoke test. Ngược lại ghi trong báo cáo "Bản đã sẵn sàng; chưa đẩy production".
