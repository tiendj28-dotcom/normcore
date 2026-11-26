"""Tìm kiếm thư viện văn bản (FEAT-020: TC-LIB-08, FR-LIB-010).

InnoDB chỉ đưa dòng vào chỉ mục FULLTEXT khi commit: test commit dữ liệu và tự dọn ở tearDown
(technical-design mục 5), không dựa vào rollback của FrappeTestCase.
"""

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.api import library as api
from normcore.nc_library.doctype.nc_legal_document.library_fixtures import make_legal_document
from normcore.tests.utils import make_user

SERVICE_CODE = "DV-LIB-ECG"
SERVICE_NAME = "Đo điện tim"
HIS_CODE = "HIS-LIB-ECG"
NUMBER = "LIBTEST/QĐ-BYT"


class TestLibrarySearch(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls._clean()
		frappe.set_user("Administrator")
		spec = frappe.get_doc(
			{"doctype": "NC Specialty", "specialty_code": "CK-LIB", "specialty_name": "Chuyên khoa thử"}
		).insert(ignore_permissions=True)
		svc = frappe.get_doc(
			{
				"doctype": "NC Technical Service",
				"service_code": SERVICE_CODE,
				"service_name": SERVICE_NAME,
				"specialty": spec.name,
				"external_codes": [
					{"source_system": "HIS", "external_code": HIS_CODE, "external_name": "ECG"}
				],
			}
		).insert(ignore_permissions=True)
		cls.service = svc.name
		doc = make_legal_document(NUMBER, effective_date="2020-01-01")
		cls.doc = doc.name
		api.index_document(doc.name)  # đọc tệp mẫu 3 quy trình; trong test không tự commit
		# thêm một văn bản "Điều N" hết hiệu lực để thử bộ lọc
		cls.old = make_legal_document(
			"LIBTEST/CV-CU",
			effective_date="2000-01-01",
			expiry_date="2001-01-01",
			is_procedure_guideline=0,
			doc_type="Công văn",
		).name
		frappe.get_doc(
			{
				"doctype": "NC Legal Section",
				"legal_document": cls.old,
				"section_no": "Điều 1",
				"heading": "Phạm vi",
				"plain_text": "Siêu âm bụng tổng quát theo quy định cũ.",
			}
		).insert(ignore_permissions=True)
		api.refresh_validity()
		frappe.db.commit()

	@classmethod
	def tearDownClass(cls):
		cls._clean()
		super().tearDownClass()

	@classmethod
	def _clean(cls):
		frappe.set_user("Administrator")
		for d in frappe.get_all(
			"NC Legal Document", filters={"doc_number": ["like", "LIBTEST/%"]}, pluck="name"
		):
			frappe.db.delete("NC Legal Section", {"legal_document": d})
			frappe.db.delete("NC Legal Document", {"name": d})
		frappe.db.delete("NC Technical Service", {"service_code": SERVICE_CODE})
		frappe.db.delete("NC Service Code Map", {"external_code": HIS_CODE})
		frappe.db.delete("NC Specialty", {"specialty_code": "CK-LIB"})
		frappe.db.commit()

	def setUp(self):
		frappe.set_user("Administrator")

	def test_TC_LIB_08_tim_theo_cum_tu_va_ma_dich_vu(self):
		r = api.search_sections("siêu âm bụng tổng quát")
		self.assertEqual(r["mode"], "text")
		mine = [x for x in r["rows"] if x["doc_number"] == NUMBER]
		self.assertEqual([x["section_no"] for x in mine], ["2"])
		row = mine[0]
		self.assertEqual(row["page_from"], 3)
		self.assertEqual(row["validity_status"], "Còn hiệu lực")
		self.assertEqual(row["legal_document"], self.doc)
		self.assertEqual(row["match"], "Nội dung")
		self.assertIn("Siêu âm bụng", row["snippet"])
		# theo mã dịch vụ: tên dịch vụ trùng tiêu đề quy trình 1 (ASM-020-08)
		for code in (SERVICE_CODE, HIS_CODE.lower()):
			r = api.search_sections(code)
			self.assertEqual(r["mode"], "service")
			mine = [x for x in r["rows"] if x["doc_number"] == NUMBER]
			self.assertEqual([x["section_no"] for x in mine], ["1"], code)
			self.assertEqual(mine[0]["match"], "Tên dịch vụ")
			self.assertEqual(mine[0]["page_from"], 1)
			self.assertEqual(mine[0]["validity_status"], "Còn hiệu lực")

	def test_FR_LIB_010_tim_theo_so_hieu(self):
		r = api.search_sections("libtest / qđ-byt")
		self.assertEqual(r["mode"], "doc_number")
		self.assertEqual([x["section_no"] for x in r["rows"]], ["1", "2", "3"])
		self.assertEqual({x["match"] for x in r["rows"]}, {"Số hiệu"})

	def test_FR_LIB_010_cum_tu_phai_khop_lien_tiep(self):
		r = api.search_sections("bụng siêu âm", mode="text")
		self.assertEqual([x for x in r["rows"] if x["doc_number"].startswith("LIBTEST/")], [])

	def test_FR_LIB_010_loc_hieu_luc_va_loai(self):
		r = api.search_sections("siêu âm bụng", validity_status="Hết hiệu lực")
		self.assertEqual(
			{x["doc_number"] for x in r["rows"] if x["doc_number"].startswith("LIBTEST/")}, {"LIBTEST/CV-CU"}
		)
		r = api.search_sections("siêu âm bụng", doc_type="Quyết định")
		self.assertEqual(
			{x["doc_number"] for x in r["rows"] if x["doc_number"].startswith("LIBTEST/")}, {NUMBER}
		)

	def test_FR_LIB_010_sap_xep_con_hieu_luc_truoc(self):
		r = api.search_sections("siêu âm bụng")
		nums = [x["doc_number"] for x in r["rows"] if x["doc_number"].startswith("LIBTEST/")]
		self.assertEqual(nums, [NUMBER, "LIBTEST/CV-CU"])

	def test_FR_LIB_010_phan_trang(self):
		r = api.search_sections("libtest/qđ-byt", page_length=2)
		self.assertEqual((r["total"], len(r["rows"])), (3, 2))
		r = api.search_sections("libtest/qđ-byt", start=2, page_length=2)
		self.assertEqual([x["section_no"] for x in r["rows"]], ["3"])

	def test_FR_LIB_010_truy_van_tu_ngan_dung_nhanh_like(self):
		r = api.search_sections("ĐO", mode="text")
		self.assertIn(NUMBER, {x["doc_number"] for x in r["rows"]})

	def test_FR_LIB_010_truy_van_1_ky_tu_bi_tu_choi(self):
		self.assertRaisesRegex(frappe.ValidationError, "ít nhất 2 ký tự", api.search_sections, "a")
		self.assertRaisesRegex(frappe.ValidationError, "ít nhất 2 ký tự", api.search_sections, "   ")

	def test_FR_LIB_010_che_do_khong_hop_le(self):
		self.assertRaises(frappe.ValidationError, api.search_sections, "điện tim", mode="sql")

	def test_FR_LIB_010_khong_co_ket_qua(self):
		r = api.search_sections("cụm từ không tồn tại xyzzy")
		self.assertEqual((r["total"], r["rows"]), (0, []))

	def test_FR_LIB_010_ky_tu_dac_biet_khong_gay_loi_sql(self):
		r = api.search_sections('+điện -"tim" (*) ~@')
		self.assertIn("rows", r)

	def test_FR_ACC_002_nguoi_dung_khong_vai_tro_nc_bi_tu_choi(self):
		user = make_user("lib.search.norole@normcore.test")
		frappe.set_user(user)
		self.assertRaises(frappe.PermissionError, api.search_sections, "điện tim")

	def test_FR_ACC_007_auditor_tim_duoc(self):
		user = make_user("lib.search.auditor@normcore.test", "NC Auditor")
		frappe.set_user(user)
		r = api.search_sections("siêu âm bụng tổng quát")
		self.assertIn(NUMBER, {x["doc_number"] for x in r["rows"]})
