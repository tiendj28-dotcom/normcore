"""FEAT-016 — bộ nhập sản lượng và tiêu chí (TC-ACCT-05, 09)."""

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.api import importer
from normcore.tests.accounting_fixtures import make_centers, make_xlsx
from normcore.tests.utils import ensure, make_base, make_user

FIN = "finance-impacct@test.local"
AUD = "auditor-impacct@test.local"
VOL_H = ["Năm tài chính *", "Mã dịch vụ *", "Mã khoa *", "Kịch bản sản lượng *", "Sản lượng *"]
DRV_H = ["Năm tài chính *", "Mã trung tâm chi phí *", "Số nhân lực", "Diện tích (m²)", "Doanh thu"]
TT = "Thực tế 12 tháng"


class TestImporterAccounting(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		make_centers()
		make_base()
		ensure("NC Technical Service", "service_code", "DV-TEST-B", service_name="Dịch vụ B")
		make_user(FIN, "NC Finance")
		make_user(AUD, "NC Auditor")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_TC_ACCT_05_ma_dich_vu_la_bao_loi_dong_dung_van_luu(self):
		frappe.set_user(FIN)
		c = make_xlsx(
			[
				[2026, "DV-TEST-A", "KHOA-TEST", TT, 4000],
				[2026, "DV-TEST-B", "KHOA-TEST", TT, 6000],
				[2026, "DV-X", "KHOA-TEST", TT, 10],
			],
			header=VOL_H,
		)
		r = importer.run_import("nc_service_volume", c, "ghi", "v.xlsx")
		self.assertEqual((r["created"], r["error_count"]), (2, 1))
		self.assertEqual(r["errors"][0]["row"], 4)
		self.assertEqual(r["errors"][0]["column"], "Mã dịch vụ")
		self.assertEqual(frappe.db.count("NC Service Volume", {"fiscal_year": 2026}), 2)
		r = importer.run_import("nc_service_volume", c, "ghi", "v.xlsx")
		self.assertEqual((r["created"], r["unchanged"], r["error_count"]), (0, 2, 1))
		self.assertEqual(frappe.db.count("NC Service Volume", {"fiscal_year": 2026}), 2)

	def test_ma_khoa_la_va_cap_nhat_san_luong(self):
		frappe.set_user(FIN)
		c = make_xlsx([[2026, "DV-TEST-A", "K-LA", TT, 5]], header=VOL_H)
		r = importer.run_import("nc_service_volume", c, "ghi", "v.xlsx")
		self.assertEqual((r["created"], r["error_count"]), (0, 1))
		self.assertIn("Mã khoa", r["errors"][0]["column"])
		importer.run_import(
			"nc_service_volume",
			make_xlsx([[2026, "DV-TEST-A", "KHOA-TEST", TT, 5]], header=VOL_H),
			"ghi",
			"v.xlsx",
		)
		r = importer.run_import(
			"nc_service_volume",
			make_xlsx([[2026, "DV-TEST-A", "KHOA-TEST", TT, 9]], header=VOL_H),
			"ghi",
			"v.xlsx",
		)
		self.assertEqual(r["updated"], 1)
		self.assertEqual(frappe.db.get_value("NC Service Volume", {"fiscal_year": 2026}, "volume"), 9)

	def test_TC_ACCT_09_nhap_tieu_chi(self):
		frappe.set_user(FIN)
		c = make_xlsx(
			[[2026, "K01", 20, None, None], [2026, "K02", 30, None, None], [2026, "K01", 5, None, None]],
			header=DRV_H,
		)
		r = importer.run_import("nc_cost_center_driver", c, "ghi", "d.xlsx")
		self.assertEqual((r["created"], r["error_count"]), (2, 1))
		self.assertIn("trùng khóa", r["errors"][0]["message"])
		self.assertEqual(frappe.db.count("NC Cost Center Driver", {"fiscal_year": 2026}), 2)

	def test_auditor_khong_thay_bo_nhap_va_khong_nhap_duoc(self):
		frappe.set_user(AUD)
		keys = [s["key"] for s in importer.list_import_sets()]
		self.assertNotIn("nc_service_volume", keys)
		self.assertNotIn("nc_cost_center_driver", keys)
		with self.assertRaises(frappe.PermissionError):
			importer.run_import(
				"nc_service_volume",
				make_xlsx([[2026, "DV-TEST-A", "KHOA-TEST", TT, 1]], header=VOL_H),
				"ghi",
				"v.xlsx",
			)
