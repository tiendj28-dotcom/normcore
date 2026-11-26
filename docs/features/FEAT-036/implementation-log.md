# FEAT-036 — Nhật ký hiện thực

| Task | Lệnh | Kết quả | Commit |
| :-- | :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_costing_cls.py normcore/tests/unit/test_costing_engine.py normcore/tests/unit/test_costing_runner.py`; `python3 docs/tools/build_rtm.py docs` | 45 passed; VAN DE: 0; độ phủ `cls.py` 99% | 32541de |
| T02 | `pytest normcore/tests/golden/test_cls_golden.py`; `python3 docs/golden/golden_cls.py`; `pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov-fail-under=90` | 16 golden passed (TC-CLS-01..14); golden thoát 0; độ phủ 99% | (T02) |
| T03 | `pytest normcore/tests/unit/test_costing_snapshot.py`; lệnh độ phủ T02 | 6 passed; độ phủ ≥ 90% | (T03) |
