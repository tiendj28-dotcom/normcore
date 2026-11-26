"""NC Section Service Map (bảng con của NC Legal Section): đóng dấu xác nhận khi lưu (FEAT-022, FR-SVC-006)."""

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.nc_library.doctype.nc_legal_document.library_fixtures import make_legal_document
from normcore.tests.utils import ensure_service, make_user


def make_section(doc, no="1", heading="Chụp X-quang ngực"):
	return frappe.get_doc(
		{
			"doctype": "NC Legal Section",
			"legal_document": doc.name,
			"section_no": no,
			"heading": heading,
			"plain_text": "Nội dung quy trình",
		}
	).insert(ignore_permissions=True)


class TestNCSectionServiceMap(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.svc_a = ensure_service("DV-MAP-A")
		self.svc_b = ensure_service("DV-MAP-B")
		self.section = make_section(make_legal_document("MAPTEST/QĐ-BYT"))

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_FR_SVC_006_validate_dong_dau(self):
		s = self.section
		s.append("service_mappings", {"technical_service": self.svc_a, "confidence": 100})
		s.save()
		row = s.service_mappings[0]
		self.assertEqual(row.mapping_status, "Đề xuất")
		self.assertFalse(row.confirmed_by)
		self.assertFalse(row.confirmed_on)

		row.mapping_status = "Đã xác nhận"
		s.save()
		s.reload()
		row = s.service_mappings[0]
		self.assertEqual(row.confirmed_by, "Administrator")
		self.assertTrue(row.confirmed_on)
		self.assertEqual(row.confidence, 100)
		first = row.confirmed_on

		# lưu lại không đổi gì: giữ dấu cũ
		s.save()
		s.reload()
		self.assertEqual(s.service_mappings[0].confirmed_on, first)

		# đặt lại "Đề xuất": xóa dấu
		s.service_mappings[0].mapping_status = "Đề xuất"
		s.save()
		s.reload()
		self.assertFalse(s.service_mappings[0].confirmed_by)
		self.assertFalse(s.service_mappings[0].confirmed_on)

	def test_FR_SVC_006_doi_dich_vu_dong_dau_lai(self):
		s = self.section
		s.append("service_mappings", {"technical_service": self.svc_a, "mapping_status": "Đã xác nhận"})
		s.save()
		s.reload()
		s.service_mappings[0].confirmed_by = "Guest"  # giả lập dấu cũ
		s.service_mappings[0].technical_service = self.svc_b
		s.save()
		s.reload()
		self.assertEqual(s.service_mappings[0].confirmed_by, "Administrator")

	def test_FR_SVC_006_hai_dong_cung_dich_vu_bi_tu_choi(self):
		s = self.section
		s.append("service_mappings", {"technical_service": self.svc_a})
		s.append("service_mappings", {"technical_service": self.svc_a})
		self.assertRaises(frappe.ValidationError, s.save)

	def test_FR_SVC_006_quyen_ban_ghi_cha(self):
		# bảng con theo quyền DocType cha: NC Auditor chỉ đọc, vai trò không NC không đọc được
		for user, role, can_write in (
			("map.auditor@example.com", "NC Auditor", False),
			("map.clin@example.com", "NC Clinician", False),
			("map.dc@example.com", "NC Document Controller", True),
		):
			make_user(user, role)
			frappe.set_user(user)
			self.assertEqual(frappe.has_permission("NC Legal Section", "write", doc=self.section), can_write)
			frappe.set_user("Administrator")
		make_user("map.none@example.com")
		frappe.set_user("map.none@example.com")
		self.assertFalse(frappe.has_permission("NC Legal Section", "read", doc=self.section))

	def test_FR_SVC_006_thay_doi_bang_con_co_version(self):
		s = self.section
		s.append("service_mappings", {"technical_service": self.svc_a})
		s.save()
		s.service_mappings[0].mapping_status = "Đã xác nhận"
		s.save(ignore_version=False)  # Frappe bỏ qua Version khi chạy test nếu không bật rõ
		ver = frappe.get_all(
			"Version", filters={"ref_doctype": "NC Legal Section", "docname": s.name}, pluck="data"
		)
		self.assertTrue(ver)
		self.assertIn("mapping_status", ver[-1])
