"""API AI đề xuất định mức cận lâm sàng từ tài liệu của hãng (FEAT-038, FR-LIB-013, FR-AI-016..018, UC-025).

Dùng chung gateway, mẫu lệnh, nhật ký AI và kiểm trích dẫn của FEAT-023/024/025; không kênh gọi AI mới.
Không sửa `api/norm.py` (AMD-025-02, DEF-025-01). Đề xuất lưu ở NC AI Norm Suggestion, chỉ vào bản ghi đích khi
người có quyền chấp nhận (FR-AI-008)."""

import frappe
from frappe import _
from frappe.utils import cint, now_datetime

from normcore.ai import gateway, guard
from normcore.norm import ai_cls_norm as logic

TS = "NC Test System"
SUG = "NC AI Norm Suggestion"
PENDING, ACCEPTED, REJECTED = "Đề xuất", "Đã chấp nhận", "Đã bỏ"
NO_DOCS = "Chưa có tài liệu của hãng nào gắn với hóa chất, thiết bị của hệ thống này"
JOB_KEY = "normcore:cls_norm_ai:{}"
JOB_TTL = 3600
CATALOG_LABEL = {"NC Item": "Mặt hàng", "NC Equipment": "Thiết bị"}


def job_set(job_id, **state):
	frappe.cache().set_value(JOB_KEY.format(job_id), state, expires_in_sec=JOB_TTL)
	frappe.publish_realtime(
		"normcore_cls_norm_ai", {"job_id": job_id, "status": state.get("status")}, user=state.get("user")
	)


# ---------------------------------------------------------------- phạm vi gửi AI (TD 3.5)


def _latest_norm_lines(test_system):
	"""Dòng của bộ định mức mới nhất (khác "Đã thay thế") của hệ thống (ASM-038-03)."""
	name = frappe.db.get_value(
		"NC Norm Set",
		{"test_system": test_system, "status": ["!=", "Đã thay thế"]},
		"name",
		order_by="version_no desc",
	)
	if not name:
		return []
	return [r.as_dict() for r in frappe.get_doc("NC Norm Set", name).lines]


def _qc_plan(test_system):
	name = frappe.db.get_value("NC QC Plan", {"test_system": test_system}, "name")
	return frappe.get_doc("NC QC Plan", name) if name else None


def _scope(ts):
	"""Khóa nguồn lực của hệ thống, tên tài liệu của hãng trong phạm vi."""
	plan = _qc_plan(ts.name)
	keys = logic.system_resources(
		ts.main_equipment,
		_latest_norm_lines(ts.name),
		[r.as_dict() for r in plan.iqc_lines] if plan else [],
		[r.as_dict() for r in plan.calibration_lines] if plan else [],
	)
	docs = frappe.get_all(
		"NC Legal Document",
		filters={"doc_type": logic.MANUFACTURER_DOC_TYPE},
		fields=["name", "doc_type", "validity_status", "index_status"],
		order_by="name",
	)
	links = frappe.get_all(
		"NC Document Resource Link",
		filters={"parenttype": "NC Legal Document", "parent": ["in", [d.name for d in docs] or [""]]},
		fields=["parent", "linked_doctype", "linked_name"],
	)
	for d in docs:
		d["related_resources"] = [r for r in links if r.parent == d.name]
	return keys, logic.docs_in_scope(docs, keys)


@frappe.whitelist()
def start_cls_norm_suggestion(test_system):
	ts = frappe.get_doc(TS, test_system)
	frappe.has_permission(TS, "write", doc=ts, throw=True)
	frappe.has_permission(SUG, "create", throw=True)
	gateway.ensure_enabled()
	if ts.status == "Ngừng dùng":
		frappe.throw(_("Hệ thống xét nghiệm đã ngừng dùng"))
	_keys, docs = _scope(ts)
	if not docs:
		return {"job_id": None, "message": _(NO_DOCS)}
	job_id = frappe.generate_hash(length=16)
	job_set(job_id, status="queued", user=frappe.session.user)
	frappe.enqueue(
		"normcore.api.cls_norm_ai.run_cls_norm_suggestion",
		queue="long",
		timeout=gateway.get_settings().timeout_seconds + 60,
		now=bool(frappe.flags.in_test),
		enqueue_after_commit=True,
		cls_job=job_id,  # `job_id` là tham số của frappe.enqueue, không tới hàm
		test_system=ts.name,
		user=frappe.session.user,
	)
	return {"job_id": job_id}


