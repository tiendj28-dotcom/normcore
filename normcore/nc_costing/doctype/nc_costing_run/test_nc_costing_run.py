from decimal import Decimal

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.costing import engine
from normcore.nc_costing.doctype.nc_norm_set.nc_norm_set import make_norm_set
from normcore.tests.utils import confirm_norm_set, make_base, make_param_set, make_procedure, make_user, publish_procedure


def _published_norm_set(service, dept, minutes=10):
	proc = make_procedure(service, dept, minutes=minutes)
	publish_procedure(proc, "QĐ-01", "2026-12-01")
	return frappe.get_doc("NC Norm Set", make_norm_set(proc.name))


def _run(params):
	run = frappe.get_doc(
		{
			"doctype": "NC Costing Run",
			"title": "Lần tính thử",
			"fiscal_year": 2026,
			"costing_date": "2026-12-31",
			"parameter_set": params.name,
		}
	)
	run.insert(ignore_permissions=True)
	return run


class TestNCCostingRun(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.service, self.dept, self.job = make_base()
		self.params = make_param_set()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_FEAT000_luong_skeleton_dong_LABOR_L01(self):
		"""Luồng trọn vẹn với dữ liệu vàng: dòng L01 -> applied_qty 10, unit_rate 59644,8864, amount 9940,81."""
		# bộ tham số: đơn giá giờ công do engine.job_rate tính (FR-RES-010)
		rate = self.params.job_title_rates[0]
		self.assertEqual(rate.rate_per_hour, 59644.8864)
		ns = _published_norm_set(self.service, self.dept)
		fin = make_user("fin.run@normcore.test", "NC Finance")
		frappe.set_user(fin)
		confirm_norm_set(ns)
		ns.lock()
		run = _run(self.params)
		self.assertEqual(run.status, "Nháp")
		run.run_costing()
		run.reload()
		self.assertEqual(run.status, "Đã tính")
		costs = frappe.get_all("NC Service Cost", {"costing_run": run.name}, pluck="name")
		self.assertEqual(len(costs), 1)
		sc = frappe.get_doc("NC Service Cost", costs[0])
		self.assertEqual(
			(sc.technical_service, sc.department, sc.norm_set), (self.service, self.dept, ns.name)
		)
		self.assertEqual(sc.calc_status, "Thành công")
		self.assertEqual(len(sc.lines), 1)
		line = sc.lines[0]
		self.assertEqual(
			(line.line_type, line.component, line.step_id, line.norm_line_id),
			("Trực tiếp", "LABOR", "S001", "L001"),
		)
		self.assertEqual(line.applied_qty, 10)
		self.assertEqual(line.unit_rate, 59644.8864)
		self.assertEqual(line.amount, 9940.81)
		self.assertEqual(line.rate_source, self.params.name)
		self.assertEqual(sc.direct_labor, 9940.81)
		# bằng đúng kết quả gọi thẳng engine với cùng đầu vào
		direct = engine.compute_direct_lines(
			[engine.LaborLine("L001", Decimal("10"), 1, Decimal("59644.8864"), None)]
		)[0]
		self.assertEqual(
			(Decimal(str(line.applied_qty)), Decimal(str(line.unit_rate)), Decimal(str(line.amount))),
			(direct.applied_qty, direct.unit_rate, direct.amount),
		)

	def test_DI06_bo_dinh_muc_nhap_khong_duoc_doc(self):
		_published_norm_set(self.service, self.dept)  # còn Nháp
		run = _run(self.params)
		run.run_costing()
		self.assertEqual(frappe.db.count("NC Service Cost", {"costing_run": run.name}), 0)

	def test_G5_chuc_danh_thieu_don_gia_ghi_loi_khong_bia_so(self):
		ns = _published_norm_set(self.service, self.dept)
		confirm_norm_set(ns)
		ns.lock()
		frappe.get_doc(
			{
				"doctype": "NC Job Title",
				"job_title_code": "BS",
				"job_title_name": "Bác sĩ",
				"job_group": "Bác sĩ",
			}
		).insert(ignore_permissions=True)
		# bộ tham số không có dòng cho DD
		params = frappe.get_doc(
			{
				"doctype": "NC Costing Parameter Set",
				"title": "Thiếu DD",
				"effective_from": "2026-01-01",
				"base_salary": 2500000,
				"employer_contribution_rate": 23.5,
				"working_days_per_year": 264,
				"working_hours_per_day": 8,
				"job_title_rates": [
					{"job_title": "BS", "salary_coefficient": 4.4, "allowance_coefficient": 0.6}
				],
			}
		).insert(ignore_permissions=True)
		run = _run(params)
		run.run_costing()
		sc = frappe.get_doc("NC Service Cost", {"costing_run": run.name})
		self.assertEqual(sc.calc_status, "Lỗi")
		self.assertIn("L001", sc.calc_message)
		self.assertEqual(len(sc.lines), 0)

	def test_chay_lai_khong_nhan_doi_ket_qua(self):
		ns = _published_norm_set(self.service, self.dept)
		confirm_norm_set(ns)
		ns.lock()
		run = _run(self.params)
		run.run_costing()
		run.db_set("status", "Tính lỗi")
		run.reload()
		run.run_costing()
		self.assertEqual(frappe.db.count("NC Service Cost", {"costing_run": run.name}), 1)

	def test_tinh_loi_duoc_luu_trang_thai(self):
		ns = _published_norm_set(self.service, self.dept)
		confirm_norm_set(ns)
		ns.lock()
		# hospital_qty âm làm engine ném lỗi; ghi thẳng DB vì validate không cho sửa bộ đã khóa
		frappe.db.set_value("NC Norm Line", ns.lines[0].name, "hospital_qty", -5)
		run = _run(self.params)
		run.run_costing()
		run.reload()
		self.assertEqual(run.status, "Tính lỗi")
		self.assertEqual(frappe.db.count("NC Service Cost", {"costing_run": run.name}), 0)
