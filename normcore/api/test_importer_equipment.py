"""FEAT-010, FR-RES-012 (phần thiết bị, phòng): bộ nhập nc_equipment, nc_room."""

import io

import frappe
from frappe.tests.utils import FrappeTestCase
from openpyxl import Workbook, load_workbook

from normcore.api import importer as api
from normcore.core.importer import get_import_set, header_label
from normcore.tests.utils import ensure, make_base, make_user

EQ = "nc_equipment"
ROOM = "nc_room"


def xlsx(rows):
	wb = Workbook()
	for r in rows:
		wb.active.append(r)
	buf = io.BytesIO()
	wb.save(buf)
	return buf.getvalue()


def head(key):
	return [header_label(c) for c in get_import_set(key).columns]


def eq_row(code="NK-EQ1", **kw):
	vals = {
		"equipment_code": code,
		"equipment_name": "Thiết bị nhập",
		"department": "KHOA-TEST",
		"in_service_date": "2022-01-01",
		"funding_source": "Ngân sách",
		"original_cost": 1200000000,
		"useful_life_years": 8,
		"annual_maintenance_cost": 30000000,
		"annual_calibration_cost": 6000000,
		"planned_hours_per_year": 2112,
		"utilization_rate": 0.5,
	}
	vals.update(kw)
	return [vals.get(c.fieldname) for c in get_import_set(EQ).columns]


