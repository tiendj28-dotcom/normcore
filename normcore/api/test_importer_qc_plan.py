"""FEAT-032, FR-CLS-008 (phần kế hoạch chất lượng): bộ nhập nc_qc_plan (ASM-032-07)."""

import io

import frappe
from frappe.tests.utils import FrappeTestCase
from openpyxl import Workbook

from normcore.api import access
from normcore.api import importer as api
from normcore.core.importer import get_import_set, header_label
from normcore.tests.utils import make_cls_data, make_qc_items, make_qc_plan, make_test_system, make_user

QP = "nc_qc_plan"


def xlsx(rows):
	wb = Workbook()
	for r in rows:
		wb.active.append(r)
	buf = io.BytesIO()
	wb.save(buf)
	return buf.getvalue()


def head():
	return [header_label(c) for c in get_import_set(QP).columns]


class TestQcPlanImport(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		service, self.dept, _ = make_cls_data()
		make_test_system("GLU-A", service, self.dept, "EQ_A", 100)
		make_qc_items()
		self.clin = make_user("clin.imp.qp@normcore.test", "NC Clinician")
		self.fin = make_user("fin.imp.qp@normcore.test", "NC Finance")
		self.auditor = make_user("aud.imp.qp@normcore.test", "NC Auditor")
		access.assign_department(self.clin, self.dept)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_ma_he_thong_la_thanh_loi_dong_va_nhap_lai_cap_nhat_giu_dong_con(self):
		frappe.set_user(self.clin)
		res = api.run_import(QP, xlsx([head(), ["GLU-A", 300], ["GLU-X", 300]]), "ghi")
		self.assertEqual((res["created"], res["error_count"]), (1, 1), res["errors"])
		self.assertIn("Mã hệ thống xét nghiệm", str(res["errors"][0]))
		self.assertEqual(frappe.db.get_value("NC QC Plan", "KHCL-GLU-A", "run_days_per_year"), 300)
		doc = frappe.get_doc("NC QC Plan", "KHCL-GLU-A")
		doc.append(
			"iqc_lines",
			dict(qc_material="QC_L", levels=2, runs_per_day=1, qty_per_run=0.2, shared_parameter_count=20),
		)
		doc.save()
		res = api.run_import(QP, xlsx([head(), ["GLU-A", 250]]), "ghi")
		self.assertEqual((res["created"], res["updated"], res["error_count"]), (0, 1, 0), res["errors"])
		doc = frappe.get_doc("NC QC Plan", "KHCL-GLU-A")
		self.assertEqual(doc.run_days_per_year, 250)
		self.assertEqual(len(doc.iqc_lines), 1)

	def test_du_lieu_sai_thanh_loi_dong(self):
		frappe.set_user(self.clin)
		res = api.run_import(QP, xlsx([head(), ["GLU-A", 0]]), "ghi")
		self.assertEqual((res["created"], res["error_count"]), (0, 1), res["errors"])

	def test_vai_tro_chi_doc_va_auditor_khong_thay_bo(self):
		make_qc_plan("GLU-A")
		content = xlsx([head(), ["GLU-A", 100]])
		frappe.set_user(self.clin)
		self.assertIn(QP, [s["key"] for s in api.list_import_sets()])
		for user in (self.fin, self.auditor):
			frappe.set_user(user)
			self.assertNotIn(QP, [s["key"] for s in api.list_import_sets()])
			for mode in ("thu", "ghi"):
				self.assertRaises(frappe.PermissionError, api.run_import, QP, content, mode)
