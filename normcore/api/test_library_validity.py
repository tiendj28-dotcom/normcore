"""Hiệu lực theo ngày (FEAT-020: TC-LIB-04, FR-LIB-006)."""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, getdate, today

from normcore.api import library as api
from normcore.nc_library.doctype.nc_legal_document.library_fixtures import make_legal_document


def _section(doc, no="1", **kw):
	return frappe.get_doc(
		{
			"doctype": "NC Legal Section",
			"legal_document": doc.name,
			"section_no": no,
			"plain_text": "nội dung",
			**kw,
		}
	).insert(ignore_permissions=True)


def _status(dt, name):
	return frappe.db.get_value(dt, name, "validity_status")


class TestLibraryValidity(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.db.rollback()

	def test_TC_LIB_04_hieu_luc_theo_ngay(self):
		tomorrow = add_days(getdate(today()), 1)
		doc = make_legal_document("HL/01", effective_date=str(tomorrow))
		sec = _section(doc)
		api.refresh_validity(today=getdate(today()))
		self.assertEqual(_status("NC Legal Document", doc.name), "Chưa hiệu lực")
		self.assertEqual(_status("NC Legal Section", sec.name), "Chưa hiệu lực")
		out = api.refresh_validity(today=tomorrow)
		self.assertEqual(_status("NC Legal Document", doc.name), "Còn hiệu lực")
		self.assertEqual(_status("NC Legal Section", sec.name), "Còn hiệu lực")
		self.assertGreaterEqual(out["documents"], 1)
		self.assertGreaterEqual(out["sections"], 1)

	def test_FR_LIB_006_van_ban_het_hieu_luc_sau_ngay_het_han(self):
		doc = make_legal_document("HL/02", effective_date="2020-01-01", expiry_date="2026-06-30")
		sec = _section(doc)
		api.refresh_validity(today=getdate("2026-06-30"))
		self.assertEqual(_status("NC Legal Document", doc.name), "Còn hiệu lực")
		api.refresh_validity(today=getdate("2026-07-01"))
		self.assertEqual(_status("NC Legal Document", doc.name), "Hết hiệu lực")
		self.assertEqual(_status("NC Legal Section", sec.name), "Hết hiệu lực")

	def test_FR_LIB_006_muc_co_han_rieng(self):
		doc = make_legal_document("HL/03", effective_date="2020-01-01")
		a = _section(doc, "1", expiry_date="2026-03-01")
		b = _section(doc, "2")
		api.refresh_validity(today=getdate("2026-03-02"))
		self.assertEqual(_status("NC Legal Section", a.name), "Hết hiệu lực")
		self.assertEqual(_status("NC Legal Section", b.name), "Còn hiệu lực")
		self.assertEqual(_status("NC Legal Document", doc.name), "Còn hiệu lực")

	def test_FR_LIB_006_chi_ghi_dong_doi_va_khong_doi_modified(self):
		doc = make_legal_document("HL/04", effective_date="2020-01-01")
		_section(doc)
		before = frappe.db.get_value("NC Legal Document", doc.name, "modified")
		out = api.refresh_validity(today=getdate(today()))
		self.assertEqual(frappe.db.get_value("NC Legal Document", doc.name, "modified"), before)
		self.assertEqual(out["sections"], 0)

	def test_FR_LIB_006_tac_vu_ngay_chay_duoc(self):
		doc = make_legal_document("HL/05", effective_date="2020-01-01")
		frappe.db.set_value("NC Legal Document", doc.name, "validity_status", "Chưa hiệu lực")
		api.daily_job()
		self.assertEqual(_status("NC Legal Document", doc.name), "Còn hiệu lực")

	def test_FR_LIB_006_tac_vu_ngay_dang_ky_trong_hooks(self):
		hooks = frappe.get_hooks("scheduler_events")
		self.assertIn("normcore.api.library.daily_job", hooks["daily"])
