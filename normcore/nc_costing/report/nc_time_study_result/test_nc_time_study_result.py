import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.nc_costing.doctype.nc_time_study.test_nc_time_study import make_four_step_procedure
from normcore.nc_costing.report.nc_time_study_result.nc_time_study_result import execute
from normcore.tests.utils import make_base, make_user


class TestNCTimeStudyResult(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.service, self.dept, _job = make_base("DV-BG", "K01")
		self.proc = make_four_step_procedure(self.service, self.dept)
		self.s2 = self.proc.steps[1].step_id
		frappe.db.set_single_value("NC Settings", "min_time_study_cases", 5)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _case(self, day, bs):
		frappe.get_doc(
			{
				"doctype": "NC Time Study",
				"technical_service": self.service,
				"department": self.dept,
				"observed_on": f"2026-11-{day:02d}",
				"lines": [{"step_id": self.s2, "job_title": "BS", "headcount": 1, "labor_minutes": bs}],
			}
		).insert()

	def _run(self):
		return execute({"technical_service": self.service, "department": self.dept})

	def test_chua_chon_dich_vu_khoa(self):
		columns, data, message, _chart, _summary = execute({})
		self.assertEqual(data, [])
		self.assertIn("Chọn dịch vụ và khoa", message)
		self.assertEqual(
			[c["fieldname"] for c in columns],
			["step_id", "step_title", "kind_label", "resource_label", "median_minutes", "n"],
		)

	def test_chua_co_ca(self):
		_c, data, message, _chart, _s = self._run()
		self.assertEqual(data, [])
		self.assertEqual(message, "Chưa có ca bấm giờ nào.")

	def test_thieu_ca_co_dai_canh_bao(self):
		for i in range(3):
			self._case(i + 1, 20)
		_c, data, message, _chart, summary = self._run()
		self.assertIn("Chưa đủ số ca", message)
		self.assertEqual(len(data), 1)
		self.assertEqual((data[0]["step_id"], data[0]["median_minutes"], data[0]["n"]), (self.s2, 20, 3))
		self.assertEqual(summary[0]["value"], "3 / 5")
		self.assertEqual(summary[0]["indicator"], "Orange")

	def test_du_ca_khong_canh_bao(self):
		for i, m in enumerate([18, 22, 20, 25, 19]):
			self._case(i + 1, m)
		_c, data, message, _chart, summary = self._run()
		self.assertIsNone(message)
		self.assertEqual(data[0]["median_minutes"], 20)
		self.assertEqual(data[0]["kind_label"], "Nhân lực")
		self.assertEqual(data[0]["resource_label"], "Bác sĩ")
		self.assertEqual(summary[0]["indicator"], "Green")

	def test_council_bi_tu_choi(self):
		council = make_user("council.rep@normcore.test", "NC Council Member")
		frappe.set_user(council)
		self.assertRaises(frappe.PermissionError, self._run)

	def test_vai_tro_doc_khop_bang(self):
		roles = {r.role for r in frappe.get_doc("Report", "NC Time Study Result").roles}
		self.assertEqual(
			roles,
			{
				"NC Clinician",
				"NC Department Head",
				"NC Finance",
				"NC Director",
				"NC Consultant",
				"NC Admin",
				"NC Auditor",
			},
		)
