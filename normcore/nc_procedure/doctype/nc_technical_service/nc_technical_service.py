import frappe
from frappe import _
from frappe.model.document import Document

from normcore.procedure import service_rules


class NCTechnicalService(Document):
	def validate(self):
		self.validate_departments()
		self.validate_paraclinical()
		self.validate_external_codes()
		self.validate_price_history()

	def validate_departments(self):
		"""Một khoa chỉ xuất hiện một lần trong khoa thực hiện (FR-SVC-003, ASM-056)."""
		seen = set()
		for row in self.departments or []:
			if row.department in seen:
				frappe.throw(
					_("Khoa {0} bị gán hai lần cho dịch vụ {1}").format(row.department, self.service_code)
				)
			seen.add(row.department)

	def validate_paraclinical(self):
		"""FR-SVC-008, FR-SVC-010, FR-SVC-011: hàm thuần ở procedure/service_rules.py."""
		values = {
			f: self.get(f)
			for f in (
				"service_code",
				"is_paraclinical",
				"cls_group",
				"result_unit",
				"is_panel",
				"is_send_out",
				"send_out_price",
			)
		}
		values["panel_components"] = [c.as_dict() for c in self.panel_components or []]
		errors = service_rules.cls_errors(values)
		if errors:
			frappe.throw("<br>".join(_(e) for e in errors))
		if not self.is_paraclinical and not self.is_new() and self.get_doc_before_save():
			if self.get_doc_before_save().is_paraclinical:
				systems = frappe.get_all("NC Test System", {"technical_service": self.name}, pluck="name")
				if systems:
					frappe.throw(
						_(
							"Không bỏ được cờ cận lâm sàng của dịch vụ {0} khi còn hệ thống xét nghiệm: {1}"
						).format(self.service_code, ", ".join(systems))
					)

	def validate_external_codes(self):
		"""FR-SVC-009, DI-09: một cặp (hệ thống nguồn, mã ngoài) chỉ thuộc một dịch vụ."""
		rows = [r.as_dict() for r in self.external_codes or []]
		for r in self.external_codes or []:
			r.external_code = service_rules.normalize_code(r.external_code)
		dups = service_rules.duplicate_codes(rows)
		if dups:
			system, code = dups[0]
			frappe.throw(
				_("Mã {0} {1} bị khai hai lần trong dịch vụ {2}").format(system, code, self.service_code)
			)
		if not rows:
			return
		mine = {service_rules.code_key(r["source_system"], r["external_code"]) for r in rows}
		others = frappe.get_all(
			"NC Service Code Map",
			filters={"parenttype": "NC Technical Service", "parent": ["!=", self.name or ""]},
			fields=["parent", "source_system", "external_code"],
		)
		for o in others:
			if service_rules.code_key(o.source_system, o.external_code) in mine:
				name = frappe.db.get_value("NC Technical Service", o.parent, "service_name")
				frappe.throw(
					_("Mã {0} {1} đã gắn với dịch vụ {2} — {3}").format(
						o.source_system, o.external_code, o.parent, name
					)
				)

	def validate_price_history(self):
		"""DI-07, FR-PRICE-010: `approved_prices` chỉ thêm dòng qua api.price_proposal (flags.price_history_write)."""
		if self.flags.price_history_write:
			return
		before = self.get_doc_before_save()
		old = [self._history_key(r) for r in (before.approved_prices if before else [])]
		new = [self._history_key(r) for r in self.approved_prices or []]
		if old != new:
			frappe.throw(_("Lịch sử giá chỉ ghi qua phê duyệt phương án giá, không sửa tay"))

	@staticmethod
	def _history_key(row):
		return (
			row.name,
			row.price_category,
			str(row.price),
			str(row.effective_date),
			row.price_proposal,
			row.authority_doc_no,
		)
