# As-Built: FEAT-017 Phân bổ hai cấp và đối soát

Issue NORM-43. FR-COST-004, 005, 008, 009, 014; NFR-PERF-002. UC-012 (bước 4, 5, 7, 8; nhánh 4b, 8b). SCR-DSK-024 (mới), SCR-DSK-022 (bổ sung). TC-COST-02, 03, 05, 08, 10, 14, 16. Người nghiệm thu: QA (chưa làm).

## 1. Luồng nghiệp vụ đã xây
1. "Chạy tính giá" (FEAT-015) nay sau khi tính chi phí trực tiếp thì phân bổ:
   - **Cấp 1 (BR-COST-010):** mỗi trung tâm hỗ trợ, mỗi loại có số kế toán khác 0 được chia một lần cho mọi trung tâm lâm sàng theo quy tắc cấp 1 (HEADCOUNT, AREA, REVENUE từ NC Cost Center Driver; hoặc tiêu chí theo dịch vụ). Nhân tỷ lệ rồi làm tròn 2 số lẻ, đúng thứ tự golden.
   - **Cấp 2 (BR-COST-011):** phần còn lại = max(số kế toán + nhận cấp 1 − Σ chi phí trực tiếp × sản lượng, 0) của (trung tâm lâm sàng, loại), chia theo tiêu chí dịch vụ, trên một ca. Mỗi phần là một dòng "Phân bổ" của NC Service Cost Line (kể cả khi bằng 0).
   - Dịch vụ sản lượng 0 hoặc thiếu: không nhận, không góp tiêu chí, `calc_message` có cảnh báo, giá vẫn tính (FR-COST-014).
   - Dịch vụ "Lỗi" bị bỏ. Khấu hao bị bỏ khi loại giá không kết cấu khấu hao (BR-COST-016).
2. **Đối soát (BR-COST-015):** mỗi (trung tâm lâm sàng, loại, không MANAGEMENT) một NC Reconciliation Line: số đã tính, số kế toán (gồm cấp 1), chênh lệch, %, vượt ngưỡng (> ngưỡng; riêng DRUG_SUPPLY còn < −ngưỡng). Số kế toán 0 mà đã tính > 0: % trống, vượt ngưỡng.
3. NC Finance ghi giải trình (SCR-DSK-024 hoặc form dòng); chỉ khi lần tính "Đã tính".
4. **Khóa:** từ chối khi còn dòng vượt ngưỡng chưa giải trình; đạt thì "Đã khóa" (không tính lại, không sửa giải trình). Chưa có ảnh chụp đầu vào (FEAT-018, ASM-017-07).
5. Tính lại xóa dòng đối soát cũ, giải trình mất theo (ASM-017-08).

## 2. DocType
- Mới: NC Reconciliation Line (độc lập, `hash`, `track_changes`). Chỉ trường bản 1.0. Controller: không tạo tay (`flags.from_costing`), chỉ sửa `explanation`, không xóa tay.
- Mở rộng: NC Costing Run thêm `allocation_warnings` (AMD-017-01, đã áp vào `docs/data-model.md`). NC Service Cost Line không đổi cấu trúc (dòng "Phân bổ" có sẵn trường).

## 3. Mã
- `costing/allocation.py`, `costing/reconcile.py` (thuần, phủ 100%).
- `nc_costing_run/loader.py` (`allocation_context`), `nc_costing_run.py` (`allocate_pools(results, actx)`, `_run`, `execute_costing`, `lock_costing`), `writer.py` (`write_reconciliation`).
- API `normcore/api/costing.py`: `get_reconciliation`, `save_explanation`, `lock_run`; mở rộng `get_run_results` (`has_volume_warning`, `recon_blocked`), `get_explanation`.
- Giao diện: `nc_costing_run.js` (nút Khóa, Bảng đối soát, dải cảnh báo), Script Report "NC Reconciliation", form và list NC Reconciliation Line. Bản dịch ở `normcore/translations/vi.d/FEAT-017.csv`.

## 4. Quyền
Dòng "Lần tính giá, kết quả, đối soát": NC Finance đọc, sửa, tạo; NC Director, NC Admin, NC Auditor chỉ đọc; vai trò khác không có quyền; không ai xóa. Khai ở `scripts/conventions/perm_matrix/nc_reconciliation_line.json` (ASM-017-12).

## 5. Hiệu năng (TC-COST-14)
500 dịch vụ, 50.000 dòng định mức: tính 8,1 s, ghi 37,7 s, tổng 45,8 s (giới hạn 300 s). Chạy nền `queue="long"`, tiến độ tăng dần tới 100. Không cần tối ưu `writer`.

## 6. Test case đã chạy
Xem `docs/rtm-testref/FEAT-017.md` và `implementation-log.md`.

## 7. Giới hạn đã biết
- Thiếu quy tắc hoặc tiêu chí chỉ cảnh báo, không chặn (ASM-017-01). Phạm vi một phần cho giá cao hơn tính toàn viện (ASM-017-03).
- Tiến độ giữ thang 0–100% của FEAT-015 (ASM-017-13).
- Đối soát vật chất, sản lượng (FEAT-037), sản lượng cận lâm sàng (FEAT-036), ảnh chụp đầu vào khi khóa (FEAT-018) chưa có.
- Giao diện chưa kiểm bằng trình duyệt, chỉ kiểm quy ước tĩnh, build và API.
