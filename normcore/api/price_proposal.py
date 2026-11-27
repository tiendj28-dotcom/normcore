"""API phương án giá (FEAT-030; FR-PRICE-001..010, FR-OUT-007). Logic thuần ở `normcore/benchmark/proposal.py`.

Kiểm quyền tường minh trong từng hàm. Giả định ASM-030-01..17 (docs/decisions/assumptions/FEAT-030.md).
"""

import frappe
from frappe import _
from frappe.utils import getdate

from normcore.api import price_compare
from normcore.benchmark import proposal
from normcore.core import permissions as scope

DT = "NC Price Proposal"
RUN = "NC Costing Run"
COST = "NC Service Cost"
ROLE_FINANCE = proposal.FINANCE
ROLE_HEAD = proposal.DEPT_HEAD
ROLE_DIRECTOR = proposal.DIRECTOR


def _deny(message):
	frappe.throw(message, frappe.PermissionError)


def _cost_rows(run_name):
	return frappe.get_all(
		COST,
		{"costing_run": run_name, "calc_status": ["!=", "Lỗi"]},
		["name", "technical_service", "department", "full_cost", "calculated_price", "rounded_price", "calc_status"],
		limit_page_length=0,
	)


@frappe.whitelist()
def create_proposal(costing_run, title=None, apply_from=None):
	"""FR-PRICE-001: lập phương án từ lần tính "Đã khóa"; mỗi dịch vụ một dòng, giá đề xuất = giá làm tròn."""
	if not frappe.has_permission(DT, "create"):
		_deny(_("Bạn không có quyền lập phương án giá"))
	run = frappe.get_doc(RUN, costing_run)
	if run.status != "Đã khóa":
		frappe.throw(_("Chỉ lập phương án từ lần tính giá đã khóa"))
	costs = [dict(c) for c in _cost_rows(run.name)]
	items = proposal.build_items(costs, price_compare.benchmark_summary(run, costs))
	if not items:
		frappe.throw(_("Lần tính này chưa có dịch vụ nào có kết quả để lập phương án"))
	doc = frappe.get_doc(
		{
			"doctype": DT,
			"title": title or _("Phương án giá {0}").format(run.title),
			"costing_run": run.name,
			"apply_from": getdate(apply_from) if apply_from else None,
			"items": items,
		}
	)
	doc.flags.proposal_action = "Lập phương án"
	doc.insert()
	return {"name": doc.name}


# ---- quyền thao tác ---------------------------------------------------------------------------------------


def _approval_authority(doc):
	return frappe.db.get_value("NC Price Category", doc.price_category, "approval_authority")


def _my_departments(doc, user):
	"""Khoa chưa xác nhận mà `user` (trưởng khoa) xác nhận được (ASM-030-12)."""
	if ROLE_HEAD not in set(frappe.get_roles(user)):
		return []
	mine = None if user == "Administrator" else scope.get_user_departments(user)
	return [
		c.department
		for c in doc.department_confirmations
		if not c.confirmed_by and (mine is None or c.department in mine)
	]


def _actor_error(doc, action, user):
	"""Lý do `user` không được làm `action` ở trạng thái hiện tại; None nếu được (technical-design 3.2)."""
	roles = set(frappe.get_roles(user))
	state = doc.workflow_state
	if action == proposal.ACT_SUBMIT:
		if ROLE_FINANCE not in roles or not frappe.has_permission(DT, "write", doc=doc, user=user):
			return _("Chỉ NC Finance được gửi duyệt phương án giá")
	elif action == proposal.ACT_CONFIRM:
		if ROLE_HEAD not in roles:
			return _("Chỉ trưởng khoa được xác nhận phương án giá")
		if not _my_departments(doc, user):
			return _("Bạn không phải trưởng khoa của khoa nào còn chờ xác nhận trong phương án này")
	elif action == proposal.ACT_APPROVE:
		if ROLE_DIRECTOR not in roles:
			return _("Chỉ NC Director được phê duyệt phương án giá")
	elif action == proposal.ACT_REJECT:
		if state == proposal.WAIT_DEPT:
			if ROLE_HEAD not in roles or not _my_departments(doc, user):
				return _("Chỉ trưởng khoa của khoa có dòng trong phương án được từ chối ở cấp này")
		elif ROLE_DIRECTOR not in roles:
			return _("Chỉ NC Director được từ chối ở cấp này")
	elif action == proposal.ACT_RECORD:
		if ROLE_FINANCE not in roles or not frappe.has_permission(DT, "write", doc=doc, user=user):
			return _("Chỉ NC Finance được ghi kết quả phê duyệt của cấp thẩm quyền")
	return None


def _available_actions(doc, user):
	out = []
	for src, act, _dst, _role in proposal.TRANSITIONS:
		if src == doc.workflow_state and act not in out and _actor_error(doc, act, user) is None:
			out.append(act)
	return out


# ---- xem ---------------------------------------------------------------------------------------------------


def _items_view(doc):
	names = {
		s.name: s.service_name
		for s in frappe.get_all(
			"NC Technical Service",
			{"name": ["in", [i.technical_service for i in doc.items] or [""]]},
			["name", "service_name"],
		)
	}
	out = []
	for i in doc.items:
		d = i.as_dict()
		d["service_name"] = names.get(i.technical_service)
		d["needs_basis"] = 1 if proposal.needs_basis(d) else 0
		out.append(d)
	return out


@frappe.whitelist()
def get_proposal(proposal_name=None, **kw):
	"""Dữ liệu form SCR-DSK-027: dòng, xác nhận, hành động người gọi làm được, tóm tắt (technical-design 3.2)."""
	name = proposal_name or kw.get("proposal")
	if not frappe.has_permission(DT, "read", doc=name):
		_deny(_("Bạn không có quyền xem phương án giá này"))
	doc = frappe.get_doc(DT, name)
	user = frappe.session.user
	items = _items_view(doc)
	depts = {
		d.name: d.department_name
		for d in frappe.get_all(
			"NC Department",
			{"name": ["in", [c.department for c in doc.department_confirmations] or [""]]},
			["name", "department_name"],
		)
	}
	confirmations = []
	for c in doc.department_confirmations:
		d = c.as_dict()
		d["department_name"] = depts.get(c.department)
		d["user_name"] = frappe.db.get_value("User", c.confirmed_by, "full_name") if c.confirmed_by else None
		confirmations.append(d)
	return {
		"doc": doc.as_dict(),
		"items": items,
		"confirmations": confirmations,
		"approval_authority": _approval_authority(doc),
		"actions": _available_actions(doc, user),
		"my_departments": _my_departments(doc, user) if doc.workflow_state == proposal.WAIT_DEPT else [],
		"summary": {
			"count": len(items),
			"adjusted": sum(1 for i in items if i["needs_basis"]),
			"below_cost": sum(1 for i in items if i["below_cost"]),
			"unacked": sum(1 for i in items if i["below_cost"] and not i["director_ack"]),
		},
	}
