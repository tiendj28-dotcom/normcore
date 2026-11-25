"""Dữ liệu dùng chung cho test FEAT-016 (technical-design mục 6)."""

import io

import frappe
from openpyxl import Workbook

from normcore.costing import accounting
from normcore.tests.utils import ensure

HEADER = ["Mã tài khoản *", "Tên tài khoản", "Mã trung tâm chi phí *", "Số tiền *"]

# Tệp vàng dạng tài khoản: tổng 2.105.000.000 (golden_engine.ACCOUNTING sau khi bỏ dòng 811)
GOLDEN_ROWS = [
	["61111", "Tiền lương", "K01", 500000000],
	["61111", "Phụ cấp, đóng góp theo lương", "K01", 200000000],
	["61112", "Thuốc, hóa chất, vật tư", "K01", 260000000],
	["61113", "Khấu hao tài sản cố định", "K01", 300000000],
	["611122", "Điện, nước", "K01", 40000000],
	["61118", "Chi khác", "K01", 100000000],
	["811", "Chi phí khác", "K01", 5000000],
	["61111", "Tiền lương", "HC", 300000000],
	["61118", "Chi khác", "HC", 150000000],
	["642", "Chi phí quản lý", "HC", 250000000],
]


def make_xlsx(rows, header=HEADER):
	wb = Workbook()
	ws = wb.active
	ws.append(header)
	for r in rows:
		ws.append(r)
	buf = io.BytesIO()
	wb.save(buf)
	return buf.getvalue()


def make_centers():
	for code, typ in (("K01", "Lâm sàng"), ("K02", "Lâm sàng"), ("HC", "Hỗ trợ")):
		ensure(
			"NC Cost Center", "cost_center_code", code, cost_center_name=f"Trung tâm {code}", center_type=typ
		)


def ensure_default_mapping():
	for prefix, cat in accounting.DEFAULT_ACCOUNT_MAPPING:
		if not frappe.db.exists(
			"NC Account Mapping", {"accounting_regime": accounting.DEFAULT_REGIME, "account_prefix": prefix}
		):
			frappe.get_doc(
				{
					"doctype": "NC Account Mapping",
					"accounting_regime": accounting.DEFAULT_REGIME,
					"account_prefix": prefix,
					"cost_category": cat,
					"note": accounting.ASSUMPTION_NOTE,
				}
			).insert(ignore_permissions=True)


def make_file(content, name="kt.xlsx"):
	f = frappe.get_doc({"doctype": "File", "file_name": name, "content": content, "is_private": 1})
	f.insert(ignore_permissions=True)
	return f.file_url


def make_import(rows=None, year=2026, content=None, filename="kt.xlsx"):
	"""Tạo lần nhập (người dùng hiện tại phải có quyền tạo)."""
	if content is None:
		content = make_xlsx(GOLDEN_ROWS if rows is None else rows)
	doc = frappe.get_doc(
		{
			"doctype": "NC Accounting Import",
			"fiscal_year": year,
			"accounting_regime": accounting.DEFAULT_REGIME,
			"source_file": make_file(content, filename),
		}
	)
	return doc.insert()
