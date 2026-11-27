"""API phương án giá (FEAT-030; FR-PRICE-001..010, FR-OUT-007). Logic thuần ở `normcore/benchmark/logic.py`.

Kiểm quyền tường minh trong từng hàm. Giả định ASM-030-01..18 (docs/decisions/assumptions/FEAT-030.md).
"""

import frappe
from frappe import _
from frappe.utils import getdate, now_datetime, nowdate

from normcore.api import benchmark as benchmark_api
from normcore.api import price_compare
from normcore.benchmark import proposal as logic
from normcore.core import notify, settings
from normcore.core import permissions as scope
from normcore.exports import price_comparison

DT = "NC Price Proposal"
RUN = "NC Costing Run"
COST = "NC Service Cost"
ROLE_FINANCE = logic.FINANCE
ROLE_HEAD = logic.DEPT_HEAD
ROLE_DIRECTOR = logic.DIRECTOR


def _deny(message):
	frappe.throw(message, frappe.PermissionError)


def _cost_rows(run_name):
	return frappe.get_all(
		COST,
		{"costing_run": run_name, "calc_status": ["!=", "Lỗi"]},
		[
			"name",
			"technical_service",
			"department",
			"full_cost",
			"calculated_price",
			"rounded_price",
			"calc_status",
		],
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
	items = logic.build_items(costs, price_compare.benchmark_summary(run, costs))
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
	if action == logic.ACT_SUBMIT:
		if ROLE_FINANCE not in roles or not frappe.has_permission(DT, "write", doc=doc, user=user):
			return _("Chỉ NC Finance được gửi duyệt phương án giá")
	elif action == logic.ACT_CONFIRM:
		if ROLE_HEAD not in roles:
			return _("Chỉ trưởng khoa được xác nhận phương án giá")
		if not _my_departments(doc, user):
			return _("Bạn không phải trưởng khoa của khoa nào còn chờ xác nhận trong phương án này")
	elif action == logic.ACT_APPROVE:
		if ROLE_DIRECTOR not in roles:
			return _("Chỉ NC Director được phê duyệt phương án giá")
	elif action == logic.ACT_REJECT:
		if state == logic.WAIT_DEPT:
			if ROLE_HEAD not in roles or not _my_departments(doc, user):
				return _("Chỉ trưởng khoa của khoa có dòng trong phương án được từ chối ở cấp này")
		elif ROLE_DIRECTOR not in roles:
			return _("Chỉ NC Director được từ chối ở cấp này")
	elif action == logic.ACT_RECORD:
		if ROLE_FINANCE not in roles or not frappe.has_permission(DT, "write", doc=doc, user=user):
			return _("Chỉ NC Finance được ghi kết quả phê duyệt của cấp thẩm quyền")
	return None


def _available_actions(doc, user):
	out = []
	for src, act, _dst, _role in logic.TRANSITIONS:
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
		d["needs_basis"] = 1 if logic.needs_basis(d) else 0
		out.append(d)
	return out


@frappe.whitelist()
def get_proposal(proposal):
	"""Dữ liệu form SCR-DSK-027: dòng, xác nhận, hành động người gọi làm được, tóm tắt (technical-design 3.2)."""
	if not frappe.has_permission(DT, "read", doc=proposal):
		_deny(_("Bạn không có quyền xem phương án giá này"))
	doc = frappe.get_doc(DT, proposal)
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
		"my_departments": _my_departments(doc, user) if doc.workflow_state == logic.WAIT_DEPT else [],
		"summary": {
			"count": len(items),
			"adjusted": sum(1 for i in items if i["needs_basis"]),
			"below_cost": sum(1 for i in items if i["below_cost"]),
			"unacked": sum(1 for i in items if i["below_cost"] and not i["director_ack"]),
		},
	}


# ---- thông báo --------------------------------------------------------------------------------------------

SKIP_USERS = ("Administrator", "Guest")


def _users_with_role(role):
	names = frappe.get_all("Has Role", {"role": role, "parenttype": "User"}, pluck="parent")
	if not names:
		return []
	users = frappe.get_all("User", {"name": ["in", names], "enabled": 1}, pluck="name")
	return [u for u in users if u not in SKIP_USERS]


def _notify(users, subject, doc):
	return notify.notify(users, subject, DT, doc.name)


# ---- lịch sử giá (FR-PRICE-006, 008, 010) ---------------------------------------------------------------


