# Đặc tả DocType (mô hình dữ liệu) – Normcore Phân hệ E

> Phiên bản 1.0 · 13/11/2026 · Đi kèm docs/srs.md và docs/calculation-rules.md.
> Đây là đặc tả mức phân tích nghiệp vụ. Bước detailed-design của dev chốt kiểu dữ liệu vật lý, index và migration.

## 1. Quy ước

- Module trên Frappe: `Normcore CLS`. Tên DocType tiếng Anh, tiền tố `CLS`; fieldname tiếng Anh dạng snake_case; label tiếng Việt.
- Không phụ thuộc cứng vào ERPNext: liên kết Item, Supplier, Asset lưu ở trường Data tùy chọn (A1, A2).
- DocType danh mục bật Track Changes (FR-AUD-001). Bản ghi đã dùng trong lần tính đã duyệt chỉ được chuyển `status` sang Ngừng (FR-AUD-002).
- Ký hiệu cột Bắt buộc: C = có, K = không, ĐK = có điều kiện.
- Trước khi tạo DocType, dev đối chiếu As-Built của các phân hệ A–D để tránh trùng (ràng buộc C5).

## 2. Danh sách DocType

| # | DocType | Label | Loại | Naming | FR chính |
| :-- | :-- | :-- | :-- | :-- | :-- |
| 1 | CLS Department | Khoa | Danh mục | field:department_code | FR-SEC-002 |
| 2 | CLS Technical Catalog | Danh mục kỹ thuật TT 23 | Danh mục | field:tt23_code | FR-SVC-002 |
| 3 | CLS Service | Dịch vụ CLS | Danh mục | field:service_code | FR-SVC-001..007 |
| 4 | CLS Service Code Map | Ánh xạ mã ngoài | Bảng con của 3 | – | FR-SVC-003 |
| 5 | CLS Panel Component | Thông số của dịch vụ bộ | Bảng con của 3 | – | FR-SVC-004 |
| 6 | CLS Equipment Type | Loại thiết bị | Danh mục | field:type_name | FR-CMP-004 |
| 7 | CLS Equipment | Thiết bị CLS | Danh mục | field:equipment_code | FR-EQP-001..009 |
| 8 | CLS Equipment Component | Linh kiện lớn | Bảng con của 7 | – | FR-EQP-005 |
| 9 | CLS Equipment Allocation | Phân bổ thiết bị theo khoa | Bảng con của 7 | – | FR-EQP-007, 008 |
| 10 | CLS Compliance Record | Hồ sơ tuân thủ thiết bị | Chứng từ | CMP-.YYYY.-.##### | FR-CMP-001..004 |
| 11 | CLS Item | Mặt hàng CLS | Danh mục | field:item_code | FR-PRC-001 |
| 12 | CLS Price Source | Nguồn giá | Chứng từ | PRC-.YYYY.-.##### | FR-PRC-002..007 |
| 13 | CLS Test System | Hệ thống xét nghiệm | Danh mục | SYS-.##### | FR-SYS-001..006 |
| 14 | CLS QC Plan | Kế hoạch nội kiểm và chuẩn máy | Danh mục | QCP-.##### | FR-QC-001, 002, 005 |
| 15 | CLS EQA Program | Chương trình ngoại kiểm | Danh mục | EQA-.YYYY.-.### | FR-QC-003, 004 |
| 16 | CLS EQA Service | Dịch vụ tham gia ngoại kiểm | Bảng con của 15 | – | FR-QC-004 |
| 17 | CLS Job Title Cost | Chi phí chức danh | Danh mục | field:job_title | FR-LAB-001 |
| 18 | CLS Time Study | Phiếu bấm giờ | Chứng từ | TS-.YYYY.-.##### | FR-LAB-002, 003 |
| 19 | CLS Cost Component | Cấu phần chi phí TT 21 | Danh mục | field:component_code | FR-CST-009 |
| 20 | CLS Cost Item | Khoản mục chi phí | Danh mục | field:cost_item_code | FR-NRM-001 |
| 21 | CLS Norm Template | Mẫu định mức theo nhóm | Danh mục | field:specialty_group | FR-NRM-002, 003 |
| 22 | CLS Norm Sheet | Phiếu định mức CLS | Chứng từ có duyệt | NRM-.YYYY.-.##### | FR-NRM-001..011 |
| 23 | CLS Norm Line | Dòng định mức | Bảng con của 22 | – | FR-NRM-001, 007 |
| 24 | CLS Volume Period | Sản lượng kỳ | Chứng từ | VOL-.YYYY.-.##### | FR-VOL-001..004, 007 |
| 25 | CLS Stock Issue Actual | Xuất kho thực tế | Chứng từ | – (hash) | FR-VOL-005 |
| 26 | CLS Department Cost Actual | Chi phí khoa thực tế | Chứng từ | – (hash) | FR-VOL-006 |
| 27 | CLS Overhead Rate | Hệ số phân bổ cấp 5 | Danh mục | OVH-.YYYY.-.### | FR-CST-006, FR-INT-002 |
| 28 | CLS Cost Run | Lần tính giá thành | Chứng từ có duyệt | RUN-.YYYY.-.#### | FR-CST-001..015, FR-APR-002..006 |
| 29 | CLS Cost Result | Kết quả giá thành dịch vụ | Kết quả | – (hash) | FR-CST-008, 009, 012 |
| 30 | CLS Cost Result Line | Dòng kết quả giá thành | Kết quả | – (hash) | FR-CST-008, FR-RPT-005 |
| 31 | CLS Reconciliation Line | Dòng đối soát | Kết quả | – (hash) | FR-REC-001..006 |
| 32 | CLS Settings | Cấu hình Phân hệ E | Single | – | FR-SEC-004 |
| 33 | CLS Rule Setting | Cấu hình quy tắc kiểm tra | Bảng con của 32 | – | NFR-MNT-002 |
| 34 | CLS AI Request Log | Nhật ký gọi AI | Nhật ký | – (hash) | FR-AI-008 |
| 35 | CLS Import Log | Nhật ký nhập liệu | Nhật ký | – (hash) | FR-IMP-005 |

