"""FEAT-039: NC Auditor chỉ đọc (FR-ACC-007, TC-CLS-44, TC-AUD-03)."""

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.core import permissions as perms


class TestQuetQuyen(FrappeTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()
		# Workflow, Custom DocPerm có thể đã commit ngầm: dọn rõ ràng để không làm bẩn site test
		for name in frappe.get_all("Workflow", {"name": ["like", "FEAT39%"]}, pluck="name"):
			frappe.delete_doc("Workflow", name, force=True, ignore_permissions=True)
		for name in frappe.get_all("Custom DocPerm", {"parent": "NC Norm Set", "role": "NC Auditor"}, pluck="name"):
			frappe.delete_doc("Custom DocPerm", name, force=True, ignore_permissions=True)
		frappe.clear_cache(doctype="NC Norm Set")
		frappe.db.commit()

	def test_TC_CLS_44_quet_quyen_sach(self):
		self.assertEqual(perms.read_only_violations(), [])
		self.assertIn("NC Norm Set", perms.nc_doctypes())

	def test_TC_CLS_44_quet_bat_custom_docperm(self):
		frappe.get_doc(
			{
				"doctype": "Custom DocPerm",
				"parent": "NC Norm Set",
				"parenttype": "DocType",
				"parentfield": "permissions",
				"role": "NC Auditor",
				"permlevel": 0,
				"read": 1,
				"write": 1,
			}
		).insert(ignore_permissions=True)
		frappe.clear_cache(doctype="NC Norm Set")
		out = perms.read_only_violations()
		self.assertTrue(any("NC Norm Set" in v and "write" in v for v in out), out)

	def test_TC_CLS_44_quet_bat_workflow(self):
		frappe.get_doc({"doctype": "Workflow State", "workflow_state_name": "FEAT39 Nháp"}).insert(
			ignore_if_duplicate=True
		)
		frappe.get_doc({"doctype": "Workflow State", "workflow_state_name": "FEAT39 Duyệt"}).insert(
			ignore_if_duplicate=True
		)
		frappe.get_doc({"doctype": "Workflow Action Master", "workflow_action_name": "FEAT39 Duyệt"}).insert(
			ignore_if_duplicate=True
		)
		frappe.get_doc(
			{
				"doctype": "Workflow",
				"workflow_name": "FEAT39 Thử",
				"document_type": "NC Norm Set",
				"is_active": 0,
				"workflow_state_field": "feat39_state",
				"states": [
					{"state": "FEAT39 Nháp", "doc_status": 0, "allow_edit": "NC Auditor"},
					{"state": "FEAT39 Duyệt", "doc_status": 0, "allow_edit": "NC Admin"},
				],
				"transitions": [
					{
						"state": "FEAT39 Nháp",
						"action": "FEAT39 Duyệt",
						"next_state": "FEAT39 Duyệt",
						"allowed": "NC Auditor",
					}
				],
			}
		).insert(ignore_permissions=True)
		out = perms.read_only_violations()
		self.assertTrue(any("FEAT39 Thử" in v and "chuyển" in v for v in out), out)
		self.assertTrue(any("FEAT39 Thử" in v and "allow_edit" in v for v in out), out)
