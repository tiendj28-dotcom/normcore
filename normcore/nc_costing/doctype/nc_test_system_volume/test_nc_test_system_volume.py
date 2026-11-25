"""FEAT-035: NC Test System Volume (FR-ACCT-012, 013, 014; DI-14)."""

import frappe
import pymysql
from frappe.tests.utils import FrappeTestCase

from normcore.api import access
from normcore.tests.utils import ensure, make_base, make_cls_data, make_test_system, make_user

DT = "NC Test System Volume"


class TestNCTestSystemVolume(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.service, self.dept, _ = make_cls_data()
		make_test_system("GLU-A", self.service, self.dept, "EQ_A", 75)
		make_test_system("GLU-B", self.service, self.dept, "EQ_B", 25)
		self.fin = make_user("fin.tsv@normcore.test", "NC Finance")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _v(self, system="GLU-A", **kw):
		return frappe.get_doc(
			{"doctype": DT, "fiscal_year": 2026, "test_system": system, "patient_results": 12000, **kw}
		)

	def test_mac_dinh_kich_ban_va_lay_dich_vu_khoa_tu_he_thong(self):
		frappe.set_user(self.fin)
		v = self._v().insert()
		self.assertEqual(v.scenario, "Thực tế 12 tháng")
		self.assertEqual(v.technical_service, self.service)
		self.assertEqual(v.department, self.dept)

	def test_DI_14_trung_nam_kich_ban_he_thong(self):
		frappe.set_user(self.fin)
		self._v().insert()
		with self.assertRaisesRegex(frappe.ValidationError, "Đã có sản lượng năm 2026"):
			self._v().insert()
		self.assertTrue(self._v(scenario="Kế hoạch").insert().name)
		self.assertTrue(self._v("GLU-B").insert().name)

	def test_chi_muc_duy_nhat_o_csdl(self):
		self._v().insert()
		with self.assertRaises(pymysql.err.IntegrityError):
			frappe.db.sql(
				f"insert into `tab{DT}` (name, fiscal_year, scenario, test_system, patient_results)"
				" values ('x-dup', 2026, 'Thực tế 12 tháng', 'GLU-A', 1)"
			)

	def test_so_am_va_thieu_qbn(self):
		frappe.set_user(self.fin)
		with self.assertRaises(frappe.ValidationError):
			self._v(patient_results=-1).insert()
		with self.assertRaises(frappe.ValidationError):
			self._v(iqc_tests=-1).insert()
		with self.assertRaises(frappe.MandatoryError):
			self._v(patient_results=None).insert()

	def test_o_test_phu_de_trong_la_null(self):
		frappe.set_user(self.fin)
		v = self._v("GLU-B", patient_results=4000).insert()
		row = frappe.db.get_value(
			DT, v.name, ["iqc_tests", "calibration_tests", "rerun_tests", "eqa_tests"], as_dict=True
		)
		self.assertEqual(list(row.values()), [None] * 4)

	def test_quyen_theo_ma_tran(self):
		doc = self._v().insert()
		cases = {
			"NC Finance": (True, True),
			"NC Director": (True, False),
			"NC Admin": (True, False),
			"NC Auditor": (True, False),
			"NC Clinician": (False, False),
			"NC Consultant": (False, False),
			"NC Resource Manager": (False, False),
			"NC Council Member": (False, False),
			"NC Document Controller": (False, False),
		}
		users = {role: make_user(f"tsv.{i}@normcore.test", role) for i, role in enumerate(cases)}
		for role, (read, write) in cases.items():
			frappe.set_user(users[role])
			self.assertEqual(bool(frappe.has_permission(DT, "read")), read, role)
			self.assertEqual(bool(frappe.has_permission(DT, "create")), write, role)
			self.assertEqual(bool(frappe.has_permission(DT, "write", doc=doc)), write, role)
			self.assertFalse(frappe.has_permission(DT, "delete"), role)

	def test_auditor_khong_ghi_duoc(self):
		doc = self._v().insert()
		aud = make_user("tsv.aud@normcore.test", "NC Auditor")
		frappe.set_user(aud)
		self.assertTrue(frappe.has_permission(DT, "read", doc=doc))
		with self.assertRaises(frappe.PermissionError):
			self._v("GLU-B").insert()
		doc.reload()
		doc.patient_results = 1
		with self.assertRaises(frappe.PermissionError):
			doc.save()

	def test_clinician_khong_doc(self):
		self._v().insert()
		clin = make_user("tsv.clin@normcore.test", "NC Clinician")
		access.assign_department(clin, self.dept)
		frappe.set_user(clin)
		self.assertFalse(frappe.has_permission(DT, "read"))
		with self.assertRaises(frappe.PermissionError):
			frappe.get_list(DT, pluck="name")

	def test_department_head_chi_doc_khoa_minh(self):
		ensure(
			"NC Department",
			"department_code",
			"VS-CLS",
			department_name="Vi sinh",
			department_type="Lâm sàng",
			cost_center=make_base(department="VS-CLS")[1],
		)
		doc = self._v().insert()
		mine = make_user("tsv.head1@normcore.test", "NC Department Head")
		other = make_user("tsv.head2@normcore.test", "NC Department Head")
		access.assign_department(mine, self.dept)
		access.assign_department(other, "VS-CLS")
		frappe.set_user(mine)
		self.assertIn(doc.name, frappe.get_list(DT, pluck="name"))
		self.assertTrue(frappe.has_permission(DT, "read", doc=doc))
		self.assertFalse(frappe.has_permission(DT, "write", doc=doc))
		frappe.set_user(other)
		self.assertNotIn(doc.name, frappe.get_list(DT, pluck="name"))
		self.assertFalse(frappe.has_permission(DT, "read", doc=doc))
