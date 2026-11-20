# Ma trận truy vết yêu cầu (RTM) – Normcore Phân hệ E

> Nguồn: docs/srs.md, docs/use-cases.md, docs/implementation-plan.md, docs/test-scenarios.md · Cập nhật: 13/11/2026 · Sinh tự động bằng scripts/build_rtm.py.
> Cột Design ref và Test ref do các bước thiết kế và nghiệm thu điền sau. Cột Plan ref lấy theo kế hoạch sơ bộ, bước implementation-planning sẽ ghi lại. Cột Kịch bản là kịch bản nghiệm thu dự kiến, chưa phải kết quả kiểm thử.

| Req ID | Yêu cầu (ngắn) | ƯT | Trạng thái | Nguồn | Use case | Design ref | Plan ref | Kịch bản | Test ref |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| FR-SVC-001 | Hồ sơ dịch vụ | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-01 | _TBD_ | E1 (sơ bộ) | TS-01 | _TBD_ |
| FR-SVC-002 | Kiểm tra mã TT 23 | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-01 | _TBD_ | E1 (sơ bộ) | TS-02 | _TBD_ |
| FR-SVC-003 | Ánh xạ mã ngoài | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-01 | _TBD_ | E1 (sơ bộ) | TS-01 | _TBD_ |
| FR-SVC-004 | Dịch vụ bộ | S | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-01 | _TBD_ | E7 (sơ bộ) | — | _TBD_ |
| FR-SVC-005 | Chặn trùng | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-01 | _TBD_ | E1 (sơ bộ) | TS-03 | _TBD_ |
| FR-SVC-006 | Ngừng dùng | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-01 | _TBD_ | E1 (sơ bộ) | TS-04 | _TBD_ |
| FR-SVC-007 | Gửi ngoài | C | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-01 | _TBD_ | E8 (sơ bộ) | — | _TBD_ |
| FR-EQP-001 | Hồ sơ thiết bị | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-02 | _TBD_ | E1 (sơ bộ) | TS-28 | _TBD_ |
| FR-EQP-002 | Hình thức có máy | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-02 | _TBD_ | E1 (sơ bộ) | TS-05 | _TBD_ |
| FR-EQP-003 | Máy đặt | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-02 | _TBD_ | E4 (sơ bộ) | TS-05 | _TBD_ |
| FR-EQP-004 | Máy thuê | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-02 | _TBD_ | E4 (sơ bộ) | TS-50 | _TBD_ |
| FR-EQP-005 | Linh kiện lớn | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-02 | _TBD_ | E1 (sơ bộ) | TS-29 | _TBD_ |
| FR-EQP-006 | Thiếu dữ liệu khấu hao | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-02 | _TBD_ | E4 (sơ bộ) | TS-06 | _TBD_ |
| FR-EQP-007 | Thiết bị dùng chung | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-02 | _TBD_ | E1 (sơ bộ) | TS-07 | _TBD_ |
| FR-EQP-008 | Tổng tỷ lệ 100% | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-02 | _TBD_ | E1 (sơ bộ) | TS-07 | _TBD_ |
| FR-EQP-009 | Liên kết Asset | C | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-02 | _TBD_ | E8 (sơ bộ) | — | _TBD_ |
| FR-SYS-001 | Hồ sơ hệ thống | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-04 | _TBD_ | E2 (sơ bộ) | TS-12 | _TBD_ |
| FR-SYS-002 | Nhiều hệ thống | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-04 | _TBD_ | E2 (sơ bộ) | TS-12 | _TBD_ |
| FR-SYS-003 | Tổng tỷ trọng | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-04 | _TBD_ | E2 (sơ bộ) | TS-12 | _TBD_ |
| FR-SYS-004 | Bình quân gia quyền | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-09 | _TBD_ | E4 (sơ bộ) | TS-30 | _TBD_ |
| FR-SYS-005 | Phút chiếm máy | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-04 | _TBD_ | E2 (sơ bộ) | TS-29 | _TBD_ |
| FR-SYS-006 | Tiêu chí chia máy | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-04 | _TBD_ | E2 (sơ bộ) | TS-29 | _TBD_ |
| FR-PRC-001 | Hồ sơ mặt hàng | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-03 | _TBD_ | E1 (sơ bộ) | TS-08 | _TBD_ |
| FR-PRC-002 | Nhiều nguồn giá | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-03 | _TBD_ | E1 (sơ bộ) | TS-08 | _TBD_ |
| FR-PRC-003 | Chọn giá | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-09 | _TBD_ | E4 (sơ bộ) | TS-08 | _TBD_ |
| FR-PRC-004 | Thiếu giá | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-09 | _TBD_ | E4 (sơ bộ) | TS-10 | _TBD_ |
| FR-PRC-005 | Xác minh chứng từ | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-03 | _TBD_ | E1 (sơ bộ) | TS-11 | _TBD_ |
| FR-PRC-006 | Giá mới có hiệu lực | S | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-13 | _TBD_ | E7 (sơ bộ) | TS-44 | _TBD_ |
| FR-PRC-007 | VAT đầu vào | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-03 | _TBD_ | E1 (sơ bộ) | TS-09 | _TBD_ |
| FR-PRC-008 | Liên kết Item | C | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-03 | _TBD_ | E8 (sơ bộ) | — | _TBD_ |
| FR-QC-001 | Kế hoạch nội kiểm | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-04 | _TBD_ | E2 (sơ bộ) | TS-27 | _TBD_ |
| FR-QC-002 | Kế hoạch chuẩn máy | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-04 | _TBD_ | E2 (sơ bộ) | TS-27 | _TBD_ |
| FR-QC-003 | Chương trình ngoại kiểm | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-04 | _TBD_ | E2 (sơ bộ) | TS-27 | _TBD_ |
| FR-QC-004 | Chia phí ngoại kiểm | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-09 | _TBD_ | E4 (sơ bộ) | TS-27 | _TBD_ |
| FR-QC-005 | Ước tính từ kế hoạch | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-08 | _TBD_ | E4 (sơ bộ) | TS-26 | _TBD_ |
| FR-QC-006 | Thiếu kế hoạch | S | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-04 | _TBD_ | E2 (sơ bộ) | — | _TBD_ |
| FR-CMP-001 | Hồ sơ tuân thủ | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-02 | _TBD_ | E2 (sơ bộ) | TS-13 | _TBD_ |
| FR-CMP-002 | Quy về năm | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-09 | _TBD_ | E4 (sơ bộ) | TS-13 | _TBD_ |
| FR-CMP-003 | Nhắc hạn | S | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-02 | _TBD_ | E2 (sơ bộ) | TS-14 | _TBD_ |
| FR-CMP-004 | Thiếu hồ sơ | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-09 | _TBD_ | E4 (sơ bộ) | TS-14 | _TBD_ |
| FR-CMP-005 | Hai cách phân bổ | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-09 | _TBD_ | E4 (sơ bộ) | TS-13 | _TBD_ |
| FR-LAB-001 | Chi phí chức danh | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-07 | _TBD_ | E2 (sơ bộ) | TS-19 | _TBD_ |
| FR-LAB-002 | Phiếu bấm giờ | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-07 | _TBD_ | E2 (sơ bộ) | TS-19 | _TBD_ |
| FR-LAB-003 | Trung bình lần đo | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-07 | _TBD_ | E2 (sơ bộ) | TS-19 | _TBD_ |
| FR-LAB-004 | Chưa bấm giờ | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-06 | _TBD_ | E3 (sơ bộ) | TS-19 | _TBD_ |
| FR-NRM-001 | Phiếu và dòng | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-05 | _TBD_ | E3 (sơ bộ) | TS-15 | _TBD_ |
| FR-NRM-002 | Tạo từ mẫu | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-05 | _TBD_ | E3 (sơ bộ) | TS-15 | _TBD_ |
| FR-NRM-003 | Thiếu khoản mục | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-06 | _TBD_ | E3 (sơ bộ) | TS-15 | _TBD_ |
| FR-NRM-004 | Thanh toán riêng | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-05 | _TBD_ | E3 (sơ bộ) | TS-16 | _TBD_ |
| FR-NRM-005 | Số xét nghiệm mỗi ống | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-05 | _TBD_ | E3 (sơ bộ) | TS-17 | _TBD_ |
| FR-NRM-006 | Thiếu số xét nghiệm mỗi ống | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-06 | _TBD_ | E3 (sơ bộ) | TS-17 | _TBD_ |
| FR-NRM-007 | Xác nhận từng dòng | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-06 | _TBD_ | E3 (sơ bộ) | TS-22 | _TBD_ |
| FR-NRM-008 | Phiên bản | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-06 | _TBD_ | E3 (sơ bộ) | TS-23 | _TBD_ |
| FR-NRM-009 | Chống trùng nội kiểm | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-05 | _TBD_ | E3 (sơ bộ) | TS-18 | _TBD_ |
| FR-NRM-010 | So sánh phiên bản | S | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-06 | _TBD_ | E7 (sơ bộ) | TS-23 | _TBD_ |
| FR-NRM-011 | Sao chép phiếu | S | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-05 | _TBD_ | E7 (sơ bộ) | — | _TBD_ |
| FR-AI-001 | Soạn dự thảo | S | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-05 | _TBD_ | E6 (sơ bộ) | TS-20 | _TBD_ |
| FR-AI-002 | Dẫn nguồn | S | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-05 | _TBD_ | E6 (sơ bộ) | TS-20 | _TBD_ |
| FR-AI-003 | Không có nguồn | S | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-05 | _TBD_ | E6 (sơ bộ) | TS-20 | _TBD_ |
| FR-AI-004 | Chờ xác nhận | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-06 | _TBD_ | E4 (sơ bộ) | TS-20 | _TBD_ |
| FR-AI-005 | Không dùng AI để tính | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-09 | _TBD_ | E4 (sơ bộ) | TS-28 | _TBD_ |
| FR-AI-006 | Chỉ dùng danh mục | S | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-05 | _TBD_ | E6 (sơ bộ) | TS-20 | _TBD_ |
| FR-AI-007 | AI lỗi | S | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-05 | _TBD_ | E6 (sơ bộ) | TS-21 | _TBD_ |
| FR-AI-008 | Nhật ký AI | S | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-05 | _TBD_ | E6 (sơ bộ) | TS-20 | _TBD_ |
| FR-VOL-001 | Sản lượng kỳ | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-08 | _TBD_ | E4 (sơ bộ) | TS-24 | _TBD_ |
| FR-VOL-002 | Ba kịch bản | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-08 | _TBD_ | E4 (sơ bộ) | TS-31 | _TBD_ |
| FR-VOL-003 | Không có sản lượng | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-09 | _TBD_ | E4 (sơ bộ) | TS-32 | _TBD_ |
| FR-VOL-004 | Sản lượng thấp | S | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-09 | _TBD_ | E7 (sơ bộ) | TS-25 | _TBD_ |
| FR-VOL-005 | Xuất kho thực tế | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-08 | _TBD_ | E5 (sơ bộ) | TS-37 | _TBD_ |
| FR-VOL-006 | Chi phí khoa | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-08 | _TBD_ | E5 (sơ bộ) | TS-38 | _TBD_ |
| FR-VOL-007 | Số dịch vụ HIS | S | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-08 | _TBD_ | E7 (sơ bộ) | — | _TBD_ |
| FR-VOL-008 | Đồng bộ API | C | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-08 | _TBD_ | E8 (sơ bộ) | — | _TBD_ |
| FR-CST-001 | Chạy lần tính | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-09 | _TBD_ | E4 (sơ bộ) | TS-28 | _TBD_ |
| FR-CST-002 | Hệ số tiêu hao | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-09 | _TBD_ | E4 (sơ bộ) | TS-24 | _TBD_ |
| FR-CST-003 | Chi phí theo mẻ | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-09 | _TBD_ | E4 (sơ bộ) | TS-32 | _TBD_ |
| FR-CST-004 | Chi phí theo ngày | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-09 | _TBD_ | E4 (sơ bộ) | TS-27 | _TBD_ |
| FR-CST-005 | Chi phí theo kỳ | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-09 | _TBD_ | E4 (sơ bộ) | TS-29 | _TBD_ |
| FR-CST-006 | Chi phí cấp 5 | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-09 | _TBD_ | E4 (sơ bộ) | TS-28 | _TBD_ |
| FR-CST-007 | Ảnh chụp tham số | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-09 | _TBD_ | E4 (sơ bộ) | TS-33 | _TBD_ |
| FR-CST-008 | Kết quả theo dòng | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-09 | _TBD_ | E4 (sơ bộ) | TS-28 | _TBD_ |
| FR-CST-009 | Tổng hợp theo TT 21 | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-09 | _TBD_ | E4 (sơ bộ) | TS-28 | _TBD_ |
| FR-CST-010 | Làm tròn | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-09 | _TBD_ | E4 (sơ bộ) | TS-28 | _TBD_ |
| FR-CST-011 | Khóa sau duyệt | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-11 | _TBD_ | E4 (sơ bộ) | TS-40 | _TBD_ |
| FR-CST-012 | Ba kịch bản | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-09 | _TBD_ | E4 (sơ bộ) | TS-31 | _TBD_ |
| FR-CST-013 | Lỗi từng dịch vụ | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-09 | _TBD_ | E4 (sơ bộ) | TS-32 | _TBD_ |
| FR-CST-014 | Chạy nền | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-09 | _TBD_ | E4 (sơ bộ) | TS-34 | _TBD_ |
| FR-CST-015 | Độ nhạy | S | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-14 | _TBD_ | E7 (sơ bộ) | TS-36 | _TBD_ |
| FR-REC-001 | Đối soát vật chất | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-10 | _TBD_ | E5 (sơ bộ) | TS-37 | _TBD_ |
| FR-REC-002 | Đối soát tài chính | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-10 | _TBD_ | E5 (sơ bộ) | TS-38 | _TBD_ |
| FR-REC-003 | Đối soát sản lượng | S | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-10 | _TBD_ | E7 (sơ bộ) | — | _TBD_ |
| FR-REC-004 | Vượt ngưỡng | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-10 | _TBD_ | E5 (sơ bộ) | TS-37 | _TBD_ |
| FR-REC-005 | Lưu giải trình | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-10 | _TBD_ | E5 (sơ bộ) | TS-37 | _TBD_ |
| FR-REC-006 | Thiếu số liệu đối soát | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-10 | _TBD_ | E5 (sơ bộ) | TS-39 | _TBD_ |
| FR-APR-001 | Luồng phiếu định mức | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-06 | _TBD_ | E3 (sơ bộ) | TS-22 | _TBD_ |
| FR-APR-002 | Luồng lần tính | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-11 | _TBD_ | E5 (sơ bộ) | TS-40 | _TBD_ |
| FR-APR-003 | Ghi vết chuyển trạng thái | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-06, UC-11 | _TBD_ | E3 (sơ bộ) | TS-22 | _TBD_ |
| FR-APR-004 | Chặn trình duyệt | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-11 | _TBD_ | E5 (sơ bộ) | TS-40 | _TBD_ |
| FR-APR-005 | Khóa tham số | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-11 | _TBD_ | E5 (sơ bộ) | TS-40 | _TBD_ |
| FR-APR-006 | Trả lại có lý do | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-06, UC-11 | _TBD_ | E3 (sơ bộ) | TS-22 | _TBD_ |
| FR-RPT-001 | Bảng định mức | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-12 | _TBD_ | E5 (sơ bộ) | TS-42 | _TBD_ |
| FR-RPT-002 | Bảng giá thành | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-12 | _TBD_ | E5 (sơ bộ) | TS-42 | _TBD_ |
| FR-RPT-003 | Thuyết minh | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-12 | _TBD_ | E5 (sơ bộ) | TS-42 | _TBD_ |
| FR-RPT-004 | Phụ lục chứng từ | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-12 | _TBD_ | E5 (sơ bộ) | TS-42 | _TBD_ |
| FR-RPT-005 | Vì sao giá này | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-12 | _TBD_ | E5 (sơ bộ) | TS-41 | _TBD_ |
| FR-RPT-006 | So sánh hai lần tính | S | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-13 | _TBD_ | E7 (sơ bộ) | TS-44 | _TBD_ |
| FR-RPT-007 | Hạn hồ sơ tuân thủ | S | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-02 | _TBD_ | E2 (sơ bộ) | TS-14 | _TBD_ |
| FR-RPT-008 | Thiếu dữ liệu | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-12 | _TBD_ | E5 (sơ bộ) | TS-10 | _TBD_ |
| FR-IMP-001 | Mẫu nhập | M | Active | BA bổ sung theo danh mục chuẩn | UC-08 | _TBD_ | E1 (sơ bộ) | TS-45 | _TBD_ |
| FR-IMP-002 | Kiểm tra theo dòng | M | Active | BA bổ sung theo danh mục chuẩn | UC-08 | _TBD_ | E1 (sơ bộ) | TS-45 | _TBD_ |
| FR-IMP-003 | Không ghi dòng lỗi | M | Active | BA bổ sung theo danh mục chuẩn | UC-08 | _TBD_ | E1 (sơ bộ) | TS-45 | _TBD_ |
| FR-IMP-004 | Nhập thử | S | Active | BA bổ sung theo danh mục chuẩn | UC-08 | _TBD_ | E1 (sơ bộ) | TS-45 | _TBD_ |
| FR-IMP-005 | Nhật ký nhập | M | Active | BA bổ sung theo danh mục chuẩn | UC-08 | _TBD_ | E1 (sơ bộ) | TS-45 | _TBD_ |
| FR-SEC-001 | Quyền theo vai trò | M | Active | BA bổ sung theo danh mục chuẩn | UC-15 | _TBD_ | E1 (sơ bộ) | TS-46 | _TBD_ |
| FR-SEC-002 | Giới hạn theo khoa | M | Active | BA bổ sung theo danh mục chuẩn | UC-15 | _TBD_ | E1 (sơ bộ) | TS-46 | _TBD_ |
| FR-SEC-003 | Che chi phí lương | M | Active | BA bổ sung theo danh mục chuẩn | UC-07 | _TBD_ | E1 (sơ bộ) | TS-47 | _TBD_ |
| FR-SEC-004 | Cấu hình | M | Active | BA bổ sung theo danh mục chuẩn | UC-15 | _TBD_ | E1 (sơ bộ) | TS-48 | _TBD_ |
| FR-AUD-001 | Nhật ký thay đổi | M | Active | BA bổ sung theo danh mục chuẩn | UC-01 | _TBD_ | E1 (sơ bộ) | TS-49 | _TBD_ |
| FR-AUD-002 | Không xóa dữ liệu đã dùng | M | Active | BA bổ sung theo danh mục chuẩn | UC-15 | _TBD_ | E1 (sơ bộ) | TS-04 | _TBD_ |
| FR-AUD-003 | Chứng từ bất biến | M | Active | BA bổ sung theo danh mục chuẩn | UC-03 | _TBD_ | E1 (sơ bộ) | TS-49 | _TBD_ |
| FR-INT-001 | Chuyển sang Phân hệ C | M | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-11 | _TBD_ | E5 (sơ bộ) | TS-43 | _TBD_ |
| FR-INT-002 | Nhận hệ số phân bổ | S | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-09 | _TBD_ | E7 (sơ bộ) | — | _TBD_ |
| FR-INT-003 | QTKT đổi phiên bản | S | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-06 | _TBD_ | E7 (sơ bộ) | — | _TBD_ |
| FR-INT-004 | API chỉ đọc | S | Active | Tài liệu ý tưởng Phân hệ E (13/11/2026) | UC-12 | _TBD_ | E7 (sơ bộ) | TS-43 | _TBD_ |
| NFR-PERF-001 | Hiệu năng: Lần tính 500 dịch vụ với ba kịch bản hoàn tất trong 10 phút trên… | M | Active | BA bổ sung theo danh mục chuẩn | — | _TBD_ | _TBD_ | TS-35 | _TBD_ |
| NFR-PERF-002 | Hiệu năng: Màn hình “vì sao giá này” của một dịch vụ có không quá 60 dòng tải… | M | Active | BA bổ sung theo danh mục chuẩn | — | _TBD_ | _TBD_ | TS-41 | _TBD_ |
| NFR-PERF-003 | Hiệu năng: Nhập tệp 10.000 dòng hoàn tất trong 5 phút. | S | Active | BA bổ sung theo danh mục chuẩn | — | _TBD_ | _TBD_ | — | _TBD_ |
| NFR-CAP-001 | Dung lượng: Hỗ trợ 3.000 dịch vụ, 500 thiết bị, 20.000 mặt hàng, 50.000 nguồn… | M | Active | BA bổ sung theo danh mục chuẩn | — | _TBD_ | _TBD_ | — | _TBD_ |
| NFR-REL-001 | Tin cậy: Chạy lại lần tính với cùng ảnh chụp tham số cho giá thành giống… | M | Active | BA bổ sung theo danh mục chuẩn | — | _TBD_ | _TBD_ | TS-33 | _TBD_ |
| NFR-REL-002 | Tin cậy: Kết quả của bộ vector kiểm thử TV-01..TV-16 khớp giá trị kỳ vọng,… | M | Active | BA bổ sung theo danh mục chuẩn | — | _TBD_ | _TBD_ | — | _TBD_ |
| NFR-REL-003 | Tin cậy: Sao lưu hằng ngày; RPO không quá 24 giờ, RTO không quá 8 giờ. | M | Active | BA bổ sung theo danh mục chuẩn | — | _TBD_ | _TBD_ | — | _TBD_ |
| NFR-SEC-001 | Bảo mật: Mọi phương thức whitelisted kiểm tra quyền theo Role và User… | M | Active | BA bổ sung theo danh mục chuẩn | — | _TBD_ | _TBD_ | TS-46 | _TBD_ |
| NFR-SEC-002 | Bảo mật: Mọi kết nối dùng HTTPS với TLS 1.2 trở lên. | M | Active | BA bổ sung theo danh mục chuẩn | — | _TBD_ | _TBD_ | — | _TBD_ |
| NFR-SEC-003 | Bảo mật: Dữ liệu gửi dịch vụ AI chỉ gồm tài liệu kỹ thuật và danh mục;… | M | Active | BA bổ sung theo danh mục chuẩn | — | _TBD_ | _TBD_ | — | _TBD_ |
| NFR-SEC-004 | Bảo mật: Nhật ký thay đổi và nhật ký duyệt giữ tối thiểu 10 năm và không… | M | Active | BA bổ sung theo danh mục chuẩn | — | _TBD_ | _TBD_ | — | _TBD_ |
| NFR-USA-001 | Dễ dùng: 100% nhãn, thông báo lỗi và biểu xuất bằng tiếng Việt. | M | Active | BA bổ sung theo danh mục chuẩn | — | _TBD_ | _TBD_ | — | _TBD_ |
| NFR-USA-002 | Dễ dùng: Trưởng khoa xác nhận xong một phiếu 40 dòng trong 15 phút, đo với… | S | Active | BA bổ sung theo danh mục chuẩn | — | _TBD_ | _TBD_ | — | _TBD_ |
| NFR-COM-001 | Tương thích: Chạy trên Frappe v15, MariaDB 10.6 trở lên, Python 3.10 trở lên;… | M | Active | BA bổ sung theo danh mục chuẩn | — | _TBD_ | _TBD_ | — | _TBD_ |
| NFR-COM-002 | Tương thích: Cài và gỡ app không cần sửa lõi Frappe hay ERPNext; chạy được khi… | M | Active | BA bổ sung theo danh mục chuẩn | — | _TBD_ | _TBD_ | — | _TBD_ |
| NFR-MNT-001 | Bảo trì: Bộ máy tính có kiểm thử đơn vị phủ ít nhất 90% dòng lệnh; mỗi quy… | M | Active | BA bổ sung theo danh mục chuẩn | — | _TBD_ | _TBD_ | — | _TBD_ |
| NFR-MNT-002 | Bảo trì: Quy tắc kiểm tra bật, tắt và đổi mức Chặn hoặc Cảnh báo bằng cấu… | S | Active | BA bổ sung theo danh mục chuẩn | — | _TBD_ | _TBD_ | — | _TBD_ |
| NFR-LEG-001 | Tuân thủ: Cấu trúc cấu phần chi phí của biểu xuất là dữ liệu cấu hình, đổi… | S | Active | BA bổ sung theo danh mục chuẩn | — | _TBD_ | _TBD_ | — | _TBD_ |
| NFR-LOC-001 | Bản địa hóa: Tiền tệ VND, định dạng số và ngày theo Việt Nam, múi giờ… | M | Active | BA bổ sung theo danh mục chuẩn | — | _TBD_ | _TBD_ | — | _TBD_ |
| NFR-OBS-001 | Vận hành: Mỗi lần tính ghi thời lượng, số dịch vụ, số lỗi; tác vụ nền thất… | S | Active | BA bổ sung theo danh mục chuẩn | — | _TBD_ | _TBD_ | TS-34 | _TBD_ |
