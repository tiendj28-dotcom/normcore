"""FEAT-033, UC-020 1a, FR-CMP-001: bộ nhập nc_equipment_compliance."""

import io

import frappe
from frappe.tests.utils import FrappeTestCase
from openpyxl import Workbook, load_workbook

from normcore.api import importer as api
from normcore.core.importer import get_import_set, header_label
from normcore.tests.utils import make_base, make_equipment, make_private_file, make_user

KEY = "nc_equipment_compliance"


def xlsx(rows):
	wb = Workbook()
	for r in rows:
		wb.active.append(r)
	buf = io.BytesIO()
	wb.save(buf)
	return buf.getvalue()


def head():
	return [header_label(c) for c in get_import_set(KEY).columns]


def row(code="NK-HS1", **kw):
	vals = {
		"record_code": code,
		"equipment": "TB-NHAP",
		"record_type": "Kiểm định",
		"cycle_months": 12,
		"provider": "Trung tâm kiểm định",
		"cost_per_time": 5000000,
		"performed_on": "2026-01-10",
		"expiry_date": "2099-01-10",
		"attachment": make_private_file(),
	}
	vals.update(kw)
	return [vals.get(c.fieldname) for c in get_import_set(KEY).columns]


class TestComplianceImport(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		_, dept, _ = make_base()
		make_equipment("TB-NHAP", department=dept)
		self.rm = make_user("rm.impcmp@normcore.test", "NC Resource Manager")
		self.fin = make_user("fin.impcmp@normcore.test", "NC Finance")
		self.auditor = make_user("aud.impcmp@normcore.test", "NC Auditor")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_UC_020_mau_dung_cot(self):
		frappe.set_user(self.rm)
		name, content = api.build_template_file(KEY)
		rows = list(load_workbook(io.BytesIO(content)).active.iter_rows(values_only=True))
		self.assertEqual(list(rows[0]), head())
		self.assertIn(KEY, name)
		self.assertEqual(
			[c.fieldname for c in get_import_set(KEY).columns],
			[
				"record_code",
				"equipment",
				"record_type",
				"cycle_months",
				"provider",
				"cost_per_time",
				"performed_on",
				"expiry_date",
				"attachment",
				"note",
			],
		)

	def test_UC_020_tao_ho_so_co_trang_thai_va_chay_lai_khong_trung(self):
		frappe.set_user(self.rm)
		content = xlsx([head(), row()])
		first = api.run_import(KEY, content, "ghi")
		self.assertEqual((first["created"], first["error_count"]), (1, 0), first["errors"])
		doc = frappe.get_doc("NC Equipment Compliance", {"record_code": "NK-HS1"})
		self.assertEqual(doc.status, "Còn hạn")
		self.assertTrue(doc.department)
		again = api.run_import(KEY, content, "ghi")
		self.assertEqual((again["created"], again["error_count"]), (0, 0))
		self.assertEqual(frappe.db.count("NC Equipment Compliance", {"record_code": "NK-HS1"}), 1)

	def test_UC_020_1b_dong_loi_khong_lam_hong_dong_khac(self):
		frappe.set_user(self.rm)
		rows = [
			head(),
			row("NK-OK"),
			row("NK-THIEU-TEP", attachment=None),
			row("NK-CHU-KY-0", cycle_months=0),
			row("NK-TEP-LA", attachment="/private/files/khong-ton-tai.pdf"),
			row("NK-TEP-PUBLIC", attachment="/files/chung-tu.txt"),
			row("NK-TB-LA", equipment="TB-KHONG-CO"),
			row("NK-HAN-SAI", expiry_date="2025-01-01"),
		]
		res = api.run_import(KEY, xlsx(rows), "ghi")
		self.assertEqual((res["created"], res["error_count"]), (1, 6), res["errors"])
		self.assertTrue(frappe.db.exists("NC Equipment Compliance", {"record_code": "NK-OK"}))
		for code in ("NK-THIEU-TEP", "NK-CHU-KY-0", "NK-TEP-LA", "NK-TEP-PUBLIC", "NK-TB-LA", "NK-HAN-SAI"):
			self.assertFalse(frappe.db.exists("NC Equipment Compliance", {"record_code": code}), code)

	def test_FR_ACC_002_chi_resource_manager_nhap_duoc(self):
		frappe.set_user(self.rm)
		self.assertIn(KEY, [s["key"] for s in api.list_import_sets()])
		for user in (self.fin, self.auditor):
			frappe.set_user(user)
			self.assertNotIn(KEY, [s["key"] for s in api.list_import_sets()])
			self.assertRaises(frappe.PermissionError, api.run_import, KEY, xlsx([head(), row()]), "ghi")
