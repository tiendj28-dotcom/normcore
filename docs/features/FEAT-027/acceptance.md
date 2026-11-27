# Acceptance FEAT-027 — Trích bảng giá PDF bằng AI (NORM-82)

Commit đã kiểm: `57f41213e0b0af4b47a3bd405ed3958808c020b3` (PR #85). QA: Tester iu.

| Tiêu chí | Bằng chứng | Kết quả |
| :-- | :-- | :-: |
| TC-BM-05 (FR-BM-003): provider giả lập trả 4 dòng từ PDF → 4 dòng "Đề xuất" có `ai_log`, chưa tham gia so sánh | `test_TC_BM_05_trich_bang_gia_pdf_de_xuat`: created=4, status "Đề xuất", ai_log = log (purpose EXTRACT_PRICE_LIST, "Thành công"), không verified_by, source_url có `#page=`, giá [25000, 40000, 90000, 120000], FR-BM-004 khớp AIP-DV-01, `get_comparable_prices` không chứa 4 dòng. Đã đọc assertion, kiểm đúng điều TC yêu cầu | Đạt |
| FR-BM-003 dòng không hợp lệ, trùng, tệp không hợp lệ | `test_FR_BM_003_bo_dong_khong_hop_le_va_trung`, `test_FR_BM_003_tep_khong_hop_le` | Đạt |
| FR-AI-010/011/014 (lỗi AI không tạo dòng; chỉ gửi chữ của tệp; mẫu lệnh, không ghi đè bản Admin) | các test `test_FR_AI_010/011/014_*`, `test_guard_price_list.py`; `FORBIDDEN_DOCTYPES` không đổi (soát diff `ai/guard.py`: chỉ thêm `price_list_pages`) | Đạt |
| FR-AI-015 / UC-013 2c: AI tắt → báo lỗi, nhập tay và Excel vẫn chạy | `test_FR_AI_015_tat_ai_gia_tham_chieu_thu_cong`, `test_FR_AI_015_nut_theo_ai_bat_va_quyen` | Đạt |
| Quyền: vai trò không quyền (Clinical) và NC Auditor bị `PermissionError`, không ghi log; Consultant/Finance chạy; người khác không xem được job | `test_quyen_feat_027` | Đạt |
| Toàn bộ test app trên site sạch `normcore-verify.test` (tạo, cài, chạy, xóa trong một lần gọi có khóa) | `Ran 2053 tests in 576.480s` / `OK` | Đạt |
| pytest unit + golden + độ phủ | 1207 passed, 190 subtests; độ phủ costing+benchmark TOTAL 99% (≥ 90%) | Đạt |
| Golden engine/cls, `check_conventions.py`, `build_rtm.py docs` | chạy không lỗi, không thêm vấn đề (Must chưa có TC: 0) | Đạt |
| Soát diff test | 21 tệp, toàn bộ là thêm mới; không xóa/skip/nới test cũ; không sửa tài liệu chỉ đọc, `.claude`, `.github` | Đạt |
| Phạm vi | chỉ tệp FEAT-027 + mở rộng nhỏ `ai/guard.py`, `ai/prompts_install.py` | Đạt |
| CI PR #85 | `gh pr checks 85`: "Test trên site Frappe v15" pass, "Tài liệu, golden, unit test" pass | Đạt |
| Nhãn tiếng Việt | `translations/vi.d/FEAT-027.csv`, check_conventions đạt | Đạt |

**Giới hạn:** chưa kiểm giao diện SCR-DSK-025 bằng trình duyệt với tài khoản test (không có thông tin đăng nhập vai trò thường); UI được phủ bằng `test_feat_027_ui.py` và test API quyền. Ghi nhận, không chặn.

Verdict: **accepted**.
