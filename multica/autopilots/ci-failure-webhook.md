# Autopilot: CI đỏ trên develop

Tự tạo issue cho Engineer khi workflow CI hoặc deploy-staging thất bại trên `develop`.

| Trường | Giá trị |
| :-- | :-- |
| Name | CI đỏ trên develop |
| Assignee | Normcore Engineer |
| Project | Normcore R1 |
| Execution mode | Create issue (payload được nối vào mô tả issue) |
| Trigger | Webhook |

## Bộ lọc sự kiện (Edit webhook → Add rule, hoặc `--event-filters-file`)
Lưu thành `ci-failure-filter.json` cạnh tệp này. Chỉ nhận `workflow_run` đã chạy xong, thất bại, trên nhánh `develop`:
```json
[
  {
    "event": "workflow_run",
    "actions": ["completed"],
    "conditions": [
      { "path": "workflow_run.conclusion", "op": "equals", "value": "failure" },
      { "path": "workflow_run.head_branch", "op": "equals", "value": "develop" }
    ]
  }
]
```

## Nối GitHub vào webhook
1. Tạo trigger webhook trong autopilot, copy URL (đừng dán URL lên issue, repo hay ảnh chụp: token nằm trong URL).
2. GitHub `mvl26/normcore` → Settings → Webhooks → Add webhook: Payload URL = URL trên, Content type `application/json`, chọn **Let me select individual events → Workflow runs**.
3. Multica khử trùng theo `X-GitHub-Delivery`, nên GitHub gửi lại cũng không tạo hai issue.

## Runbook
```
Mục tiêu: đưa develop về xanh.
Payload trong mô tả issue là sự kiện workflow_run của GitHub: đọc workflow_run.name, head_sha, html_url.
Bước:
1. gh run view <run-id> --log-failed để xem bước lỗi.
2. Phân loại: lỗi môi trường/hạ tầng CI, hay lỗi mã do commit gần nhất.
3. Lỗi mã: tìm FEAT gây ra (git log), sửa trên nhánh fix/ci-<sha ngắn>, mở PR vào develop. Tiêu đề PR bắt đầu bằng mã issue này.
4. Lỗi hạ tầng: sửa .github/workflows trong phạm vi tối thiểu, không bỏ bước kiểm nào.
Ràng buộc: CLAUDE.md mục 3. Không sửa, skip hay nới test để cho xanh. Không push thẳng develop.
Kết thúc: comment nguyên nhân, cách sửa, link PR; chuyển issue sang in_review.
```
