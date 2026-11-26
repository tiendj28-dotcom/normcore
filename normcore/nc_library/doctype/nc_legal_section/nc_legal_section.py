"""NC Legal Section: mục của văn bản (FR-LIB-003, FR-LIB-012). FULLTEXT theo ADR-006."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, today

from normcore.library.validity import compute_section_validity

FT_INDEX = "nc_section_ft"


class NCLegalSection(Document):
	def validate(self):
		if not (self.plain_text or "").strip():
			frappe.throw(_("Văn bản thuần của mục không được để trống"))
		dup = frappe.db.exists(
			"NC Legal Section",
			{
				"legal_document": self.legal_document,
				"section_no": self.section_no,
				"name": ["!=", self.name or ""],
			},
		)
		if dup:
			frappe.throw(_("Số mục {0} đã có trong văn bản này").format(self.section_no))
		doc_status = frappe.db.get_value("NC Legal Document", self.legal_document, "validity_status")
		self.validity_status = compute_section_validity(doc_status, self.expiry_date, getdate(today()))


def on_doctype_update():
	"""Chỉ mục FULLTEXT trên (heading, plain_text); idempotent, chạy khi bench migrate."""
	if frappe.db.sql("SHOW INDEX FROM `tabNC Legal Section` WHERE Key_name = %s", (FT_INDEX,)):
		return
	frappe.db.sql_ddl(
		f"ALTER TABLE `tabNC Legal Section` ADD FULLTEXT INDEX {FT_INDEX} (heading, plain_text)"
	)
