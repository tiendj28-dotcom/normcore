"""Luồng duyệt ba cấp, ban hành, tác vụ ngày của quy trình (FEAT-007; FR-WF-001..008, FR-WF-013).

Kiểm quyền tường minh trong từng hàm. Thông báo dùng Notification Log (ASM-007-01); `core/notify.py` là FEAT-002.
Logic thuần ở `normcore/procedure/approval.py` và `validation.py`.
"""

import frappe
from frappe import _
from frappe.utils import getdate, nowdate

from normcore.core import audit, notify, settings
from normcore.core import permissions as scope
from normcore.procedure import approval, diff, printing, validation

DT = "NC Clinical Procedure"
COMMENT = "NC Review Comment"
SETTINGS = "NC Settings"
ROLE_CLINICIAN = "NC Clinician"
ROLE_HEAD = "NC Department Head"
ROLE_COUNCIL = "NC Council Member"
ROLE_DIRECTOR = "NC Director"
DEFAULT_REMINDER_DAYS = 7
SKIP_USERS = ("Administrator", "Guest")


def _deny(message):
	frappe.throw(message, frappe.PermissionError)


# ---- người duyệt -----------------------------------------------------------------------------------------


def _secretary():
	return frappe.db.get_single_value(SETTINGS, "council_secretary")


def _users_with_role(role):
	names = frappe.get_all("Has Role", {"role": role, "parenttype": "User"}, pluck="parent")
	if not names:
		return []
	users = frappe.get_all("User", {"name": ["in", names], "enabled": 1}, pluck="name")
	return [u for u in users if u not in SKIP_USERS]


def _head_of(doc):
	return frappe.db.get_value("NC Department", doc.department, "head_user")


def _recipients(state, doc):
	"""Người duyệt của cấp đang chờ ở `state` (FR-WF-001, 002, 004, FR-WF-013)."""
	if state == approval.WAIT_HEAD:
		head = _head_of(doc)
		return [head] if head else []
	if state == approval.WAIT_COUNCIL:
		return _users_with_role(ROLE_COUNCIL)
	if state == approval.WAIT_PUBLISH:
		return _users_with_role(ROLE_DIRECTOR)
	return []


def _actor_error(doc, action, user):
	"""Lý do `user` không được làm `action` ở trạng thái hiện tại; None nếu được (bảng technical-design 3.1)."""
	roles = set(frappe.get_roles(user))
	state = doc.workflow_state
	if state == approval.DRAFT:  # Gửi duyệt
		if ROLE_CLINICIAN not in roles or not frappe.has_permission(DT, "write", doc=doc, user=user):
			return _("Bạn không có quyền gửi duyệt quy trình này")
	elif state == approval.WAIT_HEAD:
		if ROLE_HEAD not in roles:
			return _("Chỉ trưởng khoa được duyệt ở cấp này")
		if user != "Administrator" and doc.department not in scope.get_user_departments(user):
			return _("Bạn không phải trưởng khoa của khoa chủ trì quy trình này")
	elif state == approval.WAIT_COUNCIL:
		if ROLE_COUNCIL not in roles:
			return _("Chỉ thành viên hội đồng được duyệt ở cấp này")
		if user != _secretary():
			return _("Chỉ thư ký hội đồng được thông qua hoặc từ chối ở cấp hội đồng")
	elif state == approval.WAIT_PUBLISH:
		if ROLE_DIRECTOR not in roles:
			return _("Chỉ NC Director được ban hành hoặc từ chối ở cấp này")
	elif state == approval.PUBLISHED:  # Thu hồi (FR-WF-012)
		if ROLE_DIRECTOR not in roles:
			return _("Chỉ NC Director được thu hồi quy trình")
	return None


def _available_actions(doc, user):
	out = []
	for src, act, _dst, _role in approval.ACTIONS:
		if src == doc.workflow_state and _actor_error(doc, act, user) is None:
			out.append(act)
	return out


# ---- thông báo -------------------------------------------------------------------------------------------


