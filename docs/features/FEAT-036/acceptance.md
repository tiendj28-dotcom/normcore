# Nghiệm thu FEAT-036 — Tính giá cận lâm sàng

Người nghiệm thu: QA (Multica, Tester iu). Commit đã kiểm: `6ccdc05ea5a7132ca4c6a55fa757f48b4c080e6e` (nhánh `feat/FEAT-036-cls-costing`, PR #64).

| Tiêu chí | Bằng chứng (lệnh tự chạy) | Kết quả |
| :-- | :-- | :-- |
| Golden | `python3 docs/golden/golden_engine.py && python3 docs/golden/golden_cls.py` thoát 0 | Đạt |
| Unit + golden + độ phủ | `python -m pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov=normcore/benchmark`: 875 passed; tổng 99%; cls.py 99% (≥ 90%) | Đạt |
| Site sạch, toàn bộ test | `normcore-verify.test` tạo mới, cài app, `run-tests --app normcore`: 1545 tests OK (330s), drop site, qua `scripts/with_bench.sh` | Đạt |
| TC-CLS-01..15, 37, 38, 51 | Mỗi TC có test cùng mã (grep `test_TC_CLS_NN_` đủ 18 mã); các test golden khớp `golden_cls.py`; chạy xanh ở hai lần trên | Đạt |
| Quy ước, RTM | `check_conventions.py` thoát 0; `build_rtm.py docs`: VAN DE: 0 | Đạt |
| Soát diff test | Không dòng test nào bị xóa/đổi (`git diff origin/develop...HEAD -- normcore/tests` không có dòng `-`); không skip/expectedFailure thêm | Đạt |
| Phạm vi | 34 tệp đều thuộc FEAT-036 | Đạt |
| Tài liệu chỉ đọc | Không sửa srs, test-cases, use-cases, golden, implementation-plan, CLAUDE.md, .claude, .autopilot, .github | Đạt |
| CI PR #64 | `gh pr checks 64`: "Test trên site Frappe v15" pass, "Tài liệu, golden, unit test" pass | Đạt |
| Quyền NC Test System Cost | Bảng con, quyền theo DocType cha (NC Costing Run); NC Auditor chỉ đọc (Reviewer đã soát, bộ test quyền toàn site xanh) | Đạt |

## Giới hạn (không chặn nghiệm thu)
1. Giao diện SCR-DSK-022/023 chưa kiểm bằng trình duyệt: mã của PR chưa có trên staging (http://112.213.88.40:8100, chưa merge) nên Playwright không thấy tính năng. Chỉ có test tĩnh `test_costing_cls_ui.py`. Cần kiểm trên staging sau merge (cùng ghi chú Lead về SCR-DSK-014 của FEAT-034).
2. TC-CLS-38 chụp ảnh thay bước khóa (ASM-036-21): kiểm lại bằng khóa thật ở FEAT-018.
3. TC-CLS-51 kiểm bằng test double (ASM-036-20): kiểm lại ở FEAT-017.

Verdict: **accepted**.
