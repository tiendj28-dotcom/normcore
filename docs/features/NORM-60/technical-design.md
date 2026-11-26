# NORM-60 — Thiết kế kỹ thuật: tách tệp chung theo FEAT, sửa pr-sync

Loại: chore (không thuộc FEAT nào, không có FR/TC). Phạm vi theo Quyết định Lead trên NORM-60 (bình luận 01a21712-f050-7e1a-9e1b-ca0d2576406d): **Phần 1 và Phần 2** của mô tả issue. Phần 3, 4 thuộc NORM-61 (PR #61). Không đổi nghiệp vụ, DocType, công thức, golden. Không có ui-design.

Nhánh `chore/NORM-60-chong-conflict`, một PR, tiêu đề bắt đầu `NORM-60`. Giả định: `docs/decisions/assumptions/NORM-60.md` (`ASM-NORM60-nn`).

## 1. Hiện trạng đã kiểm (develop `879bb6a`)

Đếm trên 25 merge gần nhất của `develop` (`git log --first-parent --merges`, diff `m^1..m`):

| Tệp | Số PR | Vì sao FEAT nào cũng sửa |
|---|:-:|---|
| `docs/rtm-testref.md` | 16 | QA ghi mục `## FEAT-NNN`. **`docs/tools/build_rtm.py` không đọc tệp này** (grep không có `testref`), nên tách ra thư mục không cần sửa `build_rtm.py`. |
| `scripts/check_conventions.py` | 13 | Mỗi DocType mới thêm một dòng vào `DOCTYPE_ROW`, có khi thêm dòng `MATRIX` hoặc `DELETE_ALLOWED` (`38855a4`, `a6dcfe0`, `15705ae`, `9d175ac`, `460b24f`, `d62701c`). Không có lý do nào khác. |
| `normcore/translations/vi.csv` | 13 | Một tệp dịch chung, NC-10 bắt sắp xếp. |
| `normcore/nc_core/workspace/normcore/normcore.json` | 9 | Tệp sinh từ `shortcuts.txt` nhưng vẫn commit; NC-11 đòi khớp từng byte. |
| `normcore/hooks.py` | 8 | Sau NORM-37 còn: `scheduler_events.daily` (FEAT-007, 020, 033), `app_include_js` (FEAT-023, 002), `after_install`/`after_migrate` (NORM-9, FEAT-034 đang mở), `fixtures` (FEAT-007, 002), `jinja`, `boot_session`, `normcore_pending_sources` (mỗi cái 1 FEAT). |
| `normcore/nc_core/workspace/normcore/shortcuts.txt` | 6 | Mỗi FEAT nối thêm dòng lối tắt. |

Frappe v15.127 (bench dev) đọc bản dịch của app **chỉ** từ `<app>/translations/<lang>.csv` (`frappe/translate.py::get_translations_from_csv`) và `.mo` trong `sites/assets/locale`. Thứ tự dòng không quan trọng với Frappe. Workspace được nhập từ `<module>/workspace/<tên>/<tên>.json` trong `sync_for` (install-app) và `sync_all` (migrate); với doctype khác `DocType`, Frappe **bỏ qua tệp nếu `modified` trong tệp không mới hơn bản trong CSDL** (`frappe/modules/import_file.py`, dòng 125–142). Hiện `modified` của `normcore.json` là hằng số trong `build_workspace.py::BASE`, nên FEAT thêm lối tắt mà quên đổi hằng số thì staging (đã có bản ghi) không nhận lối tắt mới: một điểm sửa chung nữa.

Thứ tự hook (đã đọc mã Frappe): `install_app`: `before_install` → `sync_for` (nhập JSON) → `after_install` → `sync_fixtures` → `clear_cache`. `migrate`: `before_migrate` → patch, `sync_all` → `sync_fixtures`… → `after_migrate` → `tearDown` (`frappe.translate.clear_cache()`).

Hai hạn chế đã kiểm:
- `docs/tools/` là chỉ đọc (`.claude/hooks/guard.py` và bước "Tài liệu chỉ đọc" của `ci.yml`). Không sửa được `build_rtm.py`. Không cần sửa vì nó không đọc Test ref (mục 2.3).
- `ci.yml` chỉ chạy `pytest normcore/tests/unit normcore/tests/golden`, không chạy `scripts/tests/` (mục 7, R3).

## 2. Phần 1 — Không còn tệp chung mà mọi FEAT phải sửa

Nguyên tắc chung (đáp ràng buộc 2 của Lead): **tệp kết quả ghép không commit**. Nguồn là thư mục mảnh, mỗi FEAT/issue một tệp; tệp ghép sinh ra lúc cần (install, migrate, pytest, check_conventions) và nằm trong `.gitignore`. Hai nhánh song song chỉ thêm tệp mới khác tên, nên nút Merge của GitHub không thể conflict và không cần commit sinh lại.

Dữ liệu cũ (ràng buộc 4, 5): tệp chung cũ được **`git mv`** nguyên vẹn thành mảnh nền `00-base.*` (giống 100%). Nhờ phát hiện đổi tên của git (merge-ort, cả runner lẫn GitHub), PR cũ còn sửa tệp cũ khi gộp sẽ được áp phần sửa vào `00-base.*`, không mất dòng (mục 4).

Tên mảnh: `00-base.<ext>` (dữ liệu trước NORM-60), `FEAT-NNN.<ext>`, `NORM-NN.<ext>`. Thứ tự ghép: `00-base` trước, rồi theo tên tệp (sắp chuỗi).

### 2.1 Bản dịch `vi.csv`

| Hạng mục | Thiết kế |
|---|---|
| Nguồn | `normcore/translations/vi.d/*.csv`, cùng định dạng CSV của Frappe (2 hoặc 3 cột). Một FEAT một tệp `FEAT-NNN.csv`; không bắt sắp xếp trong mảnh. |
| Dữ liệu cũ | `git mv normcore/translations/vi.csv normcore/translations/vi.d/00-base.csv` (481 dòng, byte giữ nguyên). |
| Tệp ghép | `normcore/translations/vi.csv`, **không commit** (thêm vào `.gitignore`). |
| Luật ghép | Đọc mọi mảnh theo thứ tự trên; bỏ dòng trùng hệt (hai FEAT cùng dịch một chuỗi như nhau là hợp lệ); trùng khóa (cột 1 + ngữ cảnh) khác bản dịch → lỗi NC-09 nêu cả hai tệp, không ghi tệp; sắp bằng đúng `_csv_key` hiện có (cột 1 rồi ngữ cảnh), sort ổn định. Ghi `csv.writer(lineterminator="\n")` như `sort_vi_csv`. |
| Mã | Module thuần mới `normcore/generated.py` (không import `frappe`, chỉ thư viện chuẩn): `merge_translations(root) -> (rows, errors)`, `write_translations(root) -> bool`. |
| Ai sinh, khi nào | (1) Hook `before_install` và `before_migrate` (mục 2.6) → Frappe có `vi.csv` trên site mới, khi migrate, và ở deploy staging (`git reset --hard` xóa `vi.csv` cũ đang được theo dõi, rồi `bench migrate` sinh lại; bước `clear-cache` sau đó xóa bộ đệm). (2) `normcore/tests/conftest.py` (mới) sinh trước phiên pytest, để các test UI hiện đọc `normcore/translations/vi.csv` (`test_ui_conventions.py`, `test_*_ui_conventions.py`…) chạy được mà **không sửa test nào**. (3) Lệnh tay `python3 scripts/build_generated.py` (mới) cho Dev. |
| NC-09/NC-10 | `check_vi_csv(root)`: nếu có thư mục `vi.d/` thì kiểm **kết quả ghép trong bộ nhớ** (NC-09 trùng khóa trong một mảnh hoặc giữa hai mảnh; NC-10 thứ tự của kết quả ghép, và nếu `vi.csv` đang có trên đĩa thì nó phải đúng bằng kết quả ghép, khác thì báo NC-10 "vi.csv cũ, chạy scripts/build_generated.py"). Không có `vi.d/` thì kiểm `vi.csv` như hiện nay (giữ `test_vi_csv_order.py`, `test_pr_sync_fix.py` nguyên vẹn). NC-10 vẫn chạy, chỉ đổi nơi kiểm (AC-5). |

Vì sao không chọn "commit `vi.csv`, CI sinh lại": hai nhánh cùng thêm dòng vào cùng một tệp sắp xếp → GitHub conflict khi hai dòng gần nhau, trái AC-1. Vì sao không dùng `.po`/`.mo`: phải dựng `.mo` lúc `bench build`, đổi cả cách test đọc bản dịch; phức tạp hơn mà không thêm gì.

### 2.2 Workspace (`normcore.json`, `shortcuts.txt`)

| Hạng mục | Thiết kế |
|---|---|
| Nguồn | `normcore/nc_core/workspace/normcore/shortcuts.d/*.txt`, mỗi dòng `id\|nhãn\|link_to\|loại\|doc_view` như `shortcuts.txt` hiện nay (cả `CustomBlock`). |
| Dữ liệu cũ | `git mv .../shortcuts.txt .../shortcuts.d/00-base.txt`. |
| Tệp ghép | `normcore.json` **không commit**: `git rm --cached`, thêm vào `.gitignore`. Thư mục `workspace/normcore/` giữ `__init__.py`. |
| Luật ghép | Nối dòng các mảnh theo thứ tự ở mục 2; bỏ dòng trùng hệt; cùng `id` khác nội dung → lỗi NC-11. Lối tắt hiện ra theo thứ tự đó (00-base giữ thứ tự cũ; FEAT mới đứng sau theo số FEAT; ASM-NORM60-03). Dựng JSON bằng `build_workspace.render` hiện có (tất định). |
| `modified` | `render(rows, modified=None)`: mặc định giữ hằng số hiện tại (để kiểm và test cũ); hook ghi tệp với `modified = frappe.utils.now()` mỗi lần install/migrate, nên Frappe **luôn** nhập lại Workspace (một bản ghi, rẻ) và không ai phải đổi hằng số `BASE["modified"]` nữa. |
| Mã | Phần dựng (`REL`, `HEADER`, `BASE`, `read_shortcuts`, `render`) **chuyển vào `normcore/generated.py`** (Frappe chạy từ gói `normcore`, không dựa vào `scripts/` có trên đĩa); thêm `read_sources(root)` (đọc `shortcuts.d/` nếu có, không thì `shortcuts.txt`) và tham số `modified`. `scripts/build_workspace.py` thành lớp CLI mỏng: chèn gốc repo vào `sys.path`, `from normcore.generated import REL, HEADER, BASE, read_shortcuts, render` (tên cũ còn nguyên cho `check_conventions.py`, `pr_sync_fix.py` và test cũ `bw.render`, `bw.read_shortcuts`, `bw.REL`), `--check` giữ nghĩa cũ ở bố cục cũ. Một bản luật duy nhất. |
| Ai sinh | Như 2.1: `before_install`, `before_migrate`, `normcore/tests/conftest.py`, `scripts/build_generated.py`. |
| NC-11 | `check_workspace(root)`: có `shortcuts.d/` thì kiểm các mảnh đọc và dựng được (định dạng, `id` trùng khác nội dung); `normcore.json` trên đĩa (nếu có) không còn phải khớp từng byte. Không có `shortcuts.d/` thì giữ hành vi cũ (test cũ không đổi). |

Đã cân nhắc "bỏ tệp JSON, tạo Workspace bằng mã ở `after_migrate`": loại, vì `sync_fixtures` (Custom HTML Block "NC Trang chủ") chạy **sau** `after_install`, Workspace tham chiếu block đó; đường nhập JSON trong `sync_for`/`sync_all` là đường Frappe đã chạy được trên CI và staging.

### 2.3 Test ref (`docs/rtm-testref.md`)

| Hạng mục | Thiết kế |
|---|---|
| Nguồn | `docs/rtm-testref/FEAT-NNN.md` (một FEAT một tệp, bảng `| FR | Test thật |` như hiện nay). |
| Dữ liệu cũ | `git mv docs/rtm-testref.md docs/rtm-testref/00-base.md`. Không tách theo FEAT, để PR cũ còn nối mục vào tệp cũ được git chuyển sang `00-base.md` (mục 4). |
| `build_rtm.py` | **Không sửa** (chỉ đọc, và nó không đọc Test ref). Ràng buộc 1 của Lead ("build_rtm.py đọc cả thư mục") không thực hiện được và không cần: ghi CF trong `docs/decisions/assumptions/NORM-60.md` (ASM-NORM60-01). `rtm.md` không nằm trong danh sách tệp conflict (0/25 PR). |
| Văn bản cần đổi | `multica/skills/normcore-integrate/SKILL.md` bước 2: đổi `docs/rtm-testref.md` → `docs/rtm-testref/FEAT-NNN.md` (chỉ dòng 19; NORM-61 sửa dòng 14 cùng tệp, cách 4 dòng, không chồng hunk). Tệp chỉ đọc nhắc tên cũ, **người vận hành** sửa: `.autopilot/prompts/50-integrate.md` dòng 6, `scripts/autopilot.sh` dòng 95 (`:(exclude)docs/rtm-testref/`). Đoạn sửa soạn sẵn trong mô tả PR (mục 6). |

### 2.4 `scripts/check_conventions.py` (ma trận quyền)

Lý do 13 PR cùng sửa (mục 1): chỉ ba bảng `MATRIX`, `DOCTYPE_ROW`, `DELETE_ALLOWED`. Quyết định: **tách**, theo cách `scope_rules`.

- Thư mục mới `scripts/conventions/perm_matrix/<ten_doctype_snake>.json`, một DocType một tệp:
  `{"doctype": "NC Norm Template", "row": "Mẫu định mức", "codes": "R R - W R - R R W R", "delete": []}`
  (`codes` theo thứ tự `ROLES`; `delete`: vai trò được thêm quyền xóa, hiện chỉ có thể là `["NC Admin"]`).
- Khi import, `check_conventions` **nạp thêm** các tệp vào ba dict: `DOCTYPE_ROW[doctype] = row`; `MATRIX.setdefault(row, codes)`; `DELETE_ALLOWED[role].add(doctype)`. Hàm `check_permissions(data, path)` giữ nguyên chữ ký và logic, nên `test_permission_matrix.py` (sửa `cc.MATRIX[...]` tại chỗ) không đổi.
- Kiểm mới (mã NC-08, chạy trong `run`): tệp không đọc được, `doctype` không khớp tên tệp, `codes` khác `MATRIX` đã có cho cùng `row`, DocType khai ở cả dict lẫn tệp. Báo lỗi, không ghi đè im lặng.
- **Chuyển tiếp**: các dòng literal hiện có của ba dict **giữ nguyên trong NORM-60** (không xóa dòng nào). Lý do: PR #58 (FEAT-034) và #56 (FEAT-014) đang sửa đúng mấy dòng đó; xóa chúng sẽ gây conflict mã thật mà pr-sync không gỡ được. FEAT mới (sau NORM-60) chỉ thêm tệp. Việc dời literal sang tệp làm ở một chore sau khi các PR trên merge (ghi ở mục 8, ASM-NORM60-04).

### 2.5 `normcore/hooks.py`

Quyết định: **thêm sổ đăng ký theo tệp cho các hook dạng danh sách**, giữ nguyên mọi dòng hiện có.

- Thư mục mới `normcore/hook_registry/<FEAT-NNN|NORM-NN>.json`, ví dụ `{"scheduler_events": {"daily": ["normcore.api.x.daily_job"]}, "app_include_js": ["/assets/normcore/js/x.js"]}`.
- Khóa được hỗ trợ: `app_include_js`, `after_install`, `after_migrate`, `before_migrate`, `scheduler_events.<all|hourly|daily|weekly|monthly>`, `fixtures`, `normcore_pending_sources`. Khóa lạ → lỗi khi import (test thuần bắt).
- Module thuần `normcore/core/hook_registry.py`: `load(directory=None) -> dict[str, list]`, ghép theo tên tệp sắp xếp, bỏ phần tử trùng, giữ thứ tự. Cuối `hooks.py` (khối mới, sau `normcore_pending_sources`): `app_include_js = app_include_js + reg["app_include_js"]`, tương tự cho từng khóa (`scheduler_events` gộp theo tần suất; `fixtures` nối cuối danh sách, nên FEAT có fixture phụ thuộc thứ tự vẫn được đặt sau).
- Không đưa vào sổ: `doc_events` (đã sinh từ `delete_guard/`), `permission_query_conditions`/`has_permission` (đã sinh từ `scope_rules/`), `jinja`, `boot_session` (giá trị đơn, mỗi cái chỉ 1 FEAT sửa trong lịch sử).
- NORM-60 tự dùng sổ này cho hook của nó: `normcore/hook_registry/NORM-60.json` khai `before_migrate: ["normcore.generated.before_migrate"]`. `before_install` hiện là chuỗi `"normcore.install.before_install"`; NORM-60 **không sửa dòng đó** mà gọi sinh tệp từ trong `normcore.install.before_install` (mục 2.6). Như vậy NORM-60 không chạm các dòng `after_install`/`after_migrate` mà PR #58 đang sửa.

### 2.6 Điểm sinh tệp trong Frappe

`normcore/generated.py`:

```python
def build_all(root: Path, modified: str | None = None) -> list[str]:
    """Sinh vi.csv và normcore.json từ mảnh; trả danh sách tệp đã ghi; lỗi ghép → ValueError (nêu tệp, mã NC)."""

def before_migrate():            # hook Frappe, import frappe trong thân hàm
    build_all(Path(frappe.get_app_path("normcore")).parent, modified=frappe.utils.now())
```

`normcore.install.before_install` gọi `generated.before_migrate()` ở dòng đầu (cùng việc). Lỗi ghép làm install/migrate dừng với thông báo rõ: đúng ý, vì CI `check_conventions` đã bắt trước.

### 2.7 `.gitattributes`, `.gitignore`

- `.gitattributes`: bỏ dòng `vi.csv`, `rtm-testref.md`, `shortcuts.txt`; thêm `merge=union` cho `normcore/translations/vi.d/00-base.csv`, `normcore/nc_core/workspace/normcore/shortcuts.d/00-base.txt`, `docs/rtm-testref/00-base.md` (chỉ để runner gộp PR cũ còn sửa tệp nền). Giữ hai dòng `assumptions.md`, `conflicts.md`.
- `.gitignore`: thêm `normcore/translations/vi.csv` và `normcore/nc_core/workspace/normcore/normcore.json`, kèm chú thích "sinh bởi normcore/generated.py, NORM-60".

## 3. Phần 2 — Sửa pr-sync (`scripts/pr_sync.sh`, `scripts/pr_sync_fix.py`)

| # | Thay đổi | Lý do |
|---|---|---|
| P1 | Đầu script tự chép **chính nó** vào `$TOOLS` rồi `exec` bản chép (biến `PR_SYNC_SELF=1` chặn lặp). Không chép `scripts/`, `docs/tools/` vào `$TOOLS` nữa. | `git checkout -B pr-sync/<PR>` ghi đè `scripts/pr_sync.sh` đang chạy (bash đọc tệp dần dần). |
| P2 | Sau `git merge`, mọi bước sinh/kiểm chạy bằng script **trong cây đã gộp**: `python3 scripts/pr_sync_fix.py .`, `python3 docs/tools/build_rtm.py docs`, `python3 scripts/check_conventions.py .`. | Sửa nguyên nhân 3 (`0d15f23`): nhánh vừa sửa `build_workspace.py` thì bản develop xóa block mới. Bỏ ASM-NORM37-03 về "dùng công cụ của develop": bot chỉ xử lý PR cùng repo (`isCrossRepository` bị loại), mã trong nhánh đã do agent của squad đẩy lên, nên không có thêm rủi ro tin cậy (ASM-NORM60-02). |
| P3 | `pr_sync_fix.fix(root)` bổ sung, chạy trên cây đã gộp, trước khi kiểm conflict còn lại: (a) tệp sinh bị conflict kiểu sửa/xóa (`vi.csv`, `normcore.json`: develop đã bỏ theo dõi, nhánh cũ còn sửa) → `git rm --cached` (bỏ theo dõi), tệp trên đĩa sinh lại; (b) mảnh nền `00-base.*` còn conflict (hiếm, khi union không áp dụng) → ghép hai bên `:2:`/`:3:` rồi sắp/khử trùng như `sort_vi_csv`; (c) có `vi.d/` thì sắp lại không áp cho `vi.csv` (không còn theo dõi); không có thì giữ hành vi cũ. Trả danh sách tệp đã sửa như cũ. | Nguyên nhân 2: sau khi gộp, thứ tự `vi.csv` tự đúng (tệp ghép luôn được sinh đã sắp). Chuyển tiếp PR cũ (mục 4). |
| P4 | Bỏ khối `c)` riêng trong `pr_sync.sh` (lấy `--ours` cho `normcore.json`, ghép `vi.csv`); việc này nằm trong `pr_sync_fix.py` (P3) để test được bằng pytest. | Một chỗ, có test. |
| P5 | Sau khi Phần 1 vào develop, với PR theo bố cục mới, pr-sync chỉ còn: gộp, chạy `check_conventions`, commit gộp, push (CI tự chạy), hoặc gắn nhãn `conflict` khi còn conflict mã thật. Không có commit "sinh lại tệp sinh". | Mục tiêu Phần 2. |

Môi trường thử cục bộ `PR_SYNC_LOCAL=1` giữ nguyên (test AC-2 dùng nó).

## 4. Chuyển tiếp cho PR đang mở (#56 FEAT-014, #58 FEAT-034, #59 FEAT-013; #61 NORM-61 không chạm tệp chung)

| Trường hợp | Kết quả | Cơ chế |
|---|---|---|
| PR cũ merge **trước** NORM-60 | Dòng của PR vào `vi.csv`, `shortcuts.txt`, `rtm-testref.md`, `check_conventions.py` trên develop. Khi NORM-60 gộp develop (Dev hoặc pr-sync), git thấy develop sửa tệp mà NORM-60 đã đổi tên → áp phần sửa vào `00-base.*`. `normcore.json` (NORM-60 đã bỏ theo dõi, develop sửa) → conflict sửa/xóa, `pr_sync_fix` P3a gỡ. | rename detection + P3a |
| PR cũ merge **sau** NORM-60 | Ngay khi NORM-60 vào develop, pr-sync gộp develop vào từng PR mở: phần sửa `vi.csv`/`shortcuts.txt`/`rtm-testref.md` của PR được chuyển vào `00-base.*`; `normcore.json`, `vi.csv` bị bỏ theo dõi; `check_conventions.py`: NORM-60 không xóa dòng literal nào nên dòng mới của PR gộp sạch. Sau đó PR merge bằng nút GitHub như thường. | rename detection + P3 + mục 2.4 |
| Dev tự gộp tay (không qua bot) | Chạy `python3 scripts/pr_sync_fix.py .` sau `git merge origin/develop`, rồi `git status`: không còn tệp sinh bị theo dõi. Ghi vào đoạn sửa CLAUDE.md mục 11 (mục 6). | P3 |

Kiểm không mất dòng (ràng buộc 4), làm ở T08 và lặp lại ngay trước khi xin merge:
- `vi.csv` ghép từ mảnh **đúng từng byte** với `git show origin/develop:normcore/translations/vi.csv` (tệp develop đã sắp, không trùng; mảnh chỉ có `00-base`).
- Dòng của `shortcuts.d/` ghép = dòng không chú thích của `origin/develop:.../shortcuts.txt`; `normcore.json` sinh ra khác `origin/develop:.../normcore.json` **chỉ ở `modified`**.
- `docs/rtm-testref/00-base.md` đúng từng byte với `origin/develop:docs/rtm-testref.md`.
- Ba dict của `check_conventions` sau khi nạp = ba dict của bản develop (so bằng `python3 -c`, in `True`).

## 5. Tệp sẽ sửa (đủ đường dẫn, ràng buộc 8)

Thêm mới:
- `normcore/generated.py`
- `normcore/core/hook_registry.py`
- `normcore/hook_registry/NORM-60.json` (thư mục mới; nếu Frappe/ruff đòi gói Python thì không cần `__init__.py`, vì chỉ chứa JSON)
- `normcore/tests/conftest.py`
- `normcore/tests/unit/test_generated.py`, `normcore/tests/unit/test_hook_registry.py`
- `scripts/build_generated.py`
- `scripts/conventions/perm_matrix/` (thư mục, ban đầu trống trừ `README.md` mô tả định dạng; không chuyển dòng cũ ở NORM-60)
- `scripts/tests/test_norm60_parallel_merge.py` (AC-1), `scripts/tests/test_norm60_pr_sync.py` (AC-2)
- `docs/decisions/assumptions/NORM-60.md`
- `docs/features/NORM-60/implementation-log.md` (Dev)

Đổi tên (`git mv`, nội dung giữ nguyên):
- `normcore/translations/vi.csv` → `normcore/translations/vi.d/00-base.csv`
- `normcore/nc_core/workspace/normcore/shortcuts.txt` → `normcore/nc_core/workspace/normcore/shortcuts.d/00-base.txt`
- `docs/rtm-testref.md` → `docs/rtm-testref/00-base.md`

Bỏ theo dõi (`git rm --cached`): `normcore/nc_core/workspace/normcore/normcore.json`.

Sửa:
- `.gitattributes`, `.gitignore`
- `normcore/hooks.py` (chỉ thêm khối sổ đăng ký ở cuối tệp; không sửa dòng có sẵn)
- `normcore/install.py` (`before_install` gọi sinh tệp ở dòng đầu thân hàm)
- `scripts/build_workspace.py` (thành lớp CLI mỏng gọi `normcore/generated.py`, mục 2.2)
- `scripts/check_conventions.py` (`check_vi_csv`, `check_workspace`, nạp `perm_matrix/`; không xóa dòng literal)
- `scripts/pr_sync.sh`, `scripts/pr_sync_fix.py`
- `multica/skills/normcore-integrate/SKILL.md` (dòng 19)
- `README.md` hoặc `PLAYBOOK.md`: **không** (PLAYBOOK chỉ đọc). Hướng dẫn cho agent nằm ở đoạn CLAUDE.md soạn sẵn (mục 6) và `scripts/conventions/perm_matrix/README.md`.

Không sửa: `.github/` (không cần: `ci.yml` đã gọi `build_rtm.py`, `check_conventions.py`, pytest, `install-app`; `pr-sync.yml` gọi `scripts/pr_sync.sh`), `docs/tools/`, `CLAUDE.md`, `.claude/`, `.autopilot/`, test hiện có.

## 6. Cần người vận hành duyệt (soạn sẵn trong mô tả PR, agent không sửa)

- `CLAUDE.md` mục 4 dòng "bản dịch ở `normcore/translations/vi.csv`" → "bản dịch ở `normcore/translations/vi.d/FEAT-NNN.csv` (mỗi FEAT một tệp); `vi.csv` do `normcore/generated.py` sinh lúc install/migrate/pytest, không commit".
- `CLAUDE.md` mục 11 gạch đầu dòng `vi.csv`, `rtm.md` → thay bằng: "Tệp sinh (`vi.csv`, `normcore.json`) không theo dõi; sau `git merge origin/develop` chạy `python3 scripts/pr_sync_fix.py .`. Bản dịch, lối tắt Workspace, Test ref, quyền ma trận, hook dạng danh sách ghi vào tệp riêng của FEAT (`vi.d/`, `shortcuts.d/`, `docs/rtm-testref/`, `scripts/conventions/perm_matrix/`, `normcore/hook_registry/`)."
- `CLAUDE.md` mục 8 không cần đổi (Lead đã xác nhận).
- `.autopilot/prompts/50-integrate.md` dòng 6 và `scripts/autopilot.sh` dòng 95: tên `docs/rtm-testref.md` → `docs/rtm-testref/FEAT-NNN.md` / `docs/rtm-testref/`.
- `.claude/hooks/guard.py`: không cần đổi.

## 7. Tiêu chí nghiệm thu (theo Lead: AC-1…AC-5 của mô tả issue)

| Mã | Điều kiện kiểm được | Test / lệnh | Trong PR này |
|---|---|---|---|
| AC-1 | Từ một commit chung (cây thật của nhánh, chép vào repo git tạm), nhánh A và B mỗi nhánh thêm một bản dịch (`vi.d/FEAT-901.csv`, `FEAT-902.csv`), một lối tắt (`shortcuts.d/…`), một Test ref (`docs/rtm-testref/…`), một tệp `perm_matrix/` và một tệp `hook_registry/`. Gộp A vào nền, rồi gộp B bằng **`git merge-tree --write-tree`** (cách GitHub gộp phía máy chủ, không đọc `.gitattributes` của worktree, không có driver union) → thoát 0, không conflict. Trên cây kết quả: `git status --porcelain` sau khi chạy `scripts/build_generated.py` **rỗng** (không cần commit sinh lại); `check_conventions.py` thoát 0; `vi.csv` ghép chứa cả hai bản dịch, đã sắp; `normcore.json` có cả hai lối tắt; `hook_registry.load()` có cả hai hook. Đối chứng: cùng kịch bản trên bố cục cũ (sửa `vi.csv`, `shortcuts.txt` ở vị trí kề nhau) → `merge-tree` báo conflict (chứng minh test phân biệt được). | `scripts/tests/test_norm60_parallel_merge.py::test_AC1_hai_nhanh_song_song_khong_conflict`, `::test_AC1_doi_chung_bo_cuc_cu_conflict` | Có |
| AC-2 | Repo tạm có remote giả: develop thêm một lối tắt; nhánh PR sửa phần dựng workspace (`normcore/generated.py::render`, trước đây là `build_workspace.py`) để biết một loại block mới mà bản develop không biết (đúng kiểu `0d15f23`: block trang chủ) và thêm một mảnh dùng loại đó. Chạy `PR_SYNC_LOCAL=1 scripts/pr_sync.sh` → nhánh được đẩy lên; trên nhánh sau đồng bộ, `normcore.json` sinh bằng script của nhánh có **cả** block của nhánh lẫn lối tắt của develop; không có nhãn `conflict`. Thêm: PR cũ còn sửa `vi.csv`/`normcore.json` theo bố cục cũ được chuyển đúng sang bố cục mới (mục 4, dòng 2). | `scripts/tests/test_norm60_pr_sync.py::test_AC2_pr_sync_dung_script_cua_nhanh_khong_mat_block`, `::test_chuyen_tiep_pr_bo_cuc_cu` | Có |
| AC-3 | Luật giữ verdict trong `normcore-verify` | — | NORM-61 |
| AC-4 | Luật giới hạn FEAT song song trong `multica/agents.md` | — | NORM-61 |
| AC-5 | Không xóa, skip, nới test nào: `git diff origin/develop -- '*test*.py' 'scripts/tests/'` chỉ có tệp mới, không có dòng `-` chứa `assert`/`def test`; NC-09, NC-10, NC-11, NC-08 vẫn chạy (test mới: `test_generated.py` kiểm NC-09 trùng giữa hai mảnh, NC-10 `vi.csv` cũ trên đĩa, NC-11 `id` trùng giữa hai mảnh, NC-08 mảnh `perm_matrix` lệch `codes`). Toàn bộ lệnh kiểm chuẩn xanh. | `normcore/tests/unit/test_generated.py`, lệnh ở T10 | Có |

Ngoài ra (ràng buộc 2 của Lead, chứng minh Frappe đọc được): T09 chạy trên bench dev **site mới** (`new-site` + `install-app`) và **migrate** site có sẵn, kiểm bằng `bench execute`: `frappe.translate.get_all_translations("vi")` chứa một khóa của `00-base.csv` và một khóa của mảnh thử; Workspace "Normcore" có đủ số lối tắt bằng số dòng mảnh. Deploy staging dùng đúng `install-app`/`migrate` + `clear-cache` (`deploy-staging.yml`), nên hai phép kiểm này phủ cả staging; xác nhận thật trên staging làm sau merge (smoke của người vận hành, R2).

## 8. Giả định, rủi ro, việc để sau

Giả định (ghi ở `docs/decisions/assumptions/NORM-60.md`):
- **ASM-NORM60-01** (kèm CF với ràng buộc 1 của Lead): không sửa `docs/tools/build_rtm.py` (chỉ đọc theo guard và CI; và nó không đọc Test ref). Test ref nằm ở `docs/rtm-testref/FEAT-NNN.md`, dữ liệu cũ ở `00-base.md`.
- **ASM-NORM60-02**: pr-sync chạy script của cây đã gộp, thay ASM-NORM37-03; an toàn vì chỉ PR cùng repo.
- **ASM-NORM60-03**: thứ tự lối tắt Workspace = `00-base` rồi theo tên mảnh; thứ tự dòng `vi.csv` không ảnh hưởng Frappe.
- **ASM-NORM60-04**: dòng literal cũ của `check_conventions.py` và `hooks.py` giữ nguyên trong NORM-60 để không làm conflict PR đang mở; dời sang tệp là chore sau khi #56, #58, #59 merge (Lead tạo issue nếu muốn).
- **ASM-NORM60-05**: `modified` của Workspace đóng dấu lúc install/migrate (luôn nhập lại), thay hằng số.
- **ASM-NORM60-06**: test AC-1/AC-2 ở `scripts/tests/` (theo Lead); `ci.yml` không chạy thư mục này, Dev/Reviewer/QA chạy `pytest scripts/tests` bằng tay và ghi bằng chứng.

Rủi ro:
- **R1** Agent cũ vẫn sửa `vi.csv`/`shortcuts.txt` theo CLAUDE.md cũ trước khi người vận hành sửa CLAUDE.md: `vi.csv` bị `.gitignore` nên không commit được nếu không `-f`; `shortcuts.txt` không còn tồn tại, `check_conventions` không đọc nó khi có `shortcuts.d/` → bản dịch/lối tắt "mất" lặng lẽ. Giảm: `check_conventions` báo NC-11 nếu thấy `shortcuts.txt` cạnh `shortcuts.d/`, và NC-10 nếu `vi.csv` đang được git theo dõi (`git ls-files`) khi có `vi.d/`.
- **R2** Deploy staging: lần đầu sau merge, `git reset --hard` xóa `vi.csv`, `normcore.json` đang theo dõi; nếu `migrate` lỗi trước `before_migrate`, site chạy không bản dịch tới lần deploy sau. Giảm: hook chạy đầu tiên; CI site-tests (install-app) đã chứng minh trước merge.
- **R3** `scripts/tests/` không nằm trong CI (ASM-NORM60-06). Nếu Lead muốn CI chạy, cách không sửa `.github/`: thêm một test trong `normcore/tests/unit/` gọi `pytest.main(["scripts/tests"])` — chưa làm, chờ Lead.
- **R4** `git merge-tree --write-tree` cần git ≥ 2.38 (máy dev hiện có 2.43). Test không được `skip` khi git cũ (luật cứng 1): git cũ thì test đỏ với thông báo rõ.