def _catalog(codes):
	"""Mã có thật trong toàn danh mục (ASM-038-12): tra CSDL theo mã AI trả, không gửi đi."""
	out = {}
	for code in {c for c in codes if isinstance(c, str) and c}:
		for dt in logic.CATALOG_DOCTYPES:
			if frappe.db.exists(dt, code):
				out[code] = dt
				break
	return out


def _items_equipment(keys):
	items = [
		guard.build_source(
			"NC Item", frappe.db.get_value("NC Item", n, ["item_code", "item_name", "uom"], as_dict=True)
		)
		for dt, n in sorted(keys)
		if dt == "NC Item" and frappe.db.exists("NC Item", n)
	]
	equipment = [
		guard.build_source(
			"NC Equipment",
			frappe.db.get_value("NC Equipment", n, ["equipment_code", "equipment_name"], as_dict=True),
		)
		for dt, n in sorted(keys)
		if dt == "NC Equipment" and frappe.db.exists("NC Equipment", n)
	]
	return items, equipment


def _procedure_source(ts):
	from normcore.api.procedure import _current_procedure

	cur = _current_procedure(ts.technical_service, ts.department)
	if not cur:
		return None  # ASM-038-10: vẫn chạy, chỉ dựa trên tài liệu của hãng
	proc = frappe.get_doc("NC Clinical Procedure", cur.name)
	return guard.build_source("NC Clinical Procedure", proc.as_dict())


def run_cls_norm_suggestion(cls_job, test_system, user):
	"""Tác vụ nền (TD 3.5). Không ném lỗi: người gọi đọc trạng thái từ cache."""
	previous = frappe.session.user
	frappe.set_user(user)
	try:
		job_set(cls_job, status="running", user=user)
		ts = frappe.get_doc(TS, test_system)
		keys, docs = _scope(ts)
		if not docs:
			return job_set(cls_job, status="done", user=user, created=0, message=_(NO_DOCS))
		sections = frappe.get_all(
			"NC Legal Section",
			filters={"legal_document": ["in", docs]},
			fields=["name", "legal_document", "section_no", "heading", "plain_text"],
			order_by="legal_document, name",
		)
		sources = guard.manufacturer_sections(sections, docs)
		items, equipment = _items_equipment(keys)
		service = guard.build_source(
			"NC Technical Service",
			frappe.db.get_value(
				"NC Technical Service", ts.technical_service, ["service_code", "service_name"], as_dict=True
			),
		)
		variables = logic.request_variables(service, _procedure_source(ts), items, equipment)
		from normcore.ai.prompts_install import ensure_suggest_cls_norm_v2

		ensure_suggest_cls_norm_v2()
		holder = {}

		def post(data):
			raw = data.get("suggestions") if isinstance(data, dict) else None
			codes = [s.get("item_code") for s in raw if isinstance(s, dict)] if isinstance(raw, list) else []
			holder["rows"], rejected = logic.parse_suggestions(data, sources, _catalog(codes))
			return data, rejected

		res = gateway.complete(
			"SUGGEST_CLS_NORM",
			"SUGGEST_CLS_NORM",
			variables,
			sources,
			ref_doctype=TS,
			ref_name=ts.name,
			postprocess=post,
		)
		if not res.ok:  # UC-025 3c: không tạo, không đổi gì
			return job_set(cls_job, status="failed", user=user, error=res.error, log=res.log_name)
		_replace_pending(ts, holder["rows"], res.log_name)
		rows = holder["rows"]
		rejected = frappe.db.get_value("NC AI Log", res.log_name, "rejected_citations") or 0
		job_set(
			cls_job,
			status="done",
			user=user,
			created=len(rows),
			unsupported=sum(1 for r in rows if r["relation"] == logic.REL_NONE),
			not_in_catalog=sum(1 for r in rows if r["not_in_catalog"]),
			rejected=rejected,
			log=res.log_name,
		)
	except Exception as e:  # không để tác vụ nền ném lỗi
		job_set(cls_job, status="failed", user=user, error=f"{type(e).__name__}: {e}")
	finally:
		frappe.set_user(previous)