## 3. Đặc tả trường

### 3.1 CLS Service – Dịch vụ CLS

| fieldname | Label | Kiểu | Bắt buộc | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| service_code | Mã dịch vụ | Data | C | Duy nhất |
| service_name | Tên dịch vụ | Data | C | |
| specialty_group | Nhóm chuyên ngành | Select | C | 12 giá trị, Phụ lục A của SRS |
| department | Khoa thực hiện | Link CLS Department | C | Dùng cho User Permission |
| tt23_code | Mã kỹ thuật TT 23 | Link CLS Technical Catalog | K | Duy nhất theo cặp tt23_code + department trong các bản ghi Hoạt động |
| result_unit | Đơn vị kết quả | Select | C | Kết quả, Ca |
| is_panel | Là dịch vụ bộ | Check | K | |
| panel_costing_mode | Cách tính dịch vụ bộ | Select | ĐK | Theo bộ, Theo thông số; bắt buộc khi is_panel |
| panel_components | Thông số thành phần | Table CLS Panel Component | ĐK | Cột: component_service (Link CLS Service) |
| code_maps | Mã hệ thống ngoài | Table CLS Service Code Map | K | Cột: source_system (HIS, LIS, RIS), external_code, external_name |
| is_outsourced | Gửi ngoài | Check | K | Bật thì không tính định mức |
| outsourced_price | Giá hợp đồng gửi mẫu | Currency | ĐK | |
| procedure_ref | Quy trình kỹ thuật | Data | K | Tên bản ghi QTKT của Phân hệ A |
| status | Trạng thái | Select | C | Hoạt động, Ngừng |

CLS Department: department_code, department_name, department_type (Xét nghiệm, Chẩn đoán hình ảnh, Khác). CLS Technical Catalog: tt23_code, technique_name, chapter.

### 3.2 CLS Equipment – Thiết bị CLS

