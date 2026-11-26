# FEAT-014 — Acceptance (QA: Tester iu)

Commit đã kiểm: `90cb6b0` (PR #56, đã gộp develop `7663a38`). **Verdict: rework.**

| Tiêu chí | Bằng chứng | Kết quả |
| :-- | :-- | :-- |
| Chạy lại toàn bộ trên site sạch | `with_bench.sh` new-site + `run-tests --app normcore` → 1484 test OK, site đã xóa | Đạt |
| pytest unit + golden + độ phủ | 690 passed, độ phủ 99% (chạy trên `715b9a3`; phần mới gộp từ develop không đổi logic FEAT-014) | Đạt |
| check_conventions, build_rtm | exit 0; VAN DE: 0 | Đạt |
| Diff test: không xóa/skip/nới | Chỉ `test_scope_registry.py` +1 dòng (Lead duyệt) | Đạt |
| Tài liệu chỉ đọc, phạm vi | Không có tệp chỉ đọc bị sửa | Đạt |
| TC-TS-01..05, TC-ADM-03 (phần bấm giờ) | Test cùng mã nằm trong bộ 1484 test OK | Đạt |
| TC-NFR-05 (M): 768 px, không cuộn ngang | Playwright, Clinician `thu-clinician`, viewport 768 × 1024: `document.documentElement.scrollWidth` = **774 > 768**. Thủ phạm: `div.form-grid` của bảng con `lines` (right = 774). Ảnh: `qa-tc-nfr-05-03-form-768.png` (đính kèm issue) | **Không đạt** |
| Thiết kế ui-design 1.1.3: bảng `lines` ẩn dưới 1200 px | Ở 768 px bảng `lines` vẫn hiển thị (`offsetParent` ≠ null) | **Không đạt** |
| Luồng tạo phiếu mới (ui-design 1.3) | Chọn Dịch vụ + Khoa rồi Lưu → Desk chặn "Phiên bản quy trình is required" (`procedure` có `reqd: 1`), nên không thể "lưu để nạp các bước"; phải tự chọn quy trình | **Không đạt** |
| Vùng chạm ô số | Ô trong `entry_panel` cao 44 px | Đạt |
| Đếm ≤ 3 lần chạm / bước, ca 6 bước | Chưa chấm vì lỗi trên; sẽ chấm lại sau khi sửa | Chưa kiểm |
| 1366 × 768 SCR-DSK-015/016 | Chưa kiểm (chờ sửa) | Chưa kiểm |
