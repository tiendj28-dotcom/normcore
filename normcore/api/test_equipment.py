import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.api import equipment as api
from normcore.nc_costing.doctype.nc_equipment.test_nc_equipment import _eq
from normcore.nc_costing.doctype.nc_room.test_nc_room import _room
from normcore.tests.utils import GOLDEN_PARAM, make_user


def _ps(mode, date="2026-01-01"):
	frappe.get_doc(
		{
			"doctype": "NC Costing Parameter Set",
			"title": f"PS {mode}",
			"effective_from": date,
			**GOLDEN_PARAM,
			"expired_depreciation_mode": mode,
		}
	).insert()


class TestEquipmentApi(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_TC_RES_03_api_eq1(self):
		_eq().insert()
		r = api.get_indicative_rate("EQ1", "2026-12-31")
		self.assertEqual(r["annual_depreciation"], 150000000)
		self.assertEqual(r["hourly_rate"], 176136.3636)

	def test_TC_RES_04_api_theo_bo_tham_so(self):
		_eq(equipment_code="V2", in_service_date="2015-01-01").insert()
		frappe.db.delete("NC Costing Parameter Set")
		self.assertEqual(
			api.get_indicative_rate("V2", "2026-12-31")["annual_depreciation"], 0
		)  # không bộ: ZERO
		_ps("CONTINUE")
		r = api.get_indicative_rate("V2", "2026-12-31")
		self.assertEqual((r["annual_depreciation"], r["expired_mode"]), (150000000, "CONTINUE"))
		_ps("ZERO", "2026-06-01")
		self.assertEqual(api.get_indicative_rate("V2", "2026-12-31")["annual_depreciation"], 0)

	def test_TC_RES_10_api_gio_phong(self):
		_room().insert()
		self.assertEqual(api.get_room_rate("R1")["hourly_rate"], 25000)

	def test_FR_ACC_002_khong_quyen_bi_tu_choi(self):
		_eq().insert()
		_room().insert()
		none = make_user("api.eq.none@normcore.test", "NC Document Controller")
		auditor = make_user("api.eq.auditor@normcore.test", "NC Auditor")
		frappe.set_user(none)
		self.assertRaises(frappe.PermissionError, api.get_indicative_rate, "EQ1")
		self.assertRaises(frappe.PermissionError, api.get_room_rate, "R1")
		frappe.set_user(auditor)
		self.assertEqual(api.get_room_rate("R1")["hourly_rate"], 25000)
		self.assertIn("hourly_rate", api.get_indicative_rate("EQ1"))

	def test_FR_RES_006_thieu_ban_ghi(self):
		self.assertRaises(frappe.DoesNotExistError, api.get_indicative_rate, "KHONG-CO")