| fieldname | Label | Kiểu | Bắt buộc | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| equipment_code | Mã thiết bị | Data | C | Duy nhất |
| equipment_name | Tên thiết bị | Data | C | |
| equipment_type | Loại thiết bị | Link CLS Equipment Type | C | Quyết định hồ sơ tuân thủ bắt buộc |
| model, manufacturer, serial_no | Model, Hãng, Số seri | Data | K | |
| department | Khoa quản lý | Link CLS Department | C | |
| acquisition_mode | Hình thức có máy | Select | C | Mua, Thuê, Đặt theo hóa chất, Liên doanh liên kết |
| purchase_cost | Nguyên giá | Currency | ĐK | Bắt buộc khi Mua (KT-02) |
| commissioning_date | Ngày đưa vào sử dụng | Date | ĐK | Bắt buộc khi Mua |
| depreciation_years | Thời gian khấu hao (năm) | Float | ĐK | Bắt buộc khi Mua |
| rental_cost_per_period | Tiền thuê mỗi kỳ | Currency | ĐK | Bắt buộc khi Thuê |
| jv_cost_per_period | Chi phí liên kết mỗi kỳ | Currency | ĐK | Bắt buộc khi Liên doanh liên kết |
| allocation_basis | Tiêu chí chia chi phí máy | Select | C | Số kết quả, Phút chiếm máy |
| design_capacity | Công suất thiết kế | Float | K | Kèm capacity_unit (test mỗi giờ, ca mỗi ngày) |
| power_run_kw, power_standby_kw | Công suất điện chạy, chờ | Float | K | kW |
| run_hours_per_day, standby_hours_per_day | Giờ chạy, giờ chờ mỗi ngày | Float | K | |
| continuous_power | Cấp điện liên tục | Check | K | Bật thì D = 365 cho điện |
| components | Linh kiện lớn | Table CLS Equipment Component | K | Cột: component_name, replacement_cost, lifetime_basis (Tháng, Số ca, Giờ), lifetime_value, supplier_borne |
| allocations | Phân bổ theo khoa | Table CLS Equipment Allocation | K | Cột: department, share_percent; tổng 100% (KT-05); trống thì 100% cho khoa quản lý |
| erp_asset | Mã Asset trên ERPNext | Data | K | |
| status | Trạng thái | Select | C | Hoạt động, Ngừng |

CLS Equipment Type: type_name, required_compliance (Table MultiSelect các loại hồ sơ bắt buộc).

### 3.3 CLS Compliance Record – Hồ sơ tuân thủ thiết bị

| fieldname | Label | Kiểu | Bắt buộc | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| equipment | Thiết bị | Link CLS Equipment | C | |
| compliance_type | Loại hồ sơ | Select | C | Kiểm định, Hiệu chuẩn, Kiểm xạ, Giấy phép bức xạ, Bảo trì, Liều kế, Khác |
| cycle_months | Chu kỳ (tháng) | Int | C | Lớn hơn 0 |
| provider | Đơn vị thực hiện | Data | K | |
| cost_per_event | Chi phí mỗi lần | Currency | C | |
| performed_on, expires_on | Ngày thực hiện, Ngày hết hạn | Date | C | expires_on mặc định = performed_on + chu kỳ |
| certificate_no | Số giấy chứng nhận | Data | K | |
| attachment | Chứng từ | Attach | K | |
| supplier_borne | Nhà cung cấp chịu | Check | K | Bật thì chi phí bằng 0 khi máy đặt |

### 3.4 CLS Item và CLS Price Source

| fieldname | Label | Kiểu | Bắt buộc | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| item_code | Mã mặt hàng | Data | C | CLS Item; duy nhất |
| item_name | Tên mặt hàng | Data | C | Lấy theo bảng giá, không lấy theo văn xuôi của quy trình |
| item_type | Loại | Select | C | Hóa chất chính, Hóa chất phụ trợ, Chất chuẩn, Vật liệu nội kiểm, Vật tư, Linh kiện |
| purchase_uom | Đơn vị mua | Data | C | Hộp, lọ, cái |
| norm_uom | Đơn vị định mức | Data | C | Test, mL, cái |
| pack_quantity | Số đơn vị định mức mỗi đơn vị mua | Float | C | Lớn hơn 0; dùng ở QT-01 |
| nominal_tests_per_pack | Số test danh nghĩa mỗi hộp | Int | ĐK | Bắt buộc với Hóa chất chính |
| open_stability_days | Hạn dùng sau mở (ngày) | Int | K | Dùng ở KT-16 |
| erp_item | Mã Item trên ERPNext | Data | K | |
| status | Trạng thái | Select | C | Hoạt động, Ngừng |

