"""FEAT-032: NC EQA Program (FR-QC-003, 005; DI-12; FR-ACC-008; TC-CLS-24, TC-CLS-25)."""

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.api import access
from normcore.costing import qc_plans
from normcore.install import ROLES
from normcore.tests.utils import (
	ensure,
	ensure_service,
	make_base,
	make_cls_data,
	make_eqa_program,
	make_user,
)

REQUIRED = (
	"eqa_code",
	"program_name",
	"provider",
	"department",
	"rounds_per_year",
	"samples_per_round",
	"annual_fee",
)


class TestNCEQAProgram(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.service, self.dept, _ = make_cls_data()
		frappe.db.set_value("NC Technical Service", ensure_service("URE"), "is_paraclinical", 1)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _values(self, **kw):
		values = {
			"doctype": "NC EQA Program",
			"eqa_code": "EQA-HS",
			"program_name": "Ngoại kiểm hóa sinh",
			"provider": "Trung tâm kiểm chuẩn",
			"department": self.dept,
			"rounds_per_year": 3,
			"samples_per_round": 4,
			"annual_fee": 24000000,
			"annual_shipping_fee": 1200000,
			"services": [dict(technical_service="GLU")],
		}
		values.update(kw)
		return values

	def test_TC_CLS_24_chuong_trinh_du_truong_luu_duoc(self):
		doc = make_eqa_program(department=self.dept)
		self.assertEqual(doc.name, "EQA-HS")

	def test_TC_CLS_24_thieu_truong_bi_tu_choi(self):
		for f in (*REQUIRED, "services"):
			values = self._values()
			values.pop(f)
			with self.assertRaises(frappe.ValidationError, msg=f):
				frappe.get_doc(values).insert()
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(self._values(services=[])).insert()
		self.assertFalse(frappe.db.exists("NC EQA Program", "EQA-HS"))

	def test_phi_van_chuyen_trong_luu_duoc(self):
		values = self._values()
		values.pop("annual_shipping_fee")
		doc = frappe.get_doc(values).insert()
		self.assertEqual(doc.annual_shipping_fee or 0, 0)

	def test_TC_CLS_25_50_va_40_bi_tu_choi(self):
		rows = [dict(technical_service="GLU", share_pct=50), dict(technical_service="URE", share_pct=40)]
		with self.assertRaises(frappe.ValidationError) as ctx:
			frappe.get_doc(self._values(services=rows)).insert()
		self.assertIn("90", str(ctx.exception))
		self.assertIn("100", str(ctx.exception))

	def test_TC_CLS_25_60_va_40_luu_duoc(self):
		rows = [dict(technical_service="GLU", share_pct=60), dict(technical_service="URE", share_pct=40)]
		self.assertEqual(frappe.get_doc(self._values(services=rows)).insert().name, "EQA-HS")

	def test_TC_CLS_25_de_trong_chia_deu(self):
		rows = [dict(technical_service="GLU"), dict(technical_service="URE")]
		doc = frappe.get_doc(self._values(services=rows)).insert()
		shares = qc_plans.eqa_shares([r.as_dict() for r in doc.services])
		self.assertEqual([str(s) for s in shares], ["0.5", "0.5"])

	def test_DI_12_mot_so_dong_trong_bi_tu_choi(self):
		rows = [dict(technical_service="GLU", share_pct=50), dict(technical_service="URE")]
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(self._values(services=rows)).insert()

	def test_dich_vu_lap_va_khong_can_lam_sang(self):
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(self._values(services=[dict(technical_service="GLU")] * 2)).insert()
		ensure("NC Technical Service", "service_code", "KHONG-CLS", service_name="Không cận lâm sàng")
		with self.assertRaises(frappe.ValidationError) as ctx:
			frappe.get_doc(self._values(services=[dict(technical_service="KHONG-CLS")])).insert()
		self.assertIn("cận lâm sàng", str(ctx.exception))

	def _other_dept_user(self):
		make_base(department="VS-CLS")
		ensure(
			"NC Department",
			"department_code",
			"VS-CLS",
			department_name="Vi sinh",
			department_type="Lâm sàng",
			cost_center="VS-CLS",
		)
		user = make_user("eqa.vs@normcore.test", "NC Clinician")
		access.assign_department(user, "VS-CLS")
		own = make_user("eqa.hs@normcore.test", "NC Clinician")
		access.assign_department(own, self.dept)
		return user, own

	def test_FR_ACC_008_phan_quyen_khoa(self):
		make_eqa_program(department=self.dept)
		other, own = self._other_dept_user()
		frappe.set_user(other)
		doc = frappe.get_doc("NC EQA Program", "EQA-HS")
		self.assertFalse(frappe.has_permission("NC EQA Program", "read", doc=doc))
		self.assertNotIn("EQA-HS", frappe.get_list("NC EQA Program", pluck="name"))
		with self.assertRaises(frappe.PermissionError):
			frappe.get_doc(self._values(eqa_code="EQA-X")).insert()
		frappe.set_user(own)
		doc = frappe.get_doc("NC EQA Program", "EQA-HS")
		doc.rounds_per_year = 2
		doc.save()
		self.assertEqual(frappe.db.get_value("NC EQA Program", "EQA-HS", "rounds_per_year"), 2)

	def test_quyen_theo_ma_tran(self):
		make_eqa_program(department=self.dept)
		readers = {
			"NC Finance",
			"NC Resource Manager",
			"NC Director",
			"NC Consultant",
			"NC Admin",
			"NC Auditor",
		}
		users = {role: make_user(f"eqa.perm{i}@normcore.test", role) for i, role in enumerate(ROLES)}
		for role, user in users.items():
			if role in ("NC Clinician", "NC Department Head"):
				continue
			frappe.set_user(user)
			self.assertEqual(bool(frappe.has_permission("NC EQA Program", "read")), role in readers, role)
			for ptype in ("write", "create", "delete"):
				self.assertFalse(frappe.has_permission("NC EQA Program", ptype), f"{role} {ptype}")

	def test_auditor_doc_duoc_khong_ghi_duoc(self):
		make_eqa_program(department=self.dept)
		frappe.set_user(make_user("eqa.auditor@normcore.test", "NC Auditor"))
		doc = frappe.get_doc("NC EQA Program", "EQA-HS")
		self.assertTrue(frappe.has_permission("NC EQA Program", "read", doc=doc))
		doc.rounds_per_year = 9
		with self.assertRaises(frappe.PermissionError):
			doc.save()
		with self.assertRaises(frappe.PermissionError):
			frappe.get_doc(self._values(eqa_code="EQA-Y")).insert()

	def test_vai_tro_khong_co_quyen_bi_tu_choi(self):
		make_eqa_program(department=self.dept)
		users = {
			r: make_user(f"eqa.none{i}@normcore.test", r)
			for i, r in enumerate(("NC Document Controller", "NC Council Member"))
		}
		for role, user in users.items():
			frappe.set_user(user)
			self.assertFalse(frappe.has_permission("NC EQA Program", "read"), role)
			with self.assertRaises(frappe.PermissionError):
				frappe.get_doc("NC EQA Program", "EQA-HS").check_permission("read")
