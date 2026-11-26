# FEAT-023 — Nhật ký hiện thực

Điều chỉnh theo "Quyết định Lead" (NORM-55): ASM-023-04 chặn khi lũy kế > hạn mức (không phải ≥); đã sửa ASM và technical-design.

| Task | Lệnh | Kết quả | Commit |
| :-- | :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_ai_guard.py`; `grep -n "import frappe" normcore/ai/guard.py` | 10 passed (76 subtests); grep không in gì | (xem git log) |
| T02 | `pytest normcore/tests/unit/test_ai_prompts.py`; `grep -n "import frappe" normcore/ai/prompts.py` | 7 passed; grep không in gì | (xem git log) |
| T03 | `pytest normcore/tests/unit/test_ai_providers.py normcore/tests/unit/test_ai_providers_openai.py`; `git diff origin/develop -- normcore/tests/unit/test_ai_providers.py` | 15 passed; diff rỗng | (xem git log) |
| T04 | `python3 scripts/check_conventions.py`; `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --module normcore.nc_ai.doctype.nc_prompt_template.test_nc_prompt_template'` | exit 0; Ran 6 tests OK; sau migrate có 7 bản `*-v1` đang dùng | (xem git log) |
| T05 | `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --module ...nc_ai_settings.test_nc_ai_settings && ... --module ...nc_ai_log.test_nc_ai_log'` | Ran 9 tests OK; Ran 4 tests OK | (xem git log) |
| T06 | `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --module normcore.api.test_ai'` | Ran 6 tests OK | (xem git log) |
| T07 | `python3 scripts/check_conventions.py`; `pytest normcore/tests/unit -k "ui or vi_csv or i18n"`; `scripts/with_bench.sh 'bench --site normcore.test migrate && bench build --app normcore'` | exit 0; 96 passed; build exit 0 (+ node --check các tệp JS). Chuỗi giao diện viết thẳng tiếng Việt trong `__()` như tiền lệ, không thêm dòng vi.csv | (xem git log) |
| T08 | `python3 docs/tools/build_rtm.py docs` | `VAN DE: 0` (rtm.md, verification-report.md chỉ đổi ngày, không commit) | (xem git log) |
| T09 | golden_engine, golden_cls; `pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov=normcore/benchmark --cov-fail-under=90`; `check_conventions.py`; `scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --app normcore'`; `git merge origin/develop` | golden OK; 482 passed, cover 98,64%; conv exit 0; bench Ran 945 tests OK; merge: Already up to date | (xem git log) |

CI lần 2 (NORM-55): job unit thuần của CI chỉ cài pytest, pytest-cov, openpyxl (không jinja2, requests) nên `prompts.py` import jinja2 muộn; test cần jinja2/requests chuyển sang bước test trên site: `nc_prompt_template/test_prompts_render.py`, `nc_ai_settings/test_default_post.py`; test unit giữ phần kiểm lược đồ. Kiểm trong venv sạch chỉ có pytest, pytest-cov, openpyxl: 477 passed, cover 98,64%. Không sửa, bỏ hay nới assertion nào.
