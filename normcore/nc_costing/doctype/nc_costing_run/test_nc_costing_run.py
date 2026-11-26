from decimal import Decimal

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.costing import engine
from normcore.nc_costing.doctype.nc_norm_set.nc_norm_set import make_norm_set
from normcore.tests.utils import (
	confirm_norm_set,
	costing_run_inputs,
	make_base,
	make_param_set,
	make_procedure,
	make_user,
	publish_procedure,
)


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
			**costing_run_inputs(),
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


from normcore.tests import accounting_fixtures as af


class TestNCCostingRunInputs(FrappeTestCase):
	"""FR-COST-001, TC-COST-19."""

	def setUp(self):
		frappe.set_user("Administrator")
		make_base()
		self.params = make_param_set()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _doc(self, **over):
		from normcore.tests.utils import costing_run_inputs

		data = {
			"doctype": "NC Costing Run",
			"title": "Lần tính đầu vào",
			"fiscal_year": 2026,
			"costing_date": "2026-12-31",
			"parameter_set": self.params.name,
			**costing_run_inputs(),
		}
		data.update(over)
		return frappe.get_doc({k: v for k, v in data.items() if v is not None})

	def test_TC_COST_19_tao_lan_tinh_thieu_dau_vao_bi_tu_choi(self):
		with self.assertRaises(frappe.MandatoryError):
			self._doc(parameter_set=None).insert(ignore_permissions=True)
		for field in ("accounting_import", "price_category"):
			with self.subTest(thieu=field), self.assertRaises(frappe.MandatoryError):
				self._doc(**{field: None}).insert(ignore_permissions=True)
		draft = frappe.get_doc(
			{
				"doctype": "NC Accounting Import",
				"fiscal_year": 2027,
				"accounting_regime": "Hành chính sự nghiệp",
				"source_file": af.make_file(af.make_xlsx(af.GOLDEN_ROWS)),
			}
		).insert(ignore_permissions=True)
		self.assertEqual(draft.status, "Nháp")
		with self.assertRaisesRegex(frappe.ValidationError, "chưa chốt"):
			self._doc(accounting_import=draft.name).insert(ignore_permissions=True)
		ok = self._doc().insert(ignore_permissions=True)
		self.assertEqual(ok.status, "Nháp")

	def test_khoa_dau_vao_khi_da_tinh(self):
		run = self._doc().insert(ignore_permissions=True)
		run.db_set("status", "Đã tính")
		run.reload()
		run.fiscal_year = 2030
		with self.assertRaisesRegex(frappe.ValidationError, "không sửa được đầu vào"):
			run.save(ignore_permissions=True)
		with self.assertRaisesRegex(frappe.ValidationError, "không sửa được đầu vào"):
			frappe.client.set_value("NC Costing Run", run.name, "fiscal_year", 2031)
		run.reload()
		run.append("scope_services", {"technical_service": make_base()[0]})
		with self.assertRaisesRegex(frappe.ValidationError, "không sửa được đầu vào"):
			run.save(ignore_permissions=True)
		run.reload()
		run.title = "Đổi tên vẫn được"
		run.save(ignore_permissions=True)
		run.db_set("status", "Tính lỗi")
		run.reload()
		run.fiscal_year = 2032
		run.save(ignore_permissions=True)

	def test_TC_CLS_08_mac_dinh_lan_tinh(self):
		"""FR-COST-017: mặc định Thực tế 12 tháng và Theo giá trị tài sản."""
		doc = frappe.new_doc("NC Costing Run")
		self.assertEqual(doc.volume_scenario, "Thực tế 12 tháng")
		self.assertEqual(doc.compliance_allocation_mode, "Theo giá trị tài sản")
		run = self._doc().insert(ignore_permissions=True)
		self.assertEqual(run.volume_scenario, "Thực tế 12 tháng")
		self.assertEqual(run.compliance_allocation_mode, "Theo giá trị tài sản")

	def test_khoa_dau_vao_kich_ban_khi_da_tinh(self):
		run = self._doc().insert(ignore_permissions=True)
		run.db_set("status", "Đã tính")
		for field, value in (
			("volume_scenario", "Kế hoạch"),
			("compliance_allocation_mode", "Gắn trực tiếp thiết bị"),
		):
			run.reload()
			run.set(field, value)
			with self.assertRaisesRegex(frappe.ValidationError, "không sửa được đầu vào"):
				run.save(ignore_permissions=True)
		run.db_set("status", "Nháp")
		run.reload()
		run.volume_scenario = "Kế hoạch"
		run.save(ignore_permissions=True)


