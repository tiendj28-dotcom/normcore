GIAI ĐOẠN: BÁO CÁO CUỐI

Đọc `CLAUDE.md`, mọi `docs/features/*/`, `docs/as-built/`, `docs/decisions/`, `docs/releases/`, `docs/pipeline-health.md`, `.autopilot/run.log`.

Viết `docs/BUILD-REPORT.md` bằng tiếng Việt, mở đầu bằng kết luận một đoạn, rồi:
1. Bảng 39 FEAT: trạng thái (DONE/BLOCKED/chưa làm), số lần làm lại, sha merge, link As-Built.
2. FEAT BLOCKED: nguyên nhân, việc người phải làm để gỡ.
3. Danh sách ASM (giả định tự chọn) — đây là những chỗ bệnh viện/chuyên gia phải xác nhận.
4. Danh sách DEF (lỗi tài liệu) và AMD (sửa thiết kế).
5. Kết quả release R1/R2/R3, E2E, NFR.
6. Cách cài đặt lên một site mới và cấu hình bắt buộc.
7. Việc còn lại trước khi đưa vào sử dụng thật.
Commit lên `develop`.
