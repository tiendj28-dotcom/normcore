"""API kịch bản điều chỉnh và yêu cầu sửa quy trình (FEAT-029, SCR-DSK-026).

FR-ADJ-006, 007, 009; UC-014 bước 4 đến 6, 4b; UC-007 1c. Giả định ASM-029-01..17
(docs/decisions/assumptions/FEAT-029.md). Kiểm quyền tường minh trong từng hàm; máy chủ ghi bằng
`ignore_permissions` sau khi đã kiểm quyền quyết định (ASM-029-17). Không công thức mới: kịch bản tính lại
bằng `benchmark/scenario.py` → `snapshot.recompute`.
"""

from decimal import Decimal

import frappe
from frappe import _

from normcore.api import costing as costing_api
from normcore.api import price_compare as pc
from normcore.api import scenario_norm as norm_api
from normcore.benchmark import scenario as sc_logic
from normcore.core import notify, permissions
from normcore.costing import snapshot
from normcore.nc_costing.doctype.nc_costing_run import writer

RUN, COST, ADJ, PCR, PROC = (
	"NC Costing Run",
	"NC Service Cost",
	"NC Adjustment Suggestion",
	"NC Procedure Change Request",
	"NC Clinical Procedure",
)
FORWARDED = "Đã chuyển yêu cầu sửa quy trình"
PUBLISHED = "Đã ban hành"
RECEIVE, REJECT, DONE = "Tiếp nhận", "Từ chối", "Đã thực hiện"
INPUT_COPY = (
	"fiscal_year",
	"costing_date",
	"parameter_set",
	"accounting_import",
	"price_category",
	"volume_scenario",
	"compliance_allocation_mode",
)
CHANGE_COLS = (
	"technical_service",
	"change_type",
	"target_ref",
	"field",
	"old_value",
	"new_value",
	"source_suggestion",
)


# --- đọc ---------------------------------------------------------------------------------


def _fmt(d) -> str | None:
	if d is None:
		return None
	return format(Decimal(d).normalize(), "f")


def _latest_scenario(run_name):
	rows = frappe.get_all(
		RUN, {"based_on_run": run_name}, pluck="name", order_by="creation desc, name desc", limit=1
	)
	return rows[0] if rows else None


@frappe.whitelist()
def get_open_scenario(run):
	"""Kịch bản đang mở của lần tính gốc (ASM-029-01) hoặc None."""
	origin, _tol = pc._run_info(run)
	name = _latest_scenario(origin.name)
	can_create = bool(frappe.has_permission(RUN, "create")) and not origin.based_on_run
	if not name:
		return None
	scenario = frappe.get_doc(RUN, name)
	base = {
		(c.technical_service, c.department): c.calculated_price
		for c in frappe.get_list(
			COST,
			{"costing_run": origin.name},
			["technical_service", "department", "calculated_price"],
			limit_page_length=0,
		)
	}
	names = {
		s.name: s.service_name
		for s in frappe.get_all("NC Technical Service", ["name", "service_name"], limit_page_length=0)
	}
	rows = []
	for c in frappe.get_list(
		COST,
		{"costing_run": name},
		["technical_service", "department", "calculated_price"],
		limit_page_length=0,
	):
		b = base.get((c.technical_service, c.department))
		diff = None if b is None else Decimal(str(c.calculated_price or 0)) - Decimal(str(b or 0))
		pct = None if not b else round(float(diff) / float(b) * 100, 2)
		rows.append(
			{
				"technical_service": c.technical_service,
				"department": c.department,
				"service_name": names.get(c.technical_service),
				"base_price": b,
				"scenario_price": c.calculated_price,
				"diff": None if diff is None else float(diff),
				"diff_pct": pct,
			}
		)
	rows.sort(key=lambda r: (r["technical_service"], r["department"] or ""))
	changes = [{f: r.get(f) for f in CHANGE_COLS} for r in scenario.scenario_changes]
	warnings = [
		w
		for w in ((scenario.run_warnings or "") + "\n" + (scenario.allocation_warnings or "")).split("\n")
		if w
	]
	return {
		"name": scenario.name,
		"title": scenario.title,
		"status": scenario.status,
		"created_on": scenario.creation,
		"change_count": len(changes),
		"changes": changes,
		"rows": rows,
		"warnings": warnings,
		"can_create": can_create,
	}


