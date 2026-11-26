# As-Built FEAT-036 — Tính giá cận lâm sàng

Issue NORM-42. FR: FR-COST-017..025, FR-COST-031, FR-COST-032, FR-CLS-003, FR-CLS-004, FR-QC-004, FR-QC-006, FR-CMP-002..004 (và phần cảnh báo trên lần tính của FR-CMP-006), NFR-REL-003, NFR-CPL-003. UC-012. Màn hình SCR-DSK-022, SCR-DSK-023. TC: TC-CLS-01..15, 37, 38, 51.
Giới hạn: (1) giao diện chưa thao tác bằng trình duyệt (chỉ có test tĩnh `test_costing_cls_ui.py`); (2) TC-CLS-38 chụp ảnh ngay sau khi tính thay cho bước khóa (khóa và lưu `snapshot_file`, `snapshot_hash` là FEAT-018, ASM-036-21); (3) TC-CLS-51 kiểm `ServiceResult.volume` và điểm cắm `allocate` bằng test double; phân bổ cấp 2 và đối soát thật là FEAT-017 (ASM-036-20), kiểm lại khi FEAT-017 xong. Người nghiệm thu: QA (Multica).

## Đã làm
- `normcore/costing/cls.py` (thuần, không phụ thuộc `frappe`): k (BR-CLS-001), kiểm định theo hồ sơ (BR-CLS-011, hai cách phân bổ), chi phí thiết bị theo hình thức có máy và tiêu chí chia (BR-CLS-009, BR-COST-004), linh kiện, điện, năm cấp phát sinh của dòng định mức, nội kiểm, chuẩn máy, ngoại kiểm, bình quân gia quyền (BR-CLS-013), cảnh báo sản lượng thấp (BR-CLS-016), kiểm dữ liệu từng dịch vụ (FR-COST-023). Mọi con số khớp `docs/golden/golden_cls.py` (dòng, k, dịch vụ GLU 42.278,67, biến thể V1–V5, V8).
- `engine.py`: `CostLine` thêm bảy trường cận lâm sàng và `cost_category`; `ServiceInput.paraclinical`; `ServiceResult` thêm `is_paraclinical`, `eqa_cost`, `test_system_costs`; `cost_service` rẽ sang `cls` (ADR-017); `finish_service` dùng `dataclasses.replace`. Dịch vụ thường giữ nguyên.
- `costing/snapshot.py`: dựng, tuần tự hóa chuẩn (sha256), tái lập từ ảnh chụp không đọc CSDL.
- DocType: NC Costing Run (`volume_scenario`, `compliance_allocation_mode`, `run_warnings` — AMD-036-01), NC Service Cost (`is_paraclinical`, `eqa_cost`, `test_system_costs`), NC Service Cost Line (bảy trường), mới NC Test System Cost (bảng con). Chỉ thêm trường nên không cần patch.
- Lớp CSDL: `loader.scope_info` (mục cận lâm sàng theo hệ thống "Đang dùng"), nạp theo lô, `run_warnings` (hồ sơ tuân thủ hết hạn), `capture_snapshot`; `writer` ghi trường mới.
- API `get_run_results` (kịch bản, cách phân bổ, cảnh báo, hệ thống) và `get_explanation` (khối `paraclinical`, "k được tính thế nào", nhãn cấp phát sinh).
- Giao diện: dải cảnh báo lần tính, nhãn "Cận lâm sàng", khối kết quả theo hệ thống (SCR-DSK-022); bảng tổng hợp hệ thống, thẻ k, bảng dòng theo hệ thống với cấp phát sinh, mẫu số, nguồn mẫu số (SCR-DSK-023). Bản dịch ở `vi.d/36-feat-036.csv`.
- Fixture site `tests/cls_fixtures.py::make_cls_golden()` dựng bộ dữ liệu vàng 2A; Qtb 300.000 / 100.000 nhờ hệ thống phụ "Ngừng dùng" (ASM-036-10).

## Khác thiết kế
- Dịch vụ cận lâm sàng có hệ thống "Đang dùng" nhưng không bộ "Đã khóa" gắn hệ thống: đi theo đường FEAT-015 thay vì vào "chưa đủ điều kiện" ngay, để giữ test FEAT-031 (ASM-036-26).
- Dịch vụ chỉ một hệ thống: không kiểm tổng tỷ trọng khai tay (ASM-036-27).
- Dòng EQ-P, EQ-E không sinh khi bằng 0 / thiết bị không khai công suất (golden ghi dòng 0; tổng không đổi). Bảng giải trình GLU: 11 + 9 dòng hệ thống + 1 dòng ngoại kiểm.

## Giả định
ASM-036-01..27 trong `docs/decisions/assumptions/FEAT-036.md`; AMD-036-01 trong `docs/decisions/amendments/AMD-036-01.md`.