def _notify(users, subject, doc):
	"""Lớp mỏng gọi core.notify.notify (FR-NOTI-001); giữ người nhận, tiêu đề, chống trùng (ASM-007-01)."""
	return notify.notify(users, subject, DT, doc.name)


# ---- việc chờ (FR-NOTI-003) ------------------------------------------------------------------------------

_FORWARD = {
	approval.WAIT_HEAD: ("Đồng ý", "Duyệt cấp trưởng khoa", ROLE_HEAD),
	approval.WAIT_COUNCIL: ("Thông qua", "Thẩm định cấp hội đồng", ROLE_COUNCIL),
	approval.WAIT_PUBLISH: ("Ban hành", "Ban hành", ROLE_DIRECTOR),
}


def pending_for(user):
	"""Quy trình chờ `user` làm hành động tiến (ASM-002-03, 04). Nguồn của `normcore_pending_sources`."""
	if not user or user == "Guest":
		return []
	roles = set(frappe.get_roles(user))
	states = [st for st, (_a, _t, role) in _FORWARD.items() if role in roles]
	if not states:
		return []
	filters = {"workflow_state": ["in", states]}
	if user != "Administrator" and ROLE_HEAD in roles and ROLE_COUNCIL not in roles:
		filters["department"] = ["in", list(scope.get_user_departments(user)) or [""]]
	days = int(settings.get("approval_reminder_days"))
	today = getdate(nowdate())
	out = []
	for row in frappe.get_all(DT, filters, ["name", "modified"]):
		doc = frappe.get_doc(DT, row.name)
		action, task, _role = _FORWARD[doc.workflow_state]
		if _actor_error(doc, action, user) is not None:
			continue
		since = _entered_on(doc.name, doc.workflow_state, row.modified)
		out.append(
			{
				"doctype": DT,
				"name": doc.name,
				"title": f"{doc.technical_service} — {doc.department}",
				"task": task,
				"state": doc.workflow_state,
				"department": doc.department,
				"since": since.isoformat(),
				"overdue": (today - since).days >= days,
				"route": f"/app/procedure-editor/{doc.name}",
			}
		)
	return out


# ---- hành động -------------------------------------------------------------------------------------------


def _rows(doc, table):
	return [row.as_dict() for row in doc.get(table) or []]


@frappe.whitelist()
def apply_action(procedure, action, reason=None, decision_no=None, effective_date=None):
	"""Gửi duyệt / Đồng ý / Thông qua / Ban hành / Từ chối (technical-design 3.1)."""
	user = frappe.session.user
	if not frappe.has_permission(DT, "read", doc=procedure):
		_deny(_("Bạn không có quyền xem quy trình này"))
	doc = frappe.get_doc(DT, procedure)
	state = doc.workflow_state
	try:
		new_state = approval.next_state(state, action)
	except ValueError:
		frappe.throw(_("Hành động {0} không áp dụng ở trạng thái {1}").format(action, state))
	error = _actor_error(doc, action, user)
	if error:
		_deny(error)

	reason = (reason or "").strip()
	if action == "Gửi duyệt":
		errors = validation.submit_errors(
			_rows(doc, "steps"), _rows(doc, "resources"), _rows(doc, "citations")
		)
		if errors:
			frappe.throw("<br>".join(errors), title=_("Chưa gửi duyệt được"))
	elif action == "Thông qua" and not _secretary():
		frappe.throw(_("Chưa cấu hình thư ký hội đồng ở Cài đặt Normcore"))
	elif action == "Ban hành":
		decision_no = (decision_no or "").strip()
		if not decision_no or not effective_date:
			frappe.throw(_("Cần nhập số quyết định ban hành và ngày hiệu lực"))
		doc.decision_no = decision_no
		doc.effective_date = getdate(effective_date)
		doc.needs_review = 0  # FR-LIB-009: ban hành xong là đã rà soát (ASM-021-06)
	elif action == "Từ chối" and not reason:
		frappe.throw(_("Cần nhập lý do từ chối"))
	elif action == "Thu hồi":
		if not reason:
			frappe.throw(_("Cần nhập lý do thu hồi"))
		return _withdraw(doc, reason)

	doc.workflow_state = new_state
	doc.flags.workflow_action = action
	doc.flags.audit_detail = reason or None
	doc.save(ignore_permissions=True)
	doc.add_comment("Workflow", f"{action}: {state} → {new_state}" + (f" — {reason}" if reason else ""))
	_after_action(doc, action, state, new_state, reason)
	return {"workflow_state": new_state}


