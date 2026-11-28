import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, nowdate

from normcore.nc_costing.report.nc_compliance_expiry.nc_compliance_expiry import execute
from normcore.tests.utils import make_base, make_equipment, make_private_file, make_user


def _hs(equipment, days, **kw):
	values = {
		"doctype": "NC Equipment Compliance",
		"equipment": equipment,
		"record_type": "Kiểm định",
		"cycle_months": 12,
		"provider": "Trung tâm kiểm định",
		"cost_per_time": 5000000,
		"performed_on": add_days(nowdate(), min(days, 0) - 300),
		"expiry_date": add_days(nowdate(), days),
		"attachment": make_private_file(),
	}
	values.update(kw)
	return frappe.get_doc(values).insert()


class TestNCComplianceExpiry(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.set_single_value("NC Settings", "compliance_reminder_days", 30)
		_, self.dept, _ = make_base()
		self.type_req = frappe.get_doc(
			{
				"doctype": "NC Equipment Type",
				"type_code": "LT-BB",
				"type_name": "Bắt buộc",
				"compliance_required": 1,
			}
		).insert()
		self.type_opt = frappe.get_doc(
			{"doctype": "NC Equipment Type", "type_code": "LT-KB", "type_name": "Không bắt buộc"}
		).insert()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _rows(self, **filters):
		_, rows, *_rest = execute({"as_of": nowdate(), **filters})
		return rows

	def test_TC_CLS_28_bao_cao_liet_ke_ho_so_sap_het_han_theo_khoa(self):
		eq = make_equipment(department=self.dept).name
		due = _hs(eq, 20)
		expired = _hs(eq, -5)
		valid = _hs(eq, 200)
		rows = {r["record"]: r for r in self._rows() if r["record"]}
		self.assertEqual(rows[due.name]["status"], "Sắp hết hạn")
		self.assertEqual(rows[due.name]["department"], self.dept)
		self.assertEqual(rows[due.name]["days_left"], 20)
		self.assertEqual(rows[expired.name]["status"], "Hết hạn")
		self.assertNotIn(valid.name, rows)
		# đổi số ngày nhắc thành 10: hồ sơ không còn trong báo cáo
		frappe.db.set_single_value("NC Settings", "compliance_reminder_days", 10)
		self.assertNotIn(due.name, {r["record"] for r in self._rows()})

	def test_FR_CMP_007_thiet_bi_bat_buoc_thieu_ho_so(self):
		req = make_equipment("TB-BB", department=self.dept, equipment_type=self.type_req.name).name
		opt = make_equipment("TB-KB", department=self.dept, equipment_type=self.type_opt.name).name
		with_valid = make_equipment("TB-BB2", department=self.dept, equipment_type=self.type_req.name).name
		_hs(with_valid, 200)
		missing = {r["equipment"] for r in self._rows() if r["status"] == "Thiếu hồ sơ còn hạn"}
		self.assertIn(req, missing)
		self.assertNotIn(opt, missing)
		self.assertNotIn(with_valid, missing)
		# chỉ có hồ sơ hết hạn thì vẫn thiếu hồ sơ còn hạn
		_hs(req, -5)
		self.assertIn(req, {r["equipment"] for r in self._rows(status="Thiếu hồ sơ còn hạn")})

	def test_FR_CMP_007_loc_khoa_va_ngay_xem(self):
		eq = make_equipment(department=self.dept).name
		doc = _hs(eq, 90)
		self.assertEqual(self._rows(department=self.dept), [])
		later = execute({"as_of": add_days(nowdate(), 70)})[1]
		self.assertEqual([r["record"] for r in later], [doc.name])
		other = execute({"as_of": add_days(nowdate(), 70), "department": "KHOA-KHAC"})[1]
		self.assertEqual(other, [])

	def test_FR_CMP_007_tom_tat_va_cot(self):
		eq = make_equipment(department=self.dept).name
		_hs(eq, 5)
		cols, _rows, _m, _c, summary = execute({"as_of": nowdate()})
		self.assertEqual(len(cols), 10)
		labels = {s["label"]: s["value"] for s in summary}
		self.assertEqual(labels["Số ngày nhắc hạn"], 30)
		self.assertGreaterEqual(labels["Sắp hết hạn"], 1)

	def test_FR_ACC_002_quyen_bao_cao(self):
		report = frappe.get_doc("Report", "NC Compliance Expiry")
		roles = {r.role for r in report.roles}
		self.assertEqual(
			roles,
			{
				"NC Clinician",
				"NC Department Head",
				"NC Finance",
				"NC Resource Manager",
				"NC Director",
				"NC Consultant",
				"NC Admin",
				"NC Auditor",
			},
		)
		self.assertEqual(report.ref_doctype, "NC Equipment Compliance")

	def test_NORM_88_moi_vai_tro_cua_bao_cao_co_quyen_report_tren_ref_doctype(self):
		roles = [r.role for r in frappe.get_doc("Report", "NC Compliance Expiry").roles]
		for i, role in enumerate(roles):
			user = make_user(f"norm88{i}@example.com", role)
			self.assertTrue(
				frappe.has_permission("NC Equipment Compliance", "report", user=user),
				f"{role} thiếu quyền report",
			)
			frappe.set_user(user)
			try:
				frappe.get_attr("frappe.desk.query_report.run")("NC Compliance Expiry", {"as_of": nowdate()})
			finally:
				frappe.set_user("Administrator")