# --- ghi kịch bản -----------------------------------------------------------------------


def _new_scenario(origin):
	if origin.based_on_run:
		frappe.throw(_("Kịch bản không lồng được: {0} đã là kịch bản").format(origin.name))
	if origin.status not in pc.RUN_STATUSES:
		frappe.throw(_("Lần tính chưa có kết quả"))
	doc = frappe.new_doc(RUN)
	doc.update({f: origin.get(f) for f in INPUT_COPY})
	doc.title = _("Kịch bản của {0}").format(origin.title)
	doc.status = "Nháp"
	doc.based_on_run = origin.name
	for r in origin.scope_departments:
		doc.append("scope_departments", {"department": r.department})
	for r in origin.scope_services:
		doc.append("scope_services", {"technical_service": r.technical_service})
	doc.flags.scenario_write = True
	doc.insert(ignore_permissions=True)
	return doc


@frappe.whitelist()
def create_scenario(run):
	"""UC-014 bước 6: bắt đầu kịch bản mới (chỉ NC Finance, ASM-029-17)."""
	if not frappe.has_permission(RUN, "create"):
		frappe.throw(_("Bạn không có quyền tạo kịch bản điều chỉnh"), frappe.PermissionError)
	origin = frappe.get_doc(RUN, run)
	return {"name": _new_scenario(origin).name}


def _open_or_create(origin):
	name = _latest_scenario(origin.name)
	if name:
		doc = frappe.get_doc(RUN, name)
		doc.flags.scenario_write = True
		return doc
	return _new_scenario(origin)


def _changes_of(scenario) -> list:
	"""Thay đổi đã ghi của kịch bản; khoa của "Dòng định mức" lấy qua gợi ý nguồn (ASM-029-06)."""
	out = []
	for r in scenario.scenario_changes:
		dept = None
		if r.change_type == sc_logic.NORM_LINE and r.source_suggestion:
			cost = frappe.db.get_value(ADJ, r.source_suggestion, "service_cost")
			dept = cost and frappe.db.get_value(COST, cost, "department")
		out.append(
			sc_logic.Change(
				r.change_type,
				r.target_ref,
				r.field,
				Decimal(r.new_value),
				Decimal(r.old_value) if r.old_value not in (None, "") else None,
				r.technical_service or None,
				dept,
			)
		)
	return out


def _write_changes(scenario, changes, sources):
	scenario.set("scenario_changes", [])
	for c in changes:
		scenario.append(
			"scenario_changes",
			{
				"technical_service": c.service,
				"change_type": c.change_type,
				"target_ref": c.target_ref,
				"field": c.field,
				"old_value": _fmt(c.old_value),
				"new_value": _fmt(c.new_value),
				"source_suggestion": sources.get(c.key),
			},
		)
	scenario.flags.scenario_write = True
	scenario.save(ignore_permissions=True)


def _stale_warning(origin, base) -> list:
	"""Lần gốc "Đã tính" mà dữ liệu đã đổi sau lần tính: cảnh báo (ASM-029-02)."""
	if origin.status != "Đã tính":
		return []
	stored = {
		(c.technical_service, c.department): Decimal(str(c.full_cost or 0))
		for c in frappe.get_all(
			COST, {"costing_run": origin.name}, ["technical_service", "department", "full_cost"]
		)
	}
	cents = Decimal("0.01")
	changed = [
		r.service
		for r in snapshot.recompute(base).results
		if (r.service, r.department) in stored
		and abs(stored[(r.service, r.department)] - Decimal(str(r.price.full_cost))) >= cents
	]
	if not changed:
		return []
	return [_("Dữ liệu đầu vào đã đổi sau lần tính gốc; kịch bản tính trên dữ liệu hiện tại")]


