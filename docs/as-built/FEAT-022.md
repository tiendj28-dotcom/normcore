# As-Built: FEAT-022 Ánh xạ hướng dẫn với dịch vụ
- Phiên bản app 0.0.1; Dev: NORM-54; Người nghiệm thu: QA (Multica)

## 1. Luồng nghiệp vụ đã xây
Sau khi lập chỉ mục một văn bản hướng dẫn QTKT, hệ thống tự đề xuất ánh xạ từng mục với dịch vụ kỹ thuật: khớp mã trong tiêu đề → 100%, khớp tên → tối đa 95% (FR-SVC-005). Người có quyền ghi (NC Document Controller, NC Admin) xác nhận từng dòng, các dòng đã chọn, hoặc mọi dòng 100%; sửa dịch vụ, thêm tay, bỏ ánh xạ (FR-SVC-006, UC-003). Chỉ ánh xạ "Đã xác nhận" mới đưa mục vào nguồn gửi AI (FR-SVC-007, TC-SVC-02).

## 2. DocType
- Mới: NC Section Service Map (bảng con: `technical_service`, `mapping_status`, `confidence`, `confirmed_by`, `confirmed_on`).
- NC Legal Section: thêm `mapping_section`, `service_mappings`. NC Legal Document: thêm `mapping_doc_section`, `mapping_html` (chỉ bố cục, không cột CSDL). Không patch, không AMD.

## 3. Mã
- `normcore/library/mapping.py` (thuần): `suggest_for_section`, `merge_suggestions`, `stamp_rows`, hằng số ngưỡng.
- `normcore/nc_library/doctype/nc_legal_section/nc_legal_section.py`: `validate` đóng dấu người/thời điểm xác nhận ở máy chủ.
- `normcore/api/library.py`: `refresh_suggestions`, `suggest_mappings`, `get_mappings`, `confirm_mappings`, `confirm_exact`, `save_mapping`, `remove_mapping`, `get_draft_sources`.
- Giao diện SCR-DSK-004: `nc_legal_document.js`, `nc_legal_section.js`, `vi.csv`.

## 4. Hợp đồng cho FEAT-024
`normcore.api.library.get_draft_sources(technical_service, valid_only=True) -> list[dict]` (không whitelisted): mỗi phần tử là `guard.build_source("NC Legal Section", {name, section_no, heading, plain_text})`, sắp theo số hiệu văn bản rồi số mục, không trùng; chỉ mục có ánh xạ "Đã xác nhận" với dịch vụ và (mặc định) "Còn hiệu lực". FEAT-024 phải gọi hàm này, không tự truy vấn. Đổi chữ ký phải cập nhật tệp này.

## 5. Quyền
Ghi: NC Document Controller, NC Admin. Đọc: theo NC Legal Document. NC Auditor chỉ đọc `get_mappings`; mọi API ghi trả `PermissionError` cho NC Auditor, NC Clinician; người dùng không vai trò NC không đọc được.

## 6. Test và kết quả
Xem `docs/rtm-testref.md` mục FEAT-022 và `docs/features/FEAT-022/implementation-log.md`. TC-SVC-02: `test_TC_SVC_02_chi_muc_da_xac_nhan_vao_nguon_ai` (provider giả lập ghi nguồn, NC AI Log).

## 7. Giới hạn và nợ
- ASM-022-02: ngưỡng khớp tên (50%, tối đa 3 đề xuất) chưa thử trên văn bản hướng dẫn thật (TBD-09). Tiêu đề thật hiếm khi có mã dịch vụ nên phần lớn đề xuất là khớp tên.
- Chỉ dò mã trong tiêu đề, không dùng mã HIS/LIS/RIS.
- Thiếu dòng tóm tắt trên bảng ánh xạ (ASM-022-11). Giao diện chưa được thử bằng trình duyệt thật; QA kiểm trên staging.
- Văn bản đã lập chỉ mục trước FEAT này cần bấm "Đề xuất lại" (ASM-022-08).
- Ánh xạ đã xác nhận được giữ khi nội dung mục đổi sau lập lại chỉ mục; rà soát thuộc FEAT-021/025.
