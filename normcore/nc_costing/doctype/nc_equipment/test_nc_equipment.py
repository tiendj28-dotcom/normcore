from decimal import Decimal

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.tests.utils import make_base, make_chain_data, make_user

EQ1 = dict(
	equipment_code="EQ1",
	equipment_name="Thiết bị EQ1",
	acquisition_mode="Mua",
	allocation_basis="Giờ kế hoạch",
	original_cost=1200000000,
	useful_life_years=8,
	in_service_date="2022-01-01",
	funding_source="Ngân sách",
	annual_maintenance_cost=30000000,
	annual_calibration_cost=6000000,
	planned_hours_per_year=2112,
	utilization_rate=0.5,
)


def _eq(**kw):
	_, dept, _ = make_base()
	data = {"doctype": "NC Equipment", "department": dept, **EQ1, **kw}
	return frappe.get_doc(data)


class TestNCEquipment(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_TC_RES_03_eq1_khau_hao_va_don_gia_gio(self):
		r = _eq().insert().indicative(on="2026-12-31")
		self.assertEqual(r["annual_depreciation"], 150000000)
		self.assertEqual(Decimal(str(r["hourly_rate"])), Decimal("176136.3636"))
		self.assertFalse(r["expired"])

	def test_TC_RES_04_v2_het_thoi_gian_su_dung_theo_bo_tham_so(self):
		eq = _eq(equipment_code="V2", in_service_date="2015-01-01").insert()
		zero = eq.indicative(on="2026-12-31", expired_mode="ZERO")
		self.assertEqual(zero["annual_depreciation"], 0)
		self.assertEqual(Decimal(str(zero["hourly_rate"])), Decimal("34090.9091"))
		self.assertTrue(zero["expired"])
		cont = eq.indicative(on="2026-12-31", expired_mode="CONTINUE")
		self.assertEqual(cont["annual_depreciation"], 150000000)

	def test_TC_CLS_48_thue_thieu_chi_phi_hop_dong_bi_tu_choi(self):
		bad = _eq(acquisition_mode="Thuê", original_cost=None, useful_life_years=None)
		self.assertRaises(frappe.ValidationError, bad.insert)
		ok = _eq(
			acquisition_mode="Thuê",
			original_cost=None,
			useful_life_years=None,
			annual_contract_cost=450000000,
		)
		self.assertEqual(ok.insert().indicative(on="2026-12-31")["annual_depreciation"], 450000000)

	def test_TC_CLS_48_mua_thieu_nguyen_gia_bi_tu_choi(self):
		self.assertRaises(frappe.ValidationError, _eq(original_cost=None).insert)

	def test_TC_CLS_48_chia_theo_so_ket_qua_khong_can_gio_ke_hoach(self):
		eq = _eq(allocation_basis="Số kết quả", planned_hours_per_year=None, utilization_rate=None).insert()
		self.assertIsNone(eq.indicative(on="2026-12-31")["hourly_rate"])
		bad = _eq(equipment_code="EQ9", planned_hours_per_year=None)
		self.assertRaises(frappe.ValidationError, bad.insert)

	def test_TC_CLS_49_ty_le_theo_khoa(self):
		_, dept, _ = make_base()
		from normcore.tests.utils import ensure

		ensure("NC Cost Center", "cost_center_code", "KHOA-B", cost_center_name="B", center_type="Lâm sàng")
		ensure(
			"NC Department",
			"department_code",
			"KHOA-B",
			department_name="B",
			department_type="Lâm sàng",
			cost_center="KHOA-B",
		)
		bad = _eq(
			department_allocations=[
				{"department": dept, "share_pct": 60},
				{"department": "KHOA-B", "share_pct": 30},
			]
		)
		self.assertRaises(frappe.ValidationError, bad.insert)
		ok = _eq(
			department_allocations=[
				{"department": dept, "share_pct": 60},
				{"department": "KHOA-B", "share_pct": 40},
			]
		).insert()
		r = ok.indicative(on="2026-12-31")
		self.assertAlmostEqual(r["annual_equipment_cost"], 186000000 * 0.6)

	def test_FR_RES_023_linh_kien_theo_thang_va_khong_hop_le(self):
		eq = _eq(
			components=[
				{
					"component_name": "Đèn",
					"replacement_cost": 24000000,
					"life_basis": "Tháng",
					"life_value": 12,
				}
			]
		).insert()
		self.assertEqual(eq.indicative(on="2026-12-31")["annual_equipment_cost"], 186000000 + 24000000)
		bad = _eq(
			equipment_code="EQ8",
			components=[
				{"component_name": "Đèn", "replacement_cost": 1, "life_basis": "Tháng", "life_value": 0}
			],
		)
		self.assertRaises(frappe.ValidationError, bad.insert)

	def test_FR_RES_021_dat_theo_hoa_chat_khong_khau_hao(self):
		eq = _eq(
			acquisition_mode="Đặt theo hóa chất",
			original_cost=None,
			useful_life_years=None,
			maintenance_vendor_paid=1,
		).insert()
		r = eq.indicative(on="2026-12-31")
		self.assertEqual(r["annual_depreciation"], 0)
		self.assertEqual(r["annual_equipment_cost"], 6000000)

	def test_FR_RES_026_luu_truong_dien(self):
		eq = _eq(
			power_kw=2,
			power_standby_kw=0.5,
			run_hours_per_day=8,
			standby_hours_per_day=16,
			continuous_power=1,
		).insert()
		eq.reload()
		self.assertEqual((eq.power_kw, eq.power_standby_kw, eq.continuous_power), (2, 0.5, 1))

	def test_FR_RES_005_trung_ma_bi_tu_choi(self):
		_eq().insert()
		self.assertRaises(frappe.DuplicateEntryError, _eq().insert)

	def test_FR_ACC_002_finance_va_resource_manager_ghi_duoc(self):
		users = {
			r: make_user(f"eq.w{i}@normcore.test", r)
			for i, r in enumerate(("NC Finance", "NC Resource Manager"))
		}
		_eq().insert()
		for role, email in users.items():
			frappe.set_user(email)
			self.assertTrue(frappe.has_permission("NC Equipment", "write"), role)
			self.assertTrue(frappe.has_permission("NC Equipment", "create"), role)

	def test_FR_ACC_002_vai_tro_khong_quyen_va_chi_doc(self):
		none = make_user("eq.none@normcore.test", "NC Document Controller")
		clin = make_user("eq.clin@normcore.test", "NC Clinician")
		frappe.set_user(none)
		self.assertFalse(frappe.has_permission("NC Equipment", "read"))
		frappe.set_user(clin)
		self.assertTrue(frappe.has_permission("NC Equipment", "read"))
		self.assertFalse(frappe.has_permission("NC Equipment", "write"))

	def test_FR_ACC_007_auditor_chi_doc_khong_sua(self):
		eq = _eq().insert()
		frappe.set_user(make_user("eq.auditor@normcore.test", "NC Auditor"))
		self.assertTrue(frappe.has_permission("NC Equipment", "read"))
		for ptype in ("create", "write", "delete"):
			self.assertFalse(frappe.has_permission("NC Equipment", ptype), ptype)
		eq.equipment_name = "Sửa lén"
		self.assertRaises(frappe.PermissionError, eq.save)
		self.assertRaises(frappe.PermissionError, _eq(equipment_code="EQ7").insert)

	def test_FR_ADM_005_xoa_khi_dang_duoc_tham_chieu_bi_chan(self):
		service, dept, _ = make_base()
		eq = _eq().insert()
		chain = make_chain_data(service, dept)
		ns = frappe.get_doc("NC Norm Set", chain.norm_set)
		ns.flags.ignore_validate_update_after_submit = True
		ns.status = "Nháp"
		ns.append(
			"lines",
			{
				"line_id": "L99",
				"component": "EQUIPMENT",
				"resource_doctype": "NC Equipment",
				"resource": eq.name,
				"hospital_qty": 20,
				"uom": "phút",
				"basis": "Quy trình",
			},
		)
		ns.db_update()
		ns.lines[-1].db_insert()
		frappe.set_user(make_user("eq.admin@normcore.test", "NC Admin"))
		with self.assertRaises(frappe.LinkExistsError):
			frappe.delete_doc("NC Equipment", eq.name)