def _replace_pending(ts, rows, log_name):
	"""ASM-038-11: lần chạy thành công đổi các đề xuất chờ cũ sang "Đã bỏ" rồi tạo đề xuất mới."""
	for name in frappe.get_all(SUG, {"test_system": ts.name, "status": PENDING}, pluck="name"):
		old = frappe.get_doc(SUG, name)
		old.status, old.processed_by, old.processed_on = REJECTED, frappe.session.user, now_datetime()
		old.save(ignore_permissions=True)
	for r in rows:
		frappe.get_doc(
			{
				"doctype": SUG,
				"test_system": ts.name,
				"department": ts.department,
				"status": PENDING,
				"ai_log": log_name,
				**r,
			}
		).insert(ignore_permissions=True)  # chỉ tác vụ đề xuất tạo bản ghi


@frappe.whitelist()
def get_cls_norm_suggestion_status(job_id):
	state = frappe.cache().get_value(JOB_KEY.format(job_id))
	if not state:
		return {"status": "unknown"}
	if state.get("user") != frappe.session.user and frappe.session.user != "Administrator":
		frappe.throw(_("Bạn không có quyền xem tiến độ này"), frappe.PermissionError)
	out = {
		k: state.get(k)
		for k in ("status", "created", "unsupported", "not_in_catalog", "rejected")
		if k in state
	}
	if state.get("error"):
		out["message"] = state["error"]
	elif state.get("message"):
		out["message"] = state["message"]
	return out


# ---------------------------------------------------------------- xem


def _can_accept(sug, ts):
	"""Quyền chấp nhận theo bản ghi đích (ASM-038-07). Chỉ đề xuất chờ và đã có trong danh mục."""
	if sug.status != PENDING or sug.not_in_catalog or not sug.resource:
		return False
	kind = sug.suggestion_type
	if kind == logic.TYPE_LABELS["REAGENT_PER_TEST"]:
		name = frappe.db.get_value(
			"NC Norm Set",
			{"test_system": ts.name, "status": ["!=", "Đã thay thế"]},
			"name",
			order_by="version_no desc",
		)
		return bool(
			frappe.has_permission("NC Norm Set", "write", doc=name)
			if name
			else frappe.has_permission("NC Norm Set", "write")
		)
	if kind in (logic.TYPE_LABELS["CALIBRATION_FREQ"], logic.TYPE_LABELS["IQC_FREQ"]):
		plan = frappe.db.get_value("NC QC Plan", {"test_system": ts.name}, "name")
		return bool(
			frappe.has_permission("NC QC Plan", "write", doc=plan)
			if plan
			else frappe.has_permission("NC QC Plan", "write")
		)
	return bool(frappe.has_permission("NC Item", "write"))


def _row(sug, ts, can_edit, cache):
	sec = None
	if sug.legal_section:
		if sug.legal_section not in cache:
			s = frappe.db.get_value(
				"NC Legal Section", sug.legal_section, ["legal_document", "section_no"], as_dict=True
			)
			d = (
				frappe.db.get_value(
					"NC Legal Document", s.legal_document, ["doc_number", "title"], as_dict=True
				)
				if s
				else None
			)
			cache[sug.legal_section] = (s, d)
		s, d = cache[sug.legal_section]
		sec = {
			"section_no": s.section_no,
			"doc_number": d.doc_number if d else None,
			"title": d.title if d else None,
		}
	label = None
	if sug.resource:
		field = "item_name" if sug.resource_doctype == "NC Item" else "equipment_name"
		label = frappe.db.get_value(sug.resource_doctype, sug.resource, field)
	return {
		"name": sug.name,
		"suggestion_type": sug.suggestion_type,
		"resource_doctype": sug.resource_doctype,
		"resource": sug.resource,
		"resource_label": label,
		"resource_text": sug.resource_text,
		"not_in_catalog": cint(sug.not_in_catalog),
		"value": sug.value,
		"uom": sug.uom,
		"relation": sug.relation,
		"legal_section": sug.legal_section,
		"doc_number": sec and sec["doc_number"],
		"doc_title": sec and sec["title"],
		"section_no": sec and sec["section_no"],
		"quote": sug.quote,
		"status": sug.status,
		"label": PENDING if sug.status == PENDING else None,
		"can_accept": _can_accept(sug, ts),
		"can_edit": bool(can_edit and sug.status == PENDING),
	}


