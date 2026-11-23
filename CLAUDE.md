# CLAUDE.md — Normcore Autopilot

> Tệp này là luật làm việc của agent khi xây app `normcore`. Mọi phiên Claude Code trong kho mã này đều đọc tệp này trước.
> Đọc kèm `PLAYBOOK.md` (quy trình chạy) và `docs/README.md` (thứ tự đọc bộ tài liệu nghiệp vụ).

## 1. Sứ mệnh

Xây đầy đủ app **`normcore`** trên **Frappe Framework v15**, ứng dụng độc lập (không ERPNext), từ bộ tài liệu trong `docs/` (bản 1.1), gồm 39 tính năng FEAT-001 đến FEAT-039 theo ba bản phát hành R1, R2, R3.

Hệ thống chạy **tự động hoàn toàn, không có người duyệt giữa chừng**. Vì vậy:

- **Không bao giờ hỏi người dùng.** Không có ai trả lời. Khi thiếu thông tin, quyết theo mục 6 và ghi lại quyết định.
- **Không bao giờ báo xong khi chưa chứng minh được.** "Xong" nghĩa là lệnh kiểm thử đã chạy và đạt, không phải "code trông đúng".
- **Mỗi phiên chỉ làm đúng một giai đoạn** được giao trong lời nhắc (bootstrap, design, ui, implement, verify, integrate, release, report). Làm xong giai đoạn đó thì dừng.

## 2. Nguồn sự thật và thứ bậc

Khi hai nguồn mâu thuẫn, nguồn đứng trên thắng. Ghi mâu thuẫn vào `docs/decisions/conflicts.md` (mã `CF-NNN`), rồi làm theo nguồn thắng.

| Bậc | Nguồn | Quyết định điều gì | Quyền sửa của agent |
| :-: | :-- | :-- | :-- |
| 1 | `docs/golden/golden_engine.py`, `docs/golden/golden_cls.py` | Mọi con số, công thức tính giá, cách làm tròn | **Chỉ đọc** |
| 2 | `docs/test-cases.md` | Hành vi mong đợi, giá trị mong đợi, dữ liệu vàng | **Chỉ đọc** |
| 3 | `docs/srs.md` (FR, NFR, BR) | Yêu cầu | **Chỉ đọc** |
| 4 | `docs/use-cases.md` | Luồng nghiệp vụ | **Chỉ đọc** |
| 5 | `docs/data-model.md` | DocType, trường, quyền, trạng thái, ràng buộc DI | Sửa qua amendment (mục 7) |
| 6 | `docs/architecture.md` (ADR) | Cấu trúc mã, công nghệ | Sửa qua amendment |
| 7 | `docs/ux-foundations.md`, `docs/design.md` | Màn hình, điều hướng, thành phần | Sửa qua amendment |
| 8 | `docs/implementation-plan.md` | Phạm vi từng FEAT, thứ tự, tiêu chí nghiệm thu, DoD | **Chỉ đọc** |
| — | `docs/rtm.md`, `docs/verification-report.md` | Sinh bằng `docs/tools/build_rtm.py` | Không sửa tay; chỉ ghi cột Test ref ở giai đoạn integrate |

**Không dùng để xây:** `docs/sua-doi-1.1/`, mọi bản nháp `normcore-phan-he-e/`, tài liệu ý tưởng. Chúng chỉ để tra lịch sử.

Hook `.claude/hooks/guard.py` chặn ghi vào các tệp "chỉ đọc". Đừng tìm cách lách (sed, cp, python ghi tệp…): lách hook là vi phạm luật cứng.

## 3. Luật cứng — vi phạm là sai, không có ngoại lệ

