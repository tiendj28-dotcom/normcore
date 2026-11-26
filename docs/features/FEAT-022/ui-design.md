# FEAT-022 — Thiết kế giao diện

Nguồn: `ux-foundations.md` SCR-DSK-004 ("P nhẹ (bảng trong form)": đề xuất kèm độ tin cậy; lọc "chưa xác nhận"; xác nhận hàng loạt các dòng 100%); `design.md` mục 3; technical-design mục 2, 4. Chỉ dùng Form chuẩn của Desk, HTML trong form và `frappe.ui.Dialog`, không trang Vue. Chuỗi JS viết tiếng Anh trong `__()` kèm bản dịch ở `vi.csv` (cùng cách FEAT-020); nhãn DocType và thông báo máy chủ tiếng Việt. Ngày giờ theo định dạng hệ thống (dd/mm/yyyy HH:mm, NFR-LOC-001).

Màu chỉ báo (`indicator-pill` của Desk, theo `design.md` mục 3):

| Giá trị | Lớp |
| :-- | :-- |
| Đề xuất | `gray` |
| Đã xác nhận | `green` |
| Độ tin cậy 100% / 70–99% / dưới 70% | chữ thường kèm `indicator-pill green` / `blue` / `yellow` (chỉ để quét mắt; giá trị số luôn hiện) |

Đề xuất của FEAT này là đề xuất theo quy tắc, không phải của AI: không dùng kiểu "Dòng đề xuất của AI" (`purple`).

## SCR-DSK-004 Ánh xạ hướng dẫn (bảng trong Form NC Legal Document)
Loại: Form chuẩn NC Legal Document, section "Ánh xạ hướng dẫn" (`mapping_doc_section`, chỉ hiện khi `is_procedure_guideline` = 1) chứa HTML `mapping_html`, nằm sau section "Các mục". Tệp: mở rộng `nc_legal_document.js` (hàm vẽ tách riêng `normcore/public/js/library_mapping.js` nếu dài hơn ~150 dòng, nạp qua `doctype_js` cùng tệp form).

**Bố cục (từ trên xuống):**
1. Thanh công cụ trong khung (một hàng, trái → phải):
   - Ô chọn "Unconfirmed only" ("Chỉ chưa xác nhận", Check, mặc định bật khi còn dòng "Đề xuất", tắt khi không còn).
   - Dòng tóm tắt: "{0} sections · {1} confirmed · {2} suggested" ("{0} mục · {1} đã xác nhận · {2} đề xuất").
   - Bên phải (chỉ khi có quyền ghi): nút "Confirm all 100% ({0})" ("Xác nhận các dòng 100% ({0})", {0} = `pending_exact`, ẩn khi 0), nút "Confirm selected" ("Xác nhận đã chọn", khóa khi chưa chọn dòng), nút "Suggest again" ("Đề xuất lại").
2. Bảng (một hàng cho mỗi dòng ánh xạ; mục có nhiều ánh xạ gộp ô Số mục/Tiêu đề bằng `rowspan`; mục chưa có ánh xạ hiện một hàng với ô dịch vụ "—"):

| Cột | Nội dung |
| :-- | :-- |
| ☐ | Ô chọn, chỉ ở dòng "Đề xuất" và khi có quyền ghi |
| Số mục | `section_no`, liên kết mở form NC Legal Section |
| Tiêu đề | `heading` (escape), tự xuống dòng |
| Dịch vụ | `technical_service` — `service_name`; liên kết mở NC Technical Service |
| Độ tin cậy | `confidence` + "%" kèm chỉ báo màu (bảng trên); trống → "Thêm tay" ("Manual") |
| Trạng thái | chỉ báo "Đề xuất" / "Đã xác nhận"; với "Đã xác nhận" dòng nhỏ bên dưới: "{0}, {1}" (người xác nhận — `frappe.user.full_name`, thời điểm) |
| Thao tác | khi có quyền ghi: "Confirm" ("Xác nhận", chỉ ở dòng "Đề xuất"), "Change" ("Sửa"), "Remove" ("Bỏ"); cuối nhóm của mỗi mục: "+ Add service" ("+ Thêm dịch vụ") |

3. Dưới bảng: nút "More" ("Xem thêm") khi `start + rows < total` (trang 100 mục).

**Tương tác và API:**

