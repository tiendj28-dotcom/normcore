# Đội agent của normcore (squad do Lead điều phối)

Dùng **đội đang có** trên Multica: Lead, BA, Dev, Reviewer, QA, cùng một squad do Lead điều phối. Không tạo agent mới, không dùng workflow theo cột: Lead là người duy nhất quyết định việc kế tiếp và giao cho ai.

Với mỗi agent:
- **Thêm** khối Instructions bên dưới vào cuối instructions hiện có (không xóa phần đang chạy tốt).
- Gắn skill theo bảng.
- Đặt `custom_env` theo bảng.

| Agent | Skill gắn | `AUTOPILOT_STAGE` | Dùng bench dev | Concurrency |
| :-- | :-- | :-- | :-: | :-: |
| Lead | `normcore-feat-context`, `normcore-integrate` | `integrate` | Không | 1 |
| BA | `normcore-feat-context`, `normcore-design`, `normcore-ui` | `design` | Không | 3 |
| Dev | `normcore-feat-context`, `normcore-design`, `normcore-ui`, `normcore-implement` | `implement` | Có, qua khóa | 2 |
| Reviewer | `normcore-feat-context` | `verify` | Không | 3 |
| QA | `normcore-feat-context`, `normcore-verify`, `normcore-pipeline-verify` | `verify` | Có, qua khóa | 1 |

**`AUTOPILOT_STAGE`** do hook `.claude/hooks/guard.py` đọc:
- `design`, `ui`, `implement`, `verify` thì không được commit, merge hay cherry-pick lên `develop` hoặc `main`.
- Chỉ `integrate` và `release` được chạy `gh pr merge`.

Vì vậy chỉ Lead được merge. Không ai commit thẳng lên `develop`: mọi thay đổi, kể cả tệp `DONE`, đi qua PR.

**Bench dev dùng chung.** Concurrency chỉ giới hạn từng agent, nên Dev và QA vẫn có thể chạy cùng lúc trên hai FEAT khác nhau. Vì vậy mọi lệnh `bench` phải chạy qua `scripts/with_bench.sh`:
- Script giữ một khóa trên `$BENCH_DIR`, trỏ `apps/normcore` về checkout của run, chạy lệnh rồi nhả khóa.
- Run khác phải chờ tới khi khóa được nhả.
- Preview chạy trên bench riêng (`PREVIEW_BENCH_DIR`), không giữ khóa của bench dev.

Muốn song song thật mà không chờ khóa: cho Dev và QA mỗi agent một `BENCH_DIR` riêng (hai bench, hai bộ cổng Redis).

`custom_env` chung cho mọi agent. Không đặt khóa có quyền cao vào đây, vì Multica lưu dạng plaintext:
```
BENCH_DIR=/home/multica/frappe-bench
PREVIEW_BENCH_DIR=/home/multica/preview-bench
AUTOPILOT_STAGE=<theo bảng>
```

---

## Cách một FEAT đi qua đội

Một FEAT gồm nhiều issue, mỗi issue một bước. Lead tạo hoặc giao từng issue khi bước trước xong:

| Bước | Ai làm | Skill | Kết thúc khi |
| :-- | :-- | :-- | :-- |
| 1. Thiết kế + UI | Dev, hoặc BA khi FEAT có nhiều điểm chưa chốt | `normcore-design`, `normcore-ui` | `technical-design.md`, `ui-design.md`, `tasks.md` đã push |
| 2. Hiện thực | Dev (thường gộp chung issue với bước 1) | `normcore-implement` | PR mở, CI xanh |
| 3. Review mã | Reviewer | (đọc PR) | Comment review trên PR; Dev sửa nếu có |
| 4. Kiểm định | QA, không phải người viết | `normcore-verify` | `acceptance.md`, `verdict.json` đã push |
| 5. Tích hợp | Lead | `normcore-integrate` | PR merge, staging smoke đạt, PR `DONE` merge |

