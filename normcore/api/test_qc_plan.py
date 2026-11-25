"""FEAT-032: API kế hoạch chất lượng (FR-QC-007, FR-CLS-007; TC-CLS-26)."""

import json

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.api import qc_plan as api
from normcore.api import test_system as ts_api
from normcore.tests.utils import (
	ensure,
	make_cls_data,
	make_qc_items,
	make_qc_plan,
	make_test_system,
	make_user,
)


class TestQcPlanApi(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.service, self.dept, _ = make_cls_data()
		make_test_system("GLU-A", self.service, self.dept, "EQ_A", 100)
		make_qc_items()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_TC_CLS_26_he_thong_hoa_sinh_khong_ke_hoach_noi_kiem_canh_bao(self):
		r = api.missing_iqc_warning("GLU-A")
		self.assertTrue(r["warning"])
		self.assertIn("GLU-A", r["message"])

	def test_TC_CLS_26_ke_hoach_khong_dong_noi_kiem_van_canh_bao(self):
		make_qc_plan("GLU-A", iqc_lines=[])
		self.assertTrue(api.missing_iqc_warning("GLU-A")["warning"])

	def test_TC_CLS_26_co_noi_kiem_het_canh_bao(self):
		make_qc_plan("GLU-A")
		r = api.missing_iqc_warning("GLU-A")
		self.assertEqual((r["warning"], r["message"]), (False, None))

	def test_TC_CLS_26_nhom_khac_khong_canh_bao(self):
		frappe.db.set_value("NC Technical Service", self.service, "cls_group", "Chẩn đoán hình ảnh")
		self.assertFalse(api.missing_iqc_warning("GLU-A")["warning"])

	def test_canh_bao_khong_chan_viec_gi(self):
		"""Hàm chỉ trả cảnh báo, không ném lỗi dù thiếu kế hoạch (phần khóa bộ định mức kiểm ở FEAT-034)."""
		self.assertIn("warning", api.missing_iqc_warning("GLU-A"))

	def test_khoi_tinh_trang_chua_va_da_co_ke_hoach(self):
		items = {i["key"]: i for i in ts_api.get_status("GLU-A")["items"]}
		self.assertEqual((items["qc_plan"]["state"], items["qc_plan"]["message"]), ("empty", "Chưa có"))
		self.assertEqual(ts_api.get_status("GLU-A")["warnings"], [])
		make_qc_plan("GLU-A")
		items = {i["key"]: i for i in ts_api.get_status("GLU-A")["items"]}
		self.assertEqual(items["qc_plan"]["state"], "ok")
		self.assertIn("1 dòng nội kiểm", items["qc_plan"]["message"])
		self.assertEqual(ts_api.get_status("GLU-A")["warnings"], [])

	def test_estimate_tests(self):
		plan = {
			"run_days_per_year": 300,
			"iqc_lines": [{"levels": 2, "runs_per_day": 1}],
			"calibration_lines": [{"points": 2, "replicates": 2, "calibrations_per_year": 12}],
		}
		for arg in (plan, json.dumps(plan)):
			r = api.estimate_tests(arg)
			self.assertEqual((r["iqc_tests"], r["calibration_tests"], r["complete"]), (600, 48, True))
		self.assertFalse(api.estimate_tests({"iqc_lines": [{"levels": 2}]})["complete"])

	def test_eqa_summary(self):
		base = {"rounds_per_year": 3, "samples_per_round": 4}
		r = api.eqa_summary({**base, "services": [{"technical_service": "A"}, {"technical_service": "B"}]})
		self.assertEqual((r["samples_per_year"], r["mode"]), (12, "equal"))
		self.assertEqual([s["share_pct"] for s in r["shares"]], [50, 50])
		r = api.eqa_summary(
			json.dumps(
				{**base, "services": [{"technical_service": "A", "share_pct": 60}, {"technical_service": "B", "share_pct": 40}]}
			)
		)
		self.assertEqual((r["mode"], r["total_pct"]), ("custom", 100))
		r = api.eqa_summary(
			{**base, "services": [{"technical_service": "A", "share_pct": 50}, {"technical_service": "B", "share_pct": 40}]}
		)
		self.assertEqual((r["mode"], r["total_pct"]), ("invalid", 90))
		self.assertIn("90", r["message"])

	def test_phan_quyen(self):
		make_qc_plan("GLU-A")
		ensure(
			"NC Department",
			"department_code",
			"VS-API2",
			department_name="Vi sinh",
			department_type="Lâm sàng",
			cost_center="HS-CLS",
		)
		from normcore.api import access

		other = make_user("qp.api.vs@normcore.test", "NC Clinician")
		none_role = make_user("qp.api.none@normcore.test", "NC Document Controller")
		auditor = make_user("qp.api.aud@normcore.test", "NC Auditor")
		access.assign_department(other, "VS-API2")
		frappe.set_user(other)
		with self.assertRaises(frappe.PermissionError):
			api.missing_iqc_warning("GLU-A")
		frappe.set_user(none_role)
		for call in (
			lambda: api.missing_iqc_warning("GLU-A"),
			lambda: api.estimate_tests({}),
			lambda: api.eqa_summary({}),
		):
			with self.assertRaises(frappe.PermissionError):
				call()
		frappe.set_user(auditor)
		self.assertFalse(api.missing_iqc_warning("GLU-A")["warning"])
