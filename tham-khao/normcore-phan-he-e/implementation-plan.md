# Kế hoạch triển khai sơ bộ – Normcore Phân hệ E

> Phiên bản 1.0 · 13/11/2026 · Mức phân tích nghiệp vụ. Kế hoạch chính thức do dev lập bằng skill implementation-planning sau khi có tài liệu kiến trúc và UX; tài liệu này là đầu vào cho bước đó.
> Cỡ epic (S, M, L) là ước lượng tương đối của BA, dev xác nhận lại.

## 1. Lát cắt xương sống (walking skeleton)

Một dịch vụ, một thiết bị, một mặt hàng có một nguồn giá, một phiếu định mức một dòng K02, một bản ghi sản lượng, một lần tính. Đạt khi lần tính cho đúng TV-01: k = 1,108247 và K02 = 33.247,41. Lát cắt này chứng minh chuỗi dữ liệu và bộ máy tính trước khi làm rộng.

## 2. Epic

| Epic | Nội dung | FR | Cỡ | Phụ thuộc |
| :-- | :-- | :-- | :-- | :-- |
| E1 | Nền tảng và danh mục gốc: khoa, dịch vụ, thiết bị, mặt hàng, nguồn giá, phân quyền, nhật ký, nhập tệp | FR-SVC-001..003, FR-SVC-005..006, FR-EQP-001..002, FR-EQP-005, FR-EQP-007..008, FR-PRC-001..002, FR-PRC-005, FR-PRC-007, FR-SEC-001..004, FR-AUD-001..003, FR-IMP-001..005 | L | – |
| E2 | Hệ thống xét nghiệm, kế hoạch chất lượng, hồ sơ tuân thủ, nhân lực | FR-SYS-001..003, FR-SYS-005..006, FR-QC-001..003, FR-QC-006, FR-CMP-001, FR-CMP-003, FR-LAB-001..003, FR-RPT-007 | M | E1 |
| E3 | Phiếu định mức và luồng duyệt phiếu | FR-NRM-001..009, FR-LAB-004, FR-APR-001, FR-APR-003, FR-APR-006 | L | E1, E2 |
| E4 | Sản lượng và bộ máy tính giá thành | FR-VOL-001..003, FR-PRC-003..004, FR-QC-004..005, FR-CMP-002, FR-CMP-004..005, FR-EQP-003..004, FR-EQP-006, FR-SYS-004, FR-CST-001..014, FR-AI-004..005 | L | E3 |
| E5 | Đối soát, trình duyệt lần tính, hồ sơ xuất | FR-VOL-005..006, FR-REC-001..002, FR-REC-004..006, FR-APR-002, FR-APR-004..005, FR-RPT-001..005, FR-RPT-008, FR-INT-001 | L | E4 |
| E6 | AI đề xuất định mức | FR-AI-001..003, FR-AI-006..008 | M | E3 |
| E7 | Yêu cầu mức Should còn lại | FR-SVC-004, FR-PRC-006, FR-NRM-010..011, FR-VOL-004, FR-VOL-007, FR-REC-003, FR-CST-015, FR-RPT-006, FR-INT-002..004 | M | E5 |
| E8 | Yêu cầu mức Could và tích hợp | FR-SVC-007, FR-EQP-009, FR-PRC-008, FR-VOL-008 | S | E5 |

## 3. Thứ tự và mốc

1. **M0 – Xương sống.** Lát cắt ở mục 1 chạy trên site dev, có kiểm thử tự động TV-01.
2. **M1 – Tính được.** E1, E2, E3, E4 xong. Đạt khi TV-01 đến TV-16 khớp và các kịch bản TS-01 đến TS-36 liên quan đạt.
3. **M2 – Trình duyệt được (MVP).** E5 xong. Thí điểm hóa sinh và miễn dịch 30–50 dịch vụ tại một bệnh viện; đo mục tiêu G2 và G4.
4. **M3 – Có AI.** E6 xong; đo thời gian lập phiếu trước và sau.
5. **M4 – Mở rộng.** E7; nạp mẫu định mức và dữ liệu cho huyết học, vi sinh, sinh học phân tử, giải phẫu bệnh, rồi chẩn đoán hình ảnh. Phần mở rộng nhóm chuyên ngành chủ yếu là dữ liệu mẫu và kiểm thử, không phải mã mới.
6. **M5 – Tích hợp.** E8 và kết nối LIS, RIS.

Rủi ro làm sớm: bộ máy tính (E4) và ảnh chụp tham số. Hai phần này quyết định tính đúng và tính tái lập, nên xương sống đi qua chúng ngay từ M0.

## 4. Definition of Done cho mỗi tính năng

- [ ] Mọi FR của tính năng có kịch bản TS đạt; quy tắc QT, KT liên quan có kiểm thử đơn vị.
- [ ] Vector TV liên quan khớp giá trị kỳ vọng, sai số 0 đồng ở kết quả cuối.
- [ ] Fieldname tiếng Anh, label tiếng Việt; không sửa lõi Frappe; không trùng DocType với phân hệ A–D.
- [ ] Phân quyền đã kiểm thử với ít nhất ba vai trò, gồm một vai trò khoa.
- [ ] Thông báo lỗi bằng tiếng Việt, nêu rõ trường hoặc quy tắc vi phạm.
- [ ] Có tài liệu As-Built theo mục 5 và đã cập nhật RTM (cột Design ref, Test ref).
- [ ] Chủ sản phẩm nghiệm thu trên site staging bằng dữ liệu mẫu.

## 5. Mẫu tài liệu As-Built

Mỗi epic bàn giao một tệp `docs/as-built/<epic>.md` gồm:

1. **Luồng nghiệp vụ thực tế đã xây**, nêu chỗ khác với use case và lý do.
2. **DocType tạo mới và sửa đổi**: tên, ý nghĩa, trường chính, quan hệ; đánh dấu chỗ khác với docs/data-model.md.
3. **Quy tắc tính và kiểm tra đã cài**: mã QT, KT, vị trí trong mã nguồn, tham số cấu hình.
4. **Phân quyền và workflow** đã cấu hình.
5. **Hook, tác vụ nền, API, báo cáo, print format** đã thêm.
6. **Dữ liệu khởi tạo và mẫu nhập** đi kèm.
7. **Kết quả kiểm thử**: danh sách TS, TV đã chạy và kết quả.
8. **Điểm chưa làm, nợ kỹ thuật, câu hỏi mở.**

## 6. Bước tiếp theo với bộ skill agentic-sdlc-kit

| Bước | Skill | Đầu vào | Đầu ra |
| :-- | :-- | :-- | :-- |
| 1 | pipeline-verify | Bộ tài liệu này | Báo cáo ID mồ côi, tham chiếu hỏng |
| 2 | software-architecture | docs/srs.md | docs/architecture.md, các ADR |
| 3 | ux-foundations | SRS, kiến trúc | docs/ux-foundations.md, design.md |
| 4 | implementation-planning | SRS, use case, kiến trúc, UX | Kế hoạch chính thức thay tài liệu này |
| 5 | project-scaffolding | Kiến trúc, kế hoạch | Repo có xương sống chạy được |
| 6 | detailed-design, ui-design, feature-implementation, acceptance-verification | Từng tính năng | Thiết kế, mã, báo cáo nghiệm thu; RTM được điền dần |

Khi đổi yêu cầu, chạy lại requirements-engineering ở chế độ sửa đổi: mã yêu cầu không đổi và không tái sử dụng.
