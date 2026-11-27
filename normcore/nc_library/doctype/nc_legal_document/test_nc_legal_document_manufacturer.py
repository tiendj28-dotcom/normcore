"""FEAT-038: tài liệu của hãng (FR-LIB-013)."""

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.nc_library.doctype.nc_legal_document.library_fixtures import legal_values
from normcore.tests.cls_norm_ai_fixtures import make_glu_a


class TestManufacturerDocument(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		make_glu_a()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _values(self, rows, **kw):
		return legal_values(
			"HG-GLU-2.0",
			doc_type="Tài liệu của hãng",
			is_procedure_guideline=0,
			related_resources=rows,
			**kw,
		)

	def test_FR_LIB_013_tai_lieu_hang_phai_gan(self):
		with self.assertRaisesRegex(frappe.ValidationError, "phải gắn ít nhất một mặt hàng"):
			frappe.get_doc(self._values([])).insert(ignore_permissions=True)
		doc = frappe.get_doc(
			self._values([{"linked_doctype": "NC Item", "linked_name": "HC_GLU"}])
		).insert(ignore_permissions=True)
		self.assertEqual(doc.doc_type, "Tài liệu của hãng")
		self.assertEqual(doc.index_status, "Chưa lập")
		self.assertEqual(doc.related_resources[0].linked_name, "HC_GLU")
		# tách mục như văn bản khác: có thể đặt thủ công mục cho tài liệu của hãng
		sec = frappe.get_doc(
			{
				"doctype": "NC Legal Section",
				"legal_document": doc.name,
				"section_no": "1",
				"heading": "TH",
				"plain_text": "Nội dung",
			}
		).insert(ignore_permissions=True)
		self.assertEqual(sec.legal_document, doc.name)

	def test_FR_LIB_013_loai_va_trung(self):
		with self.assertRaisesRegex(frappe.ValidationError, "Chỉ gắn được mặt hàng hoặc thiết bị"):
			frappe.get_doc(
				self._values([{"linked_doctype": "NC Technical Service", "linked_name": "GLU"}])
			).insert(ignore_permissions=True)
		row = {"linked_doctype": "NC Equipment", "linked_name": "EQ_A"}
		with self.assertRaisesRegex(frappe.ValidationError, "trùng với dòng 1"):
			frappe.get_doc(self._values([row, dict(row)])).insert(ignore_permissions=True)

	def test_FR_LIB_013_loai_khac_giu_bang_khong_loi(self):
		values = legal_values("TT-1/2026", related_resources=[{"linked_doctype": "NC Item", "linked_name": "HC_GLU"}])
		doc = frappe.get_doc(values).insert(ignore_permissions=True)
		self.assertEqual(len(doc.related_resources), 1)
