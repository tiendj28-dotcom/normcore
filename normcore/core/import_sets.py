"""Sổ đăng ký các bộ nhập Excel (FEAT-004). FEAT sau thêm một khai báo + một dòng `register`."""

from normcore.core.importer import Column, ImportSet, register

JOB_GROUPS = ("Bác sĩ", "Điều dưỡng", "Kỹ thuật viên", "Dược sĩ", "Hộ lý", "Khác")

NC_JOB_TITLE = ImportSet(
	key="nc_job_title",
	label="Chức danh",
	doctype="NC Job Title",
	key_field="job_title_code",
	columns=(
		Column("job_title_code", "Mã chức danh", "Data", required=True, example="VD-BS"),
		Column("job_title_name", "Tên chức danh", "Data", required=True, example="Bác sĩ (ví dụ)"),
		Column("job_group", "Nhóm", "Select", options=JOB_GROUPS, example="Bác sĩ"),
	),
)

register(NC_JOB_TITLE)

# FEAT-005, FR-SVC-001: danh mục kỹ thuật. Chuyên khoa ghi mã; mã chưa có thì dòng lỗi (ASM-051).
NC_TECHNICAL_SERVICE = ImportSet(
	key="nc_technical_service",
	label="Dịch vụ kỹ thuật",
	doctype="NC Technical Service",
	key_field="service_code",
	columns=(
		Column("service_code", "Mã dịch vụ", "Data", required=True, example="VD-DV01"),
		Column("service_name", "Tên dịch vụ", "Data", required=True, example="Dịch vụ kỹ thuật (ví dụ)"),
		Column("specialty", "Chuyên khoa", "Link", link_doctype="NC Specialty"),
	),
)

register(NC_TECHNICAL_SERVICE)

# FEAT-010, FR-RES-012 (phần thiết bị, phòng): chỉ trường phẳng ở data-model 3.5 (ASM-084).
# Ô trống: tạo mới lấy mặc định DocType, cập nhật giữ nguyên. Linh kiện, tỷ lệ theo khoa khai trên form.
EQUIPMENT_MODES = ("Mua", "Thuê", "Đặt theo hóa chất", "Liên doanh, liên kết")
ALLOCATION_BASES = ("Giờ kế hoạch", "Số kết quả", "Phút chiếm máy")
FUNDING_SOURCES = ("Ngân sách", "Quỹ phát triển", "Vay", "Liên doanh, liên kết", "Viện trợ", "Khác")

NC_EQUIPMENT = ImportSet(
	key="nc_equipment",
	label="Thiết bị",
	doctype="NC Equipment",
	key_field="equipment_code",
	columns=(
		Column("equipment_code", "Mã thiết bị", "Data", required=True, example="VD-TB01"),
		Column("equipment_name", "Tên thiết bị", "Data", required=True, example="Thiết bị (ví dụ)"),
		Column(
			"department",
			"Khoa quản lý",
			"Link",
			required=True,
			link_doctype="NC Department",
			example="VD-K01",
		),
		Column("equipment_type", "Loại thiết bị", "Link", link_doctype="NC Equipment Type"),
		Column("acquisition_mode", "Hình thức có máy", "Select", options=EQUIPMENT_MODES, example="Mua"),
		Column(
			"allocation_basis",
			"Tiêu chí chia chi phí",
			"Select",
			options=ALLOCATION_BASES,
			example="Giờ kế hoạch",
		),
		Column("in_service_date", "Ngày đưa vào sử dụng", "Date", required=True, example="2022-01-01"),
		Column(
			"funding_source",
			"Nguồn hình thành",
			"Select",
			required=True,
			options=FUNDING_SOURCES,
			example="Ngân sách",
		),
		Column("original_cost", "Nguyên giá", "Float", example=1200000000),
		Column("useful_life_years", "Thời gian sử dụng (năm)", "Float", example=8),
		Column("annual_contract_cost", "Chi phí năm theo hợp đồng", "Float"),
		Column("contract_asset_value", "Giá trị ghi trên hợp đồng", "Float"),
		Column("annual_maintenance_cost", "Bảo trì năm", "Float", example=30000000),
		Column("maintenance_vendor_paid", "Bảo trì do nhà cung cấp chịu", "Check"),
		Column("annual_calibration_cost", "Kiểm định, hiệu chuẩn năm", "Float", example=6000000),
		Column("planned_hours_per_year", "Giờ khai thác kế hoạch năm", "Float", example=2112),
		Column("utilization_rate", "Hệ số sử dụng", "Float", example=0.5),
		Column("power_kw", "Công suất khi chạy (kW)", "Float"),
		Column("power_standby_kw", "Công suất khi chờ (kW)", "Float"),
		Column("run_hours_per_day", "Số giờ chạy mỗi ngày", "Float"),
		Column("standby_hours_per_day", "Số giờ chờ mỗi ngày", "Float"),
		Column("continuous_power", "Cấp điện liên tục", "Check"),
	),
)

register(NC_EQUIPMENT)

