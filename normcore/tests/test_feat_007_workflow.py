"""FEAT-007: fixture Workflow khớp approval.TRANSITIONS; NC Auditor không duyệt được (FR-WF-001..007, FR-ACC-007)."""

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.core import readonly
from normcore.procedure import approval


class TestWorkflowFixture(FrappeTestCase):
	def _wf(self):
		return frappe.get_doc("Workflow", "NC Clinical Procedure")

	def test_workflow_fixture_khop_transitions(self):
		wf = self._wf()
		self.assertTrue(wf.is_active)
		self.assertEqual(wf.workflow_state_field, "workflow_state")
		got = {(t.state, t.action, t.next_state, t.allowed) for t in wf.transitions}
		self.assertEqual(got, set(approval.TRANSITIONS))

	def test_workflow_fixture_du_bay_trang_thai(self):
		states = {s.state for s in self._wf().states}
		self.assertEqual(
			states, set(approval.PENDING_STATES) | set(approval.CLOSED_STATES) | {approval.DRAFT}
		)

	def test_workflow_fixture_auditor_khong_duoc_duyet(self):
		wf = self._wf()
		data = {
			"name": wf.name,
			"transitions": [{"state": t.state, "action": t.action, "allowed": t.allowed} for t in wf.transitions],
			"states": [{"state": s.state, "allow_edit": s.allow_edit} for s in wf.states],
		}
		self.assertEqual(readonly.workflow_violations([data]), [])

	def test_workflow_fixture_dieu_kien_thu_ky(self):
		for t in self._wf().transitions:
			if t.allowed == "NC Council Member":
				self.assertIn("council_secretary", t.condition or "")
			else:
				self.assertFalse(t.condition)

	def test_nc_settings_truong_moi(self):
		meta = frappe.get_meta("NC Settings")
		self.assertEqual(meta.get_field("approval_reminder_days").default, "7")
		self.assertEqual(meta.get_field("council_secretary").options, "User")

	def test_nc_settings_thu_ky_phai_la_council_member(self):
		from normcore.tests.utils import make_user

		other = make_user("t007-khong-vai-tro@example.com")
		doc = frappe.get_single("NC Settings")
		doc.council_secretary = other
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)
		frappe.db.rollback()
