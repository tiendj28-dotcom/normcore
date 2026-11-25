"""FEAT-033: tác vụ hằng ngày, thông báo, đổi số ngày nhắc (TC-CLS-28, FR-CMP-005, FR-ADM-006)."""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, nowdate

from normcore.api import compliance as api
from normcore.tests.utils import make_base, make_equipment, make_private_file, make_user


def _hs(equipment, **kw):
	values = {
		"doctype": "NC Equipment Compliance",
		"equipment": equipment,
		"record_type": "Kiểm định",
		"cycle_months": 12,
		"provider": "Trung tâm kiểm định",
		"cost_per_time": 5000000,
		"performed_on": add_days(nowdate(), -300),
		"expiry_date": add_days(nowdate(), 20),
		"attachment": make_private_file(),
	}
	values.update(kw)
	return frappe.get_doc(values).insert()


def _logs(doc_name):
	return frappe.get_all(
		"Notification Log",
		filters={"document_type": "NC Equipment Compliance", "document_name": doc_name},
		fields=["for_user", "subject", "type", "from_user"],
	)


class TestComplianceJob(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.set_single_value("NC Settings", "compliance_reminder_days", 30)
		_, self.dept, _ = make_base()
		self.rm = make_user("hstt.job.rm@normcore.test", "NC Resource Manager")
		self.head = make_user("hstt.job.head@normcore.test", "NC Department Head")
		frappe.db.set_value("NC Department", self.dept, "head_user", self.head)
		self.eq = make_equipment(department=self.dept).name

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_TC_CLS_28_nhac_han_thong_bao_va_doi_so_ngay(self):
		doc = _hs(self.eq)
		self.assertEqual(doc.status, "Sắp hết hạn")  # còn 20 ngày, nhắc trước 30
		# tác vụ ngày: thông báo đến Resource Manager và trưởng khoa, liên kết tới hồ sơ
		api.daily_job()
		users = {x.for_user for x in _logs(doc.name)}
		self.assertTrue({self.rm, self.head} <= users)
		self.assertNotIn("Administrator", users)
		for log in _logs(doc.name):
			self.assertEqual(log.type, "Alert")
			self.assertIn(doc.record_code, log.subject)
		# chạy lần hai không gửi trùng
		before = len(_logs(doc.name))
		self.assertEqual(api.send_reminders(), 0)
		api.daily_job()
		self.assertEqual(len(_logs(doc.name)), before)
		# đổi số ngày nhắc thành 10: hồ sơ về Còn hạn ngay, không cần chạy tác vụ
		settings = frappe.get_doc("NC Settings")
		settings.compliance_reminder_days = 10
		settings.save()
		self.assertEqual(frappe.db.get_value("NC Equipment Compliance", doc.name, "status"), "Còn hạn")
		# và không gửi thêm
		self.assertEqual(api.send_reminders(), 0)

	def test_FR_CMP_005_het_han_va_con_han_khong_gui(self):
		valid = _hs(self.eq, expiry_date=add_days(nowdate(), 90))
		expired = _hs(self.eq, expiry_date=add_days(nowdate(), -1), performed_on=add_days(nowdate(), -400))
		self.assertEqual(expired.status, "Hết hạn")
		api.daily_job()
		self.assertEqual(_logs(valid.name), [])
		self.assertEqual(_logs(expired.name), [])

	def test_FR_CMP_005_refresh_theo_ngay_va_dem_so_doi(self):
		doc = _hs(self.eq, expiry_date=add_days(nowdate(), 90))
		self.assertEqual(api.refresh_all_statuses(), 0)
		self.assertEqual(api.refresh_all_statuses(today=add_days(nowdate(), 70)), 1)
		self.assertEqual(frappe.db.get_value("NC Equipment Compliance", doc.name, "status"), "Sắp hết hạn")
		self.assertEqual(api.refresh_all_statuses(today=add_days(nowdate(), 100)), 1)
		self.assertEqual(frappe.db.get_value("NC Equipment Compliance", doc.name, "status"), "Hết hạn")

	def test_FR_CMP_005_khoa_khong_co_truong_khoa_van_gui_resource_manager(self):
		frappe.db.set_value("NC Department", self.dept, "head_user", None)
		doc = _hs(self.eq)
		api.send_reminders()
		self.assertEqual({x.for_user for x in _logs(doc.name)}, {self.rm})

	def test_FR_ADM_006_mac_dinh_30_khi_trong(self):
		# chưa từng lưu NC Settings: lấy mặc định 30 (Int trống đã lưu hiểu là 0, hợp lệ)
		frappe.db.delete("Singles", {"doctype": "NC Settings", "field": "compliance_reminder_days"})
		frappe.clear_document_cache("NC Settings")
		self.assertEqual(api.get_reminder_days(), 30)
		frappe.db.set_single_value("NC Settings", "compliance_reminder_days", 0)
		self.assertEqual(api.get_reminder_days(), 0)
		frappe.db.set_single_value("NC Settings", "compliance_reminder_days", 7)
		self.assertEqual(api.get_reminder_days(), 7)

	def test_FR_ADM_006_so_ngay_am_bi_tu_choi(self):
		settings = frappe.get_doc("NC Settings")
		settings.compliance_reminder_days = -1
		self.assertRaises(frappe.ValidationError, settings.save)

	def test_FR_ACC_007_run_compliance_check_theo_quyen(self):
		doc = _hs(self.eq)
		auditor = make_user("hstt.job.auditor@normcore.test", "NC Auditor")
		finance = make_user("hstt.job.fin@normcore.test", "NC Finance")
		council = make_user("hstt.job.council@normcore.test", "NC Council Member")
		for user in (auditor, finance, council):
			frappe.set_user(user)
			self.assertRaises(frappe.PermissionError, api.run_compliance_check)
		frappe.set_user(self.rm)
		result = api.run_compliance_check()
		self.assertEqual(result["updated"], 0)
		self.assertEqual(result["notified"], len({x.for_user for x in _logs(doc.name)}))
		self.assertGreaterEqual(result["notified"], 2)

	def test_FR_ACC_007_nc_settings_chi_admin_ghi(self):
		admin = make_user("hstt.job.admin@normcore.test", "NC Admin")
		frappe.set_user(self.rm)
		settings = frappe.get_doc("NC Settings")
		settings.compliance_reminder_days = 5
		self.assertRaises(frappe.PermissionError, settings.save)
		frappe.set_user(admin)
		settings.save()
		self.assertEqual(api.get_reminder_days(), 5)

	def test_daily_job_duoc_khai_bao_trong_hooks(self):
		self.assertIn("normcore.api.compliance.daily_job", frappe.get_hooks("scheduler_events")["daily"])
