"""NC Legal Document: văn bản pháp lý (FR-LIB-001, FR-LIB-002, FR-LIB-006). Logic thuần ở normcore/library."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, getdate, today

from normcore.library.search import normalize_doc_number
from normcore.library.validity import compute_validity

MAX_FILE_BYTES = 100 * 1024 * 1024  # NFR-SCAL-002, ASM-020-09
ALLOWED_EXT = (".pdf", ".docx")


class DuplicateDocNumberError(frappe.ValidationError):
	pass


class NCLegalDocument(Document):
	def validate(self):
		self.check_duplicate_number()
		self.check_dates()
		self.check_file()
		self.validity_status = compute_validity(self.effective_date, self.expiry_date, getdate(today()))
		self.mark_for_index()

	def check_duplicate_number(self):
		key = normalize_doc_number(self.doc_number)
		rows = frappe.get_all(
			"NC Legal Document", filters={"name": ["!=", self.name or ""]}, fields=["name", "doc_number"]
		)
		for r in rows:
			if normalize_doc_number(r.doc_number) == key:
				link = frappe.utils.get_link_to_form("NC Legal Document", r.name)
				frappe.throw(
					_("Số hiệu {0} trùng với văn bản {1} ({2})").format(
						frappe.bold(self.doc_number), link, r.name
					),
					DuplicateDocNumberError,
				)

	def check_dates(self):
		if (
			self.expiry_date
			and self.effective_date
			and getdate(self.expiry_date) < getdate(self.effective_date)
		):
			frappe.throw(_("Ngày hết hiệu lực phải từ ngày hiệu lực trở đi"))

	def check_file(self):
		url = self.file or ""
		if not url.startswith("/private/files/"):
			frappe.throw(_("Tệp văn bản phải là tệp riêng tư"))
		if not url.lower().endswith(ALLOWED_EXT):
			frappe.throw(_("Chỉ nhận tệp PDF hoặc DOCX"))
		size = frappe.db.get_value("File", {"file_url": url}, "file_size")
		if size and cint(size) > MAX_FILE_BYTES:
			frappe.throw(_("Tệp vượt 100 MB"))

	def mark_for_index(self):
		"""Bản ghi mới, hoặc tệp / cờ QTKT đổi: đặt 'Chưa lập' và xếp tác vụ sau khi lưu (T04)."""
		before = None if self.is_new() else self.get_doc_before_save()
		if (
			before is None
			or before.file != self.file
			or cint(before.is_procedure_guideline) != cint(self.is_procedure_guideline)
		):
			self.index_status = "Chưa lập"
			self.index_error = ""
			self.flags.needs_index = True

	def on_update(self):
		before = self.get_doc_before_save()
		if before and (
			str(before.effective_date) != str(self.effective_date)
			or str(before.expiry_date or "") != str(self.expiry_date or "")
		):
			from normcore.api.library import refresh_section_validity

			refresh_section_validity(self.name)
		if self.flags.get("needs_index"):
			from normcore.api.library import enqueue_index

			enqueue_index(self.name, frappe.session.user)
