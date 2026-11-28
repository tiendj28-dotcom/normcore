"""FEAT-037: API đối soát vật chất, sản lượng (get_physical_reconciliation) và điều kiện khóa."""

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.api import costing as api
from normcore.tests import cls_fixtures as fx
from normcore.tests.utils import make_user

FIN = "fin.apiphys37@normcore.test"
AUD = "aud.apiphys37@normcore.test"
CLIN = "clin.apiphys37@normcore.test"
HEAD = "head.apiphys37@normcore.test"
DT = "NC Reconciliation Line"


class TestCostingPhysicalApi(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.addCleanup(frappe.db.rollback)
		for u, r in (
			(FIN, "NC Finance"),
			(AUD, "NC Auditor"),
			(CLIN, "NC Clinician"),
			(HEAD, "NC Department Head"),
		):
			make_user(u, r)
		self.world = fx.make_cls_golden()
		frappe.db.set_value("NC Stock Issue Actual", {"item": "HC_GLU"}, "issued_qty", 100)
		frappe.db.set_value("NC Service Volume", {"technical_service": "GLU"}, "volume", 15500)
		self.run = fx.make_run(self.world)
		frappe.set_user(FIN)
		api.start_costing(self.run.name)

	def tearDown(self):
		frappe.set_user("Administrator")

	def _physical(self):
		return api.get_physical_reconciliation(self.run.name)

	def _explain_financial(self):
		for x in api.get_reconciliation(self.run.name)["lines"]:
			if x["needs_explanation"]:
				api.save_explanation(x["name"], "Dữ liệu thử")

	def test_dang_tra_ve_va_can_lock(self):
		r = self._physical()
		self.assertEqual(
			(r["status"], r["available"], r["material_tolerance"], r["volume_tolerance"]),
			("Đã tính", 1, 5, 2),
		)
		glu = next(x for x in r["material"] if x["item"] == "HC_GLU")
		self.assertEqual(
			(
				glu["department"],
				glu["actual_qty"],
				glu["variance_pct"],
				glu["over_tolerance"],
				glu["needs_explanation"],
			),
			(fx.DEPT, 20000, 9.07, 1, True),
		)
		self.assertEqual(round(glu["diff_qty"], 2), round(20000 - glu["calculated_qty"], 2))
		vol = r["volume"][0]
		self.assertEqual(
			(
				vol["technical_service"],
				vol["calculated_qty"],
				vol["actual_qty"],
				vol["variance_pct"],
				vol["over_tolerance"],
				vol["needs_explanation"],
			),
			("GLU", 16000, 15500, 3.23, 1, False),
		)
		self.assertEqual(
			(r["blocked"], r["can_explain"], r["can_lock"]),
			(
				len([x for x in r["material"] if x["needs_explanation"]])
				+ sum(1 for x in api.get_reconciliation(self.run.name)["lines"] if x["needs_explanation"]),
				True,
				False,
			),
		)

	def test_get_reconciliation_chi_dong_tai_chinh_va_dai_vat_chat(self):
		r = api.get_reconciliation(self.run.name)
		self.assertTrue(all(x["cost_category"] for x in r["lines"]))
		self.assertEqual(
			r["physical"], {"available": 1, "material_blocked": 1, "unreconciled": 0, "volume_warnings": 1}
		)
		self.assertEqual(api.get_run_results(self.run.name)["physical_unreconciled"], 0)

	def test_giai_trinh_va_khoa(self):
		self._explain_financial()
		glu = next(x for x in self._physical()["material"] if x["item"] == "HC_GLU")
		out = api.save_explanation(glu["name"], "Nhập thêm cuối kỳ")
		self.assertEqual((out["needs_explanation"], out["blocked"]), (False, 0))
		r = self._physical()
		self.assertEqual((r["blocked"], r["can_lock"]), (0, True))
		self.assertEqual(api.lock_run(self.run.name), {"status": "Đã khóa"})

	def test_chua_doi_soat_dem_khoa(self):
		frappe.set_user("Administrator")
		frappe.db.delete("NC Stock Issue Actual")
		run = fx.make_run(self.world)
		frappe.set_user(FIN)
		api.start_costing(run.name)
		self.assertEqual(api.get_run_results(run.name)["physical_unreconciled"], 1)
		r = api.get_physical_reconciliation(run.name)
		self.assertEqual(
			[(x["item"], x["recon_status"], x["variance_pct"]) for x in r["material"]],
			[(None, "Chưa đối soát", None)],
		)

	def test_chua_doi_soat_het_khi_da_giai_trinh_hoac_khoa(self):
		# NORM-90: dòng vật chất đã giải trình thì không còn tính là chưa đối soát.
		frappe.set_user("Administrator")
		frappe.db.delete("NC Stock Issue Actual")
		run = fx.make_run(self.world)
		frappe.set_user(FIN)
		api.start_costing(run.name)
		self.assertEqual(api.get_run_results(run.name)["physical_unreconciled"], 1)
		line = api.get_physical_reconciliation(run.name)["material"][0]["name"]
		api.save_explanation(line, "Khoa chưa xuất kho kỳ này")
		self.assertEqual(api.get_run_results(run.name)["physical_unreconciled"], 0)

	def test_quyen(self):
		line = self._physical()["material"][0]["name"]
		for user in (CLIN, HEAD):
			frappe.set_user(user)
			with self.assertRaises(frappe.PermissionError):
				api.get_physical_reconciliation(self.run.name)
		frappe.set_user(AUD)
		self.assertEqual(self._physical()["status"], "Đã tính")
		with self.assertRaises(frappe.PermissionError):
			api.save_explanation(line, "x")
