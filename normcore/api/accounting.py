"""API số liệu kế toán (FEAT-016, UC-011; CLAUDE.md mục 4): kiểm quyền tường minh trong từng hàm."""

import json

import frappe
from frappe import _

from normcore.core import importer as core
from normcore.costing import accounting
from normcore.nc_costing.doctype.nc_account_mapping.nc_account_mapping import mapping_for
from normcore.nc_costing.doctype.nc_accounting_import.nc_accounting_import import (
	fill_from_file,
	line_dicts,
)

DT = "NC Accounting Import"
MAX_ERRORS = 200


def _doc(name, ptype):
	frappe.has_permission(DT, ptype, doc=name, throw=True)
	return frappe.get_doc(DT, name)


def _draft(doc):
	if doc.status != accounting.STATUS_DRAFT:
		frappe.throw(_("Lần nhập {0} đã chốt, không sửa được").format(doc.name))


def _summary(doc):
	lines = line_dicts(doc.lines)
	un = accounting.unassigned(lines)
	blockers = accounting.finalize_blockers(doc.status, doc.error_count, lines)
	if doc.status == accounting.STATUS_FINAL:
		totals = [{"cost_center": t.cost_center, "cost_category": t.cost_category, "amount": t.amount} for t in doc.totals]
	else:
		totals = [
			{"cost_center": c, "cost_category": cat, "amount": float(v)} for c, cat, v in accounting.totals(lines)
		]
	return {
		"name": doc.name,
		"status": doc.status,
		"line_count": doc.line_count or 0,
		"total_amount": doc.total_amount or 0,
		"error_count": doc.error_count or 0,
		"errors": json.loads(doc.import_errors or "[]")[:MAX_ERRORS],
		"unassigned": [
			{"idx": u["idx"], "account_code": u.get("account_code"), "cost_center": u.get("cost_center"), "amount": u.get("amount")}
			for u in un
		],
		"excluded_count": sum(1 for ln in lines if ln.get("is_excluded")),
		"can_finalize": not blockers,
		"blockers": blockers,
		"totals": totals,
	}


@frappe.whitelist()
def get_import_summary(name):
	return _summary(_doc(name, "read"))


@frappe.whitelist()
def update_line(name, row, cost_category=None, is_excluded=0, change_reason=None):
	"""FR-ACCT-004: đổi loại chi phí hoặc loại trừ của một dòng, bắt buộc có lý do."""
	doc = _doc(name, "write")
	_draft(doc)
	if not (change_reason or "").strip():
		frappe.throw(_("Nhập lý do khi đổi loại chi phí hoặc loại trừ"))
	line = next((r for r in doc.lines if r.name == row), None)
	if line is None:
		frappe.throw(_("Không tìm thấy dòng {0} của lần nhập {1}").format(row, name))
	if cost_category and cost_category not in accounting.COST_CATEGORIES:
		frappe.throw(_("Loại chi phí {0} không hợp lệ").format(cost_category))
	line.cost_category = cost_category or None
	line.is_excluded = 1 if int(frappe.utils.cint(is_excluded)) else 0
	line.change_reason = change_reason.strip()
	doc.save()
	return _summary(doc)


@frappe.whitelist()
def reapply_mapping(name):
	"""UC-011 2a: gán lại theo bảng ánh xạ hiện tại; dòng đã sửa tay giữ nguyên (ASM-122)."""
	doc = _doc(name, "write")
	_draft(doc)
	lines = line_dicts(doc.lines)
	changed = accounting.assign_categories(lines, mapping_for(doc.accounting_regime), keep_manual=True)
	for row, ln in zip(doc.lines, lines, strict=True):
		row.cost_category, row.is_excluded = ln["cost_category"], ln["is_excluded"]
	doc.flags.nc_replace_lines = True
	doc.save()
	return {"changed": changed, **_summary(doc)}


@frappe.whitelist()
def reload_file(name):
	"""Đọc lại `source_file` hiện tại, thay toàn bộ dòng và bỏ sửa tay (ASM-122)."""
	doc = _doc(name, "write")
	_draft(doc)
	fill_from_file(doc)
	doc.flags.nc_replace_lines = True
	doc.save()
	return _summary(doc)


@frappe.whitelist()
def finalize(name):
	"""FR-ACCT-005, 006: chốt, khóa dòng, ghi tổng theo (trung tâm, loại)."""
	doc = _doc(name, "write")
	blockers = accounting.finalize_blockers(doc.status, doc.error_count, line_dicts(doc.lines))
	if blockers:
		frappe.throw(
			_("Không chốt được lần nhập {0}: {1}").format(name, "; ".join(blockers)),
			title=_("Chưa chốt được"),
		)
	doc.set("totals", [])
	for cc, cat, amount in accounting.totals(line_dicts(doc.lines)):
		doc.append("totals", {"cost_center": cc, "cost_category": cat, "amount": amount})
	doc.status = accounting.STATUS_FINAL
	doc.flags.nc_finalizing = True
	doc.save()
	return _summary(doc)


@frappe.whitelist()
def download_template():
	frappe.has_permission(DT, "read", throw=True)
	frappe.response["filename"] = "mau-nhap-so-lieu-ke-toan.xlsx"
	frappe.response["filecontent"] = core.build_template(accounting.ACCOUNTING_LINES)
	frappe.response["type"] = "binary"
