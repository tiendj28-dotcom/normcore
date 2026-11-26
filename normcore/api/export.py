"""API xuất hồ sơ (FEAT-019; UC-016; FR-OUT-001..006, 008, 009; FR-AUD-004). Logic sinh tệp ở normcore.exports;
ở đây chỉ nạp dữ liệu, kiểm quyền, ghi sự kiện nhật ký và trả tệp."""

from decimal import Decimal
from pathlib import Path

import frappe
import jinja2
from frappe import _
from frappe.utils import now_datetime

from normcore.api import costing, norm
from normcore.core import audit, notify
from normcore.exports import annex, bundle, explanation, meta as meta_mod
from normcore.exports import norm_set as norm_set_export

RUN, COST, NS = "NC Costing Run", "NC Service Cost", "NC Norm Set"
LOCKED = "Đã khóa"
TEMPLATES = Path(norm_set_export.__file__).parent / "templates"
NO_PERMISSION = "Bạn không có quyền xuất tệp này"

# mã -> (nhãn ghi vào nhật ký và hộp thoại, tệp, cần chọn)
FILE_TYPES = {
	"annex_ii": ("Phụ lục II — Phương án giá", "PL-II-{run}.xlsx", None),
	"annex_iii": ("Phụ lục III — Giá thành theo yếu tố chi phí", "PL-III-{run}.xlsx", None),
	"annex_iv": ("Phụ lục IV — Giá thành theo phương pháp phân bổ", "PL-IV-{run}.xlsx", None),
	"annex_v": ("Phụ lục V — Danh mục dịch vụ đề nghị định giá", "PL-V-{run}.xlsx", None),
	"explanation_pdf": ("Bảng giải trình (PDF)", "giai-trinh-{service_code}-{run}.pdf", "service_cost"),
	"norm_set_xlsx": ("Bộ định mức (Excel)", "{norm_set}.xlsx", "norm_set"),
	"norm_set_pdf": ("Bộ định mức (PDF)", "{norm_set}.pdf", "norm_set"),
	"bundle": ("Hồ sơ nén", "ho-so-{run}.zip", None),
}
ANNEX_BUILDERS = {
	"annex_ii": annex.build_annex_ii,
	"annex_iii": annex.build_annex_iii,
	"annex_iv": annex.build_annex_iv,
	"annex_v": annex.build_annex_v,
}
ANNEX_CODE = {"annex_ii": "II", "annex_iii": "III", "annex_iv": "IV", "annex_v": "V"}
MONEY_FIELDS = (
	"direct_labor direct_drug direct_supply direct_equipment direct_infra direct_utility alloc_labor "
	"alloc_drug_supply alloc_depreciation alloc_utility alloc_management full_cost accumulation obligation "
	"calculated_price rounded_price eqa_cost"
).split()


def _deny():
	frappe.throw(_(NO_PERMISSION), frappe.PermissionError)


def _can_read(doc) -> bool:
	return bool(frappe.has_permission(doc.doctype, "read", doc=doc))


def _full_name(user):
	return frappe.db.get_value("User", user, "full_name") or user


def _meta(file_type, source, run=None, user=None):
	user = user or frappe.session.user
	m = {
		"run": run,
		"parameter_set": None,
		"parameter_set_title": None,
		"exported_at": now_datetime(),
		"exported_by": user,
		"exported_by_name": _full_name(user),
		"file_type": FILE_TYPES[file_type][0],
		"source": source,
	}
	if run:
		ps = frappe.db.get_value(RUN, run, "parameter_set")
		m["parameter_set"] = ps
		m["parameter_set_title"] = frappe.db.get_value("NC Costing Parameter Set", ps, "title") if ps else None
	return m


def _locked_run(run, check_read=True):
	doc = frappe.get_doc(RUN, run)
	if check_read and not _can_read(doc):
		_deny()
	if doc.status != LOCKED:
		frappe.throw(
			_("Chỉ xuất hồ sơ từ lần tính giá đã khóa. Lần tính {0} đang ở trạng thái {1}.").format(
				run, doc.status
			),
			frappe.ValidationError,
		)
	return doc


