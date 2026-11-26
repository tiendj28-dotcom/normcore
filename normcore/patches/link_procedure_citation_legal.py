"""NORM-65 (ASM-046): NC Procedure Citation.legal_document / legal_section từ Data sang Link.
Khớp được thì đổi sang tên bản ghi; không khớp được thì ghi vào đầu `quote` "[Căn cứ cũ: …]" và để trống. Chạy lại không đổi gì thêm."""

import frappe

from normcore.procedure.citation_link import convert_row


def execute():
	frappe.reload_doc("nc_procedure", "doctype", "nc_procedure_citation")
	documents = dict(frappe.get_all("NC Legal Document", fields=["name", "doc_number"], as_list=True))
	sections = {
		r[0]: (r[1], r[2])
		for r in frappe.get_all(
			"NC Legal Section", fields=["name", "legal_document", "section_no"], as_list=True
		)
	}
	rows = frappe.db.sql(
		"""SELECT name, legal_document, legal_section, quote FROM `tabNC Procedure Citation`
		WHERE IFNULL(legal_document, '') != '' OR IFNULL(legal_section, '') != ''""",
		as_dict=True,
	)
	for r in rows:
		doc, sec, quote = convert_row(r.legal_document, r.legal_section, r.quote, documents, sections)
		if (doc, sec, quote) != (r.legal_document, r.legal_section, r.quote):
			frappe.db.set_value(
				"NC Procedure Citation",
				r.name,
				{"legal_document": doc, "legal_section": sec, "quote": quote},
				update_modified=False,
			)
