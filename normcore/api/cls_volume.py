"""Chuẩn bị dòng nhập sản lượng cận lâm sàng, phút khai thác, xuất kho (FEAT-035, ASM-035-01, 02).

Không whitelisted: chỉ khung nhập (`core/importer.py`) gọi qua `ImportSet.prepare`, ở cả chế độ "thu" và "ghi".
Logic kiểm nằm ở `normcore/costing/cls_volume.py` (hàm thuần).
"""

import frappe

from normcore.core.importer import RowValueError
from normcore.costing import cls_volume


def _labels(errors):
	return [(cls_volume.LABELS.get(f, f), m) for f, m in errors]


def _raise(errors):
	if errors:
		raise RowValueError(_labels(errors))


def prepare_test_system_volume(values):
	"""Đổi mã dịch vụ ngoài sang mã nội bộ, đối chiếu hệ thống xét nghiệm, kiểm số; trả dịch vụ, khoa của hệ thống."""

	def map_lookup(source, code):
		return frappe.db.get_value(
			"NC Service Code Map",
			{
				"source_system": source,
				"external_code": code,
				"parenttype": "NC Technical Service",
			},
			"parent",
		)

	errors = list(cls_volume.volume_errors(values.get))
	system = frappe.db.get_value(
		"NC Test System", values["test_system"], ["technical_service", "department"], as_dict=True
	)
	try:
		service = cls_volume.resolve_service(
			values.get("source_system"),
			values["service_code"],
			map_lookup,
			lambda code: bool(frappe.db.exists("NC Technical Service", code)),
		)
	except ValueError as e:
		errors.append(("service_code", str(e)))
	else:
		errors += cls_volume.system_mismatch(system, service, values.get("department"))
	_raise(errors)
	return {"technical_service": system.technical_service, "department": system.department}


def prepare_equipment_usage(values):
	basis = frappe.db.get_value("NC Equipment", values["equipment"], "allocation_basis")
	_raise(cls_volume.usage_errors(values.get, basis))
	return {}


def prepare_stock_issue(values):
	_raise(cls_volume.stock_errors(values.get))
	return {}
