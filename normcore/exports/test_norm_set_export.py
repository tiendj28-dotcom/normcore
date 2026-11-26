"""FEAT-034 T08: tệp Excel của bộ định mức (FR-OUT-011, TC-CLS-33). k lấy từ golden_cls, không chép số."""

import importlib.util
import io
import pathlib
import unittest

from openpyxl import load_workbook

from normcore.exports import norm_set

_spec = importlib.util.spec_from_file_location(
	"golden_cls", pathlib.Path(__file__).resolve().parents[2] / "docs" / "golden" / "golden_cls.py"
)
golden_cls = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(golden_cls)


def line(lid, **kw):
	base = {
		"step_id": "S001",
		"step_title": "Bước 1",
		"line_id": lid,
		"component": "DRUG",
		"resource_label": "HC_GLU",
		"cost_level_label": "Theo kết quả",
		"apply_k_label": "Có",
		"attach_label": "",
		"hospital_qty": 1,
		"uom": "test",
		"basis": "Quy trình",
		"confirmed_by": "head@x",
	}
	base.update(kw)
	return base


def data(system=True, **kw):
	d = {
		"head": {
			"name": "DM-GLU-XN-GLU-A-v1",
			"technical_service_label": "GLU — Glucose",
			"department": "XN",
			"version_no": 1,
			"status": "Đã khóa",
			"test_system": "GLU-A" if system else None,
			"tests_per_tube": 4,
		},
		"has_test_system": system,
		"lines": [
			line("L001"),
			line("L002", cost_level_label="Theo ống mẫu", apply_k_label="", component="SUPPLY"),
		],
		"qc_plan": {
			"run_days_per_year": 300,
			"iqc_lines": [
				dict(qc_material="QC_L", levels=2, runs_per_day=1, qty_per_run=0.2, shared_parameter_count=20)
			],
			"calibration_lines": [
				dict(
					calibrator="CAL",
					points=2,
					replicates=2,
					calibrations_per_year=12,
					cost_per_calibration=400000,
				)
			],
		},
		"eqa": [
			dict(
				eqa_code="EQA-HS",
				program_name="Ngoại kiểm",
				provider="TT",
				rounds_per_year=3,
				samples_per_round=4,
				annual_fee=24000000,
				annual_shipping_fee=1200000,
				share_pct=5,
			)
		],
		"k": None,
	}
	d.update(kw)
	return d


def load(raw):
	return load_workbook(io.BytesIO(raw))


def table(ws, header_first):
	"""Hàng tiêu đề (ô đầu = header_first) và các hàng sau nó."""
	rows = list(ws.iter_rows(values_only=True))
	i = next(n for n, r in enumerate(rows) if r[0] == header_first)
	return rows[i], rows[i + 1 :]


class TestBuildWorkbook(unittest.TestCase):
	def test_TC_CLS_33_tep_xuat_co_k_6_chu_so(self):
		k, _total, estimated = golden_cls.k_factor("GLU-A")
		self.assertFalse(estimated)
		wb = load(
			norm_set.build_workbook(
				data(k={"run": "TG-1", "costing_date": "2026-11-01", "k_factor": k, "k_estimated": 0})
			)
		)
		ws = wb["Hệ số k"]
		cell = ws.cell(2, 4)
		self.assertEqual(cell.value, float(k))
		self.assertEqual(round(cell.value, 6), 1.108247)
		self.assertEqual(cell.number_format, "0.000000")
		self.assertIsNone(ws.cell(2, 5).value)

	def test_TC_CLS_33_k_uoc_tinh_co_nhan(self):
		k, _total, estimated = golden_cls.k_factor("GLU-B")
		self.assertTrue(estimated)
		wb = load(norm_set.build_workbook(data(k={"run": "TG-1", "k_factor": k, "k_estimated": 1})))
		self.assertEqual(wb["Hệ số k"].cell(2, 5).value, "Ước tính từ kế hoạch")

	def test_TC_CLS_33_chua_co_lan_tinh_gia(self):
		wb = load(norm_set.build_workbook(data()))
		self.assertEqual(wb["Hệ số k"].cell(2, 4).value, "Chưa có lần tính giá")

	def test_TC_CLS_33_trang_dong_co_cap_phat_sinh_dung_gia_tri(self):
		wb = load(norm_set.build_workbook(data()))
		self.assertEqual(wb.sheetnames, ["Bộ định mức", "Nội kiểm", "Chuẩn máy", "Ngoại kiểm", "Hệ số k"])
		header, rows = table(wb["Bộ định mức"], "Bước")
		col = {h: i for i, h in enumerate(header)}
		self.assertEqual([r[col["Cấp phát sinh"]] for r in rows], ["Theo kết quả", "Theo ống mẫu"])
		self.assertEqual([r[col["Nhân k"]] for r in rows], ["Có", None])
		self.assertEqual(rows[0][col["Định mức BV"]], 1)  # số, không phải chuỗi
		self.assertEqual(rows[0][col["Người xác nhận"]], "head@x")
		self.assertEqual(wb["Bộ định mức"]["B7"].value, "GLU-A")  # đầu trang có hệ thống
		qc = wb["Nội kiểm"]
		self.assertEqual([c.value for c in qc[2]][:2], ["QC_L", 2])
		self.assertEqual(qc.cell(2, 6).value, 300)
		self.assertEqual(wb["Chuẩn máy"].cell(2, 1).value, "CAL")
		self.assertEqual(wb["Ngoại kiểm"].cell(2, 1).value, "EQA-HS")

	def test_bo_khong_co_he_thong(self):
		wb = load(norm_set.build_workbook(data(system=False)))
		self.assertEqual(wb.sheetnames, ["Bộ định mức"])
		header, _rows = table(wb["Bộ định mức"], "Bước")
		for c in norm_set.CLS_COLUMNS:
			self.assertNotIn(c, header)
		labels = [r[0] for r in wb["Bộ định mức"].iter_rows(values_only=True)]
		self.assertNotIn("Hệ thống xét nghiệm", labels)

	def test_chua_co_ke_hoach_va_ngoai_kiem(self):
		wb = load(norm_set.build_workbook(data(qc_plan=None, eqa=[])))
		self.assertEqual(wb["Nội kiểm"]["A1"].value, "Chưa có kế hoạch chất lượng")
		self.assertEqual(wb["Chuẩn máy"]["A1"].value, "Chưa có kế hoạch chất lượng")
		self.assertEqual(wb["Ngoại kiểm"]["A1"].value, "Chưa có chương trình ngoại kiểm")


class TestLatestK(unittest.TestCase):
	def row(self, run, date, status="Đã tính", k=1.1, est=0):
		return {"run": run, "costing_date": date, "status": status, "k_factor": k, "k_estimated": est}

	def test_chon_lan_gan_nhat_da_tinh_hoac_da_khoa(self):
		rows = [
			self.row("A", "2026-01-01"),
			self.row("B", "2026-03-01", status="Đã khóa", k=1.2),
			self.row("C", "2026-05-01", status="Nháp", k=9),
			self.row("D", "2026-03-01", k=1.3),
		]
		self.assertEqual(norm_set.latest_k(rows)["run"], "D")  # hòa ngày thì tên lớn nhất

	def test_khong_co(self):
		self.assertIsNone(norm_set.latest_k([]))
		self.assertIsNone(norm_set.latest_k([self.row("A", "2026-01-01", status="Lỗi")]))
		self.assertIsNone(norm_set.latest_k([self.row("A", "2026-01-01", k=None)]))
