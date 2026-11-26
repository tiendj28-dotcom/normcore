"""NC Legal Document và NC Legal Section: lưu, trùng số hiệu, quyền (FEAT-020)."""

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.nc_library.doctype.nc_legal_document.library_fixtures import (
	legal_values,
	make_legal_document,
	make_legal_file,
	read_sample,
)
from normcore.nc_library.doctype.nc_legal_document.nc_legal_document import DuplicateDocNumberError
from normcore.tests.utils import make_user


def _section(doc, no="1", text="Nội dung mục"):
	return frappe.get_doc(
		{
			"doctype": "NC Legal Section",
			"legal_document": doc.name,
			"section_no": no,
			"heading": "TIÊU ĐỀ",
			"plain_text": text,
		}
	)


class TestNCLegalDocument(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_FR_LIB_001_tao_ban_ghi_chua_lap_va_tinh_hieu_luc(self):
		doc = make_legal_document(effective_date="2020-01-01")
		self.assertEqual(doc.index_status, "Chưa lập")
		self.assertEqual(doc.validity_status, "Còn hiệu lực")
		self.assertTrue(doc.name.startswith("LD-"))

	def test_FR_LIB_001_thieu_truong_bat_buoc_bi_tu_choi(self):
		values = legal_values()
		del values["issuer"]
		self.assertRaises(frappe.MandatoryError, frappe.get_doc(values).insert)

	def test_TC_LIB_02_trung_so_hieu(self):
		old = make_legal_document("123/QĐ-BYT")
		for variant in ("123/qđ-byt", "123 / QĐ-BYT"):
			with self.assertRaises(DuplicateDocNumberError) as cm:
				make_legal_document(variant, file_url=make_legal_file("khac.pdf"))
			self.assertIn(old.name, str(cm.exception))

	def test_FR_LIB_002_sua_chinh_minh_khong_bi_coi_la_trung(self):
		doc = make_legal_document("55/QĐ-BYT")
		doc.title = "Tên mới"
		doc.save()
		self.assertEqual(doc.title, "Tên mới")

	def test_FR_LIB_001_tep_sai_duoi_bi_tu_choi(self):
		url = make_legal_file("bang.xlsx", b"x")
		self.assertRaisesRegex(
			frappe.ValidationError, "PDF hoặc DOCX", make_legal_document, "9/A", file_url=url
		)

	def test_FR_LIB_001_tep_public_bi_tu_choi(self):
		f = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": "cong-khai.pdf",
				"is_private": 0,
				"content": read_sample("qtkt_3_quy_trinh.pdf"),
			}
		).insert(ignore_permissions=True)
		self.assertRaisesRegex(
			frappe.ValidationError, "riêng tư", make_legal_document, "9/B", file_url=f.file_url
		)

	def test_FR_LIB_001_tep_qua_100mb_bi_tu_choi(self):
		url = make_legal_file("lon.pdf")
		frappe.db.set_value("File", {"file_url": url}, "file_size", 100 * 1024 * 1024 + 1)
		self.assertRaisesRegex(frappe.ValidationError, "100 MB", make_legal_document, "9/C", file_url=url)

	def test_FR_LIB_001_ngay_het_hieu_luc_truoc_ngay_hieu_luc_bi_tu_choi(self):
		self.assertRaisesRegex(
			frappe.ValidationError, "Ngày hết hiệu lực", make_legal_document, "9/D", expiry_date="2025-01-01"
		)

	def test_FR_LIB_006_hieu_luc_theo_ngay_khi_luu(self):
		self.assertEqual(
			make_legal_document("9/E", effective_date="2999-01-01").validity_status, "Chưa hiệu lực"
		)
		self.assertEqual(
			make_legal_document("9/F", effective_date="2000-01-01", expiry_date="2001-01-01").validity_status,
			"Hết hiệu lực",
		)

	def test_FR_LIB_003_doi_tep_dat_lai_chua_lap(self):
		doc = make_legal_document("9/G")
		frappe.db.set_value("NC Legal Document", doc.name, {"index_status": "Đã lập"})
		doc.reload()
		doc.file = make_legal_file("tep-moi.pdf", read_sample("khong_lop_van_ban.pdf"))
		doc.save()
		self.assertEqual(doc.index_status, "Chưa lập")

	def test_FR_LIB_003_doi_tieu_de_khong_dat_lai_chi_muc(self):
		doc = make_legal_document("9/H")
		frappe.db.set_value("NC Legal Document", doc.name, {"index_status": "Đã lập"})
		doc.reload()
		doc.title = "Đổi tên"
		doc.save()
		self.assertEqual(doc.index_status, "Đã lập")

	# ---- NC Legal Section ----

	def test_FR_LIB_003_muc_trung_so_muc_bi_tu_choi_va_ke_thua_hieu_luc(self):
		doc = make_legal_document("9/I", effective_date="2999-01-01")
		s = _section(doc).insert(ignore_permissions=True)
		self.assertEqual(s.validity_status, "Chưa hiệu lực")
		self.assertRaisesRegex(frappe.ValidationError, "đã có", _section(doc).insert, ignore_permissions=True)

	def test_FR_LIB_003_muc_van_ban_thuan_khong_duoc_rong(self):
		doc = make_legal_document("9/J")
		self.assertRaises(frappe.ValidationError, _section(doc, text="  ").insert, ignore_permissions=True)

	def test_FR_LIB_003_cap_nhat_hieu_luc_muc_khi_doi_ngay_van_ban(self):
		doc = make_legal_document("9/K", effective_date="2999-01-01")
		s = _section(doc).insert(ignore_permissions=True)
		doc.effective_date = "2000-01-01"
		doc.save()
		self.assertEqual(frappe.db.get_value("NC Legal Section", s.name, "validity_status"), "Còn hiệu lực")

	def test_FR_LIB_010_co_chi_muc_fulltext(self):
		rows = frappe.db.sql(
			"SHOW INDEX FROM `tabNC Legal Section` WHERE Key_name = 'nc_section_ft'", as_dict=True
		)
		self.assertEqual({r.Column_name for r in rows}, {"heading", "plain_text"})
		self.assertEqual({r.Index_type for r in rows}, {"FULLTEXT"})

	# ---- quyền ----

	def test_FR_ACC_002_quyen_ghi_cua_doc_controller_va_admin(self):
		users = [
			make_user(f"ld.w{i}@normcore.test", r)
			for i, r in enumerate(("NC Document Controller", "NC Admin"))
		]
		for role, user in zip(("NC Document Controller", "NC Admin"), users, strict=True):
			frappe.set_user(user)
			for dt in ("NC Legal Document", "NC Legal Section"):
				self.assertTrue(frappe.has_permission(dt, "write"), (role, dt))
				self.assertTrue(frappe.has_permission(dt, "create"), (role, dt))
				self.assertFalse(frappe.has_permission(dt, "delete"), (role, dt))
		frappe.set_user("Administrator")
		file_url = make_legal_file("dc.pdf")
		frappe.set_user(users[0])
		doc = frappe.get_doc(legal_values("9/L", file_url)).insert()
		self.assertEqual(doc.owner, "ld.w0@normcore.test")

	def test_FR_ACC_002_vai_tro_chi_doc_khong_ghi(self):
		roles = ("NC Finance", "NC Clinician", "NC Director")
		users = [make_user(f"ld.ro{i}@normcore.test", r) for i, r in enumerate(roles)]
		for role, user in zip(roles, users, strict=True):
			frappe.set_user(user)
			for dt in ("NC Legal Document", "NC Legal Section"):
				self.assertTrue(frappe.has_permission(dt, "read"), (role, dt))
				self.assertFalse(frappe.has_permission(dt, "create"), (role, dt))
				self.assertFalse(frappe.has_permission(dt, "write"), (role, dt))

	def test_FR_ACC_007_auditor_chi_doc(self):
		user = make_user("ld.auditor@normcore.test", "NC Auditor")
		values = legal_values("9/M")
		frappe.set_user(user)
		for dt in ("NC Legal Document", "NC Legal Section"):
			self.assertTrue(frappe.has_permission(dt, "read"))
			for ptype in ("create", "write", "delete"):
				self.assertFalse(frappe.has_permission(dt, ptype), (dt, ptype))
		self.assertRaises(frappe.PermissionError, frappe.get_doc(values).insert)

	def test_FR_ACC_002_nguoi_dung_khong_vai_tro_nc_khong_doc(self):
		user = make_user("ld.noroles@normcore.test")
		frappe.set_user(user)
		for dt in ("NC Legal Document", "NC Legal Section"):
			self.assertFalse(frappe.has_permission(dt, "read"), dt)