def _recompute(scenario, origin):
	"""Tính lại toàn bộ kịch bản từ ảnh chụp lần gốc + mọi thay đổi (ASM-029-02, 16)."""
	base = costing_api._snapshot_for(origin)
	changes = _changes_of(scenario)
	codes = {c.target_ref for c in changes if c.change_type == sc_logic.EQUIPMENT}
	equipment = pc._equipment_facts(codes, origin)
	try:
		rec = sc_logic.recompute(base, changes, equipment)
	except sc_logic.InvalidChange as e:
		frappe.throw(str(e))
	for name in frappe.get_all(COST, {"costing_run": scenario.name}, pluck="name"):
		frappe.delete_doc(COST, name, force=True, ignore_permissions=True)
	writer.write_results(scenario, rec.results)
	scenario.db_set(
		{
			"run_warnings": "\n".join(_stale_warning(origin, base)) or None,
			"allocation_warnings": "\n".join(rec.warnings) or None,
			"status": "Đã tính",
			"progress": 100,
		}
	)
	return rec


# --- yêu cầu sửa quy trình ---------------------------------------------------------------


def _target_procedure(service, department, norm_set_procedure=None):
	"""ASM-029-13: quy trình "Đã ban hành" mới nhất của (dịch vụ, khoa); không có thì quy trình của bộ định mức."""
	name = frappe.db.get_value(
		PROC,
		{"technical_service": service, "department": department, "workflow_state": PUBLISHED},
		"name",
		order_by="version_no desc",
	)
	if not name:
		name = frappe.db.get_value(
			"NC Norm Set",
			{"technical_service": service, "department": department, "status": "Đã khóa"},
			"procedure",
			order_by="version_no desc",
		)
	if not name:
		frappe.throw(_("Dịch vụ chưa có quy trình để yêu cầu sửa đổi"))
	return name


def _create_request(cost, text, suggestion):
	procedure = _target_procedure(cost.technical_service, cost.department)
	doc = frappe.get_doc(
		{
			"doctype": PCR,
			"procedure": procedure,
			"requested_by": frappe.session.user,
			"source_suggestion": suggestion,
			"proposed_change": text,
			"status": "Mới",
		}
	)
	doc.flags.pcr_write = True
	doc.insert(ignore_permissions=True)
	dept = frappe.db.get_value(PROC, procedure, "department")
	head = frappe.db.get_value("NC Department", dept, "head_user")
	notified, warnings = [], []
	if head and notify.notify(
		[head],
		_("Yêu cầu sửa đổi quy trình {0} từ Bàn so sánh giá").format(procedure),
		PCR,
		doc.name,
	):
		notified.append(head)
	if not head:
		warnings.append(_("Khoa {0} chưa có trưởng khoa để nhận thông báo").format(dept))
	return doc, notified, warnings


def _decide(adj, status, reason=None):
	adj.status = status
	adj.decision_reason = (reason or "").strip() or None
	adj.decided_by = frappe.session.user
	adj.decided_on = frappe.utils.now_datetime()
	adj.flags.adj_decision = True
	adj.save(ignore_permissions=True)


def _accept(adj, cost, note=None) -> dict:
	"""FR-ADJ-006, 007, 009: một giao dịch; lỗi nào cũng hoàn tác toàn bộ, gợi ý giữ "Mới"."""
	origin = frappe.get_doc(RUN, cost.costing_run)
	if origin.based_on_run:
		frappe.throw(_("Gợi ý thuộc kịch bản; mở lần tính gốc để chấp nhận"))
	frappe.db.savepoint("nc_accept_suggestion")
	try:
		return _accept_inner(adj, cost, origin, note)
	except Exception:
		frappe.db.rollback(save_point="nc_accept_suggestion")
		raise