1. **Không sửa, bỏ qua, nới lỏng hay xóa test để cho qua.** Không đổi giá trị mong đợi. Không thêm `skip`, `xfail`, `try/except: pass` quanh assertion. Test sai thật thì ghi `DEF-NNN` (mục 7) chứ không sửa. Ngoại lệ duy nhất: cập nhật danh sách hoặc số đếm trong test cũ khi FEAT mới thêm DocType, bộ nhập, vai trò đúng FR hoặc ma trận `docs/data-model.md` mục 4; assertion giữ nguyên độ chặt (vẫn so khớp đủ); có "Quyết định Lead" trên issue và ASM dẫn chứng. Ngoại lệ này không áp dụng cho số liệu tiền, công thức, `docs/golden/`, `docs/test-cases.md`.
2. **Không tự chế công thức.** Mọi phép tính giá phải truy được về một `BR-COST-*`, `BR-ADJ-*` hoặc `BR-CLS-*` và về hàm tương ứng trong `docs/golden/`. Cài đặt phải cho cùng kết quả với golden trên mọi bộ dữ liệu vàng: tiền khớp đến đơn vị nhỏ nhất mà golden dùng, hệ số k khớp 6 chữ số thập phân.
3. **Làm tròn và kiểu số theo golden.** Đọc golden để biết làm tròn ở bước nào, bao nhiêu chữ số. Tiền dùng `Decimal` hoặc đúng kiểu golden dùng; không tự đổi thứ tự làm tròn.
4. **Không phụ thuộc ERPNext** hay app nào ngoài `frappe`. `required_apps = []`.
5. **Không commit bí mật.** Khóa AI, mật khẩu, token chỉ đọc từ `site_config.json` hoặc biến môi trường.
6. **Không gọi nhà cung cấp AI thật trong test.** Test dùng provider giả lập của `ai/gateway.py`.
7. **Git:** không `push --force`, không viết lại lịch sử `develop`/`main`, không push thẳng `main` ngoài giai đoạn release.
8. **Một tính năng một lúc.** Không sửa mã ngoài phạm vi FEAT đang làm, trừ khi cần để một test đang đỏ do chính FEAT này gây ra trở lại xanh. Không refactor tiện tay.
9. **Không chạm production** trừ giai đoạn release khi `AUTO_DEPLOY_PROD=true`.
10. **Không xóa dữ liệu hay site** ngoài site test `normcore.test` do chính autopilot tạo.

## 4. Quy ước kỹ thuật Frappe v15

**Cấu trúc**

- App `normcore`; module và cấu trúc thư mục theo `docs/architecture.md` (Module Def, các gói `core/`, `procedure/`, `costing/`, `library/`, `ai/`, `benchmark/`, `exports/`, `api/`).
- Logic nghiệp vụ nằm ở **module Python thuần** (ví dụ `normcore/costing/engine.py`, `cls.py`, `allocation.py`), không phụ thuộc `frappe`, kiểm thử được bằng `pytest` không cần site. Controller DocType chỉ gọi vào đó.
- `costing/engine.py` phải có điểm cắm cho bước chi phí trực tiếp để `costing/cls.py` cắm vào (ADR-017).

**DocType**

- Tiền tố `NC ` cho tên DocType. Fieldname tiếng Anh `snake_case`. Label, mô tả, thông báo bằng tiếng Việt (NFR-MNT-003).
- Bật `track_changes` cho mọi DocType nghiệp vụ.
- Quyền đúng ma trận ở `docs/data-model.md` mục 4. Vai trò **NC Auditor** chỉ đọc, không tạo/sửa/xóa/duyệt gì.
- Ràng buộc `DI-01` đến `DI-17` cài bằng `validate` hoặc ràng buộc CSDL, mỗi ràng buộc có test.
- Mã bất biến (mã bước, mã dòng nguồn lực…) cấp từ bộ đếm trên bản ghi cha, không tái dùng.

**API và giao diện**

- API ở `normcore/api/*.py`, `@frappe.whitelist()`, kiểm quyền tường minh trong từng hàm (`frappe.has_permission` hoặc kiểm phạm vi khoa).
- Ba trang Vue (`procedure-editor`, `norm-grid`, `price-compare`, cùng `sensitivity`) theo `docs/design.md`, dùng biến CSS của Desk, chạy được trên 1366 × 768.
- Chuỗi giao diện qua `_()`; bản dịch ở `normcore/translations/vi.csv`. Định dạng số, tiền, ngày theo NFR-LOC-001.