def _withdraw(doc, reason):
	"""FR-WF-012: Thu hồi đi đường hệ thống như "Đã thay thế" (ASM-008-02): không có transition trong fixture
	Workflow; kiểm vai trò ở `_actor_error`, lý do bắt buộc, ghi sổ sự kiện."""
	state, new_state = doc.workflow_state, approval.WITHDRAWN
	frappe.db.set_value(DT, doc.name, "workflow_state", new_state, update_modified=False)
	audit.log_event("Chuyển trạng thái", DT, doc.name, state, new_state, detail=reason)
	doc.add_comment("Workflow", f"Thu hồi: {state} → {new_state} — {reason}")
	_notify([doc.owner], f"{doc.name}: đã thu hồi — {reason}", doc)
	return {"workflow_state": new_state}


NORM_SET = "NC Norm Set"
REPLACED = "Đã thay thế"


def _procedure_data(name):
	doc = frappe.get_doc(DT, name)
	return {"steps": _rows(doc, "steps"), "resources": _rows(doc, "resources")}


def _flag_norm_sets(doc):
	"""FR-WF-011 (ASM-008-14): gắn cờ "Cần cập nhật" và ghi chú bước thêm, bỏ, đổi cho các bộ định mức dựa trên
	phiên bản cũ hơn của cùng (dịch vụ, khoa), trừ bộ "Đã thay thế". Ghi bằng `db.set_value` (bộ "Đã khóa" chặn
	`save()`); chạy với quyền hệ thống vì người ban hành chỉ có quyền đọc bộ định mức."""
	rows = frappe.get_all(
		NORM_SET,
		{
			"technical_service": doc.technical_service,
			"department": doc.department,
			"status": ["!=", REPLACED],
			"procedure": ["!=", doc.name],
		},
		["name", "procedure"],
	)
	if not rows:
		return 0
	new = _procedure_data(doc.name)
	notes, flagged = {}, 0
	for r in rows:
		if (frappe.db.get_value(DT, r.procedure, "version_no") or 0) >= doc.version_no:
			continue
		if r.procedure not in notes:
			notes[r.procedure] = diff.format_step_note(diff.step_changes(_procedure_data(r.procedure), new))
		note = notes[r.procedure]
		frappe.db.set_value(
			NORM_SET, r.name, {"needs_update": 1, "step_change_note": note}, update_modified=False
		)
		frappe.get_doc(NORM_SET, r.name).add_comment(
			"Info", _("Cần cập nhật do ban hành {0}: {1}").format(doc.name, note)
		)
		flagged += 1
	return flagged


def _after_action(doc, action, from_state, new_state, reason):
	name = doc.name
	if action in ("Gửi duyệt", "Đồng ý", "Thông qua"):
		_notify(_recipients(new_state, doc), f"{name}: {new_state[0].lower()}{new_state[1:]}", doc)
	elif action == "Ban hành":
		if getdate(doc.effective_date) <= getdate(nowdate()):
			supersede_due(for_procedure=name)
		_flag_norm_sets(doc)
		_notify([doc.owner], f"{name}: đã ban hành", doc)
	elif action == "Từ chối":
		level = approval.reject_level(from_state)
		_notify([doc.owner], f"{name}: bị từ chối ở cấp {level} — {reason}", doc)


# ---- xem thông tin duyệt ---------------------------------------------------------------------------------


