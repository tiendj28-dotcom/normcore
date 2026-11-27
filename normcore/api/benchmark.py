"""API kho giá tham chiếu (FEAT-026). Logic thuần ở `normcore/benchmark/reference.py`.

`prepare_benchmark_price` không whitelisted: chỉ khung nhập (`core/importer.py`) gọi qua `ImportSet.prepare`.
"""

import frappe
from frappe import _

from normcore.benchmark import reference as ref
from normcore.core.importer import RowValueError
from normcore.exports import price_survey
from normcore.nc_benchmark.doctype.nc_benchmark_price.nc_benchmark_price import find_saved_duplicate


def prepare_benchmark_price(values):
	"""Kiểm dòng nhập giá tham chiếu (TD 3.3); chạy ở cả chế độ "thu" và "ghi"."""
	service, raw = values.get("technical_service"), values.get("service_name_raw")
	if not service and not raw:
		raise RowValueError("Tên dịch vụ gốc", "cần mã dịch vụ hoặc tên dịch vụ gốc")
	extra = {}
	if service and not raw:  # ASM-026-04
		raw = frappe.db.get_value("NC Technical Service", service, "service_name")
		extra["service_name_raw"] = raw
	if not values.get("source_doc_no") and not values.get("source_url"):  # ASM-026-05
		raise RowValueError("Số văn bản nguồn", "cần số văn bản hoặc đường dẫn nguồn")
	dup = find_saved_duplicate({**values, **extra})  # FR-BM-007, ASM-026-06
	if dup:
		raise RowValueError(
			"Tên dịch vụ gốc",
			f"trùng giá tham chiếu {dup} (cùng đơn vị, dịch vụ, loại giá, ngày hiệu lực)",
		)
	return extra


# --- xác nhận, so sánh, giá hiệu chỉnh (TD 3.4) -----------------------------

PRICE = "NC Benchmark Price"


def _names(names):
	if isinstance(names, str):
		names = frappe.parse_json(names)
	return list(names or [])


def _check(ptype, doc=None):
	if not frappe.has_permission(PRICE, ptype, doc=doc):
		frappe.throw(_("Bạn không có quyền {0} giá tham chiếu").format(_(ptype)), frappe.PermissionError)


def _set_status(names, status, allowed_from):
	"""Đổi trạng thái từng dòng: (đã đổi, lỗi theo dòng). Quyền ghi kiểm từng dòng."""
	done, errors = [], []
	for name in _names(names):
		doc = frappe.get_doc(PRICE, name)
		_check("write", doc)
		if doc.status not in allowed_from:
			errors.append({"name": name, "message": _("Trạng thái hiện tại là {0}").format(doc.status)})
			continue
		doc.status = status
		try:
			doc.save()
		except frappe.ValidationError as e:
			frappe.clear_last_message()
			errors.append({"name": name, "message": frappe.utils.strip_html(str(e))})
			continue
		done.append(name)
	return done, errors


@frappe.whitelist()
def confirm_prices(names, technical_service=None):
	"""Xác nhận cặp khớp (UC-013 bước 4). `technical_service` chỉ khi một dòng: đổi cặp trước khi xác nhận."""
	names = _names(names)
	if technical_service and len(names) != 1:
		frappe.throw(_("Chỉ đổi dịch vụ khi xác nhận một dòng"))
	done, errors = [], []
	for name in names:
		doc = frappe.get_doc(PRICE, name)
		_check("write", doc)
		if technical_service:
			doc.technical_service = technical_service
		if doc.status == ref.STATUS_REJECTED:
			errors.append({"name": name, "message": _("Dòng đã loại bỏ, hãy mở lại trước")})
			continue
		doc.status = ref.STATUS_CONFIRMED
		try:
			doc.save()
		except frappe.ValidationError as e:
			frappe.clear_last_message()
			errors.append({"name": name, "message": frappe.utils.strip_html(str(e))})
			continue
		done.append(name)
	return {"confirmed": done, "errors": errors}


@frappe.whitelist()
def reject_prices(names):
	done, errors = _set_status(names, ref.STATUS_REJECTED, (ref.STATUS_PROPOSED, ref.STATUS_CONFIRMED))
	return {"rejected": done, "errors": errors}


@frappe.whitelist()
def reopen_prices(names):
	done, errors = _set_status(names, ref.STATUS_PROPOSED, (ref.STATUS_CONFIRMED, ref.STATUS_REJECTED))
	return {"reopened": done, "errors": errors}


def _cpi_by_month():
	rows = frappe.get_all("NC CPI Index", fields=["month", "index_value"])
	return {ref.month_start(r.month): r.index_value for r in rows}


def _target_month(target_month, cpi):
	if target_month:
		return ref.month_start(target_month)
	return max(cpi) if cpi else None


