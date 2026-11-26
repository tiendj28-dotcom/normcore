# Giả định của FEAT-013 (NORM-51)

Theo ASM-NORM32-02: mỗi FEAT một tệp, mã `ASM-013-XX`. Thiết kế: `docs/features/FEAT-013/technical-design.md`. Sửa thiết kế: AMD-013-01.

| Mã | TBD | FEAT/BR | Lựa chọn | Chỗ trong mã | Trạng thái |
| :-- | :-- | :-- | :-- | :-- | :-- |
| ASM-013-01 | — | FEAT-013, FR-NORM-015, FR-WF-011 | "Quy trình mới" = NC Clinical Procedure "Đã ban hành" cùng (dịch vụ, khoa) có `version_no` lớn nhất, lớn hơn `version_no` của quy trình bộ nguồn; kể cả khi ngày hiệu lực ở tương lai (khớp FEAT-008 đặt cờ ngay lúc ban hành) | `api/norm.py::_latest_published`, `new_version` | Áp dụng theo CLAUDE.md mục 6 |
| ASM-013-02 | — | FEAT-013, FR-NORM-015, UC-009 1a | Có quy trình mới hơn thì tạo phiên bản được từ bộ "Nháp", "Đã xác nhận chuyên môn" hoặc "Đã khóa" (không từ "Đã thay thế"); bộ nguồn giữ nguyên. Không có quy trình mới hơn: giữ luật FEAT-012 (chỉ từ "Đã khóa") | `api/norm.py::new_version`, `_actions` | Áp dụng theo CLAUDE.md mục 6 |
| ASM-013-03 | — | FEAT-013, FR-NORM-015, ASM-012-09 | Đã có bộ "Nháp"/"Đã xác nhận chuyên môn" cùng (dịch vụ, khoa) tham chiếu đúng quy trình mới → trả bộ đó (`existing` = 1), không tạo thêm. Bộ đang soạn theo quy trình cũ không chặn | `api/norm.py::new_version` | Áp dụng theo CLAUDE.md mục 6 |
| ASM-013-04 | — | FEAT-013, FR-NORM-015 | Mang dòng theo **mã bước** (không theo mã dòng nguồn lực): mọi dòng của bước còn tồn tại và mọi dòng "Chung" được mang sang, giữ `line_id`, `procedure_resource_row`, bỏ xác nhận. Không tự sinh dòng cho bước mới hay dòng nguồn lực mới; chỉ liệt kê bước chưa có dòng (dòng loại trừ tính là có dòng) | `norm/init_from_procedure.py::carry_lines`, `steps_without_lines` | Áp dụng theo CLAUDE.md mục 6 |
| ASM-013-05 | — | FEAT-013, FR-NORM-015, ASM-012-07 | Dòng thuộc bước đã bỏ mang sang kèm cờ `step_removed` (AMD-013-01), giữ `step_id` cũ; xóa được kể cả khi lấy từ quy trình; gán bước khác hoặc "Chung" thì cờ tự gỡ | `nc_norm_set.py::validate_lines`, `api/norm.py::delete_line` | Áp dụng theo CLAUDE.md mục 6 |
| ASM-013-06 | — | FEAT-013, FR-WF-011 | Không gỡ `needs_update` ở bộ nguồn; bộ mới `needs_update` = 0. Bộ nguồn "Đã khóa" thành "Đã thay thế" khi bộ mới khóa (DI-03 sẵn có) | `api/norm.py::new_version` | Áp dụng theo CLAUDE.md mục 6 |
| ASM-013-07 | — | FEAT-013, FR-NORM-016 | Chi phí tạm tính vẫn tính dòng thuộc bước đã bỏ, gộp dưới mã bước cũ (hàng riêng); không thêm công thức | `api/norm.py::get_norm_set` | Áp dụng theo CLAUDE.md mục 6 |
| ASM-013-08 | — | FEAT-013, FR-NORM-015 | Kết quả mang sang ghi bằng Comment "Info" trên bộ mới (không thêm trường; `step_change_note` vẫn là của FR-WF-011) và trả trong kết quả `new_version`; danh sách bước chưa có dòng tính lại mỗi lần mở lưới | `api/norm.py::new_version`, `get_norm_set` | Áp dụng theo CLAUDE.md mục 6 |