| fieldname | Label | Kiểu | Bắt buộc | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| item | Mặt hàng | Link CLS Item | C | CLS Price Source |
| source_type | Loại nguồn | Select | C | Trúng thầu, Hợp đồng, Hóa đơn, Báo giá |
| unit_price | Đơn giá theo đơn vị mua | Currency | C | Lớn hơn 0 |
| price_includes_vat | Giá đã gồm VAT | Check | K | |
| vat_rate | Thuế suất VAT | Percent | ĐK | Bắt buộc khi giá chưa gồm VAT |
| valid_from, valid_to | Hiệu lực từ, đến | Date | C, K | valid_to trống là không hạn |
| document_no | Số chứng từ | Data | C | Số quyết định, hợp đồng, hóa đơn |
| supplier_name | Nhà cung cấp | Data | K | |
| attachment | Tệp chứng từ | Attach | ĐK | Bắt buộc để Đã xác minh (KT-04); khóa sau khi dùng trong lần tính đã duyệt (FR-AUD-003) |
| verification_status | Trạng thái xác minh | Select | C | Chưa xác minh, Đã xác minh |
| verified_by, verified_on | Người, ngày xác minh | Link User, Datetime | K | Hệ thống ghi |

### 3.5 CLS Test System và CLS QC Plan

| fieldname | Label | Kiểu | Bắt buộc | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| service | Dịch vụ | Link CLS Service | C | CLS Test System |
| equipment | Thiết bị chính | Link CLS Equipment | C | |
| volume_share | Tỷ trọng sản lượng | Percent | C | Tổng theo dịch vụ = 100% (KT-06) |
| machine_minutes_per_result | Phút chiếm máy mỗi kết quả | Float | ĐK | Bắt buộc khi thiết bị chia theo phút |
| qc_plan | Kế hoạch chất lượng | Link CLS QC Plan | K | Thiếu thì KT-13 |
| is_active | Đang hoạt động | Check | C | |

| fieldname | Label | Kiểu | Bắt buộc | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| plan_name | Tên kế hoạch | Data | C | CLS QC Plan; một kế hoạch dùng được cho nhiều hệ thống cùng máy |
| iqc_material | Vật liệu nội kiểm | Link CLS Item | K | |
| iqc_levels | Số mức | Int | K | |
| iqc_runs_per_day | Số lần mỗi ngày | Float | K | |
| iqc_volume_per_run | Lượng dùng mỗi lần | Float | K | Theo norm_uom của vật liệu |
| run_days_per_year | Số ngày chạy mỗi năm | Int | C | |
| shared_parameters | Số thông số dùng chung vật liệu | Int | C | Mặc định 1 |
| calibrator | Chất chuẩn | Link CLS Item | K | |
| calibration_points, calibration_replicates | Số điểm chuẩn, số lần lặp | Int | K | Dùng ước tính Qchuan |
| calibrations_per_year | Số lần chuẩn mỗi năm | Int | K | |
| calibrator_cost_per_event | Chi phí chất chuẩn mỗi lần | Currency | K | Trống thì tính từ định lượng × đơn giá |

CLS EQA Program: program_name, provider, year, rounds_per_year, samples_per_round, program_fee, shipping_fee, attachment, services (Table CLS EQA Service: service, share_percent; trống share thì chia đều; tổng 100%).

### 3.6 CLS Job Title Cost và CLS Time Study

- CLS Job Title Cost: job_title (Data, C), annual_cost (Currency, C, permlevel 1 theo FR-SEC-003), standard_hours_per_year (Float, C), valid_year (Int).
- CLS Time Study: service (Link, C), test_system (Link, K), stage (Select: Tiền phân tích, Phân tích, Hậu phân tích; C), job_title (Link, C), minutes_per_sample (Float), minutes_per_batch (Float), sample_count (Int, số mẫu đã đo), measured_by (Link User), measured_on (Date), is_valid (Check), attachment (Attach, phiếu có chữ ký).

