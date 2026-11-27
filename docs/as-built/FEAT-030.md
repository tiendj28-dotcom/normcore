# As-Built: FEAT-030 Phương án giá, phê duyệt, lịch sử giá
- Phiên bản app 0.0.1, ngày hoàn tất mã 2026-11-27, người nghiệm thu: chờ QA (Multica)

## 1. Luồng nghiệp vụ đã xây
UC-015 bước 1–7, 2a, 7a, 4a, 6a và UC-016 phần bảng so sánh giá. Tài chính lập phương án từ lần tính "Đã khóa" hoặc kịch bản đã tính của lần khóa (nút "Tạo phương án giá" trên NC Costing Run): mỗi dịch vụ một dòng, giá đề xuất mặc định là giá làm tròn của bộ máy (golden 302.100 và 92.600), kèm giá thành toàn bộ, giá tính toán, trung vị và số đơn vị tham chiếu chụp từ thống kê FEAT-028. Sửa giá đề xuất khác giá làm tròn thì phải ghi căn cứ, nếu không "Gửi duyệt" bị từ chối. Gửi duyệt chuyển "Chờ khoa xác nhận" và thông báo trưởng khoa; khi mọi khoa xác nhận thì "Chờ phê duyệt" và thông báo Giám đốc. Dòng dưới giá thành phải được Giám đốc tích xác nhận riêng khi phê duyệt. Loại giá "Bệnh viện": "Đã duyệt", ghi giá và ngày áp dụng vào lịch sử giá từng dịch vụ. Loại giá "Cơ quan có thẩm quyền": "Đã duyệt nội bộ, chờ trình"; sau đó Tài chính ghi số văn bản, ngày, giá được duyệt (lưu cạnh giá đã trình) và lịch sử giá. Từ chối ở cấp khoa hoặc Giám đốc cần lý do, trả về "Nháp", thông báo người lập. Bảng so sánh giá Excel xuất từ hộp thoại "Xuất hồ sơ" (lần tính đã khóa) hoặc từ form phương án giá.

## 2. DocType tạo mới hoặc thay đổi
Mới: NC Price Proposal, NC Price Proposal Item, NC Proposal Dept Confirmation (module NC Benchmark); NC Service Price History (module NC Procedure, bảng con). Thay đổi: NC Technical Service thêm `approved_prices` (chỉ đọc, ghi qua phê duyệt; controller chặn sửa/xóa/thêm tay, ASM-030-15, không cần patch). Trạng thái chỉ đổi qua API; ngoài "Nháp" nội dung bị khóa (DI-07).

## 3. API, tác vụ nền, hook, fixtures
`normcore/api/price_proposal.py`: `create_proposal`, `get_proposal`, `apply_action`, `record_authority_result`, `export_price_comparison`, `write_price_history`, `comparison_data`, `pending_for`. Mở rộng `api/price_compare.py` (`benchmark_summary`), `api/export.py` (loại tệp `price_comparison`), `core/permissions.py` và `core/scope_registry.py` (khóa `child`). Python thuần: `benchmark/proposal.py`, `exports/price_comparison.py`. Workflow "NC Price Proposal" tạo bằng mã (`benchmark/proposal_setup.py`, hook_registry `FEAT-030.json`, ASM-030-03). Giao diện: `nc_price_proposal.js`, `nc_price_proposal_list.js`, nút trong `nc_costing_run.js`, section "Giá đã duyệt" trong `nc_technical_service.js`, dòng trong `export_dialog.js`, shortcut workspace, `translations/vi.d/FEAT-030.csv`.

## 4. Quyền và luồng trạng thái
Theo `perm_matrix/nc_price_proposal.json` (dòng "Gợi ý, kịch bản, phương án giá"): Finance tạo/sửa, Trưởng khoa đọc phương án có dòng của khoa mình và xác nhận/từ chối phần khoa mình, Giám đốc đọc và phê duyệt/từ chối, Consultant, Admin, Auditor chỉ đọc, Clinician không đọc. NC Finance không có quyền xóa (ASM-030-17). Luồng: Nháp → Chờ khoa xác nhận → Chờ phê duyệt → Đã duyệt | Đã duyệt nội bộ, chờ trình → Đã được cấp thẩm quyền duyệt; từ chối về Nháp.

## 5. Cấu hình cần thiết khi triển khai
Loại giá phải khai `approval_authority` (TBD-05). Mỗi NC Department cần `head_user` để nhận thông báo; trưởng khoa cần User Permission theo khoa. Cần giá tham chiếu "Đã xác nhận" (FEAT-026) để có trung vị. Bệnh viện đổi tên trạng thái workflow trên Desk sẽ bị `after_migrate` ghi đè về cấu hình gốc.

## 6. Test case đã chạy và kết quả (mã TC)
TC-PRICE-01..07 và TC-OUT-05 có test cùng mã (xem `docs/rtm-testref/FEAT-030.md` và `implementation-log.md`); kết quả QA ở `acceptance.md`.

## 7. Giới hạn đã biết và nợ kỹ thuật
- Nguồn kịch bản FEAT-029 (ASM-030-01, 19): kịch bản không bị khóa; nếu kịch bản đổi sau khi lập phương án thì "Gửi duyệt" và "Phê duyệt" báo "đã thay đổi", phải lập phương án mới.
- Bảng so sánh giá chưa nằm trong hồ sơ nén (ASM-030-14).
- Trung vị tham chiếu chụp lúc lập phương án, không tự cập nhật (ASM-030-10).
- Lưới "Giá đã duyệt" hiển thị theo thứ tự ghi, không sắp giảm dần ở phía khách.
- Giao diện kiểm bằng test tĩnh và build; chưa có kiểm tay bằng trình duyệt trong tệp này.
