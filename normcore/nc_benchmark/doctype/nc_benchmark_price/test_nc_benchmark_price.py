import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.tests.benchmark_utils import make_category, make_facility, make_service, price_values
from normcore.tests.utils import make_user

DOCTYPE = "NC Benchmark Price"


def _price(**kw):
	return frappe.get_doc(price_values(**kw))


class TestNCBenchmarkPrice(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		make_facility()
		make_category()
		make_service("GTC-DV-01", "Định lượng Glucose máu")
		make_service("GTC-DV-02", "Siêu âm ổ bụng tổng quát")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_FR_BM_002_bat_buoc_khi_nhap_tay(self):
		for missing in ("facility", "price", "price_category", "effective_date"):
			doc = _price()
			doc.set(missing, None)
			with self.subTest(missing=missing):
				self.assertRaises(frappe.ValidationError, doc.insert)
		# thiếu nguồn
		self.assertRaises(frappe.ValidationError, _price(source_doc_no=None).insert)
		# giá <= 0
		for bad in (0, -1):
			self.assertRaises(frappe.ValidationError, _price(price=bad).insert)
		# đủ: lưu được; có nguồn là đường dẫn hoặc tệp cũng được
		_price(source_doc_no=None, source_url="https://example.test/bang-gia").insert()
		_price(source_doc_no=None, source_file="/files/bang-gia.pdf", effective_date="2026-02-01").insert()

	def test_FR_BM_002_ten_hoac_ma(self):
		# thiếu cả mã và tên gốc
		with self.assertRaises(frappe.ValidationError) as ctx:
			_price(service_name_raw=None, technical_service=None).insert()
		self.assertIn("mã dịch vụ hoặc tên", str(ctx.exception))
		# chỉ có mã: điền tên dịch vụ vào tên gốc (ASM-026-04)
		doc = _price(service_name_raw=None, technical_service="GTC-DV-01").insert()
		self.assertEqual(doc.service_name_raw, "Định lượng Glucose máu")

	def test_FR_BM_002_xac_nhan_khi_chua_co_ma_bi_tu_choi(self):
		doc = _price(service_name_raw="Tên lạ không khớp", status="Đề xuất").insert()
		self.assertEqual((doc.status, doc.technical_service), ("Đề xuất", None))
		doc.status = "Đã xác nhận"
		with self.assertRaises(frappe.ValidationError) as ctx:
			doc.save()
		self.assertIn("Chưa gắn mã", str(ctx.exception))

	def test_FR_BM_004_trang_thai_ban_dau(self):
		# tên gốc khớp dịch vụ: đề xuất mã, trạng thái Đề xuất, chưa có người xác nhận
		d1 = _price(service_name_raw="dinh luong glucose mau").insert()
		self.assertEqual((d1.technical_service, d1.status, d1.verified_by), ("GTC-DV-01", "Đề xuất", None))
		# người dùng tự gắn mã: Đã xác nhận ngay, người xác nhận là người nhập (ASM-026-02)
		d2 = _price(
			technical_service="GTC-DV-02", service_name_raw="Siêu âm bụng", effective_date="2026-02-01"
		).insert()
		self.assertEqual((d2.status, d2.verified_by), ("Đã xác nhận", "Administrator"))
		self.assertTrue(d2.verified_on)
		# có cờ keep_status: giữ Đề xuất
		d3 = _price(
			technical_service="GTC-DV-02", service_name_raw="Siêu âm bụng khác", effective_date="2026-03-01"
		)
		d3.flags.keep_status = True
		d3.insert()
		self.assertEqual((d3.status, d3.verified_by), ("Đề xuất", None))
		# chuyển Đề xuất -> Đã xác nhận ghi người và thời điểm; trả về Đề xuất thì xóa
		d1.status = "Đã xác nhận"
		d1.save()
		self.assertEqual(frappe.get_doc(DOCTYPE, d1.name).verified_by, "Administrator")
		d1.status = "Đề xuất"
		d1.save()
		d1 = frappe.get_doc(DOCTYPE, d1.name)
		self.assertIsNone(d1.verified_by)
		self.assertIsNone(d1.verified_on)

	def test_TC_BM_02_tu_choi_dong_trung(self):
		first = _price(technical_service="GTC-DV-01").insert()
		# cùng đơn vị, dịch vụ (mã), loại giá, ngày: từ chối
		with self.assertRaises(frappe.ValidationError) as ctx:
			_price(technical_service="GTC-DV-01", service_name_raw="Tên khác").insert()
		self.assertIn(first.name, str(ctx.exception))
		# cùng tên gốc chuẩn hóa, chưa gắn mã: từ chối
		self.assertRaises(
			frappe.ValidationError,
			_price(service_name_raw="ĐỊNH LƯỢNG glucose máu", technical_service=None).insert,
		)
		# khác ngày hiệu lực: lưu được
		_price(technical_service="GTC-DV-01", effective_date="2026-02-01").insert()
		# dòng Loại bỏ không tính trùng
		first.status = "Loại bỏ"
		first.save()
		_price(technical_service="GTC-DV-01").insert()
		# sửa một dòng không tự coi là trùng với chính nó
		other = _price(
			technical_service="GTC-DV-02", service_name_raw="Siêu âm", effective_date="2026-04-01"
		).insert()
		other.price = 30000
		other.save()

	def test_FR_BM_001_chan_xoa_don_vi_dang_dung(self):
		_price(technical_service="GTC-DV-01").insert()
		with self.assertRaises(frappe.LinkExistsError):
			frappe.delete_doc("NC Benchmark Facility", "Bệnh viện thử GTC")
		# đơn vị chưa có giá xóa được (Administrator)
		make_facility("Đơn vị chưa dùng")
		frappe.delete_doc("NC Benchmark Facility", "Đơn vị chưa dùng")

	def test_quyen_feat_026_gia(self):
		cases = {
			"NC Finance": (True, True),
			"NC Consultant": (True, True),
			"NC Department Head": (True, False),
			"NC Director": (True, False),
			"NC Admin": (True, False),
			"NC Auditor": (True, False),
			"NC Clinician": (False, False),
			"NC Document Controller": (False, False),
		}
		users = {role: make_user(f"bmprice.{i}@normcore.test", role) for i, role in enumerate(cases)}
		for role, (read, write) in cases.items():
			frappe.set_user(users[role])
			with self.subTest(role=role):
				self.assertEqual(bool(frappe.has_permission(DOCTYPE, "read")), read)
				self.assertEqual(bool(frappe.has_permission(DOCTYPE, "create")), write)
				self.assertEqual(bool(frappe.has_permission(DOCTYPE, "write")), write)
				self.assertFalse(frappe.has_permission(DOCTYPE, "delete"))

	def test_quyen_feat_026_auditor_va_clinician_khong_tao(self):
		users = [
			make_user("bmprice.aud@normcore.test", "NC Auditor"),
			make_user("bmprice.cl@normcore.test", "NC Clinician"),
		]
		for email in users:
			frappe.set_user(email)
			self.assertRaises(frappe.PermissionError, _price().insert)

	def test_quyen_feat_026_finance_tao_va_xac_nhan(self):
		email = make_user("bmprice.fin@normcore.test", "NC Finance")
		frappe.set_user(email)
		doc = _price(service_name_raw="dinh luong glucose mau").insert()
		self.assertEqual(doc.status, "Đề xuất")
		doc.status = "Đã xác nhận"
		doc.save()
		self.assertEqual(frappe.get_doc(DOCTYPE, doc.name).verified_by, email)
