# Workflow "Normcore Delivery"

Tạo trong **Settings → Workflows → New workflow** (bắt đầu từ mẫu *Delivery* rồi sửa cột). Cần quyền owner hoặc admin. Trước đó tạo năm trạng thái tùy biến loại **Started** trong status library: `Design`, `UI`, `Implement`, `Verify`, `Integrate`.

Sau khi lưu: mở project "Normcore R1" → **Workflow** → chọn "Normcore Delivery".

| Cột | Handler | When done, move to | If rejected, send back to | Instructions cho cột |
| :-- | :-- | :-- | :-- | :-- |
| Backlog | No handoff | — | — | Chỗ để FEAT chưa tới lượt. Không agent nào chạy ở đây. |
| Todo | No handoff | — | — | — |
| Design | Normcore Architect | UI | — | `Dùng skill normcore-design cho FEAT trong tiêu đề issue.` |
| UI | Normcore Architect | Implement | Design | `Dùng skill normcore-ui. Thiết kế kỹ thuật thiếu hoặc sai thì trả về Design kèm lý do.` |
| Implement | Normcore Engineer | Verify | Design | `Dùng skill normcore-implement. Nếu verdict.json có lý do rework, sửa đúng các lý do đó.` |
| Verify | Normcore Verifier | Integrate | Implement | `Dùng skill normcore-verify. design-defect thì chuyển sang Design thay vì send-back.` |
| Integrate | Normcore Integrator | Done | Implement | `Dùng skill normcore-integrate.` |
| Blocked | Hand to a member (bạn) | — | — | Chỉ dùng khi có trở ngại thật từ bên ngoài (CLAUDE.md mục 7). |
| Done | No handoff | — | — | — |

Cách chạy một FEAT: tạo issue tiêu đề `FEAT-NNN <tên>` trong project R1, đặt trạng thái **Design**. Architect tự nhận việc; từ đó mỗi cột tự giao cho agent kế.

Ghi chú từ tài liệu Multica:
- Run kết thúc không tự chuyển cột; agent phải tự đổi trạng thái. Khi agent chuyển issue vào cột có handoff, handoff chạy như khi người chuyển.
- Workflow chỉ có một đích "send back". Verifier chuyển thẳng sang Design khi gặp `design-defect`.
- Tạo issue trong project mà không chọn assignee và đặt ở cột có handoff: issue đi thẳng tới agent của cột đó. Muốn tạo trước mà chưa chạy thì để ở **Backlog**.
