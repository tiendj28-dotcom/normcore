# Nghiệm thu FEAT-037 — Đối soát vật chất và sản lượng; thiếu dữ liệu; độ nhạy

Commit đã kiểm: `960fc88`. Người kiểm: Tester iu (QA, không viết FEAT này).

| Tiêu chí | Bằng chứng | Kết quả |
| :-- | :-- | :-- |
| TC-CLS-16 (V6, xuất 94 hộp: 18.185,56; 18.800; 3,27%) | `test_reconcile_cls_golden.py::test_TC_CLS_16`, `test_nc_costing_physical.py::test_TC_CLS_16` | Đạt |
| TC-CLS-17 (V6, 100 hộp, 9,07% Vượt ngưỡng, từ chối khóa, khóa sau giải trình) | `test_TC_CLS_17` (golden, unit, DocType) | Đạt |
| TC-CLS-18 (V7: 1,27% không cảnh báo; 3,23% cảnh báo; không chặn khóa) | `test_TC_CLS_18_V7_san_luong`, `test_TC_CLS_18_canh_bao_san_luong_khong_chan_khoa` | Đạt |
| TC-CLS-19 (chưa đối soát vật chất, khóa sau xác nhận) | `test_TC_CLS_19_chua_doi_soat_vat_chat` | Đạt |
| TC-CLS-39 (báo cáo thiếu dữ liệu đúng ba dịch vụ, đúng loại) | `test_nc_missing_data.py::test_TC_CLS_39` | Đạt |
| TC-CLS-40 (độ nhạy GLU, Qbn 6.000, không ghi dữ liệu) | `test_sensitivity.py`, `api/test_costing_sensitivity.py::test_TC_CLS_40` | Đạt |
| Chạy lại site sạch `normcore-verify.test` (new-site, install-app, run-tests, drop-site) | 1845 test OK, rc=0, mã `960fc88` | Đạt |
| pytest unit + golden + độ phủ | 1126 passed; costing tổng 99% (sensitivity 96%) | Đạt |
| golden_engine / golden_cls, build_rtm, check_conventions | chạy được; Must chưa có TC: 0; check_conventions rc=0 | Đạt |
| Soát diff test | Không test bị xóa/skip/nới (chỉ đổi dòng `make_cls_golden` trong fixture, mở rộng) | Đạt |
| Tài liệu chỉ đọc | Diff không chạm docs/golden, srs, test-cases, use-cases, implementation-plan, CLAUDE.md, .claude, .autopilot, .github | Đạt |
| CI PR #73 | Hai job pass (Test trên site Frappe, Tài liệu/golden/unit) | Đạt |

Ghi chú: kiểm giao diện bằng trình duyệt chưa thực hiện được vì staging chưa có nhánh này; bao phủ qua test API/DocType/query_report.run trong bộ test bench. TBD-14: Dev ghi ASM-037 trong `docs/decisions/assumptions/FEAT-037.md`.

## Cập nhật 2026-11-27: kiểm lại trên HEAD `960fc88`
Từ `70b0e1e` nhánh chỉ gộp thêm develop (FEAT-019); tệp của FEAT-037 không đổi. Chạy lại: site sạch `normcore-verify.test` 1894 test OK (rc=0, site đã xóa); pytest unit+golden 1126 passed, độ phủ costing 99%; check_conventions rc=0; CI PR #73 hai job pass. Verdict giữ `accepted`.
