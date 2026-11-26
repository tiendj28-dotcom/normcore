"""API cấu hình AI (FEAT-023, UC-017): trạng thái, kiểm tra kết nối, mức dùng, phiên bản mẫu lệnh, boot."""

import frappe
from frappe import _
from frappe.utils import now_datetime

from normcore.ai import gateway, guard

SETTINGS = "NC AI Settings"
TEMPLATE = "NC Prompt Template"


def boot_session(bootinfo):
	"""FR-AI-015: giao diện đọc `frappe.boot.normcore_ai_enabled` để ẩn nút gọi AI."""
	bootinfo.normcore_ai_enabled = gateway.is_enabled()


@frappe.whitelist()
def get_ai_status():
	"""Mọi người dùng đã đăng nhập; không lộ cấu hình khác."""
	return {"enabled": gateway.is_enabled()}


@frappe.whitelist()
def test_connection():
	"""Nút "Kiểm tra kết nối": theo cấu hình đã lưu, không đổi `enabled` (UC-017 bước 4)."""
	if not frappe.has_permission(SETTINGS, "write"):
		frappe.throw(_("Bạn không có quyền kiểm tra kết nối AI"), frappe.PermissionError)
	res = gateway.ping()
	return {
		"ok": res.ok,
		"status": res.status,
		"message": res.error or _("Kết nối thành công"),
		"duration_ms": res.duration_ms,
	}


@frappe.whitelist()
def get_ai_usage():
	if not frappe.has_permission(SETTINGS, "read"):
		frappe.throw(_("Bạn không có quyền xem cấu hình AI"), frappe.PermissionError)
	budget = gateway.get_settings().monthly_token_budget
	used = gateway.monthly_usage()
	return {
		"used": used,
		"budget": budget,
		"month": now_datetime().strftime("%m/%Y"),
		"blocked": guard.budget_exceeded(used, budget),
	}


@frappe.whitelist()
def new_prompt_version(template_code, system_prompt, user_prompt, output_schema):
	"""FR-AI-014: "sửa" mẫu lệnh = tạo phiên bản mới đang dùng, giữ bản cũ."""
	if not frappe.has_permission(TEMPLATE, "create"):
		frappe.throw(_("Bạn không có quyền tạo mẫu lệnh"), frappe.PermissionError)
	doc = frappe.get_doc(
		{
			"doctype": TEMPLATE,
			"template_code": template_code,
			"system_prompt": system_prompt,
			"user_prompt": user_prompt,
			"output_schema": output_schema,
			"is_active": 1,
		}
	).insert()
	return {"name": doc.name, "version": doc.version}
