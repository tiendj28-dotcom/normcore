"""Dữ liệu thử dùng chung cho test FEAT-026 (kho giá tham chiếu)."""

import frappe

from normcore.tests.utils import ensure

FACILITY = "Bệnh viện thử GTC"
CATEGORY = "GTC-LG"


def make_facility(name=FACILITY, **kw):
	values = {"province": "Hà Nội", "ownership": "Công lập", "facility_level": "Hạng I", **kw}
	return ensure("NC Benchmark Facility", "facility_name", name, **values)


def make_category(code=CATEGORY):
	return ensure(
		"NC Price Category",
		"category_code",
		code,
		category_name="Loại giá thử GTC",
		approval_authority="Bệnh viện",
	)


def make_service(code, name):
	return ensure("NC Technical Service", "service_code", code, service_name=name)


def price_values(**kw):
	values = {
		"doctype": "NC Benchmark Price",
		"facility": FACILITY,
		"service_name_raw": "Định lượng Glucose máu",
		"price": 25000,
		"price_category": CATEGORY,
		"effective_date": "2026-01-01",
		"source_doc_no": "123/QĐ-BV",
	}
	values.update(kw)
	return values


def make_price(**kw):
	return frappe.get_doc(price_values(**kw)).insert()
