"""API đề xuất liên kết định mức của AI (FEAT-025, FR-AI-007, UC-009 bước 3; AMD-025-02).

Tách khỏi `api/norm.py` (giữ như develop). Dùng lại các hàm tiện ích của `api/norm.py`, không sửa tệp đó."""

import frappe
from frappe import _
from frappe.utils import cint

from normcore.ai import gateway, guard
from normcore.api.norm import (
	DRAFT,
	NS,
	_dict,
	_label,
	_line,
	_load,
	_need_draft,
	_need_role,
)
from normcore.norm import ai_link
from normcore.norm.init_from_procedure import RESOURCE_DOCTYPE_BY_COMPONENT

LINK_JOB_KEY = "normcore:ai_link:{}"
LINK_JOB_TTL = 3600


def link_set(job_id, **state):
	frappe.cache().set_value(LINK_JOB_KEY.format(job_id), state, expires_in_sec=LINK_JOB_TTL)
	frappe.publish_realtime(
		"normcore_ai_link", {"job_id": job_id, "status": state.get("status")}, user=state.get("user")
	)


def start_link_job(ns):
	job_id = frappe.generate_hash(length=16)
	link_set(job_id, status="queued", user=frappe.session.user)
	frappe.enqueue(
		"normcore.api.norm_link.run_link_suggestion",
		queue="long",
		timeout=gateway.get_settings().timeout_seconds + 60,
		now=bool(frappe.flags.in_test),
		enqueue_after_commit=True,
		link_job=job_id,  # `job_id` là tham số của frappe.enqueue, không tới hàm
		norm_set=ns.name,
		user=frappe.session.user,
	)
	return job_id


@frappe.whitelist()
def start_link_suggestion(norm_set):
	ns = _load(norm_set, "write")
	_need_draft(ns)
	_need_role("confirm_line")  # người soạn: Clinician / Dept Head (data-model mục 4)
	gateway.ensure_enabled()
	if not ai_link.pending_lines([_dict(r) for r in ns.lines]):
		return {"job_id": None, "message": _("Không có dòng nào cần đề xuất")}
	return {"job_id": start_link_job(ns)}


def _candidates(doctype):
	"""Ứng viên của một danh mục, dựng ở máy chủ và qua guard (FR-AI-011)."""
	if doctype == "NC Item":
		rows = frappe.get_all(
			"NC Item",
			filters={"is_active": 1, "item_type": ["not in", ["Chất chuẩn", "Vật liệu nội kiểm"]]},
			fields=["item_code", "item_name", "uom"],
			order_by="item_code",
		)
		out = []
		for r in rows:
			src = guard.build_source("NC Item", r)
			out.append(
				{"doctype": doctype, "name": src["item_code"], "label": src["item_name"], "uom": src["uom"]}
			)
		return out
	rows = frappe.get_all(
		"NC Equipment", fields=["equipment_code", "equipment_name"], order_by="equipment_code"
	)
	out = []
	for r in rows:
		src = guard.build_source("NC Equipment", r)
		out.append(
			{"doctype": doctype, "name": src["equipment_code"], "label": src["equipment_name"], "uom": None}
		)
	return out


@frappe.whitelist()
def run_link_suggestion(link_job, norm_set, user):
	"""Tác vụ nền (TD 3.5): lọc ứng viên bằng quy tắc, AI chọn trong danh sách, ghi `ai_suggested`. Không ném lỗi."""
	previous = frappe.session.user
	frappe.set_user(user)
	try:
		link_set(link_job, status="running", user=user)
		ns = frappe.get_doc(NS, norm_set)
		if ns.status != DRAFT:
			return link_set(link_job, status="done", user=user, suggested=0, rejected=0)
		pending = ai_link.pending_lines([_dict(r) for r in ns.lines])
		proc = frappe.get_doc("NC Clinical Procedure", ns.procedure)
		by_row = {r.resource_row_id: r.as_dict() for r in proc.resources}
		pool = {}
		offered = {}
		for ln in pending:
			res = by_row.get(ln["procedure_resource_row"])
			if not res:
				continue
			cands = []
			for dt in ai_link.pools_for(res.get("resource_type")):
				if dt not in pool:
					pool[dt] = _candidates(dt)
				cands += pool[dt]
			short = ai_link.shortlist(res.get("resource_text"), cands)
			if short:
				offered[ln["procedure_resource_row"]] = short
		variables = ai_link.request_variables(pending, by_row, offered)
		if not variables["lines"]:
			return link_set(link_job, status="done", user=user, suggested=0, rejected=0)
		from normcore.ai.prompts_install import ensure_suggest_norm_link_v2

		ensure_suggest_norm_link_v2()
		holder = {}

		def post(data):
			holder["accepted"], rejected = ai_link.parse_suggestions(data, offered)
			return data, rejected

		res = gateway.complete(
			"SUGGEST_NORM_LINK",
			"SUGGEST_NORM_LINK",
			variables,
			[],
			ref_doctype=NS,
			ref_name=ns.name,
			postprocess=post,
		)
		if not res.ok:
			return link_set(link_job, status="failed", user=user, error=res.error, log=res.log_name)
		ns.reload()  # người dùng có thể đã sửa trong lúc chờ
		done = ai_link.apply_suggestions(ns.lines, holder["accepted"])
		if done:
			ns.flags.norm_action = "ai_link"
			ns.save()
		rejected = frappe.db.get_value("NC AI Log", res.log_name, "rejected_citations") or 0
		link_set(link_job, status="done", user=user, suggested=len(done), rejected=rejected, log=res.log_name)
	except Exception as e:  # không để tác vụ nền ném lỗi; người gọi đọc trạng thái từ cache
		link_set(link_job, status="failed", user=user, error=f"{type(e).__name__}: {e}")
	finally:
		frappe.set_user(previous)


