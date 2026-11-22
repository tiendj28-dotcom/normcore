import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.tests.utils import ensure, make_user


def _item(code="MH-P01"):
	return ensure("NC Item", "item_code", code, item_name="Mặt hàng thử", item_type="Thuốc", uom="viên")


def _price(**kw):
	values = {
		"doctype": "NC Item Price",
		"item": "MH-P01",
		"unit_price": 1000,
		"price_source": "Hóa đơn",
		"document_no": "HD-01",
		"document_date": "2026-01-10",
		"valid_from": "2026-01-10",
	}
	values.update(kw)
	return frappe.get_doc(values)


class TestNCItemPrice(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		_item()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_FR_RES_002_thieu_truong_bat_buoc_bi_tu_choi(self):
		for missing in ("item", "unit_price", "price_source", "document_no", "document_date", "valid_from"):
			doc = _price()
			doc.set(missing, None)
			with self.subTest(missing=missing), self.assertRaises(frappe.MandatoryError):
				doc.insert()

	def test_TC_CLS_46_nguon_hop_dong_co_ngay_het_hieu_luc_luu_duoc(self):
		doc = _price(price_source="Hợp đồng", valid_to="2026-12-31").insert()
		doc = frappe.get_doc("NC Item Price", doc.name)
		self.assertEqual(doc.price_source, "Hợp đồng")
		self.assertEqual(str(doc.valid_to), "2026-12-31")
		self.assertEqual(doc.verification_status, "Chưa xác minh")

	def test_FR_RES_002_nam_nguon_gia(self):
		options = frappe.get_meta("NC Item Price").get_field("price_source").options.split("\n")[1:]
		self.assertEqual(options, ["Trúng thầu", "Hợp đồng", "Hóa đơn", "Giá công bố", "Báo giá"])

	def test_FR_RES_002_ngay_het_hieu_luc_truoc_ngay_bat_dau_bi_tu_choi(self):
		self.assertRaises(frappe.ValidationError, _price(valid_to="2026-01-09").insert)

	def test_FR_RES_002_don_gia_phai_duong(self):
		for bad in (0, -5):
			self.assertRaises(frappe.ValidationError, _price(unit_price=bad).insert)

	def test_FR_RES_002_don_gia_giu_4_so_le(self):
		doc = _price(unit_price=33.3333).insert()
		self.assertEqual(frappe.db.get_value("NC Item Price", doc.name, "unit_price"), 33.3333)

	def test_TC_CLS_46_xac_minh_khi_chua_co_tep_bi_tu_choi(self):
		doc = _price().insert()
		doc.verification_status = "Đã xác minh"
		with self.assertRaises(frappe.ValidationError) as ctx:
			doc.save()
		self.assertIn("tệp chứng từ", str(ctx.exception))

	def test_FR_RES_016_xac_minh_co_tep_ghi_nguoi_va_thoi_diem(self):
		doc = _price(attachment="/files/hd-01.pdf").insert()
		self.assertIsNone(doc.verified_by)
		doc.verification_status = "Đã xác minh"
		doc.save()
		doc = frappe.get_doc("NC Item Price", doc.name)
		self.assertEqual(doc.verified_by, "Administrator")
		self.assertTrue(doc.verified_on)

	def test_FR_RES_016_nguoi_xac_minh_khong_do_nguoi_dung_tu_khai(self):
		doc = _price(
			attachment="/files/hd-01.pdf",
			verification_status="Đã xác minh",
			verified_by="Guest",
			verified_on="2000-01-01 00:00:00",
		).insert()
		self.assertEqual(doc.verified_by, "Administrator")
		self.assertNotEqual(str(doc.verified_on)[:4], "2000")
		doc.verified_by = "Guest"
		doc.save()
		self.assertEqual(frappe.db.get_value("NC Item Price", doc.name, "verified_by"), "Administrator")

	def test_FR_RES_016_bo_xac_minh_xoa_nguoi_va_thoi_diem(self):
		doc = _price(attachment="/files/hd-01.pdf", verification_status="Đã xác minh").insert()
		self.assertTrue(doc.verified_by)
		doc.verification_status = "Chưa xác minh"
		doc.save()
		self.assertIsNone(frappe.db.get_value("NC Item Price", doc.name, "verified_by"))

	def test_FR_ACC_002_quyen_theo_ma_tran(self):
		cases = {"NC Finance": True, "NC Resource Manager": True, "NC Admin": True, "NC Clinician": False}
		users = {role: make_user(f"price.{i}@normcore.test", role) for i, role in enumerate(cases)}
		for role, write in cases.items():
			frappe.set_user(users[role])
			with self.subTest(role=role):
				self.assertTrue(frappe.has_permission("NC Item Price", "read"))
				self.assertEqual(bool(frappe.has_permission("NC Item Price", "create")), write)

	def test_FR_ACC_007_auditor_chi_doc(self):
		frappe.set_user(make_user("price.auditor@normcore.test", "NC Auditor"))
		self.assertTrue(frappe.has_permission("NC Item Price", "read"))
		self.assertRaises(frappe.PermissionError, _price().insert)

	def test_FR_ACC_002_vai_tro_khong_quyen_khong_doc(self):
		users = {
			r: make_user(f"price.no{i}@normcore.test", r)
			for i, r in enumerate(("NC Council Member", "NC Document Controller"))
		}
		for role, email in users.items():
			frappe.set_user(email)
			self.assertFalse(frappe.has_permission("NC Item Price", "read"), role)