**Dữ liệu cài sẵn**

- Fixtures: vai trò (10, gồm NC Auditor), Workflow, loại giá mẫu, bảng ánh xạ tài khoản mẫu, mẫu lệnh AI, mẫu in, mẫu định mức Hóa sinh và Miễn dịch, mẫu Excel của các bộ nhập.
- Đổi cấu trúc sau khi FEAT đã lên staging: viết patch trong `normcore/patches/` và khai báo ở `patches.txt`.

**Kiểm thử**

| Loại | Vị trí | Chạy bằng |
| :-- | :-- | :-- |
| Đơn vị thuần | `normcore/tests/unit/` | `pytest normcore/tests/unit` |
| Golden | `normcore/tests/golden/` — import `docs/golden/*.py`, so kết quả bộ máy với golden | `pytest normcore/tests/golden` |
| Tích hợp trên site | `test_*.py` cạnh DocType, lớp `FrappeTestCase` | `bench --site normcore.test run-tests --app normcore` |
| Quét quy ước | `scripts/check_conventions.py` (fieldname, label, tiền tố, `track_changes`, quyền, NC Auditor không có quyền ghi) | `python3 scripts/check_conventions.py` |

- **Tên test mang mã test case:** `test_TC_PROC_01_tao_ban_nhap`. Cột Test ref của RTM lấy từ đây.
- Mỗi FR mức Must của FEAT có ít nhất một test tự động; mỗi TC được liệt kê trong tiêu chí nghiệm thu của FEAT phải có test cùng mã.
- Độ phủ ≥ 90% cho `normcore/costing/` và `normcore/benchmark/rules.py` (NFR-MNT-001).

## 5. Tệp trạng thái — "trí nhớ" của hệ thống

Mỗi phiên bắt đầu không nhớ gì. Trạng thái nằm trong tệp, không nằm trong đầu agent.

```
docs/features/FEAT-NNN/
  technical-design.md   # giai đoạn design: hợp đồng API, DocType/migration, thiết kế thành phần, tiêu chí nghiệm thu
  ui-design.md          # giai đoạn ui: màn hình SCR-DSK-*, trạng thái, tương tác
  tasks.md              # danh sách việc có thứ tự, dạng "- [ ] T01 ... (done-when: ...)"
  implementation-log.md # giai đoạn implement: mỗi task một dòng, lệnh đã chạy, kết quả
  acceptance.md         # giai đoạn verify: báo cáo kiểm định độc lập
  verdict.json          # {"verdict": "accepted|rework|design-defect|requirement-defect", "reasons": [...], "commit": "<sha>"}
  DONE                  # giai đoạn integrate tạo khi đã merge và lên staging
  BLOCKED               # lý do bị chặn; runner bỏ qua FEAT này
docs/as-built/FEAT-NNN.md      # theo mẫu ở implementation-plan.md mục 6
docs/decisions/assumptions.md  # ASM-NNN: mọi quyết định tự chọn khi tài liệu chưa chốt
docs/decisions/conflicts.md    # CF-NNN: mâu thuẫn giữa tài liệu và cách đã xử lý
docs/decisions/amendments/AMD-NNN.md  # sửa tài liệu thiết kế
docs/decisions/defects/DEF-NNN.md     # lỗi ở tài liệu chỉ đọc; cần người xử lý sau
docs/BUILD-REPORT.md           # báo cáo cuối
.autopilot/                    # của runner; agent không sửa, trừ khi lời nhắc yêu cầu ghi HALT
```

## 6. Tự quyết khi tài liệu chưa chốt

