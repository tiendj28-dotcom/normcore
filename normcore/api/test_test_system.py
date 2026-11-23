"""FEAT-031: API khối tình trạng và danh sách hệ thống của dịch vụ (FR-CLS-007; TC-CLS-20)."""

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.api import access
from normcore.api import test_system as api
from normcore.tests.utils import ensure, make_cls_data, make_test_system, make_user


class TestTestSystemApi(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.service, self.dept, _ = make_cls_data()
		make_test_system("GLU-A", self.service, self.dept, "EQ_A", 75, est_rerun_rate=2, est_wastage_rate=3)
		make_test_system("GLU-B", self.service, self.dept, "EQ_B", 25, est_rerun_rate=2, est_wastage_rate=3)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_TC_CLS_20_khoi_tinh_trang_du_bon_muc(self):
		r = api.get_status("GLU-A")
		self.assertEqual([i["key"] for i in r["items"]], ["norm_set", "qc_plan", "volume", "latest_cost"])
		for i in r["items"]:
			self.assertEqual((i["state"], i["message"]), ("empty", "Chưa có"))
		self.assertEqual(r["warnings"], [])  # 75 + 25 = 100

	def test_TC_CLS_20_canh_bao_tong_ty_trong_va_ngung_dung(self):
		frappe.db.set_value("NC Test System", "GLU-B", "status", "Ngừng dùng")
		a = api.get_status("GLU-A")
		self.assertEqual([w["code"] for w in a["warnings"]], ["share_total"])
		self.assertEqual(a["warnings"][0]["total"], 75)
		self.assertIn("75", a["warnings"][0]["message"])
		b = api.get_status("GLU-B")
		self.assertIn("inactive", [w["code"] for w in b["warnings"]])

	def test_get_service_systems(self):
		r = api.get_service_systems(self.service)
		self.assertTrue(r["is_paraclinical"])
		self.assertTrue(r["can_create"])
		dept = r["departments"][0]
		self.assertEqual((dept["department"], dept["total_share"], dept["warning"]), (self.dept, 100, False))
		self.assertEqual([s["name"] for s in dept["systems"]], ["GLU-A", "GLU-B"])
		frappe.db.set_value("NC Test System", "GLU-B", "status", "Ngừng dùng")
		dept = api.get_service_systems(self.service)["departments"][0]
		self.assertEqual((dept["total_share"], dept["warning"]), (75, True))

	def test_TC_CLS_22_clinician_khoa_khac_bi_tu_choi(self):
		ensure(
			"NC Department",
			"department_code",
			"VS-API",
			department_name="Vi sinh",
			department_type="Lâm sàng",
			cost_center="HS-CLS",
		)
		other = make_user("clin.api.vs@normcore.test", "NC Clinician")
		access.assign_department(other, "VS-API")
		frappe.set_user(other)
		with self.assertRaises(frappe.PermissionError):
			api.get_status("GLU-A")
		r = api.get_service_systems(self.service)
		self.assertEqual(r["departments"], [])

	def test_clinician_khoa_minh_thay_tong_that(self):
		own = make_user("clin.api.hs@normcore.test", "NC Clinician")
		access.assign_department(own, self.dept)
		frappe.set_user(own)
		self.assertEqual(api.get_status("GLU-A")["warnings"], [])
		self.assertEqual(len(api.get_service_systems(self.service)["departments"][0]["systems"]), 2)

	def test_auditor_doc_duoc(self):
		auditor = make_user("auditor.api@normcore.test", "NC Auditor")
		frappe.set_user(auditor)
		self.assertEqual(api.get_status("GLU-A")["test_system"], "GLU-A")
		r = api.get_service_systems(self.service)
		self.assertEqual(len(r["departments"][0]["systems"]), 2)
		self.assertFalse(r["can_create"])

	def test_vai_tro_khong_quyen_bi_tu_choi(self):
		ctrl = make_user("doc.ctrl.api@normcore.test", "NC Document Controller")
		frappe.set_user(ctrl)
		with self.assertRaises(frappe.PermissionError):
			api.get_status("GLU-A")
		r = api.get_service_systems(self.service)  # đọc được dịch vụ, không đọc được hệ thống
		self.assertEqual(r["departments"], [])
