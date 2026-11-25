"""In PDF, xuất DOCX quy trình (FR-PROC-010, FR-PROC-011; TC-PROC-07)."""

import frappe

from normcore.api import procedure_workflow as wf
from normcore.api.test_procedure_workflow import DT, WorkflowBase
from normcore.exports.procedure_docx import docx_text
from normcore.tests.utils import make_user


class TestPrint(WorkflowBase):
	def html(self, name):
		return frappe.get_print(DT, name, print_format=wf.PRINT_FORMAT)

	def publish_via_flow(self):
		self.to_council()
		self.act(self.sec, "Thông qua")
		self.act(self.director, "Ban hành", decision_no="456/QĐ-BV", effective_date="2026-03-05")

	def _download(self, fn, user):
		frappe.set_user(user)
		try:
			fn(self.name)
			return frappe.local.response
		finally:
			frappe.set_user("Administrator")

	def test_TC_PROC_07_ban_nhap_co_du_thao(self):
		self.assertIn("DỰ THẢO", self.html(self.name))
		doc = frappe.get_doc(DT, self.name)
		self.assertIn("DỰ THẢO", docx_text(wf._docx_bytes(doc)))

	def test_TC_PROC_07_ban_ban_hanh_day_du(self):
		self.publish_via_flow()
		html = self.html(self.name)
		self.assertNotIn("DỰ THẢO", html)
		for s in (
			"456/QĐ-BV",
			"Phiên bản 1",
			"05/03/2026",
			"Người soạn",
			"Trưởng khoa",
			"Hội đồng chuyên môn",
			"Giám đốc",
		):
			self.assertIn(s, html)
		doc = frappe.get_doc(DT, self.name)
		text = docx_text(wf._docx_bytes(doc))
		self.assertNotIn("DỰ THẢO", text)
		for s in ("456/QĐ-BV", "Phiên bản 1", "05/03/2026"):
			self.assertIn(s, text)
		ctx = wf.get_print_context(doc)
		names = [s["user"] for s in ctx["signatures"]]
		self.assertTrue(all(names), names)  # cả bốn ô có người ký

	def test_TC_PROC_07_pdf_bat_dau_bang_pdf(self):
		resp = self._download(wf.download_pdf, self.clin)
		self.assertTrue(resp.filecontent.startswith(b"%PDF"))
		self.assertEqual(resp.filename, f"{self.name}.pdf")
		self.assertEqual(resp.type, "download")

	def test_TC_PROC_07_docx_va_ghi_xuat_tep(self):
		resp = self._download(wf.download_docx, self.clin)
		self.assertEqual(resp.filecontent[:2], b"PK")
		self.assertEqual(resp.filename, f"{self.name}.docx")
		events = frappe.get_all(
			"NC Audit Event", {"ref_name": self.name, "event_type": "Xuất tệp"}, pluck="detail"
		)
		self.assertEqual(events, [f"DOCX: {self.name}.docx"])

	def test_TC_PROC_07_quyen_tai(self):
		# Auditor tải được (ASM-007-09); Resource Manager đọc được quy trình thì tải được
		self.assertTrue(self._download(wf.download_pdf, self.auditor).filecontent.startswith(b"%PDF"))
		self.publish_via_flow()  # bản ban hành đọc công khai (FR-ACC-003)
		rm = make_user("rm.print@normcore.test", "NC Resource Manager")
		self.assertTrue(self._download(wf.download_docx, rm).filecontent)
		# người không đọc được quy trình
		nobody = make_user("nobody.print@normcore.test")
		frappe.set_user(nobody)
		self.assertRaises(frappe.PermissionError, wf.download_pdf, self.name)
		self.assertRaises(frappe.PermissionError, wf.download_docx, self.name)
