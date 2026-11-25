"""FEAT-035 — hàm thuần sản lượng cận lâm sàng, phút khai thác, xuất kho (FR-ACCT-012..015)."""

import unittest

from normcore.costing import cls_volume as cv
from normcore.costing import test_systems as ts

GLU_A = {
	"fiscal_year": 2026,
	"patient_results": 12000,
	"iqc_tests": 600,
	"calibration_tests": 48,
	"rerun_tests": 240,
	"eqa_tests": 12,
	"wastage_rate": 3,
	"avg_batch_size": 40,
	"run_days": 300,
}
GLU_B = {"fiscal_year": 2026, "patient_results": 4000}


def fields(errors):
	return [f for f, _ in errors]


class TestVolumeErrors(unittest.TestCase):
	def test_hop_le_day_du(self):
		self.assertEqual(cv.volume_errors(GLU_A.get), [])

	def test_hop_le_cot_phu_de_trong(self):
		self.assertEqual(cv.volume_errors(GLU_B.get), [])

	def test_TC_CLS_35_so_am(self):
		errs = cv.volume_errors({**GLU_B, "patient_results": -5}.get)
		self.assertEqual(fields(errs), ["patient_results"])
		self.assertIn("không được âm", errs[0][1])

	def test_so_test_phu_am(self):
		for f in cv.AUX_FIELDS:
			self.assertEqual(fields(cv.volume_errors({**GLU_B, f: -1}.get)), [f])

	def test_thieu_qbn(self):
		self.assertEqual(fields(cv.volume_errors({"fiscal_year": 2026}.get)), ["patient_results"])
		self.assertEqual(fields(cv.volume_errors({"fiscal_year": 2026, "patient_results": ""}.get)), ["patient_results"])

	def test_qbn_bang_0_hop_le(self):
		self.assertEqual(cv.volume_errors({**GLU_B, "patient_results": 0}.get), [])

	def test_nam_ngoai_mien(self):
		self.assertEqual(fields(cv.volume_errors({**GLU_B, "fiscal_year": 1999}.get)), ["fiscal_year"])
		self.assertEqual(fields(cv.volume_errors({**GLU_B, "fiscal_year": 2101}.get)), ["fiscal_year"])

	def test_hao_hut_tren_100(self):
		self.assertEqual(fields(cv.volume_errors({**GLU_B, "wastage_rate": 120}.get)), ["wastage_rate"])
		self.assertEqual(cv.volume_errors({**GLU_B, "wastage_rate": 100}.get), [])

	def test_co_me_phai_lon_hon_0(self):
		self.assertEqual(fields(cv.volume_errors({**GLU_B, "avg_batch_size": 0}.get)), ["avg_batch_size"])

	def test_ngay_chay(self):
		self.assertEqual(fields(cv.volume_errors({**GLU_B, "run_days": 0}.get)), ["run_days"])
		self.assertEqual(fields(cv.volume_errors({**GLU_B, "run_days": 367}.get)), ["run_days"])
		self.assertEqual(cv.volume_errors({**GLU_B, "run_days": 366}.get), [])

	def test_khong_phai_so(self):
		errs = cv.volume_errors({**GLU_B, "iqc_tests": "abc"}.get)
		self.assertEqual(fields(errs), ["iqc_tests"])
		self.assertIn("phải là số", errs[0][1])

	def test_nhieu_loi(self):
		errs = cv.volume_errors({"fiscal_year": 2026, "patient_results": -1, "rerun_tests": -2}.get)
		self.assertEqual(fields(errs), ["patient_results", "rerun_tests"])


class TestResolveService(unittest.TestCase):
	def setUp(self):
		self.map = {("LIS", "LIS-GLU"): "GLU"}
		self.lookup = lambda src, code: self.map.get((src, code))
		self.exists = lambda code: code in ("GLU", "URE")

	def test_TC_CLS_34_ma_lis_doi_sang_ma_dich_vu(self):
		self.assertEqual(cv.resolve_service("LIS", "LIS-GLU", self.lookup, self.exists), "GLU")

	def test_ma_noi_bo_khi_khong_co_nguon(self):
		self.assertEqual(cv.resolve_service(None, "URE", self.lookup, self.exists), "URE")
		self.assertEqual(cv.resolve_service("", "GLU", self.lookup, self.exists), "GLU")

	def test_ma_ngoai_khong_co_trong_anh_xa(self):
		with self.assertRaises(ValueError) as e:
			cv.resolve_service("LIS", "LIS-XXX", self.lookup, self.exists)
		self.assertIn("LIS-XXX", str(e.exception))
		self.assertIn("LIS", str(e.exception))

	def test_ma_noi_bo_khong_ton_tai(self):
		with self.assertRaises(ValueError) as e:
			cv.resolve_service(None, "ZZZ", self.lookup, self.exists)
		self.assertIn("NC Technical Service", str(e.exception))

	def test_anh_xa_tro_toi_dich_vu_khong_ton_tai(self):
		self.map[("LIS", "LIS-OLD")] = "GONE"
		with self.assertRaises(ValueError):
			cv.resolve_service("LIS", "LIS-OLD", self.lookup, self.exists)


