# FEAT-025 — Nhật ký hiện thực

Python dùng để chạy pytest: `~/frappe-bench/env/bin/python -m pytest`. `build_rtm.py` sinh lại `docs/rtm.md`, `docs/verification-report.md`; hai tệp chung này không đưa vào PR (quy tắc tránh conflict 3, 5).

| Task | Lệnh | Kết quả |
| :-- | :-- | :-- |
| T01 | `with_bench 'migrate && run-tests --module normcore.api.test_norm'`; check_conventions.py; build_rtm.py | 32 tests OK; conventions exit 0; VAN DE: 0. Thêm `ai_confidence` (AMD-025-01), áp data-model 3.5 |
| T02 | `pytest test_procedure_consistency.py --cov=normcore.procedure.consistency` | 4 passed, độ phủ 100%; không import frappe |
| T03 | `pytest test_norm_ai_link.py --cov=normcore.norm.ai_link` | 2 passed, độ phủ 100%; không import frappe |
| T04 | with_bench migrate + run-tests test_procedure_consistency + test_nc_prompt_template | 1 test OK; 6 tests OK; test_nc_prompt_template.py không đổi |
