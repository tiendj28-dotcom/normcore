# As-Built: FEAT-018 Khóa, ảnh chụp đầu vào, so sánh hai lần tính

Issue NORM-47. FR-COST-011, 012, 013; NFR-REL-001. UC-012 (bước 8, nhánh 8a, 8c). SCR-DSK-022 (bổ sung). TC-COST-09, 11, 18 (và TC-CLS-38 với khóa thật). Người nghiệm thu: QA (Multica).

## 1. Luồng nghiệp vụ đã xây
1. **Khóa (FR-COST-011):** sau các kiểm cũ của FEAT-017, hệ thống dựng ảnh chụp toàn bộ đầu vào từ dữ liệu sống trên đúng danh sách dịch vụ đã tính, tính lại từ ảnh chụp và so từng trường với kết quả đã lưu. Trùng hết mới lưu tệp `.json.gz` private gắn lần tính, `snapshot_hash` (sha256 của JSON chuẩn hóa) và chuyển "Đã khóa" (NC Audit Event "Khóa" kèm 12 ký tự đầu mã băm). Đầu vào đã đổi sau lần tính thì từ chối, giữ "Đã tính".
2. **Kiểm tra tái lập (NFR-REL-001):** tính lại từ tệp đã lưu (không đọc dữ liệu sống), so từng trường; tệp sai mã băm hoặc mất thì báo `ok: false`, không raise. Mọi vai trò đọc được (gồm NC Auditor).
3. **Đã khóa (FR-COST-012):** `run_costing` từ chối với câu riêng; mọi sửa và xóa bị từ chối. **Nhân bản** tạo lần tính mới ở "Nháp" với cùng đầu vào và phạm vi, không mang kết quả, đối soát, ảnh chụp (NC Finance).
4. **So sánh (FR-COST-013):** Script Report "So sánh hai lần tính giá" (và API `compare_runs`): chênh lệch = lần so sánh − lần gốc theo dịch vụ và 15–16 cấu phần. DV-TEST-A gốc → V1 = −63.636,36 (thiết bị −47.348,48, hạ tầng −12.500,00, phân bổ khấu hao −3.787,88).

## 2. DocType
Không có DocType mới. NC Costing Run thêm `snapshot_file`, `snapshot_hash` (đã có trong data-model; section "Ảnh chụp đầu vào"), `no_copy` cho `progress`, `allocation_warnings`. Không đổi quyền.

## 3. Mã
- Thuần: `costing/snapshot.py` (lược đồ 2: `pack`, `unpack`, `recompute`, `diff_rows`, khóa map tuple), `costing/compare.py` (mới), `reconcile.depreciation_centers`.
- CSDL: `loader.capture_snapshot` (thêm `allocation`, `meta`), `eligible_from_results`, `stored_rows`; `writer.service_cost_values`, `recon_values`, `expected_rows`, `canonical`; `NCCostingRun.lock_costing`, `verify_snapshot`, `duplicate_run`, `validate`, `on_trash`.
- API: `verify_snapshot`, `duplicate_run`, `compare_runs`, `build_comparison`; `get_run_results` thêm `snapshot_hash`, `can_duplicate`, `can_verify`.
- Giao diện: `nc_costing_run.js`, report `nc_costing_run_comparison`; bản dịch `vi.d/FEAT-018.csv`.

## 4. Hiệu năng
Khóa 500 dịch vụ (dữ liệu `test_costing_perf`, đo một lần): 15,4 s, đồng bộ (ASM-018-11).

## 5. Test case đã chạy
Xem `docs/rtm-testref/FEAT-018.md` và `implementation-log.md`.

## 6. Giới hạn đã biết
- `lock_run` không trả `snapshot_hash` (ASM-018-13); lấy qua `get_run_results`.
- Tệp ảnh chụp bị xóa tay thì `verify_snapshot` báo không tìm thấy; không có hook chặn xóa File (ASM-018-10).
- Đối soát vật chất (FEAT-037) và kịch bản (FEAT-029) chưa vào ảnh chụp.
- Giao diện chưa kiểm bằng trình duyệt, chỉ kiểm quy ước tĩnh, build và API.