def _dec(x):
	return Decimal(str(x or 0))


def _service_row(sc, names, his):
	row = {f: _dec(sc.get(f)) for f in MONEY_FIELDS}
	row.update(
		service_code=sc.technical_service,
		service_name=names.get(sc.technical_service) or sc.technical_service,
		department=sc.department,
		volume=sc.volume,
		his_code=his.get(sc.technical_service) or "",
		calc_status=sc.calc_status,
		calc_message=sc.calc_message,
		is_paraclinical=sc.is_paraclinical,
		alloc_lines=[
			{
				"component": ln.component,
				"allocation_rule": ln.allocation_rule,
				"driver_value": ln.driver_value,
				"driver_total": ln.driver_total,
				"pool_amount": ln.pool_amount,
				"amount": _dec(ln.amount),
			}
			for ln in sc.lines
			if ln.line_type == "Phân bổ"
		],
	)
	return row


def _annex_data(run_doc, meta):
	names = dict(frappe.get_all("NC Technical Service", fields=["service_code", "service_name"], as_list=True))
	his = {}
	for r in frappe.get_all(
		"NC Service Code Map",
		{"parenttype": "NC Technical Service", "source_system": "HIS"},
		["parent", "external_code"],
		order_by="idx",
	):
		his.setdefault(r.parent, r.external_code)
	services = []
	for name in frappe.get_all(COST, {"costing_run": run_doc.name}, pluck="name"):
		row = _service_row(frappe.get_doc(COST, name), names, his)
		row["price_category"] = run_doc.price_category
		services.append(row)
	return {
		"run": {
			"name": run_doc.name,
			"costing_date": run_doc.costing_date,
			"price_category": run_doc.price_category,
			"parameter_set": run_doc.parameter_set,
		},
		"services": services,
		"meta": meta,
	}


def _render(template, ctx):
	src = (TEMPLATES / template).read_text(encoding="utf-8")
	return jinja2.Environment(autoescape=True).from_string(src).render(**ctx)


def _pdf(html):
	from frappe.utils.pdf import get_pdf

	return get_pdf(html)


def _service_cost(name):
	sc = frappe.get_doc(COST, name)
	if not _can_read(sc):
		_deny()
	return sc


def explanation_html(service_cost, user=None):
	sc = _service_cost(service_cost)
	_locked_run(sc.costing_run, check_read=False)  # quyền theo bản ghi dịch vụ (ASM-019-04)
	expl = costing.get_explanation(sc.name)
	m = _meta("explanation_pdf", f"{COST} {sc.name}", sc.costing_run, user)
	return _render("service_explanation.html", explanation.pdf_context(expl, m)), sc


def norm_set_html(data, meta):
	return _render("norm_set.html", norm_set_export.pdf_context(data, meta))


def _norm_set_for(name, run=None):
	ns = norm._load(name)
	if run:
		_locked_run(run)
		if not frappe.db.exists(COST, {"costing_run": run, "norm_set": name}):
			frappe.throw(_("Bộ định mức {0} không thuộc lần tính giá {1}").format(name, run))
	return ns


def _norm_set_file(file_type, ns, run=None, user=None):
	m = _meta(file_type, f"{NS} {ns.name}", run, user)
	data = norm._export_data(ns)
	if file_type == "norm_set_xlsx":
		return norm_set_export.build_workbook(data, m)
	return _pdf(norm_set_html(data, m))


def _send(filename, content, file_type, ref_doctype, ref_name):
	audit.log_export(FILE_TYPES[file_type][0], ref_doctype, ref_name, filename)
	frappe.response["filename"] = filename
	frappe.response["filecontent"] = content
	frappe.response["type"] = "binary"


def _generation_error(filename, exc):
	frappe.log_error(title=f"Xuất tệp {filename}")
	frappe.throw(_("Không sinh được tệp {0}: {1}").format(filename, exc))


