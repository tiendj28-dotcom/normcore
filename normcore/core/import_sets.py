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
