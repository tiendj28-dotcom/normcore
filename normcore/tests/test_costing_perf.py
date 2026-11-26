"""FEAT-017, NFR-PERF-002: 500 dịch vụ, 50.000 dòng định mức tính xong dưới 5 phút, chạy nền, có tiến độ."""

import time
from unittest import mock

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now

from normcore.nc_costing.doctype.nc_costing_run import nc_costing_run as mod
from normcore.nc_costing.doctype.nc_costing_run import writer
from normcore.tests import costing_fixtures as cf

SERVICES, LINES_PER_SERVICE = 500, 100
LIMIT_SECONDS = 300


def _meta(extra=None):
	n = now()
	return {
		"owner": "Administrator",
		"modified_by": "Administrator",
		"creation": n,
		"modified": n,
		"docstatus": 0,
		**(extra or {}),
	}


def make_bulk_world(dept, procedure):
	"""500 dịch vụ, mỗi dịch vụ một bộ định mức "Đã khóa" 100 dòng (chu kỳ theo dòng của DV-TEST-A), sản lượng 1.000."""
	codes = [f"PF-{i:03d}" for i in range(SERVICES)]
	m = _meta()
	frappe.db.bulk_insert(
		"NC Technical Service",
		["name", "service_code", "service_name", "is_active", "idx", *m],
		[(c, c, f"Dịch vụ {c}", 1, 0, *m.values()) for c in codes],
	)
	frappe.db.bulk_insert(
		"NC Service Volume",
		["name", "fiscal_year", "technical_service", "department", "scenario", "volume", "idx", *m],
		[
			(frappe.generate_hash(length=10), 2026, c, dept, "Thực tế 12 tháng", 1000, 0, *m.values())
			for c in codes
		],
	)
	frappe.db.bulk_insert(
		"NC Norm Set",
		["name", "technical_service", "department", "procedure", "version_no", "status", "idx", *m],
		[(f"DM-{c}-{dept}-v1", c, dept, procedure, 1, "Đã khóa", 0, *m.values()) for c in codes],
	)
	base = cf.g.NORMS["DV-TEST-A"]
	rows = []
	for c in codes:
		parent = f"DM-{c}-{dept}-v1"
		for i in range(LINES_PER_SERVICE):
			l = base[i % len(base)]
			rows.append(
				(
					frappe.generate_hash(length=12),
					parent,
					"NC Norm Set",
					"lines",
					i + 1,
					f"L{i + 1:03d}",
					None,
					1,
					"x",
					l.comp,
					cf.RESOURCE_DOCTYPE[l.comp],
					l.res,
					l.headcount,
					float(l.qty),
					float(l.authority) if l.authority is not None else 0,
					float(l.wastage * 100),
					"Quy trình",
					1 if l.excluded else 0,
					"Thanh toán riêng" if l.excluded else None,
					*m.values(),
				)
			)
	frappe.db.bulk_insert(
		"NC Norm Line",
		[
			"name",
			"parent",
			"parenttype",
			"parentfield",
			"idx",
			"line_id",
			"step_id",
			"service_level",
			"procedure_resource_row",
			"component",
			"resource_doctype",
			"resource",
			"headcount",
			"hospital_qty",
			"authority_qty",
			"wastage_rate",
			"basis",
			"is_excluded",
			"exclude_reason",
			*m,
		],
		rows,
	)
	return codes


class TestCostingPerformance(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.addCleanup(frappe.db.rollback)

	def test_TC_COST_14_500_dich_vu_50000_dong_duoi_5_phut(self):
		params, dept, sets = cf.make_golden_world()
		cf.make_golden_allocation(dept)
		codes = make_bulk_world(dept, sets[0].procedure)
		self.assertEqual(
			frappe.db.count("NC Norm Line", {"parent": ["like", "DM-PF-%"]}), SERVICES * LINES_PER_SERVICE
		)
		run = cf.make_golden_run(params, scope_services=[{"technical_service": c} for c in codes])
		with mock.patch("frappe.enqueue") as enq:
			self.assertEqual(run.run_costing(), "Đang tính")
		enq.assert_called_once()
		self.assertEqual(enq.call_args.kwargs["queue"], "long")
		self.assertEqual(len(enq.call_args.kwargs["eligible"]), SERVICES)
		timing = {}
		real = writer.write_results

		def timed(*a, **k):
			t = time.monotonic()
			try:
				return real(*a, **k)
			finally:
				timing["write"] = time.monotonic() - t

		start = time.monotonic()
		with (
			mock.patch("frappe.db.commit"),
			mock.patch("frappe.publish_realtime") as rt,
			mock.patch.object(writer, "write_results", timed),
		):
			status = mod.execute_costing(run.name, enq.call_args.kwargs["eligible"], background=True)
		total = time.monotonic() - start
		print(
			f"\n[TC-COST-14] tính {total - timing['write']:.1f}s, ghi {timing['write']:.1f}s, tổng {total:.1f}s"
		)
		self.assertEqual(status, "Đã tính")
		self.assertLess(total, LIMIT_SECONDS)
		events = [c.args[1]["progress"] for c in rt.call_args_list if c.args[0] == mod.PROGRESS_EVENT]
		self.assertEqual(events, sorted(events))
		self.assertEqual(events[-1], 100)
		self.assertGreater(len(set(events)), 10)
		run.reload()
		self.assertEqual((run.status, run.progress), ("Đã tính", 100))
		self.assertEqual(frappe.db.count("NC Service Cost", {"costing_run": run.name}), SERVICES)
