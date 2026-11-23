"""FEAT-031, FR-CLS-008 (phần hệ thống xét nghiệm): bộ nhập nc_test_system (TC-CLS-23)."""

import io

import frappe
from frappe.tests.utils import FrappeTestCase
from openpyxl import Workbook, load_workbook

from normcore.api import access
from normcore.api import importer as api
from normcore.core.importer import get_import_set, header_label
from normcore.tests.utils import ensure, make_cls_data, make_user

TS = "nc_test_system"


def xlsx(rows):
	wb = Workbook()
	for r in rows:
		wb.active.append(r)
	buf = io.BytesIO()
	wb.save(buf)
	return buf.getvalue()


def head():
	return [header_label(c) for c in get_import_set(TS).columns]


def row(code, equipment="EQ_A", dept="HS-CLS", **kw):
	vals = {
		"test_system_code": code,
		"technical_service": "GLU",
		"department": dept,
		"main_equipment": equipment,
		"volume_share_pct": 50,
		"est_rerun_rate": 2,
		"est_wastage_rate": 3,
	}
	vals.update(kw)
	return [vals.get(c.fieldname) for c in get_import_set(TS).columns]


class TestTestSystemImport(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		make_cls_data()
		self.clin = make_user("clin.imp.ts@normcore.test", "NC Clinician")
		self.head = make_user("head.imp.ts@normcore.test", "NC Department Head")
		self.fin = make_user("fin.imp.ts@normcore.test", "NC Finance")
		self.auditor = make_user("aud.imp.ts@normcore.test", "NC Auditor")
		access.assign_department(self.clin, "HS-CLS")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_TC_CLS_23_dong_thiet_bi_la_bao_loi_dong_dung_duoc_luu(self):
		frappe.set_user(self.clin)
		rows = [
			head(),
			row("GLU-A", volume_share_pct=75),
			row("GLU-X", "EQ_X"),
			row("GLU-B", "EQ_B", volume_share_pct=25),
		]
		res = api.run_import(TS, xlsx(rows), "ghi")
		self.assertEqual((res["created"], res["error_count"]), (2, 1), res["errors"])
		err = str(res["errors"][0])
		self.assertIn("EQ_X", err)
		self.assertIn("Mã thiết bị chính", err)
		self.assertTrue(frappe.db.exists("NC Test System", "GLU-A"))
		self.assertTrue(frappe.db.exists("NC Test System", "GLU-B"))
		self.assertFalse(frappe.db.exists("NC Test System", "GLU-X"))
		self.assertEqual(
			frappe.db.get_value("NC Test System", "GLU-A", ["est_rerun_rate", "est_wastage_rate"]), (2, 3)
		)
		again = api.run_import(
			TS,
			xlsx([head(), row("GLU-A", volume_share_pct=75), row("GLU-B", "EQ_B", volume_share_pct=25)]),
			"ghi",
		)
		self.assertEqual((again["created"], again["unchanged"], again["error_count"]), (0, 2, 0))
		self.assertEqual(frappe.db.count("NC Test System"), 2)

	def test_cap_nhat_theo_ma_va_loi_nghiep_vu_thanh_loi_dong(self):
		frappe.set_user(self.clin)
		api.run_import(TS, xlsx([head(), row("GLU-A", volume_share_pct=75)]), "ghi")
		res = api.run_import(
			TS,
			xlsx(
				[
					head(),
					row("GLU-A", volume_share_pct=60, status="Ngừng dùng"),
					row("GLU-Z", volume_share_pct=150),
				]
			),
			"ghi",
		)
		self.assertEqual((res["updated"], res["error_count"]), (1, 1), res["errors"])
		self.assertEqual(
			frappe.db.get_value("NC Test System", "GLU-A", ["volume_share_pct", "status"]), (60, "Ngừng dùng")
		)

	def test_khoa_khong_duoc_gan_thanh_loi_dong(self):
		ensure(
			"NC Department",
			"department_code",
			"VS-IMP",
			department_name="Vi sinh",
			department_type="Lâm sàng",
			cost_center="HS-CLS",
		)
		frappe.set_user(self.clin)
		res = api.run_import(TS, xlsx([head(), row("GLU-V", dept="VS-IMP"), row("GLU-A")]), "ghi")
		self.assertEqual((res["created"], res["error_count"]), (1, 1), res["errors"])
		self.assertFalse(frappe.db.exists("NC Test System", "GLU-V"))

	def test_mau_tai_ve_co_dong_dau_va_dong_vi_du(self):
		frappe.set_user(self.clin)
		name, content = api.build_template_file(TS)
		rows = list(load_workbook(io.BytesIO(content)).active.iter_rows(values_only=True))
		self.assertEqual(list(rows[0]), head())
		self.assertIn(TS, name)

	def test_quyen_nhap_vai_tro_chi_doc_va_auditor_bi_tu_choi(self):
		content = xlsx([head(), row("GLU-Q")])
		for user in (self.head, self.clin):
			self.assertIn(TS, [s["key"] for s in _sets(user)])
		for user in (self.fin, self.auditor):
			frappe.set_user(user)
			self.assertNotIn(TS, [s["key"] for s in api.list_import_sets()])
			for mode in ("thu", "ghi"):
				self.assertRaises(frappe.PermissionError, api.run_import, TS, content, mode)
		frappe.set_user("Administrator")
		self.assertFalse(frappe.db.exists("NC Test System", "GLU-Q"))


def _sets(user):
	frappe.set_user(user)
	return api.list_import_sets()
