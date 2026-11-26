"""Ánh xạ hướng dẫn với dịch vụ (FEAT-022: TC-SVC-02, FR-SVC-005..007).

Không gọi nhà cung cấp AI thật: gateway dùng provider giả lập ghi lại nguồn.
"""

from unittest import mock

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.api import library as api
from normcore.library.extract import Page
from normcore.nc_library.doctype.nc_legal_document.library_fixtures import (
	make_legal_document,
	make_legal_file,
	read_sample,
)
from normcore.tests.utils import make_user

CODE_SVC = "01.0099"  # mã dịch vụ xuất hiện trong tiêu đề mục 1
NAME_SVC = "NAME-SIEU-AM"
OTHER_SVC = "KHONG-LIEN-QUAN"

TEXT = (
	"Phần mở đầu của hướng dẫn.\n"
	f"1. QUY TRÌNH {CODE_SVC} KIỂM TRA MẪU\nNội dung quy trình một.\n"
	"2. SIÊU ÂM BỤNG MẪU\nNội dung quy trình hai.\n"
	"3. QUY TRÌNH KHÁC HẲN\nNội dung quy trình ba.\n"
)


def make_service(code, name):
	if not frappe.db.exists("NC Technical Service", code):
		frappe.get_doc(
			{"doctype": "NC Technical Service", "service_code": code, "service_name": name, "is_active": 1}
		).insert(ignore_permissions=True)
	return code


def index_with_text(doc, text=TEXT):
	with mock.patch("normcore.api.library.available_ocr", return_value=None), mock.patch(
		"normcore.api.library.extract_pages", return_value=[Page(1, text)]
	):
		api.index_document(doc.name)
	doc.reload()


def section_by_no(doc, no):
	return frappe.get_doc(
		"NC Legal Section", frappe.db.get_value("NC Legal Section", {"legal_document": doc.name, "section_no": no})
	)


