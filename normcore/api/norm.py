"""API bộ định mức (FEAT-012; UC-009; FR-NORM-001..014, 016). Logic nghiệp vụ ở normcore.norm và
normcore.costing.provisional (hàm thuần); ở đây chỉ nạp dữ liệu, kiểm quyền và lưu."""

import json
from decimal import Decimal

import frappe
from frappe import _
from frappe.utils import cint, getdate, now_datetime, today

from normcore.costing import engine, pricing, qc_plans, resources
from normcore.costing import provisional as prov
from normcore.nc_costing.doctype.nc_norm_set import nc_norm_set as ctl
from normcore.norm import copy as norm_copy
from normcore.norm import templates, validation, workflow
from normcore.norm.init_from_procedure import RESOURCE_DOCTYPE_BY_COMPONENT

NS = "NC Norm Set"
DRAFT, CONFIRMED, LOCKED = workflow.DRAFT, workflow.CONFIRMED, workflow.LOCKED
# Trường người dùng được nhập qua save_line (không gồm mã dòng, dòng gốc, đề xuất AI, xác nhận)
SAVE_FIELDS = tuple(
	f for f in ctl.LINE_INPUTS if f not in ("line_id", "procedure_resource_row", "ai_suggested")
)
NO_PRICE = "Chưa có đơn giá"
DEFERRED = "Tính ở lần tính giá"  # ASM-034-22
# Trường tên hiển thị của từng DocType nguồn lực; đọc ở máy chủ nên người dùng không cần quyền đọc DocType đó
NAME_FIELD = {
	"NC Job Title": "job_title_name",
	"NC Item": "item_name",
	"NC Equipment": "equipment_name",
	"NC Room": "room_name",
}


# ---------------------------------------------------------------- tiện ích


def _load(name, perm="read"):
	ns = frappe.get_doc(NS, name)
	frappe.has_permission(NS, perm, doc=ns, throw=True)
	return ns


def _need_role(action):
	allowed = workflow.ROLE_OF_ACTION[action]
	if not set(allowed) & set(frappe.get_roles()):
		frappe.throw(_("Bạn không có quyền thực hiện thao tác này"), frappe.PermissionError)


def _need_draft(ns):
	if ns.status != DRAFT:
		frappe.throw(_("Bộ định mức ở trạng thái {0}, không sửa được.").format(ns.status))


def _line(ns, line_id):
	for r in ns.lines:
		if r.line_id == line_id:
			return r
	frappe.throw(_("Không có dòng {0} trong bộ định mức").format(line_id))


def _values(values):
	if isinstance(values, str):
		values = json.loads(values or "{}")
	if not isinstance(values, dict):
		frappe.throw(_("Giá trị dòng không hợp lệ"))
	return dict(values)  # bản sao: Document.append thêm khóa vào dict truyền vào


def _label(doctype, name, cache):
	"""Nhãn "<mã> — <tên>" của nguồn lực, đọc ở máy chủ (không đòi quyền đọc DocType nguồn lực)."""
	if not name:
		return ""
	key = (doctype, name)
	if key not in cache:
		field = NAME_FIELD.get(doctype)
		title = frappe.db.get_value(doctype, name, field) if field and doctype else None
		cache[key] = f"{name} — {title}" if title else name
	return cache[key]


def _dict(row):
	return {f: row.get(f) for f in (*ctl.LINE_INPUTS, *ctl.CONFIRM_FIELDS)}


# ---------------------------------------------------------------- đơn giá tạm tính (ASM-012-11)


