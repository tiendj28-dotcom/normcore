# As-Built: FEAT-009 Mặt hàng và đơn giá có chứng từ
- Phiên bản app 0.0.1; Dev: NORM-18; người nghiệm thu: QA (Multica), 2026-11-23, commit đã kiểm dc1d8fa

## 1. Luồng nghiệp vụ đã xây
NC Resource Manager, NC Finance tạo mặt hàng (mã, tên, loại, đơn vị tính; số lần dùng mặc định 1; hóa chất, chất chuẩn, vật liệu nội kiểm khai số đơn vị định mức, số test danh nghĩa, hạn dùng sau mở) hoặc nhập tệp Excel mặt hàng, đơn giá (tạo hoặc cập nhật theo mã, dòng lỗi bị bỏ và liệt kê). Thêm đơn giá có chứng từ (nguồn gồm Hợp đồng, hiệu lực từ/đến), đính tệp rồi bấm "Xác minh". Hệ thống chọn đơn giá theo nguồn rồi ngày hiệu lực, cảnh báo quá 24 tháng và chưa xác minh, quy đổi đơn giá một đơn vị định mức, loại mặt hàng thanh toán riêng (hàm thuần cho FEAT-012 dùng).

## 2. DocType tạo mới hoặc thay đổi
Mới: NC Item (`item_code`), NC Item Price (`DG-#####`, thêm `price_code` theo AMD-008), module NC Costing. AMD-008 đã áp vào `data-model.md`.

## 3. API, tác vụ nền, hook, fixtures
`normcore/api/item.py`: `get_effective_price`, `verify_price`, `get_equivalent_items`. Hàm thuần `normcore/costing/pricing.py`: `select_price`, `price_warnings`, `unit_price_per_norm`, `material_line`. Bộ nhập `nc_item`, `nc_item_price` ở `core/import_sets.py`. JS: `nc_item.js`, `nc_item_price.js`, `nc_item_price_list.js`; bản dịch `vi.csv`. Không hook, không fixture.

## 4. Quyền và luồng trạng thái
Dòng "Mặt hàng, đơn giá": Finance, Resource Manager, Admin ghi; Clinician, Dept Head, Director, Consultant, Auditor đọc; Council, Document Controller không có quyền; không ai xóa. Xác minh: Chưa xác minh ↔ Đã xác minh, cần tệp chứng từ, người và thời điểm do hệ thống ghi; đang Đã xác minh thì khóa nội dung (phải bỏ xác minh trước).

## 5. Cấu hình cần thiết khi triển khai
`bench migrate`; `bench build --app normcore`. Không patch.

## 6. Test case đã chạy và kết quả
TC-RES-01, 02, 07, 08, 09, TC-CLS-45, 46, 47, TC-ADM-02 (mặt hàng): đều xanh. QA chạy lại trên site sạch: `run-tests --app normcore` Ran 411 tests OK; pytest unit + golden: 169 passed, độ phủ 98,44%. Chi tiết ở `docs/features/FEAT-009/implementation-log.md`.

## 7. Giới hạn đã biết và nợ kỹ thuật
- FR-RES-013 làm tối thiểu (ASM-089).
- Cảnh báo, lý do loại chưa hiện trên bảng giải trình: **FEAT-015** gọi `material_line` (ASM-087). Hàm chưa có hệ số k, cấp ống, mẻ, ngày, UTILITY (ASM-097).
- Giao diện chưa kiểm bằng trình duyệt (Playwright MCP không kết nối khi QA kiểm); quyền và luồng được kiểm bằng test trên site sạch.
- Test cũ: kỳ vọng danh sách bộ nhập ở `api/test_importer.py` thêm `nc_item`, `nc_item_price`; số DocType ở `test_permissions.py` thành 27 (ASM-096, Lead duyệt).
- Đổi loại mặt hàng (ASM-094): mặt hàng loại khác để trống số đơn vị định mức được lưu là 1; đổi loại sang Hóa chất, Chất chuẩn, Vật liệu nội kiểm rồi lưu **vẫn được** (số đơn vị giữ 1), vì FR-RES-018 chỉ ràng buộc lúc tạo. QA đã thử trên site sạch. Người dùng cần tự sửa số đơn vị khi đổi loại.