class TestNCCostingRunGolden(FrappeTestCase):
	"""FR-COST-002, 003, 007, 010, 016: lần tính trên site với dữ liệu vàng."""

	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _world(self, **kw):
		from normcore.tests import costing_fixtures as cf

		self.cf = cf
		self.params, self.dept, self.sets = cf.make_golden_world(**kw)
		return cf

	def _costs(self, run):
		return {
			c.technical_service: frappe.get_doc("NC Service Cost", c.name)
			for c in frappe.get_all(
				"NC Service Cost", {"costing_run": run.name}, ["name", "technical_service"]
			)
		}

	def test_TC_COST_01_tren_site_tong_truc_tiep_va_gia(self):
		self._world()
		run = self.cf.make_golden_run(self.params)
		self.assertEqual(run.run_costing(), "Đã tính")
		a = self._costs(run)["DV-TEST-A"]
		self.assertEqual(a.calc_status, "Thành công")
		self.assertEqual(sum(ln.amount for ln in a.lines), 183963.06)
		import sys

		sys.path.insert(0, frappe.get_app_path("normcore", "..", "docs", "golden"))
		import golden_engine as g

		by_cat = g.run()[0]["DV-TEST-A"]["by_cat"]
		self.assertEqual(a.direct_labor, float(by_cat["LABOR"]))  # 69.000,94 theo golden
		self.assertEqual(a.direct_utility, float(by_cat["UTILITY"]))  # 1.500,00 theo golden
		self.assertEqual(a.full_cost, 183963.06)  # chưa có phân bổ (ASM-015-02)
		self.assertEqual(a.volume, 4000)

	def test_TC_COST_17_dich_vu_chua_khoa_bi_liet_ke_va_bo_qua(self):
		cf = self._world()
		cf.ensure("NC Technical Service", "service_code", "DV-CHUA", service_name="Chưa khóa")
		svc = frappe.get_doc("NC Technical Service", "DV-CHUA")
		svc.is_active = 1
		svc.append("departments", {"department": self.dept})
		svc.save(ignore_permissions=True)
		for s in ("DV-TEST-A", "DV-TEST-B"):
			doc = frappe.get_doc("NC Technical Service", s)
			doc.is_active = 1
			doc.append("departments", {"department": self.dept})
			doc.save(ignore_permissions=True)
		run = cf.make_golden_run(
			self.params,
			scope_services=[{"technical_service": "DV-TEST-A"}, {"technical_service": "DV-CHUA"}],
		)
		info = run.scope()
		self.assertEqual(info["ineligible"], [("DV-CHUA", self.dept)])
		self.assertEqual([e["service"] for e in info["eligible"]], ["DV-TEST-A"])
		with self.assertRaisesRegex(frappe.ValidationError, "DV-CHUA"):
			run.run_costing()
		self.assertEqual(frappe.db.count("NC Service Cost", {"costing_run": run.name}), 0)
		self.assertEqual(run.reload().status, "Nháp")
		run.run_costing(confirm_ineligible=1)
		self.assertEqual(list(self._costs(run)), ["DV-TEST-A"])

	def test_TC_COST_07_V4_tren_site_dich_vu_khac_van_tinh(self):
		self._world(skip_price=("THUOCX",))
		run = self.cf.make_golden_run(self.params)
		run.run_costing()
		costs = self._costs(run)
		a, b = costs["DV-TEST-A"], costs["DV-TEST-B"]
		self.assertEqual(a.calc_status, "Lỗi")
		self.assertIn("L05", a.calc_message)
		self.assertEqual(len(a.lines), 0)
		self.assertEqual(b.calc_status, "Thành công")
		self.assertEqual(b.direct_labor + b.direct_supply, 32822.44)

	def test_TC_COST_06_bang_giai_trinh_ghi_khau_hao_bi_loai(self):
		self._world()
		self.cf.make_price_category("PC-V1", include_depreciation=0)
		run = self.cf.make_golden_run(self.params, price_category="PC-V1")
		run.run_costing()
		a = self._costs(run)["DV-TEST-A"]
		by = {ln.norm_line_id: ln for ln in a.lines}
		self.assertEqual((by["L07"].unit_rate, by["L08"].unit_rate, by["L08"].amount), (34090.9091, 0, 0))
		for lid in ("L07", "L08"):
			self.assertIn("Khấu hao bị loại", by[lid].warning)
		self.assertFalse(by["L01"].warning)

	def test_TC_COST_15_dong_giai_trinh_du_nguon(self):
		from unittest import mock

		from normcore.costing import engine

		self._world()
		run = self.cf.make_golden_run(self.params)
		rule = frappe.get_doc(
			{
				"doctype": "NC Allocation Rule",
				"rule_name": "Quy tắc thử",
				"level": "Cấp 2",
				"cost_category": "LABOR",
				"driver": "LABOR_MIN",
			}
		).insert(ignore_permissions=True)
		alloc = engine.CostLine(
			"Phân bổ",
			"LABOR",
			Decimal("100"),
			allocation_rule=rule.name,
			driver_value=10,
			driver_total=40,
			pool_amount=400,
		)
		pools = "normcore.nc_costing.doctype.nc_costing_run.nc_costing_run.allocate_pools"
		with mock.patch(pools, return_value={("DV-TEST-A", self.dept): [alloc]}):
			self.assertEqual(
				run.run_costing(), "Đã tính", frappe.get_all("Error Log", pluck="error", limit=1)
			)
		a = self._costs(run)["DV-TEST-A"]
		direct = [ln for ln in a.lines if ln.line_type == "Trực tiếp"]
		self.assertEqual(len(direct), 11)
		for ln in direct:
			with self.subTest(line=ln.norm_line_id):
				self.assertTrue(ln.step_id or ln.norm_line_id == "L10")  # L10 là dòng chung (service_level)
				self.assertTrue(ln.resource_label and ln.rate_source)
				self.assertIsNotNone(ln.applied_qty)
				self.assertIsNotNone(ln.unit_rate)
		(pl,) = [ln for ln in a.lines if ln.line_type == "Phân bổ"]
		self.assertEqual(
			(pl.component, pl.allocation_rule, pl.driver_value, pl.driver_total, pl.amount),
			("LABOR", rule.name, 10, 40, 100),
		)
		self.assertEqual((a.alloc_labor, a.full_cost), (100, 184063.06))