def _accept_inner(adj, cost, origin, note) -> dict:
	try:
		kind = sc_logic.change_for(
			adj.rule_code,
			adj.target_ref,
			adj.current_value,
			adj.suggested_value,
			cost.technical_service,
			cost.department,
		)
	except sc_logic.InvalidChange as e:
		frappe.throw(str(e))
	out = {"suggestion": adj.name, "warnings": []}
	if kind is sc_logic.PROCEDURE:
		text = sc_logic.proposal_text(
			adj.rule_code,
			adj.target_ref,
			adj.current_value,
			adj.suggested_value,
			pc._suggestion_view(adj.as_dict())["text"],
			note,
		)
		req, notified, warnings = _create_request(cost, text, adj.name)
		_decide(adj, FORWARDED, note)
		return {
			**out,
			"outcome": "procedure_request",
			"change_request": req.name,
			"notified": notified,
			"warnings": warnings,
		}
	if kind is None:
		_decide(adj, "Chấp nhận", note)
		out["warnings"].append(
			_("Gợi ý không có giá trị để áp vào kịch bản; cập nhật dữ liệu nguồn rồi tính lần mới")
		)
		return {**out, "outcome": "decision_only"}
	scenario = _open_or_create(origin)
	current = _changes_of(scenario)
	sources = {c.key: r.source_suggestion for c, r in zip(current, scenario.scenario_changes, strict=True)}
	merged = sc_logic.merge(current, kind)
	sources[kind.key] = adj.name
	_write_changes(scenario, merged, sources)
	_recompute(scenario, origin)
	if kind.change_type == sc_logic.NORM_LINE:
		res = norm_api.version_for_adjustment(
			cost.technical_service,
			cost.department,
			None,
			kind.target_ref,
			kind.field,
			float(kind.new_value),
			_("Thay đổi từ kịch bản {0}, gợi ý {1}: {2} {3} {4} → {5}").format(
				scenario.name,
				adj.name,
				kind.target_ref,
				kind.field,
				_fmt(kind.old_value),
				_fmt(kind.new_value),
			),
		)
		out.update(norm_set=res["name"], norm_set_created=res["created"])
	_decide(adj, "Chấp nhận", note)
	price = frappe.db.get_value(
		COST,
		{
			"costing_run": scenario.name,
			"technical_service": cost.technical_service,
			"department": cost.department,
		},
		"calculated_price",
	)
	return {**out, "outcome": "scenario", "scenario": scenario.name, "scenario_price": price}


@frappe.whitelist()
def accept_suggestion(name, note=None):
	"""UC-014 bước 4, 4b, 5: chấp nhận một gợi ý "Mới" (kịch bản, yêu cầu sửa quy trình hoặc chỉ ghi quyết định)."""
	adj = frappe.get_doc(ADJ, name)
	cost = frappe.get_doc(COST, adj.service_cost)
	if not pc._can_decide(cost):
		frappe.throw(_("Bạn không có quyền quyết định gợi ý này"), frappe.PermissionError)
	if adj.status != "Mới":
		frappe.throw(_("Gợi ý đã có quyết định"))
	return _accept(adj, cost, note)


@frappe.whitelist()
def request_procedure_change(service_cost, proposed_change, reason):
	"""FR-ADJ-007 vế 2 (ASM-029-14): người dùng đề xuất đổi bước hoặc nguồn lực; tạo yêu cầu gửi khoa chủ trì."""
	cost = frappe.get_doc(COST, service_cost)
	if not pc._can_decide(cost):
		frappe.throw(_("Bạn không có quyền đề xuất sửa quy trình cho dịch vụ này"), frappe.PermissionError)
	if not (proposed_change or "").strip() or not (reason or "").strip():
		frappe.throw(_("Nhập đề xuất thay đổi và lý do"))
	if frappe.db.get_value(RUN, cost.costing_run, "based_on_run"):
		frappe.throw(_("Gợi ý thuộc kịch bản; mở lần tính gốc để chấp nhận"))
	text = f"{proposed_change.strip()}\n{_('Lý do')}: {reason.strip()}"
	req, notified, warnings = _create_request(cost, text, None)
	return {"change_request": req.name, "notified": notified, "warnings": warnings}


