# As-Built: NORM-92 dịch tên DocType và Report NC sang tiếng Việt

## 1. Thay đổi
- `normcore/translations/vi.d/NORM-92.csv`: 76 bản dịch tên DocType/Report NC theo data-model, SRS và nhãn lối tắt. Không đổi mã, DocType, quyền.
- Test: `normcore/tests/unit/test_norm92_doctype_labels.py` (đủ bản dịch; nhãn lối tắt khớp bản dịch).

## 2. Giới hạn
- Chưa kiểm bằng trình duyệt; hộp thoại lỗi mặc định của Frappe vẫn tiếng Anh (BA quyết).

Người nghiệm thu: QA (Multica).
