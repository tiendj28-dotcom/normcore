"""Unit test FEAT-019 T02: exports/annex.py (FR-OUT-001..004, NFR-CPL-002)."""

import io
import unittest
from datetime import date, datetime
from decimal import Decimal as D

from openpyxl import load_workbook

from normcore.exports import annex as a
from normcore.exports import meta


def svc(code="S1", **kw):
	s = {
		"service_code": code,
		"service_name": "Dịch vụ " + code,
		"department": "K01",
		"volume": 100,
		"his_code": "H1",
		"calc_status": "Thành công",
		"calc_message": "",
		"is_paraclinical": 0,
		"eqa_cost": 0,
		"price_category": "BHYT",
		"direct_labor": D("10"),
		"direct_drug": D("5"),
		"direct_supply": D("1"),
		"direct_equipment": D("20"),
		"direct_infra": D("4"),
		"direct_utility": D("2"),
		"alloc_labor": D("3"),
		"alloc_drug_supply": D("2"),
		"alloc_depreciation": D("1"),
		"alloc_utility": D("1"),
		"alloc_management": D("1"),
		"full_cost": D("50"),
		"accumulation": D("2.5"),
		"obligation": D("0"),
		"calculated_price": D("52.5"),
		"rounded_price": D("100"),
		"alloc_lines": [],
	}
	s.update(kw)
	return s


META = {
	"run": "CR-1",
	"parameter_set": "PS",
	"parameter_set_title": "T",
	"exported_at": datetime(2026, 1, 2, 3, 4, 5),
	"exported_by": "u@x",
	"exported_by_name": "U",
	"file_type": "x",
	"source": "NC Costing Run CR-1",
}


def data(*services):
	return {
		"run": {"name": "CR-1", "costing_date": date(2026, 12, 31), "price_category": "BHYT"},
		"services": list(services),
		"meta": META,
	}


def wb_of(b):
	return load_workbook(io.BytesIO(b))


class TestRows(unittest.TestCase):
	def test_ii_tong_nhom_ty_trong(self):
		rows = a.annex_rows_ii(svc())
		by = {(r[0], r[1]): r for r in rows}
		self.assertEqual(by[("I", "Chi phí trực tiếp")][2], D("42"))
		self.assertEqual(by[("II", "Chi phí phân bổ")][2], D("8"))
		self.assertEqual(by[("I", "Chi phí trực tiếp")][3], D("84.00"))
		self.assertIsNone(by[("III", "Giá thành toàn bộ (I + II)")][3])
		self.assertEqual(by[("III", "Giá thành toàn bộ (I + II)")][4], "")

	def test_ii_lech_ghi_chu(self):
		rows = a.annex_rows_ii(svc(full_cost=D("60")))
		self.assertIn("Lệch", [r for r in rows if r[0] == "III"][0][4])

	def test_ii_can_lam_sang_va_ngoai_kiem(self):
		rows = a.annex_rows_ii(svc(is_paraclinical=1, eqa_cost=D("3")))
		self.assertEqual(rows[0][4], a.PARACLINICAL_NOTE)
		self.assertIn(["7", "Ngoại kiểm", D("3"), D("6.00"), ""], rows)

	def test_ii_full_cost_zero(self):
		rows = a.annex_rows_ii(svc(full_cost=D("0")))
		self.assertIsNone(rows[0][3])

	def test_iii_yeu_to_va_ghi_chu_chenh(self):
		row = a.annex_rows_iii(svc())
		self.assertEqual(row[4:9], [D("13"), D("8"), D("25"), D("3"), D("1")])
		self.assertEqual(row[10], "")
		self.assertEqual(row[9], D("50"))
		self.assertIn("ngoại kiểm", a.annex_rows_iii(svc(full_cost=D("70")))[10])

	def test_iv_khong_phan_bo(self):
		rows = a.annex_rows_iv(svc())
		self.assertEqual(rows[2][1], "Không có chi phí phân bổ")

	def test_iv_co_phan_bo(self):
		lines = [
			{"component": "LABOR", "allocation_rule": "R", "driver_value": 1, "driver_total": 2, "pool_amount": 9, "amount": 3}
		]
		rows = a.annex_rows_iv(svc(alloc_lines=lines))
		self.assertEqual(rows[2][2:], ["Phân bổ", "R", 1, 2, 9, D("3")])
		self.assertEqual(rows[-1][7], D("50"))

	def test_v_loi_va_canh_bao(self):
		r = a.annex_row_v(svc(calc_status="Lỗi", calc_message="Thiếu giá"))
		self.assertEqual(r[5:8], [None, None, None])
		self.assertEqual(r[8], "Tính lỗi: Thiếu giá")
		self.assertEqual(a.annex_row_v(svc(calc_status="Cảnh báo", calc_message="W"))[8], "W")
		self.assertEqual(a.annex_row_v(svc())[7], D("100"))


