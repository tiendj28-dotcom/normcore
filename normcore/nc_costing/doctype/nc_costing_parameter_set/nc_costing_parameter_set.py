from decimal import Decimal

import frappe
from frappe import _
from frappe.model.document import Document

from normcore.costing import engine, parameters


def _d(x):
	return Decimal(str(x or 0))


def locked_runs(name):
	"""Các lần tính giá "Đã khóa" đang dùng bộ tham số (ASM-068)."""
	return frappe.get_all(
		"NC Costing Run", filters={"parameter_set": name, "status": "Đã khóa"}, pluck="name"
	)


def is_in_use(name):
	"""FR-RES-011: đã có cờ `is_locked` hoặc có lần tính giá khóa trỏ tới."""
	return bool(frappe.db.get_value("NC Costing Parameter Set", name, "is_locked")) or bool(locked_runs(name))


class NCCostingParameterSet(Document):
	def validate(self):
		self.check_not_in_use()
		self.fill_defaults()
		errors = parameters.check_ranges(self.as_dict())
		if errors:
			frappe.throw("<br>".join(_(e) for e in errors))
		self.compute_job_rates()

	def on_trash(self):
		self.check_not_in_use()

	def onload(self):
		self.set_onload("in_use", bool(self.name) and is_in_use(self.name))

	def check_not_in_use(self):
		"""FR-RES-011, TC-RES-06: bộ đang được dùng thì từ chối sửa, xóa; nhân bản để có bản sửa được."""
		if self.is_new() or not is_in_use(self.name):
			return
		runs = locked_runs(self.name)
		which = ", ".join(runs) if runs else _("đã đánh dấu đã dùng")
		frappe.throw(
			_(
				"Bộ tham số {0} đang được lần tính giá khóa sử dụng ({1}), không sửa hoặc xóa được. Hãy nhân bản thành bộ mới."
			).format(self.name, which),
			frappe.ValidationError,
		)

	def fill_defaults(self):
		"""Bản ghi cũ (trước FEAT-011) có thể trống các trường mới: điền mặc định (ASM-065)."""
		for key, value in parameters.DEFAULTS.items():
			if self.get(key) in (None, ""):
				self.set(key, value)

	@frappe.whitelist()
	def duplicate(self):
		"""FR-RES-011: nhân bản thành bộ mới chưa khóa; trả tên bộ mới."""
		frappe.has_permission("NC Costing Parameter Set", "create", throw=True)
		frappe.has_permission("NC Costing Parameter Set", "read", doc=self, throw=True)
		new = frappe.copy_doc(self)
		new.set("is_locked", 0)  # Document.is_locked là property của Frappe (khóa tệp), phải đi qua set()
		new.title = _("{0} (bản sao)").format(self.title)
		new.insert()
		return new.name

	def compute_job_rates(self):
		"""FR-RES-010, BR-COST-001: gọi engine.job_rate; tỷ lệ đóng góp là Percent nên chia 100."""
		rate = _d(self.employer_contribution_rate) / 100
		for row in self.job_title_rates:
			override = _d(row.annual_cost_override) or None  # 0/trống = dùng công thức (ASM-002)
			res = engine.job_rate(
				_d(self.base_salary),
				_d(row.salary_coefficient),
				_d(row.allowance_coefficient),
				rate,
				_d(row.other_annual_income),
				_d(self.working_days_per_year),
				_d(self.working_hours_per_day),
				override,
			)
			row.annual_cost = float(res.annual_cost)
			row.rate_per_hour = float(res.hourly_rate)
