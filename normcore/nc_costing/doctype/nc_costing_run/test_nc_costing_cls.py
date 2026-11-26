"""FEAT-036: lần tính cận lâm sàng trên site với bộ dữ liệu vàng 2A."""

import sys
from decimal import Decimal as D

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.tests import cls_fixtures as fx

sys.path.insert(0, frappe.get_app_path("normcore", "..", "docs", "golden"))
import golden_cls as g


class TestNCCostingCls(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.world = fx.make_cls_golden()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _run(self, **kw):
		run = fx.make_run(self.world, **kw)
		run.run_costing(confirm_ineligible=1)
		return run.reload()

	def _cost(self, run, service="GLU"):
		name = frappe.db.get_value("NC Service Cost", {"costing_run": run.name, "technical_service": service})
		return frappe.get_doc("NC Service Cost", name)

	def test_TC_CLS_10_dich_vu_GLU_tren_site(self):
		run = self._run()
		self.assertEqual(run.status, "Đã tính")
		sc = self._cost(run)
		self.assertEqual(sc.calc_status, "Thành công", sc.calc_message)
		per, _weighted, eqa, direct, _qsum = g.service_direct()
		self.assertEqual(sc.eqa_cost, float(eqa))
		self.assertEqual(
			round(
				sum(
					sc.get(f)
					for f in (
						"direct_labor",
						"direct_drug",
						"direct_supply",
						"direct_equipment",
						"direct_infra",
						"direct_utility",
					)
				),
				2,
			),
			float(direct),
		)
		self.assertEqual(
			{r.test_system: (r.direct_cost, r.k_factor, r.share_pct) for r in sc.test_system_costs},
			{"GLU-A": (float(per["GLU-A"]), 1.108247, 75.0), "GLU-B": (float(per["GLU-B"]), 1.221649, 25.0)},
		)
		self.assertTrue(sc.is_paraclinical)

	def _other(self, run):
		return self._cost(run, "DV-TEST-A")

	def _expect_error(self, text):
		run = self._run()
		sc = self._cost(run)
		self.assertEqual(sc.calc_status, "Lỗi")
		self.assertIn(text, sc.calc_message)
		self.assertEqual(len(sc.lines), 0)
		other = self._other(run)
		self.assertEqual(other.calc_status, "Thành công")  # dịch vụ khác vẫn tính (FR-COST-023)
		self.assertEqual(run.status, "Đã tính")

	def test_TC_CLS_15_dung_dich_vu_GLU_tren_site(self):
		"""Bốn ca của TC-CLS-15; mỗi ca chạy lại từ dữ liệu sạch (rollback giữa các ca)."""

		def a():
			frappe.db.delete("NC Test System Volume", {"test_system": "GLU-B"})
			return "Hệ thống GLU-B thiếu sản lượng năm 2026"

		def b():
			frappe.db.set_value("NC Test System Volume", {"test_system": "GLU-A"}, "patient_results", 0)
			return "Hệ thống GLU-A có số kết quả trả bằng 0"

		def c():
			frappe.db.set_value("NC Test System Volume", {"test_system": "GLU-A"}, "avg_batch_size", None)
			return "Hệ thống GLU-A có dòng Theo mẻ (L04) nhưng thiếu cỡ mẻ bình quân"

		def d():
			frappe.db.delete("NC Test System Volume", {"test_system": ["in", ["GLU-A", "GLU-B"]]})
			frappe.db.set_value("NC Test System", "GLU-A", "volume_share_pct", 60)
			frappe.db.set_value("NC Test System", "GLU-B", "volume_share_pct", 30)
			return "Tổng tỷ trọng sản lượng các hệ thống của dịch vụ GLU tại khoa XN là 90%, khác 100%"

		for i, make in enumerate((a, b, c, d)):
			with self.subTest(ca="abcd"[i]):
				frappe.db.savepoint(f"cls15_{i}")
				text = make()
				self._expect_error(text)
				frappe.db.rollback(save_point=f"cls15_{i}")

	def test_TC_CLS_37_canh_bao_tren_lan_tinh(self):
		frappe.get_doc(
			{
				"doctype": "NC Equipment Type",
				"type_code": "XN-BB",
				"type_name": "Máy xét nghiệm bắt buộc",
				"compliance_required": 1,
			}
		).insert(ignore_permissions=True)
		frappe.db.set_value("NC Equipment", "EQ_A", "equipment_type", "XN-BB")
		frappe.db.set_value(
			"NC Equipment Compliance",
			{"equipment": "EQ_A"},
			{"performed_on": "2025-01-01", "expiry_date": "2025-12-31"},
		)
		# V8: sản lượng thấp của GLU-A
		frappe.db.set_value(
			"NC Test System Volume",
			{"test_system": "GLU-A"},
			{
				"patient_results": 1000,
				"iqc_tests": None,
				"calibration_tests": None,
				"rerun_tests": None,
				"eqa_tests": None,
				"wastage_rate": None,
			},
		)
		run = self._run()
		self.assertEqual(run.status, "Đã tính")
		self.assertIn("EQ_A", run.run_warnings)
		self.assertIn("không có hồ sơ tuân thủ còn hạn", run.run_warnings)
		sc = self._cost(run)
		self.assertEqual(sc.calc_status, "Cảnh báo")
		self.assertIn("Sản lượng thấp: GLU-A", sc.calc_message)
		self.assertEqual(
			{r.test_system: r.low_volume_warning for r in sc.test_system_costs}, {"GLU-A": 1, "GLU-B": 0}
		)

	def test_TC_CLS_38_tai_lap_tu_anh_chup(self):
		from normcore.costing import snapshot
		from normcore.nc_costing.doctype.nc_costing_run import loader

		run = self._run()
		before = self._cost(run)
		snap = loader.capture_snapshot(run, run.scope()["eligible"])
		blob = snapshot.dumps(snap)
		self.assertEqual(
			snapshot.digest(blob), snapshot.digest(snapshot.dumps(__import__("json").loads(blob)))
		)
		# sửa kế hoạch chất lượng và hồ sơ tuân thủ sau khi chụp
		frappe.db.set_value("NC QC IQC Line", {"parent": "KHCL-GLU-A"}, "levels", 3)
		frappe.db.set_value("NC Equipment Compliance", {"equipment": "EQ_A"}, "cost_per_time", 16000000)
		results = snapshot.reproduce(__import__("json").loads(blob))
		glu = next(r for r in results if r.service == "GLU")
		self.assertEqual(
			float(glu.direct_total),
			round(
				sum(
					before.get(f)
					for f in (
						"direct_labor",
						"direct_drug",
						"direct_supply",
						"direct_equipment",
						"direct_infra",
						"direct_utility",
					)
				),
				2,
			),
		)
		self.assertEqual(float(glu.eqa_cost), before.eqa_cost)
		self.assertEqual(
			{t.test_system: (float(t.k_factor), float(t.direct_cost)) for t in glu.test_system_costs},
			{r.test_system: (r.k_factor, r.direct_cost) for r in before.test_system_costs},
		)
		stored = {(l.test_system or "", l.norm_line_id): l.amount for l in before.lines}
		again = {(l.test_system, l.norm_line_id): float(l.amount) for l in glu.lines}
		self.assertEqual(again, stored)
		# tính lại trực tiếp từ CSDL (đã sửa) thì khác
		run.run_costing()
		after = self._cost(run.reload())
		self.assertNotEqual(
			after.direct_equipment + after.direct_drug, before.direct_equipment + before.direct_drug
		)

	def test_TC_CLS_51_san_luong_tren_site(self):
		run = self._run()
		self.assertEqual(
			frappe.db.get_value("NC Service Volume", {"technical_service": "GLU"}, "volume"), 15800
		)
		self.assertEqual(self._cost(run).volume, 16000)

	def test_che_do_gan_truc_tiep_va_kich_ban(self):
		run = self._run(compliance_allocation_mode="Gắn trực tiếp thiết bị")
		sc = self._cost(run)
		by = {l.test_system: l.amount for l in sc.lines if l.norm_line_id == "L07"}
		self.assertEqual(by, {"GLU-A": 1706.67, "GLU-B": 60.0})
		self.assertEqual(sc.calc_status, "Thành công")
		# kịch bản khác không có sản lượng → GLU Lỗi
		run2 = self._run(volume_scenario="Kế hoạch")
		self.assertEqual(self._cost(run2).calc_status, "Lỗi")
