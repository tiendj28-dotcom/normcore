"""FEAT-032: hàm thuần kế hoạch chất lượng và ngoại kiểm (FR-QC-001..003, 005, 007, 008; TC-CLS-24..26)."""

import unittest
from decimal import Decimal as D

from normcore.costing import qc_plans as qp
from normcore.costing import test_systems as ts

ITEMS = {"QC_L": "Vật liệu nội kiểm", "CAL": "Chất chuẩn", "HC_GLU": "Hóa chất"}
IQC = dict(qc_material="QC_L", levels=2, runs_per_day=1, qty_per_run=0.2, shared_parameter_count=20)
CALL = dict(calibrator="CAL", points=2, replicates=2, calibrations_per_year=12, cost_per_calibration=400000)


def plan(**kw):
	base = dict(
		test_system="GLU-A", run_days_per_year=300, iqc_lines=[dict(IQC)], calibration_lines=[dict(CALL)]
	)
	base.update(kw)
	return base


def errs(**kw):
	return qp.validate_qc_plan(plan(**kw), ITEMS)


def has(errors, *words):
	return any(all(w in e for w in words) for e in errors)


class TestValidateQcPlan(unittest.TestCase):
	def test_hop_le(self):
		self.assertEqual(errs(), [])

	def test_rong_hai_bang_hop_le(self):
		self.assertEqual(errs(iqc_lines=[], calibration_lines=[]), [])

	def test_TC_CLS_24_thieu_truong_dau(self):
		for f, label in (
			("test_system", "Hệ thống xét nghiệm"),
			("run_days_per_year", "Số ngày chạy mỗi năm"),
		):
			for empty in (None, "", "  "):
				self.assertTrue(has(errs(**{f: empty}), "Thiếu", label), (f, empty))

	def test_TC_CLS_24_thieu_truong_dong_noi_kiem(self):
		for f, label in (
			("qc_material", "Vật liệu nội kiểm"),
			("levels", "Số mức"),
			("runs_per_day", "Số lần chạy mỗi ngày"),
			("qty_per_run", "Lượng dùng mỗi lần"),
			("shared_parameter_count", "Số thông số dùng chung"),
		):
			line = {**IQC, f: None}
			self.assertTrue(has(errs(iqc_lines=[IQC, line]), "Dòng nội kiểm 2", "Thiếu", label), f)

	def test_TC_CLS_24_thieu_truong_dong_chuan_may(self):
		for f, label in (
			("calibrator", "Chất chuẩn"),
			("points", "Số điểm chuẩn"),
			("replicates", "Số lần lặp"),
			("calibrations_per_year", "Số lần chuẩn mỗi năm"),
			("cost_per_calibration", "Chi phí chất chuẩn mỗi lần"),
		):
			line = {**CALL, f: ""}
			self.assertTrue(has(errs(calibration_lines=[line]), "Dòng chuẩn máy 1", "Thiếu", label), f)

	def test_mien_gia_tri(self):
		for v in (0, -1, 367, "abc"):
			self.assertTrue(errs(run_days_per_year=v), v)
		for v in (1, 366):
			self.assertEqual(errs(run_days_per_year=v), [])
		for f in ("levels", "shared_parameter_count"):
			self.assertTrue(errs(iqc_lines=[{**IQC, f: 0}]), f)
			self.assertTrue(errs(iqc_lines=[{**IQC, f: "x"}]), f)
		for f in ("runs_per_day", "qty_per_run"):
			self.assertTrue(errs(iqc_lines=[{**IQC, f: 0}]), f)
		for f in ("points", "replicates"):
			self.assertTrue(errs(calibration_lines=[{**CALL, f: 0}]), f)
		for f in ("calibrations_per_year", "cost_per_calibration"):
			self.assertTrue(errs(calibration_lines=[{**CALL, f: 0}]), f)

	def test_TC_CLS_25_vat_lieu_sai_loai(self):
		e = errs(iqc_lines=[{**IQC, "qc_material": "HC_GLU"}])
		self.assertTrue(has(e, "Dòng nội kiểm 1", "HC_GLU", "Hóa chất", "Vật liệu nội kiểm"), e)

	def test_TC_CLS_25_chat_chuan_sai_loai(self):
		e = errs(calibration_lines=[{**CALL, "calibrator": "QC_L"}])
		self.assertTrue(has(e, "Dòng chuẩn máy 1", "QC_L", "Chất chuẩn"), e)

	def test_mat_hang_khong_ton_tai(self):
		self.assertTrue(has(errs(iqc_lines=[{**IQC, "qc_material": "ZZZ"}]), "ZZZ", "Vật liệu nội kiểm"))

	def test_lap_vat_lieu_va_chat_chuan(self):
		self.assertTrue(has(errs(iqc_lines=[IQC, dict(IQC)]), "Dòng nội kiểm 2", "lặp"))
		self.assertTrue(has(errs(calibration_lines=[CALL, dict(CALL)]), "Dòng chuẩn máy 2", "lặp"))


