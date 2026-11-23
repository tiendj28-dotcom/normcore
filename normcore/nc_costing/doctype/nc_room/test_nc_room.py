import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.tests.utils import make_base, make_user


def _room(**kw):
	_, dept, _ = make_base()
	data = {
		"doctype": "NC Room",
		"room_code": "R1",
		"room_name": "Phòng R1",
		"department": dept,
		"annual_infrastructure_cost": 52800000,
		"available_hours_per_year": 2112,
	}
	data.update(kw)
	return frappe.get_doc(data)


class TestNCRoom(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_TC_RES_10_thieu_gio_khai_thac_bi_tu_choi_roi_r1_luu_duoc(self):
		bad = _room(available_hours_per_year=None)
		self.assertRaises(frappe.ValidationError, bad.insert)
		ok = _room().insert()
		self.assertEqual(ok.name, "R1")
		from normcore.costing.resources import room_hourly_rate

		self.assertEqual(room_hourly_rate(ok.annual_infrastructure_cost, ok.available_hours_per_year), 25000)

	def test_FR_RES_008_gio_khong_hop_le_bi_tu_choi(self):
		self.assertRaises(frappe.ValidationError, _room(available_hours_per_year=0).insert)
		self.assertRaises(frappe.ValidationError, _room(annual_infrastructure_cost=-1).insert)

	def test_FR_RES_008_trung_ma_bi_tu_choi(self):
		_room().insert()
		self.assertRaises(frappe.DuplicateEntryError, _room().insert)

	def test_FR_ACC_002_finance_va_resource_manager_ghi_duoc(self):
		users = {
			r: make_user(f"room.w{i}@normcore.test", r)
			for i, r in enumerate(("NC Finance", "NC Resource Manager"))
		}
		for role, email in users.items():
			frappe.set_user(email)
			self.assertTrue(frappe.has_permission("NC Room", "create"), role)

	def test_FR_ACC_002_vai_tro_khong_quyen_va_chi_doc(self):
		none, clin = (
			make_user("room.none@normcore.test"),
			make_user("room.clin@normcore.test", "NC Clinician"),
		)
		frappe.set_user(none)
		self.assertFalse(frappe.has_permission("NC Room", "read"))
		frappe.set_user(clin)
		self.assertTrue(frappe.has_permission("NC Room", "read"))
		self.assertFalse(frappe.has_permission("NC Room", "write"))

	def test_FR_ACC_007_auditor_chi_doc(self):
		_room().insert()
		frappe.set_user(make_user("room.auditor@normcore.test", "NC Auditor"))
		self.assertTrue(frappe.has_permission("NC Room", "read"))
		for ptype in ("create", "write", "delete"):
			self.assertFalse(frappe.has_permission("NC Room", ptype), ptype)
		self.assertRaises(frappe.PermissionError, _room(room_code="R2").insert)

	def test_FR_ADM_005_admin_xoa_duoc_phong_chua_dung(self):
		_room().insert()
		frappe.set_user(make_user("room.admin@normcore.test", "NC Admin"))
		frappe.delete_doc("NC Room", "R1")
		self.assertFalse(frappe.db.exists("NC Room", "R1"))
