"""NORM-65 (ASM-046): patch chuyển legal_document, legal_section từ Data sang Link."""

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.nc_library.doctype.nc_legal_document.library_fixtures import make_legal_document
from normcore.nc_library.doctype.nc_section_service_map.test_nc_section_service_map import make_section
from normcore.patches import link_procedure_citation_legal
from normcore.tests.utils import make_base, make_procedure


class TestCitationLinkPatch(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		service, dept, _job = make_base()
		self.proc = make_procedure(service, dept)
		self.ld = make_legal_document("43/2013/TT-BYT")
		self.ls = make_section(self.ld, "5").name

	def tearDown(self):
		frappe.db.rollback()

	def _legacy_rows(self, *rows):
		"""Dòng như trước khi đổi kiểu: giá trị Data tự do, ghi thẳng CSDL sau khi lưu cha (lưu lại sẽ xóa giá trị)."""
		for _doc, _sec, quote in rows:
			self.proc.append(
				"citations", {"target_step_id": "S001", "relation": "Chưa có căn cứ", "quote": quote}
			)
		self.proc.save()
		names = [c.name for c in self.proc.citations]
		for name, (document, section, _quote) in zip(names, rows, strict=True):
			frappe.db.set_value(
				"NC Procedure Citation", name, {"legal_document": document, "legal_section": section}
			)
		return names

	def _row(self, name):
		return frappe.db.get_value(
			"NC Procedure Citation", name, ["legal_document", "legal_section", "quote"], as_dict=True
		)

	def test_patch_khop_duoc_doi_sang_ten_ban_ghi(self):
		by_text, by_name = self._legacy_rows(
			("Thông tư 43/2013/TT-BYT", "Điều 5", "đoạn trích"), (self.ld.name, self.ls, "đoạn trích")
		)
		link_procedure_citation_legal.execute()
		for name in (by_text, by_name):
			r = self._row(name)
			self.assertEqual(
				(r.legal_document, r.legal_section, r.quote), (self.ld.name, self.ls, "đoạn trích")
			)

	def test_patch_khong_khop_khong_mat_gia_tri(self):
		both, only_section = self._legacy_rows(
			("Thông tư 99/2020/TT-BYT", "Điều 5", "đoạn trích"), ("43/2013/TT-BYT", "Phụ lục A", None)
		)
		link_procedure_citation_legal.execute()
		r = self._row(both)
		self.assertEqual((r.legal_document, r.legal_section), (None, None))
		self.assertEqual(r.quote, "[Căn cứ cũ: Thông tư 99/2020/TT-BYT — Điều 5] đoạn trích")
		r = self._row(only_section)
		self.assertEqual((r.legal_document, r.legal_section), (self.ld.name, None))
		self.assertEqual(r.quote, "[Căn cứ cũ: Phụ lục A]")

	def test_patch_chay_lai_khong_doi_gi(self):
		(name,) = self._legacy_rows(("Thông tư 99/2020/TT-BYT", "Điều 5", "đoạn trích"))
		link_procedure_citation_legal.execute()
		first = self._row(name)
		link_procedure_citation_legal.execute()
		self.assertEqual(self._row(name), first)