class _Prices:
	"""Nạp đơn giá từ dữ liệu của FEAT-009/010/011; thiếu thì trả None (không bịa số)."""

	def __init__(self):
		self.on = getdate(today())
		rows = frappe.get_all("NC Costing Parameter Set", fields=["name", "effective_from"], order_by="name")
		for r in rows:
			r["effective_from"] = getdate(r["effective_from"]) if r["effective_from"] else None
		chosen = validation.effective_parameter_set(rows, self.on)
		self.params = frappe.get_doc("NC Costing Parameter Set", chosen["name"]) if chosen else None
		self.job_rates = (
			{r.job_title: r.rate_per_hour for r in self.params.job_title_rates} if self.params else {}
		)

	def rate(self, line):
		"""-> (rate, headcount_used, reuse, billed_separately) hoặc None."""
		comp, res = line["component"], line["resource"]
		if not res:
			return None
		try:
			if comp == "LABOR":
				r = self.job_rates.get(res)
				return Decimal(str(r)) if r else None
			if comp in ("DRUG", "SUPPLY", "UTILITY"):
				return self._item_rate(res)
			if comp == "EQUIPMENT":
				eq = frappe.get_doc("NC Equipment", res)
				mode = self.params.expired_depreciation_mode if self.params else resources.ZERO
				h = eq.indicative(self.on, mode)["hourly_rate"]
				return Decimal(str(h)) if h is not None else None
			if comp == "INFRA":
				room = frappe.db.get_value(
					"NC Room", res, ["annual_infrastructure_cost", "available_hours_per_year"], as_dict=True
				)
				if not room:
					return None
				return resources.room_hourly_rate(
					room.annual_infrastructure_cost, room.available_hours_per_year
				)
		except (ValueError, frappe.DoesNotExistError):
			return None
		return None

	def _item_rate(self, item):
		meta = frappe.db.get_value(
			"NC Item",
			item,
			["item_type", "norm_units_per_purchase_unit", "reuse_count", "billed_separately"],
			as_dict=True,
		)
		if not meta:
			return None
		if meta.billed_separately:
			return Decimal("0")
		price_rows = frappe.get_all(
			"NC Item Price",
			filters={"item": item},
			fields=[
				"name",
				"unit_price",
				"price_source",
				"document_date",
				"valid_from",
				"valid_to",
				"verification_status",
			],
		)
		records = [
			pricing.PriceRecord(
				name=r.name,
				unit_price=Decimal(str(r.unit_price)),
				price_source=r.price_source,
				document_date=getdate(r.document_date),
				valid_from=getdate(r.valid_from),
				valid_to=getdate(r.valid_to) if r.valid_to else None,
				verified=r.verification_status == "Đã xác minh",
			)
			for r in price_rows
		]
		picked = pricing.select_price(records, self.on)
		if picked is None:
			return None
		units = meta.norm_units_per_purchase_unit
		if not units and meta.item_type not in pricing.NORM_ITEM_TYPES:
			units = 1
		if not units:
			return None
		return pricing.unit_price_per_norm(picked.unit_price, Decimal(str(units)))

	def reuse(self, line):
		if line["component"] not in prov.MATERIAL or not line["resource"]:
			return 1
		return cint(frappe.db.get_value("NC Item", line["resource"], "reuse_count")) or 1


def _deferred(row) -> bool:
	"""ASM-034-22: dòng không phải Theo kết quả, hoặc nhân k, tính ở lần tính giá (FEAT-036), không tạm tính ở lưới."""
	return not row["is_excluded"] and (
		(row.get("cost_level") or "RESULT") != "RESULT" or bool(row.get("apply_k"))
	)


def _cost(prices, row):
	"""Thành tiền tạm tính của một dòng: (rate, amount) hoặc None khi thiếu đơn giá."""
	if row["is_excluded"]:
		return {"rate": None, "amount": "0"}
	rate = prices.rate(row)
	if rate is None:
		return None
	authority = row["authority_qty"] or None  # 0 = không có (ASM-013)
	q = engine.applied_qty(
		Decimal(str(row["hospital_qty"] or 0)), Decimal(str(authority)) if authority else None
	)
	amount = prov.line_amount(
		row["component"],
		q,
		rate,
		headcount=cint(row["headcount"]) or 1,
		wastage_rate=Decimal(str(row["wastage_rate"] or 0)) / 100,
		reuse_count=prices.reuse(row),
	)
	return {"rate": str(rate), "amount": str(amount)}


# ---------------------------------------------------------------- đọc