@frappe.whitelist()
def list_cls_norm_suggestions(test_system, status=PENDING):
	ts = frappe.get_doc(TS, test_system)
	frappe.has_permission(TS, "read", doc=ts, throw=True)
	frappe.has_permission(SUG, "read", throw=True)
	filters = {"test_system": ts.name}
	if status in (PENDING, ACCEPTED, REJECTED):
		filters["status"] = status
	names = frappe.get_all(SUG, filters=filters, pluck="name", order_by="creation, name")
	can_edit = bool(frappe.has_permission(TS, "write", doc=ts) and frappe.has_permission(SUG, "write"))
	cache = {}
	rows = [_row(frappe.get_doc(SUG, n), ts, can_edit, cache) for n in names]
	rank = {t: i for i, t in enumerate(logic.TYPE_ORDER)}
	rows.sort(key=lambda r: rank.get(r["suggestion_type"], 99))
	return {
		"rows": rows,
		"can_edit": can_edit,
		"ai_enabled": bool(gateway.is_enabled()),
		"pending": frappe.db.count(SUG, {"test_system": ts.name, "status": PENDING}),
	}


# ---------------------------------------------------------------- xử lý đề xuất (TD 3.3, 3.4)


def _load_pending(name, perm="read"):
	sug = frappe.get_doc(SUG, name)
	frappe.has_permission(SUG, perm, doc=sug, throw=True)
	if sug.status != PENDING:
		frappe.throw(_("Đề xuất đã được xử lý"))
	return sug


def _finish(sug, **values):
	"""Ghi trạng thái đề xuất. Người chỉ có quyền đọc (Finance, Resource Mgr, Admin chấp nhận hạn dùng sau mở) đã được
	kiểm quyền ghi trên bản ghi đích; khi đó ghi bằng `ignore_permissions` và ghi `processed_by` (ASM-038-07)."""
	sug.update(values)
	sug.processed_by, sug.processed_on = frappe.session.user, now_datetime()
	sug.save(ignore_permissions=not frappe.has_permission(SUG, "write", doc=sug))


def _basis_ref(sug):
	if not sug.legal_section:
		return logic.NO_BASIS_REF
	sec = frappe.db.get_value(
		"NC Legal Section", sug.legal_section, ["legal_document", "section_no"], as_dict=True
	)
	number = frappe.db.get_value("NC Legal Document", sec.legal_document, "doc_number") if sec else None
	return logic.basis_ref(number, sec and sec.section_no)


def _plain(sug):
	return {
		"test_system": sug.test_system,
		"suggestion_type": sug.suggestion_type,
		"resource_doctype": sug.resource_doctype,
		"resource": sug.resource,
		"not_in_catalog": cint(sug.not_in_catalog),
		"value": sug.value,
	}


def _draft_norm_set(test_system):
	return frappe.db.get_value(
		"NC Norm Set", {"test_system": test_system, "status": "Nháp"}, "name", order_by="version_no desc"
	)


def _apply_norm_line(sug, plan, ns):
	frappe.has_permission("NC Norm Set", "write", doc=ns, throw=True)
	basis_ref = _basis_ref(sug)
	if plan["line_id"]:
		row = next(r for r in ns.lines if r.line_id == plan["line_id"])
		row.hospital_qty, row.basis, row.basis_ref = plan["value"], "Ước tính", basis_ref
	else:
		uom = sug.uom or frappe.db.get_value("NC Item", sug.resource, "uom")
		ns.append(
			"lines",
			{
				"service_level": 1,
				"component": "DRUG",
				"resource_doctype": "NC Item",
				"resource": sug.resource,
				"cost_level": "RESULT",
				"uom": uom,
				"hospital_qty": plan["value"],
				"basis": "Ước tính",
				"basis_ref": basis_ref,
			},
		)
	ns.save()  # controller kiểm DI-17, FR-NORM-*, quyền, phạm vi khoa; xóa xác nhận dòng đã đổi
	row = next(r for r in ns.lines if r.line_id == plan["line_id"]) if plan["line_id"] else ns.lines[-1]
	return {"norm_set": ns.name, "applied_ref": row.line_id}


