import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.tests.utils import make_user


def _new(code="LG-T01", **over):
	data = {"doctype": "NC Price Category", "category_code": code, "category_name": "Loại giá thử"}
	data.update(over)
	return frappe.get_doc(data)


class TestNCPriceCategory(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_TC_RES_11_thieu_cap_phe_duyet_bi_tu_choi_roi_luu_duoc(self):
		with self.assertRaises(frappe.MandatoryError):
			_new().insert()
		doc = _new(approval_authority="Bệnh viện", include_depreciation=0, include_accumulation=1).insert()
		doc = frappe.get_doc("NC Price Category", doc.name)
		self.assertEqual(doc.approval_authority, "Bệnh viện")
		self.assertEqual(doc.include_depreciation, 0)
		self.assertEqual(doc.include_accumulation, 1)

	def test_TC_RES_11_cap_phe_duyet_ngoai_danh_sach_bi_tu_choi(self):
		self.assertRaises(frappe.ValidationError, _new(approval_authority="Khác").insert)

	def test_FR_RES_015_thieu_ten_bi_tu_choi(self):
		doc = frappe.get_doc(
			{"doctype": "NC Price Category", "category_code": "LG-T02", "approval_authority": "Bệnh viện"}
		)
		self.assertRaises(frappe.MandatoryError, doc.insert)

	def test_FR_RES_015_trung_ma_bi_tu_choi(self):
		_new(approval_authority="Bệnh viện").insert()
		self.assertRaises(frappe.DuplicateEntryError, _new(approval_authority="Bệnh viện").insert)

	def test_FR_RES_015_finance_tao_duoc(self):
		frappe.set_user(make_user("pc.finance@normcore.test", "NC Finance"))
		self.assertEqual(_new("LG-T03", approval_authority="Cơ quan có thẩm quyền").insert().name, "LG-T03")

	def test_FR_ACC_007_auditor_chi_doc(self):
		frappe.set_user(make_user("pc.auditor@normcore.test", "NC Auditor"))
		self.assertTrue(frappe.has_permission("NC Price Category", "read"))
		for ptype in ("create", "write", "delete"):
			self.assertFalse(frappe.has_permission("NC Price Category", ptype), ptype)
		self.assertRaises(frappe.PermissionError, _new("LG-T04", approval_authority="Bệnh viện").insert)

	def test_FR_ACC_002_vai_tro_khong_quyen(self):
		frappe.set_user(make_user("pc.clinician@normcore.test", "NC Clinician"))
		self.assertFalse(frappe.has_permission("NC Price Category", "read"))
		self.assertRaises(frappe.PermissionError, _new("LG-T05", approval_authority="Bệnh viện").insert)

	def test_FR_ACC_002_resource_manager_chi_doc(self):
		frappe.set_user(make_user("pc.rm@normcore.test", "NC Resource Manager"))
		self.assertTrue(frappe.has_permission("NC Price Category", "read"))
		self.assertFalse(frappe.has_permission("NC Price Category", "write"))

	def test_FR_ADM_005_chan_xoa_khi_tham_chieu_da_dang_ky(self):
		# Chưa DocType nào của R1 liên kết tới NC Price Category (FEAT-012/030 sẽ thêm); kiểm móc chặn đã gắn
		hooks = frappe.get_hooks("doc_events").get("NC Price Category", {})
		self.assertIn("normcore.core.references.check_not_referenced", hooks.get("on_trash", []))

	def test_FR_ADM_005_admin_xoa_duoc_khi_khong_tham_chieu(self):
		_new("LG-T07", approval_authority="Bệnh viện").insert()
		frappe.set_user(make_user("pc.admin2@normcore.test", "NC Admin"))
		frappe.delete_doc("NC Price Category", "LG-T07")
		self.assertFalse(frappe.db.exists("NC Price Category", "LG-T07"))

	def test_TBD_05_hai_loai_gia_mau(self):
		from normcore.install import ensure_sample_price_categories

		ensure_sample_price_categories()
		ensure_sample_price_categories()  # chạy lại không tạo trùng, không lỗi
		bv = frappe.get_doc("NC Price Category", "GIA-BV")
		nn = frappe.get_doc("NC Price Category", "GIA-NN")
		self.assertEqual(
			(bv.approval_authority, bv.include_depreciation, bv.include_accumulation), ("Bệnh viện", 0, 1)
		)
		self.assertEqual(
			(nn.approval_authority, nn.include_depreciation, nn.include_accumulation),
			("Cơ quan có thẩm quyền", 1, 0),
		)
		for c in (bv, nn):
			self.assertIn("Giả định — chờ xác nhận", c.category_name)

	def test_TBD_05_khong_ghi_de_ban_da_sua(self):
		from normcore.install import ensure_sample_price_categories

		ensure_sample_price_categories()
		frappe.db.set_value("NC Price Category", "GIA-BV", "category_name", "Tên bệnh viện đã sửa")
		ensure_sample_price_categories()
		self.assertEqual(
			frappe.db.get_value("NC Price Category", "GIA-BV", "category_name"), "Tên bệnh viện đã sửa"
		)
