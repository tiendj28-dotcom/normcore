from decimal import Decimal

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.costing.allocation_rules import driver_shares
from normcore.nc_costing.doctype.nc_cost_center_driver.nc_cost_center_driver import get_driver_values
from normcore.tests.accounting_fixtures import make_centers
from normcore.tests.utils import make_user

FIN = "finance-drv@test.local"
AUD = "auditor-drv@test.local"
CLIN = "clinician-drv@test.local"


def _d(cc, **kw):
	return frappe.get_doc({"doctype": "NC Cost Center Driver", "fiscal_year": 2026, "cost_center": cc, **kw})


class TestNCCostCenterDriver(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		make_centers()
		make_user(FIN, "NC Finance")
		make_user(AUD, "NC Auditor")
		make_user(CLIN, "NC Clinician")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_TC_ACCT_09_tieu_chi_nam_va_ty_le_cap1(self):
		frappe.set_user(FIN)
		_d("K01", headcount=20).insert()
		_d("K02", headcount=30).insert()
		with self.assertRaisesRegex(frappe.ValidationError, "Đã có tiêu chí năm 2026"):
			_d("K01", headcount=5).insert()
		vals = get_driver_values(2026, "HEADCOUNT")
		self.assertEqual(vals, {"K01": Decimal(20), "K02": Decimal(30)})
		self.assertEqual(driver_shares(vals)["K01"], Decimal("0.4"))
		self.assertEqual(get_driver_values(2027, "HEADCOUNT"), {})
		self.assertEqual(get_driver_values(2026, "AREA"), {})
		with self.assertRaises(ValueError):
			get_driver_values(2026, "VOLUME")

	def test_so_am_bi_tu_choi(self):
		frappe.set_user(FIN)
		for kw in ({"headcount": -1}, {"area_m2": -1}, {"revenue": -1}):
			with self.assertRaises(frappe.ValidationError):
				_d("K01", **kw).insert()

	def test_N31_08_so_am_bao_nhan_tieng_viet(self):
		frappe.set_user(FIN)
		with self.assertRaises(frappe.ValidationError) as cm:
			_d("K01", headcount=-1).insert()
		msg = str(cm.exception)
		self.assertIn("Số nhân lực không được âm", msg)
		self.assertNotIn("headcount", msg)

	def test_quyen(self):
		frappe.set_user(AUD)
		self.assertTrue(frappe.has_permission("NC Cost Center Driver", "read"))
		for p in ("write", "create", "delete"):
			self.assertFalse(frappe.has_permission("NC Cost Center Driver", p), p)
		frappe.set_user(CLIN)
		self.assertFalse(frappe.has_permission("NC Cost Center Driver", "read"))
