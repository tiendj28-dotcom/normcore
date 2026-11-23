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

	# --- ASM-091: khóa khi đã xác minh
	def _verified(self, **kw):
		return _price(attachment="/files/hd-01.pdf", verification_status="Đã xác minh", **kw).insert()

	def test_FR_RES_016_da_xac_minh_khong_sua_noi_dung(self):
		changes = {
			"unit_price": 2000,
			"price_source": "Báo giá",
			"document_no": "HD-02",
			"document_date": "2026-01-11",
			"valid_from": "2026-01-11",
			"valid_to": "2026-12-31",
			"attachment": "/files/khac.pdf",
		}
		for field, value in changes.items():
			doc = self._verified()
			with self.subTest(field=field):
				doc = frappe.get_doc("NC Item Price", doc.name)
				doc.set(field, value)
				with self.assertRaises(frappe.ValidationError) as ctx:
					doc.save()
				self.assertIn("bỏ xác minh", str(ctx.exception))
			frappe.db.rollback()
			_item()

	def test_FR_RES_016_da_xac_minh_khong_doi_mat_hang(self):
		_item("MH-P02")
		doc = self._verified()
		doc = frappe.get_doc("NC Item Price", doc.name)
		doc.item = "MH-P02"
		self.assertRaises(frappe.ValidationError, doc.save)

	def test_FR_RES_016_luu_lai_khong_doi_gi_van_duoc(self):
		doc = frappe.get_doc("NC Item Price", self._verified().name)
		doc.valid_from = str(doc.valid_from)  # cùng giá trị, khác kiểu
		doc.save()
		self.assertEqual(frappe.db.get_value("NC Item Price", doc.name, "verification_status"), "Đã xác minh")

	def test_FR_RES_016_bo_xac_minh_roi_sua_duoc_ca_cung_luot(self):
		doc = frappe.get_doc("NC Item Price", self._verified().name)
		doc.verification_status = "Chưa xác minh"
		doc.unit_price = 2500
		doc.save()
		doc = frappe.get_doc("NC Item Price", doc.name)
		self.assertEqual((doc.unit_price, doc.verification_status), (2500, "Chưa xác minh"))
		self.assertIsNone(doc.verified_by)

	# --- B3: ngày dạng chuỗi so với ngày từ CSDL
	def test_FR_RES_002_doi_rieng_valid_to_sau_khi_nap_lai(self):
		doc = frappe.get_doc("NC Item Price", _price().insert().name)
		doc.valid_to = "2026-12-31"  # chuỗi, trong khi valid_from nạp từ CSDL là date
		doc.save()
		doc = frappe.get_doc("NC Item Price", doc.name)
		doc.valid_to = "2026-01-01"
		with self.assertRaises(frappe.ValidationError) as ctx:
			doc.save()
		self.assertNotIsInstance(ctx.exception, TypeError)
		self.assertIn("hết hiệu lực", str(ctx.exception))

	# --- B4: nhân bản không chép xác minh
	def test_FR_RES_016_nhan_ban_khong_chep_xac_minh_va_tep(self):
		src = self._verified()
		copy = frappe.copy_doc(
			frappe.get_doc("NC Item Price", src.name), ignore_no_copy=False
		)  # như nút Nhân bản
		copy.unit_price = 1111
		copy.insert()
		copy = frappe.get_doc("NC Item Price", copy.name)
		self.assertEqual(copy.verification_status, "Chưa xác minh")
		self.assertFalse(copy.attachment)
		self.assertFalse(copy.verified_by)
		self.assertFalse(copy.verified_on)
		self.assertNotEqual(copy.price_code, src.price_code)

	# --- AMD-008: price_code
	def test_FR_RES_012_price_code_de_trong_lay_bang_ten(self):
		doc = _price().insert()
		self.assertEqual(frappe.db.get_value("NC Item Price", doc.name, "price_code"), doc.name)

	def test_FR_RES_012_price_code_tu_dat_duoc_giu(self):
		doc = _price(price_code="GIA-A1").insert()
		self.assertEqual(frappe.db.get_value("NC Item Price", doc.name, "price_code"), "GIA-A1")

	def test_FR_RES_012_price_code_trung_bi_tu_choi(self):
		_price(price_code="GIA-A2").insert()
		self.assertRaises(frappe.ValidationError, _price(price_code="GIA-A2", document_no="X").insert)

	def test_FR_RES_012_khong_tu_dat_ma_dang_dg_so(self):
		with self.assertRaises(frappe.ValidationError) as ctx:
			_price(price_code="DG-99999").insert()
		self.assertIn("DG-", str(ctx.exception))
