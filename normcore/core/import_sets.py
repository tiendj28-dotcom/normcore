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

# FEAT-009, FR-RES-012, FR-RES-018: mặt hàng và đơn giá (khóa đơn giá là `price_code`, AMD-005).
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
