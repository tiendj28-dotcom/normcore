# FEAT-001 implementation log
Site kiểm: `norm12.test` (site `normcore.test` dùng chung có DocType của NORM-11 nên không dùng được cho toàn app).

- T01–T08 (commit `cc8f8bd`): `bench --site norm12.test run-tests --app normcore --module normcore.tests.test_feat_001` → `Ran 19 tests ... OK`. Test viết cùng lượt với mã, chưa chạy đỏ riêng trước (ghi trung thực).
- Lần chạy đầu của từng nhóm đỏ rồi sửa: thiếu mã khoa ném `ValidationError` (không phải `MandatoryError`); Select bắt buộc tự điền tùy chọn đầu (ASM-034); thông báo xóa của Frappe chỉ nêu bản ghi đầu tiên (thêm `core/references.py`).
- T09: toàn app lần đầu `110 tests, FAILED (errors=3)` ở `api/test_procedure.py` (Clinician chưa gán khoa, G5). Người duyệt chọn (a) → thêm một dòng `assign_department` vào `setUp` (ASM-026). Sau đó: `Ran 110 tests ... OK`.
- `pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov=normcore/benchmark` → `43 passed`; engine.py 99%.
- `pytest normcore/tests/unit -k TC_ACC_04 -v` → 6 passed. `python3 scripts/check_conventions.py` → thoát 0.
