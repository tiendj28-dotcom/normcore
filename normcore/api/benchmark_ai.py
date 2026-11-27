"""API trích bảng giá PDF bằng AI (FEAT-027, FR-BM-003, FR-AI-008..011, FR-AI-015, UC-013 2a, 2c).

Dùng chung gateway, mẫu lệnh, nhật ký AI của FEAT-023; mẫu tác vụ nền theo `api/cls_norm_ai.py` (FEAT-038).
Không sửa `api/benchmark.py`. Dòng AI tạo luôn ở trạng thái "Đề xuất" (`before_insert` của FEAT-026, có `ai_log`)."""

import frappe
from frappe import _
from frappe.utils import cint, getdate

from normcore.ai import gateway, guard, prompts_install
from normcore.benchmark import pdf_extract as px
from normcore.library import extract

PRICE = "NC Benchmark Price"
FACILITY = "NC Benchmark Facility"
JOB_KEY = "normcore:price_list_ai:{}"
JOB_TTL = 3600
MANUAL_HINT = "Có thể nhập tay hoặc nhập từ Excel."


def job_set(job_id, **state):
	frappe.cache().set_value(JOB_KEY.format(job_id), state, expires_in_sec=JOB_TTL)
	frappe.publish_realtime(
		"normcore_price_list_ai", {"job_id": job_id, "status": state.get("status")}, user=state.get("user")
	)


@frappe.whitelist()
def start_price_list_extraction(
	facility, price_category, file_url, source_doc_no=None, default_effective_date=None
):
	frappe.has_permission(PRICE, "create", throw=True)
	fac = frappe.get_doc(FACILITY, facility)
	frappe.has_permission(FACILITY, "read", doc=fac, throw=True)
	gateway.ensure_enabled()
	if not price_category or not frappe.db.exists("NC Price Category", price_category):
		frappe.throw(_("Loại giá không tồn tại"))
	file_name = frappe.db.get_value("File", {"file_url": file_url}, "name") if file_url else None
	if not file_name:
		frappe.throw(_("Không tìm thấy tệp"))
	file_doc = frappe.get_doc("File", file_name)
	frappe.has_permission("File", "read", doc=file_doc, throw=True)
	try:
		kind = extract.file_kind(file_doc.file_name)
	except extract.ExtractionError:
		kind = None
	if kind != "pdf":
		frappe.throw(_("Chỉ nhận tệp PDF"))
	if default_effective_date:
		try:
			default_effective_date = str(getdate(default_effective_date))
		except Exception:
			frappe.throw(_("Ngày hiệu lực mặc định không hợp lệ"))
	job_id = frappe.generate_hash(length=16)
	job_set(job_id, status="queued", user=frappe.session.user)
	frappe.enqueue(
		"normcore.api.benchmark_ai.run_price_list_extraction",
		queue="long",
		timeout=gateway.get_settings().timeout_seconds + 120,
		now=bool(frappe.flags.in_test),
		enqueue_after_commit=True,
		price_job=job_id,  # `job_id` là tham số của frappe.enqueue, không tới hàm
		facility=fac.name,
		price_category=price_category,
		file_url=file_url,
		source_doc_no=source_doc_no,
		default_effective_date=default_effective_date,
		user=frappe.session.user,
	)
	return {"job_id": job_id}


def _fail(job_id, user, message, log=None):
	return job_set(job_id, status="failed", user=user, message=message, log=log)


def run_price_list_extraction(
	price_job, facility, price_category, file_url, source_doc_no, default_effective_date, user
):
	"""Tác vụ nền (TD 3.4). Không ném lỗi: người gọi đọc trạng thái từ cache."""
	previous = frappe.session.user
	frappe.set_user(user)
	try:
		saved = False
		job_set(price_job, status="running", user=user)
		file_doc = frappe.get_doc("File", {"file_url": file_url})
		try:
			pages = extract.extract_pages(
				file_doc.get_content(), file_doc.file_name, ocr=extract.available_ocr()
			)
			px.check_page_count(pages)
		except (extract.ExtractionError, ValueError) as e:
			return _fail(price_job, user, str(e))
		prompts_install.ensure_extract_price_list_v2()
		sources = guard.price_list_pages(pages)
		fac_name = frappe.db.get_value(FACILITY, facility, "facility_name") or facility
		variables = {"facility_name": fac_name, "file_name": file_doc.file_name}
		default_date = getdate(default_effective_date) if default_effective_date else None
		holder = {}

		def post(data):
			rows, skipped = px.parse_rows(data, pages, default_date)
			holder["rows"], holder["skipped"] = rows, skipped
			return data, px.summary(0, [], skipped)["not_in_file"]

		res = gateway.complete(
			"EXTRACT_PRICE_LIST",
			"EXTRACT_PRICE_LIST",
			variables,
			sources,
			ref_doctype=FACILITY,
			ref_name=facility,
			postprocess=post,
		)
		if not res.ok:  # FR-AI-010, UC-013 2c: không tạo dòng nào
			return _fail(price_job, user, f"{res.error} {_(MANUAL_HINT)}".strip(), res.log_name)
		created, duplicates, skipped = 0, [], list(holder["skipped"])
		frappe.db.savepoint("nc_price_all")
		saved = True
		for r in holder["rows"]:
			frappe.db.savepoint("nc_price_row")
			try:
				frappe.get_doc(
					{
						"doctype": PRICE,
						"facility": facility,
						"service_name_raw": r["service_name_raw"],
						"price": r["price"],
						"price_category": price_category,
						"effective_date": r["effective_date"],
						"source_doc_no": source_doc_no,
						"source_file": file_url,
						"source_url": px.source_url(file_url, r["page"]),
						"ai_log": res.log_name,
					}
				).insert()
				created += 1
			except frappe.ValidationError as e:
				frappe.db.rollback(save_point="nc_price_row")
				msg = str(e)
				entry = {"service_name": r["service_name_raw"], "message": msg}
				if "Trùng" in msg:
					duplicates.append(entry)
				else:
					skipped.append({"service_name": r["service_name_raw"], "reason": msg})
		# Trong tác vụ nền, Frappe commit khi hàm trả về; không commit tay (giữ được rollback trong test)
		job_set(
			price_job, status="done", user=user, log=res.log_name, **px.summary(created, duplicates, skipped)
		)
	except Exception as e:  # không để tác vụ nền ném lỗi
		if saved:
			frappe.db.rollback(save_point="nc_price_all")
		_fail(price_job, user, f"{type(e).__name__}: {e}")
	finally:
		frappe.set_user(previous)


@frappe.whitelist()
def get_price_list_extraction_status(job_id):
	state = frappe.cache().get_value(JOB_KEY.format(job_id))
	if not state:
		return {"status": "unknown"}
	if state.get("user") != frappe.session.user and frappe.session.user != "Administrator":
		frappe.throw(_("Bạn không có quyền xem tiến độ này"), frappe.PermissionError)
	out = {
		k: state.get(k)
		for k in ("status", "created", "duplicates", "skipped", "not_in_file", "log", "message")
		if k in state
	}
	out["created"] = cint(out.get("created"))
	return out