def _last_reject(name):
	rows = frappe.get_all(
		audit.EVENT,
		{
			"ref_doctype": DT,
			"ref_name": name,
			"event_type": "Chuyển trạng thái",
			"to_state": approval.DRAFT,
			"from_state": ["in", list(approval.PENDING_STATES)],
		},
		["user", "event_time", "detail"],
		order_by="event_time desc, creation desc",
		limit=1,
	)
	if not rows:
		return None
	return {"by": rows[0].user, "at": rows[0].event_time, "reason": rows[0].detail}


def _last_withdraw(name):
	rows = frappe.get_all(
		audit.EVENT,
		{
			"ref_doctype": DT,
			"ref_name": name,
			"event_type": "Chuyển trạng thái",
			"to_state": approval.WITHDRAWN,
		},
		["user", "event_time", "detail"],
		order_by="event_time desc, creation desc",
		limit=1,
	)
	if not rows:
		return None
	return {"by": rows[0].user, "at": rows[0].event_time, "reason": rows[0].detail}


@frappe.whitelist()
def get_review(procedure):
	if not frappe.has_permission(DT, "read", doc=procedure):
		_deny(_("Bạn không có quyền xem quy trình này"))
	doc = frappe.get_doc(DT, procedure)
	user = frappe.session.user
	deviations = [
		{
			"idx": c.idx,
			"relation": c.relation,
			"target_section": c.target_section,
			"target_step_id": c.target_step_id,
			"legal_document": c.legal_document,
			"quote": c.quote,
			"deviation_reason": c.deviation_reason,
		}
		for c in doc.citations
		if c.relation in ("Khác biệt", "Chưa có căn cứ")
	]
	out = {
		"workflow_state": doc.workflow_state,
		"actions": _available_actions(doc, user),
		"is_secretary": bool(user) and user == _secretary(),
		"deviations": deviations,
		"last_reject": _last_reject(doc.name),
		"last_withdraw": _last_withdraw(doc.name),
		"decision_no": doc.decision_no,
		"effective_date": doc.effective_date,
	}
	out.update(_comments_block(doc))
	return out


def _comments_block(doc):
	rows = frappe.get_all(
		COMMENT,
		{"ref_doctype": DT, "ref_name": doc.name},
		[
			"name",
			"owner",
			"creation",
			"target_section",
			"target_step_id",
			"comment",
			"resolved",
			"review_state",
		],
		order_by="creation asc, name asc",
	)
	by_step, by_section, general = {}, {}, []
	for r in rows:
		if r.target_step_id:
			by_step.setdefault(r.target_step_id, []).append(r)
		elif r.target_section:
			by_section.setdefault(r.target_section, []).append(r)
		else:
			general.append(r)
	return {
		"comments_by_step": by_step,
		"comments_by_section": by_section,
		"comments_general": general,
		"open_comments": sum(1 for r in rows if not r.resolved),
	}


@frappe.whitelist()
def add_review_comment(procedure, comment, target_section=None, target_step_id=None):
	"""FR-WF-003: ghi ý kiến gắn phần hoặc mã bước."""
	if not frappe.has_permission(COMMENT, "create") or not frappe.has_permission(DT, "read", doc=procedure):
		_deny(_("Bạn không có quyền ghi ý kiến thẩm định"))
	doc = frappe.get_doc(
		{
			"doctype": COMMENT,
			"ref_doctype": DT,
			"ref_name": procedure,
			"comment": comment,
			"target_section": target_section or None,
			"target_step_id": target_step_id or None,
		}
	)
	doc.insert(ignore_permissions=True)
	return {"name": doc.name}


@frappe.whitelist()
def set_comment_resolved(name, resolved):
	if not frappe.has_permission(COMMENT, "write", doc=name):
		_deny(_("Bạn không có quyền sửa ý kiến thẩm định"))
	doc = frappe.get_doc(COMMENT, name)
	if not frappe.has_permission(DT, "read", doc=doc.ref_name):
		_deny(_("Bạn không có quyền xem quy trình này"))
	doc.resolved = 1 if str(resolved) in ("1", "true", "True") else 0
	doc.save(ignore_permissions=True)
	return {"resolved": doc.resolved}


