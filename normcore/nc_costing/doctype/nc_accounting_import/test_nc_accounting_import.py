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

DT = "NC Accounting Import"
FIN = "finance-acct@test.local"
AUD = "auditor-acct@test.local"
CLIN = "clinician-acct@test.local"
EXPECTED = [
	"LABOR",
	"LABOR",
	"DRUG_SUPPLY",
	"DEPRECIATION",
	"UTILITY",
	"MANAGEMENT",
	"EXCLUDED",
	"LABOR",
	"MANAGEMENT",
	"MANAGEMENT",
]


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
		self.assertEqual(
			[(e["row"], e["column"]) for e in errs], [(3, "Số tiền"), (4, "Mã trung tâm chi phí")]
		)

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


class TestAccountingImportApi(FrappeTestCase):
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

	def test_TC_ACCT_02_khong_chot_khi_con_dong_loi(self):
		from normcore.api import accounting as api

		frappe.set_user(FIN)
		doc = make_import([["61111", "", "K01", 1], ["61111", "", "K01", "abc"], ["61112", "", "K99", 5]])
		s = api.get_import_summary(doc.name)
		self.assertEqual((s["error_count"], len(s["errors"]), s["can_finalize"]), (2, 2, False))
		self.assertIn("Dòng 3", s["errors"][0]["text"])
		with self.assertRaisesRegex(frappe.ValidationError, "2 dòng lỗi"):
			api.finalize(doc.name)
		self.assertEqual(frappe.db.get_value(DT, doc.name, "status"), "Nháp")

	def test_TC_ACCT_03_dong_chua_gan_chan_chot(self):
		from normcore.api import accounting as api

		frappe.set_user(FIN)
		doc = make_import([*GOLDEN_ROWS, ["99999", "Lạ", "K01", 7]])
		s = api.get_import_summary(doc.name)
		self.assertEqual(
			[(u["idx"], u["account_code"], u["cost_center"]) for u in s["unassigned"]], [(11, "99999", "K01")]
		)
		with self.assertRaises(frappe.ValidationError) as ctx:
			api.finalize(doc.name)
		msg = str(ctx.exception)
		self.assertIn("dòng 11", msg)
		self.assertIn("99999", msg)
		self.assertIn("K01", msg)
		row = next(r for r in doc.lines if r.account_code == "99999").name
		api.update_line(doc.name, row, "MANAGEMENT", 0, "Chi phí quản lý chung")
		self.assertEqual(api.finalize(doc.name)["status"], "Đã chốt")

	def test_TC_ACCT_04_update_line_can_ly_do_va_luu_nguoi_sua(self):
		from normcore.api import accounting as api

		frappe.set_user(FIN)
		doc = make_import()
		row = doc.lines[0].name
		for reason in (None, "", "   "):
			with self.assertRaisesRegex(frappe.ValidationError, "lý do"):
				api.update_line(doc.name, row, "MANAGEMENT", 0, reason)
		s = api.update_line(doc.name, row, "MANAGEMENT", 0, "Sai tài khoản")
		d = frappe.get_doc(DT, doc.name)
		self.assertEqual(
			(d.lines[0].cost_category, d.lines[0].changed_by, d.lines[0].change_reason),
			("MANAGEMENT", FIN, "Sai tài khoản"),
		)
		self.assertEqual(s["status"], "Nháp")
		s = api.update_line(doc.name, d.lines[1].name, "", 1, "Không tính vào giá")
		d.reload()
		self.assertEqual(d.lines[1].is_excluded, 1)
		self.assertEqual(s["excluded_count"], 2)
		with self.assertRaises(frappe.ValidationError):
			api.update_line(doc.name, "khong-co", "LABOR", 0, "x")
		with self.assertRaises(frappe.ValidationError):
			api.update_line(doc.name, row, "SAI", 0, "x")

	def test_TC_ACCT_06_chot_ghi_tong_khop_golden_va_khoa(self):
		import sys
		from pathlib import Path

		sys.path.insert(0, str(Path(frappe.get_app_path("normcore")).parent / "docs" / "golden"))
		import golden_engine as g

		from normcore.api import accounting as api

		frappe.set_user(FIN)
		doc = make_import()
		preview = api.get_import_summary(doc.name)
		self.assertTrue(preview["can_finalize"])
		self.assertEqual(len(preview["totals"]), 7)
		s = api.finalize(doc.name)
		self.assertEqual(s["status"], "Đã chốt")
		got = {}
		for t in s["totals"]:
			got.setdefault(t["cost_center"], {})[t["cost_category"]] = D(str(t["amount"]))
		self.assertEqual(got, g.ACCOUNTING)
		self.assertEqual(len(s["totals"]), 7)
		ev = frappe.get_all("NC Audit Event", {"ref_doctype": DT, "ref_name": doc.name, "event_type": "Khóa"})
		self.assertEqual(len(ev), 1)
		# sau chốt: mọi sửa bị từ chối
		d = frappe.get_doc(DT, doc.name)
		d.lines[0].amount = 1
		with self.assertRaisesRegex(frappe.ValidationError, "đã chốt"):
			d.save()
		for fn, args in (
			(api.update_line, (doc.name, d.lines[0].name, "LABOR", 0, "x")),
			(api.reapply_mapping, (doc.name,)),
			(api.reload_file, (doc.name,)),
			(api.finalize, (doc.name,)),
		):
			with self.assertRaises(frappe.ValidationError):
				fn(*args)
		frappe.set_user("Administrator")
		with self.assertRaises(frappe.PermissionError):
			frappe.delete_doc(DT, doc.name)

	def test_gan_lai_giu_dong_sua_tay_va_doc_lai_tep(self):
		from normcore.api import accounting as api

		frappe.set_user(FIN)
		doc = make_import()
		api.update_line(doc.name, doc.lines[0].name, "MANAGEMENT", 0, "Sửa tay")
		frappe.db.set_value("NC Account Mapping", {"account_prefix": "61112"}, "cost_category", "UTILITY")
		r = api.reapply_mapping(doc.name)
		self.assertEqual(r["changed"], 1)
		d = frappe.get_doc(DT, doc.name)
		self.assertEqual([x.cost_category for x in d.lines][:3], ["MANAGEMENT", "LABOR", "UTILITY"])
		self.assertEqual(d.lines[0].changed_by, FIN)
		s = api.reload_file(doc.name)
		d.reload()
		self.assertEqual(
			(s["line_count"], d.lines[0].cost_category, d.lines[0].changed_by), (10, "LABOR", None)
		)

	def test_quyen_api(self):
		from normcore.api import accounting as api

		frappe.set_user(FIN)
		doc = make_import()
		frappe.set_user(AUD)
		self.assertEqual(api.get_import_summary(doc.name)["name"], doc.name)
		with self.assertRaises(frappe.PermissionError):
			api.finalize(doc.name)
		with self.assertRaises(frappe.PermissionError):
			api.update_line(doc.name, doc.lines[0].name, "LABOR", 0, "x")
		with self.assertRaises(frappe.PermissionError):
			api.reapply_mapping(doc.name)
		with self.assertRaises(frappe.PermissionError):
			api.reload_file(doc.name)
		frappe.set_user(CLIN)
		with self.assertRaises(frappe.PermissionError):
			api.get_import_summary(doc.name)
		with self.assertRaises(frappe.PermissionError):
			api.download_template()

	def test_tai_tep_mau(self):
		from normcore.api import accounting as api

		frappe.set_user(AUD)
		api.download_template()
		self.assertEqual(frappe.response["filename"], "mau-nhap-so-lieu-ke-toan.xlsx")
		self.assertEqual(frappe.response["filecontent"][:2], b"PK")
