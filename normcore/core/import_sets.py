"""Sổ đăng ký các bộ nhập Excel (FEAT-004). FEAT sau thêm một khai báo + một dòng `register`."""

from normcore.core.importer import Column, ImportSet, register
from normcore.costing.accounting import COST_CATEGORIES, REGIMES

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

# FEAT-031, FR-CLS-008 (phần hệ thống xét nghiệm, ASM-116): kế hoạch chất lượng và hồ sơ tuân thủ đăng ký ở FEAT của chúng.
# Tỷ lệ nhập theo phần trăm (2 nghĩa là 2%). Ô trống: tạo mới lấy mặc định DocType, cập nhật giữ nguyên.
NC_TEST_SYSTEM = ImportSet(
	key="nc_test_system",
	label="Hệ thống xét nghiệm",
	doctype="NC Test System",
	key_field="test_system_code",
	columns=(
		Column("test_system_code", "Mã hệ thống", "Data", required=True, example="GLU-A"),
		Column(
			"technical_service",
			"Mã dịch vụ",
			"Link",
			required=True,
			link_doctype="NC Technical Service",
			example="GLU",
		),
		Column("department", "Mã khoa", "Link", required=True, link_doctype="NC Department", example="HS"),
		Column(
			"main_equipment",
			"Mã thiết bị chính",
			"Link",
			required=True,
			link_doctype="NC Equipment",
			example="EQ_A",
		),
		Column("volume_share_pct", "Tỷ trọng sản lượng (%)", "Float", required=True, example=75),
		Column("machine_minutes_per_case", "Phút chiếm máy một ca", "Float"),
		Column("est_rerun_rate", "Tỷ lệ chạy lại ước tính (%)", "Float", example=2),
		Column("est_wastage_rate", "Tỷ lệ hao hụt ước tính (%)", "Float", example=3),
		Column("status", "Trạng thái", "Select", options=("Đang dùng", "Ngừng dùng")),
	),
)

register(NC_TEST_SYSTEM)

# FEAT-016, FR-ACCT-009: bảng ánh xạ tài khoản; khóa ghép (chế độ, tiền tố) (ASM-124).
NC_ACCOUNT_MAPPING = ImportSet(
	key="nc_account_mapping",
	label="Bảng ánh xạ tài khoản",
	doctype="NC Account Mapping",
	key_field="accounting_regime",
	key_fields=("accounting_regime", "account_prefix"),
	columns=(
		Column(
			"accounting_regime",
			"Chế độ kế toán",
			"Select",
			required=True,
			options=REGIMES,
			example="Hành chính sự nghiệp",
		),
		Column("account_prefix", "Tiền tố tài khoản", "Data", required=True, example="61111"),
		Column(
			"cost_category", "Loại chi phí", "Select", required=True, options=COST_CATEGORIES, example="LABOR"
		),
		Column("note", "Ghi chú", "Data"),
	),
)

register(NC_ACCOUNT_MAPPING)

# FEAT-016, FR-ACCT-007: sản lượng dịch vụ theo khóa ghép (năm, dịch vụ, khoa, kịch bản).
SCENARIOS = ("Thực tế 12 tháng", "Kế hoạch", "Công suất")

NC_SERVICE_VOLUME = ImportSet(
	key="nc_service_volume",
	label="Sản lượng dịch vụ",
	doctype="NC Service Volume",
	key_field="fiscal_year",
	key_fields=("fiscal_year", "technical_service", "department", "scenario"),
	columns=(
		Column("fiscal_year", "Năm tài chính", "Int", required=True, example=2026),
		Column(
			"technical_service",
			"Mã dịch vụ",
			"Link",
			link_doctype="NC Technical Service",
			required=True,
			example="DV-TEST-A",
		),
		Column("department", "Mã khoa", "Link", link_doctype="NC Department", required=True, example="K01"),
		Column(
			"scenario",
			"Kịch bản sản lượng",
			"Select",
			required=True,
			options=SCENARIOS,
			example="Thực tế 12 tháng",
		),
		Column("volume", "Sản lượng", "Float", required=True, example=4000),
	),
)

register(NC_SERVICE_VOLUME)

# FEAT-016, FR-ACCT-010: tiêu chí phân bổ cấp 1 theo (năm, trung tâm chi phí).
NC_COST_CENTER_DRIVER = ImportSet(
	key="nc_cost_center_driver",
	label="Tiêu chí trung tâm chi phí",
	doctype="NC Cost Center Driver",
	key_field="fiscal_year",
	key_fields=("fiscal_year", "cost_center"),
	columns=(
		Column("fiscal_year", "Năm tài chính", "Int", required=True, example=2026),
		Column(
			"cost_center",
			"Mã trung tâm chi phí",
			"Link",
			link_doctype="NC Cost Center",
			required=True,
			example="K01",
		),
		Column("headcount", "Số nhân lực", "Float", example=20),
		Column("area_m2", "Diện tích (m²)", "Float"),
		Column("revenue", "Doanh thu", "Float"),
	),
)

register(NC_COST_CENTER_DRIVER)
