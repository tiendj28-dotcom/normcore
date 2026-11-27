"""Unit test FEAT-019 T01: exports/meta.py (FR-OUT-008)."""

import unittest
from datetime import datetime

from openpyxl import Workbook

from normcore.exports import meta

M = {
	"run": "CR-0001",
	"parameter_set": "PS-1",
	"parameter_set_title": "Bộ 2026",
	"exported_at": datetime(2026, 3, 5, 14, 7, 9),
	"exported_by": "a@x.vn",
	"exported_by_name": "An Nguyễn",
	"file_type": "Phụ lục II",
	"source": "NC Costing Run CR-0001",
}


class TestMeta(unittest.TestCase):
	def test_info_rows_day_du(self):
		d = dict(meta.info_rows(M))
		self.assertEqual(d["Mã lần tính giá"], "CR-0001")
		self.assertEqual(d["Bộ tham số"], "PS-1 — Bộ 2026")
		self.assertEqual(d["Thời điểm xuất"], "05/03/2026 14:07:09")
		self.assertEqual(d["Người xuất"], "An Nguyễn (a@x.vn)")
		self.assertEqual(d["Loại tệp"], "Phụ lục II")
		self.assertNotIn(meta.TEMPLATE_NOTE, d.values())

	def test_info_rows_template_note_va_khong_co_run(self):
		m = dict(M, run=None, parameter_set=None, template_note=meta.TEMPLATE_NOTE)
		rows = meta.info_rows(m)
		d = dict(rows)
		self.assertEqual(d["Mã lần tính giá"], meta.NO_RUN)
		self.assertEqual(d["Bộ tham số"], "—")
		self.assertIn(meta.TEMPLATE_NOTE, [v for _, v in rows] + [k for k, _ in rows])

	def test_bo_tham_so_khong_ten(self):
		d = dict(meta.info_rows(dict(M, parameter_set_title="")))
		self.assertEqual(d["Bộ tham số"], "PS-1")

	def test_footer(self):
		self.assertEqual(
			meta.footer_text(M),
			"Lần tính CR-0001 · Bộ tham số PS-1 · Xuất 05/03/2026 14:07 · An Nguyễn",
		)

	def test_add_info_sheet_cuoi_va_chan_trang_moi_trang(self):
		wb = Workbook()
		wb.active.title = "A"
		wb.create_sheet("B")
		meta.add_info_sheet(wb, M)
		self.assertEqual(wb.sheetnames, ["A", "B", meta.INFO_SHEET])
		for ws in wb.worksheets:
			self.assertIn("CR-0001", ws.oddFooter.center.text)
		info = wb[meta.INFO_SHEET]
		self.assertEqual(info["A1"].value, "Loại tệp")
		self.assertTrue(info["A1"].font.bold)
		vals = {info.cell(r, 1).value: info.cell(r, 2).value for r in range(1, info.max_row + 1)}
		self.assertEqual(vals["Mã lần tính giá"], "CR-0001")

	def test_extra_rows(self):
		wb = Workbook()
		meta.add_info_sheet(wb, dict(M, extra=[("Dịch vụ tính lỗi, không xuất", "S1")]))
		info = wb[meta.INFO_SHEET]
		self.assertEqual(info.cell(info.max_row, 1).value, "Dịch vụ tính lỗi, không xuất")
