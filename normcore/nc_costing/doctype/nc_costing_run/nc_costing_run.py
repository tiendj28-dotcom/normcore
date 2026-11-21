from decimal import Decimal

import frappe
from frappe import _
from frappe.model.document import Document

from normcore.costing import engine

DRAFT, CALCULATED, FAILED = "Nháp", "Đã tính", "Tính lỗi"
LOCKED_NORM = "Đã khóa"


def _d(x):
	return Decimal(str(x or 0))


class NCCostingRun(Document):
	@frappe.whitelist()
	def run_costing(self):
		"""FR-COST-003: tính cho mọi bộ định mức "Đã khóa" (DI-06). Việc tính nằm ở normcore.costing.engine."""
		frappe.has_permission("NC Costing Run", "write", doc=self, throw=True)
		if self.status not in (DRAFT, FAILED):
			frappe.throw(_("Chỉ chạy được lần tính giá ở trạng thái Nháp hoặc Tính lỗi"))
		try:
			self._run()
		except Exception:
			self.db_set("status", FAILED)
			raise
		self.db_set("status", CALCULATED)
		return self.status

	def _run(self):
		for name in frappe.get_all("NC Service Cost", {"costing_run": self.name}, pluck="name"):
			frappe.delete_doc("NC Service Cost", name, force=True, ignore_permissions=True)
		params = frappe.get_doc("NC Costing Parameter Set", self.parameter_set)
		rates = {r.job_title: r for r in params.job_title_rates}
		for ns_name in frappe.get_all("NC Norm Set", {"status": LOCKED_NORM}, pluck="name", order_by="name"):
			self._cost_norm_set(frappe.get_doc("NC Norm Set", ns_name), params, rates)

	def _cost_norm_set(self, ns, params, rates):
		priced, missing = [], []
		for line in ns.lines:
			if line.component != "LABOR":
				continue
			rate = rates.get(line.resource)
			if rate is None:  # G5: không bịa đơn giá
				missing.append(f"{line.line_id} ({line.resource})")
				continue
			authority = (
				line.authority_qty or None
			)  # Frappe lưu Float trống thành 0: 0 = chưa có định mức ban hành (ASM-004)
			priced.append(
				(
					line,
					engine.LaborLine(
						line.line_id,
						_d(line.hospital_qty),
						int(line.headcount or 1),
						_d(rate.rate_per_hour),
						_d(authority) if authority is not None else None,
					),
				)
			)
		results = engine.compute_direct_lines([p[1] for p in priced])
		sc = frappe.new_doc("NC Service Cost")
		sc.update(
			{
				"costing_run": self.name,
				"technical_service": ns.technical_service,
				"department": ns.department,
				"norm_set": ns.name,
				"calc_status": "Lỗi" if missing else "Thành công",
				"calc_message": (_("Dòng thiếu đơn giá: ") + ", ".join(missing)) if missing else None,
			}
		)
		total = Decimal(0)
		for (line, _ll), res in zip(priced, results, strict=True):
			total += res.amount
			sc.append(
				"lines",
				{
					"line_type": "Trực tiếp",
					"component": "LABOR",
					"step_id": line.step_id,
					"norm_line_id": line.line_id,
					"resource_label": line.resource,
					"applied_qty": float(res.applied_qty),
					"unit_rate": float(res.unit_rate),
					"amount": float(res.amount),
					"rate_source": params.name,
				},
			)
		sc.direct_labor = float(total)
		sc.insert(ignore_permissions=True)  # kết quả do mã máy chủ ghi; quyền chạy đã kiểm ở run_costing
