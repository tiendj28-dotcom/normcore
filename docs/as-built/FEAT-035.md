# As-Built FEAT-035 — Sản lượng cận lâm sàng và xuất kho

Issue NORM-36. FR: FR-ACCT-012..015, FR-CLS-007 (mục sản lượng). UC-022. Màn hình SCR-DSK-037 (mới), SCR-DSK-021 (nút sang SCR-DSK-037). TC: TC-CLS-34, TC-CLS-35, TC-CLS-36.
Giới hạn: giao diện chưa thao tác bằng trình duyệt (SCR-DSK-037, nút ở SCR-DSK-021 chưa có trên staging; Lead quyết kiểm sau khi merge và deploy staging). Không có site sạch cục bộ (thiếu `DB_ROOT_PASSWORD`); dùng CI run 45568804074 thay (ASM-035-13). Người nghiệm thu: QA (Multica).

## Đã làm
- Ba DocType mới: NC Test System Volume (duy nhất theo năm, kịch bản, hệ thống xét nghiệm, DI-14), NC Equipment Usage (năm, kịch bản, thiết bị, khoa), NC Stock Issue Actual (năm, khoa, mặt hàng). Quyền theo ma trận mục 4 (NC Finance ghi; NC Department Head đọc theo khoa qua `SCOPE_RULES`; NC Director, NC Admin, NC Auditor đọc; không ai xóa).
- Hàm thuần `normcore/costing/cls_volume.py` (không import `frappe`; phủ 100%): kiểm số, đổi mã ngoài sang mã dịch vụ, khớp hệ thống xét nghiệm, kiểm phút khai thác và xuất kho, trạng thái mục sản lượng. `costing/test_systems.py::status_items(volume=None)` nhận bản ghi sản lượng.
- Ba bộ nhập `nc_test_system_volume`, `nc_equipment_usage`, `nc_stock_issue_actual` (`core/import_sets.py`) và `api/cls_volume.py` (hàm `prepare_*`).
- Khung nhập FEAT-004 mở rộng tương thích ngược (ASM-035-01, Lead duyệt): `Column.virtual`, `ImportSet.prepare`, `ImportSet.stored_columns`, `RowValueError`, `process(prepare=)`. Bộ nhập cũ chạy như trước; test cũ không sửa.
- `api/test_system.py::get_status` truyền sản lượng mới nhất kịch bản "Thực tế 12 tháng" vào khối tình trạng; form NC Test System hiện pill xanh/cam kèm liên kết.
- Giao diện: ba danh sách và form (nút Nhập từ Excel, bộ lọc kịch bản mặc định, indicator "Sẽ ước tính từ kế hoạch", cảnh báo cột trống), nút sang SCR-DSK-037 ở danh sách NC Service Volume, nhóm lối tắt Workspace, `vi.csv`.
- `api/test_importer.py`: danh sách bộ nhập của NC Finance thêm đúng 3 khóa, vẫn `assertEqual` đủ danh sách (ASM-035-09, Lead duyệt trên NORM-36).

## Ghi chú cho FEAT-036
- Ô số test phụ (nội kiểm, chuẩn máy, chạy lại, ngoại kiểm), hao hụt, cỡ mẻ, số ngày chạy để trống được lưu là **NULL** (không phải 0): NULL nghĩa là ước tính từ kế hoạch chất lượng (FR-QC-006, TBD-16); 0 là số thực. Cột DB của NC Test System Volume được đặt `null default null` ở `on_doctype_update` (ASM-035-12).
- Qtb không lưu. NC Equipment Usage chỉ có `total_minutes` (Mtb); bộ máy tính giá cộng `patient_results` của các hệ thống dùng thiết bị trong khoa.
- NC Stock Issue Actual: lượng xuất theo đơn vị mua `NC Item.uom`, dùng cho đối soát vật chất (FR-COST-026).
- Dòng sản lượng đọc theo (năm, kịch bản, hệ thống); `technical_service` và `department` lấy từ hệ thống.

## Giả định
ASM-035-01..13 trong `docs/decisions/assumptions/FEAT-035.md`. ASM-035-01 và 09 do Lead duyệt trên NORM-36; ASM-035-12 (cột NULL) mới.
