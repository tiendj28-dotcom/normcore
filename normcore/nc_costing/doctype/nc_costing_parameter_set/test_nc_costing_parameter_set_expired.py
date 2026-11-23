import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.tests.utils import GOLDEN_PARAM


def _ps(**kw):
	return frappe.get_doc(
		{
			"doctype": "NC Costing Parameter Set",
			"title": "PS thử",
			"effective_from": "2026-01-01",
			**GOLDEN_PARAM,
			**kw,
		}
	)


class TestNCCostingParameterSetExpired(FrappeTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def test_FR_RES_007_mac_dinh_zero(self):
		self.assertEqual(_ps().insert().expired_depreciation_mode, "ZERO")

	def test_FR_RES_007_chon_continue_luu_duoc(self):
		ps = _ps(expired_depreciation_mode="CONTINUE").insert()
		self.assertEqual(frappe.db.get_value(ps.doctype, ps.name, "expired_depreciation_mode"), "CONTINUE")

	def test_FR_RES_007_gia_tri_ngoai_danh_sach_bi_tu_choi(self):
		self.assertRaises(frappe.ValidationError, _ps(expired_depreciation_mode="KHAC").insert)