def _actions(ns):
	roles = set(frappe.get_roles())
	out = []
	can_write = frappe.has_permission(NS, "write", doc=ns)
	if ns.status == DRAFT:
		if can_write:
			out += ["save_line", "delete_line", "save_head"]
			if roles & set(workflow.ROLE_OF_ACTION["confirm_line"]):
				out.append("confirm_line")
			if "NC Department Head" in roles:
				out.append("confirm_set")
	elif ns.status == CONFIRMED and "NC Finance" in roles:
		out += ["return_set", "lock_set"]
	elif ns.status == LOCKED and can_write and frappe.has_permission(NS, "create"):
		out.append("new_version")
	if (
		ns.test_system
		and frappe.has_permission(NS, "create")
		and len(_active_systems(ns.technical_service, ns.department)) > 1
	):
		out.append("copy_norm_set")
	return out  # export_norm_set: ai đọc được bộ thì xuất được, giao diện luôn hiện nút (ASM-034-24)


@frappe.whitelist()
def get_norm_set(name):
	ns = _load(name)
	proc = frappe.get_doc("NC Clinical Procedure", ns.procedure)
	steps = [{"step_id": s.step_id, "step_title": s.step_title, "phase": s.phase} for s in proc.steps]
	rows = [_dict(r) for r in ns.lines]
	dups = validation.duplicates(rows)
	blockers = validation.confirm_blockers(rows) if ns.status == DRAFT else []
	cls = ctl.cls_ctx(ns)
	set_blockers = _set_blockers(ns, rows, cls) if ns.status == DRAFT else []
	cap, cap_src = ctl.effective_wastage_cap()
	prices = _Prices()
	labels = {}
	lines, summary_rows = [], []
	for r in ns.lines:
		d = _dict(r)
		deferred = _deferred(d)
		cost = None if deferred else _cost(prices, d)
		d.update(
			{
				"applied_qty": float(
					engine.applied_qty(
						Decimal(str(d["hospital_qty"] or 0)),
						Decimal(str(d["authority_qty"])) if d["authority_qty"] else None,
					)
				),
				"resource_label": _label(d["resource_doctype"], d["resource"], labels),
				"unlinked": not d["resource"],
				"duplicate_of": dups.get(d["line_id"], []),
				"cost": cost if cost is not None else {"missing": _(DEFERRED if deferred else NO_PRICE)},
				"excluded": bool(d["is_excluded"]),
				"placeholder": validation.is_placeholder(d),
				"qc_conflict": validation.qc_conflict(d, cls),
			}
		)
		lines.append(d)
		key = "service" if d["service_level"] else (d["step_id"] or "service")
		summary_rows.append(
			(key, d["component"], Decimal(cost["amount"]) if cost else None, bool(d["is_excluded"]))
		)
	summary = prov.summarize(summary_rows)
	summary = {
		"by_step_component": {
			k: {c: str(v) for c, v in comps.items()} for k, comps in summary["by_step_component"].items()
		},
		"by_component": {c: str(v) for c, v in summary["by_component"].items()},
		"total": str(summary["total"]),
		"incomplete": summary["incomplete"],
		"parameter_set": prices.params.name if prices.params else None,
	}
	step_keys = [s["step_id"] for s in steps]
	groups = []
	for s in steps:
		g = [x for x in lines if not x["service_level"] and x["step_id"] == s["step_id"]]
		groups.append({"step_id": s["step_id"], "title": s["step_title"], "lines": g, "total": _total(g)})
	general = [x for x in lines if x["service_level"] or x["step_id"] not in step_keys]
	groups.append(
		{"step_id": None, "title": _("Chung cho cả dịch vụ"), "lines": general, "total": _total(general)}
	)
	return {
		"doc": {
			"name": ns.name,
			"technical_service": ns.technical_service,
			"technical_service_name": frappe.db.get_value(
				"NC Technical Service", ns.technical_service, "service_name"
			),
			"department": ns.department,
			"procedure": ns.procedure,
			"version_no": ns.version_no,
			"status": ns.status,
			"previous_version": ns.previous_version,
			"needs_update": cint(ns.needs_update),
			"step_change_note": ns.step_change_note,
			"locked_by": ns.locked_by,
			"locked_on": str(ns.locked_on) if ns.locked_on else None,
			"modified": str(ns.modified),
			"test_system": ns.test_system,
			"test_system_label": _system_label(ns.test_system),
			"tests_per_tube": ns.tests_per_tube,
			"norm_template": ns.norm_template,
			"copied_from": ns.copied_from,
		},
		"steps": steps,
		"groups": groups,
		"summary": summary,
		"wastage_cap": cap,
		"wastage_cap_source": cap_src or _("mặc định"),
		"blockers": blockers,
		"set_blockers": set_blockers,
		"warnings": _warnings(ns, cls),
		"template_items": _template_status(cls["mandatory_items"], rows),
		"actions": _actions(ns),
		"options": {
			"component": list(validation.COMPONENTS),
			"basis": list(validation.BASIS_VALUES),
			"exclude_reason": list(validation.EXCLUDE_REASONS),
			"resource_doctype_by_component": RESOURCE_DOCTYPE_BY_COMPONENT,
			"cost_level": [{"value": v, "label": validation.COST_LEVEL_LABELS[v]} for v in validation.COST_LEVELS],
			"attach_to": list(validation.ATTACH_TO),
		},
		"meta": {
			"has_test_system": bool(frappe.get_meta(NS).has_field("test_system")),
			"is_paraclinical": cls["paraclinical"],
			"other_test_systems": [
				sy
				for sy in _active_systems(ns.technical_service, ns.department)
				if sy["name"] != ns.test_system
			],
		},
	}


