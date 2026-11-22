import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.tests.utils import GOLDEN_PARAM, ensure, make_base, make_user


def _new(**over):
	make_base(job="DD")
	ensure("NC Job Title", "job_title_code", "BS", job_title_name="Bác sĩ", job_group="Bác sĩ")
	data = {
		"doctype": "NC Costing Parameter Set",
		"title": "Bộ thử",
		"effective_from": "2026-01-01",
		**GOLDEN_PARAM,
		"job_title_rates": [
			{"job_title": "BS", "salary_coefficient": 4.4, "allowance_coefficient": 0.6},
			{"job_title": "DD", "salary_coefficient": 3.0, "allowance_coefficient": 0.4},
		],
	}
	data.update(over)
	return frappe.get_doc(data)


def _lock_run(ps_name):
	return frappe.get_doc(
		{
			"doctype": "NC Costing Run",
			"title": "Lần thử",
			"fiscal_year": 2026,
			"costing_date": "2026-12-31",
			"parameter_set": ps_name,
			"status": "Đã khóa",
		}
	).insert(ignore_permissions=True)


class TestNCCostingParameterSet(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_TC_CLS_50_bo_moi_co_ba_tham_so_mac_dinh(self):
		ps = _new().insert()
		self.assertEqual(ps.expired_depreciation_mode, "ZERO")
		self.assertEqual(ps.material_recon_tolerance, 5)
		self.assertEqual(ps.volume_recon_tolerance, 2)
		self.assertEqual(ps.eqa_cost_category, "DRUG_SUPPLY")
		self.assertEqual(ps.rental_cost_category, "DEPRECIATION")
		self.assertEqual(ps.jv_cost_category, "DEPRECIATION")

	def test_TC_RES_05_don_gia_gio_cong_tren_doc(self):
		ps = _new().insert()
		rows = {r.job_title: r for r in ps.job_title_rates}
		self.assertEqual(rows["BS"].annual_cost, 185250000)
		self.assertAlmostEqual(rows["BS"].rate_per_hour, 87713.0682, places=4)
		self.assertEqual(rows["DD"].annual_cost, 125970000)
		self.assertAlmostEqual(rows["DD"].rate_per_hour, 59644.8864, places=4)

	def test_FR_RES_009_tham_so_ngoai_khoang_bi_tu_choi(self):
		with self.assertRaises(frappe.ValidationError):
			_new(accumulation_rate=100).insert()
		with self.assertRaises(frappe.ValidationError):
			_new(wastage_cap=120).insert()

	def test_TC_RES_06_bo_da_khoa_khong_sua_duoc(self):
		ps = _new().insert()
		run = _lock_run(ps.name)
		ps.reload()
		ps.base_salary = 3000000
		with self.assertRaises(frappe.ValidationError) as ctx:
			ps.save()
		self.assertIn(run.name, str(ctx.exception))
		self.assertEqual(frappe.db.get_value("NC Costing Parameter Set", ps.name, "base_salary"), 2500000)

	def test_TC_RES_06_bo_co_is_locked_khong_sua_duoc(self):
		ps = _new().insert()
		frappe.db.set_value("NC Costing Parameter Set", ps.name, "is_locked", 1)
		ps.reload()
		ps.title = "Đổi tên"
		self.assertRaises(frappe.ValidationError, ps.save)

	def test_TC_RES_06_bo_chua_khoa_sua_duoc(self):
		ps = _new().insert()
		ps.base_salary = 3000000
		ps.save()
		self.assertEqual(ps.reload().base_salary, 3000000)

	def test_TC_RES_06_bo_da_khoa_khong_xoa_duoc(self):
		ps = _new().insert()
		frappe.db.set_value("NC Costing Parameter Set", ps.name, "is_locked", 1)
		self.assertRaises(frappe.ValidationError, frappe.delete_doc, "NC Costing Parameter Set", ps.name)

	def test_TC_RES_06_nhan_ban_thanh_bo_moi_sua_duoc(self):
		ps = _new().insert()
		_lock_run(ps.name)
		ps.reload()
		new_name = ps.duplicate()
		self.assertNotEqual(new_name, ps.name)
		copy = frappe.get_doc("NC Costing Parameter Set", new_name)
		self.assertFalse(copy.get("is_locked"))
		self.assertEqual(len(copy.job_title_rates), 2)
		self.assertEqual(copy.base_salary, 2500000)
		copy.base_salary = 3100000
		copy.save()
		self.assertEqual(copy.reload().base_salary, 3100000)
		self.assertEqual(frappe.db.get_value("NC Costing Parameter Set", ps.name, "base_salary"), 2500000)

	def test_TC_RES_06_nhan_ban_can_quyen_tao(self):
		ps = _new().insert()
		frappe.set_user(make_user("ps.rm@normcore.test", "NC Resource Manager"))
		self.assertRaises(
			frappe.PermissionError, frappe.get_doc("NC Costing Parameter Set", ps.name).duplicate
		)

	def test_FR_ACC_007_auditor_chi_doc(self):
		ps = _new().insert()
		frappe.set_user(make_user("ps.auditor@normcore.test", "NC Auditor"))
		self.assertTrue(frappe.has_permission("NC Costing Parameter Set", "read"))
		for ptype in ("create", "write", "delete"):
			self.assertFalse(frappe.has_permission("NC Costing Parameter Set", ptype), ptype)
		self.assertRaises(
			frappe.PermissionError, frappe.get_doc("NC Costing Parameter Set", ps.name).duplicate
		)

	def test_FR_ACC_002_vai_tro_ngoai_ma_tran_khong_doc(self):
		frappe.set_user(make_user("ps.noroles@normcore.test", "NC Clinician"))
		self.assertFalse(frappe.has_permission("NC Costing Parameter Set", "read"))

	def test_FR_RES_009_finance_tao_duoc(self):
		make_base(job="DD")
		frappe.set_user(make_user("ps.finance@normcore.test", "NC Finance"))
		ps = _new()
		ps.insert()
		self.assertTrue(ps.name.startswith("PS-"))

	def test_ASM_065_patch_dien_mac_dinh_cho_bo_cu(self):
		from normcore.patches import backfill_parameter_set_defaults

		ps = _new().insert()
		frappe.db.set_value(
			"NC Costing Parameter Set",
			ps.name,
			{"expired_depreciation_mode": None, "eqa_cost_category": "", "wastage_cap": 33},
		)
		backfill_parameter_set_defaults.execute()
		row = frappe.db.get_value(
			"NC Costing Parameter Set",
			ps.name,
			["expired_depreciation_mode", "eqa_cost_category", "wastage_cap"],
		)
		self.assertEqual(row, ("ZERO", "DRUG_SUPPLY", 33))