@frappe.whitelist()
def get_link_suggestion_status(job_id):
	state = frappe.cache().get_value(LINK_JOB_KEY.format(job_id))
	if not state:
		return {"status": "unknown"}
	if state.get("user") != frappe.session.user and frappe.session.user != "Administrator":
		frappe.throw(_("Bạn không có quyền xem tiến độ này"), frappe.PermissionError)
	out = {k: state.get(k) for k in ("status", "suggested", "rejected") if k in state}
	if state.get("error"):
		out["message"] = state["error"]
	return out


def _link_rows_proc_type(ns, row):
	return frappe.db.get_value(
		"NC Procedure Resource",
		{"parent": ns.procedure, "resource_row_id": row.procedure_resource_row},
		"resource_type",
	)


@frappe.whitelist()
def accept_link_suggestions(norm_set, line_ids=None, all=0):
	ns = _load(norm_set, "write")
	_need_draft(ns)
	_need_role("confirm_line")
	if cint(all):
		rows = list(ns.lines)
	else:
		ids = frappe.parse_json(line_ids) if isinstance(line_ids, str) else (line_ids or [])
		rows = [_line(ns, i) for i in ids]
	for row in rows:
		if cint(row.ai_suggested):
			row.ai_suggested, row.ai_confidence = 0, 0
	ns.flags.norm_action = "ai_link"
	ns.save()
	return list_link_suggestions(ns.name)


@frappe.whitelist()
def reject_link_suggestion(norm_set, line_id):
	ns = _load(norm_set, "write")
	_need_draft(ns)
	_need_role("confirm_line")
	row = _line(ns, line_id)
	if not cint(row.ai_suggested):
		frappe.throw(_("Dòng {0} không còn là đề xuất").format(line_id))
	component = ai_link.original_component(_link_rows_proc_type(ns, row))
	row.resource = None
	row.component = component
	row.resource_doctype = RESOURCE_DOCTYPE_BY_COMPONENT[component]
	row.ai_suggested, row.ai_confidence = 0, 0
	ns.flags.norm_action = "ai_link"
	ns.save()
	return list_link_suggestions(ns.name)


@frappe.whitelist()
def list_link_suggestions(norm_set):
	"""Các dòng đề xuất chưa xử lý, kèm cờ quyền (đọc được bộ là xem được; Auditor không có nút ghi)."""
	ns = _load(norm_set)
	by_row = {
		r.resource_row_id: r.resource_text
		for r in frappe.get_doc("NC Clinical Procedure", ns.procedure).resources
	}
	labels = {}
	rows = []
	for r in ns.lines:
		if not cint(r.ai_suggested):
			continue
		rows.append(
			{
				"line_id": r.line_id,
				"step_id": r.step_id,
				"component": r.component,
				"resource_doctype": r.resource_doctype,
				"resource": r.resource,
				"resource_label": _label(r.resource_doctype, r.resource, labels),
				"ai_confidence": cint(r.ai_confidence),
				"resource_text": by_row.get(r.procedure_resource_row),
			}
		)
	can_edit = bool(
		ns.status == DRAFT
		and frappe.has_permission(NS, "write", doc=ns)
		and set(("NC Clinician", "NC Department Head")) & set(frappe.get_roles())
	)
	return {
		"norm_set": ns.name,
		"lines": rows,
		"can_edit": can_edit,
		"ai_enabled": bool(gateway.is_enabled()),
	}
