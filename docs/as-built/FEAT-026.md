# As-Built: FEAT-026 Kho giá tham chiếu và chỉ số giá
- Phiên bản app 0.0.1; Dev: NORM-80; nghiệm thu: QA (Multica), `docs/features/FEAT-026/acceptance.md`

## 1. Luồng nghiệp vụ đã xây
- **FR-BM-001.** NC Finance, NC Consultant tạo đơn vị tham chiếu: tên, tỉnh/thành phố, loại hình (Công lập/Tư nhân), hạng hoặc cấp chuyên môn, cả bốn bắt buộc. Đặt tên theo tên đơn vị (ASM-026-01).
- **FR-BM-002, FR-BM-004 (UC-013 bước 2–4).** Nhập giá bằng form hoặc bộ nhập Excel `nc_benchmark_price` (khung FEAT-004). Cần đơn vị, giá, loại giá, ngày hiệu lực, dịch vụ (mã hoặc tên gốc) và nguồn (số văn bản, đường dẫn hoặc tệp). Dòng chỉ có tên gốc: hệ thống đề xuất dịch vụ khớp bằng quy tắc so khớp tên (không dùng AI), trạng thái "Đề xuất". Dòng người dùng tự gắn mã: "Đã xác nhận" ngay (ASM-026-02, đổi được bằng hằng `CONFIRM_CODED_ROWS`). Người dùng xác nhận, loại bỏ, mở lại từng dòng hoặc hàng loạt.
- **FR-BM-005.** `api.benchmark.get_comparable_prices(technical_service, price_category, target_month)` chỉ trả dòng "Đã xác nhận", kèm thông tin đơn vị và giá hiệu chỉnh. Màn hình so sánh thuộc FEAT-028.
- **FR-BM-006 (UC-013 bước 5).** NC CPI Index theo tháng (đưa về ngày 1, duy nhất theo tháng). Giá hiệu chỉnh theo BR-ADJ-009 tính khi đọc, không lưu: giá × chỉ số tháng tính giá ÷ chỉ số tháng hiệu lực, `Decimal`, 2 chữ số, `ROUND_HALF_UP` (ASM-026-08; `docs/golden/` không có hàm cho BR-ADJ-009). Thiếu chỉ số thì không hiệu chỉnh và nêu tháng thiếu. 200.000 × 104 ÷ 100 = 208.000,00 (TC-BM-04).
- **FR-BM-007 (UC-013 2b).** Dòng trùng đơn vị, dịch vụ (cùng mã hoặc cùng tên gốc sau chuẩn hóa), loại giá, ngày hiệu lực bị từ chối ở form, API và bộ nhập (báo lỗi theo dòng, không cập nhật đè). Dòng "Loại bỏ" không tính trùng (ASM-026-06).
- **FR-BM-008 (UC-013 1a).** Từ form đơn vị: "Lập phiếu khảo sát giá" theo chuyên khoa hoặc danh sách dịch vụ → tệp `.xlsx`; tờ 1 có đúng cột của bộ nhập (điền xong nhập lại được), tờ 2 thông tin phiếu. Mẫu `exports/templates/phu_luc_i.xlsx` thay được (TBD-01, ASM-026-10).

## 2. DocType tạo mới hoặc thay đổi
Ba DocType mới, module NC Benchmark: NC Benchmark Facility, NC Benchmark Price, NC CPI Index. Trường đúng `data-model.md`; thêm trường bố cục/HTML `adjusted_html` và các Section/Column Break. **NC Benchmark Price đã có** nên TC-AI-07 phần "giá tham chiếu bằng tay" (ASM-023-16, FEAT-023) có thể chạy; FEAT này không sửa test FEAT-023. NC Benchmark Price và NC CPI Index đã nằm trong `FORBIDDEN_DOCTYPES` của `ai/guard.py`, giữ nguyên. Chưa lên staging nên không cần patch.

## 3. API, hook, khung nhập
- `api/benchmark.py`: `confirm_prices`, `reject_prices`, `reopen_prices`, `get_comparable_prices`, `get_adjusted_price`, `download_price_survey` (whitelist, kiểm quyền); `prepare_benchmark_price` (chỉ khung nhập gọi).
- `benchmark/reference.py` (thuần), `exports/price_survey.py` (thuần). Độ phủ `normcore/benchmark/` 100%.
- Hợp đồng cho **FEAT-027** (AI trích PDF): tạo dòng bằng `NC Benchmark Price` với `ai_log` đặt thì `before_insert` giữ "Đề xuất"; `flags.keep_status = True` cũng giữ "Đề xuất".
- Hợp đồng cho **FEAT-028**: dùng `get_comparable_prices`.
- Bộ nhập `nc_benchmark_price` ở `core/import_sets.py`. Sửa tối thiểu khung nhập (`core/importer.py`: `key_of`, `parse` dùng `values.get`) để khóa ghép có thành phần tùy chọn (ASM-026-13). Hành vi cũ không đổi.
- Chặn xóa đơn vị còn giá: `core/delete_guard/nc_benchmark_facility.json`.
- Giao diện: `nc_benchmark_price_list.js`, `nc_benchmark_price.js`, `nc_benchmark_facility.js`, `nc_cpi_index_list.js`; bản dịch `translations/vi.d/FEAT-026.csv`; lối tắt `shortcuts.d/FEAT-026.txt`.
- Ma trận quyền: `scripts/conventions/perm_matrix/` ba tệp (dòng "Giá tham chiếu, chỉ số giá").

## 4. Quyền
Dòng "Giá tham chiếu, chỉ số giá" (data-model mục 4): NC Finance, NC Consultant đọc/tạo/sửa; NC Department Head, NC Director, NC Admin, NC Auditor chỉ đọc; các vai khác không có quyền. Không ai xóa. `confirm_prices`, `reject_prices`, `reopen_prices` cần quyền ghi từng dòng; `download_price_survey` cần quyền tạo giá.

## 5. Cấu hình cần thiết khi triển khai
Không. Mẫu Excel: dòng ví dụ dùng đơn vị "Bệnh viện mẫu", dịch vụ "VD-DV01", loại giá "VD-LG01"; cần tạo các bản ghi này trước khi nhập đúng dòng ví dụ (như các bộ nhập Link khác). Nguồn chỉ số giá nhập tay (TBD-11).

## 6. Test case đã chạy và kết quả
TC-BM-01, 02, 03, 04, 06: xanh (xem `docs/rtm-testref/FEAT-026.md` và `implementation-log.md`). Không gọi AI.

## 7. Giới hạn đã biết
- ASM-026-01..13 (`docs/decisions/assumptions/FEAT-026.md`). Mẫu Phụ lục I là cấu trúc giả định (TBD-01); đổi mẫu chỉ cần thay tệp template và `INFO_LABELS`.
- Trùng trong cùng tệp sau chuẩn hóa tên: ở chế độ "Kiểm tra" chưa báo, chế độ "Ghi" từ chối dòng sau.
- So khớp tên bằng Jaccard có thể đề xuất sai khi tên ngắn; bắt buộc xác nhận trước khi so sánh.
- Giao diện chưa kiểm bằng trình duyệt trong lượt Dev (chỉ test tĩnh và build).
