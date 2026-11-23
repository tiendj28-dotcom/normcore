import frappe

from normcore.costing import parameters

DOCTYPE = "NC Costing Parameter Set"


def execute():
	"""FEAT-011 (ASM-072): bộ tham số có trước khi thêm trường mới được điền mặc định cho ô trống (NULL hoặc rỗng), không ghi đè giá trị đã có; cột số mới đã nhận mặc định lúc ALTER TABLE."""
	for name in frappe.get_all(DOCTYPE, pluck="name"):
		current = frappe.db.get_value(DOCTYPE, name, list(parameters.DEFAULTS), as_dict=True)
		missing = {k: v for k, v in parameters.DEFAULTS.items() if current.get(k) in (None, "")}
		if missing:
			frappe.db.set_value(DOCTYPE, name, missing, update_modified=False)
