# Autopilot: Pipeline verify hằng đêm

| Trường | Giá trị |
| :-- | :-- |
| Name | Pipeline verify hằng đêm |
| Assignee | QA |
| Project | Normcore R1 |
| Execution mode | Create issue |
| Subscribers | bạn |
| Trigger | Schedule, cron `0 2 * * *`, timezone `Asia/Ho_Chi_Minh` |

CLI (sau khi tạo bằng UI hoặc `multica autopilot create`):
```
multica autopilot trigger-add <autopilot-id> --cron "0 2 * * *" --timezone Asia/Ho_Chi_Minh
```

## Runbook (dán vào ô Runbook)
```
Mục tiêu: kiểm sức khỏe truy vết của normcore trên origin/develop mới nhất, không sửa mã.
Dùng skill normcore-pipeline-verify, làm đủ 6 mục kiểm của skill.
Ràng buộc: chỉ ghi docs/pipeline-health.md; không sửa mã, test hay tài liệu nào khác.
Kết thúc: một comment mở đầu bằng "ĐẠT" hoặc "CÓ VẤN ĐỀ", rồi bảng từng mục.
Đạt hết thì chuyển issue sang done; có vấn đề thì để in_review.
```
