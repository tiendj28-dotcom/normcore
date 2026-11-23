import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.tests.accounting_fixtures import make_centers
from normcore.tests.utils import make_user

FIN = "finance-rule@test.local"
AUD = "auditor-rule@test.local"
CLIN = "clinician-rule@test.local"


def _r(level="Cấp 2", cat="LABOR", driver="LABOR_MIN", **kw):
	return frappe.get_doc(
		{"doctype": "NC Allocation Rule", "rule_name": "Quy tắc thử", "level": level, "cost_category": cat, "driver": driver, **kw}
	)


class TestNCAllocationRule(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		make_centers()
		make_user(FIN, "NC Finance")
		make_user(AUD, "NC Auditor")
		make_user(CLIN, "NC Clinician")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_TC_ACCT_07_thieu_tieu_chi_cap2_headcount_cap2_labor_min(self):
		frappe.set_user(FIN)
		with self.assertRaises(frappe.MandatoryError):
			_r(driver=None).insert()
		with self.assertRaisesRegex(frappe.ValidationError, "HEADCOUNT.*cấp 1"):
			_r(driver="HEADCOUNT").insert()
		self.assertTrue(_r(driver="LABOR_MIN").insert().name)

	def test_cap1_dung_moi_tieu_chi_va_cap2_area_revenue_bi_tu_choi(self):
		frappe.set_user(FIN)
		self.assertTrue(_r("Cấp 1", "MANAGEMENT", "HEADCOUNT").insert().name)
		for d in ("AREA", "REVENUE"):
			with self.assertRaises(frappe.ValidationError):
				_r("Cấp 2", "UTILITY", d).insert()

	def test_trung_cap_loai_trung_tam_bi_tu_choi(self):
		frappe.set_user(FIN)
		_r().insert()
		with self.assertRaisesRegex(frappe.ValidationError, "Đã có quy tắc"):
			_r(driver="VOLUME").insert()
		_r(cost_center="K01").insert()  # cụ thể một trung tâm thì khác "mọi trung tâm"
		with self.assertRaises(frappe.ValidationError):
			_r(cost_center="K01").insert()

	def test_loai_trung_tam_theo_cap(self):
		frappe.set_user(FIN)
		with self.assertRaises(frappe.ValidationError):
			_r(cost_center="HC").insert()  # cấp 2 phải là Lâm sàng
		with self.assertRaises(frappe.ValidationError):
			_r("Cấp 1", "LABOR", "HEADCOUNT", cost_center="K01").insert()  # cấp 1 phải là Hỗ trợ
		self.assertTrue(_r("Cấp 1", "LABOR", "HEADCOUNT", cost_center="HC").insert().name)

	def test_excluded_khong_phan_bo(self):
		with self.assertRaises(frappe.ValidationError):
			_r(cat="EXCLUDED").insert()

	def test_quyen(self):
		frappe.set_user(AUD)
		self.assertTrue(frappe.has_permission("NC Allocation Rule", "read"))
		for p in ("write", "create", "delete"):
			self.assertFalse(frappe.has_permission("NC Allocation Rule", p), p)
		frappe.set_user(CLIN)
		self.assertFalse(frappe.has_permission("NC Allocation Rule", "read"))
		frappe.set_user(FIN)
		self.assertTrue(frappe.has_permission("NC Allocation Rule", "create"))
		self.assertFalse(frappe.has_permission("NC Allocation Rule", "delete"))
