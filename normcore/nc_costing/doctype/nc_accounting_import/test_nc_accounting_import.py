import json
from decimal import Decimal as D

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.tests.accounting_fixtures import (
	GOLDEN_ROWS,
	ensure_default_mapping,
	make_centers,
	make_import,
	make_xlsx,
)
from normcore.tests.utils import make_user

FIN = "finance-acct@test.local"
AUD = "auditor-acct@test.local"
CLIN = "clinician-acct@test.local"
EXPECTED = ["LABOR", "LABOR", "DRUG_SUPPLY", "DEPRECIATION", "UTILITY", "MANAGEMENT", "EXCLUDED", "LABOR", "MANAGEMENT", "MANAGEMENT"]


class TestNCAccountingImport(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		make_centers()
		ensure_default_mapping()
		make_user(FIN, "NC Finance")
		make_user(AUD, "NC Auditor")
		make_user(CLIN, "NC Clinician")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_TC_ACCT_01_nap_tep_vang_ra_ban_nhap(self):
		frappe.set_user(FIN)
		doc = make_import()
		self.assertEqual(doc.status, "Nháp")
		self.assertEqual(doc.line_count, 10)
		self.assertEqual(D(str(doc.total_amount)), D("2105000000"))
		self.assertEqual(doc.error_count, 0)
		self.assertEqual([r.cost_category for r in doc.lines], EXPECTED)
		self.assertEqual([r.is_excluded for r in doc.lines], [0] * 6 + [1] + [0] * 3)
		self.assertEqual(doc.lines[4].account_code, "611122")  # tiền tố dài nhất, không phải 61112
		self.assertTrue(doc.name.startswith("KT-2026-"))

	def test_TC_ACCT_02_loi_dong_khong_chot_duoc(self):
		frappe.set_user(FIN)
		rows = [
			["61111", "", "K01", 100],
			["61111", "", "K01", "abc"],
			["61112", "", "K99", 50],
			["61118", "", "K01", 20],
		]
		doc = make_import(rows)
		self.assertEqual((doc.status, doc.error_count, doc.line_count), ("Nháp", 2, 2))
		errs = json.loads(doc.import_errors)
		self.assertEqual([(e["row"], e["column"]) for e in errs], [(3, "Số tiền"), (4, "Mã trung tâm chi phí")])

	def test_thieu_ma_tai_khoan_va_tep_khong_hop_le(self):
		frappe.set_user(FIN)
		doc = make_import([[None, "", "K01", 5], ["61111", "", "K01", 5]])
		self.assertEqual(doc.error_count, 1)
		self.assertIn("ô bắt buộc", json.loads(doc.import_errors)[0]["message"])
		before = frappe.db.count("NC Accounting Import")
		with self.assertRaises(frappe.ValidationError):
			make_import(content=b"khong phai excel")
		with self.assertRaises(frappe.ValidationError):
			make_import(content=make_xlsx([["61111", "", "K01", 1]]), filename="kt.csv")
		with self.assertRaises(frappe.ValidationError):
			make_import(year=1999)
		self.assertEqual(frappe.db.count("NC Accounting Import"), before)

	def test_TC_ACCT_04_sua_truc_tiep_khong_ly_do_bi_tu_choi(self):
		frappe.set_user(FIN)
		doc = make_import()
		doc.lines[0].cost_category = "MANAGEMENT"
		with self.assertRaisesRegex(frappe.ValidationError, "lý do"):
			doc.save()
		doc.reload()
		doc.lines[0].cost_category = "MANAGEMENT"
		doc.lines[0].change_reason = "Tài khoản ghi nhầm"
		doc.save()
		doc.reload()
		self.assertEqual(doc.lines[0].cost_category, "MANAGEMENT")
		self.assertEqual(doc.lines[0].changed_by, FIN)
		self.assertEqual(doc.lines[0].change_reason, "Tài khoản ghi nhầm")
		self.assertFalse(doc.lines[1].changed_by)

	def test_loai_tru_can_ly_do_va_excluded_tu_loai_tru(self):
		frappe.set_user(FIN)
		doc = make_import()
		doc.lines[1].is_excluded = 1
		with self.assertRaisesRegex(frappe.ValidationError, "lý do"):
			doc.save()
		doc.reload()
		doc.lines[1].cost_category = "EXCLUDED"
		doc.lines[1].change_reason = "Không tính vào giá"
		doc.save()
		doc.reload()
		self.assertEqual(doc.lines[1].is_excluded, 1)
		self.assertEqual(D(str(doc.total_amount)), D("2105000000"))

	def test_khong_them_bot_hay_sua_so_tien_dong(self):
		frappe.set_user(FIN)
		doc = make_import()
		doc.lines[0].amount = 1
		with self.assertRaisesRegex(frappe.ValidationError, "đọc lại tệp"):
			doc.save()
		doc.reload()
		doc.remove(doc.lines[0])
		with self.assertRaisesRegex(frappe.ValidationError, "đọc lại tệp"):
			doc.save()

	def test_trang_thai_chi_doi_bang_chot(self):
		frappe.set_user(FIN)
		doc = make_import()
		doc.status = "Đã chốt"
		with self.assertRaises(frappe.ValidationError):
			doc.save()

	def test_FR_ACCT_011_lan_nhap_thu_hai_cung_nam_giu_lan_cu(self):
		frappe.set_user(FIN)
		first = make_import()
		modified = frappe.db.get_value("NC Accounting Import", first.name, "modified")
		second = make_import(GOLDEN_ROWS[:2])
		self.assertNotEqual(first.name, second.name)
		self.assertTrue(first.name.startswith("KT-2026-") and second.name.startswith("KT-2026-"))
		self.assertEqual(int(first.name[-2:]) + 1, int(second.name[-2:]))
		self.assertEqual(frappe.db.get_value("NC Accounting Import", first.name, "modified"), modified)
		self.assertEqual(len(frappe.get_doc("NC Accounting Import", first.name).lines), 10)

	def test_auditor_chi_doc_va_vai_tro_khac_khong_co_quyen(self):
		frappe.set_user(FIN)
		doc = make_import()
		frappe.set_user(AUD)
		self.assertTrue(frappe.has_permission("NC Accounting Import", "read", doc=doc.name))
		for ptype in ("write", "create", "delete"):
			self.assertFalse(frappe.has_permission("NC Accounting Import", ptype), ptype)
		frappe.set_user(CLIN)
		self.assertFalse(frappe.has_permission("NC Accounting Import", "read"))
		with self.assertRaises(frappe.PermissionError):
			frappe.get_doc("NC Accounting Import", doc.name).check_permission("read")

	def test_khong_ai_xoa_duoc(self):
		frappe.set_user(FIN)
		doc = make_import()
		self.assertFalse(frappe.has_permission("NC Accounting Import", "delete", doc=doc.name))