def _system_label(test_system):
	if not test_system:
		return None
	equipment = frappe.db.get_value("NC Test System", test_system, "main_equipment")
	return f"{test_system} · {equipment}" if equipment else test_system


def _set_blockers(ns, rows, cls) -> list[str]:
	"""FR-NORM-020, 023, 024, ASM-034-01: lý do cấp bộ chặn "Xác nhận chuyên môn"."""
	ctx = {
		"ts_required": bool(_active_systems(ns.technical_service, ns.department)),
		"qc_items": cls["qc_items"],
		"mandatory_items": cls["mandatory_items"],
	}
	return validation.set_blockers({"test_system": ns.test_system, "tests_per_tube": ns.tests_per_tube}, rows, ctx)


def _warnings(ns, cls) -> list[dict]:
	"""FR-QC-007, TC-CLS-26 (ASM-034-17): cảnh báo thiếu nội kiểm; không chặn khóa."""
	if not ns.test_system:
		return []
	plan = {"iqc_lines": []}
	for name in frappe.get_all("NC QC Plan", {"test_system": ns.test_system}, pluck="name"):
		plan = {"iqc_lines": [r.as_dict() for r in frappe.get_doc("NC QC Plan", name).iqc_lines]}
	msg = qc_plans.missing_iqc_warning(cls["cls_group"], plan, ns.test_system)
	return [{"code": "missing_iqc", "message": _(msg)}] if msg else []


def _template_status(items, rows) -> list[dict]:
	status = {s["item_name"]: s["satisfied"] for s in validation.mandatory_status(items, rows)}
	return [{**it, "satisfied": status[it["item_name"]]} for it in items]


def _total(lines):
	amounts = [x["cost"].get("amount") for x in lines if "amount" in x["cost"]]
	return str(sum((Decimal(a) for a in amounts), Decimal("0"))) if amounts else None


@frappe.whitelist()
def search_resources(norm_set, component, txt=None):
	"""Gợi ý nguồn lực cho ô chọn của lưới: [{"value", "label"}], tối đa 30. Đọc ở máy chủ; người gọi cần quyền
	đọc bộ định mức (không cần quyền đọc DocType nguồn lực, ma trận data-model mục 4)."""
	_load(norm_set)
	doctype = RESOURCE_DOCTYPE_BY_COMPONENT.get(component)
	if not doctype:
		frappe.throw(_("Cấu phần không hợp lệ: {0}").format(component))
	field = NAME_FIELD[doctype]
	txt = (txt or "").strip()
	rows = frappe.get_all(
		doctype,
		or_filters=[["name", "like", f"%{txt}%"], [field, "like", f"%{txt}%"]] if txt else None,
		fields=["name", field],
		order_by="name",
		limit_page_length=30,
	)
	return [
		{"value": r["name"], "label": f"{r['name']} — {r[field]}" if r[field] else r["name"]} for r in rows
	]


# ---------------------------------------------------------------- ghi