@frappe.whitelist()
def export_file(file_type, run=None, service_cost=None, norm_set=None):
	"""UC-016: xuất một tệp; quyền theo quyền đọc bản ghi nguồn (ASM-019-04)."""
	if file_type not in FILE_TYPES or file_type == "bundle":
		frappe.throw(_("Loại tệp không hợp lệ"), frappe.ValidationError)
	need = FILE_TYPES[file_type][2]
	if need == "service_cost" and not service_cost:
		frappe.throw(_("Chọn dịch vụ để xuất"), frappe.ValidationError)
	if need == "norm_set" and not norm_set:
		frappe.throw(_("Chọn bộ định mức để xuất"), frappe.ValidationError)
	if not need and not run:
		frappe.throw(_("Chọn lần tính giá để xuất"), frappe.ValidationError)
	template = FILE_TYPES[file_type][1]
	if file_type in ANNEX_BUILDERS:
		doc = _locked_run(run)
		filename = template.format(run=run)
		try:
			content = ANNEX_BUILDERS[file_type](_annex_data(doc, _meta(file_type, f"{RUN} {run}", run)))
		except Exception as e:
			_generation_error(filename, e)
		return _send(filename, content, file_type, RUN, run)
	if file_type == "explanation_pdf":
		sc = _service_cost(service_cost)
		filename = template.format(service_code=sc.technical_service, run=sc.costing_run)
		try:
			html, _sc = explanation_html(sc.name)
			content = _pdf(html)
		except frappe.PermissionError:
			raise
		except frappe.ValidationError:
			raise
		except Exception as e:
			_generation_error(filename, e)
		return _send(filename, content, file_type, COST, sc.name)
	ns = _norm_set_for(norm_set, run)
	filename = template.format(norm_set=ns.name)
	try:
		content = _norm_set_file(file_type, ns, run)
	except Exception as e:
		_generation_error(filename, e)
	return _send(filename, content, file_type, NS, ns.name)


def _bundle_job_id(run):
	return f"nc-export-bundle-{run}"


@frappe.whitelist()
def export_bundle(run):
	"""FR-OUT-009: đóng gói toàn bộ hồ sơ của lần tính giá, chạy nền."""
	_locked_run(run)
	job_id = _bundle_job_id(run)
	from frappe.utils.background_jobs import is_job_enqueued

	if is_job_enqueued(job_id):
		return {"queued": False, "running": True}
	frappe.enqueue(
		"normcore.api.export.build_bundle",
		queue="long",
		timeout=1500,
		run=run,
		user=frappe.session.user,
		job_id=job_id,
		deduplicate=True,
	)
	return {"queued": True, "job_id": job_id}


def _bundle_files(run_doc, user):
	run = run_doc.name
	files = []
	for ft in ("annex_ii", "annex_iii", "annex_iv", "annex_v"):
		data = _annex_data(run_doc, _meta(ft, f"{RUN} {run}", run, user))
		files.append((FILE_TYPES[ft][1].format(run=run), ANNEX_BUILDERS[ft](data)))
	costs = frappe.get_all(
		COST, {"costing_run": run}, ["name", "technical_service", "norm_set", "calc_status"], order_by="technical_service"
	)
	for c in costs:
		if c.calc_status == "Lỗi":
			continue
		html, _sc = explanation_html(c.name, user=user)
		files.append((FILE_TYPES["explanation_pdf"][1].format(service_code=c.technical_service, run=run), _pdf(html)))
	for ns_name in dict.fromkeys(c.norm_set for c in costs if c.norm_set):
		ns = frappe.get_doc(NS, ns_name)
		for ft in ("norm_set_xlsx", "norm_set_pdf"):
			files.append((FILE_TYPES[ft][1].format(norm_set=ns_name), _norm_set_file(ft, ns, run, user)))
	return files


def _commit():
	if not frappe.flags.in_test:
		frappe.db.commit()