### 3.7 CLS Cost Component, CLS Cost Item, CLS Norm Template

- CLS Cost Component: component_code (NC, VT, DN, DT, KH, QL), component_name, sort_order. Dữ liệu khởi tạo theo docs/calculation-rules.md mục 2.
- CLS Cost Item: cost_item_code (K01..K17), cost_item_name, default_level (1–5), cost_component (Link), rule_code (QT-xx), apply_k_default (Check).
- CLS Norm Template: specialty_group, lines (cost_item, is_mandatory, default_level).

### 3.8 CLS Norm Sheet – Phiếu định mức CLS

| fieldname | Label | Kiểu | Bắt buộc | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| test_system | Hệ thống xét nghiệm | Link CLS Test System | C | Một phiếu Đã duyệt còn hiệu lực cho mỗi hệ thống |
| service, equipment, department | Dịch vụ, Thiết bị, Khoa | Link | C | Lấy theo test_system, chỉ đọc |
| tests_per_tube | Số xét nghiệm bình quân mỗi ống | Float | ĐK | Bắt buộc khi có K01 (KT-10) |
| source_documents | Tài liệu nguồn | Table (file, document_type) | K | Tài liệu hãng, QTKT, kế hoạch chất lượng; đầu vào của AI |
| needs_review | Cần rà soát | Check | K | Bật khi QTKT đổi phiên bản (FR-INT-003) |
| lines | Dòng định mức | Table CLS Norm Line | C | |
| workflow_state | Trạng thái | Link Workflow State | C | Mục 5.1 |
| amended_from | Sửa từ phiên bản | Link CLS Norm Sheet | K | FR-NRM-008 |

CLS Norm Line:

| fieldname | Label | Kiểu | Bắt buộc | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| cost_item | Khoản mục | Link CLS Cost Item | C | |
| item | Mặt hàng | Link CLS Item | ĐK | Bắt buộc với khoản mục vật chất |
| job_title, stage | Chức danh, Công đoạn | Link, Select | ĐK | Bắt buộc với K11 |
| cost_level | Cấp phát sinh | Select | C | 1–5; mặc định theo khoản mục |
| quantity | Định lượng | Float | ĐK | Theo norm_uom; với K11 lấy từ phiếu bấm giờ |
| apply_k | Nhân hệ số k | Check | K | Mặc định theo khoản mục |
| separately_billed | Thanh toán riêng | Check | K | KT-09 |
| supplier_borne | Nhà cung cấp chịu | Check | K | KT-01 |
| line_status | Trạng thái dòng | Select | C | Đề xuất, Đã xác nhận, Từ chối |
| confirmed_by, confirmed_on | Người, thời điểm xác nhận | Link User, Datetime | K | Hệ thống ghi |
| origin | Nguồn gốc dòng | Select | C | Nhập tay, AI, Mẫu, Sao chép |
| evidence_document, evidence_page | Tài liệu, trang dẫn nguồn | Data | K | FR-AI-002 |
| ai_flag | Nhãn AI | Select | K | Không có nguồn, Chưa ánh xạ |
| note | Ghi chú | Small Text | K | |

### 3.9 CLS Volume Period và số liệu đối soát

| fieldname | Label | Kiểu | Bắt buộc | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| test_system | Hệ thống xét nghiệm | Link CLS Test System | C | Duy nhất theo test_system + kỳ + scenario |
| period_from, period_to | Kỳ từ, đến | Date | C | |
| scenario | Kịch bản | Select | C | Thực tế, Kế hoạch, Công suất |
| reported_results | Số kết quả trả | Float | C | Qbn |
| iqc_tests, calibration_tests, rerun_tests, eqa_tests | Test nội kiểm, chuẩn, chạy lại, ngoại kiểm | Float | K | Trống thì ước tính (QT-02) |
| wastage_rate | Tỷ lệ hao hụt | Percent | K | Mặc định 0; nhỏ hơn 100 |
| avg_batch_size | Số mẫu bình quân mỗi mẻ | Float | ĐK | Bắt buộc khi phiếu có dòng cấp 2 |
| machine_minutes | Tổng phút khai thác thiết bị | Float | ĐK | Bắt buộc khi thiết bị chia theo phút |
| his_service_count | Số dịch vụ trên HIS | Float | K | Đối soát sản lượng |
| data_source | Nguồn số liệu | Select | C | Nhập tệp, Nhập tay, Tự động |
| estimated_from_plan | Ước tính từ kế hoạch | Check | K | Hệ thống ghi |

