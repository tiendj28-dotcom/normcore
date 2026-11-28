# Nghiệm thu NORM-91: preview_env.sh cập nhật normcore.pth

Commit kiểm: `9c2fa38` (nhánh `fix/NORM-91-preview-pth`, PR #93 vào `develop`). Hạ tầng kiểm thử, không có FEAT/TC/giao diện.

| Kiểm | Kết quả |
|---|---|
| Diff chỉ gồm `scripts/preview_env.sh`, `scripts/tests/test_norm91_preview_pth.py` | Đạt |
| `bash -n scripts/preview_env.sh` | Đạt |
| 2 test của PR | Đạt |
| `multica env start preview` từ checkout mới, khi `normcore.pth` đang trỏ checkout cũ | Đạt |

Tái hiện thực: log ghi `normcore.pth: .../norm-86-55ad539b2351/workdir/normcore -> .../norm-91-73d846a2adf4/workdir/normcore`. `bench migrate` không lỗi `ModuleNotFoundError`, môi trường lên `running` tại `http://localhost:41000/app`, `/api/method/ping` trả 200. Đã `multica env stop preview` sau khi kiểm.

Lưu ý: checkout cũ ở máy này vẫn còn trên đĩa, nên chưa tái hiện được tình huống thư mục cũ đã bị xóa. Cơ chế sửa (ghi lại `.pth` trước migrate) là cùng một đường chạy.

Verdict: accepted.