# --- xử lý yêu cầu (trưởng khoa) ----------------------------------------------------------


def _is_head_of(department) -> bool:
	user = frappe.session.user
	if user == "Administrator":
		return True
	return "NC Department Head" in frappe.get_roles(user) and department in permissions.get_user_departments(
		user
	)


def _procedure_info(req):
	return frappe.db.get_value(
		PROC, req.procedure, ["department", "technical_service", "version_no"], as_dict=True
	)


@frappe.whitelist()
def change_request_actions(name):
	"""Hành động hợp lệ cho người gọi: Tiếp nhận / Từ chối / Đã thực hiện (bảng 2.3)."""
	req = frappe.get_doc(PCR, name)
	frappe.has_permission(PCR, "read", doc=req, throw=True)
	if not _is_head_of(_procedure_info(req).department):
		return []
	return {
		"Mới": [RECEIVE, REJECT],
		"Đã tiếp nhận": [REJECT, DONE],
	}.get(req.status, [])


def _set_status(req, status):
	req.status = status
	req.flags.pcr_write = True
	req.save(ignore_permissions=True)


@frappe.whitelist()
def act_on_change_request(name, action, reason=None):
	"""FR-ADJ-007, FR-WF-009, UC-007 1c: Trưởng khoa của khoa quy trình tiếp nhận, từ chối, đánh dấu đã thực hiện."""
	req = frappe.get_doc(PCR, name)
	info = _procedure_info(req)
	if not _is_head_of(info.department):
		frappe.throw(_("Chỉ trưởng khoa của khoa chủ trì xử lý yêu cầu này"), frappe.PermissionError)
	if action not in (RECEIVE, REJECT, DONE):
		frappe.throw(_("Hành động phải là Tiếp nhận, Từ chối hoặc Đã thực hiện"))
	out = {"name": req.name}
	if action == RECEIVE:
		if req.status != "Mới":
			frappe.throw(_("Chỉ tiếp nhận được yêu cầu ở trạng thái Mới"))
		from normcore.api import procedure as procedure_api

		rev = procedure_api.create_revision(req.procedure)
		frappe.get_doc(PROC, rev["name"]).add_comment(
			"Info",
			_("Yêu cầu sửa đổi từ Bàn so sánh giá {0}: {1}").format(req.name, req.proposed_change),
		)
		_set_status(req, "Đã tiếp nhận")
		out["revision"] = rev["name"]
	elif action == REJECT:
		if req.status not in ("Mới", "Đã tiếp nhận"):
			frappe.throw(_("Yêu cầu đã xử lý xong"))
		if not (reason or "").strip():
			frappe.throw(_("Từ chối yêu cầu phải nêu lý do"))
		req.add_comment("Comment", reason.strip())
		_set_status(req, "Từ chối")
		notify.notify(
			[req.requested_by], _("Yêu cầu sửa quy trình {0} bị từ chối").format(req.name), PCR, req.name
		)
	else:
		if req.status != "Đã tiếp nhận":
			frappe.throw(_("Chỉ đánh dấu Đã thực hiện được yêu cầu đã tiếp nhận"))
		newer = frappe.db.exists(
			PROC,
			{
				"technical_service": info.technical_service,
				"department": info.department,
				"workflow_state": PUBLISHED,
				"version_no": [">", info.version_no],
			},
		)
		if not newer:
			frappe.throw(_("Phiên bản sửa đổi chưa ban hành"))
		_set_status(req, "Đã thực hiện")
	out["status"] = req.status
	return out
