from decimal import Decimal

import frappe
from frappe.model.document import Document

from normcore.costing import engine


def _d(x):
	return Decimal(str(x or 0))


class NCCostingParameterSet(Document):
	def validate(self):
		self.compute_job_rates()

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