class TestEquipmentImport(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		make_base()
		self.rm = make_user("rm.impeq@normcore.test", "NC Resource Manager")
		self.fin = make_user("fin.impeq@normcore.test", "NC Finance")
		self.auditor = make_user("aud.impeq@normcore.test", "NC Auditor")
		self.clin = make_user("clin.impeq@normcore.test", "NC Clinician")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_FR_RES_012_tai_mau_roi_nhap_lai_khong_trung(self):
		frappe.set_user(self.rm)
		name, content = api.build_template_file(EQ)
		rows = list(load_workbook(io.BytesIO(content)).active.iter_rows(values_only=True))
		self.assertEqual(list(rows[0]), head(EQ))
		self.assertIn(EQ, name)
		ensure("NC Cost Center", "cost_center_code", "VD-K01", cost_center_name="VD", center_type="Lâm sàng")
		ensure(
			"NC Department",
			"department_code",
			"VD-K01",
			department_name="VD",
			department_type="Lâm sàng",
			cost_center="VD-K01",
		)
		first = api.run_import(EQ, content, "ghi")
		self.assertEqual((first["created"], first["error_count"]), (1, 0), first["errors"])
		again = api.run_import(EQ, content, "ghi")
		self.assertEqual((again["unchanged"], again["created"], again["error_count"]), (1, 0, 0))

	def test_FR_RES_012_nhap_va_cap_nhat_theo_ma_giu_dong_con(self):
		frappe.set_user(self.rm)
		res = api.run_import(EQ, xlsx([head(EQ), eq_row()]), "ghi")
		self.assertEqual((res["created"], res["error_count"]), (1, 0), res["errors"])
		doc = frappe.get_doc("NC Equipment", "NK-EQ1")
		self.assertEqual(
			(doc.acquisition_mode, doc.allocation_basis), ("Mua", "Giờ kế hoạch")
		)  # mặc định DocType
		doc.append(
			"components",
			{"component_name": "Đèn", "replacement_cost": 1, "life_basis": "Tháng", "life_value": 12},
		)
		doc.append("department_allocations", {"department": "KHOA-TEST", "share_pct": 100})
		doc.save()
		res = api.run_import(
			EQ, xlsx([head(EQ), eq_row(equipment_name="Tên mới", annual_maintenance_cost=31000000)]), "ghi"
		)
		self.assertEqual((res["updated"], res["created"], res["error_count"]), (1, 0, 0))
		doc.reload()
		self.assertEqual((doc.equipment_name, doc.annual_maintenance_cost), ("Tên mới", 31000000))
		self.assertEqual(len(doc.components), 1)
		self.assertEqual([r.share_pct for r in doc.department_allocations], [100])
		self.assertEqual(doc.original_cost, 1200000000)  # ô trống/giống: giữ nguyên

	def test_FR_RES_012_dong_loi_khong_lam_hong_dong_khac(self):
		frappe.set_user(self.rm)
		rows = [
			head(EQ),
			eq_row("NK-OK"),
			eq_row(
				"NK-THUE", acquisition_mode="Thuê", original_cost=None, useful_life_years=None
			),  # thiếu hợp đồng
			eq_row("NK-MUA", original_cost=None),  # thiếu nguyên giá
			eq_row("NK-KHOA", department="KHOA-LA"),
			eq_row("NK-OK"),  # trùng mã trong tệp
			eq_row(
				"NK-THUE2",
				acquisition_mode="Thuê",
				original_cost=None,
				useful_life_years=None,
				annual_contract_cost=450000000,
			),
		]
		res = api.run_import(EQ, xlsx(rows), "ghi")
		self.assertEqual(res["created"], 2)
		self.assertEqual(res["error_count"], 4)
		self.assertTrue(frappe.db.exists("NC Equipment", "NK-OK"))
		self.assertTrue(frappe.db.exists("NC Equipment", "NK-THUE2"))
		for code in ("NK-THUE", "NK-MUA", "NK-KHOA"):
			self.assertFalse(frappe.db.exists("NC Equipment", code), code)

	def test_FR_RES_012_thieu_cot_bat_buoc_va_gia_tri_ngoai_danh_sach(self):
		frappe.set_user(self.rm)
		res = api.run_import(
			EQ,
			xlsx(
				[head(EQ), eq_row("NK-X", funding_source=None), eq_row("NK-Y", acquisition_mode="Cho mượn")]
			),
			"ghi",
		)
		self.assertEqual((res["created"], res["error_count"]), (0, 2))

	def test_FR_ACC_002_quyen_nhap_thiet_bi(self):
		content = xlsx([head(EQ), eq_row("NK-Q")])
		frappe.set_user(self.fin)
		self.assertIn(EQ, [s["key"] for s in api.list_import_sets()])
		self.assertEqual(api.run_import(EQ, content, "ghi")["created"], 1)
		frappe.set_user("Administrator")
		frappe.db.delete("NC Equipment", {"equipment_code": "NK-Q"})
		for user in (self.auditor, self.clin):
			frappe.set_user(user)
			self.assertNotIn(EQ, [s["key"] for s in api.list_import_sets()])
			self.assertNotIn(ROOM, [s["key"] for s in api.list_import_sets()])
			for mode in ("thu", "ghi"):
				self.assertRaises(frappe.PermissionError, api.run_import, EQ, content, mode)
				self.assertRaises(frappe.PermissionError, api.run_import, ROOM, content, mode)
		frappe.set_user("Administrator")
		self.assertFalse(frappe.db.exists("NC Equipment", "NK-Q"))

	def test_FR_RES_012_nhap_phong(self):
		frappe.set_user(self.rm)
		rows = [
			head(ROOM),
			["NK-R1", "Phòng R1", "KHOA-TEST", None, 52800000, 2112],
			["NK-R2", "Phòng thiếu giờ", "KHOA-TEST", 40, 1000, None],
			["NK-R3", "Phòng giờ 0", "KHOA-TEST", 40, 1000, 0],
		]
		res = api.run_import(ROOM, xlsx(rows), "ghi")
		self.assertEqual((res["created"], res["error_count"]), (1, 2), res["errors"])
		self.assertTrue(frappe.db.exists("NC Room", "NK-R1"))
		again = api.run_import(ROOM, xlsx(rows[:2]), "ghi")
		self.assertEqual((again["unchanged"], again["created"]), (1, 0))
		upd = api.run_import(
			ROOM, xlsx([rows[0], ["NK-R1", "Phòng R1", "KHOA-TEST", 40, 52800000, 2112]]), "ghi"
		)
		self.assertEqual(upd["updated"], 1)
		self.assertEqual(frappe.db.get_value("NC Room", "NK-R1", "area_m2"), 40)