Các mục ở `docs/README.md` "Việc cần chốt" và `docs/srs.md` Phụ lục B chưa có người chốt. Áp dụng mặc định dưới đây, ghi mỗi lần áp dụng thành một dòng `ASM-NNN` trong `docs/decisions/assumptions.md` (mã TBD, FEAT, lựa chọn, chỗ trong mã), và đánh dấu trên giao diện hoặc bộ tham số là **"Giả định — chờ xác nhận"** khi có thể.

| Mục | Mặc định khi tự chạy |
| :-- | :-- |
| TBD-02 công thức tích lũy, nghĩa vụ tài chính (BR-COST-013) | Cài đúng như `golden_engine.py`; tỷ lệ là tham số trong NC Costing Parameter Set; công thức nằm trong **một hàm** |
| TBD-01 mẫu biểu Phụ lục I–V TT 21/2024 | Xuất theo cấu trúc trong `srs.md`, `design.md`; mẫu là tệp template thay được (fixtures) |
| TBD-03 ánh xạ tài khoản TT 24/2024/TT-BTC | Cài bảng ánh xạ mẫu tối thiểu + mẫu Excel nhập; bệnh viện tự nạp |
| TBD-04 mẫu in quy trình | Mẫu in mặc định |
| TBD-05 loại giá, cấp phê duyệt | Hai loại giá mẫu như kế hoạch; là dữ liệu cấu hình |
| TBD-06 bệnh viện thí điểm | Dùng bộ dữ liệu vàng và bộ dữ liệu giả `normcore/demo/` sinh từ dữ liệu vàng; có cả một máy mua và một máy đặt |
| TBD-09 chất lượng tách mục, OCR | Thử trên PDF mẫu tự tạo; ghi giới hạn vào As-Built |
| TBD-14 loại chi phí ngoại kiểm, thuê máy, liên doanh | Ba trường tạm trong bộ tham số như kế hoạch |
| TBD-15 vật liệu nội kiểm dùng chung | Chia đều theo số thông số; công thức trong một hàm |
| TBD-16 LIS xuất số test phụ | Đường ước tính từ kế hoạch chất lượng là đường chính; vẫn cài đường nạp số thực |
| TBD-17 dịch vụ bộ (FR-SVC-010, mức Should) | Nếu SRS có mặc định thì theo; không có thì để cấu hình, mặc định "theo thông số" |
| TBD-18 loại thiết bị bắt buộc có hồ sơ | Cài trống, bệnh viện tự đánh dấu |
| Bốn lựa chọn thiết kế của BA trước FEAT-034 | Theo đúng lựa chọn BA đã ghi |
| BR-COST, BR-CLS chưa được chuyên gia rà | Theo golden. Không "sửa cho hợp lý hơn" |
| Nhà cung cấp AI | Cài bộ chuyển đổi Anthropic (model cấu hình được) và provider giả lập; khóa đọc từ cấu hình |
| Câu hỏi mở khác | Chọn phương án **đơn giản nhất, đảo ngược được, cấu hình được**, khớp test case; ghi ASM |

## 7. Khi gặp vướng

| Tình huống | Làm gì |
| :-- | :-- |
| Một task đỏ sau **3 lần** sửa | Đưa nhánh về commit xanh gần nhất, ghi lý do vào `implementation-log.md`, tạo `BLOCKED` với nguyên nhân, dừng phiên |
| Thiết kế (data-model, ADR, UX) không làm được hoặc mâu thuẫn với yêu cầu | Viết `AMD-NNN` (vấn đề, phương án, tệp sửa, ảnh hưởng FEAT khác); sửa tài liệu thiết kế; chạy `python3 docs/tools/build_rtm.py docs` phải 0 vấn đề; tiếp tục |
| Tài liệu chỉ đọc tự mâu thuẫn hoặc test case trái golden | Viết `DEF-NNN` (trích dẫn hai bên); nếu chặn FEAT thì tạo `BLOCKED`; **không** tự sửa yêu cầu |
| Phụ thuộc FEAT khác chưa có | Không làm thay FEAT kia. Tạo `BLOCKED` ghi "chờ FEAT-xxx" |
| Môi trường hỏng (bench, MariaDB, Redis, node) | Tự sửa môi trường, tối đa 3 lần; không được thì ghi `.autopilot/HALT` với lý do |
| Thiếu bí mật (khóa API, SSH staging) | Ghi `.autopilot/HALT`; không bịa giá trị, không tắt bước kiểm |

