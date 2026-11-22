from datetime import date
from decimal import Decimal

import frappe
from frappe.model.document import Document
from frappe.utils import getdate

from normcore.costing import resources

_FIELDS = (
	"acquisition_mode",
	"allocation_basis",
	"original_cost",
	"useful_life_years",
	"annual_contract_cost",
	"contract_asset_value",
	"annual_maintenance_cost",
	"annual_calibration_cost",
	"planned_hours_per_year",
	"utilization_rate",
	"power_kw",
	"power_standby_kw",
	"run_hours_per_day",
	"standby_hours_per_day",
)


def _d(x):
	return Decimal(str(x or 0))


class NCEquipment(Document):
	def validate(self):
		# FR-RES-005, 019..022, 025; DI-10
		errors = resources.validate_equipment({k: self.get(k) for k in _FIELDS})
		errors += self.validate_components()
		errors += resources.validate_allocations(
			[(r.department, r.share_pct) for r in self.department_allocations]
		)
		if errors:
			frappe.throw("<br>".join(errors), title="Thiết bị chưa hợp lệ")

	def validate_components(self):
		errors = []
		for r in self.components:
			if _d(r.replacement_cost) < 0 or _d(r.life_value) <= 0:
				errors.append(f"Linh kiện {r.component_name}: giá thay thế không âm, tuổi thọ lớn hơn 0")
		return errors

	def indicative(self, on: date | None = None, expired_mode: str | None = resources.ZERO) -> dict:
		"""FR-RES-006, 007: khấu hao năm và đơn giá giờ máy tại `on`; không lưu (data-model 3.5)."""
		on = getdate(on) if on else getdate()
		mode = self.acquisition_mode
		in_service = getdate(self.in_service_date) if self.in_service_date else None
		machine = resources.machine_annual(
			mode,
			self.original_cost,
			self.useful_life_years,
			in_service,
			self.annual_contract_cost,
			on,
			expired_mode,
		)
		share = Decimal(1)
		if self.department_allocations:
			by_dept = {r.department: _d(r.share_pct) for r in self.department_allocations}
			share = by_dept.get(self.department, Decimal(100)) / 100
		annual = resources.equipment_annual(
			machine,
			self.annual_maintenance_cost,
			self.annual_calibration_cost,
			[(c.replacement_cost, c.life_basis, c.life_value, c.vendor_paid) for c in self.components],
			mode,
			bool(self.maintenance_vendor_paid),
			share,
		)
		out = {
			"annual_depreciation": float(machine),
			"annual_equipment_cost": float(annual),
			"expired": bool(
				mode == resources.BUY
				and in_service
				and self.useful_life_years
				and resources.is_expired(in_service, self.useful_life_years, on)
			),
			"hourly_rate": None,
		}
		if self.allocation_basis == resources.BASIS_HOURS:
			out["hourly_rate"] = float(
				resources.machine_hourly_rate(annual, self.planned_hours_per_year, self.utilization_rate)
			)
		return out
