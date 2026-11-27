"""Dữ liệu test FEAT-030: lần tính vàng đã khóa để lập phương án giá."""

import frappe

from normcore.api import costing as api
from normcore.tests import costing_fixtures as cf

FIN_USER = "fin.n84@normcore.test"


def make_locked_golden_run(fin_user, category="PC-GOLD"):
	"""Lần tính vàng "Đã khóa" (DV-TEST-A 302.100, DV-TEST-B 92.600). Trả (run, params, dept)."""
	params, dept, _ = cf.make_golden_world()
	imp = cf.make_golden_allocation(dept)
	run = cf.make_golden_run(params, price_category=category, accounting_import=imp)
	frappe.set_user(fin_user)
	api.start_costing(run.name)
	frappe.set_user("Administrator")
	name = frappe.db.get_value(
		"NC Reconciliation Line", {"costing_run": run.name, "cost_category": "DRUG_SUPPLY"}
	)
	frappe.db.set_value("NC Reconciliation Line", name, "explanation", "Nhập thuốc chưa xuất kho")
	frappe.set_user(fin_user)
	api.lock_run(run.name)
	frappe.set_user("Administrator")
	return frappe.get_doc("NC Costing Run", run.name), params, dept
