GIAI ĐOẠN: INTEGRATE — {{FEAT}}

Đọc `CLAUDE.md`. Runner đã kiểm `verdict.json` là `accepted` và mã chưa đổi sau lần kiểm. Ở giai đoạn này **không sửa mã sản phẩm hay test**; chỉ được ghi As-Built, RTM, DONE và sửa hạ tầng CI/deploy nếu lỗi môi trường. Giai đoạn này có thể chạy lại nhiều lần: bước nào đã xong thì bỏ qua.

1. Viết `docs/as-built/{{FEAT}}.md` theo mẫu ở `docs/implementation-plan.md` mục 6 (luồng đã xây, DocType mới và ý nghĩa, API, hook, tác vụ nền, fixtures, quyền, cấu hình, TC đã chạy, giới hạn và nợ kỹ thuật, ASM/AMD liên quan). Người nghiệm thu: "Autopilot verify".
2. Ghi cột Test ref cho các FR của {{FEAT}} trong `docs/rtm.md` (tên test thật); chạy `python3 docs/tools/build_rtm.py docs` — 0 vấn đề. Nếu script sinh lại `rtm.md` và xóa cột Test ref, ghi Test ref vào `docs/rtm-testref.md` (FR → test) thay vì sửa tay `rtm.md`.
3. Commit, push. `gh pr create --base develop` (nếu chưa có), `gh pr checks --watch`. CI đỏ: sửa lỗi hạ tầng CI nếu là lỗi môi trường; lỗi mã thì ghi `verdict.json` thành `rework` với lý do và dừng.
4. CI xanh: `gh pr merge --squash --delete-branch`.
5. Đợi workflow deploy staging (`gh run watch`) xanh; chạy smoke test trên staging (`scripts/smoke_staging.sh` nếu có, hoặc gọi API luồng chính của {{FEAT}} qua REST bằng tài khoản smoke). Smoke đỏ: mở lại nhánh sửa, ghi `rework`, dừng.
6. Tạo `docs/features/{{FEAT}}/DONE` (nội dung: sha merge, thời điểm), commit thẳng lên `develop`.
