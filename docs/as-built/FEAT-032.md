# As-Built FEAT-032 — Kế hoạch chất lượng và ngoại kiểm

Issue NORM-35. FR: FR-QC-001..003, FR-QC-005, FR-QC-008 (đủ); FR-QC-007 (một phần); FR-CLS-007, FR-CLS-008 (phần kế hoạch chất lượng). UC-019, SCR-DSK-033, SCR-DSK-034. TC: TC-CLS-24, TC-CLS-25, TC-CLS-26 (một phần).
Giới hạn: TC-CLS-26 mới kiểm hàm cảnh báo, API và thẻ trên SCR-DSK-032; phần gắn cảnh báo vào bộ định mức và kiểm "vẫn khóa được" làm ở FEAT-034 (ASM-032-05). Giao diện chưa xem bằng trình duyệt (chỉ test quy ước tĩnh và `bench build`).

## Đã làm
- DocType mới: NC QC Plan (`KHCL-<hệ thống>`, một kế hoạch mỗi hệ thống — DI-11), NC QC IQC Line, NC QC Calibration Line, NC EQA Program, NC EQA Service. Quyền theo dòng ma trận chung, không ai xóa (ASM-032-01).
- Logic thuần `normcore/costing/qc_plans.py`: kiểm kế hoạch (DI-16, miền giá trị, không lặp), kiểm chương trình ngoại kiểm (DI-12), tỷ lệ hiệu lực, số test ước tính (khớp `golden_cls.py` 154–156: 600, 48, 12), cảnh báo thiếu nội kiểm, thẻ tình trạng. Không có phép tính tiền.
- `core/permissions.py`: `ScopeRule.via` (khoa qua hệ thống xét nghiệm) cho NC QC Plan; NC EQA Program theo `department`.
- `costing/test_systems.py::status_items(qc_plan=None, cls_group=None)`; `api/test_system.py::get_status` có thẻ `qc_plan`.
- API `normcore/api/qc_plan.py`: `estimate_tests`, `missing_iqc_warning`, `eqa_summary`.
- Bộ nhập `nc_qc_plan` (chỉ phần đầu kế hoạch).
- Giao diện: `nc_qc_plan.js`, `nc_eqa_program.js` (+ danh sách), nút "Kế hoạch chất lượng" và thẻ trên `nc_test_system.js`, lối tắt Workspace, `vi.csv`.

## Ghi chú
- ASM-032-01..10 ở `docs/decisions/assumptions/FEAT-032.md`; Lead duyệt thiết kế và các chỗ sửa tệp chung ở bình luận NORM-35.
- Chuẩn `shared_parameter_count` có mặc định 1 nên thiếu trường này trên form không bị Frappe báo thiếu; hàm thuần vẫn từ chối ô trống.
- Không viết patch (ASM-032-09).