class MappingTestBase(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.code_svc = make_service(CODE_SVC, "Dịch vụ kiểm tra mẫu")
		self.name_svc = make_service(NAME_SVC, "Siêu âm bụng mẫu")
		self.other_svc = make_service(OTHER_SVC, "Thứ gì đó không liên quan")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def make_doc(self, number="MAP/01", **kw):
		doc = make_legal_document(number, effective_date="2020-01-01", **kw)
		index_with_text(doc)
		return doc


class TestLibraryMappingSuggest(MappingTestBase):
	def test_FR_SVC_005_de_xuat_sau_lap_chi_muc(self):
		doc = self.make_doc()
		self.assertEqual(doc.index_status, "Đã lập")
		s1, s2, s0 = section_by_no(doc, "1"), section_by_no(doc, "2"), section_by_no(doc, "0")
		self.assertEqual(
			[(r.technical_service, r.confidence, r.mapping_status) for r in s1.service_mappings],
			[(CODE_SVC, 100, "Đề xuất")],
		)
		self.assertEqual(
			[(r.technical_service, r.confidence, r.mapping_status) for r in s2.service_mappings],
			[(NAME_SVC, 95, "Đề xuất")],
		)
		self.assertEqual(len(s0.service_mappings), 0)

	def test_FR_SVC_005_van_ban_khong_phai_huong_dan_khong_co_de_xuat(self):
		doc = make_legal_document("MAP/02", effective_date="2020-01-01", is_procedure_guideline=0)
		index_with_text(doc, "Điều 1. Siêu âm bụng mẫu\nNội dung.")
		rows = frappe.db.sql(
			"SELECT m.name FROM `tabNC Section Service Map` m JOIN `tabNC Legal Section` s ON s.name = m.parent "
			"WHERE s.legal_document = %s",
			doc.name,
		)
		self.assertEqual(rows, ())
		self.assertEqual(api.refresh_suggestions(doc.name), {"sections": 0, "suggested": 0})

	def test_FR_SVC_005_loi_de_xuat_khong_lam_van_ban_loi(self):
		doc = make_legal_document("MAP/03", effective_date="2020-01-01")
		with mock.patch("normcore.api.library.refresh_suggestions", side_effect=RuntimeError("boom")):
			index_with_text(doc)
		self.assertEqual(doc.index_status, "Đã lập")
		self.assertEqual(len(section_by_no(doc, "1").service_mappings), 0)

	def test_FR_SVC_005_lap_lai_giu_da_xac_nhan(self):
		doc = self.make_doc("MAP/04")
		s1 = section_by_no(doc, "1")
		s1.service_mappings[0].mapping_status = "Đã xác nhận"
		s1.save()
		old = section_by_no(doc, "1").service_mappings[0]
		old_by, old_on, old_name = old.confirmed_by, old.confirmed_on, old.name
		self.assertTrue(old_by)
		index_with_text(doc)  # lập lại
		rows = section_by_no(doc, "1").service_mappings
		self.assertEqual([(r.technical_service, r.mapping_status) for r in rows], [(CODE_SVC, "Đã xác nhận")])
		self.assertEqual((rows[0].confirmed_by, rows[0].confirmed_on, rows[0].name), (old_by, old_on, old_name))
		# dòng "Đề xuất" cũ của mục 2 được tính lại, không nhân đôi
		self.assertEqual(len(section_by_no(doc, "2").service_mappings), 1)

	def test_FR_SVC_005_de_xuat_lai_va_quyen(self):
		doc = self.make_doc("MAP/05")
		out = api.suggest_mappings(doc.name)
		self.assertEqual(out["suggested"], 2)
		doc.db_set("index_status", "Chưa lập")
		with self.assertRaises(frappe.ValidationError):
			api.suggest_mappings(doc.name)
		doc.db_set("index_status", "Đã lập")
		doc.db_set("is_procedure_guideline", 0)
		with self.assertRaises(frappe.ValidationError):
			api.suggest_mappings(doc.name)

	def test_SCR_DSK_004_loc_chua_xac_nhan(self):
		doc = self.make_doc("MAP/07")
		s1 = section_by_no(doc, "1")
		s1.service_mappings[0].mapping_status = "Đã xác nhận"
		s1.save()
		allr = api.get_mappings(doc.name)
		self.assertEqual([r["section_no"] for r in allr["rows"]], ["1", "2", "3"])  # bỏ mục "0"
		self.assertEqual(allr["total"], 3)
		self.assertEqual(allr["pending_exact"], 0)
		row1 = allr["rows"][0]["mappings"][0]
		self.assertEqual(row1["service_name"], "Dịch vụ kiểm tra mẫu")
		self.assertEqual(row1["mapping_status"], "Đã xác nhận")
		unconf = api.get_mappings(doc.name, unconfirmed_only=1)
		# mục 1 đã xác nhận hết; mục 2 có đề xuất; mục 3 chưa có dòng
		self.assertEqual([r["section_no"] for r in unconf["rows"]], ["2", "3"])

	def test_SCR_DSK_004_pending_exact(self):
		doc = self.make_doc("MAP/08")
		self.assertEqual(api.get_mappings(doc.name)["pending_exact"], 1)


class TestLibraryMappingConfirm(MappingTestBase):
	def test_FR_SVC_006_xac_nhan_luu_nguoi_va_thoi_diem(self):
		dc = make_user("map.dc2@normcore.test", "NC Document Controller")
		doc = self.make_doc("MAP/10")
		s1, s2 = section_by_no(doc, "1"), section_by_no(doc, "2")
		frappe.set_user(dc)
		out = api.confirm_mappings(doc.name, frappe.as_json([s2.service_mappings[0].name]))
		self.assertEqual(out, {"confirmed": 1})
		r = section_by_no(doc, "2").service_mappings[0]
		self.assertEqual((r.mapping_status, r.confirmed_by), ("Đã xác nhận", dc))
		self.assertTrue(r.confirmed_on)
		stamp = (r.confirmed_by, r.confirmed_on)
		# xác nhận lại: bỏ qua, không đóng dấu lại
		self.assertEqual(api.confirm_mappings(doc.name, [r.name]), {"confirmed": 0})
		r = section_by_no(doc, "2").service_mappings[0]
		self.assertEqual((r.confirmed_by, r.confirmed_on), stamp)
		# xác nhận mọi dòng 100%
		self.assertEqual(api.confirm_exact(doc.name), {"confirmed": 1})
		self.assertEqual(section_by_no(doc, "1").service_mappings[0].mapping_status, "Đã xác nhận")
		self.assertEqual(api.confirm_exact(doc.name), {"confirmed": 0})
		# thêm tay (UC-003 5a) và sửa dịch vụ của dòng
		out = api.save_mapping(s1.name, self.other_svc)
		self.assertEqual(out["mapping_status"], "Đã xác nhận")
		added = frappe.get_doc("NC Section Service Map", out["row"])
		self.assertEqual((added.technical_service, added.confirmed_by), (self.other_svc, dc))
		self.assertFalse(added.confidence)
		row2 = section_by_no(doc, "3")
		row2.append("service_mappings", {"technical_service": self.name_svc})
		row2.save()
		rname = section_by_no(doc, "3").service_mappings[0].name
		out = api.save_mapping(row2.name, self.other_svc, row=rname)
		self.assertEqual(out["row"], rname)
		edited = section_by_no(doc, "3").service_mappings[0]
		self.assertEqual((edited.technical_service, edited.mapping_status), (self.other_svc, "Đã xác nhận"))
		# trùng dịch vụ trong mục
		with self.assertRaises(frappe.ValidationError):
			api.save_mapping(s1.name, self.other_svc)
		# dịch vụ không tồn tại
		with self.assertRaises(frappe.DoesNotExistError):
			api.save_mapping(s1.name, "KHONG-TON-TAI")
		# bỏ ánh xạ
		self.assertEqual(api.remove_mapping(rname), {"removed": 1})
		self.assertEqual(len(section_by_no(doc, "3").service_mappings), 0)

	def test_FR_SVC_006_dong_khong_thuoc_van_ban(self):
		doc, other = self.make_doc("MAP/11"), self.make_doc("MAP/12")
		row = section_by_no(other, "1").service_mappings[0].name
		with self.assertRaises(frappe.ValidationError):
			api.confirm_mappings(doc.name, [row])

	def test_FR_SVC_006_quyen_anh_xa(self):
		doc = self.make_doc("MAP/13")
		s1 = section_by_no(doc, "1")
		row = s1.service_mappings[0].name
		writers = (
			lambda: api.confirm_mappings(doc.name, [row]),
			lambda: api.confirm_exact(doc.name),
			lambda: api.save_mapping(s1.name, self.other_svc),
			lambda: api.remove_mapping(row),
			lambda: api.suggest_mappings(doc.name),
		)
		users = {
			"map.aud@normcore.test": make_user("map.aud@normcore.test", "NC Auditor"),
			"map.cli@normcore.test": make_user("map.cli@normcore.test", "NC Clinician"),
			"map.norole@normcore.test": make_user("map.norole@normcore.test"),
			"map.dc3@normcore.test": make_user("map.dc3@normcore.test", "NC Document Controller"),
		}
		for email in ("map.aud@normcore.test", "map.cli@normcore.test"):
			frappe.set_user(users[email])
			for call in writers:
				with self.assertRaises(frappe.PermissionError):
					call()
		frappe.set_user("map.aud@normcore.test")
		self.assertEqual(api.get_mappings(doc.name)["total"], 3)  # Auditor đọc được
		frappe.set_user(users["map.norole@normcore.test"])
		with self.assertRaises(frappe.PermissionError):
			api.get_mappings(doc.name)
		frappe.set_user(users["map.dc3@normcore.test"])
		self.assertEqual(api.confirm_exact(doc.name), {"confirmed": 1})
		self.assertEqual(api.suggest_mappings(doc.name)["sections"], 3)
		self.assertEqual(api.remove_mapping(row), {"removed": 1})
