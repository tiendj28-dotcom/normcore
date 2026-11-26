"""FEAT-037 trên site: đối soát vật chất, sản lượng trong lần tính giá (TC-CLS-17, 18, 19)."""

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.tests import cls_fixtures as fx
from normcore.tests.utils import make_user

DT = "NC Reconciliation Line"
FIN = "fin.phys37@normcore.test"
AUD = "aud.phys37@normcore.test"
CLIN = "clin.phys37@normcore.test"


class TestNCCostingPhysical(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.addCleanup(frappe.db.rollback)
		self.world = fx.make_cls_golden()
		make_user(FIN, "NC Finance")
		make_user(AUD, "NC Auditor")
		make_user(CLIN, "NC Clinician")

	def tearDown(self):
		frappe.set_user("Administrator")

	def _run(self, **kw):
		run = fx.make_run(self.world, **kw)
		run.run_costing(confirm_ineligible=1)
		return run.reload()

	def _set_boxes(self, item, boxes):
		frappe.db.set_value(
			"NC Stock Issue Actual", {"item": item, "department": fx.DEPT}, "issued_qty", boxes
		)

	def _lines(self, run, kind):
		return frappe.get_all(
			DT,
			{"costing_run": run.name, "recon_type": kind},
			[
				"name",
				"department",
				"item",
				"technical_service",
				"calculated_qty",
				"actual_qty",
				"variance_pct",
				"over_tolerance",
				"recon_status",
				"explanation",
				"cost_category",
			],
			order_by="item, technical_service",
		)

	def _explain_financial(self, run):
		"""Giải trình hết dòng tài chính vượt ngưỡng của bộ dữ liệu thử, để chỉ còn lại dòng đang kiểm."""
		for name in frappe.get_all(
			DT, {"costing_run": run.name, "recon_type": "Tài chính", "over_tolerance": 1}, pluck="name"
		):
			frappe.db.set_value(DT, name, "explanation", "Chênh lệch bộ dữ liệu thử")

	def _prepare(self, hc_boxes):
		"""Mọi mặt hàng xuất đúng lượng tính được (bộ dữ liệu), riêng HC_GLU xuất `hc_boxes` hộp."""
		self._set_boxes("HC_GLU", hc_boxes)
		return self._run()

	def test_TC_CLS_17_vuot_nguong_chan_khoa(self):
		run = self._prepare(100)
		self._explain_financial(run)
		glu = next(x for x in self._lines(run, "Vật chất") if x.item == "HC_GLU")
		self.assertEqual((glu.actual_qty, glu.variance_pct, glu.over_tolerance), (20000, 9.07, 1))
		self.assertEqual(
			(glu.department, glu.cost_category, glu.recon_status), (fx.DEPT, "DRUG_SUPPLY", "Đã đối soát")
		)
		with self.assertRaises(frappe.ValidationError) as ctx:
			run.lock_costing()
		self.assertIn(f"Vật chất · {fx.DEPT} · HC_GLU", str(ctx.exception))
		frappe.db.set_value(DT, glu.name, "explanation", "Nhập thêm cuối kỳ")
		self.assertEqual(run.lock_costing(), "Đã khóa")

	def test_TC_CLS_16_khong_vuot_xuat_94_hop(self):
		run = self._prepare(94)
		glu = next(x for x in self._lines(run, "Vật chất") if x.item == "HC_GLU")
		self.assertEqual(
			(round(glu.calculated_qty, 2), glu.actual_qty, glu.variance_pct, glu.over_tolerance),
			(18185.56, 18800, 3.27, 0),
		)

	def test_TC_CLS_19_chua_doi_soat_vat_chat(self):
		frappe.db.delete("NC Stock Issue Actual")
		run = self._run()
		self._explain_financial(run)
		rows = self._lines(run, "Vật chất")
		self.assertEqual(len(rows), 1)
		self.assertEqual(
			(rows[0].item, rows[0].recon_status, rows[0].department), (None, "Chưa đối soát", fx.DEPT)
		)
		self.assertEqual(rows[0].over_tolerance, 0)
		with self.assertRaises(frappe.ValidationError) as ctx:
			run.lock_costing()
		self.assertIn("Chưa đối soát", str(ctx.exception))
		frappe.db.set_value(DT, rows[0].name, "explanation", "Kho chưa tách số liệu theo khoa (A-08)")
		self.assertEqual(run.lock_costing(), "Đã khóa")

	def test_TC_CLS_18_canh_bao_san_luong_khong_chan_khoa(self):
		run = self._prepare(100)
		self._explain_financial(run)
		for ln in self._lines(run, "Vật chất"):
			if ln.over_tolerance:
				frappe.db.set_value(DT, ln.name, "explanation", "đã rà")
		vol = self._lines(run, "Sản lượng")
		self.assertEqual(
			(len(vol), vol[0].technical_service, vol[0].calculated_qty, vol[0].actual_qty),
			(1, "GLU", 16000, 15800),
		)
		self.assertEqual((vol[0].variance_pct, vol[0].over_tolerance), (1.27, 0))
		frappe.db.set_value("NC Service Volume", {"technical_service": "GLU"}, "volume", 15500)
		run = self._run()
		self._explain_financial(run)
		for ln in self._lines(run, "Vật chất"):
			if ln.over_tolerance:
				frappe.db.set_value(DT, ln.name, "explanation", "đã rà")
		vol = self._lines(run, "Sản lượng")[0]
		self.assertEqual((vol.variance_pct, vol.over_tolerance), (3.23, 1))
		self.assertEqual(run.lock_costing(), "Đã khóa")  # cảnh báo sản lượng không chặn khóa

	def test_khong_doi_soat_vat_chat_khi_ke_hoach(self):
		for ts in frappe.get_all("NC Test System Volume", {"scenario": "Thực tế 12 tháng"}, ["name"]):
			d = frappe.get_doc("NC Test System Volume", ts.name).as_dict()
			d.update({"doctype": "NC Test System Volume", "scenario": "Kế hoạch", "name": None})
			frappe.get_doc(
				{
					k: v
					for k, v in d.items()
					if k not in ("name", "creation", "modified", "owner", "modified_by", "docstatus", "idx")
				}
			).insert(ignore_permissions=True)
		run = self._run(volume_scenario="Kế hoạch")
		self.assertEqual(
			frappe.db.count(DT, {"costing_run": run.name, "recon_type": ["in", ["Vật chất", "Sản lượng"]]}), 0
		)

	def test_quyen_clinician_auditor(self):
		frappe.db.delete("NC Stock Issue Actual")
		run = self._run()
		line = self._lines(run, "Vật chất")[0]
		frappe.set_user(CLIN)
		self.assertFalse(frappe.has_permission(DT, "read", doc=line.name))
		frappe.set_user(AUD)
		self.assertTrue(frappe.has_permission(DT, "read", doc=line.name))
		self.assertFalse(frappe.has_permission(DT, "write", doc=line.name))
		frappe.set_user(FIN)
		self.assertTrue(frappe.has_permission(DT, "write", doc=line.name))