def write_price_history(doc, use_authority=False, effective_date=None, authority_doc_no=None):
	"""Thêm dòng NC Service Price History vào từng dịch vụ; trùng (dịch vụ, loại giá, ngày) thì chặn trước khi
	ghi bất cứ dòng nào (ASM-030-09). Không xóa, không sửa dòng cũ (FR-PRICE-010)."""
	items = [i.as_dict() for i in doc.items]
	rows = logic.history_rows(
		items,
		doc.price_category,
		effective_date or doc.apply_from,
		doc.name,
		authority_doc_no,
		use_authority,
	)
	existing = {}
	for r in frappe.get_all(
		"NC Service Price History",
		{"parenttype": "NC Technical Service", "parent": ["in", [r["technical_service"] for r in rows]]},
		["parent", "price_category", "effective_date", "price_proposal"],
	):
		existing.setdefault(r.parent, []).append(r)
	conflicts = logic.history_conflicts(existing, rows)
	if conflicts:
		c = conflicts[0]
		frappe.throw(
			_(
				"Dịch vụ {0} đã có giá loại {1} áp dụng ngày {2} (phương án {3}), không ghi đè lịch sử giá"
			).format(c["technical_service"], c["price_category"], c["effective_date"], c["price_proposal"]),
			title=_("Trùng lịch sử giá"),
		)
	for r in rows:
		svc = frappe.get_doc("NC Technical Service", r["technical_service"])
		svc.flags.price_history_write = True
		svc.append(
			"approved_prices",
			{
				k: r[k]
				for k in ("price_category", "price", "effective_date", "price_proposal", "authority_doc_no")
			},
		)
		svc.save(ignore_permissions=True)
	return len(rows)


# ---- hành động ---------------------------------------------------------------------------------------------


def _json(value, default):
	if value in (None, ""):
		return default
	return frappe.parse_json(value) if isinstance(value, str) else value


def _set_items(doc, dict_rows, fields):
	by_name = {d["name"]: d for d in dict_rows}
	for row in doc.items:
		for f in fields:
			row.set(f, by_name[row.name].get(f))


def _transition(doc, action, new_state, reason=None):
	old = doc.workflow_state
	doc.workflow_state = new_state
	doc.flags.proposal_action = action
	doc.flags.workflow_action = action
	doc.flags.audit_detail = reason or None
	doc.save(ignore_permissions=True)
	doc.add_comment("Workflow", f"{action}: {old} → {new_state}" + (f" — {reason}" if reason else ""))


def _head_users(depts):
	heads = [frappe.db.get_value("NC Department", d, "head_user") for d in depts]
	return [h for h in heads if h]


