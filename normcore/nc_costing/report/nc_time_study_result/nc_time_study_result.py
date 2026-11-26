"""Script Report SCR-DSK-016: kết quả bấm giờ (FR-TS-003, FR-TS-005). Số liệu do api.time_study.get_result tính."""

import frappe
from frappe import _

from normcore.api import time_study


def get_columns():
	return [
		{"fieldname": "step_id", "label": _("Mã bước"), "fieldtype": "Data", "width": 90},
		{"fieldname": "step_title", "label": _("Tên bước"), "fieldtype": "Data", "width": 220},
		{"fieldname": "kind_label", "label": _("Loại"), "fieldtype": "Data", "width": 100},
		{
			"fieldname": "resource_label",
			"label": _("Chức danh / thiết bị"),
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"fieldname": "median_minutes",
			"label": _("Trung vị (phút)"),
			"fieldtype": "Float",
			"precision": 2,
			"width": 130,
		},
		{"fieldname": "n", "label": _("Số ca có số liệu"), "fieldtype": "Int", "width": 130},
	]


def execute(filters=None):
	filters = frappe._dict(filters or {})
	columns = get_columns()
	if not filters.get("technical_service") or not filters.get("department"):
		return columns, [], _("Chọn dịch vụ và khoa để xem trung vị số phút từ các ca bấm giờ."), None, []
	result = time_study.get_result(
		filters.technical_service, filters.department, filters.get("procedure") or None
	)
	if not result["n_cases"]:
		return columns, [], _("Chưa có ca bấm giờ nào."), None, []
	kind = {"labor": _("Nhân lực"), "equipment": _("Thiết bị")}
	data = [{**r, "kind_label": kind[r["kind"]]} for r in result["rows"]]
	message = None
	if not result["sufficient"]:
		message = _("Chưa đủ số ca. Trung vị chỉ để tham khảo; áp vào bộ định mức cần xác nhận.")
	summary = [
		{
			"value": f"{result['n_cases']} / {result['min_cases']}",
			"label": _("Số ca / tối thiểu"),
			"datatype": "Data",
			"indicator": "Green" if result["sufficient"] else "Orange",
		}
	]
	if result["first_date"]:
		summary.append(
			{
				"value": f"{frappe.utils.formatdate(result['first_date'])} - {frappe.utils.formatdate(result['last_date'])}",
				"label": _("Từ ngày - đến ngày"),
				"datatype": "Data",
			}
		)
	return columns, data, message, None, summary