class TestTemplates(unittest.TestCase):
	def test_tieu_de_mau_bang_hang(self):
		for code, spec in a.ANNEX.items():
			ws = a.load_template(code).active
			self.assertEqual(header_tuple(ws, code), spec["columns"])
			self.assertTrue(a.template_path(code).exists(), code)

	def test_make_template_thieu_tep(self):
		ws = a.make_template("III").active
		self.assertEqual(a.header_of(ws, "III"), a.ANNEX_III_COLUMNS)


def header_tuple(ws, code):
	return a.header_of(ws, code)


class TestBuild(unittest.TestCase):
	def test_ii_mot_trang_moi_dich_vu_va_thong_tin(self):
		wb = wb_of(a.build_annex_ii(data(svc("B"), svc("A"))))
		self.assertEqual(wb.sheetnames, ["A", "B", meta.INFO_SHEET])
		ws = wb["A"]
		self.assertEqual(a.header_of(ws, "II"), a.ANNEX_II_COLUMNS)
		self.assertEqual(ws.cell(7, 3).value, 42)
		self.assertIn("CR-1", ws.oddFooter.center.text)
		self.assertIn("Lần tính giá CR-1", ws["A4"].value)

	def test_ii_ten_trang_trung_va_dai(self):
		long = "X" * 40
		wb = wb_of(a.build_annex_ii(data(svc(long), svc(long))))
		names = wb.sheetnames[:2]
		self.assertEqual(len(set(n.lower() for n in names)), 2)
		self.assertTrue(all(len(n) <= 31 for n in names))

	def test_ii_bo_dich_vu_loi_va_ghi_o_thong_tin(self):
		wb = wb_of(a.build_annex_ii(data(svc("A"), svc("E", calc_status="Lỗi"))))
		self.assertEqual(wb.sheetnames, ["A", meta.INFO_SHEET])
		info = wb[meta.INFO_SHEET]
		vals = {info.cell(r, 1).value: info.cell(r, 2).value for r in range(1, info.max_row + 1)}
		self.assertEqual(vals["Dịch vụ tính lỗi, không xuất"], "E")
		self.assertEqual(vals["Ghi chú mẫu biểu"], meta.TEMPLATE_NOTE)

	def test_ii_khong_co_dich_vu(self):
		wb = wb_of(a.build_annex_ii(data()))
		self.assertIn(meta.INFO_SHEET, wb.sheetnames)

	def test_iii_iv_v(self):
		d = data(svc("B"), svc("A"), svc("E", calc_status="Lỗi", calc_message="m"))
		w3 = wb_of(a.build_annex_iii(d)).worksheets[0]
		self.assertEqual(a.header_of(w3, "III"), a.ANNEX_III_COLUMNS)
		self.assertEqual([w3.cell(6, 2).value, w3.cell(7, 2).value, w3.cell(8, 2).value], ["A", "B", None])
		w4 = wb_of(a.build_annex_iv(d)).worksheets[0]
		self.assertEqual(a.header_of(w4, "IV"), a.ANNEX_IV_COLUMNS)
		self.assertEqual(w4.cell(6, 1).value, 1)
		w5 = wb_of(a.build_annex_v(d)).worksheets[0]
		self.assertEqual(a.header_of(w5, "V"), a.ANNEX_V_COLUMNS)
		self.assertEqual(w5.cell(8, 10).value, "Tính lỗi: m")
		self.assertEqual(w5.cell(6, 9).number_format, a.MONEY0_FMT)