- CLS Stock Issue Actual: item, department, period_from, period_to, quantity (theo norm_uom), import_log.
- CLS Department Cost Actual: department, period_from, period_to, cost_component, amount, import_log.
- CLS Overhead Rate: department, period_from, period_to, cost_item (K13..K15), mode (Tỷ lệ, Đơn giá), rate, amount_per_result, source (Nhập tay, Phân hệ C).

### 3.10 CLS Cost Run – Lần tính giá thành

| fieldname | Label | Kiểu | Bắt buộc | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| run_title | Tên lần tính | Data | C | |
| period_from, period_to | Kỳ tính | Date | C | |
| calc_date | Ngày tính | Date | C | Ngày chọn đơn giá (QT-01) |
| scope_department, scope_group | Phạm vi khoa, nhóm | Link, Select | K | Trống là toàn bộ |
| scope_services | Dịch vụ chọn riêng | Table MultiSelect | K | |
| primary_scenario | Kịch bản chính | Select | C | Mặc định Thực tế |
| compliance_allocation_method | Cách phân bổ kiểm định, hiệu chuẩn | Select | C | Trực tiếp, Theo giá trị tài sản |
| material_threshold, financial_threshold, volume_threshold | Ngưỡng đối soát | Percent | C | Mặc định từ CLS Settings |
| snapshot_file | Ảnh chụp tham số | Attach | K | JSON do hệ thống sinh (FR-CST-007) |
| services_total, services_ok, services_error, services_excluded | Số dịch vụ | Int | K | Hệ thống ghi |
| duration_seconds | Thời lượng chạy | Float | K | NFR-OBS-001 |
| reconciliation_status | Trạng thái đối soát | Select | K | Chưa đối soát, Đạt, Cần giải trình, Không đủ số liệu |
| skip_reconciliation_confirmed_by | Người xác nhận bỏ qua đối soát | Link User | K | FR-REC-006 |
| minutes_attachment | Biên bản hội đồng | Attach | ĐK | Bắt buộc khi duyệt (FR-APR-005) |
| workflow_state | Trạng thái | Link Workflow State | C | Mục 5.2 |
| amended_from | Tính lại từ | Link CLS Cost Run | K | |

Kết quả của lần tính (hệ thống ghi, chỉ đọc):

- CLS Cost Result: cost_run, service, scenario, is_primary, unit_cost (Currency, làm tròn đồng), unit_cost_raw (Float 6), amount_nc, amount_vt, amount_dn, amount_dt, amount_kh, amount_ql, result_status (Đạt, Lỗi, Loại), error_message, warnings (Small Text, mã KT).
- CLS Cost Result Line: cost_result, test_system, cost_item, cost_component, cost_level, item, quantity, k_factor, unit_price, amount_per_result (Float 6), price_source, rule_code, note.
- CLS Reconciliation Line: cost_run, recon_type (Vật chất, Tài chính, Sản lượng), subject_type, subject_name, calculated_value, actual_value, variance_percent, exceeds_threshold, explanation, explained_by, explained_on, attachment.

### 3.11 CLS Settings và nhật ký

- CLS Settings (Single): price_source_priority (bảng thứ tự loại nguồn), include_input_vat (Check, mặc định bật), default_material_threshold 5, default_financial_threshold 5, default_volume_threshold 2, compliance_alert_days 30, background_run_min_services 20, ai_enabled, ai_endpoint, ai_timeout_seconds 120, rules (Table CLS Rule Setting: rule_code, enabled, severity).
- CLS AI Request Log: norm_sheet, requested_by, requested_on, model_version, input_documents, lines_returned, status, error_message.
- CLS Import Log: import_type, file, dry_run, imported_by, imported_on, rows_ok, rows_error, error_report.