# ---- tác vụ ngày -----------------------------------------------------------------------------------------


def supersede_due(today=None, for_procedure=None):
	"""FR-WF-006: chuyển "Đã ban hành" → "Đã thay thế" cho bản trước khi bản mới đến ngày hiệu lực."""
	today = getdate(today or nowdate())
	published = frappe.get_all(
		DT,
		{"workflow_state": approval.PUBLISHED},
		["name", "technical_service", "department", "version_no", "effective_date"],
	)
	for r in published:
		r["effective_date"] = getdate(r["effective_date"]) if r["effective_date"] else None
	names = approval.to_supersede(published, today)
	if for_procedure:
		key = {(r["technical_service"], r["department"]) for r in published if r["name"] == for_procedure}
		same = {r["name"] for r in published if (r["technical_service"], r["department"]) in key}
		names = [n for n in names if n in same]
	for name in names:
		frappe.db.set_value(DT, name, "workflow_state", approval.SUPERSEDED, update_modified=False)
		audit.log_event(
			"Chuyển trạng thái", DT, name, approval.PUBLISHED, approval.SUPERSEDED, user="Administrator"
		)
	return len(names)


def _entered_on(name, state, fallback):
	"""Ngày quy trình vào trạng thái chờ hiện tại: sự kiện "Chuyển trạng thái" mới nhất tới `state`."""
	rows = frappe.get_all(
		audit.EVENT,
		{"ref_doctype": DT, "ref_name": name, "event_type": "Chuyển trạng thái", "to_state": state},
		pluck="event_time",
		order_by="event_time desc, creation desc",
		limit=1,
	)
	return getdate(rows[0] if rows else fallback)


def send_approval_reminders(today=None):
	"""FR-WF-013: nhắc người duyệt của cấp có quy trình chờ quá `approval_reminder_days`; mỗi lần vào
	trạng thái nhắc một lần (tiêu đề có ngày vào trạng thái, ASM-007-07). Trả số thông báo tạo."""
	today = getdate(today or nowdate())
	days = frappe.db.get_single_value(SETTINGS, "approval_reminder_days") or DEFAULT_REMINDER_DAYS
	rows = frappe.get_all(
		DT, {"workflow_state": ["in", list(approval.PENDING_STATES)]}, ["name", "workflow_state", "modified"]
	)
	pending = [
		{
			"name": r.name,
			"state": r.workflow_state,
			"entered_on": _entered_on(r.name, r.workflow_state, r.modified),
		}
		for r in rows
	]
	created = 0
	for p in approval.overdue(pending, today, int(days)):
		doc = frappe.get_doc(DT, p["name"])
		subject = f"Nhắc duyệt: {doc.name} chờ ở '{p['state']}' từ {p['entered_on'].strftime('%d/%m/%Y')}"
		created += _notify(_recipients(p["state"], doc), subject, doc)
	return created


def daily_job():
	"""Scheduler hằng ngày (hooks.py): thay thế phiên bản đến ngày hiệu lực, rồi nhắc duyệt quá hạn."""
	supersede_due()
	send_approval_reminders()


# ---- in, xuất tệp (FR-PROC-010, FR-PROC-011) --------------------------------------------------------------

PRINT_FORMAT = "NC Clinical Procedure Standard"
SIGN_STATES = {
	"head": approval.WAIT_HEAD,
	"council": approval.WAIT_COUNCIL,
	"director": approval.WAIT_PUBLISH,
}


def _full_name(user):
	return (frappe.db.get_value("User", user, "full_name") or user) if user else ""


