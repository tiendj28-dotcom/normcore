# FEAT-014 — Acceptance (QA: Tester iu)

Commit đã kiểm: `faa65ca` (PR #56, CI xanh). **Verdict: rework** (lần 2).

| Tiêu chí | Bằng chứng | Kết quả |
| :-- | :-- | :-- |
| Chạy lại toàn bộ trên site sạch | Lần trước trên `90cb6b0`: `run-tests --app normcore` 1484 OK, site đã xóa. Lần này chưa chạy lại trên `faa65ca` vì mã sẽ đổi để sửa lỗi dưới; sẽ chạy lại trên HEAD sau sửa | Chưa (chạy lại sau sửa) |
| Dev báo: bench 1532 OK, pytest 842 passed, phủ 98,94%; CI 2 job xanh trên `faa65ca` | CI `gh pr checks 56` | Đạt (CI) |
| Diff test không xóa/skip/nới, không sửa tài liệu chỉ đọc | `git diff origin/develop...HEAD` | Đạt |
| TC-NFR-05 không cuộn ngang ở 768 px | Playwright, Clinician: `scrollWidth` = 753 ≤ 768 trên form mới và form đã lưu; bảng `lines` ẩn. Ảnh `qa-tc-nfr-05-10/11-*-768.png` | Đạt |
| TC-NFR-05 ≤ 3 lần chạm/bước, ca 6 bước | Chạm ô phút bước 1, rồi Enter: bước 1 = 1, bước 2 (BS + thiết bị) = 3, bước 3 = 2, bước 4 (BS + thiết bị) = 3, bước 5 = 2, bước 6 = 2; không cuộn ngang trong suốt. Ghi chú: Enter đi qua cả ô "Số người" (mặc định 1) trước khi tới ô phút, khác ui-design 1.2 ("ô phút kế tiếp") nhưng vẫn ≤ 3. Ảnh `qa-tc-nfr-05-12-entry-768.png` | Đạt |
| Phiếu mới lưu được khi chỉ chọn Dịch vụ + Khoa | `BG-THU-DV01-K01-0003` lưu OK, nạp 6 bước | Đạt |
| NC Norm Set mở sau phiếu bấm giờ: `lines` vẫn hiện | `display: block` ở 768 px (DM-THU-DV01-K01-v1) | Đạt |
| SCR-DSK-015 ở 1366 × 768 | `scrollWidth` 1351, bảng `lines` hiện, 14 ô nhập. Ảnh `qa-SCR-DSK-015-1366.png` | Đạt |
| **SCR-DSK-016 (Kết quả bấm giờ) mở được với Clinician / Auditor** | `frappe.desk.query_report.run` và `/app/query-report/NC Time Study Result` → **403 "You don't have permission to get a report on: NC Time Study"** cho cả `thu-clinician` và `thu-auditor`. Không role nào của DocType NC Time Study có `report: 1` (`nc_time_study.json` permissions), nên Script Report không dùng được | **Không đạt** |
