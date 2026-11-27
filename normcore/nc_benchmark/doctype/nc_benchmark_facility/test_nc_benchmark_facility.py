import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.tests.utils import make_user

DOCTYPE = "NC Benchmark Facility"


def _facility(**kw):
	values = {
		"doctype": DOCTYPE,
		"facility_name": "Bệnh viện thử FEAT-026",
		"province": "Hà Nội",
		"ownership": "Công lập",
		"facility_level": "Hạng I",
	}
	values.update(kw)
	return frappe.get_doc(values)


class TestNCBenchmarkFacility(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_TC_BM_06_don_vi_tham_chieu_bat_buoc(self):
		# Lần đầu thiếu tỉnh, thành phố: bị từ chối
		self.assertRaises(frappe.MandatoryError, _facility(province=None).insert)
		# Lần sau đủ tên, tỉnh, loại hình, hạng: lưu được
		doc = _facility().insert()
		doc = frappe.get_doc(DOCTYPE, doc.name)
		self.assertEqual(doc.name, "Bệnh viện thử FEAT-026")
		self.assertEqual((doc.province, doc.ownership, doc.facility_level), ("Hà Nội", "Công lập", "Hạng I"))

	def test_FR_BM_001_bon_truong_bat_buoc(self):
		for missing in ("facility_name", "province", "ownership", "facility_level"):
			with self.subTest(missing=missing):
				doc = _facility()
				doc.set(missing, None)
				# tên đơn vị là trường đặt tên: Frappe báo ValidationError "is required" trước khi kiểm bắt buộc
				self.assertRaises(frappe.ValidationError, doc.insert)

	def test_FR_BM_001_loai_hinh_chi_cong_lap_hoac_tu_nhan(self):
		options = frappe.get_meta(DOCTYPE).get_field("ownership").options.split("\n")
		self.assertEqual([o for o in options if o], ["Công lập", "Tư nhân"])
		self.assertRaises(frappe.ValidationError, _facility(ownership="Khác").insert)

	def test_FR_BM_001_trung_ten_bi_tu_choi(self):
		_facility().insert()
		self.assertRaises(frappe.DuplicateEntryError, _facility().insert)

	def test_quyen_feat_026_don_vi(self):
		cases = {
			"NC Finance": (True, True),
			"NC Consultant": (True, True),
			"NC Department Head": (True, False),
			"NC Director": (True, False),
			"NC Admin": (True, False),
			"NC Auditor": (True, False),
			"NC Clinician": (False, False),
			"NC Council Member": (False, False),
		}
		users = {role: make_user(f"bmfac.{i}@normcore.test", role) for i, role in enumerate(cases)}
		for role, (read, write) in cases.items():
			frappe.set_user(users[role])
			with self.subTest(role=role):
				self.assertEqual(bool(frappe.has_permission(DOCTYPE, "read")), read)
				self.assertEqual(bool(frappe.has_permission(DOCTYPE, "create")), write)
				self.assertEqual(bool(frappe.has_permission(DOCTYPE, "write")), write)
				self.assertFalse(frappe.has_permission(DOCTYPE, "delete"))

	def test_quyen_feat_026_auditor_khong_tao_duoc(self):
		email = make_user("bmfac.auditor@normcore.test", "NC Auditor")
		frappe.set_user(email)
		self.assertRaises(frappe.PermissionError, _facility().insert)

	def test_quyen_feat_026_clinician_khong_tao_duoc(self):
		email = make_user("bmfac.clin@normcore.test", "NC Clinician")
		frappe.set_user(email)
		self.assertRaises(frappe.PermissionError, _facility().insert)
