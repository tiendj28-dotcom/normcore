import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.tests.utils import make_user


def _item(code="MH-T01", **kw):
	values = {"item_code": code, "item_name": "Mặt hàng thử", "item_type": "Thuốc", "uom": "viên"}
	values.update(kw)
	return frappe.get_doc({"doctype": "NC Item", **values})


class TestNCItem(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_TC_RES_09_thieu_don_vi_tinh_bi_tu_choi_roi_luu_duoc(self):
		doc = frappe.get_doc(
			{"doctype": "NC Item", "item_code": "MH-T02", "item_name": "Gạc", "item_type": "Vật tư tiêu hao"}
		)
		with self.assertRaises(frappe.MandatoryError) as ctx:
			doc.insert()
		self.assertIn("uom", str(ctx.exception))
		doc.uom = "cái"
		doc.insert()
		self.assertEqual(frappe.db.get_value("NC Item", "MH-T02", "reuse_count"), 1)

	def test_FR_RES_001_thieu_ma_ten_loai_bi_tu_choi(self):
		for missing in ("item_code", "item_name", "item_type"):
			values = {"item_code": "MH-T03", "item_name": "x", "item_type": "Thuốc", "uom": "viên"}
			values.pop(missing)
			with (
				self.subTest(missing=missing),
				self.assertRaises(frappe.ValidationError),
			):  # thiếu mã: lỗi đặt tên
				frappe.get_doc({"doctype": "NC Item", **values}).insert()

	def test_FR_RES_001_so_lan_dung_phai_tu_1(self):
		self.assertRaises(frappe.ValidationError, _item("MH-T04", reuse_count=0).insert)
		self.assertEqual(_item("MH-T05", reuse_count=200).insert().reuse_count, 200)

	def test_FR_RES_001_trung_ma_bi_tu_choi(self):
		_item("MH-T06").insert()
		self.assertRaises(frappe.DuplicateEntryError, _item("MH-T06").insert)

	def test_FR_RES_018_hoa_chat_can_so_don_vi_dinh_muc_duong(self):
		for kind in ("Hóa chất", "Chất chuẩn", "Vật liệu nội kiểm"):
			with self.subTest(kind=kind):
				self.assertRaises(
					frappe.ValidationError,
					_item("MH-T07", item_type=kind, norm_units_per_purchase_unit=0).insert,
				)
		doc = _item(
			"MH-T08",
			item_type="Hóa chất",
			uom="hộp",
			norm_uom="test",
			norm_units_per_purchase_unit=200,
			nominal_tests=200,
			open_stability_days=30,
			is_main_reagent=1,
		).insert()
		self.assertEqual(doc.norm_units_per_purchase_unit, 200)
		self.assertEqual(doc.open_stability_days, 30)

	def test_FR_RES_018_mac_dinh_1_cho_loai_khac(self):
		self.assertEqual(_item("MH-T09").insert().norm_units_per_purchase_unit, 1)

	def test_FR_RES_018_hai_loai_moi_co_trong_danh_sach(self):
		options = frappe.get_meta("NC Item").get_field("item_type").options.split("\n")[1:]
		self.assertIn("Chất chuẩn", options)
		self.assertIn("Vật liệu nội kiểm", options)

	def test_FR_ACC_002_quyen_theo_ma_tran(self):
		cases = {
			"NC Finance": (True, True),
			"NC Resource Manager": (True, True),
			"NC Admin": (True, True),
			"NC Clinician": (True, False),
			"NC Director": (True, False),
			"NC Auditor": (True, False),
			"NC Council Member": (False, False),
			"NC Document Controller": (False, False),
		}
		users = {role: make_user(f"item.{i}@normcore.test", role) for i, role in enumerate(cases)}
		for role, (can_read, can_write) in cases.items():
			frappe.set_user(users[role])
			with self.subTest(role=role):
				self.assertEqual(bool(frappe.has_permission("NC Item", "read")), can_read)
				self.assertEqual(bool(frappe.has_permission("NC Item", "create")), can_write)
				self.assertFalse(frappe.has_permission("NC Item", "delete"))

	def test_FR_ACC_007_auditor_chi_doc_khong_ghi(self):
		frappe.set_user(make_user("item.auditor@normcore.test", "NC Auditor"))
		self.assertRaises(frappe.PermissionError, _item("MH-T10").insert)

	def test_FR_ACC_002_vai_tro_ngoai_ma_tran_khong_doc(self):
		frappe.set_user(make_user("item.noroles@normcore.test"))
		self.assertFalse(frappe.has_permission("NC Item", "read"))
