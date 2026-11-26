"""Thay thế văn bản (FEAT-021: TC-LIB-05, TC-LIB-06, FR-LIB-007, FR-LIB-008)."""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, getdate, today

from normcore.api import library as api
from normcore.nc_library.doctype.nc_legal_document.library_fixtures import make_legal_document
from normcore.tests.utils import make_user


def _section(doc, no):
	return frappe.get_doc(
		{"doctype": "NC Legal Section", "legal_document": doc.name, "section_no": no, "plain_text": "nội dung"}
	).insert(ignore_permissions=True)


def _status(dt, name):
	return frappe.db.get_value(dt, name, "validity_status")


def _pair(a="TT/A", b="TT/B", sections=("1", "2", "3", "4", "5")):
	old = make_legal_document(b, effective_date="2026-01-01")
	secs = {n: _section(old, n) for n in sections}
	new = make_legal_document(a, effective_date="2026-02-01")
	return new, old, secs


class TestLibrarySupersession(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_TC_LIB_05_thay_toan_bo(self):
		a, b, secs = _pair()
		out = api.declare_supersession(a.name, b.name, "Toàn bộ", "2099-07-01")
		self.assertEqual(str(out["expiry_date"]), "2099-06-30")
		a.reload()
		row = a.supersessions[0]
		self.assertEqual(
			(row.superseded_document, row.scope, str(row.from_date), row.superseded_sections or ""),
			(b.name, "Toàn bộ", "2099-07-01", ""),
		)
		api.refresh_validity(today=getdate("2099-06-30"))
		self.assertEqual(_status("NC Legal Document", b.name), "Còn hiệu lực")
		self.assertTrue(all(_status("NC Legal Section", s.name) == "Còn hiệu lực" for s in secs.values()))
		api.refresh_validity(today=getdate("2099-07-01"))
		self.assertEqual(_status("NC Legal Document", b.name), "Hết hiệu lực")
		self.assertTrue(all(_status("NC Legal Section", s.name) == "Hết hiệu lực" for s in secs.values()))
		self.assertTrue(frappe.db.exists("Comment", {"reference_doctype": "NC Legal Document",
			"reference_name": b.name, "comment_type": "Info", "content": ["like", "%Bị thay thế toàn bộ%"]}))

	def test_TC_LIB_06_thay_mot_phan(self):
		a, b, secs = _pair()
		out = api.declare_supersession(a.name, b.name, "Một phần", "2099-07-01", ["5", "2"])
		self.assertEqual(sorted(s["section_no"] for s in out["sections"]), ["2", "5"])
		a.reload()
		self.assertEqual(a.supersessions[0].superseded_sections, "2, 5")
		for no, s in secs.items():
			exp = frappe.db.get_value("NC Legal Section", s.name, "expiry_date")
			self.assertEqual(str(exp) if exp else None, "2099-06-30" if no in ("2", "5") else None)
		self.assertIsNone(frappe.db.get_value("NC Legal Document", b.name, "expiry_date"))
		api.refresh_validity(today=getdate("2099-07-01"))
		for no, s in secs.items():
			self.assertEqual(
				_status("NC Legal Section", s.name), "Hết hiệu lực" if no in ("2", "5") else "Còn hiệu lực", no
			)
		self.assertEqual(_status("NC Legal Document", b.name), "Còn hiệu lực")

	def test_FR_LIB_007_kiem_khi_luu(self):
		a, b, _s = _pair()

		def attempt(**kw):
			frappe.db.savepoint("att")
			with self.assertRaises(frappe.ValidationError) as cm:
				api.declare_supersession(**{"legal_document": a.name, "superseded_document": b.name,
					"scope": "Toàn bộ", "from_date": "2099-07-01", **kw})
			frappe.db.rollback(save_point="att")
			return str(cm.exception)

		self.assertIn("chính nó", attempt(superseded_document=a.name))
		self.assertIn("sau ngày hiệu lực", attempt(from_date="2026-01-01"))
		self.assertIn("Chọn ít nhất một mục", attempt(scope="Một phần"))
		self.assertIn("không có mục: 9", attempt(scope="Một phần", sections="1, 9"))
		# Toàn bộ xóa danh sách mục
		api.declare_supersession(a.name, b.name, "Toàn bộ", "2099-07-01", "1, 2")
		a.reload()
		self.assertFalse(a.supersessions[0].superseded_sections)
		# hai dòng cùng B trong một lần lưu
		a.append("supersessions", {"superseded_document": b.name, "scope": "Toàn bộ", "from_date": "2099-08-01"})
		with self.assertRaises(frappe.ValidationError) as cm:
			a.save()
		self.assertIn("đã được khai báo thay thế ở dòng 1", str(cm.exception))

	def test_FR_LIB_007_hai_van_ban_cung_thay_lay_ngay_som(self):
		a, b, _s = _pair()
		c = make_legal_document("TT/C", effective_date="2026-02-01")
		api.declare_supersession(a.name, b.name, "Toàn bộ", "2099-09-01")
		api.declare_supersession(c.name, b.name, "Toàn bộ", "2099-07-01")
		self.assertEqual(str(frappe.db.get_value("NC Legal Document", b.name, "expiry_date")), "2099-06-30")
		api.declare_supersession(a.name, b.name, "Toàn bộ", "2099-09-01")  # lưu lại: không đổi
		self.assertEqual(str(frappe.db.get_value("NC Legal Document", b.name, "expiry_date")), "2099-06-30")

	def test_FR_LIB_007_quyen_thay_the(self):
		a, b, _s = _pair()
		clin = make_user("tc_clin21@example.com", "NC Clinician")
		aud = make_user("tc_aud21@example.com", "NC Auditor")
		ctl = make_user("tc_ctl21@example.com", "NC Document Controller")
		for user in (clin, aud):
			frappe.set_user(user)
			with self.assertRaises(frappe.PermissionError):
				api.declare_supersession(a.name, b.name, "Toàn bộ", "2099-07-01")
		frappe.set_user(aud)
		self.assertEqual(api.get_supersessions(a.name)["supersedes"], [])
		frappe.set_user(ctl)
		api.declare_supersession(a.name, b.name, "Toàn bộ", "2099-07-01")
		res = api.get_supersessions(b.name)
		self.assertEqual(res["superseded_by"][0]["document"], a.name)
		self.assertEqual(res["superseded_by"][0]["scope"], "Toàn bộ")
		res = api.get_supersessions(a.name)
		self.assertEqual(res["supersedes"][0]["superseded_document"], b.name)
