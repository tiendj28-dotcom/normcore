"""Thu hồi quy trình (FEAT-008; FR-WF-012)."""

import frappe

from normcore.api import procedure_workflow as wf
from normcore.api.test_procedure_revision import RevisionBase

DT = "NC Clinical Procedure"


class TestWithdraw(RevisionBase):
	def setUp(self):
		super().setUp()
		frappe.db.set_value(DT, self.v1.name, "owner", self.clin)
		self.council = self.make_council()

	def make_council(self):
		from normcore.tests.utils import make_user

		return make_user("council.wd@normcore.test", "NC Council Member")

	def withdraw(self, user, reason="Sai quy định mới"):
		frappe.set_user(user)
		try:
			return wf.apply_action(self.v1.name, "Thu hồi", reason=reason)
		finally:
			frappe.set_user("Administrator")

	def test_FR_WF_012_thu_hoi_co_ly_do(self):
		self.assertEqual(self.withdraw(self.director)["workflow_state"], "Đã thu hồi")
		self.assertEqual(frappe.db.get_value(DT, self.v1.name, "workflow_state"), "Đã thu hồi")
		ev = frappe.get_all(
			"NC Audit Event",
			{"ref_name": self.v1.name, "event_type": "Chuyển trạng thái", "to_state": "Đã thu hồi"},
			["from_state", "detail", "user"],
		)
		self.assertEqual(len(ev), 1)
		self.assertEqual(
			(ev[0].from_state, ev[0].detail, ev[0].user), ("Đã ban hành", "Sai quy định mới", self.director)
		)
		self.assertTrue(
			frappe.get_all(
				"Comment",
				{
					"reference_doctype": DT,
					"reference_name": self.v1.name,
					"comment_type": "Workflow",
					"content": ["like", "%Sai quy định mới%"],
				},
			)
		)
		self.assertTrue(
			frappe.get_all("Notification Log", {"for_user": self.clin, "document_name": self.v1.name})
		)
		# nội dung vẫn bị khóa
		doc = frappe.get_doc(DT, self.v1.name)
		doc.overview = "đổi"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)
		frappe.set_user(self.auditor)
		try:
			self.assertEqual(wf.get_review(self.v1.name)["last_withdraw"]["reason"], "Sai quy định mới")
		finally:
			frappe.set_user("Administrator")

	def test_FR_WF_012_thu_hoi_tu_choi(self):
		for user in (self.head, self.council, self.auditor, self.finance, self.clin):
			with self.assertRaises(frappe.PermissionError, msg=user):
				self.withdraw(user)
		for reason in ("", "   ", None):
			with self.assertRaises(frappe.ValidationError):
				self.withdraw(self.director, reason)
		self.assertEqual(frappe.db.get_value(DT, self.v1.name, "workflow_state"), "Đã ban hành")
		# chỉ Director thấy hành động Thu hồi
		for user, expect in ((self.director, True), (self.head, False), (self.auditor, False)):
			frappe.set_user(user)
			try:
				self.assertEqual("Thu hồi" in wf.get_review(self.v1.name)["actions"], expect, user)
			finally:
				frappe.set_user("Administrator")
		self.assertIsNone(wf.get_review(self.v1.name)["last_withdraw"])

	def test_FR_WF_012_sai_trang_thai(self):
		from normcore.tests.utils import to_state

		for state in ("Đã thay thế", "Nháp", "Đã thu hồi"):
			to_state(self.v1, state)
			with self.assertRaises(frappe.ValidationError, msg=state):
				self.withdraw(self.director)