def _active_systems(service, department) -> list[dict]:
	"""ASM-034-01: hệ thống "Đang dùng" của (dịch vụ, khoa); đọc ở máy chủ."""
	return frappe.get_all(
		"NC Test System",
		{"technical_service": service, "department": department, "status": "Đang dùng"},
		["name", "main_equipment"],
		order_by="name",
	)


def _open_set(service, department, test_system):
	"""ASM-034-14: bộ đang soạn (Nháp hoặc Đã xác nhận chuyên môn) theo (dịch vụ, khoa, hệ thống)."""
	rows = frappe.get_all(
		NS,
		{
			"technical_service": service,
			"department": department,
			"test_system": test_system or ["is", "not set"],
			"status": ["in", [DRAFT, CONFIRMED]],
		},
		pluck="name",
		order_by="name",
	)
	return rows[0] if rows else None


@frappe.whitelist()
def create_options(procedure):
	"""Hộp chọn hệ thống khi khởi tạo (UC-021): hệ thống đang dùng, có bắt buộc chọn không, mẫu sẽ áp."""
	frappe.has_permission(NS, "create", throw=True)
	proc = frappe.get_doc("NC Clinical Procedure", procedure)
	frappe.has_permission("NC Clinical Procedure", "read", doc=proc, throw=True)
	systems = _active_systems(proc.technical_service, proc.department)
	for sy in systems:
		sy["open_set"] = _open_set(proc.technical_service, proc.department, sy["name"])
	svc = frappe.db.get_value(
		"NC Technical Service", proc.technical_service, ["is_paraclinical", "cls_group"], as_dict=True
	)
	template = None
	if svc and svc.is_paraclinical:
		template = templates.pick_template(
			frappe.get_all("NC Norm Template", fields=["name", "cls_group", "is_active"]), svc.cls_group
		)
	return {"test_systems": systems, "required": bool(systems), "template": template}


@frappe.whitelist()
def create_norm_set(procedure, test_system=None):
	proc = frappe.get_doc("NC Clinical Procedure", procedure)
	systems = _active_systems(proc.technical_service, proc.department)
	if test_system:
		ts = frappe.db.get_value(
			"NC Test System", test_system, ["technical_service", "department"], as_dict=True
		)
		if not ts or (ts.technical_service, ts.department) != (proc.technical_service, proc.department):
			frappe.throw(
				_("Hệ thống xét nghiệm {0} không thuộc dịch vụ/khoa của bộ định mức").format(test_system)
			)
		open_set = _open_set(proc.technical_service, proc.department, test_system)
		if open_set:  # ASM-034-14
			return {"name": open_set, "message": _("Đã có bộ định mức đang soạn: {0}").format(open_set)}
	elif systems:  # ASM-034-01
		frappe.throw(
			_("Dịch vụ có hệ thống xét nghiệm: chọn hệ thống cho bộ định mức ({0})").format(
				", ".join(sy["name"] for sy in systems)
			)
		)
	return {"name": ctl.create_from_procedure(procedure, test_system or None)}


@frappe.whitelist()
def save_line(norm_set, values, line_id=None, allow_duplicate=0):
	ns = _load(norm_set, "write")
	_need_draft(ns)
	values = _values(values)
	unknown = set(values) - set(SAVE_FIELDS)
	if unknown:
		frappe.throw(_("Trường không được nhập: {0}").format(", ".join(sorted(unknown))))
	if line_id:
		row = _line(ns, line_id)
		row.update(values)
	else:
		row = ns.append("lines", values)
	proposed = []
	for r in ns.lines:
		d = _dict(r)
		d["line_id"] = d["line_id"] or "(dòng mới)"
		proposed.append(d)
	touched = row.line_id or "(dòng mới)"
	dup = validation.duplicates(proposed).get(touched)
	if dup and not cint(allow_duplicate):
		ns.reload()
		by_id = {r.line_id: r for r in ns.lines}
		return {
			"saved": False,
			"duplicates": [
				{"line_id": i, "step_id": by_id[i].step_id, "resource": by_id[i].resource} for i in dup
			],
		}
	ns.save()
	return {"saved": True, "norm_set": get_norm_set(ns.name)}


