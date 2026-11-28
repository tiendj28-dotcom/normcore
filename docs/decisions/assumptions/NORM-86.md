# Giả định của NORM-86 (kiểm thử giao diện toàn bộ chức năng)

Tệp theo quy ước ASM-NORM32-02. Quyết định của BA khi trả lời câu hỏi của Tester ở vòng kiểm 1.

| Mã | TBD | FEAT/BR | Lựa chọn | Chỗ trong mã | Trạng thái |
| :-- | :-- | :-- | :-- | :-- | :-- |
| ASM-NORM86-01 | — | CLAUDE.md (nhãn giao diện tiếng Việt), SCR-DSK-001 | Tài liệu không chốt ngôn ngữ mặc định của site. Ngôn ngữ mặc định `vi` là cấu hình triển khai, không sửa mã: đặt `System Settings.language = vi` trên site (preview, staging, production). Người dùng tạo mới nhận ngôn ngữ của site. Đổi được, không ảnh hưởng dữ liệu. | Cấu hình site (không đổi mã) | Quyết định BA (CLAUDE.md mục 6, phương án đơn giản, đảo ngược được) |
| ASM-NORM86-02 | — | FEAT-016, NORM-87 | NC Accounting Import không đặt `title_field`. Thiết kế cũ ghi `title_field` = `name`, nhưng `name` không phải trường thật nên ListView lỗi; PR #90 bỏ thuộc tính này. `technical-design.md` mục 2.2 đã sửa theo mã. | `nc_accounting_import.json` | Đã sửa trong mã (PR #90, NORM-87) |
| ASM-NORM86-03 | — | NORM-86 kế hoạch kiểm, `docs/golden/` | Dữ liệu mẫu cho kiểm thử giao diện lấy từ các bộ dựng sẵn đã đối chiếu golden: `normcore/tests/costing_fixtures.py::make_golden_world` (tính giá lâm sàng) và `normcore/tests/golden/cls_fixture.py` (cận lâm sàng, C-10). Chỉ nạp vào site preview `normcore.test`, không nạp vào staging hay production. Không viết script nạp mới trong NORM-86. | `normcore/tests/costing_fixtures.py`, `normcore/tests/golden/cls_fixture.py` | Quyết định BA |
