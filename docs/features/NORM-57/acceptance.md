# Nghiệm thu NORM-57 (sửa FR-OUT-010, FEAT-002) — PR #60, head 21c64ec

| Tiêu chí | Bằng chứng | Kết quả |
| :-- | :-- | :-- |
| Test mới mang mã FR-OUT-010 (`TestChainStageRoute`, 2 test), test cũ không bị xóa/skip/nới | `git diff origin/develop...HEAD -- normcore/tests/test_feat_002.py`: chỉ thêm dòng, không có dòng bị xóa | Đạt |
| Chạy toàn bộ trên site sạch `normcore-verify.test` (cài app, run-tests, drop site, một lần gọi with_bench.sh) | Ran 1280 tests, OK | Đạt |
| pytest unit + golden + độ phủ | 666 passed, coverage 98.94% (≥ 90%) | Đạt |
| golden_engine.py, golden_cls.py | chạy bình thường | Đạt |
| check_conventions.py, build_rtm.py docs | exit 0, không lỗi mới | Đạt |
| Phạm vi | 3 tệp: `nc_technical_service_list.js`, `test_feat_002.py`, `docs/as-built/FEAT-002.md`. Không chạm tài liệu chỉ đọc, không sửa `api/home.py` | Đạt |
| CI PR #60 | cả hai job pass (run 45784074240) | Đạt |
| Trình duyệt: liên kết có tham số, đổi khoa/mức, tải lại sau dropdown | Chưa kiểm: staging chỉ chạy develop (chưa có bản vá) và không dựng được môi trường chạy nhánh PR trong lượt này | Chờ, kiểm lại bằng Playwright trên staging sau merge theo quyết định của Lead |
