"""NC Settings: tham số vận hành (FEAT-002; FR-ADM-003, TC-ADM-03)."""

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.core import settings
from normcore.costing import accounting
from normcore.patches import nc_settings_operating_defaults as patch
from normcore.tests.utils import make_user

NEW_FIELDS = (
	"min_time_study_cases",
	"price_valid_months",
	"benchmark_window_months",
	"min_benchmark_facilities",
	"accounting_regime",
)


def _save(user, **values):
	frappe.set_user(user)
	try:
		doc = frappe.get_single("NC Settings")
		doc.update(values)
		doc.save()
	finally:
		frappe.set_user("Administrator")


class TestNCSettings(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()
		frappe.db.value_cache.clear()  # cache giá trị single còn giữ phần đã rollback
		frappe.cache.delete_value("document_cache::NC Settings")

	def test_nc_settings_mac_dinh(self):
		meta = frappe.get_meta("NC Settings")
		defaults = {f: meta.get_field(f).default for f in NEW_FIELDS}
		self.assertEqual(
			defaults,
			{
				"min_time_study_cases": "5",
				"price_valid_months": "24",
				"benchmark_window_months": "24",
				"min_benchmark_facilities": "3",
				"accounting_regime": "Hành chính sự nghiệp",
			},
		)

	def test_nc_settings_gia_tri_khong_hop_le_bi_tu_choi(self):
		for field in NEW_FIELDS[:4]:
			for bad in (0, -1):
				doc = frappe.get_single("NC Settings")
				doc.set(field, bad)
				with self.assertRaises(frappe.ValidationError):
					doc.save()
		doc = frappe.get_single("NC Settings")
		doc.min_time_study_cases = 0
		with self.assertRaisesRegex(frappe.ValidationError, "Số ca bấm giờ tối thiểu phải lớn hơn 0"):
			doc.save()

	def test_nc_settings_tuy_chon_khop_regimes(self):
		options = frappe.get_meta("NC Settings").get_field("accounting_regime").options.split("\n")
		self.assertEqual(tuple(options), accounting.REGIMES)

	def test_nc_settings_patch_khong_ghi_de_va_chay_lai_khong_doi(self):
		frappe.db.set_single_value("NC Settings", "min_time_study_cases", 9)
		frappe.db.set_single_value("NC Settings", "price_valid_months", None)
		frappe.db.set_single_value("NC Settings", "accounting_regime", None)
		patch.execute()
		self.assertEqual(frappe.db.get_single_value("NC Settings", "min_time_study_cases"), 9)
		self.assertEqual(int(frappe.db.get_single_value("NC Settings", "price_valid_months")), 24)
		self.assertEqual(
			frappe.db.get_single_value("NC Settings", "accounting_regime"), "Hành chính sự nghiệp"
		)
		before = {f: frappe.db.get_single_value("NC Settings", f) for f in NEW_FIELDS}
		patch.execute()
		self.assertEqual(before, {f: frappe.db.get_single_value("NC Settings", f) for f in NEW_FIELDS})

	def test_nc_settings_get_tra_mac_dinh_khi_trong(self):
		for field in NEW_FIELDS:
			frappe.db.set_single_value("NC Settings", field, None)
		for field, default in settings.DEFAULTS.items():
			if field in NEW_FIELDS:
				self.assertEqual(settings.get(field), default)

	def test_nc_settings_get_truong_la_keyerror(self):
		with self.assertRaises(KeyError):
			settings.get("khong_co_truong_nay")

	def test_quyen_nc_settings_finance_khong_luu_duoc(self):
		finance = make_user("fin.set@normcore.test", "NC Finance")
		with self.assertRaises(frappe.PermissionError):
			_save(finance, min_time_study_cases=4)

	def test_quyen_nc_settings_auditor_chi_doc(self):
		auditor = make_user("aud.set@normcore.test", "NC Auditor")
		frappe.set_user(auditor)
		try:
			self.assertTrue(frappe.has_permission("NC Settings", "read"))
		finally:
			frappe.set_user("Administrator")
		with self.assertRaises(frappe.PermissionError):
			_save(auditor, min_time_study_cases=4)


class TestApplyImmediately(FrappeTestCase):
	"""FR-ADM-003: đổi tham số vận hành rồi áp ngay cho thao tác kế tiếp, không clear_cache, không khởi động lại."""

	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.flags.pop("normcore_ai_transport", None)
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_TC_ADM_03_doi_so_ca_toi_thieu_ap_ngay(self):
		# Phần tham số của TC-ADM-03 (ASM-002-13, Lead chọn PA1). Phần "mở kết quả 3 ca → có trung vị,
		# hết cảnh báo thiếu ca" là test_TC_ADM_03_ket_qua_bam_gio_3_ca của FEAT-014.
		admin = make_user("adm.set@normcore.test", "NC Admin")
		self.assertEqual(settings.get("min_time_study_cases"), 5)
		_save(admin, min_time_study_cases=3)
		self.assertEqual(settings.get("min_time_study_cases"), 3)

	def test_FR_ADM_003_so_ngay_nhac_ap_ngay(self):
		from frappe.utils import add_days, nowdate

		from normcore.api import access
		from normcore.api import procedure_workflow as wf
		from normcore.tests.utils import make_base, make_procedure

		service, dept, _ = make_base()
		head = make_user("head.adm3@normcore.test", "NC Department Head")
		access.assign_department(head, dept)
		frappe.db.set_value("NC Department", dept, "head_user", head)
		proc = make_procedure(service, dept)
		frappe.db.set_value("NC Clinical Procedure", proc.name, "workflow_state", "Chờ trưởng khoa duyệt")
		frappe.db.set_value(
			"NC Clinical Procedure", proc.name, "modified", add_days(nowdate(), -3), update_modified=False
		)
		today = nowdate()
		_save("Administrator", approval_reminder_days=7)
		self.assertEqual(wf.send_approval_reminders(today=today), 0)
		self.assertFalse(wf.pending_for(head)[0]["overdue"])
		_save("Administrator", approval_reminder_days=2)
		self.assertEqual(wf.send_approval_reminders(today=today), 1)
		self.assertTrue(wf.pending_for(head)[0]["overdue"])

	def test_FR_ADM_003_thoi_han_ai_ap_ngay(self):
		from normcore.ai import gateway

		seen = []

		def post(url, headers, payload, timeout):
			seen.append(timeout)
			return {"content": [{"type": "text", "text": "{}"}], "usage": {}}

		ai = frappe.get_doc("NC AI Settings")
		ai.update({"protocol": "Anthropic Messages", "model": "m", "api_key": "K-1", "timeout_seconds": 180})
		ai.save(ignore_permissions=True)
		frappe.flags.normcore_ai_transport = post
		gateway.get_provider().complete("thử", "T", {}, [])
		ai.timeout_seconds = 30
		ai.save(ignore_permissions=True)
		gateway.get_provider().complete("thử", "T", {}, [])
		self.assertEqual(seen, [180, 30])