## 4. Ma trận quyền

R đọc, W tạo và sửa, S gửi duyệt, A duyệt, – không có quyền. Vai trò khoa bị giới hạn theo department (FR-SEC-002).

| Nhóm DocType | Pricing Officer | Department User | Department Head | Equipment Officer | Accountant | Approver | Auditor | Administrator |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| Dịch vụ, hệ thống xét nghiệm, khoản mục, mẫu | W | R | R | R | R | R | R | W |
| Thiết bị, hồ sơ tuân thủ | R | R | R | W | R | R | R | W |
| Mặt hàng | W | R | R | R | W | R | R | W |
| Nguồn giá | W | – | R | – | W, xác minh | R | R | W |
| Kế hoạch chất lượng, ngoại kiểm, bấm giờ | W | W | W | – | R | R | R | W |
| Chi phí chức danh (annual_cost) | R | – | – | – | W | – | – | W |
| Phiếu định mức | W, S | W, S | W, xác nhận khoa | R | R, thẩm định | R | R | W |
| Sản lượng, xuất kho, chi phí khoa, hệ số cấp 5 | W | R | R | – | W | R | R | W |
| Lần tính và kết quả | W, S | R (khoa mình) | R (khoa mình) | – | R | A | R | R |
| Dòng đối soát (giải trình) | W | – | W (khoa mình) | – | W | R | R | R |
| Cấu hình | R | – | – | – | R | – | R | W |
| Nhật ký AI, nhập liệu | R | – | – | – | R | – | R | R |

## 5. Luồng trạng thái

### 5.1 Phiếu định mức (CLS Norm Sheet)

| Từ | Hành động | Đến | Vai trò | Điều kiện |
| :-- | :-- | :-- | :-- | :-- |
| Nháp | Gửi khoa xác nhận | Chờ khoa xác nhận | Pricing Officer, Department User | Qua KT-07, KT-08, KT-10 |
| Chờ khoa xác nhận | Xác nhận | Chờ thẩm định | Department Head | Mọi dòng khác Đề xuất |
| Chờ khoa xác nhận | Trả lại | Nháp | Department Head | Có lý do |
| Chờ thẩm định | Duyệt | Đã duyệt | Accountant | – |
| Chờ thẩm định | Từ chối | Từ chối | Accountant | Có lý do |
| Đã duyệt | Sửa (amend) | Nháp, phiên bản mới | Pricing Officer | Bản cũ chỉ đọc |

### 5.2 Lần tính (CLS Cost Run)

| Từ | Hành động | Đến | Vai trò | Điều kiện |
| :-- | :-- | :-- | :-- | :-- |
| Nháp | Chạy tính | Đã tính | Pricing Officer | Có ít nhất một dịch vụ trong phạm vi |
| Đã tính | Hoàn tất đối soát | Đã đối soát | Pricing Officer | Mọi dòng vượt ngưỡng có giải trình, hoặc có xác nhận bỏ qua |
| Đã tính, Đã đối soát | Chạy lại | Đã tính | Pricing Officer | Xóa kết quả cũ của lần tính này |
| Đã đối soát | Trình hội đồng | Trình hội đồng | Pricing Officer | Không còn vi phạm mức Chặn |
| Trình hội đồng | Duyệt | Đã duyệt | Approver | Có biên bản đính kèm |
| Trình hội đồng | Trả lại | Trả lại | Approver | Có lý do |
| Trả lại | Mở lại | Nháp | Pricing Officer | – |

## 6. Quan hệ chính

- CLS Service 1–n CLS Test System n–1 CLS Equipment.
- CLS Test System 1–n CLS Norm Sheet (theo phiên bản) 1–n CLS Norm Line n–1 CLS Item, CLS Cost Item.
- CLS Item 1–n CLS Price Source.
- CLS Equipment 1–n CLS Compliance Record.
- CLS Test System 1–n CLS Volume Period.
- CLS Cost Run 1–n CLS Cost Result 1–n CLS Cost Result Line; CLS Cost Run 1–n CLS Reconciliation Line.