def build_bundle(run, user):
	"""Tác vụ nền (không whitelist): sinh tệp nén, gắn vào lần tính, ghi nhật ký và thông báo."""
	frappe.set_user(user)
	try:
		run_doc = _locked_run(run)
		content = bundle.zip_files(_bundle_files(run_doc, user), _meta("bundle", f"{RUN} {run}", run, user))
		filename = FILE_TYPES["bundle"][1].format(run=run)
		for old in frappe.get_all(
			"File", {"attached_to_doctype": RUN, "attached_to_name": run, "file_name": filename}, pluck="name"
		):
			frappe.delete_doc("File", old, ignore_permissions=True, force=True)
		f = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": filename,
				"attached_to_doctype": RUN,
				"attached_to_name": run,
				"is_private": 1,
				"content": content,
			}
		).insert(ignore_permissions=True)
		audit.log_export(FILE_TYPES["bundle"][0], RUN, run, filename, user=user)
		notify.notify([user], _("Đã đóng gói hồ sơ {0}").format(run), RUN, run)
		frappe.publish_realtime(
			"nc_export_bundle", {"run": run, "status": "done", "file_url": f.file_url}, user=user
		)
		_commit()
		return f.file_url
	except Exception as e:
		if not frappe.flags.in_test:  # test dùng giao dịch của người gọi
			frappe.db.rollback()
		frappe.log_error(title=f"Xuất hồ sơ nén {run}")
		notify.notify([user], _("Lỗi đóng gói hồ sơ {0}").format(run), RUN, run)
		frappe.publish_realtime(
			"nc_export_bundle", {"run": run, "status": "error", "message": str(e)}, user=user
		)
		_commit()


def _options(enabled_all, reason):
	out = []
	for code, (label, _f, need) in FILE_TYPES.items():
		out.append(
			{
				"file_type": code,
				"label": label,
				"enabled": enabled_all,
				"reason": "" if enabled_all else reason,
				"needs": need,
			}
		)
	return out


@frappe.whitelist()
def get_export_options(run=None, service_cost=None, norm_set=None):
	"""Dữ liệu cho hộp thoại SCR-DSK-028."""
	if service_cost:
		sc = _service_cost(service_cost)
		run = sc.costing_run
	elif norm_set:
		norm._load(norm_set)
	elif run:
		frappe.get_doc(RUN, run)
	else:
		frappe.throw(_("Chọn nguồn để xuất"), frappe.ValidationError)
	out = {"source": {"run": run, "service_cost": service_cost, "norm_set": norm_set}}
	reason, enabled = "", True
	if run:
		doc = frappe.get_doc(RUN, run)
		if not _can_read(doc):
			_deny()
		if doc.status != LOCKED:
			enabled = False
			reason = _("Chỉ xuất hồ sơ từ lần tính giá đã khóa. Lần tính {0} đang ở trạng thái {1}.").format(
				run, doc.status
			)
	out["options"] = _options(enabled, reason)
	if norm_set and not run:  # bộ định mức xuất độc lập: chỉ hai loại của bộ
		for o in out["options"]:
			o["enabled"] = o["file_type"] in ("norm_set_xlsx", "norm_set_pdf")
			o["reason"] = "" if o["enabled"] else _("Chỉ áp dụng cho lần tính giá")
	out["service_costs"], out["norm_sets"], out["bundle"] = [], [], None
	if run and enabled:
		costs = frappe.get_all(
			COST,
			{"costing_run": run},
			["name", "technical_service", "department", "calc_status", "norm_set"],
			order_by="technical_service",
		)
		names = dict(frappe.get_all("NC Technical Service", fields=["service_code", "service_name"], as_list=True))
		out["service_costs"] = [
			{
				"name": c.name,
				"service_code": c.technical_service,
				"service_name": names.get(c.technical_service),
				"department": c.department,
				"calc_status": c.calc_status,
			}
			for c in costs
		]
		seen = {}
		for c in costs:
			if c.norm_set:
				seen.setdefault(c.norm_set, {"name": c.norm_set, "service_code": c.technical_service, "department": c.department})
		out["norm_sets"] = list(seen.values())
		f = frappe.get_all(
			"File",
			{"attached_to_doctype": RUN, "attached_to_name": run, "file_name": FILE_TYPES["bundle"][1].format(run=run)},
			["file_url", "creation"],
			limit=1,
		)
		out["bundle"] = f[0] if f else None
	return out
