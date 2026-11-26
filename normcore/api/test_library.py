"""Lập chỉ mục, mục, nguồn trang gốc (FEAT-020: TC-LIB-01, TC-LIB-03, FR-LIB-004, 005, 011, 012)."""

from unittest import mock

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.api import library as api
from normcore.library.extract import Page
from normcore.nc_library.doctype.nc_legal_document.library_fixtures import (
	make_corrupt_file,
	make_legal_document,
	make_legal_file,
	read_sample,
)
from normcore.tests.utils import make_user


def _sections(doc):
	return frappe.get_all(
		"NC Legal Section",
		filters={"legal_document": doc.name},
		fields=["name", "section_no", "heading", "page_from", "page_to", "plain_text", "validity_status"],
		order_by="section_no asc",
	)


class TestLibraryIndex(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_TC_LIB_01_nap_pdf_tach_3_muc(self):
		doc = make_legal_document("QTKT/01")
		self.assertEqual(doc.index_status, "Chưa lập")
		api.index_document(doc.name)
		doc.reload()
		self.assertEqual(doc.index_status, "Đã lập")
		self.assertFalse(doc.index_error)
		rows = _sections(doc)
		self.assertEqual([r.section_no for r in rows], ["1", "2", "3"])
		self.assertEqual([r.heading for r in rows], ["ĐO ĐIỆN TIM", "SIÊU ÂM BỤNG", "NỘI SOI DẠ DÀY"])
		self.assertEqual([(r.page_from, r.page_to) for r in rows], [(1, 2), (3, 3), (4, 4)])
		self.assertIn("Đo điện tim là kỹ thuật ghi hoạt động điện của tim.", rows[0].plain_text)
		self.assertEqual({r.validity_status for r in rows}, {"Còn hiệu lực"})

	def test_TC_LIB_03_tep_hong_bao_loi(self):
		user = make_user("lib.uploader@normcore.test", "NC Document Controller")
		doc = make_legal_document("QTKT/03", file_url=make_corrupt_file())
		api.index_document(doc.name, notify_user=user)
		doc.reload()
		self.assertEqual(doc.index_status, "Lỗi")
		self.assertIn("Không đọc được tệp", doc.index_error)
		self.assertEqual(_sections(doc), [])
		note = frappe.get_all(
			"Notification Log",
			filters={"for_user": user, "document_type": "NC Legal Document", "document_name": doc.name},
			fields=["subject", "type"],
		)
		self.assertEqual(len(note), 1)
		self.assertIn("QTKT/03", note[0].subject)
		self.assertIn("thất bại", note[0].subject)

	def test_FR_LIB_005_loi_la_ghi_loi_he_thong_va_van_bao_loi(self):
		doc = make_legal_document("QTKT/05")
		with mock.patch("normcore.api.library.split_sections", side_effect=RuntimeError("boom")):
			api.index_document(doc.name)
		doc.reload()
		self.assertEqual(doc.index_status, "Lỗi")
		self.assertEqual(doc.index_error, "Lỗi hệ thống khi lập chỉ mục")

	def test_FR_LIB_005_loi_giua_chung_khong_de_lai_muc_do_dang(self):
		doc = make_legal_document("QTKT/06")
		api.index_document(doc.name)
		with mock.patch("normcore.api.library._write_sections", side_effect=RuntimeError("giữa chừng")):
			api.index_document(doc.name)
		doc.reload()
		self.assertEqual(doc.index_status, "Lỗi")
		self.assertEqual(len(_sections(doc)), 3)

	def test_FR_LIB_004_pdf_khong_lop_van_ban_khong_ocr_bao_loi(self):
		url = make_legal_file("trang.pdf", read_sample("khong_lop_van_ban.pdf"))
		doc = make_legal_document("QTKT/07", file_url=url)
		with mock.patch("normcore.api.library.available_ocr", return_value=None):
			api.index_document(doc.name)
		doc.reload()
		self.assertEqual(doc.index_status, "Lỗi")
		self.assertIn("không có lớp văn bản", doc.index_error)

	def test_FR_LIB_004_ocr_gia_tra_van_ban_thi_tach_muc_binh_thuong(self):
		url = make_legal_file("trang2.pdf", read_sample("khong_lop_van_ban.pdf"))
		doc = make_legal_document("QTKT/08", file_url=url)
		text = "1. QUY TRÌNH NHẬN DẠNG\nNội dung nhận dạng được từ ảnh quét của trang."
		with mock.patch("normcore.api.library.available_ocr", return_value=lambda c: [Page(1, text)]):
			api.index_document(doc.name)
		doc.reload()
		self.assertEqual(doc.index_status, "Đã lập")
		self.assertEqual([r.heading for r in _sections(doc)], ["QUY TRÌNH NHẬN DẠNG"])

	def test_FR_LIB_003_docx_lap_duoc_muc_khong_co_trang(self):
		url = make_legal_file("mau.docx", read_sample("qtkt_mau.docx"))
		doc = make_legal_document("QTKT/09", file_url=url, is_procedure_guideline=0)
		api.index_document(doc.name)
		doc.reload()
		self.assertEqual(doc.index_status, "Đã lập")
		rows = _sections(doc)
		self.assertEqual(len(rows), 1)
		self.assertIsNone(rows[0].page_from or None)
		self.assertEqual(rows[0].heading, "QUY TRÌNH KỸ THUẬT MẪU")

	def test_FR_LIB_003_lap_lai_giu_ten_muc_va_go_muc_cu(self):
		doc = make_legal_document("QTKT/10")
		api.index_document(doc.name)
		first = {r.section_no: r.name for r in _sections(doc)}
		frappe.get_doc(
			{
				"doctype": "NC Legal Section",
				"legal_document": doc.name,
				"section_no": "99",
				"plain_text": "mục thừa",
			}
		).insert(ignore_permissions=True)
		api.index_document(doc.name)
		again = {r.section_no: r.name for r in _sections(doc)}
		self.assertEqual(again, first)

	def test_FR_LIB_003_lap_lai_giu_han_rieng_cua_muc(self):
		doc = make_legal_document("QTKT/11")
		api.index_document(doc.name)
		s = frappe.get_doc("NC Legal Section", {"legal_document": doc.name, "section_no": "2"})
		s.expiry_date = "2000-01-01"
		s.save(ignore_permissions=True)
		api.index_document(doc.name)
		self.assertEqual(str(frappe.db.get_value("NC Legal Section", s.name, "expiry_date")), "2000-01-01")
		self.assertEqual(frappe.db.get_value("NC Legal Section", s.name, "validity_status"), "Hết hiệu lực")

	def test_FR_LIB_003_van_ban_khong_ton_tai_thi_bo_qua(self):
		self.assertIsNone(api.index_document("LD-KHONG-CO"))

	# ---- reindex ----

	def test_FR_LIB_003_reindex_dat_chua_lap_va_xep_tac_vu(self):
		user = make_user("lib.dc@normcore.test", "NC Document Controller")
		doc = make_legal_document("QTKT/12")
		api.index_document(doc.name)
		frappe.set_user(user)
		with mock.patch("normcore.api.library.enqueue_index") as enq:
			out = api.reindex(doc.name)
		self.assertEqual(out, {"index_status": "Chưa lập"})
		self.assertEqual(frappe.db.get_value("NC Legal Document", doc.name, "index_status"), "Chưa lập")
		enq.assert_called_once_with(doc.name, user)

	def test_FR_ACC_007_reindex_cua_auditor_bi_tu_choi(self):
		user = make_user("lib.auditor@normcore.test", "NC Auditor")
		doc = make_legal_document("QTKT/13")
		frappe.set_user(user)
		self.assertRaises(frappe.PermissionError, api.reindex, doc.name)

	def test_FR_LIB_003_reindex_khi_dang_lap_bi_tu_choi(self):
		doc = make_legal_document("QTKT/14")
		frappe.db.set_value("NC Legal Document", doc.name, "index_status", "Đang lập")
		self.assertRaisesRegex(frappe.ValidationError, "đang được lập chỉ mục", api.reindex, doc.name)

	# ---- FR-LIB-012 ----

	def test_FR_LIB_012_sua_van_ban_thuan_luu_ban_truoc(self):
		doc = make_legal_document("QTKT/15")
		api.index_document(doc.name)
		s = frappe.get_doc("NC Legal Section", {"legal_document": doc.name, "section_no": "1"})
		old = s.plain_text
		editor = make_user("lib.editor@normcore.test", "NC Document Controller")
		frappe.set_user(editor)
		s = frappe.get_doc("NC Legal Section", s.name)
		s.plain_text = old + "\nĐã sửa lỗi nhận dạng."
		s.save(ignore_version=False)  # Frappe bỏ qua Version khi chạy test nếu không bật rõ
		frappe.set_user("Administrator")
		ver = frappe.get_all(
			"Version",
			filters={"ref_doctype": "NC Legal Section", "docname": s.name},
			fields=["data", "owner", "creation"],
		)
		self.assertEqual(len(ver), 1)
		self.assertEqual(ver[0].owner, editor)
		self.assertIsNotNone(ver[0].creation)
		changed = frappe.parse_json(ver[0].data)["changed"]
		before = next(c for c in changed if c[0] == "plain_text")[1]
		self.assertEqual(before.replace("<br>", "\n"), old)  # Version lưu xuống dòng dạng <br>

	# ---- đọc ----

	def test_FR_LIB_003_get_sections_theo_thu_tu_tu_nhien(self):
		doc = make_legal_document("QTKT/16")
		for no in ("10", "2", "1"):
			frappe.get_doc(
				{
					"doctype": "NC Legal Section",
					"legal_document": doc.name,
					"section_no": no,
					"plain_text": "x",
				}
			).insert(ignore_permissions=True)
		out = api.get_sections(doc.name)
		self.assertEqual(out["total"], 3)
		self.assertEqual([r["section_no"] for r in out["rows"]], ["1", "2", "10"])
		page = api.get_sections(doc.name, start=1, page_length=1)
		self.assertEqual([r["section_no"] for r in page["rows"]], ["2"])

	def test_FR_LIB_003_get_sections_can_quyen_doc(self):
		doc = make_legal_document("QTKT/17")
		user = make_user("lib.norole@normcore.test")
		frappe.set_user(user)
		self.assertRaises(frappe.PermissionError, api.get_sections, doc.name)

	def test_FR_LIB_011_get_source_view_tra_tep_va_trang(self):
		doc = make_legal_document("QTKT/18")
		api.index_document(doc.name)
		sec = frappe.db.get_value("NC Legal Section", {"legal_document": doc.name, "section_no": "2"})
		out = api.get_source_view(sec)
		self.assertEqual(out["file_url"], doc.file)
		self.assertEqual(out["file_kind"], "pdf")
		self.assertEqual((out["page_from"], out["page_to"]), (3, 3))
		self.assertEqual((out["doc_number"], out["section_no"]), ("QTKT/18", "2"))

	def test_FR_LIB_011_get_source_view_docx_khong_co_trang(self):
		url = make_legal_file("mau2.docx", read_sample("qtkt_mau.docx"))
		doc = make_legal_document("QTKT/19", file_url=url, is_procedure_guideline=0)
		api.index_document(doc.name)
		sec = frappe.db.get_value("NC Legal Section", {"legal_document": doc.name})
		out = api.get_source_view(sec)
		self.assertEqual(out["file_kind"], "docx")
		self.assertIsNone(out["page_from"])

	def test_FR_LIB_011_get_source_view_can_quyen_doc(self):
		doc = make_legal_document("QTKT/20")
		api.index_document(doc.name)
		sec = frappe.db.get_value("NC Legal Section", {"legal_document": doc.name}, "name")
		frappe.set_user(make_user("lib.norole2@normcore.test"))
		self.assertRaises(frappe.PermissionError, api.get_source_view, sec)

	def test_FR_LIB_003_dat_hang_doi_sau_commit(self):
		with mock.patch("normcore.api.library.frappe.enqueue") as enq:
			api.enqueue_index("LD-00001", "a@b.c")
		kw = enq.call_args.kwargs
		self.assertEqual(kw["queue"], "long")
		self.assertTrue(kw["enqueue_after_commit"])
		self.assertEqual(kw["notify_user"], "a@b.c")
