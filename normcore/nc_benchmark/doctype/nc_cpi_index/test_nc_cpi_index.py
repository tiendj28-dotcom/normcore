from datetime import date

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.tests.utils import make_user

DOCTYPE = "NC CPI Index"


def _cpi(**kw):
	values = {"doctype": DOCTYPE, "month": "2026-03-01", "index_value": 100.5, "source": "Nhập tay"}
	values.update(kw)
	return frappe.get_doc(values)


class TestNCCPIIndex(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.delete(DOCTYPE)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_FR_BM_006_chi_so_gia_theo_thang(self):
		# Ngày giữa tháng được đưa về ngày 1
		doc = _cpi(month="2026-03-17").insert()
		self.assertEqual(frappe.get_doc(DOCTYPE, doc.name).month, date(2026, 3, 1))
		# Trùng tháng (kể cả ngày khác trong tháng) bị từ chối
		with self.assertRaises(frappe.ValidationError) as ctx:
			_cpi(month="2026-03-25").insert()
		self.assertIn("03/2026", str(ctx.exception))
		# Tháng khác lưu được
		_cpi(month="2026-04-09", index_value=104).insert()
		# Chỉ số phải lớn hơn 0
		for bad in (0, -1):
			self.assertRaises(frappe.ValidationError, _cpi(month="2026-05-01", index_value=bad).insert)

	def test_FR_BM_006_bat_buoc(self):
		for missing in ("month", "index_value"):
			doc = _cpi()
			doc.set(missing, None)
			with self.subTest(missing=missing):
				self.assertRaises(frappe.MandatoryError, doc.insert)

	def test_FR_BM_006_sua_sang_thang_da_co_bi_tu_choi(self):
		_cpi(month="2026-03-01").insert()
		other = _cpi(month="2026-04-01").insert()
		other.month = "2026-03-20"
		self.assertRaises(frappe.ValidationError, other.save)

	def test_quyen_feat_026_chi_so(self):
		cases = {
			"NC Finance": (True, True),
			"NC Consultant": (True, True),
			"NC Department Head": (True, False),
			"NC Director": (True, False),
			"NC Admin": (True, False),
			"NC Auditor": (True, False),
			"NC Clinician": (False, False),
			"NC Resource Manager": (False, False),
		}
		users = {role: make_user(f"bmcpi.{i}@normcore.test", role) for i, role in enumerate(cases)}
		for role, (read, write) in cases.items():
			frappe.set_user(users[role])
			with self.subTest(role=role):
				self.assertEqual(bool(frappe.has_permission(DOCTYPE, "read")), read)
				self.assertEqual(bool(frappe.has_permission(DOCTYPE, "create")), write)
				self.assertFalse(frappe.has_permission(DOCTYPE, "delete"))

	def test_quyen_feat_026_chi_so_auditor_va_clinician_khong_tao(self):
		users = [make_user("bmcpi.aud@normcore.test", "NC Auditor"), make_user("bmcpi.cl@normcore.test", "NC Clinician")]
		for email in users:
			frappe.set_user(email)
			self.assertRaises(frappe.PermissionError, _cpi().insert)
