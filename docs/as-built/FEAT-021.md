# As-Built: FEAT-021 Thay thế văn bản và hàng đợi rà soát

Issue NORM-64. FR-LIB-007, 008, 009 (và FR-WF-009, FR-NOTI-001 qua UC-002). UC-002 (bước 1–7; nhánh 2a, 5a). SCR-DSK-012 (mới), SCR-DSK-003 (bổ sung), SCR-DSK-007 (bổ sung nhỏ). TC-LIB-05, 06, 07. Người nghiệm thu: QA (chưa làm).

## 1. Luồng nghiệp vụ đã xây
1. Trên văn bản A: nút "Khai báo thay thế" (hoặc bảng "Thay thế") ghi dòng NC Legal Supersession: văn bản B, phạm vi Toàn bộ / Một phần, danh sách mã mục, từ ngày D.
2. Khi lưu: kiểm (không tự thay chính nó, một dòng cho mỗi B, D sau ngày hiệu lực của B, mục phải có trong B) rồi áp dụng: B (hoặc từng mục được chọn) có `expiry_date` = D − 1, chỉ kéo sớm hơn (ASM-021-02). Comment "Info" ghi trên B.
3. D ≤ hôm nay: tính lại hiệu lực ngay. Ngược lại tác vụ hằng ngày `daily_job` → `refresh_validity` chuyển sang "Hết hiệu lực" khi đến ngày.
4. `refresh_validity` gọi `api/review.flag_affected` cho văn bản/mục vừa hết hiệu lực: quy trình "Đã ban hành" có trích dẫn → `needs_review` = 1, Comment, Notification Log (+ email theo cài đặt) cho `head_user` của khoa chủ trì. Không có quy trình trích dẫn → chỉ còn liên kết thay thế (UC-002 5a).
5. Hàng đợi rà soát (Desk Page `review-queue`, SCR-DSK-012): quy trình có cờ, trích dẫn bị ảnh hưởng, văn bản thay thế. Trưởng khoa chọn "Sửa đổi" (`create_revision` của FEAT-008) hoặc "Không cần sửa" kèm lý do (`dismiss_review`, gỡ cờ, ghi Comment). Ban hành bản sửa đổi gỡ cờ của bản mới.

## 2. DocType
- Mới: NC Legal Supersession (bảng con, đúng 4 trường data-model, `permissions` rỗng, theo quyền DocType cha).
- Mở rộng: NC Legal Document thêm `supersession_section`, `supersessions`, `superseded_by_html` (trường bố cục). NC Clinical Procedure không đổi cấu trúc (dùng `needs_review`).
- Không cần patch (không đổi cột đã có).

## 3. Mã
- `library/supersession.py`, `procedure/review.py` (thuần, phủ 100% và 99%).
- `nc_legal_document.py` (`check_supersessions`, `on_update`), `api/library.py` (`declare_supersession`, `get_supersessions`, `apply_supersessions`, `refresh_validity` trả thêm `flagged`), `api/review.py` (`flag_affected`, `get_review_queue`, `dismiss_review`), `api/procedure_workflow.py` ("Ban hành" đặt `needs_review` = 0).
- Giao diện: `nc_legal_document.js` (hộp thoại, khối "Bị thay thế bởi"), `nc_procedure/page/review_queue/`, `nc_clinical_procedure.js` và `_list.js` (dải và chỉ báo "Cần rà soát"), lối tắt Workspace, bản dịch `translations/vi.d/FEAT-021.csv`.

## 4. Quyền
Dòng "Văn bản, mục, ánh xạ": NC Document Controller, NC Admin ghi (khai báo thay thế); các vai khác và NC Auditor chỉ đọc. Hàng đợi: mọi vai đọc quy trình đọc được; chỉ NC Department Head của khoa chủ trì (và Administrator) hành động; người chỉ có vai NC Clinician / NC Department Head chỉ thấy khoa mình (ASM-021-12).

## 5. Test case đã chạy
Xem `docs/rtm-testref/FEAT-021.md` và `implementation-log.md`.

## 6. Giới hạn đã biết
- **Trích dẫn khớp theo tên hoặc số hiệu (ASM-021-01, Lead đã duyệt):** `legal_document`, `legal_section` của NC Procedure Citation vẫn là Data (nợ ASM-046). Trích dẫn gõ sai số hiệu hoặc mã mục không được khớp nên quy trình không bị gắn cờ. Việc đổi sang Link kèm patch dữ liệu tách ở NORM-65; bộ khớp ưu tiên tên `LS-…`/`LD-…` nên vẫn đúng sau đó.
- Xóa dòng thay thế không hoàn tác ngày hết hiệu lực (ASM-021-02). Quy trình đã "Không cần sửa" không bị gắn cờ lại trừ khi có văn bản/mục khác hết hiệu lực (ASM-021-05).
- Hàng đợi không có ánh xạ mục-với-mục; chỉ hiện văn bản thay thế (ASM-021-09).
- Giao diện chưa kiểm bằng trình duyệt ở 1366 × 768 và bàn phím (agent không có trình duyệt); chỉ kiểm quy ước tĩnh, `bench build`, API và Page có trong site.