| Hành động | Gọi | Sau khi xong |
| :-- | :-- | :-- |
| Mở form / đổi bộ lọc / Xem thêm | `normcore.api.library.get_mappings(legal_document, unconfirmed_only, start, page_length=100)` | Vẽ lại bảng |
| Xác nhận một dòng | `confirm_mappings(legal_document, [row])` | `frappe.show_alert` "Confirmed {0} mapping(s)" ("Đã xác nhận {0} ánh xạ", `green`), tải lại bảng |
| Xác nhận đã chọn | `confirm_mappings(legal_document, rows)` | như trên; bỏ chọn |
| Xác nhận các dòng 100% | `frappe.confirm` "Confirm {0} suggestions with 100% confidence?" ("Xác nhận {0} đề xuất có độ tin cậy 100%?") → `confirm_exact(legal_document)` | như trên |
| Sửa / Thêm dịch vụ | `frappe.ui.Dialog` tiêu đề "Change service" / "Add service" ("Sửa dịch vụ" / "Thêm dịch vụ"), một trường Link NC Technical Service (BB, lọc `is_active` = 1), dòng gợi ý "Saving confirms the mapping." ("Lưu là xác nhận ánh xạ.") → `save_mapping(section, technical_service, row)` | alert "Mapping saved" ("Đã lưu ánh xạ"), tải lại bảng |
| Bỏ | `frappe.confirm` "Remove this mapping?" ("Bỏ ánh xạ này?") → `remove_mapping(row)` | alert "Mapping removed" ("Đã bỏ ánh xạ"), tải lại |
| Đề xuất lại | `frappe.confirm` "Recalculate suggestions? Confirmed mappings are kept; current suggestions are replaced." ("Tính lại đề xuất? Ánh xạ đã xác nhận được giữ; đề xuất hiện có được thay.") → `suggest_mappings(legal_document)` | alert "{0} suggestions created" ("Đã tạo {0} đề xuất"), tải lại |

Khi đang gọi: nút đang bấm bị khóa (`frappe.call` với `freeze: true` cho thao tác hàng loạt, `btn` cho thao tác một dòng). Bảng tự tải lại khi form `refresh` (kể cả sau lập chỉ mục xong).

## Form mục — bảng ánh xạ (Form NC Legal Section, một phần SCR-DSK-004)
Loại: bảng con chuẩn `service_mappings` trong section "Ánh xạ dịch vụ" (sau "Hiệu lực", trước "Đối chiếu"). Cột lưới: Dịch vụ kỹ thuật, Trạng thái, Độ tin cậy (%), Người xác nhận, Thời điểm xác nhận (ba cột cuối chỉ đọc). Người có quyền ghi thêm/sửa/xóa dòng và lưu bằng Ctrl+S; máy chủ đóng dấu người/thời điểm (technical-design 2.4). Lưới dùng `get_query` lọc `is_active` = 1 cho `technical_service`. Thay đổi hiện trên timeline (Version của mục).

## Trạng thái

| Trạng thái | Hiển thị |
| :-- | :-- |
| Văn bản không phải hướng dẫn QTKT | Section "Ánh xạ hướng dẫn" ẩn (`depends_on`) |
| Chưa lập / Đang lập / Lỗi | Khung hiện "Mappings are available after indexing finishes." ("Ánh xạ có sau khi lập chỉ mục xong."); không gọi API |
| Rỗng (đã lập, chưa có ánh xạ nào) | "No suggestions found. Use + Add service on each section or Suggest again." ("Không có đề xuất. Dùng + Thêm dịch vụ ở từng mục hoặc Đề xuất lại."); bảng vẫn liệt kê các mục |
| Bộ lọc "Chỉ chưa xác nhận" không còn dòng | "All sections are confirmed." ("Mọi mục đã được xác nhận.") (`green`) |
| Đang tải | "Loading…" trong khung; nút hàng loạt khóa |
| Lỗi | Thông báo máy chủ tiếng Việt qua `frappe.msgprint` (trùng dịch vụ, ánh xạ không thuộc văn bản, chưa lập chỉ mục); bảng giữ dữ liệu cũ |
| Không có quyền đọc | Trang không đủ quyền của Desk |
| Chỉ đọc (NC Auditor và mọi vai không phải Doc Controller/Admin) | Bảng hiện đủ cột, không ô chọn, không cột Thao tác, không nút hàng loạt/"Đề xuất lại"; bộ lọc vẫn dùng được. Quyết định theo `frm.perm[0].write` của NC Legal Document và quyền máy chủ (API vẫn tự kiểm) |

Bàn phím: mọi nút, liên kết, ô chọn là phần tử focus được theo thứ tự đọc (Tab); Enter/Space kích hoạt; hộp thoại Enter lưu, Esc đóng. 1366 × 768: bảng toàn chiều rộng form, cột Tiêu đề co giãn và xuống dòng, cột Thao tác dùng nút nhỏ `btn-xs`; thanh công cụ xuống hai hàng khi hẹp. Tương phản (NFR-USE-004): chỉ dùng lớp và biến CSS của Desk, không mã màu cứng.

## Workspace
Không thêm lối tắt: màn hình nằm trong form văn bản (đã có "Văn bản pháp lý" từ FEAT-020).
