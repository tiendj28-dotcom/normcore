import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.tests.utils import make_user

FIN = "finance-map@test.local"
AUD = "auditor-map@test.local"
CLIN = "clinician-map@test.local"


def _m(prefix, cat="LABOR", **kw):
	return frappe.get_doc(
		{
			"doctype": "NC Account Mapping",
			"accounting_regime": "Hành chính sự nghiệp",
			"account_prefix": prefix,
			"cost_category": cat,
			**kw,
		}
	)


class TestNCAccountMapping(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		make_user(FIN, "NC Finance")
		make_user(AUD, "NC Auditor")
		make_user(CLIN, "NC Clinician")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_chuan_hoa_tien_to_va_chan_trung(self):
		frappe.set_user(FIN)
		doc = _m(" 7.77 x ").insert()
		self.assertEqual(doc.account_prefix, "777X")
		with self.assertRaisesRegex(frappe.ValidationError, "777X"):
			_m("777x", "UTILITY").insert()
		_m("777X", "UTILITY", accounting_regime="Doanh nghiệp").insert()  # chế độ khác thì được

	def test_tien_to_rong_bi_tu_choi(self):
		with self.assertRaises(frappe.ValidationError):
			_m(" . ").insert()

	def test_quyen_theo_ma_tran(self):
		frappe.set_user(AUD)
		self.assertTrue(frappe.has_permission("NC Account Mapping", "read"))
		for ptype in ("write", "create", "delete"):
			self.assertFalse(frappe.has_permission("NC Account Mapping", ptype), ptype)
		frappe.set_user(CLIN)
		self.assertFalse(frappe.has_permission("NC Account Mapping", "read"))
		frappe.set_user(FIN)
		self.assertTrue(frappe.has_permission("NC Account Mapping", "create"))
		self.assertFalse(frappe.has_permission("NC Account Mapping", "delete"))


class TestDefaultMapping(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		make_user(FIN, "NC Finance")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_TC_ACCT_08_bang_mac_dinh_va_lan_nhap_moi_theo_gia_tri_da_doi(self):
		from normcore.install import ensure_default_account_mapping
		from normcore.tests.accounting_fixtures import make_centers, make_import

		make_centers()
		ensure_default_account_mapping()
		rows = frappe.get_all(
			"NC Account Mapping", {"accounting_regime": "Hành chính sự nghiệp"}, ["name", "account_prefix", "cost_category", "note"]
		)
		self.assertEqual(len(rows), 13)
		self.assertTrue(all("Giả định — chờ xác nhận" in (r.note or "") for r in rows))
		ensure_default_account_mapping()  # gọi lại không trùng
		self.assertEqual(frappe.db.count("NC Account Mapping", {"accounting_regime": "Hành chính sự nghiệp"}), 13)

		frappe.set_user(FIN)
		old = make_import()
		m = frappe.get_doc("NC Account Mapping", {"account_prefix": "61113"})
		m.cost_category = "MANAGEMENT"
		m.save()
		ensure_default_account_mapping()  # không ghi đè giá trị đã sửa
		self.assertEqual(frappe.db.get_value("NC Account Mapping", m.name, "cost_category"), "MANAGEMENT")
		new = make_import()
		self.assertEqual(new.lines[3].cost_category, "MANAGEMENT")
		self.assertEqual(frappe.get_doc("NC Accounting Import", old.name).lines[3].cost_category, "DEPRECIATION")
		from normcore.api import accounting as api

		api.reapply_mapping(old.name)
		self.assertEqual(frappe.get_doc("NC Accounting Import", old.name).lines[3].cost_category, "MANAGEMENT")

	def test_bo_nhap_nc_account_mapping_chi_finance(self):
		from normcore.api import importer

		frappe.set_user(FIN)
		self.assertIn("nc_account_mapping", [s["key"] for s in importer.list_import_sets()])
		frappe.set_user("Administrator")
		from normcore.tests.accounting_fixtures import make_xlsx

		content = make_xlsx(
			[["Hành chính sự nghiệp", "7777", "UTILITY", "thử"]],
			header=["Chế độ kế toán *", "Tiền tố tài khoản *", "Loại chi phí *", "Ghi chú"],
		)
		r = importer.run_import("nc_account_mapping", content, "ghi", "m.xlsx")
		self.assertEqual((r["created"], r["error_count"]), (1, 0))
		r = importer.run_import("nc_account_mapping", content, "ghi", "m.xlsx")
		self.assertEqual((r["created"], r["updated"], r["unchanged"]), (0, 0, 1))
