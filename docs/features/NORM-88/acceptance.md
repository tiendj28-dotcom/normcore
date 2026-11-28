# Nghiệm thu NORM-88: báo cáo hạn hồ sơ tuân thủ bị từ chối quyền

Người nghiệm thu: QA (Multica). Commit đã kiểm: `dc01ac38c9d0c9150428afd4309027b935bcdcca` (PR #89, nền `81e24f9`).

| Tiêu chí | Bằng chứng | Kết quả |
| :-- | :-- | :-- |
| Nguyên nhân: DocType thiếu `report` | diff `nc_equipment_compliance.json`: thêm `report: 1` cho đúng 8 vai trò đã có `read` (khớp `roles` của Report NC Compliance Expiry) | Đạt |
| Không mở quyền ngoài phạm vi; Auditor chỉ đọc | Auditor chỉ có `read`+`report`; không thêm write/create/delete | Đạt |
| Mỗi vai trò chạy được `frappe.desk.query_report.run` | test mới `test_NORM_88_moi_vai_tro_cua_bao_cao_co_quyen_report_tren_ref_doctype` trong bộ chạy đầy đủ | Đạt |
| Site sạch, toàn bộ test | `bench new-site normcore-verify.test` + `run-tests --app normcore`: Ran 2213 tests in 730s, OK, rc=0; site đã xóa | Đạt |
| Soát diff test | chỉ thêm 1 test; không xóa/skip/nới test nào | Đạt |
| Phạm vi, tài liệu chỉ đọc | 2 tệp sản phẩm/test; không chạm docs chỉ đọc | Đạt |

Giới hạn: chưa kiểm bằng trình duyệt trên http://112.213.88.40:8100 vì staging chưa chứa bản sửa (chưa merge); quyền được kiểm bằng API theo từng vai trò trong test. CI Frappe của PR đang chạy khi nghiệm thu.