def _apply_plan_row(sug, plan, field):
	doc = frappe.get_doc("NC QC Plan", {"test_system": sug.test_system})
	frappe.has_permission("NC QC Plan", "write", doc=doc, throw=True)
	table = "iqc_lines" if field == "runs_per_day" else "calibration_lines"
	row = next(r for r in doc.get(table) if r.name == plan["row"])
	row.set(field, plan["value"])
	doc.save()
	return {"applied_ref": row.name}


@frappe.whitelist()
def accept_cls_norm_suggestion(name):
	sug = _load_pending(name)
	if sug.not_in_catalog or not sug.resource:  # FR-AI-018
		frappe.throw(_("Liên kết mặt hàng hoặc thiết bị trong danh mục trước khi chấp nhận"))
	kind = sug.suggestion_type
	is_item_only = kind == logic.TYPE_LABELS["OPEN_STABILITY"]
	if is_item_only and not frappe.has_permission("NC Item", "write"):
		frappe.throw(
			_("Hạn dùng sau mở thuộc danh mục mặt hàng; cần Quản lý nguồn lực hoặc Tài chính chấp nhận"),
			frappe.PermissionError,
		)
	ns = ns_lines = plan_doc = None
	if kind == logic.TYPE_LABELS["REAGENT_PER_TEST"]:
		name_ns = _draft_norm_set(sug.test_system)
		if name_ns:
			ns = frappe.get_doc("NC Norm Set", name_ns)
			ns_lines = [r.as_dict() for r in ns.lines]
	elif kind in (logic.TYPE_LABELS["CALIBRATION_FREQ"], logic.TYPE_LABELS["IQC_FREQ"]):
		plan_doc = _qc_plan(sug.test_system)
	plan = logic.plan_accept(
		_plain(sug),
		ns_lines,
		[r.as_dict() for r in plan_doc.iqc_lines] if plan_doc else None,
		[r.as_dict() for r in plan_doc.calibration_lines] if plan_doc else None,
	)
	if plan.get("error"):
		frappe.throw(_(plan["error"]))
	target = plan["target"]
	if target == "norm_line":
		result = _apply_norm_line(sug, plan, ns)
	elif target == "calibration":
		result = _apply_plan_row(sug, plan, "calibrations_per_year")
	elif target == "iqc":
		result = _apply_plan_row(sug, plan, "runs_per_day")
	else:
		item = frappe.get_doc("NC Item", sug.resource)
		item.open_stability_days = plan["value"]
		item.save()
		result = {"applied_ref": item.name}
	_finish(sug, status=ACCEPTED, norm_set=result.get("norm_set"), applied_ref=result["applied_ref"])
	return {"status": ACCEPTED, "applied_ref": result["applied_ref"], "norm_set": result.get("norm_set")}


@frappe.whitelist()
def reject_cls_norm_suggestion(name):
	sug = _load_pending(name, "write")
	_finish(sug, status=REJECTED)
	return {"status": REJECTED}


@frappe.whitelist()
def link_cls_norm_suggestion(name, resource_doctype, resource):
	"""FR-AI-018: người dùng liên kết thủ công đề xuất ngoài danh mục với mặt hàng hoặc thiết bị có thật."""
	sug = _load_pending(name, "write")
	if resource_doctype not in logic.CATALOG_DOCTYPES:
		frappe.throw(_("Chỉ liên kết được với mặt hàng hoặc thiết bị"))
	if not resource or not frappe.db.exists(resource_doctype, resource):
		frappe.throw(
			_("Không có {0} {1} trong danh mục").format(_(CATALOG_LABEL[resource_doctype]), resource)
		)
	sug.resource_doctype, sug.resource, sug.not_in_catalog = resource_doctype, resource, 0
	sug.save()
	ts = frappe.get_doc(TS, sug.test_system)
	return _row(sug, ts, True, {})