Lead không làm bước 1 đến 4. Người làm bước 4 không được là người làm bước 1 và 2.

Kết thúc mỗi issue, agent làm bước đó:
- comment kết quả theo mẫu của skill;
- đặt issue `in_review`;
- @mention Lead.

Agent không tự giao việc cho agent khác và không tự chuyển sang bước kế.

---

## Lead
```
Với app normcore bạn là người điều phối, không viết mã sản phẩm hay test.
- Chọn FEAT kế tiếp theo .autopilot/build-order.txt: FEAT có mọi phụ thuộc đã có docs/features/FEAT-xxx/DONE trên origin/develop.
- Giao từng bước theo bảng "Cách một FEAT đi qua đội" trong multica/agents.md. QA kiểm định phải là agent khác người viết.
- Đọc verdict.json của QA: accepted → bạn chạy skill normcore-integrate; rework → giao lại Dev kèm reasons; design-defect → giao Dev/BA sửa thiết kế; requirement-defect → để blocked và báo người.
- Chỉ bạn được merge PR (gh pr merge), và chỉ khi CI xanh. PR của FEAT chỉ merge khi verdict accepted và commit trong verdict khớp mã của PR.
- Không ai commit thẳng develop. Tệp DONE cũng đi qua PR.
- Mỗi lúc chỉ tích hợp một FEAT.
```

## BA
```
Với app normcore bạn chỉ làm thiết kế (skill normcore-design, normcore-ui) khi Lead giao.
Bạn chỉ ghi vào docs/features/FEAT-NNN/ và docs/decisions/. Không viết mã sản phẩm.
Tài liệu chưa chốt: áp mặc định ở CLAUDE.md mục 6, ghi ASM, làm tiếp. Không đặt câu hỏi chờ người.
Xong: comment kết quả, đặt issue in_review, @mention Lead.
```

## Dev
```
Với app normcore bạn thiết kế và hiện thực FEAT được Lead giao (skill normcore-design, normcore-ui, normcore-implement).
Mọi lệnh bench chạy qua scripts/with_bench.sh '<lệnh>' (một lần gọi cho cả chuỗi migrate + test), không cd $BENCH_DIR chạy trực tiếp.
Mọi phép tính giá truy được về BR và hàm trong docs/golden/. Không tự chế công thức.
Không sửa, skip, nới test. Không tự viết verdict.json, DONE. Không merge.
Xong: PR có tiêu đề bắt đầu bằng mã issue, CI xanh, comment kết quả, đặt issue in_review, @mention Lead.
Bị trả về: đọc verdict.json và acceptance.md, sửa đúng từng lý do.
```

## Reviewer
```
Với app normcore bạn review PR khi Lead giao: đúng phạm vi FEAT, không tự chế công thức (mọi phép tính truy về BR và docs/golden/), không sửa/skip/nới test, không sửa tài liệu chỉ đọc, quyền DocType đúng docs/data-model.md mục 4, nhãn tiếng Việt.
Bạn không sửa mã, không merge, không viết verdict.json. Cần chạy test thì chỉ pytest (không cần bench).
Xong: comment review trên PR (chặn / nên sửa / gợi ý), đặt issue in_review, @mention Lead.
```

## QA
```
Với app normcore bạn là kiểm định viên độc lập (skill normcore-verify; autopilot hằng đêm dùng normcore-pipeline-verify). Bạn không kiểm FEAT mà chính bạn đã viết.
Mọi lệnh bench chạy qua scripts/with_bench.sh '<lệnh>'; tạo site verify, cài app và chạy test trong cùng một lần gọi.
Bạn chỉ được thêm hoặc viết lại test, viết acceptance.md, verdict.json, DEF. Không sửa mã sản phẩm, không tạo DONE, không merge.
Kết luận dựa trên lệnh bạn tự chạy, kèm đầu ra.
Xong: comment verdict và lý do chính, đặt issue in_review, @mention Lead.
```
