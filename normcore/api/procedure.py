"""API trình soạn quy trình (CLAUDE.md mục 4; NFR-SEC-003): kiểm quyền tường minh trong từng hàm."""

import frappe
from frappe import _

PUBLISHED = "Đã ban hành"


@frappe.whitelist()
def list_procedures():
	"""Quy trình mà người dùng đọc được (frappe.get_list đã lọc theo quyền)."""
	frappe.has_permission("NC Clinical Procedure", "read", throw=True)
	return frappe.get_list(
		"NC Clinical Procedure",
		fields=["name", "technical_service", "department", "version_no", "workflow_state"],
		order_by="modified desc",
		limit_page_length=100,
	)


@frappe.whitelist()
def get_procedure(name):
	if not frappe.has_permission("NC Clinical Procedure", "read", doc=name):
		frappe.throw(_("Bạn không có quyền xem quy trình này"), frappe.PermissionError)
	doc = frappe.get_doc("NC Clinical Procedure", name)
	return {
		"name": doc.name,
		"technical_service": doc.technical_service,
		"department": doc.department,
		"version_no": doc.version_no,
		"workflow_state": doc.workflow_state,
		"can_edit": bool(frappe.has_permission("NC Clinical Procedure", "write", doc=doc))
		and doc.workflow_state != PUBLISHED,
		"steps": [
			{
				"step_id": s.step_id,
				"phase": s.phase,
				"step_title": s.step_title,
				"description": s.description,
			}
			for s in doc.steps
		],
	}


@frappe.whitelist()
def add_step(procedure, phase, step_title, description):
	"""FR-PROC-003: thêm bước vào quy trình Nháp; mã bước do máy chủ cấp (DI-01)."""
	if not frappe.has_permission("NC Clinical Procedure", "write", doc=procedure):
		frappe.throw(_("Bạn không có quyền sửa quy trình này"), frappe.PermissionError)
	missing = [
		label
		for label, value in ((_("Giai đoạn"), phase), (_("Tên bước"), step_title), (_("Mô tả"), description))
		if not (value or "").strip()
	]
	if missing:
		frappe.throw(_("Thiếu: {0}").format(", ".join(missing)))
	doc = frappe.get_doc("NC Clinical Procedure", procedure)
	if doc.workflow_state == PUBLISHED:  # DI-07, FR-WF-008
		frappe.throw(_("Quy trình đã ban hành, không thêm bước được"))
	row = doc.append(
		"steps", {"phase": phase, "step_title": step_title.strip(), "description": description.strip()}
	)
	doc.save()
	return {
		"step_id": row.step_id,
		"phase": row.phase,
		"step_title": row.step_title,
		"description": row.description,
	}
