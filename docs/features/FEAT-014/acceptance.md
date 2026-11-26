# FEAT-014 — Acceptance (QA: Tester iu)

Commit đã kiểm: `d8ca627` (PR #56, CI xanh). **Verdict: accepted.**

| Tiêu chí | Bằng chứng | Kết quả |
| :-- | :-- | :-- |
| Chạy lại toàn bộ trên site sạch | `with_bench.sh` new-site + `run-tests --app normcore` → 1536 test OK, site đã xóa | Đạt |
| pytest unit + golden + độ phủ | 842 passed, độ phủ `costing`+`benchmark` 99% | Đạt |
| check_conventions, build_rtm | exit 0; VAN DE: 0 | Đạt |
| CI PR | 2 job pass trên `d8ca627` | Đạt |
| Diff test không xóa/skip/nới; tài liệu chỉ đọc không đổi | `git diff origin/develop...HEAD` | Đạt |
| TC-TS-01..05, TC-ADM-03 (bấm giờ) | Test cùng mã nằm trong bộ 1536 test OK | Đạt |
| TC-NFR-05: 768 px không cuộn ngang | Clinician: `scrollWidth` 753 ≤ 768 (form mới và đã lưu), bảng `lines` ẩn | Đạt |
| TC-NFR-05: ca 6 bước ≤ 3 lần chạm/bước | 1 / 3 / 2 / 3 / 2 / 2 (Enter đi qua cả ô Số người); không cuộn ngang suốt ca | Đạt |
| Phiếu mới chỉ chọn Dịch vụ + Khoa lưu được | `BG-THU-DV01-K01-0003` lưu, nạp 6 bước | Đạt |
| NC Norm Set mở sau phiếu bấm giờ: `lines` hiện | `display: block` | Đạt |
| SCR-DSK-015 1366 × 768 | `scrollWidth` 1351, `lines` hiện | Đạt |
| SCR-DSK-016 mở được (sau sửa quyền report) | Clinician và Auditor đều xem được; 3 ca → "Số ca 3 / tối thiểu 5", trung vị 21,00 (nhân lực) và 19,00 (thiết bị) đúng từ 20/21/22 và 18/19/20 | Đạt |
| TC-TS-03 qua giao diện | "Áp vào bộ định mức" → hộp xác nhận "Mới 3 ca, ít hơn mức tối thiểu 5…" | Đạt |
| TC-TS-02 qua giao diện | Xác nhận → "Đã cập nhật 8 dòng", căn cứ các dòng = "Bấm giờ" | Đạt |
| Vai trò Auditor | Xem report; không có nút "Áp vào bộ định mức" | Đạt |

Ảnh: `qa-tc-nfr-05-*`, `qa-SCR-DSK-015-1366`, `qa-SCR-DSK-016-*`, `qa-TC-TS-02/03-*` (đính kèm issue).
Giới hạn: vai trò Clinician khoa khác, Council, Resource Mgr kiểm bằng test tự động, chưa kiểm tay.
