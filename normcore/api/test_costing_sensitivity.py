"""FEAT-037: API phân tích độ nhạy (FR-COST-030). Không ghi dữ liệu."""

import frappe
from frappe.permissions import add_user_permission
from frappe.tests.utils import FrappeTestCase

from normcore.api import costing as api
from normcore.tests import cls_fixtures as fx
from normcore.tests.utils import make_user

FIN = "fin.sens37@normcore.test"
AUD = "aud.sens37@normcore.test"
CLIN = "clin.sens37@normcore.test"
HEAD_IN = "head.in.sens37@normcore.test"
HEAD_OUT = "head.out.sens37@normcore.test"


def _count(dt, **f):
	return frappe.db.count(dt, f)


class TestCostingSensitivityApi(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.addCleanup(frappe.db.rollback)
		self.world = fx.make_cls_golden()
		for u, r in ((FIN, "NC Finance"), (AUD, "NC Auditor"), (CLIN, "NC Clinician"), (HEAD_IN, "NC Department Head"), (HEAD_OUT, "NC Department Head")):
			make_user(u, r)
		add_user_permission("NC Department", fx.DEPT, HEAD_IN)
		add_user_permission("NC Department", self.world.other_dept, HEAD_OUT)
		self.run = fx.make_run(self.world)
		frappe.set_user(FIN)
		api.start_costing(self.run.name)
		self.sc = frappe.db.get_value("NC Service Cost", {"costing_run": self.run.name, "technical_service": "GLU"})

	def tearDown(self):
		frappe.set_user("Administrator")

	def _state(self):
		run = frappe.db.get_value("NC Costing Run", self.run.name, ["modified", "status", "snapshot_hash"])
		costs = frappe.get_all("NC Service Cost", {"costing_run": self.run.name}, ["name", "modified", "full_cost", "rounded_price"], order_by="name")
		lines = frappe.get_all("NC Service Cost Line", {"parenttype": "NC Service Cost"}, ["name", "amount", "modified"], order_by="name")
		recon = frappe.get_all("NC Reconciliation Line", {"costing_run": self.run.name}, ["name", "modified", "variance_pct", "explanation"], order_by="name")
		return run, costs, lines, recon, _count("NC Service Cost"), _count("NC Reconciliation Line")

	def test_TC_CLS_40_do_nhay_khong_ghi(self):
		base = api.get_sensitivity_base(self.sc)
		self.assertEqual((base["service"], base["is_paraclinical"], base["run_status"]), ("GLU", True, "Đã tính"))
		self.assertEqual({x["test_system"]: x["qbn"] for x in base["inputs"]["systems"]}, {"GLU-A": 12000, "GLU-B": 4000})
		self.assertIn("HC_GLU", [x["item"] for x in base["inputs"]["items"]])
		before = self._state()
		r = api.run_sensitivity(self.sc, {"system_volumes": {"GLU-A": 6000}})
		self.assertNotEqual(r["trial"]["full_cost"], r["origin"]["full_cost"])
		self.assertEqual(r["origin"]["full_cost"], base["origin"]["full_cost"])
		self.assertEqual(r["note"], "Kết quả thử, không lưu")
		self.assertEqual(r["diff"]["full_cost"], round(r["trial"]["full_cost"] - r["origin"]["full_cost"], 2))
		self.assertEqual({x["test_system"] for x in r["systems"]}, {"GLU-A", "GLU-B"})
		self.assertEqual(self._state(), before)
		again = api.run_sensitivity(self.sc, {"system_volumes": {"GLU-A": 6000}})
		self.assertEqual(again["trial"], r["trial"])

	def test_khoa_ket_qua_dung_anh_chup(self):
		api.run_sensitivity(self.sc, {"prices": {"HC_GLU": 7000000}})
		frappe.set_user("Administrator")
		run = frappe.get_doc("NC Costing Run", self.run.name)
		for n in frappe.get_all("NC Reconciliation Line", {"costing_run": run.name, "over_tolerance": 1}, pluck="name"):
			frappe.db.set_value("NC Reconciliation Line", n, "explanation", "Dữ liệu thử")
		run.lock_costing()
		frappe.set_user(FIN)
		self.assertEqual(api.get_sensitivity_base(self.sc)["run_status"], "Đã khóa")
		r = api.run_sensitivity(self.sc, {"prices": {"HC_GLU": 7000000}})
		self.assertGreater(r["trial"]["full_cost"], r["origin"]["full_cost"])
		self.assertEqual(r["warnings"], [])

	def test_gia_dinh_khong_hop_le(self):
		for ov, msg in (
			({"system_volumes": {"GLU-A": 0}}, "Sản lượng giả định phải lớn hơn 0"),
			({}, "Nhập ít nhất một giả định"),
			({"prices": {"HC_GLU": -5}}, "Đơn giá giả định không được âm"),
		):
			with self.assertRaises(frappe.ValidationError) as ctx:
				api.run_sensitivity(self.sc, ov)
			self.assertIn(msg, str(ctx.exception))

	def test_chua_co_ket_qua(self):
		frappe.set_user("Administrator")
		frappe.db.set_value("NC Costing Run", self.run.name, "status", "Nháp")
		frappe.set_user(FIN)
		with self.assertRaises(frappe.ValidationError):
			api.get_sensitivity_base(self.sc)

	def test_quyen_truong_khoa_ngoai_khoa(self):
		frappe.set_user(HEAD_OUT)
		with self.assertRaises(frappe.PermissionError):
			api.run_sensitivity(self.sc, {"system_volumes": {"GLU-A": 6000}})
		with self.assertRaises(frappe.PermissionError):
			api.get_sensitivity_base(self.sc)
		frappe.set_user(HEAD_IN)
		self.assertTrue(api.run_sensitivity(self.sc, {"system_volumes": {"GLU-A": 6000}})["trial"]["full_cost"])

	def test_quyen_auditor_doc_duoc_clinician_khong(self):
		frappe.set_user(AUD)
		self.assertTrue(api.get_sensitivity_base(self.sc)["origin"]["full_cost"])
		self.assertTrue(api.run_sensitivity(self.sc, {"system_volumes": {"GLU-A": 6000}})["trial"])
		frappe.set_user(CLIN)
		with self.assertRaises(frappe.PermissionError):
			api.run_sensitivity(self.sc, {"system_volumes": {"GLU-A": 6000}})