SERVICES = {"GLU", "URE", "CRE"}


def eqa(**kw):
	base = dict(
		eqa_code="EQA-HS",
		program_name="Ngoại kiểm hóa sinh",
		provider="TTKN",
		department="HS",
		rounds_per_year=3,
		samples_per_round=4,
		annual_fee=24000000,
		annual_shipping_fee=1200000,
		services=[dict(technical_service="GLU", share_pct=0), dict(technical_service="URE", share_pct=0)],
	)
	base.update(kw)
	return base


def eerrs(**kw):
	return qp.validate_eqa_program(eqa(**kw), SERVICES)


class TestValidateEqa(unittest.TestCase):
	def test_hop_le_chia_deu(self):
		self.assertEqual(eerrs(), [])

	def test_TC_CLS_24_thieu_truong(self):
		for f, label in (
			("eqa_code", "Mã chương trình"),
			("program_name", "Tên chương trình"),
			("provider", "Đơn vị triển khai"),
			("department", "Khoa tham gia"),
			("rounds_per_year", "Số đợt mỗi năm"),
			("samples_per_round", "Số mẫu mỗi đợt"),
			("annual_fee", "Phí chương trình năm"),
		):
			self.assertTrue(has(eerrs(**{f: None}), "Thiếu", label), f)
		self.assertTrue(has(eerrs(services=[]), "dịch vụ"))
		self.assertTrue(has(eerrs(services=[dict(technical_service=None)]), "Thiếu", "Dịch vụ"))

	def test_phi_van_chuyen_trong_hop_le(self):
		self.assertEqual(eerrs(annual_shipping_fee=None), [])
		self.assertTrue(eerrs(annual_shipping_fee=-1))

	def test_mien_gia_tri(self):
		for f in ("rounds_per_year", "samples_per_round", "annual_fee"):
			self.assertTrue(eerrs(**{f: 0}), f)
			self.assertTrue(eerrs(**{f: "x"}), f)

	def test_dich_vu_lap_va_khong_can_lam_sang(self):
		two = [dict(technical_service="GLU"), dict(technical_service="GLU")]
		self.assertTrue(has(eerrs(services=two), "lặp"))
		self.assertTrue(has(eerrs(services=[dict(technical_service="XQ")]), "XQ", "cận lâm sàng"))

	def test_TC_CLS_25_50_va_40_bi_tu_choi(self):
		rows = [dict(technical_service="GLU", share_pct=50), dict(technical_service="URE", share_pct=40)]
		e = eerrs(services=rows)
		self.assertTrue(has(e, "90", "100"), e)

	def test_60_40_hop_le(self):
		rows = [dict(technical_service="GLU", share_pct=60), dict(technical_service="URE", share_pct=40)]
		self.assertEqual(eerrs(services=rows), [])

	def test_DI12_mot_so_dong_trong(self):
		rows = [dict(technical_service="GLU", share_pct=50), dict(technical_service="URE", share_pct=None)]
		self.assertTrue(has(eerrs(services=rows), "mọi dòng"))

	def test_ty_le_ngoai_0_100(self):
		rows = [dict(technical_service="GLU", share_pct=101), dict(technical_service="URE", share_pct=-1)]
		self.assertTrue(has(eerrs(services=rows), "0", "100"))
		self.assertTrue(has(eerrs(services=[dict(technical_service="GLU", share_pct="x")]), "số"))

	def test_eqa_shares(self):
		two = [dict(share_pct=0), dict(share_pct=None)]
		self.assertEqual(qp.eqa_shares(two), [D("0.5"), D("0.5")])
		self.assertEqual(qp.eqa_shares([dict(share_pct=60), dict(share_pct=40)]), [D("0.6"), D("0.4")])
		self.assertEqual(qp.eqa_shares([]), [])


