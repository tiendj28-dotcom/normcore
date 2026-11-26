"""FEAT-015: API lần tính giá. NC Clinician không có quyền, NC Auditor chỉ đọc."""

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.api import costing as api
from normcore.tests import costing_fixtures as cf
from normcore.tests.utils import make_user

FIN = "fin.costing@normcore.test"
AUD = "aud.costing@normcore.test"
CLIN = "clin.costing@normcore.test"


class TestCostingApi(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		make_user(FIN, "NC Finance")
		make_user(AUD, "NC Auditor")
		make_user(CLIN, "NC Clinician")
		self.params, self.dept, self.sets = cf.make_golden_world()
		self.run = cf.make_golden_run(self.params)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _cost(self, service="DV-TEST-A"):
		return frappe.get_value(
			"NC Service Cost", {"costing_run": self.run.name, "technical_service": service}, "name"
		)

	def test_TC_COST_17_check_scope_liet_ke(self):
		cf.ensure("NC Technical Service", "service_code", "DV-CHUA", service_name="Chưa khóa")
		svc = frappe.get_doc("NC Technical Service", "DV-CHUA")
		svc.is_active = 1
		svc.append("departments", {"department": self.dept})
		svc.save(ignore_permissions=True)
		self.run.append("scope_services", {"technical_service": "DV-CHUA"})
		self.run.append("scope_services", {"technical_service": "DV-TEST-A"})
		self.run.save(ignore_permissions=True)
		frappe.set_user(FIN)
		r = api.check_scope(self.run.name)
		self.assertEqual([x["service"] for x in r["ineligible"]], ["DV-CHUA"])
		self.assertEqual(r["ineligible"][0]["service_name"], "Chưa khóa")
		self.assertEqual([x["service"] for x in r["eligible"]], ["DV-TEST-A"])
		self.assertFalse(r["background"])
		with self.assertRaisesRegex(frappe.ValidationError, "DV-CHUA"):
			api.start_costing(self.run.name)
		out = api.start_costing(self.run.name, 1)
		self.assertEqual(out, {"status": "Đã tính", "enqueued": False, "skipped": 1})
		self.assertEqual(api.get_progress(self.run.name), {"status": "Đã tính", "progress": 100})

	def test_get_run_results(self):
		frappe.set_user(FIN)
		api.start_costing(self.run.name)
		r = api.get_run_results(self.run.name)
		self.assertEqual([x["service"] for x in r["results"]], ["DV-TEST-A", "DV-TEST-B"])
		self.assertEqual(r["counts"], {"Thành công": 2})
		self.assertFalse(r["results"][0]["has_allocation"])
		self.assertEqual(r["results"][0]["full_cost"], 183963.06)

	def test_TC_COST_15_get_explanation_du_truong(self):
		frappe.set_user(FIN)
		api.start_costing(self.run.name)
		e = api.get_explanation(self._cost())
		h = e["header"]
		self.assertEqual(
			(h["service"], h["full_cost"], h["rounded_price"]), ("DV-TEST-A", 183963.06, 193200.0)
		)
		self.assertTrue(h["include_depreciation"])
		self.assertFalse(h["has_allocation"])
		self.assertEqual(h["direct_total"], 183963.06)
		self.assertEqual([g["component"] for g in e["direct_groups"]][:2], ["LABOR", "DRUG"])
		shared = [s for g in e["direct_groups"] for s in g["steps"] if not s["step_id"]]
		self.assertEqual([s["step_label"] for s in shared], ["Chung"])
		n = 0
		for g in e["direct_groups"]:
			for s in g["steps"]:
				for ln in s["lines"]:
					n += 1
					for f in ("step_label", "resource_label", "applied_qty", "unit_rate", "rate_source"):
						self.assertTrue(ln[f] not in (None, ""), (ln["norm_line_id"], f))
		self.assertEqual(n, 11)
		self.assertEqual(round(sum(x["share_pct"] for x in e["structure"]), 1), 100.0)
		self.assertEqual(e["notes"], ["Chưa gồm chi phí phân bổ chung (phân bổ cấp 1, cấp 2 làm ở FEAT-017)"])

	def test_TC_COST_06_ghi_chu_khau_hao_bi_loai(self):
		cf.make_price_category("PC-V1", include_depreciation=0)
		run = cf.make_golden_run(self.params, price_category="PC-V1")
		frappe.set_user(FIN)
		api.start_costing(run.name)
		name = frappe.get_value(
			"NC Service Cost", {"costing_run": run.name, "technical_service": "DV-TEST-A"}
		)
		e = api.get_explanation(name)
		self.assertFalse(e["header"]["include_depreciation"])
		self.assertIn("Khấu hao bị loại (loại giá không kết cấu khấu hao)", e["notes"])

	def test_quyen_costing_clinician_bi_tu_choi(self):
		frappe.set_user(CLIN)
		for fn, args in (
			(api.check_scope, (self.run.name,)),
			(api.start_costing, (self.run.name,)),
			(api.get_progress, (self.run.name,)),
			(api.get_run_results, (self.run.name,)),
		):
			with self.subTest(fn=fn.__name__), self.assertRaises(frappe.PermissionError):
				fn(*args)

	def test_quyen_clinician_khong_goi_get_explanation_va_doc_service_cost(self):
		"""FR-ACC-003, data-model.md:815: Clinician không có quyền với NC Service Cost."""
		frappe.set_user(FIN)
		api.start_costing(self.run.name)
		name = self._cost()
		self.assertTrue(name)
		frappe.set_user(CLIN)
		with self.assertRaises(frappe.PermissionError):
			api.get_explanation(name)
		with self.assertRaises(frappe.PermissionError):
			frappe.get_doc("NC Service Cost", name).check_permission("read")
		with self.assertRaises(frappe.PermissionError):
			frappe.get_list("NC Service Cost", {"costing_run": self.run.name})

	def test_quyen_costing_auditor_chi_doc(self):
		frappe.set_user(FIN)
		api.start_costing(self.run.name)
		frappe.set_user(AUD)
		self.assertEqual(api.get_progress(self.run.name)["status"], "Đã tính")
		self.assertEqual(len(api.get_run_results(self.run.name)["results"]), 2)
		self.assertEqual(api.get_explanation(self._cost())["header"]["service"], "DV-TEST-A")
		with self.assertRaises(frappe.PermissionError):
			api.start_costing(self.run.name)
		with self.assertRaises(frappe.PermissionError):
			api.check_scope(self.run.name)


class TestServiceCostPermission(FrappeTestCase):
	"""Quyết định Lead Q2 (ASM-015-22): NC Service Cost theo dòng "Bảng giải trình của dịch vụ thuộc khoa"."""

	def setUp(self):
		from normcore.api import access

		frappe.set_user("Administrator")
		self.head = make_user("head.costing@normcore.test", "NC Department Head")
		self.params, self.dept, self.sets = cf.make_golden_world()
		cf.ensure(
			"NC Department",
			"department_code",
			"KHOA-KHAC",
			department_name="Khoa khác",
			department_type="Lâm sàng",
			cost_center=self.dept,
		)
		access.assign_department(self.head, self.dept)
		self.run = cf.make_golden_run(self.params)
		self.run.run_costing()
		self.name = frappe.get_value("NC Service Cost", {"costing_run": self.run.name}, "name")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_quyen_bang_giai_trinh_truong_khoa_theo_khoa(self):
		frappe.set_user(self.head)
		self.assertTrue(frappe.has_permission("NC Service Cost", "read", self.name))
		self.assertEqual(len(frappe.get_list("NC Service Cost", {"costing_run": self.run.name})), 2)
		self.assertEqual(api.get_explanation(self.name)["header"]["department"], self.dept)
		for ptype in ("write", "create", "delete"):
			self.assertFalse(frappe.has_permission("NC Service Cost", ptype), ptype)
		# lần tính (kết quả tổng hợp) vẫn không dành cho trưởng khoa
		self.assertFalse(frappe.has_permission("NC Costing Run", "read", self.run.name))
		# khoa khác: không đọc được
		frappe.set_user("Administrator")
		frappe.db.set_value("NC Service Cost", self.name, "department", "KHOA-KHAC")
		frappe.set_user(self.head)
		self.assertFalse(frappe.has_permission("NC Service Cost", "read", self.name))
		with self.assertRaises(frappe.PermissionError):
			api.get_explanation(self.name)


class TestCostingClsApi(FrappeTestCase):
	"""FEAT-036: get_run_results, get_explanation cho dịch vụ cận lâm sàng; quyền NC Test System Cost theo cha."""

	def setUp(self):
		from normcore.tests import cls_fixtures as fx

		frappe.set_user("Administrator")
		make_user(FIN, "NC Finance")
		make_user(AUD, "NC Auditor")
		make_user(CLIN, "NC Clinician")
		self.world = fx.make_cls_golden()
		self.run = fx.make_run(self.world)
		frappe.set_user(FIN)
		api.start_costing(self.run.name, 1)
		self.cost = frappe.get_value("NC Service Cost", {"costing_run": self.run.name, "technical_service": "GLU"}, "name")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_get_run_results_them_truong_can_lam_sang(self):
		r = api.get_run_results(self.run.name)
		self.assertEqual(r["run"]["volume_scenario"], "Thực tế 12 tháng")
		self.assertEqual(r["run"]["compliance_allocation_mode"], "Theo giá trị tài sản")
		self.assertEqual(r["run"]["run_warnings"], [])
		glu = next(x for x in r["results"] if x["service"] == "GLU")
		self.assertTrue(glu["is_paraclinical"])
		self.assertEqual(glu["eqa_cost"], 75.0)
		self.assertEqual([t["test_system"] for t in glu["test_systems"]], ["GLU-A", "GLU-B"])
		self.assertEqual(glu["test_systems"][0]["k_factor"], 1.108247)
		other = next(x for x in r["results"] if x["service"] == "DV-TEST-A")
		self.assertFalse(other["is_paraclinical"])
		self.assertEqual(other["test_systems"], [])

	def test_TC_CLS_38_get_explanation_du_mau_so(self):
		e = api.get_explanation(self.cost)
		p = e["paraclinical"]
		self.assertEqual([s["test_system"] for s in p["systems"]], ["GLU-A", "GLU-B"])
		a, b = p["systems"]
		self.assertEqual((a["patient_results"], a["q_iqc"], a["q_calibration"], a["q_rerun"], a["q_eqa"]), (12000, 600, 48, 240, 12))
		self.assertEqual((a["total_tests"], a["wastage_rate"], a["k_factor"], a["k_estimated"]), (12900, 3, 1.108247, False))
		self.assertEqual((b["k_factor"], b["k_estimated"], b["share_source"]), (1.221649, True, "Từ số kết quả trả"))
		self.assertEqual((p["weighted_direct"], p["eqa_cost"], p["direct_total"]), (42203.67, 75.0, 42278.67))
		self.assertEqual(e["header"]["direct_total"], 42278.67)
		n = 0
		for s in p["systems"]:
			for g in s["groups"]:
				for st in g["steps"]:
					for ln in st["lines"]:
						n += 1
						for f in ("test_system", "cost_level", "divisor_label", "divisor_value", "divisor_source", "line_origin"):
							self.assertTrue(ln[f] not in (None, ""), (ln["norm_line_id"], f))
						self.assertEqual(ln["k_factor"] is not None, ln["norm_line_id"] in ("L02", "L03"))
		self.assertEqual(n, 20)  # GLU-A 11 dòng, GLU-B 9 (không linh kiện, không điện)
		(eqa,) = p["service_lines"]
		self.assertEqual((eqa["norm_line_id"], eqa["amount"], eqa["divisor_value"]), ("EQA", 75.0, 16000))
		self.assertEqual(eqa["divisor_source"], "Thực tế")

	def test_quyen_test_system_cost_clinician_va_auditor(self):
		frappe.set_user(AUD)
		doc = frappe.get_doc("NC Service Cost", self.cost)
		self.assertEqual(len(doc.test_system_costs), 2)
		self.assertEqual(api.get_explanation(self.cost)["paraclinical"]["systems"][0]["test_system"], "GLU-A")
		with self.assertRaises(frappe.PermissionError):
			frappe.get_doc({"doctype": "NC Service Cost", "costing_run": self.run.name, "technical_service": "GLU", "department": "XN"}).insert()
		frappe.set_user(CLIN)
		with self.assertRaises(frappe.PermissionError):
			api.get_explanation(self.cost)
		with self.assertRaises(frappe.PermissionError):
			frappe.get_doc("NC Service Cost", self.cost).check_permission("read")
		with self.assertRaises(frappe.PermissionError):
			api.start_costing(self.run.name)