NC_ROOM = ImportSet(
	key="nc_room",
	label="Phòng",
	doctype="NC Room",
	key_field="room_code",
	columns=(
		Column("room_code", "Mã phòng", "Data", required=True, example="VD-P01"),
		Column("room_name", "Tên phòng", "Data", required=True, example="Phòng (ví dụ)"),
		Column("department", "Khoa", "Link", required=True, link_doctype="NC Department", example="VD-K01"),
		Column("area_m2", "Diện tích (m²)", "Float", example=40),
		Column("annual_infrastructure_cost", "Chi phí hạ tầng năm", "Float", required=True, example=52800000),
		Column("available_hours_per_year", "Số giờ khai thác năm", "Float", required=True, example=2112),
	),
)

register(NC_ROOM)

# FEAT-009, FR-RES-012, FR-RES-018: mặt hàng và đơn giá (khóa đơn giá là `price_code`, AMD-008).
ITEM_TYPES = (
	"Thuốc",
	"Hóa chất",
	"Dịch truyền",
	"Máu và chế phẩm",
	"Vật tư tiêu hao",
	"Vật tư dùng nhiều lần",
	"Khí y tế",
	"Tiện ích",
	"Chất chuẩn",
	"Vật liệu nội kiểm",
	"Khác",
)

NC_ITEM = ImportSet(
	key="nc_item",
	label="Mặt hàng",
	doctype="NC Item",
	key_field="item_code",
	columns=(
		Column("item_code", "Mã mặt hàng", "Data", required=True, example="VD-MH01"),
		Column("item_name", "Tên mặt hàng", "Data", required=True, example="Mặt hàng (ví dụ)"),
		Column("item_type", "Loại", "Select", required=True, options=ITEM_TYPES, example="Vật tư tiêu hao"),
		Column("uom", "Đơn vị tính", "Data", required=True, example="cái"),
		Column("reuse_count", "Số lần dùng", "Int"),
		Column("equivalent_group", "Nhóm tương đương", "Data"),
		Column("billed_separately", "Thanh toán riêng", "Check"),
		Column("norm_uom", "Đơn vị định mức", "Data"),
		Column("norm_units_per_purchase_unit", "Số đơn vị định mức trong một đơn vị mua", "Float"),
		Column("nominal_tests", "Số test danh nghĩa", "Int"),
		Column("open_stability_days", "Hạn dùng sau mở (ngày)", "Int"),
	),
)

register(NC_ITEM)

PRICE_SOURCES = ("Trúng thầu", "Hợp đồng", "Hóa đơn", "Giá công bố", "Báo giá")

# Không có cột xác minh hay tệp chứng từ: xác minh chỉ qua nút trên form (FR-RES-016)
NC_ITEM_PRICE = ImportSet(
	key="nc_item_price",
	label="Đơn giá",
	doctype="NC Item Price",
	key_field="price_code",
	columns=(
		Column("price_code", "Mã đơn giá", "Data", required=True, example="VD-DG01"),
		Column("item", "Mặt hàng", "Link", required=True, link_doctype="NC Item", example="VD-MH01"),
		Column("unit_price", "Đơn giá (đã gồm thuế GTGT)", "Float", required=True, example=1500),
		Column(
			"price_source", "Nguồn giá", "Select", required=True, options=PRICE_SOURCES, example="Hóa đơn"
		),
		Column("document_no", "Số chứng từ", "Data", required=True, example="HD-0001"),
		Column("document_date", "Ngày chứng từ", "Date", required=True, example="2026-01-10"),
		Column("valid_from", "Hiệu lực từ", "Date", required=True, example="2026-01-10"),
		Column("valid_to", "Hiệu lực đến", "Date"),
	),
)

register(NC_ITEM_PRICE)

# FEAT-033, UC-020 1a, FR-CMP-001: hồ sơ tuân thủ thiết bị, khóa `record_code` (AMD-009, ASM-103).
# Tệp chứng từ nhập bằng đường dẫn tệp private đã tải lên; không có cột trạng thái, khoa (hệ thống tính).
COMPLIANCE_RECORD_TYPES = ("Kiểm định", "Hiệu chuẩn", "Kiểm xạ", "Giấy phép an toàn bức xạ", "Khác")

NC_EQUIPMENT_COMPLIANCE = ImportSet(
	key="nc_equipment_compliance",
	label="Hồ sơ tuân thủ thiết bị",
	doctype="NC Equipment Compliance",
	key_field="record_code",
	columns=(
		Column("record_code", "Mã hồ sơ", "Data", required=True, example="VD-HS01"),
		Column(
			"equipment", "Thiết bị", "Link", required=True, link_doctype="NC Equipment", example="VD-TB01"
		),
		Column(
			"record_type",
			"Loại hồ sơ",
			"Select",
			required=True,
			options=COMPLIANCE_RECORD_TYPES,
			example="Kiểm định",
		),
		Column("cycle_months", "Chu kỳ (tháng)", "Int", required=True, example=12),
		Column("provider", "Đơn vị thực hiện", "Data", required=True, example="Trung tâm kiểm định"),
		Column(
			"cost_per_time", "Chi phí mỗi lần (đã gồm thuế GTGT)", "Float", required=True, example=5000000
		),
		Column("performed_on", "Ngày thực hiện", "Date", required=True, example="2026-01-10"),
		Column("expiry_date", "Ngày hết hạn", "Date", required=True, example="2027-01-10"),
		Column(
			"attachment",
			"Tệp chứng từ (đường dẫn tệp private)",
			"Data",
			required=True,
			example="/private/files/kd-tb01.pdf",
		),
		Column("note", "Ghi chú", "Data"),
	),
)

register(NC_EQUIPMENT_COMPLIANCE)