class TestEstimate(unittest.TestCase):
	def test_so_test_uoc_tinh(self):
		self.assertEqual(qp.estimated_tests(plan()), (D("600"), D("48")))
		self.assertEqual(qp.eqa_samples_per_year(3, 4), D("12"))

	def test_dong_thieu_so_bi_bo_qua(self):
		p = plan(iqc_lines=[IQC, dict(levels=None, runs_per_day=1)], calibration_lines=[dict(points=2)])
		self.assertEqual(qp.estimated_tests(p), (D("600"), D("0")))
		self.assertFalse(qp.estimate_complete(p))
		self.assertTrue(qp.estimate_complete(plan()))
		self.assertFalse(qp.estimate_complete(plan(run_days_per_year=None)))

	def test_thieu_so_ngay_chay(self):
		self.assertEqual(qp.estimated_tests(plan(run_days_per_year=None))[0], D("0"))


class TestWarning(unittest.TestCase):
	def test_TC_CLS_26_khong_ke_hoach(self):
		m = qp.missing_iqc_warning("Hóa sinh", None, "GLU-A")
		self.assertIn("GLU-A", m)
		self.assertIn("nội kiểm", m)

	def test_TC_CLS_26_ke_hoach_khong_dong_noi_kiem(self):
		self.assertTrue(qp.missing_iqc_warning("Hóa sinh", plan(iqc_lines=[]), "GLU-A"))

	def test_co_noi_kiem(self):
		self.assertIsNone(qp.missing_iqc_warning("Hóa sinh", plan(), "GLU-A"))

	def test_nhom_khac_khong_canh_bao(self):
		self.assertIsNone(qp.missing_iqc_warning("Chẩn đoán hình ảnh", None, "XQ-1"))
		self.assertIsNone(qp.missing_iqc_warning(None, None, "X"))

	def test_moi_nhom_xet_nghiem(self):
		for g in qp.LAB_GROUPS:
			self.assertTrue(qp.missing_iqc_warning(g, None, "S"), g)


class TestStatusItem(unittest.TestCase):
	def test_co_ke_hoach(self):
		it = qp.plan_status_item(plan(), "Hóa sinh")
		self.assertEqual((it["key"], it["state"]), ("qc_plan", "ok"))
		self.assertIn("1 dòng nội kiểm", it["message"])
		self.assertIn("1 dòng chuẩn máy", it["message"])

	def test_thieu_noi_kiem_nhom_xet_nghiem(self):
		it = qp.plan_status_item(plan(iqc_lines=[]), "Hóa sinh")
		self.assertEqual(it["state"], "warning")
		self.assertIn("Thiếu nội kiểm", it["message"])

	def test_thieu_noi_kiem_nhom_khac_van_ok(self):
		self.assertEqual(qp.plan_status_item(plan(iqc_lines=[]), "Khác")["state"], "ok")

	def test_status_items_khong_tham_so_nhu_cu(self):
		items = ts.status_items()
		self.assertEqual([i["key"] for i in items], ["norm_set", "qc_plan", "volume", "latest_cost"])
		self.assertTrue(all(i["state"] == "empty" for i in items))

	def test_status_items_co_ke_hoach(self):
		items = ts.status_items(qc_plan=plan(), cls_group="Hóa sinh")
		self.assertEqual([i["key"] for i in items], ["norm_set", "qc_plan", "volume", "latest_cost"])
		self.assertEqual(items[1]["state"], "ok")
		self.assertEqual(items[0]["state"], "empty")