## 8. Definition of Done (bản tự động)

Thay "chủ dự án nghiệm thu" bằng **kiểm định độc lập** ở một phiên mới không thấy quá trình viết mã. Một FEAT chỉ được tạo `DONE` khi đủ:

- [ ] Mọi task trong `tasks.md` đã đánh dấu và có bằng chứng chạy trong `implementation-log.md`.
- [ ] Mọi FR của FEAT có test đạt; mọi TC trong tiêu chí nghiệm thu có test cùng mã và đạt.
- [ ] Toàn bộ test của app đạt (không chỉ test của FEAT); bộ golden đạt; quét quy ước đạt; độ phủ đạt.
- [ ] Quyền DocType mới khớp ma trận; có test với ít nhất một vai trò không có quyền và với NC Auditor.
- [ ] Nhãn, thông báo tiếng Việt.
- [ ] `verdict.json` = `accepted`, do phiên verify viết, `commit` trùng HEAD của nhánh.
- [ ] CI trên PR xanh; đã merge vào `develop`; đã lên staging và smoke test đạt.
- [ ] Có `docs/as-built/FEAT-NNN.md`; cột Test ref trong `docs/rtm.md` được ghi; `build_rtm.py` 0 vấn đề.

## 9. Git

- Nhánh: `main` (production), `develop` (staging), `feat/FEAT-NNN-<slug>` (mỗi tính năng), `release/rN`.
- Commit nhỏ, mỗi task một commit: `FEAT-006 T03: API sắp lại bước`.
- PR từ `feat/*` vào `develop`, squash merge khi CI xanh và verdict accepted.
- Tag `v1.0.0` (R1), `v2.0.0` (R2), `v3.0.0` (R3) ở giai đoạn release.

## 10. Lệnh thường dùng

```bash
# Kiểm bộ tài liệu (phải chạy không lỗi trước mọi thứ)
python3 docs/golden/golden_engine.py
python3 docs/golden/golden_engine.py --no-depr
python3 docs/golden/golden_cls.py
python3 docs/tools/build_rtm.py docs

# Kiểm thử
pytest normcore/tests/unit normcore/tests/golden --cov=normcore/costing --cov=normcore/benchmark
cd $BENCH_DIR && bench --site normcore.test run-tests --app normcore
python3 scripts/check_conventions.py

# Cài lại app trên site test sau khi đổi DocType
cd $BENCH_DIR && bench --site normcore.test migrate && bench build --app normcore
```

`$BENCH_DIR` là bench dev (mặc định `~/frappe-bench`); app được liên kết vào `$BENCH_DIR/apps/normcore`.


## 11. Xung đột khi merge (Dev, Reviewer)

- Khi PR của mình báo "This branch has conflicts", hoặc khi có PR khác vừa merge vào `develop`: tự `git fetch` rồi `git merge origin/develop` vào nhánh. Không rebase, không force-push.
- `normcore/translations/vi.csv`: giữ cả hai bên, bỏ dòng trùng khóa nếu có; giữ thứ tự chữ cái theo cột đầu. `.gitattributes` đặt `merge=union` cho tệp này; `scripts/check_conventions.py` báo lỗi khi tệp chưa sắp xếp hoặc có khóa trùng.
- `docs/rtm.md`, `docs/verification-report.md`: không sửa tay; chạy lại `python3 docs/tools/build_rtm.py docs` rồi commit kết quả.
- Tệp khác: tự gỡ nếu chỉ là hai bên cùng thêm; nếu hai bên sửa cùng logic thì dừng và báo Lead.
- Sau khi gỡ, chạy lại toàn bộ test. PR chỉ được coi là xong khi hết conflict và CI xanh.