@frappe.whitelist()
def apply_action(proposal, action, reason=None, acknowledged=None, department=None, note=None):
	"""Gửi duyệt / Xác nhận / Phê duyệt / Từ chối (technical-design 3.2)."""
	user = frappe.session.user
	if not frappe.has_permission(DT, "read", doc=proposal):
		_deny(_("Bạn không có quyền xem phương án giá này"))
	doc = frappe.get_doc(DT, proposal)
	state = doc.workflow_state
	if not any(t[0] == state and t[1] == action for t in logic.TRANSITIONS):
		frappe.throw(_("Hành động {0} không áp dụng ở trạng thái {1}").format(action, state))
	error = _actor_error(doc, action, user)
	if error:
		_deny(error)
	reason = (reason or "").strip()
	items = [i.as_dict() for i in doc.items]
	authority = _approval_authority(doc)

	if action == logic.ACT_SUBMIT:
		errors = logic.submit_errors(items, authority, doc.apply_from)
		if errors:
			frappe.throw("<br>".join(errors), title=_("Chưa gửi duyệt được"))
		depts = logic.departments(items)
		doc.set("department_confirmations", [{"department": d} for d in depts])
		doc.flags.proposal_action = action
		_transition(doc, action, logic.WAIT_DEPT)
		_notify(_head_users(depts), _("{0}: chờ khoa xác nhận").format(doc.name), doc)
		return {"workflow_state": logic.WAIT_DEPT}

	if action == logic.ACT_CONFIRM:
		mine = _my_departments(doc, user)
		if department:
			if department not in mine:
				_deny(
					_("Bạn không phải trưởng khoa của khoa {0} hoặc khoa này đã xác nhận").format(department)
				)
			mine = [department]
		conf = [c.as_dict() for c in doc.department_confirmations]
		try:
			_n, done = logic.confirm(conf, mine, user, now_datetime())
		except ValueError as e:
			frappe.throw(_(str(e)))
		for row, c in zip(doc.department_confirmations, conf, strict=True):
			for f in ("confirmed_by", "confirmed_on"):
				row.set(f, c.get(f))
			if note and c["department"] in mine:
				row.note = note
		new_state = logic.WAIT_DIRECTOR if done else logic.WAIT_DEPT
		doc.flags.proposal_action = action
		_transition(doc, action, new_state, ", ".join(mine))
		if done:
			_notify(_users_with_role(ROLE_DIRECTOR), _("{0}: chờ phê duyệt").format(doc.name), doc)
		return {"workflow_state": new_state}

	if action == logic.ACT_APPROVE:
		errors = logic.approve_errors(items, _json(acknowledged, []))
		if errors:
			frappe.throw("<br>".join(errors), title=_("Chưa phê duyệt được"))
		try:
			new_state = logic.approved_state(authority)
		except ValueError:
			frappe.throw(_("Loại giá {0} chưa khai cấp phê duyệt").format(doc.price_category))
		_set_items(doc, items, ("director_ack",))
		doc.flags.proposal_action = action
		if new_state == logic.APPROVED:
			write_price_history(doc, use_authority=False)
		_transition(doc, action, new_state)
		subject = _("{0}: đã duyệt") if new_state == logic.APPROVED else _("{0}: đã duyệt nội bộ, chờ trình")
		_notify([doc.owner], subject.format(doc.name), doc)
		return {"workflow_state": new_state}

	# Từ chối
	if not reason:
		frappe.throw(_("Cần nhập lý do từ chối"))
	level = _("trưởng khoa") if state == logic.WAIT_DEPT else _("giám đốc")
	logic.reset_for_draft(items, doc.department_confirmations)
	_set_items(doc, items, ("director_ack",))
	doc.set("department_confirmations", [])
	doc.flags.proposal_action = action
	_transition(doc, action, logic.DRAFT, reason)
	_notify([doc.owner], _("{0}: bị từ chối ở cấp {1} — {2}").format(doc.name, level, reason), doc)
	return {"workflow_state": logic.DRAFT}


@frappe.whitelist()
def record_authority_result(proposal, authority_doc_no, authority_doc_date, prices, apply_from=None):
	"""FR-PRICE-008: ghi kết quả phê duyệt của cơ quan có thẩm quyền; giá được duyệt nằm cạnh giá đã trình."""
	if not frappe.has_permission(DT, "read", doc=proposal):
		_deny(_("Bạn không có quyền xem phương án giá này"))
	doc = frappe.get_doc(DT, proposal)
	user = frappe.session.user
	if doc.workflow_state != logic.WAIT_AUTHORITY:
		frappe.throw(_("Chỉ ghi kết quả khi phương án ở trạng thái {0}").format(logic.WAIT_AUTHORITY))
	error = _actor_error(doc, logic.ACT_RECORD, user)
	if error:
		_deny(error)
	prices = _json(prices, {})
	items = [i.as_dict() for i in doc.items]
	errors = logic.authority_errors(items, prices, authority_doc_no, authority_doc_date)
	if errors:
		frappe.throw("<br>".join(errors), title=_("Chưa ghi được kết quả phê duyệt"))
	for row in doc.items:
		row.authority_price = prices[row.name]
	doc.authority_doc_no = authority_doc_no.strip()
	doc.authority_doc_date = getdate(authority_doc_date)
	effective = getdate(apply_from) if apply_from else (doc.apply_from or doc.authority_doc_date)
	doc.flags.proposal_action = logic.ACT_RECORD
	write_price_history(
		doc, use_authority=True, effective_date=effective, authority_doc_no=doc.authority_doc_no
	)
	_transition(doc, logic.ACT_RECORD, logic.AUTHORITY_APPROVED)
	return {"workflow_state": logic.AUTHORITY_APPROVED}


# ---- việc chờ (FR-NOTI-003) --------------------------------------------------------------------------------


