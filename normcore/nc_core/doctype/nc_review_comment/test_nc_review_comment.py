"""NC Review Comment (FR-WF-003; TC-WF-08) và quyền theo ma trận (FR-ACC-007)."""

import frappe

from normcore.api import procedure_workflow as wf
from normcore.api.test_procedure_workflow import WorkflowBase

DT = "NC Clinical Procedure"
COMMENT = "NC Review Comment"


class TestNCReviewComment(WorkflowBase):
	def _as(self, user, fn, *a, **kw):
		frappe.set_user(user)
		try:
			return fn(*a, **kw)
		finally:
			frappe.set_user("Administrator")

	def test_TC_WF_08_y_kien_theo_buoc_hien_cho_nguoi_soan_sau_khi_bi_tra_lai(self):
		self.to_council()
		res = self._as(self.member, wf.add_review_comment, self.name, "Bước này thiếu chống nhiễm", target_step_id="S001")
		self.assertEqual(frappe.db.get_value(COMMENT, res["name"], "target_step_id"), "S001")
		self.assertEqual(frappe.db.get_value(COMMENT, res["name"], "review_state"), "Chờ hội đồng thẩm định")
		self._as(self.member, wf.add_review_comment, self.name, "Đại cương quá ngắn", target_section="Đại cương")
		self._as(self.member, wf.add_review_comment, self.name, "Ý kiến chung")
		self.act(self.sec, "Từ chối", reason="Cần sửa")
		review = self._as(self.clin, wf.get_review, self.name)
		self.assertEqual([c["comment"] for c in review["comments_by_step"]["S001"]], ["Bước này thiếu chống nhiễm"])
		self.assertEqual(len(review["comments_by_section"]["Đại cương"]), 1)
		self.assertEqual(len(review["comments_general"]), 1)
		self.assertEqual(review["open_comments"], 3)
		self.assertEqual(review["last_reject"]["reason"], "Cần sửa")
		self._as(self.head, wf.set_comment_resolved, res["name"], 1)
		self.assertEqual(self._as(self.clin, wf.get_review, self.name)["open_comments"], 2)

	def test_rang_buoc_validate(self):
		self.to_council()
		bad = [
			dict(comment="x", target_step_id="S999"),
			dict(comment="x", target_step_id="S001", target_section="Chỉ định"),
			dict(comment="   "),
		]
		for kw in bad:
			with self.assertRaises(frappe.ValidationError):
				self._as(self.member, wf.add_review_comment, self.name, **kw)

	def test_khong_ghi_khi_nhap(self):
		with self.assertRaises(frappe.ValidationError):
			self._as(self.head, wf.add_review_comment, self.name, "Ý kiến")

	def test_chi_resolved_doi_duoc(self):
		self.to_council()
		name = self._as(self.member, wf.add_review_comment, self.name, "Ý kiến")["name"]
		doc = frappe.get_doc(COMMENT, name)
		doc.comment = "Đổi"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)

	def test_quyen_review_comment_cac_vai_tro(self):
		self.to_council()
		name = self._as(self.member, wf.add_review_comment, self.name, "Ý kiến")["name"]
		resource = __import__("normcore.tests.utils", fromlist=["make_user"]).make_user(
			"rm.wf@normcore.test", "NC Resource Manager"
		)
		# Resource Manager không quyền
		frappe.set_user(resource)
		self.assertFalse(frappe.has_permission(COMMENT, "read", doc=name))
		self.assertRaises(frappe.PermissionError, wf.add_review_comment, self.name, "x")
		# Auditor: chỉ đọc
		frappe.set_user(self.auditor)
		self.assertTrue(frappe.has_permission(COMMENT, "read", doc=name))
		self.assertFalse(frappe.has_permission(COMMENT, "write", doc=name))
		self.assertFalse(frappe.has_permission(COMMENT, "create"))
		self.assertRaises(frappe.PermissionError, wf.add_review_comment, self.name, "x")
		self.assertRaises(frappe.PermissionError, wf.set_comment_resolved, name, 1)
		# Clinician đọc, không tạo
		frappe.set_user(self.clin)
		self.assertTrue(frappe.has_permission(COMMENT, "read", doc=name))
		self.assertRaises(frappe.PermissionError, wf.add_review_comment, self.name, "x")
		frappe.set_user("Administrator")
		self.assertEqual(frappe.db.count(COMMENT, {"ref_name": self.name}), 1)
