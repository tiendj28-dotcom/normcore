"""API mặt hàng và đơn giá (FEAT-009; FR-RES-004, FR-RES-016, FR-RES-013, FR-ACC-005).

Logic chọn giá nằm ở `normcore/costing/pricing.py`; ở đây chỉ đọc bản ghi (có kiểm quyền) và gọi vào đó.
"""

from decimal import Decimal

import frappe
from frappe import _
from frappe.utils import getdate, nowdate

from normcore.costing import pricing

ITEM = "NC Item"
PRICE = "NC Item Price"
PRICE_FIELDS = [
	"name",
	"unit_price",
	"price_source",
	"document_no",
	"document_date",
	"valid_from",
	"valid_to",
	"verification_status",
]


def _records(item):
	rows = frappe.get_list(PRICE, filters={"item": item}, fields=PRICE_FIELDS, limit_page_length=0)
	return [
		pricing.PriceRecord(
			name=r.name,
			unit_price=Decimal(str(r.unit_price)),
			price_source=r.price_source,
			document_date=getdate(r.document_date),
			valid_from=getdate(r.valid_from),
			valid_to=getdate(r.valid_to) if r.valid_to else None,
			verified=r.verification_status == "Đã xác minh",
		)
		for r in rows
	]


@frappe.whitelist()
def get_effective_price(item, as_of=None):
	"""Đơn giá được dùng cho `item` tại `as_of` (mặc định hôm nay), kèm cảnh báo và đơn giá một đơn vị
	định mức. Không có đơn giá hiệu lực → `price` là None (không bịa số)."""
	if not frappe.has_permission(ITEM, "read", item):
		frappe.throw(_("Bạn không có quyền xem mặt hàng này"), frappe.PermissionError)
	meta = frappe.db.get_value(ITEM, item, ["norm_units_per_purchase_unit", "norm_uom", "uom"], as_dict=True)
	as_of = getdate(as_of or nowdate())
	picked = pricing.select_price(_records(item), as_of)
	if picked is None:
		return {"item": item, "as_of": str(as_of), "price": None, "warnings": [], "norm_unit_price": None}
	units = meta.norm_units_per_purchase_unit or 1
	return {
		"item": item,
		"as_of": str(as_of),
		"price": {
			"name": picked.name,
			"unit_price": str(picked.unit_price),
			"price_source": picked.price_source,
			"valid_from": str(picked.valid_from),
			"valid_to": str(picked.valid_to) if picked.valid_to else None,
			"verified": picked.verified,
		},
		"warnings": list(pricing.price_warnings(picked, as_of)),
		"norm_unit_price": str(pricing.unit_price_per_norm(picked.unit_price, Decimal(str(units)))),
		"norm_uom": meta.norm_uom or meta.uom,
	}


@frappe.whitelist()
def verify_price(name):
	"""FR-RES-016: chuyển đơn giá sang "Đã xác minh"; từ chối khi chưa có tệp chứng từ (UC-008 2f)."""
	doc = frappe.get_doc(PRICE, name)
	doc.check_permission("write")
	doc.verification_status = "Đã xác minh"
	doc.save()
	return {"name": doc.name, "verified_by": doc.verified_by, "verified_on": str(doc.verified_on)}


@frappe.whitelist()
def get_equivalent_items(item):
	"""FR-RES-013: các mặt hàng cùng nhóm tương đương (không tính chính nó); dùng cho BR-ADJ-003 sau này."""
	if not frappe.has_permission(ITEM, "read", item):
		frappe.throw(_("Bạn không có quyền xem mặt hàng này"), frappe.PermissionError)
	group = frappe.db.get_value(ITEM, item, "equivalent_group")
	if not group:
		return []
	return frappe.get_list(
		ITEM,
		filters={"equivalent_group": group, "name": ["!=", item]},
		fields=["name", "item_name", "uom"],
		order_by="name",
		limit_page_length=0,
	)
