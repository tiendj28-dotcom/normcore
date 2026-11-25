# NORM-31 — Thiết kế giao diện bản sửa

Không màn hình mới, không đổi bố cục. Chỉ đổi hành vi hai màn hình Desk chuẩn đã có. Chuỗi JS tiếng Anh trong `__()`, bản dịch ở `normcore/translations/vi.csv` (thứ tự chữ cái, không trùng khóa). Không mã màu cứng. Quyền vẫn do máy chủ quyết.

## SCR-DSK-031 Nhập dữ liệu từ Excel (Desk Page `import-excel`, FEAT-004)

Loại hiện thực: Desk Page (`frappe.ui.make_app_page`), giữ nguyên bố cục: trường "Danh mục" (Select) ở thanh trường; nút phụ "Tải mẫu"; nút trong "Tải tệp lên", "Kiểm tra", "Xác nhận nhập"; vùng tên tệp và vùng kết quả.

Thay đổi hành vi (technical-design mục 2):

| Cách vào trang | Kết quả |
| :-- | :-- |
| Từ nút "Nhập từ Excel" ở danh sách Bảng ánh xạ tài khoản / Sản lượng dịch vụ / Tiêu chí trung tâm chi phí / Hệ thống xét nghiệm (`import_set` = khóa bộ nhập), người dùng có quyền tạo DocType đích | "Danh mục" đã chọn sẵn bộ nhập đó; vùng tệp "Chưa chọn tệp"; "Kiểm tra", "Xác nhận nhập" tắt |
| URL `/app/import-excel?import_set=<khóa>` | Như trên |
| Khóa sai hoặc người dùng không có quyền với bộ nhập đó | Chọn bộ nhập đầu danh sách như cũ; không thông báo, không lỗi |
| Không có tham số (menu, Workspace, danh sách hồ sơ tuân thủ thiết bị) | Như cũ: bộ nhập đầu danh sách |
| Trang đang mở bộ A (có thể đã tải tệp), quay lại danh sách khác rồi bấm "Nhập từ Excel" với bộ B | "Danh mục" đổi sang B; tệp đã tải bị bỏ, nút Kiểm tra/Xác nhận tắt (như khi tự đổi danh mục) |
| Quay lại trang bằng nút Back sau khi đã tự đổi danh mục | Giữ danh mục người dùng đang chọn (tham số đã dùng một lần) |
| Người dùng không có quyền với bộ nhập nào | Như cũ: "Bạn không có quyền nhập dữ liệu." |

Trạng thái đang tải: trường "Danh mục" trống cho tới khi `list_import_sets` trả về, sau đó chọn ngay khóa chờ (không nhấp nháy qua bộ đầu tiên). NC Auditor: không có quyền tạo → rơi vào hàng "không có quyền với bộ nhập nào". 1366 × 768, bàn phím: không đổi.

API: `normcore.api.importer.list_import_sets` (có sẵn). Không API mới.

## SCR-DSK-020 Nhập số liệu kế toán (Form NC Accounting Import, FEAT-016)

Loại hiện thực: Form chuẩn Desk. Bố cục không đổi. Nút "Sửa loại chi phí của một dòng" (nhóm Thao tác) hiện như cũ: chỉ khi trạng thái "Nháp" và có quyền ghi.

| Tình huống khi bấm nút | Kết quả |
| :-- | :-- |
| Chưa tích dòng nào trong bảng Dòng | Hộp thông báo "Chọn một dòng trong bảng Dòng trước."; không mở hộp thoại sửa |
| Tích từ hai dòng trở lên | Hộp thông báo "Chỉ chọn một dòng để sửa."; không mở hộp thoại sửa (ASM-016-01) |
| Tích đúng một dòng | Hộp thoại tiêu đề "Sửa loại chi phí: dòng {số thứ tự}, tài khoản {mã tài khoản}" (ví dụ "Sửa loại chi phí: dòng 3, tài khoản 6421"); các trường Loại chi phí, Loại trừ, Lý do (bắt buộc), mô tả mã — giữ nguyên; Lưu gọi `normcore.api.accounting.update_line` như cũ; thiếu lý do vẫn bị từ chối (TC-ACCT-04) |

Số dòng là cột "#" của lưới (`idx`). Mã tài khoản thoát HTML trước khi hiển thị. Trạng thái Đã chốt, NC Auditor, người không có quyền ghi: không có nút (không đổi).

## Chuỗi mới cho `vi.csv`

| Khóa (JS) | Bản dịch |
| :-- | :-- |
| `Edit cost category: line {0}, account {1}` | `Sửa loại chi phí: dòng {0}, tài khoản {1}` |
| `Select one line in the Lines table first.` | `Chọn một dòng trong bảng Dòng trước.` |
| `Select only one line to edit.` | `Chỉ chọn một dòng để sửa.` |

Trang `import-excel` không thêm chuỗi mới.