class TestNCCostingRunBackground(FrappeTestCase):
	"""FR-COST-015 (Should): quá ngưỡng thì chạy nền."""

	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_FR_COST_015_tren_50_dich_vu_chay_nen_co_tien_do(self):
		from unittest import mock

		from normcore.costing import runner
		from normcore.nc_costing.doctype.nc_costing_run import nc_costing_run as mod
		from normcore.tests import costing_fixtures as cf

		params, _dept, _sets = cf.make_golden_world()
		run = cf.make_golden_run(params)
		with mock.patch.object(runner, "BACKGROUND_THRESHOLD", 1), mock.patch("frappe.enqueue") as enq:
			self.assertEqual(run.run_costing(), "Đang tính")
		enq.assert_called_once()
		self.assertEqual(enq.call_args.kwargs["queue"], "long")
		self.assertEqual(enq.call_args.args[0], mod.EXECUTE)
		run.reload()
		self.assertEqual((run.status, run.progress), ("Đang tính", 0))
		self.assertEqual(frappe.db.count("NC Service Cost", {"costing_run": run.name}), 0)
		with mock.patch("frappe.db.commit"), mock.patch("frappe.publish_realtime") as rt:
			self.assertEqual(mod.execute_costing(run.name, enq.call_args.kwargs["eligible"]), "Đã tính")
		run.reload()
		self.assertEqual((run.status, run.progress), ("Đã tính", 100))
		self.assertEqual(frappe.db.count("NC Service Cost", {"costing_run": run.name}), 2)
		events = [c.args[1] for c in rt.call_args_list if c.args[0] == mod.PROGRESS_EVENT]
		self.assertEqual([e["progress"] for e in events], [50, 100])
		# ngưỡng: đúng 50 thì chạy ngay
		self.assertFalse(runner.needs_background(50))
