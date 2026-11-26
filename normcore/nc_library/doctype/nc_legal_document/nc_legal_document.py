"""NC Legal Document: văn bản pháp lý (FR-LIB-001, FR-LIB-002, FR-LIB-006). Logic thuần ở normcore/library."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, getdate, today

from normcore.library.search import normalize_doc_number
from normcore.library import supersession
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
		self.check_supersessions()
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

	def check_supersessions(self):
		"""FR-LIB-007, FR-LIB-008: kiểm từng dòng thay thế rồi chuẩn hóa (technical-design 2.4)."""
		rows = [
			{
				"idx": r.idx,
				"superseded_document": r.superseded_document,
				"scope": r.scope,
				"superseded_sections": r.superseded_sections,
				"from_date": r.from_date,
			}
			for r in self.get("supersessions") or []
		]
		if not rows:
			return
		targets = {}
		for r in rows:
			b = r["superseded_document"]
			if not b or b == self.name or b in targets:
				continue
			info = frappe.db.get_value("NC Legal Document", b, ["effective_date", "doc_number"], as_dict=True)
			if not info:
				continue
			info["section_nos"] = frappe.get_all(
				"NC Legal Section", filters={"legal_document": b}, pluck="section_no"
			)
			targets[b] = info
		errors = supersession.row_errors(rows, self.name, targets)
		if errors:
			frappe.throw("<br>".join(errors))
		supersession.normalize_rows(rows)
		for r, row in zip(self.supersessions, rows):
			r.superseded_sections = row["superseded_sections"]

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
		from normcore.api.library import apply_supersessions

		apply_supersessions(self)
		if self.flags.get("needs_index"):
			from normcore.api.library import enqueue_index

			enqueue_index(self.name, frappe.session.user)
