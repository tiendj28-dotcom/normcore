# Nghiệm thu NORM-92: tên DocType và báo cáo NC tiếng Anh dù ngôn ngữ vi

Người nghiệm thu: QA (Multica). Commit đã kiểm: `024c1b60b9f322c6c0f01a1d26709a26993f30d4` (PR #94, nền `36f25b2`).

| Tiêu chí | Bằng chứng | Kết quả |
| :-- | :-- | :-- |
| Có bản dịch tên DocType/Report NC | `vi.d/NORM-92.csv` 76 dòng; Reviewer đối chiếu data-model, SRS, lối tắt `shortcuts.d/` | Đạt |
| Test mới | `python3 -m unittest normcore.tests.unit.test_norm92_doctype_labels`: 2 test OK (gồm khớp nhãn lối tắt với bản dịch) | Đạt |
| Site sạch, bộ test bench | `bench new-site normcore-verify.test` + `run-tests --app normcore` chạy đến hết, rc=0, site đã xóa (chỉ thấy phần cuối log, không có dòng tổng số test) | Đạt (hạn chế) |
| CI PR | cả 2 job SUCCESS ở `024c1b6` (Lint đã xanh sau `ruff format`; site Frappe v15 xanh) | Đạt |
| check_conventions | rc=0 | Đạt |
| Soát diff test, phạm vi, tài liệu chỉ đọc | diff chỉ 2 tệp mới (CSV, test); không xóa/skip/nới test cũ; không chạm tài liệu chỉ đọc | Đạt |

Giới hạn: chưa kiểm bằng trình duyệt (Playwright) vì staging chưa có bản sửa trước merge; hộp thoại lỗi mặc định của Frappe nằm ngoài phạm vi (BA quyết). Chưa chạy pytest cục bộ (máy không có pytest); CI đã chạy unit và golden.
