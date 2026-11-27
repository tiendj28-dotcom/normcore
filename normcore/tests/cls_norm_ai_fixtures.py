"""Tiện ích test của FEAT-038 (không phải test)."""

import frappe

from normcore.nc_library.doctype.nc_legal_document.library_fixtures import legal_values
from normcore.tests.utils import make_cls_data, make_qc_items, make_test_system

QUOTE_A = "Mỗi test glucose dùng 0,02 ml thuốc thử"
QUOTE_B = "Chuẩn máy mỗi 90 ngày"
TEXT_A = f"1. Thuốc thử. {QUOTE_A}. Hạn dùng sau mở là 28 ngày."


def make_manufacturer_doc(doc_number, resources, section_text=TEXT_A, **kw):
	"""Tài liệu của hãng đã lập chỉ mục, gắn `resources` = [(doctype, name)], kèm một mục `1`."""
	values = legal_values(
		doc_number,
		doc_type="Tài liệu của hãng",
		is_procedure_guideline=0,
		related_resources=[{"linked_doctype": d, "linked_name": n} for d, n in resources],
		**kw,
	)
	values.setdefault("effective_date", "2020-01-01")
	doc = frappe.get_doc(values).insert(ignore_permissions=True)
	frappe.db.set_value("NC Legal Document", doc.name, "index_status", "Đã lập")
	sec = frappe.get_doc(
		{
			"doctype": "NC Legal Section",
			"legal_document": doc.name,
			"section_no": "1",
			"heading": "THUỐC THỬ",
			"plain_text": section_text,
		}
	).insert(ignore_permissions=True)
	return doc, sec


def make_ai_log(purpose="SUGGEST_CLS_NORM"):
	return (
		frappe.get_doc({"doctype": "NC AI Log", "purpose": purpose, "status": "Thành công"})
		.insert(ignore_permissions=True)
		.name
	)


def make_glu_a():
	"""GLU-A (thiết bị EQ_A) cùng các mặt hàng QC_L, CAL, HC_GLU; trả (service, dept)."""
	service, dept, _ = make_cls_data()
	make_test_system("GLU-A", service, dept, "EQ_A", 75)
	make_qc_items()
	return service, dept


def suggestion_values(test_system="GLU-A", **kw):
	dept = frappe.db.get_value("NC Test System", test_system, "department")
	values = {
		"doctype": "NC AI Norm Suggestion",
		"test_system": test_system,
		"department": dept,
		"suggestion_type": "Lượng hóa chất mỗi test",
		"resource_doctype": "NC Item",
		"resource": "HC_GLU",
		"resource_text": "HC_GLU",
		"value": 0.02,
		"uom": "ml",
		"relation": "Chưa có căn cứ",
		"status": "Đề xuất",
		"ai_log": make_ai_log(),
	}
	values.update(kw)
	return values


def make_suggestion(test_system="GLU-A", **kw):
	return frappe.get_doc(suggestion_values(test_system, **kw)).insert(ignore_permissions=True)
