import json

import frappe
from frappe import _
from frappe.model.document import Document

from normcore.core.importer import ImportFileError
from normcore.costing import accounting
from normcore.costing.allocation_rules import valid_year
from normcore.nc_costing.doctype.nc_account_mapping.nc_account_mapping import mapping_for

LINE_FIELDS = (
	"account_code",
	"account_name",
	"cost_center",
	"amount",
	"cost_category",
	"is_excluded",
	"change_reason",
	"changed_by",
)


def line_dicts(rows):
	return [{f: r.get(f) for f in LINE_FIELDS} for r in rows]


def read_source(source_file):
	"""Nội dung và tên tệp đã tải lên; chỉ đọc được tệp người dùng có quyền đọc."""
	name = frappe.db.get_value("File", {"file_url": source_file})
	if not name or not frappe.has_permission("File", "read", doc=name):
		frappe.throw(_("Không tìm thấy tệp nguồn đã tải lên"), frappe.PermissionError)
	f = frappe.get_doc("File", name)
	return f.get_content(), f.file_name


def fill_from_file(doc):
	"""Đọc `source_file`, thay `lines`, `import_errors`, `error_count`, gán loại theo ánh xạ (FR-ACCT-001..003)."""
	content, filename = read_source(doc.source_file)
	try:
		lines, errors = accounting.parse_lines(
			content, filename, lambda code: bool(frappe.db.exists("NC Cost Center", code))
		)
	except ImportFileError as e:
		frappe.throw(_("Không đọc được tệp: {0}").format(str(e)))
	accounting.assign_categories(lines, mapping_for(doc.accounting_regime))
	doc.set("lines", [{f: ln.get(f) for f in LINE_FIELDS if f in ln} for ln in lines])
	doc.import_errors = json.dumps([e.as_dict() for e in errors], ensure_ascii=False)
	doc.error_count = len(errors)
	doc.set("totals", [])
	recount(doc)


def recount(doc):
	lines = line_dicts(doc.lines)
	doc.line_count = len(lines)
	doc.total_amount = accounting.total_amount(lines)


class NCAccountingImport(Document):
	def before_insert(self):
		if not valid_year(self.fiscal_year):
			frappe.throw(_("Năm tài chính phải từ 2000 đến 2100"))
		if self.source_file:
			fill_from_file(self)

	def validate(self):
		if self.is_new():
			self.status = accounting.STATUS_DRAFT
			return
		db_status = frappe.db.get_value(self.doctype, self.name, "status")
		if self.flags.nc_finalizing:
			return
		if db_status == accounting.STATUS_FINAL:
			frappe.throw(_("Lần nhập {0} đã chốt, không sửa được").format(self.name))
		if self.status != db_status:
			frappe.throw(_("Trạng thái chỉ đổi bằng thao tác Chốt"))
		self.set("totals", [])
		before = self.get_doc_before_save()
		if self.flags.nc_replace_lines:  # đọc lại tệp / gán lại: máy chủ thay dòng (ASM-122)
			recount(self)
			return
		old, new = line_dicts(before.lines), line_dicts(self.lines)
		for ln, prev in zip(self.lines, old, strict=False):
			if ln.cost_category == accounting.EXCLUDED and prev["cost_category"] != accounting.EXCLUDED:
				ln.is_excluded = 1
		new = line_dicts(self.lines)
		errors = accounting.check_line_changes(old, new)
		if errors:
			frappe.throw("<br>".join(_(e) for e in errors), title=_("Dòng chưa hợp lệ"))
		for ln, prev, cur in zip(self.lines, old, new, strict=False):
			if (prev["cost_category"] or None) != (cur["cost_category"] or None) or int(
				bool(prev["is_excluded"])
			) != int(bool(cur["is_excluded"])):
				ln.changed_by = frappe.session.user
		recount(self)

	def on_trash(self):
		if frappe.db.get_value(self.doctype, self.name, "status") == accounting.STATUS_FINAL:
			frappe.throw(_("Lần nhập {0} đã chốt, không xóa được").format(self.name), frappe.PermissionError)
