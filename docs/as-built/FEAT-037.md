# As-Built FEAT-037 — Đối soát vật chất và sản lượng; thiếu dữ liệu; độ nhạy

Issue NORM-46. FR: FR-COST-026..030, FR-OUT-012. BR: BR-CLS-014, BR-CLS-015. UC-023, UC-024. Màn hình SCR-DSK-038, SCR-DSK-039, SCR-DSK-040, phần [1.1] của SCR-DSK-024, SCR-DSK-022, SCR-DSK-023. TC: TC-CLS-16..19, TC-CLS-39, TC-CLS-40.
Giới hạn: (1) giao diện chưa thao tác bằng trình duyệt, chỉ có test tĩnh (`test_physical_reconciliation_ui.py`, `test_sensitivity_ui.py`) và `bench build` đạt; (2) TBD-14 chưa có người chốt: đối soát tính theo lượng nên không phụ thuộc loại chi phí tạm (ASM-037-01); (3) độ nhạy tính lại cả phân bổ như lần tính (ASM-037-14). Người nghiệm thu: QA (Multica).

## Đã làm
- `normcore/costing/reconcile.py` (thuần): `material_quantities` (BR-CLS-014 cho dòng Theo kết quả có/không k, Theo ống mẫu, Theo mẻ, Theo ngày-máy, Theo kỳ, nội kiểm), `material_rows`, `volume_rows` (BR-CLS-015), `needs_explanation`, `lock_blockers` mở rộng (Tài chính, Vật chất chặn; Sản lượng không chặn). Khớp `golden_cls.material_recon` (18.185,56 / 18.800 / 3,27% / 9,07%) và `volume_recon` (1,27% / 3,23%).
- `costing/sensitivity.py` (thuần): giả định sản lượng từng hệ thống, đơn giá một đơn vị mua, hình thức có máy; tính lại từ ảnh chụp bằng `snapshot.recompute`; bảy lỗi giả định. `costing/missing_data.py` (thuần): năm loại thiếu.
- NC Reconciliation Line mở rộng bảy trường (`recon_type`, `department`, `item`, `technical_service`, `calculated_qty`, `actual_qty`, `recon_status`); `cost_center`, `cost_category` chỉ bắt buộc với dòng Tài chính. Patch `backfill_reconciliation_type` (dòng cũ = Tài chính).
- Lớp CSDL: `loader.physical_context`, `writer.physical_values`, `write_physical_reconciliation`; `execute_costing` ghi dòng Vật chất, Sản lượng khi kịch bản là "Thực tế 12 tháng"; `lock_costing` dùng luật chặn mới; `loader.stored_rows` chỉ dòng Tài chính (ảnh chụp, ASM-037-09).
- API `get_physical_reconciliation`, `get_sensitivity_base`, `run_sensitivity` (chỉ đọc); `get_reconciliation`, `get_run_results`, `save_explanation` cập nhật.
- Báo cáo "NC Physical Reconciliation", "NC Missing Data"; trang `sensitivity` (Vue, `public/js/sensitivity/`); nút, dải ở `nc_costing_run.js`, `nc_service_cost.js`, `nc_reconciliation.js`. Bản dịch `vi.d/37-feat-037.csv`.
- Đo `run_sensitivity` trên bộ dữ liệu vàng 2A (GLU, 2 hệ thống): lần đầu 0,13 s, lần có đệm ảnh chụp 0,08 s. Chưa đo trên bộ hiệu năng 500 dịch vụ (TC-COST-14 là bộ dữ liệu dịch vụ thường, không có ảnh chụp cận lâm sàng); lần "Đã tính" mỗi lần thử dựng lại ảnh chụp (đệm 10 phút).

## Khác thiết kế
- Fixture `tests/cls_fixtures.py::make_cls_golden()` thêm số liệu xuất kho khớp lượng tính được (tham số `stock_issue=False` để bỏ) vì FR-COST-029 (Must) chặn khóa lần tính cận lâm sàng không có xuất kho, mà test FEAT-018 `test_TC_CLS_38_khoa_that_tai_lap_tu_anh_chup` khóa lần tính đó; test cũ không sửa (ASM-037-19).
- Báo cáo thiếu dữ liệu nhận một khoa, một dịch vụ trong bộ lọc (không chọn nhiều) ở bản này.

## Giả định
ASM-037-01..19 trong `docs/decisions/assumptions/FEAT-037.md`. Không có AMD, CF, DEF.
