# FEAT-031 — Nhật ký hiện thực

| Task | Lệnh | Kết quả | sha |
| :-- | :-- | :-- | :-- |
| T01 | `pytest normcore/tests/unit/test_test_systems.py normcore/tests/unit/test_service_rules.py --cov=normcore/costing --cov-report=term`; `grep -n frappe normcore/costing/test_systems.py normcore/procedure/service_rules.py` | 21 passed; `costing/test_systems.py` phủ 100%; grep không in gì | T01_SHA |
