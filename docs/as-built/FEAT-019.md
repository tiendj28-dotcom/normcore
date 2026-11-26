# As-Built: FEAT-019 Xuất biểu Thông tư 21, bảng giải trình, bộ định mức

Issue NORM-48. FR-OUT-001..006, 008, 009; FR-AUD-004; NFR-CPL-002. UC-016. SCR-DSK-028. TC-OUT-01, 02, 03, 04. Người nghiệm thu: QA (Multica).

## 1. Luồng nghiệp vụ đã xây
1. **Hộp thoại "Xuất hồ sơ" (SCR-DSK-028)** mở từ form NC Costing Run ("Đã khóa"), NC Service Cost, NC Norm Set; lưới định mức có thêm nút "Xuất PDF".
2. **Phụ lục II, III, IV, V** (Excel) từ lần tính giá "Đã khóa": II mỗi dịch vụ một trang tính (cơ cấu I–VII); III một dòng/dịch vụ, năm yếu tố; IV mỗi dịch vụ một khối với các dòng phân bổ; V danh mục đề nghị định giá. Dịch vụ "Lỗi" bị bỏ ở II–IV và nêu ở trang thông tin, ở V để trống giá kèm "Tính lỗi: …".
3. **Bảng giải trình PDF** nhóm theo cấu phần rồi bước, phần phân bổ, cơ cấu, tổng (287.745,46 cho DV-TEST-A).
4. **Bộ định mức** Excel (FEAT-034, thêm trang thông tin và nhật ký) và PDF (nhóm theo bước, căn cứ, người xác nhận).
5. **Hồ sơ nén** chạy nền (`queue=long`): Phụ lục II–V, mọi giải trình PDF, mọi bộ định mức (xlsx + pdf), `thong-tin-xuat.txt`; File private gắn lần tính; thông báo và sự kiện realtime khi xong hoặc lỗi.
6. Mọi tệp có **trang thông tin** (mã lần tính, bộ tham số, thời điểm, người xuất) và chân trang; mỗi lần xuất thành công ghi một NC Audit Event "Xuất tệp".

## 2. DocType
Không DocType mới, không đổi quyền. Quyền xuất = quyền đọc bản ghi nguồn (ASM-019-04, 019-15).

## 3. Mã
- Thuần (`normcore/exports/`): `meta.py`, `annex.py` (hằng cột, 4 tệp mẫu `templates/phu_luc_*.xlsx`), `explanation.py`, `bundle.py`, `norm_set.py` (mở rộng `build_workbook(data, meta)`, `pdf_context`); mẫu Jinja `service_explanation.html`, `norm_set.html`.
- API: `api/export.py` (`get_export_options`, `export_file`, `export_bundle`, `build_bundle`); `api/norm.py::export_norm_set` thêm trang thông tin và nhật ký; `core/audit.py::log_export(user=)`.
- Giao diện: `public/js/export_dialog.js` (nạp qua `hook_registry/FEAT-019.json`), nút ở `nc_costing_run.js`, `nc_service_cost.js`, `nc_norm_set.js`, `NormGrid.vue`; bản dịch `vi.d/FEAT-019.csv`.

## 4. Hiệu năng
`build_bundle` trên dữ liệu `test_costing_perf` (500 dịch vụ, đo một lần): 104,3 s với PDF giả (Excel, HTML, nén); một PDF giải trình thật 0,60 s nên ước tính toàn bộ ≈ 400 s, dưới `timeout=1500`.

## 5. Test case đã chạy
Xem `docs/rtm-testref/FEAT-019.md` và `implementation-log.md`.

## 6. Giới hạn đã biết
- **TBD-01:** cấu trúc cột Phụ lục II–V là mẫu tạm (ASM-019-01); mọi tệp Phụ lục ghi "Giả định — chờ xác nhận". Khi có mẫu chính thức thay tệp `.xlsx` và hằng trong `annex.py`.
- Phụ lục I (FEAT-026), bảng so sánh giá (FEAT-027/028) và điểm vào từ phương án giá (R3) chưa có.
- PDF chỉ kiểm chữ ký `%PDF` và HTML sinh ra; chưa kiểm bố cục bằng mắt, chưa kiểm giao diện trên trình duyệt.
