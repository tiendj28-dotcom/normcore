"""Cài Frappe Workflow "NC Price Proposal" từ `proposal.TRANSITIONS` (ASM-030-03, ADR-011).

Idempotent; gọi ở after_install và after_migrate (hook_registry/FEAT-030.json).
"""

import frappe

from normcore.benchmark import proposal

DOCTYPE = "NC Price Proposal"
WORKFLOW = "NC Price Proposal"
STATE_ROLES = {
	proposal.DRAFT: [proposal.FINANCE],
	proposal.WAIT_DEPT: [proposal.FINANCE],
	proposal.WAIT_DIRECTOR: [proposal.FINANCE],
	proposal.APPROVED: [proposal.FINANCE],
	proposal.WAIT_AUTHORITY: [proposal.FINANCE],
	proposal.AUTHORITY_APPROVED: [proposal.FINANCE],
}


def _ensure(doctype, name_field, name):
	if not frappe.db.exists(doctype, name):
		frappe.get_doc({"doctype": doctype, name_field: name}).insert(ignore_permissions=True)


def ensure_workflow():
	if not frappe.db.exists("DocType", DOCTYPE):
		return
	for state in proposal.STATES:
		_ensure("Workflow State", "workflow_state_name", state)
	for action in sorted({t[1] for t in proposal.TRANSITIONS}):
		_ensure("Workflow Action Master", "workflow_action_name", action)
	if frappe.db.exists("Workflow", WORKFLOW):
		wf = frappe.get_doc("Workflow", WORKFLOW)
		wf.states, wf.transitions = [], []
	else:
		wf = frappe.new_doc("Workflow")
		wf.workflow_name = WORKFLOW
	wf.document_type = DOCTYPE
	wf.workflow_state_field = "workflow_state"
	wf.is_active = 1
	wf.send_email_alert = 0
	wf.override_status = 1
	for state in proposal.STATES:
		for role in STATE_ROLES[state]:
			wf.append("states", {"state": state, "doc_status": "0", "allow_edit": role})
	for src, action, dst, role in proposal.TRANSITIONS:
		wf.append(
			"transitions",
			{"state": src, "action": action, "next_state": dst, "allowed": role, "allow_self_approval": 1},
		)
	if wf.is_new():
		wf.insert(ignore_permissions=True)
	else:
		wf.save(ignore_permissions=True)


def after_install():
	ensure_workflow()


def after_migrate():
	ensure_workflow()
