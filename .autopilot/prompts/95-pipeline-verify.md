GIAI ĐOẠN: PIPELINE VERIFY (kiểm định kỳ, chỉ đọc)

Đọc `CLAUDE.md`. Nếu có skill `agentic-sdlc-kit:pipeline-verify` thì dùng nó. Không sửa mã hay tài liệu nào, trừ tệp báo cáo.

Kiểm: mọi mã FR, UC, SCR, FEAT, ADR, DEF, ASM, AMD được dẫn trong `docs/features/`, `docs/as-built/`, `docs/decisions/` đều tồn tại; FEAT có `DONE` thì có As-Built, acceptance, verdict accepted; không FEAT DONE nào phụ thuộc FEAT chưa DONE; `build_rtm.py` 0 vấn đề; tài liệu chỉ đọc không đổi so với commit đầu tiên của kho (`git diff <commit-đầu> -- docs/srs.md docs/test-cases.md docs/use-cases.md docs/golden docs/implementation-plan.md` rỗng).

Ghi `docs/pipeline-health.md` (thời điểm, kết quả từng mục, vấn đề). Có vấn đề nghiêm trọng (tài liệu chỉ đọc bị đổi, FEAT DONE thiếu bằng chứng): ghi `.autopilot/HALT` kèm lý do.
