"""FEAT-032: NC QC Plan (FR-QC-001, 002, 008; DI-11, DI-16; FR-ACC-008; TC-CLS-24, TC-CLS-25)."""

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.api import access
from normcore.install import ROLES
from normcore.tests.utils import (
	ensure,
	make_base,
	make_cls_data,
	make_qc_items,
	make_qc_plan,
	make_test_system,
	make_user,
	qc_plan_values,
)


class TestNCQCPlan(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.service, self.dept, _ = make_cls_data()
		make_test_system("GLU-A", self.service, self.dept, "EQ_A", 75)
		make_qc_items()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _insert(self, **kw):
		return frappe.get_doc(qc_plan_values("GLU-A", **kw)).insert()

	def test_TC_CLS_24_ke_hoach_du_truong_luu_duoc(self):
		doc = make_qc_plan("GLU-A")
		self.assertEqual(doc.name, "KHCL-GLU-A")
		self.assertEqual(doc.iqc_lines[0].shared_parameter_count, 20)

	def test_TC_CLS_24_thieu_truong_bi_tu_choi_den_khi_du(self):
		for f in ("test_system", "run_days_per_year"):
			values = qc_plan_values("GLU-A")
			values.pop(f)
			with self.assertRaises(frappe.ValidationError, msg=f):
				frappe.get_doc(values).insert()
		for table, fields in (
			("iqc_lines", ("qc_material", "levels", "runs_per_day", "qty_per_run", "shared_parameter_count")),
			(
				"calibration_lines",
				("calibrator", "points", "replicates", "calibrations_per_year", "cost_per_calibration"),
			),
		):
			for f in fields:
				if f == "shared_parameter_count":
					continue  # có mặc định 1 (TBD-15); trường trống được hàm thuần kiểm ở test_qc_plans
				values = qc_plan_values("GLU-A")
				values[table][0].pop(f)
				with self.assertRaises(frappe.ValidationError, msg=f"{table}.{f}"):
					frappe.get_doc(values).insert()
				self.assertFalse(frappe.db.exists("NC QC Plan", "KHCL-GLU-A"))
		self.assertEqual(make_qc_plan("GLU-A").name, "KHCL-GLU-A")  # điền đủ thì lưu được

	def test_TC_CLS_24_so_khong_bi_tu_choi(self):
		values = qc_plan_values("GLU-A")
		values["iqc_lines"][0]["levels"] = 0
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(values).insert()
		with self.assertRaises(frappe.ValidationError):
			self._insert(run_days_per_year=0)

	def test_TC_CLS_25_vat_lieu_noi_kiem_sai_loai(self):
		values = qc_plan_values("GLU-A")
		values["iqc_lines"][0]["qc_material"] = "HC_GLU"
		with self.assertRaises(frappe.ValidationError) as ctx:
			frappe.get_doc(values).insert()
		self.assertIn("HC_GLU", str(ctx.exception))
		self.assertIn("Vật liệu nội kiểm", str(ctx.exception))

	def test_TC_CLS_25_chat_chuan_sai_loai(self):
		values = qc_plan_values("GLU-A")
		values["calibration_lines"][0]["calibrator"] = "QC_L"
		with self.assertRaises(frappe.ValidationError) as ctx:
			frappe.get_doc(values).insert()
		self.assertIn("Chất chuẩn", str(ctx.exception))

	def test_ke_hoach_rong_hai_bang_luu_duoc(self):
		doc = self._insert(iqc_lines=[], calibration_lines=[])
		self.assertEqual(len(doc.iqc_lines), 0)

	def test_DI_11_mot_ke_hoach_moi_he_thong(self):
		make_qc_plan("GLU-A")
		with self.assertRaises(frappe.ValidationError) as ctx:
			self._insert()
		self.assertIn("KHCL-GLU-A", str(ctx.exception))

	def test_khong_doi_he_thong_sau_khi_luu(self):
		make_test_system("GLU-B", self.service, self.dept, "EQ_B", 25)
		doc = make_qc_plan("GLU-A")
		doc.test_system = "GLU-B"
		with self.assertRaises(frappe.ValidationError):
			doc.save()

	def test_he_thong_ngung_dung_van_co_ke_hoach(self):
		frappe.db.set_value("NC Test System", "GLU-A", "status", "Ngừng dùng")
		self.assertEqual(make_qc_plan("GLU-A").name, "KHCL-GLU-A")

	def _other_dept_user(self, email="clin.vs@normcore.test"):
		make_base(department="VS-CLS")
		ensure(
			"NC Department",
			"department_code",
			"VS-CLS",
			department_name="Vi sinh",
			department_type="Lâm sàng",
			cost_center="VS-CLS",
		)
		user = make_user(email, "NC Clinician")
		access.assign_department(user, "VS-CLS")
		return user

	def test_FR_ACC_008_phan_quyen_khoa_qua_he_thong(self):
		make_qc_plan("GLU-A")
		other = self._other_dept_user()
		own = make_user("clin.hs@normcore.test", "NC Clinician")
		access.assign_department(own, self.dept)
		frappe.set_user(other)
		doc = frappe.get_doc("NC QC Plan", "KHCL-GLU-A")
		self.assertFalse(frappe.has_permission("NC QC Plan", "read", doc=doc))
		self.assertFalse(frappe.has_permission("NC QC Plan", "write", doc=doc))
		self.assertNotIn("KHCL-GLU-A", frappe.get_list("NC QC Plan", pluck="name"))
		with self.assertRaises(frappe.PermissionError):
			frappe.get_doc(qc_plan_values("GLU-A")).insert()
		frappe.set_user(own)
		self.assertIn("KHCL-GLU-A", frappe.get_list("NC QC Plan", pluck="name"))
		doc = frappe.get_doc("NC QC Plan", "KHCL-GLU-A")
		doc.run_days_per_year = 250
		doc.save()
		self.assertEqual(frappe.db.get_value("NC QC Plan", "KHCL-GLU-A", "run_days_per_year"), 250)

	def test_clinician_khoa_dung_tao_duoc(self):
		own = make_user("clin.hs2@normcore.test", "NC Clinician")
		access.assign_department(own, self.dept)
		frappe.set_user(own)
		self.assertEqual(self._insert().name, "KHCL-GLU-A")

	def test_quyen_theo_ma_tran(self):
		make_qc_plan("GLU-A")
		readers = {"NC Finance", "NC Resource Manager", "NC Director", "NC Consultant", "NC Admin", "NC Auditor"}
		users = {role: make_user(f"qp.perm{i}@normcore.test", role) for i, role in enumerate(ROLES)}
		for role, user in users.items():
			if role in ("NC Clinician", "NC Department Head"):
				continue
			frappe.set_user(user)
			self.assertEqual(bool(frappe.has_permission("NC QC Plan", "read")), role in readers, role)
			for ptype in ("write", "create", "delete"):
				self.assertFalse(frappe.has_permission("NC QC Plan", ptype), f"{role} {ptype}")

	def test_auditor_doc_duoc_khong_ghi_duoc(self):
		make_qc_plan("GLU-A")
		frappe.set_user(make_user("qp.auditor@normcore.test", "NC Auditor"))
		doc = frappe.get_doc("NC QC Plan", "KHCL-GLU-A")
		self.assertTrue(frappe.has_permission("NC QC Plan", "read", doc=doc))
		doc.run_days_per_year = 100
		with self.assertRaises(frappe.PermissionError):
			doc.save()
		with self.assertRaises(frappe.PermissionError):
			frappe.get_doc(qc_plan_values("GLU-A")).insert()

	def test_vai_tro_khong_co_quyen_bi_tu_choi(self):
		make_qc_plan("GLU-A")
		users = {r: make_user(f"qp.none{i}@normcore.test", r) for i, r in enumerate(("NC Document Controller", "NC Council Member"))}
		for role, user in users.items():
			frappe.set_user(user)
			self.assertFalse(frappe.has_permission("NC QC Plan", "read"), role)
			with self.assertRaises(frappe.PermissionError):
				frappe.get_doc("NC QC Plan", "KHCL-GLU-A").check_permission("read")