@frappe.whitelist()
def save_head(norm_set, values):
	"""FR-NORM-020: chỉ nhập Số xét nghiệm bình quân trên một ống mẫu (ASM-034-12), bộ "Nháp"."""
	ns = _load(norm_set, "write")
	_need_draft(ns)
	values = _values(values)
	unknown = set(values) - {"tests_per_tube"}
	if unknown:
		frappe.throw(_("Trường không được nhập: {0}").format(", ".join(sorted(unknown))))
	if "tests_per_tube" in values:
		try:
			value = float(values["tests_per_tube"] or 0)
		except (TypeError, ValueError):
			frappe.throw(_("Số xét nghiệm trên một ống mẫu phải là số"))
		if value < 0:
			frappe.throw(_("Số xét nghiệm trên một ống mẫu không được âm"))
		ns.tests_per_tube = value
	ns.save()
	return get_norm_set(ns.name)


@frappe.whitelist()
def delete_line(norm_set, line_id):
	ns = _load(norm_set, "write")
	_need_draft(ns)
	row = _line(ns, line_id)
	if row.procedure_resource_row:  # ASM-012-07
		frappe.throw(_("Dòng lấy từ quy trình không xóa được; đánh dấu Loại trừ nếu không tính"))
	ns.remove(row)
	ns.save()
	return get_norm_set(ns.name)


@frappe.whitelist()
def confirm_line(norm_set, line_id):
	_need_role("confirm_line")
	ns = _load(norm_set, "write")
	_need_draft(ns)
	row = _line(ns, line_id)
	if not row.resource:
		frappe.throw(_("Dòng {0} chưa liên kết danh mục, chưa xác nhận được").format(line_id))
	if cint(row.ai_suggested):
		frappe.throw(_("Dòng {0} còn đề xuất AI, chưa xác nhận được").format(line_id))
	row.confirmed_by = frappe.session.user
	row.confirmed_on = now_datetime()
	ns.flags.norm_action = "confirm_line"
	ns.save()
	return get_norm_set(ns.name)


@frappe.whitelist()
def confirm_set(norm_set):
	_need_role("confirm_set")
	ns = _load(norm_set, "write")
	_need_draft(ns)
	rows = [_dict(r) for r in ns.lines]
	# lỗi cấp bộ (FR-NORM-020, 023, 024, ASM-034-01) đứng trước lỗi dòng, cùng một thông báo (TC-CLS-32)
	messages = [_(m) for m in _set_blockers(ns, rows, ctl.cls_ctx(ns))]
	messages += [f"{b['line_id']}: {', '.join(b['reasons'])}" for b in validation.confirm_blockers(rows)]
	if messages:
		frappe.throw("<br>".join(messages), title=_("Chưa xác nhận chuyên môn được"))
	ns.status = CONFIRMED
	ns.flags.norm_action = "confirm_set"
	ns.save()
	return get_norm_set(ns.name)


@frappe.whitelist()
def return_set(norm_set, reason=None):
	_need_role("return_set")
	ns = _load(norm_set)
	if ns.status != CONFIRMED:
		frappe.throw(_("Chỉ trả lại được bộ định mức Đã xác nhận chuyên môn"))
	reason = (reason or "").strip()
	if not reason:
		frappe.throw(_("Cần nhập lý do trả lại"))
	ns.status = DRAFT
	ns.flags.norm_action = "return_set"
	ns.flags.audit_detail = reason
	ns.save(ignore_permissions=True)
	ns.add_comment("Info", _("Trả lại về Nháp: {0}").format(reason))
	return get_norm_set(ns.name)


@frappe.whitelist()
def lock_set(norm_set):
	ns = _load(norm_set)
	ctl.lock_norm_set(ns)
	return get_norm_set(ns.name)