@frappe.whitelist()
def get_comparable_prices(technical_service, price_category=None, target_month=None):
	"""FR-BM-005: chỉ dòng "Đã xác nhận" của dịch vụ; kèm giá hiệu chỉnh (BR-ADJ-009). FEAT-028 dùng hàm này."""
	_check("read")
	filters = {"technical_service": technical_service}
	if price_category:
		filters["price_category"] = price_category
	rows = frappe.get_all(
		PRICE,
		filters=filters,
		fields=[
			"name",
			"facility",
			"price",
			"price_category",
			"effective_date",
			"source_doc_no",
			"source_url",
			"status",
		],
		order_by="effective_date desc, name asc",
	)
	rows = ref.comparable_prices(rows)
	cpi = _cpi_by_month()
	target = _target_month(target_month, cpi)
	facilities = {
		f.name: f
		for f in frappe.get_all(
			"NC Benchmark Facility",
			fields=["name", "facility_name", "province", "ownership", "facility_level"],
		)
	}
	out = []
	for r in rows:
		f = facilities.get(r.facility) or {}
		out.append(
			{
				"name": r.name,
				"facility": r.facility,
				"facility_name": f.get("facility_name"),
				"province": f.get("province"),
				"ownership": f.get("ownership"),
				"facility_level": f.get("facility_level"),
				"price": r.price,
				"price_category": r.price_category,
				"effective_date": r.effective_date,
				"source_doc_no": r.source_doc_no,
				"source_url": r.source_url,
				"adjusted": _adjust(r, cpi, target),
			}
		)
	return {"rows": out, "target_month": target}


def comparable_prices_bulk(technical_services, price_category, target_month=None):
	"""FEAT-028 (TD 3.4): giá "Đã xác nhận" của nhiều dịch vụ, cùng loại giá, một truy vấn. Không whitelisted.

	Trả {dịch vụ: [dòng]} cùng dạng với `get_comparable_prices(...)["rows"]`; kiểm quyền ở nơi gọi.
	"""
	services = list(technical_services or [])
	if not services:
		return {}
	rows = frappe.get_all(
		PRICE,
		filters={"technical_service": ["in", services], "price_category": price_category},
		fields=[
			"name",
			"facility",
			"price",
			"price_category",
			"effective_date",
			"source_doc_no",
			"source_url",
			"status",
			"technical_service",
		],
		order_by="effective_date desc, name asc",
	)
	rows = ref.comparable_prices(rows)
	cpi = _cpi_by_month()
	target = _target_month(target_month, cpi)
	facilities = {
		f.name: f
		for f in frappe.get_all(
			"NC Benchmark Facility",
			fields=["name", "facility_name", "province", "ownership", "facility_level"],
		)
	}
	out = {svc: [] for svc in services}
	for r in rows:
		f = facilities.get(r.facility) or {}
		out[r.technical_service].append(
			{
				"name": r.name,
				"facility": r.facility,
				"facility_name": f.get("facility_name"),
				"province": f.get("province"),
				"ownership": f.get("ownership"),
				"facility_level": f.get("facility_level"),
				"price": r.price,
				"price_category": r.price_category,
				"effective_date": r.effective_date,
				"source_doc_no": r.source_doc_no,
				"source_url": r.source_url,
				"adjusted": _adjust(r, cpi, target),
			}
		)
	return out


def _adjust(row, cpi, target):
	if target is None:
		return {"adjusted_price": None, "missing": []}
	return ref.adjust(row, cpi, target)


@frappe.whitelist()
def get_adjusted_price(name, target_month=None):
	"""Giá hiệu chỉnh của một dòng (BR-ADJ-009, tính khi đọc)."""
	doc = frappe.get_doc(PRICE, name)
	_check("read", doc)
	cpi = _cpi_by_month()
	target = _target_month(target_month, cpi)
	out = _adjust({"price": doc.price, "effective_date": doc.effective_date}, cpi, target)
	return {**out, "price": doc.price, "effective_date": doc.effective_date}


@frappe.whitelist()
def download_price_survey(facility, price_category, specialty=None, services=None):
	"""FR-BM-008, UC-013 1a: phiếu khảo sát giá (.xlsx) cho một nhóm dịch vụ (chuyên khoa hoặc danh sách mã)."""
	_check("create")
	fac = frappe.get_doc("NC Benchmark Facility", facility)
	filters = {"is_active": 1}
	group = specialty
	if services:
		filters["name"] = ["in", _names(services)]
		group = group or _("Danh sách dịch vụ chọn")
	elif specialty:
		filters["specialty"] = specialty
	else:
		frappe.throw(_("Chọn chuyên khoa hoặc danh sách dịch vụ"))
	rows = frappe.get_all("NC Technical Service", filters=filters, fields=["name", "service_name"])
	if not rows:
		frappe.throw(_("Nhóm dịch vụ trống"))
	meta = {
		"group": group,
		"author": frappe.utils.get_fullname(frappe.session.user),
		"created": frappe.utils.getdate(),
	}
	content = price_survey.build_survey(fac.as_dict(), rows, price_category, meta)
	frappe.response["filename"] = f"phieu-khao-sat-gia-{frappe.scrub(fac.name)}.xlsx"
	frappe.response["filecontent"] = content
	frappe.response["type"] = "binary"