def pending_for(user):
	"""Phương án chờ `user`: trưởng khoa (còn khoa chưa xác nhận), Giám đốc (chờ phê duyệt), NC Finance (chờ trình)."""
	if not user or user == "Guest":
		return []
	roles = set(frappe.get_roles(user))
	wanted = {}
	if ROLE_HEAD in roles:
		wanted[logic.WAIT_DEPT] = ("Xác nhận phần của khoa", ROLE_HEAD)
	if ROLE_DIRECTOR in roles:
		wanted[logic.WAIT_DIRECTOR] = ("Phê duyệt phương án giá", ROLE_DIRECTOR)
	if ROLE_FINANCE in roles:
		wanted[logic.WAIT_AUTHORITY] = ("Ghi kết quả phê duyệt của cấp thẩm quyền", ROLE_FINANCE)
	if not wanted:
		return []
	days = int(settings.get("approval_reminder_days"))
	today = getdate(nowdate())
	out = []
	for row in frappe.get_all(
		DT, {"workflow_state": ["in", list(wanted)]}, ["name", "modified", "workflow_state", "title"]
	):
		task, _role = wanted[row.workflow_state]
		doc = frappe.get_doc(DT, row.name)
		if row.workflow_state == logic.WAIT_DEPT and not _my_departments(doc, user):
			continue
		since = getdate(row.modified)
		out.append(
			{
				"doctype": DT,
				"name": row.name,
				"title": row.title,
				"task": task,
				"state": row.workflow_state,
				"department": None,
				"since": since.isoformat(),
				"overdue": (today - since).days >= days,
				"route": f"/app/nc-price-proposal/{row.name}",
			}
		)
	return out


# ---- bảng so sánh giá (FR-OUT-007) -------------------------------------------------------------------------


def comparison_data(run_doc, proposal_doc=None, departments=None):
	"""Dữ liệu bảng so sánh giá: thống kê và giá tham chiếu theo đúng tập giá của Bàn so sánh giá (FEAT-028).

	`departments`: chỉ giữ dịch vụ của các khoa này (Trưởng khoa, ASM-030-13).
	"""
	costs = frappe.get_all(
		COST,
		{"costing_run": run_doc.name, "calc_status": ["!=", "Lỗi"]},
		["name", "technical_service", "department", "calculated_price", "rounded_price"],
		order_by="technical_service",
		limit_page_length=0,
	)
	if departments is not None:
		costs = [c for c in costs if c.department in departments]
	services = [c.technical_service for c in costs]
	names = {
		s.name: s.service_name
		for s in frappe.get_all(
			"NC Technical Service", {"name": ["in", services or [""]]}, ["name", "service_name"]
		)
	}
	proposed = {i.technical_service: i.proposed_price for i in proposal_doc.items} if proposal_doc else {}
	prices = benchmark_api.comparable_prices_bulk(services, run_doc.price_category, run_doc.costing_date)
	filters = price_compare._filters(None, None, None)
	out_services, out_prices = [], []
	for c in costs:
		summary, selected, _excluded = price_compare._stats_for(
			c, prices.get(c.technical_service, []), run_doc, filters, False
		)
		out_services.append(
			{
				"service_code": c.technical_service,
				"service_name": names.get(c.technical_service),
				"department": c.department,
				"calculated_price": c.calculated_price,
				"rounded_price": c.rounded_price,
				"proposed_price": proposed.get(c.technical_service),
				**{k: summary[k] for k in ("count", "min", "median", "max", "deviation_pct", "label")},
			}
		)
		for r in selected:
			out_prices.append(
				{**r, "service_code": c.technical_service, "service_name": names.get(c.technical_service)}
			)
	data = {"services": out_services, "prices": out_prices, "proposal": None}
	if proposal_doc:
		data["proposal"] = {"name": proposal_doc.name, "title": proposal_doc.title}
	return data


def build_comparison_file(run_doc, meta, proposal_doc=None, departments=None):
	return price_comparison.build_workbook(comparison_data(run_doc, proposal_doc, departments), meta)


@frappe.whitelist()
def export_price_comparison(proposal):
	"""FR-OUT-007: bảng so sánh giá từ phương án giá; Trưởng khoa chỉ nhận dòng của khoa mình (ASM-030-13)."""
	from normcore.api import export as export_api

	if not frappe.has_permission(DT, "read", doc=proposal):
		_deny(_("Bạn không có quyền xem phương án giá này"))
	doc = frappe.get_doc(DT, proposal)
	run = frappe.get_doc(RUN, doc.costing_run)
	meta = export_api._meta("price_comparison", f"{DT} {doc.name}", run.name)
	filename = f"so-sanh-gia-{doc.name}.xlsx"
	try:
		content = build_comparison_file(run, meta, doc, scope.readable_departments(DT))
	except Exception as e:
		export_api._generation_error(filename, e)
	return export_api._send(filename, content, "price_comparison", DT, doc.name)
