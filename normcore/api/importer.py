"""API nhập Excel (FEAT-004, ADR-012; CLAUDE.md mục 4): kiểm quyền tường minh trong từng hàm."""

import frappe
from frappe import _

from normcore.core import import_sets  # đăng ký các bộ nhập
from normcore.core import importer as core

SAVEPOINT = "nc_import_row"


def _get_set(key):
	try:
		return core.get_import_set(key)
	except KeyError:
		frappe.throw(_("Không có bộ nhập '{0}'").format(key))


def _require(doctype, ptype):
	if not frappe.has_permission(doctype, ptype):
		frappe.throw(
			_("Bạn không có quyền {0} {1}").format(
				_("nhập dữ liệu vào") if ptype == "create" else _("xem"), doctype
			),
			frappe.PermissionError,
		)


@frappe.whitelist()
def list_import_sets():
	"""Bộ nhập mà người dùng hiện tại tạo được bản ghi."""
	return [
		{"key": s.key, "label": s.label, "doctype": s.doctype}
		for s in core.REGISTRY.values()
		if frappe.has_permission(s.doctype, "create")
	]


def build_template_file(import_set_key):
	"""(tên tệp, nội dung) của tệp mẫu; chỉ cần quyền đọc DocType đích (G6)."""
	s = _get_set(import_set_key)
	_require(s.doctype, "read")
	return f"mau-nhap-{s.key}.xlsx", core.build_template(s)


@frappe.whitelist()
def download_template(import_set):
	filename, content = build_template_file(import_set)
	frappe.response["filename"] = filename
	frappe.response["filecontent"] = content
	frappe.response["type"] = "binary"


def run_import(import_set_key, content, mode, filename=None):
	s = _get_set(import_set_key)
	if mode not in (core.MODE_DRY, core.MODE_WRITE):
		frappe.throw(_("Chế độ không hợp lệ"))
	_require(s.doctype, "create")
	dt, key_field = s.doctype, s.key_field

	def lookup(key):
		name = frappe.db.get_value(dt, {key_field: key}, "name")
		if not name:
			return None
		return frappe.db.get_value(dt, name, [c.fieldname for c in s.columns], as_dict=True)

	def can_update(key):
		return bool(frappe.has_permission(dt, "write", doc=frappe.db.get_value(dt, {key_field: key}, "name")))

	def write(action, key, values):
		frappe.db.savepoint(SAVEPOINT)
		log_len = len(frappe.local.message_log)
		try:
			if action == "tao":
				doc = frappe.get_doc({"doctype": dt, **values})
				doc.insert()
			else:
				doc = frappe.get_doc(dt, frappe.db.get_value(dt, {key_field: key}, "name"))
				doc.update(values)
				doc.save()
		except Exception as e:
			frappe.db.rollback(save_point=SAVEPOINT)
			del frappe.local.message_log[log_len:]  # lỗi dòng nằm trong bảng lỗi, không bật hộp thoại
			raise ValueError(_clean(e)) from None

	result = core.process(
		s,
		content,
		mode,
		lookup,
		write,
		link_exists=lambda link_dt, v: bool(frappe.db.exists(link_dt, v)),
		can_update=can_update,
		filename=filename,
	)
	return result.as_dict()


def _clean(e):
	from frappe.utils import strip_html

	return strip_html(str(e)) or e.__class__.__name__


@frappe.whitelist()
def import_file(import_set, file_url, mode="thu"):
	"""Nhập tệp .xlsx đã tải lên (File riêng tư). mode: 'thu' (không ghi) hoặc 'ghi'."""
	s = _get_set(import_set)
	_require(s.doctype, "create")
	name = frappe.db.get_value("File", {"file_url": file_url})
	if not name or not frappe.has_permission("File", "read", doc=name):
		frappe.throw(_("Không tìm thấy tệp đã tải lên"), frappe.PermissionError)
	file_doc = frappe.get_doc("File", name)
	return run_import(import_set, file_doc.get_content(), mode, filename=file_doc.file_name)