class TestSystemMismatch(unittest.TestCase):
	system = {"technical_service": "GLU", "department": "HS-CLS"}

	def test_khop(self):
		self.assertEqual(cv.system_mismatch(self.system, "GLU", "HS-CLS"), [])

	def test_khoa_trong_khong_kiem(self):
		self.assertEqual(cv.system_mismatch(self.system, "GLU", None), [])

	def test_khac_dich_vu(self):
		errs = cv.system_mismatch(self.system, "URE", "HS-CLS")
		self.assertEqual(fields(errs), ["service_code"])
		self.assertIn("GLU", errs[0][1])
		self.assertIn("URE", errs[0][1])

	def test_khac_khoa(self):
		self.assertEqual(fields(cv.system_mismatch(self.system, "GLU", "XN")), ["department"])

	def test_khac_ca_hai(self):
		self.assertEqual(fields(cv.system_mismatch(self.system, "URE", "XN")), ["service_code", "department"])


class TestBlankAux(unittest.TestCase):
	def test_glu_b_bon_cot_trong(self):
		self.assertEqual(cv.blank_aux(GLU_B.get), list(cv.AUX_FIELDS))

	def test_glu_a_khong_trong(self):
		self.assertEqual(cv.blank_aux(GLU_A.get), [])

	def test_so_0_khong_phai_trong(self):
		self.assertEqual(cv.blank_aux({**GLU_B, "iqc_tests": 0}.get), ["calibration_tests", "rerun_tests", "eqa_tests"])


class TestUsageStock(unittest.TestCase):
	def test_usage_hop_le(self):
		d = {"fiscal_year": 2026, "total_minutes": 120000}
		self.assertEqual(cv.usage_errors(d.get, "Phút chiếm máy"), [])

	def test_usage_co_so_khac(self):
		d = {"fiscal_year": 2026, "total_minutes": 10}
		errs = cv.usage_errors(d.get, "Số kết quả")
		self.assertEqual(fields(errs), ["equipment"])
		self.assertIn("Số kết quả", errs[0][1])

	def test_usage_thieu_va_am(self):
		self.assertEqual(fields(cv.usage_errors({"fiscal_year": 2026}.get, "Phút chiếm máy")), ["total_minutes"])
		d = {"fiscal_year": 2026, "total_minutes": -1}
		self.assertEqual(fields(cv.usage_errors(d.get, "Phút chiếm máy")), ["total_minutes"])

	def test_usage_nam_sai(self):
		d = {"fiscal_year": 1, "total_minutes": 1}
		self.assertEqual(fields(cv.usage_errors(d.get, "Phút chiếm máy")), ["fiscal_year"])

	def test_usage_khong_phai_so(self):
		d = {"fiscal_year": 2026, "total_minutes": "x"}
		self.assertEqual(fields(cv.usage_errors(d.get, "Phút chiếm máy")), ["total_minutes"])

	def test_TC_CLS_36_stock_hop_le(self):
		self.assertEqual(cv.stock_errors({"fiscal_year": 2026, "issued_qty": 94}.get), [])

	def test_stock_am_thieu_nam(self):
		self.assertEqual(fields(cv.stock_errors({"fiscal_year": 2026, "issued_qty": -1}.get)), ["issued_qty"])
		self.assertEqual(fields(cv.stock_errors({"fiscal_year": 2026}.get)), ["issued_qty"])
		self.assertEqual(fields(cv.stock_errors({"fiscal_year": 0, "issued_qty": 1}.get)), ["fiscal_year"])


class TestVolumeStatus(unittest.TestCase):
	def test_chua_co(self):
		self.assertEqual(cv.volume_status(None), {"state": "empty", "message": "Chưa có"})

	def test_glu_a_ok(self):
		st = cv.volume_status(GLU_A)
		self.assertEqual(st["state"], "ok")
		self.assertIn("2026", st["message"])
		self.assertIn("12.000", st["message"])

	def test_glu_b_uoc_tinh(self):
		st = cv.volume_status(GLU_B)
		self.assertEqual(st["state"], "estimated")
		self.assertIn("4.000", st["message"])
		self.assertIn("ước tính từ kế hoạch", st["message"])

	def test_status_items_voi_volume(self):
		items = ts.status_items(volume=GLU_B)
		vol = next(i for i in items if i["key"] == "volume")
		self.assertEqual(vol["state"], "estimated")
		for i in items:
			if i["key"] != "volume":
				self.assertEqual(i["state"], "empty")
