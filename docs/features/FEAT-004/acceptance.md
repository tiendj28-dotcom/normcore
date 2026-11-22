# Acceptance FEAT-004 — Kiểm định độc lập (NORM-14)

Kết luận: **accepted**. Mã và test đạt; giao diện kiểm bằng trình duyệt trên staging (xem mục "Bổ sung giao diện").

## Môi trường kiểm
Nhánh `ai/NORM-14-verify-006-001-004` từ `develop` 98d21fe; site sạch `normcore-verify.test` (đã xóa sau khi kiểm).

| Lệnh | Kết quả |
| :-- | :-- |
| `bench --site normcore-verify.test run-tests --app normcore` | 148 test, OK (147 trước khi QA thêm 1 test) |
| `pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov-fail-under=90` | 69 passed, độ phủ 98,9% |
| `python3 docs/golden/golden_engine.py` / `--no-depr` / `golden_cls.py` | thoát 0, số khớp |
| `python3 scripts/check_conventions.py` | thoát 0 |
| `python3 docs/tools/build_rtm.py docs` | thoát 0, `VAN DE: 0`; 12 ghi chú có sẵn (DEF-001) |
## Độ phủ tiêu chí

| Tiêu chí | Bằng chứng | Đạt |
| :-- | :-- | :-: |
| TC-ADM-02 (tải mẫu có tiêu đề + 1 dòng ví dụ; nhập lại chính tệp tạo bản ghi ví dụ, không lỗi) | `test_TC_ADM_02_tai_mau_roi_nhap_lai_chinh_tep_do`: tiêu đề đúng, 2 dòng; chế độ thử không ghi; ghi tạo 1, nhập lại "không đổi" (0 tạo, 0 sửa, 1 không đổi), tổng số bản ghi +1. Làm trên NC Job Title vì NC Item thuộc FEAT-009 (ASM-026, người duyệt đã chốt) | Đạt (thay DocType) |
| Test lỗi của `importer.py` | 17 test đơn vị `test_FR_ADM_002_*`: thiếu cột, ô bắt buộc trống, sai kiểu (số nguyên, số, ngày, danh sách, 1/0), khóa trùng trong tệp, tệp rỗng, không phải Excel, quá ngưỡng, link không tồn tại, thiếu quyền sửa, số dòng tính cả dòng trống; thông báo cụ thể "Dòng n, cột \"…\": …" | Đạt |
| Vai trò không quyền + NC Auditor | `test_vai_tro_chi_doc_va_auditor_bi_tu_choi`: NC Resource Manager và NC Auditor bị `PermissionError` cả chế độ thử và ghi, danh sách bộ nhập rỗng, không ghi gì. FEAT-004 không thêm DocType | Đạt |
| Trang nhập Excel ở 1366×768, `vi` (SCR-DSK-031) | Không có trình duyệt | **Chưa kiểm** |

## Kiểm trực tiếp (site verify, NC Finance)
Tải mẫu → nhập lại → không tạo trùng (kiểm trong test và chạy tay). Tệp 3 dòng, 1 hợp lệ, 1 thiếu mã, 1 nhóm sai: ghi 1 bản, báo lỗi tiếng Việt: `Dòng 3, cột "Mã chức danh": ô bắt buộc đang để trống` và `Dòng 4, cột "Nhóm": "Sai" không nằm trong danh sách (Bác sĩ, Điều dưỡng, ...)`.

## Soát diff test và tài liệu
- Không có test bị xóa/skip/nới. Commit `1061f4b` chỉ bỏ `import pytest` ở test_importer (chạy được trong `bench run-tests`); `d76f4e3` thêm openpyxl vào CI.
- Không sửa tài liệu chỉ đọc.
- AMD-002 (ux-foundations SCR-DSK-031): đủ vấn đề/phương án/tệp sửa/ảnh hưởng; chỉ một dòng bảng đổi, đúng phạm vi.

## ASM-026..036
Không dòng nào trái FR/TC. ASM-026 (TC-ADM-02 trên NC Job Title) chỉ thay DocType, nội dung TC giữ; FEAT-009 phải thêm `test_TC_ADM_02_mat_hang_*` (đã ghi). ASM-031: nhập lại ô trống không xóa dữ liệu cũ, ASM-034 giới hạn 5 MB/5.000 dòng đồng bộ: gấp thì kiểm lại NFR-PERF-001 khi có dữ liệu thật.

## Việc còn lại (người duyệt tự bấm, 1366×768, `vi`)
Mở trang nhập Excel từ SCR-DSK-031 → chọn bộ nhập → tải mẫu → tải lên chính tệp, bấm kiểm tra → bật "Xác nhận ghi" → ghi; nhập lại → "không đổi"; tải tệp có dòng lỗi → danh sách lỗi theo dòng/cột bằng tiếng Việt, không vỡ bố cục; người dùng chỉ đọc → thông báo không có quyền.

## Bổ sung giao diện (cập nhật sau kiểm tay)
Người duyệt (tiendj28) bấm trên staging `http://112.213.88.40:8100/app/import-excel` và báo **đạt** cho: tệp lỗi (tải tệp mẫu của bộ nhập khác: báo bỏ qua 3 cột lạ, thiếu 2 cột bắt buộc theo dòng/cột bằng tiếng Việt, "Xác nhận ghi" bị khóa; có ảnh chụp trong issue NORM-14), nhập mẫu đúng, nhập lại, quyền chỉ đọc. Ảnh chụp chỉ có bước "tệp có lỗi"; các bước còn lại ghi theo xác nhận bằng lời. Chưa có ảnh ở khung 1366×768; QA không tự kiểm giao diện (không có trình duyệt).
