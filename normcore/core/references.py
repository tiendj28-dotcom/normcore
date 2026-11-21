"""Xóa bản ghi danh mục đang được tham chiếu (FR-ADM-005, TC-ADM-05).

Frappe chỉ nêu bản ghi tham chiếu đầu tiên; ở đây nêu tất cả (DocType và tên bản ghi, dòng con quy về
bản ghi cha), bằng tiếng Việt. Chạy ở `on_trash`, trước kiểm tra liên kết mặc định của Frappe.
"""

import frappe
from frappe import _
from frappe.model.delete_doc import get_dynamic_linked_docs, get_linked_docs

MAX_LISTED = 10


def check_not_referenced(doc, method=None):
	refs = []
	for link in [*get_linked_docs(doc), *get_dynamic_linked_docs(doc)]:
		ref = (link["reference_doctype"], link["reference_docname"])
		if ref not in refs:
			refs.append(ref)
	if not refs:
		return
	listed = ", ".join(f"{dt} {name}" for dt, name in refs[:MAX_LISTED])
	if len(refs) > MAX_LISTED:
		listed += _(" và {0} bản ghi khác").format(len(refs) - MAX_LISTED)
	frappe.throw(
		_("Không xóa được {0} {1} vì đang được tham chiếu bởi: {2}").format(doc.doctype, doc.name, listed),
		frappe.LinkExistsError,
	)
