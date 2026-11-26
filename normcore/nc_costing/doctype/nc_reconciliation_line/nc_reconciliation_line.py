import frappe
from frappe import _
from frappe.model.document import Document

CALCULATED = "Đã tính"


class NCReconciliationLine(Document):
	"""Dòng đối soát (FR-COST-008, FR-COST-009): do lần tính giá tạo; chỉ sửa được `explanation`."""

	def before_insert(self):
		if not self.flags.get("from_costing"):
			frappe.throw(_("Dòng đối soát do hệ thống tạo khi tính giá"))

	def validate(self):
		prev = None if self.is_new() else self.get_doc_before_save()
		if prev is None:
			if (self.recon_type or "Tài chính") == "Tài chính" and not (
				self.cost_center and self.cost_category
			):
				frappe.throw(_("Dòng đối soát tài chính cần trung tâm chi phí và loại chi phí"))
			return
		changed = [
			f.fieldname
			for f in self.meta.fields
			if f.fieldname != "explanation"
			and f.fieldtype not in ("Section Break", "Column Break")
			and self.get(f.fieldname) != prev.get(f.fieldname)
		]
		if changed:
			frappe.throw(_("Chỉ sửa được giải trình của dòng đối soát"))
		text = (self.explanation or "").strip()
		self.explanation = text or None
		if (prev.explanation or None) != self.explanation:
			status = frappe.db.get_value("NC Costing Run", self.costing_run, "status")
			if status != CALCULATED:
				frappe.throw(_("Lần tính giá ở trạng thái {0}, không sửa được giải trình").format(status))

	def on_trash(self):
		if not self.flags.get("from_costing"):
			frappe.throw(_("Dòng đối soát do hệ thống quản lý, không xóa được"))