@frappe.whitelist()
def new_version(norm_set):
	frappe.has_permission(NS, "create", throw=True)
	src = _load(norm_set, "write")
	if src.status != LOCKED:
		frappe.throw(_("Chỉ tạo phiên bản mới từ bộ Đã khóa"))
	open_set = _open_set(src.technical_service, src.department, src.test_system)  # ASM-012-09, 034-14
	if open_set:
		return {"name": open_set, "message": _("Đã có bộ định mức đang soạn: {0}").format(open_set)}
	new = frappe.new_doc(NS)
	new.update(
		{
			"technical_service": src.technical_service,
			"department": src.department,
			"procedure": src.procedure,
			"test_system": src.test_system,
			"tests_per_tube": src.tests_per_tube,
			"norm_template": src.norm_template,
			"version_no": ctl.next_version(src.technical_service, src.department, src.test_system),
			"previous_version": src.name,
			"status": DRAFT,
			"next_line_seq": src.next_line_seq,
		}
	)
	for r in src.lines:  # giữ line_id; bỏ xác nhận (DI-03 giữ nguyên ở lock)
		new.append("lines", {f: r.get(f) for f in ctl.LINE_INPUTS})
	new.flags.from_procedure = True  # dòng giữ chỗ chưa sửa không bị kiểm đầy đủ (ASM-034-05)
	new.insert()
	return {"name": new.name}


@frappe.whitelist()
def copy_norm_set(source, test_system):
	"""FR-NORM-025 (ASM-034-13, 14): bộ Nháp mới cho hệ thống khác của cùng dịch vụ."""
	frappe.has_permission(NS, "create", throw=True)
	src = _load(source)
	if not src.test_system:
		frappe.throw(_("Chỉ sao chép được bộ định mức có hệ thống xét nghiệm"))
	target = frappe.db.get_value(
		"NC Test System",
		test_system,
		["technical_service", "department", "main_equipment", "status"],
		as_dict=True,
	)
	if not target or target.technical_service != src.technical_service:
		frappe.throw(_("Hệ thống xét nghiệm {0} không thuộc dịch vụ của bộ định mức").format(test_system))
	if test_system == src.test_system:
		frappe.throw(_("Chọn hệ thống khác hệ thống của bộ nguồn"))
	if target.status != "Đang dùng":
		frappe.throw(_("Hệ thống xét nghiệm {0} đã ngừng dùng").format(test_system))
	open_set = _open_set(src.technical_service, target.department, test_system)
	if open_set:
		return {"name": open_set, "message": _("Đã có bộ định mức đang soạn: {0}").format(open_set)}
	procs = frappe.get_all(
		"NC Clinical Procedure",
		{
			"technical_service": src.technical_service,
			"department": target.department,
			"workflow_state": ctl.PUBLISHED,
		},
		pluck="name",
		order_by="version_no desc",
		limit_page_length=1,
	)
	if not procs:
		frappe.throw(
			_("Khoa {0} chưa có quy trình đã ban hành của dịch vụ này, chưa sao chép được").format(
				target.department
			)
		)
	proc = frappe.get_doc("NC Clinical Procedure", procs[0])
	src_equipment = frappe.db.get_value("NC Test System", src.test_system, "main_equipment")
	lines, skipped = norm_copy.copy_lines(
		[_dict(r) for r in src.lines],
		{st.step_id for st in proc.steps},
		{r.resource_row_id for r in proc.resources},
		{src_equipment: target.main_equipment} if src_equipment and target.main_equipment else {},
		ctl.qc_items_of(test_system),
		inputs=ctl.LINE_INPUTS,
	)
	new = frappe.new_doc(NS)
	new.update(
		{
			"technical_service": src.technical_service,
			"department": target.department,
			"procedure": proc.name,
			"test_system": test_system,
			"tests_per_tube": src.tests_per_tube,
			"norm_template": src.norm_template,
			"copied_from": src.name,
			"version_no": ctl.next_version(src.technical_service, target.department, test_system),
			"status": DRAFT,
			"next_line_seq": src.next_line_seq,
		}
	)
	if not frappe.has_permission(NS, "create", doc=new):  # phạm vi theo khoa (FR-ACC-003)
		frappe.throw(_("Bạn không có quyền tạo bộ định mức cho khoa này"), frappe.PermissionError)
	for ln in lines:
		new.append("lines", ln)
	new.flags.from_procedure = True  # dòng giữ chỗ chưa sửa không bị kiểm đầy đủ
	new.insert()
	return {"name": new.name, "skipped": skipped}
