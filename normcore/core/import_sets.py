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