def _signatures(doc):
	"""Người, ngày của bốn cấp từ sổ sự kiện (technical-design 5.3): người soạn = người gửi duyệt gần nhất;
	trưởng khoa = người chuyển khỏi "Chờ trưởng khoa duyệt"; hội đồng = người chuyển khỏi "Chờ hội đồng thẩm
	định"; giám đốc = người ban hành."""
	rows = frappe.get_all(
		audit.EVENT,
		{"ref_doctype": DT, "ref_name": doc.name, "event_type": "Chuyển trạng thái"},
		["user", "event_time", "from_state", "to_state"],
		order_by="event_time asc, creation asc",
	)

	def last(**kw):
		hit = None
		for r in rows:
			if all(r.get(k) == v for k, v in kw.items()):
				hit = r
		return hit

	sigs = {}
	submit = last(from_state=approval.DRAFT, to_state=approval.WAIT_HEAD)
	if submit:
		sigs["drafter"] = submit
	for key, state in (("head", approval.WAIT_HEAD), ("council", approval.WAIT_COUNCIL)):
		ev = last(
			from_state=state, to_state=approval.next_state(state, "Đồng ý" if key == "head" else "Thông qua")
		)
		if ev:
			sigs[key] = ev
	ev = last(from_state=approval.WAIT_PUBLISH, to_state=approval.PUBLISHED)
	if ev:
		sigs["director"] = ev
	return {k: {"user": _full_name(v.user), "date": v.event_time} for k, v in sigs.items()}


def get_print_context(doc):
	"""Ngữ cảnh in cho Print Format Jinja và DOCX (cùng nội dung). `doc` là Document hoặc tên quy trình."""
	if isinstance(doc, str):
		doc = frappe.get_doc(DT, doc)
	data = {
		f: doc.get(f)
		for f in (
			"name",
			"version_no",
			"workflow_state",
			"decision_no",
			"effective_date",
			"overview",
			"indications",
			"contraindications",
			"cautions",
			"preparation_notes",
			"monitoring",
			"references",
		)
	}
	data["steps"] = [r.as_dict() for r in doc.steps]
	data["resources"] = [r.as_dict() for r in doc.resources]
	data["service_name"], data["service_code"] = frappe.db.get_value(
		"NC Technical Service", doc.technical_service, ["service_name", "service_code"]
	) or (doc.technical_service, "")
	data["department_name"] = (
		frappe.db.get_value("NC Department", doc.department, "department_name") or doc.department
	)
	return printing.print_context(data, _signatures(doc))


def _check_print(procedure):
	if not frappe.has_permission(DT, "read", doc=procedure):
		_deny(_("Bạn không có quyền xem quy trình này"))
	return frappe.get_doc(DT, procedure)


def _html(doc):
	"""HTML tự chứa (không tải CSS, ảnh ngoài) từ Print Format mặc định; thêm Letter Head mặc định nếu có.
	Dùng cho PDF để in được cả khi máy chủ không phân giải được tên miền site."""
	fmt = frappe.get_doc("Print Format", PRINT_FORMAT)
	body = frappe.render_template(fmt.html, {"doc": doc})
	head = frappe.db.get_value("Letter Head", {"is_default": 1, "disabled": 0}, "content") or ""
	return f"<!DOCTYPE html><html><head><meta charset='utf-8'></head><body>{head}{body}</body></html>"


def _pdf_bytes(doc):
	from frappe.utils.pdf import get_pdf

	return get_pdf(_html(doc))


def _docx_bytes(doc):
	from normcore.exports.procedure_docx import build_docx

	return build_docx(get_print_context(doc))


def _respond(filename, content):
	frappe.local.response.filename = filename
	frappe.local.response.filecontent = content
	frappe.local.response.type = "download"


@frappe.whitelist()
def download_pdf(procedure):
	doc = _check_print(procedure)
	content = _pdf_bytes(doc)
	audit.log_export("PDF", DT, doc.name, f"{doc.name}.pdf")
	_respond(f"{doc.name}.pdf", content)


@frappe.whitelist()
def download_docx(procedure):
	doc = _check_print(procedure)
	try:
		content = _docx_bytes(doc)
	except ImportError:
		frappe.throw(_("Máy chủ chưa cài thư viện python-docx, chưa xuất được DOCX"))
	audit.log_export("DOCX", DT, doc.name, f"{doc.name}.docx")
	_respond(f"{doc.name}.docx", content)
