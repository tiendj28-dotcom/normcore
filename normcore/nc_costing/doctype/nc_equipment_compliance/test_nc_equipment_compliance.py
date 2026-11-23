import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, nowdate

from normcore.tests.utils import make_equipment, make_private_file, make_user


def _hs(**kw):
	eq = make_equipment()
	values = {
		"doctype": "NC Equipment Compliance",
		"equipment": eq.name,
		"record_type": "Kiểm định",
		"cycle_months": 12,
		"provider": "Trung tâm kiểm định",
		"cost_per_time": 5000000,
		"performed_on": add_days(nowdate(), -100),
		"expiry_date": add_days(nowdate(), 265),
		"attachment": make_private_file(),
	}
	values.update(kw)
	return frappe.get_doc(values)


class TestNCEquipmentCompliance(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.set_single_value("NC Settings", "compliance_reminder_days", 30)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_TC_CLS_27_thieu_chung_tu_bi_tu_choi(self):
		# lần đầu: thiếu tệp chứng từ → từ chối
		doc = _hs(attachment=None)
		with self.assertRaises(frappe.ValidationError) as ctx:
			doc.insert()
		self.assertIn("Tệp chứng từ", str(ctx.exception))
		# lần sau: đủ tệp → lưu, trạng thái Còn hạn
		doc = _hs().insert()
		doc = frappe.get_doc("NC Equipment Compliance", doc.name)
		self.assertEqual(doc.status, "Còn hạn")
		self.assertTrue(doc.name.startswith("HSTT-"))

	def test_FR_CMP_001_thieu_tung_truong_bat_buoc_bi_tu_choi(self):
		for missing in (
			"equipment",
			"record_type",
			"cycle_months",
			"provider",
			"cost_per_time",
			"performed_on",
			"expiry_date",
			"attachment",
		):
			doc = _hs()
			doc.set(missing, None)
			with self.subTest(missing=missing), self.assertRaises(frappe.ValidationError):
				doc.insert()

	def test_FR_CMP_001_nam_loai_ho_so(self):
		options = frappe.get_meta("NC Equipment Compliance").get_field("record_type").options.split("\n")[1:]
		self.assertEqual(options, ["Kiểm định", "Hiệu chuẩn", "Kiểm xạ", "Giấy phép an toàn bức xạ", "Khác"])

	def test_UC_020_1b_rang_buoc_bi_tu_choi(self):
		bad = {
			"chu_ky_0": {"cycle_months": 0},
			"het_han_truoc_thuc_hien": {"expiry_date": add_days(nowdate(), -200)},
			"chi_phi_am": {"cost_per_time": -1},
			"tep_public": {"attachment": "/files/chung-tu.txt"},
		}
		for name, kw in bad.items():
			with self.subTest(case=name), self.assertRaises(frappe.ValidationError):
				_hs(**kw).insert()

	def test_FR_CMP_005_trang_thai_tinh_khi_luu_va_nguoi_dung_khong_sua(self):
		doc = _hs(expiry_date=add_days(nowdate(), 20), status="Còn hạn").insert()
		self.assertEqual(doc.status, "Sắp hết hạn")
		doc.expiry_date = add_days(nowdate(), -1)
		doc.performed_on = add_days(nowdate(), -400)
		doc.save()
		self.assertEqual(doc.status, "Hết hạn")

	def test_AMD_009_khoa_lay_tu_thiet_bi_va_ma_ho_so(self):
		doc = _hs().insert()
		self.assertEqual(doc.department, frappe.db.get_value("NC Equipment", doc.equipment, "department"))
		self.assertEqual(doc.record_code, doc.name)  # ASM-093 tương tự: để trống thì lấy bằng tên
		self.assertRaises(frappe.ValidationError, _hs(record_code="HSTT-9999-0001").insert)
		other = _hs(record_code="HS-RIENG").insert()
		self.assertEqual(other.record_code, "HS-RIENG")
		self.assertRaises(frappe.UniqueValidationError, _hs(record_code="HS-RIENG").insert)

	def test_FR_ACC_002_quyen_theo_ma_tran(self):
		cases = {
			"NC Resource Manager": True,
			"NC Admin": True,
			"NC Finance": False,
			"NC Clinician": False,
			"NC Department Head": False,
			"NC Director": False,
			"NC Consultant": False,
		}
		users = {r: make_user(f"hstt.{i}@normcore.test", r) for i, r in enumerate(cases)}
		for role, write in cases.items():
			frappe.set_user(users[role])
			with self.subTest(role=role):
				self.assertTrue(frappe.has_permission("NC Equipment Compliance", "read"))
				self.assertEqual(bool(frappe.has_permission("NC Equipment Compliance", "create")), write)

	def test_FR_ACC_007_auditor_chi_doc(self):
		doc = _hs().insert()
		frappe.set_user(make_user("hstt.auditor@normcore.test", "NC Auditor"))
		self.assertTrue(frappe.has_permission("NC Equipment Compliance", "read"))
		self.assertFalse(frappe.has_permission(doc=doc, ptype="write"))
		self.assertRaises(frappe.PermissionError, _hs().insert)

	def test_FR_ACC_002_vai_tro_khong_quyen_khong_doc(self):
		users = {
			r: make_user(f"hstt.no{i}@normcore.test", r)
			for i, r in enumerate(("NC Council Member", "NC Document Controller"))
		}
		for role, email in users.items():
			frappe.set_user(email)
			self.assertFalse(frappe.has_permission("NC Equipment Compliance", "read"), role)

	def test_FR_ADM_006_nc_settings_quyen_va_mac_dinh(self):
		frappe.db.set_single_value("NC Settings", "compliance_reminder_days", 0)
		meta = frappe.get_meta("NC Settings")
		self.assertEqual(meta.get_field("compliance_reminder_days").default, "30")
		admin = make_user("hstt.admin@normcore.test", "NC Admin")
		auditor = make_user("hstt.audit2@normcore.test", "NC Auditor")
		rm = make_user("hstt.rm@normcore.test", "NC Resource Manager")
		frappe.set_user(admin)
		self.assertTrue(frappe.has_permission("NC Settings", "write"))
		frappe.set_user(auditor)
		self.assertTrue(frappe.has_permission("NC Settings", "read"))
		self.assertFalse(frappe.has_permission("NC Settings", "write"))
		frappe.set_user(rm)
		self.assertFalse(frappe.has_permission("NC Settings", "read"))
