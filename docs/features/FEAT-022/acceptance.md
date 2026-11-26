# Nghiệm thu FEAT-022 — Ánh xạ hướng dẫn với dịch vụ

Commit đã kiểm: `3458567764b5504ec1623b1d78f17c42b6157583`. Người kiểm: Tester iu (độc lập).

| Tiêu chí | Bằng chứng | Kết quả |
| :-- | :-- | :-- |
| TC-SVC-02 (FR-SVC-006/007) | `test_TC_SVC_02_chi_muc_da_xac_nhan_vao_nguon_ai` trong normcore/api/test_library_mapping.py, đạt | Đạt |
| FR-SVC-005 | 5 test `test_FR_SVC_005_*`, đạt | Đạt |
| FR-SVC-006 (người + thời điểm, dịch vụ ngừng dùng bị từ chối) | `test_FR_SVC_006_*`, đạt | Đạt |
| FR-SVC-007 | `test_FR_SVC_007_*`, đạt (nguồn AI giả lập, không gọi AI thật) | Đạt |
| DocType NC Section Service Map: vai trò không quyền và NC Auditor | test_nc_section_service_map.py và `test_FR_SVC_006_quyen_anh_xa`, đạt | Đạt |
| Chạy lại trên site sạch normcore-verify.test | `Ran 1143 tests ... OK` (site đã xóa sau chạy) | Đạt |
| pytest unit + golden + độ phủ | 589 passed, phủ 99% | Đạt |
| golden_engine, golden_cls, check_conventions | thoát 0 | Đạt |
| build_rtm | VAN DE: 0 | Đạt |
| Soát diff test | chỉ thêm test; không xóa/skip/nới | Đạt |
| Tài liệu chỉ đọc | không đổi | Đạt |
| CI PR #55 | cả hai job pass | Đạt |
| Giao diện SCR-DSK-004 bằng trình duyệt | Không có tài khoản test của vai trò để đăng nhập; chưa kiểm bằng Playwright. Luồng được kiểm ở tầng API/test có vai trò. | Chưa thử (ghi chú) |
