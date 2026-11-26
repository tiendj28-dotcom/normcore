"""Unit test FEAT-019 T04: exports/norm_set.py mở rộng (FR-OUT-006, 008). Không sửa test FEAT-034."""

import io
import unittest
from datetime import datetime

from openpyxl import load_workbook

from normcore.exports import meta as meta_mod
from normcore.exports import norm_set

META = {
	"run": None,
	"exported_at": datetime(2026, 1, 1, 8, 0, 0),
	"exported_by": "u@x",
	"exported_by_name": "U",
	"file_type": "Bộ định mức (Excel)",
	"source": "NC Norm Set DM-1",
}


def ln(lid, sid, title, **kw):
	d = {"step_id": sid, "step_title": title, "line_id": lid, "component": "LABOR", "basis": "Quy trình", "confirmed_by": "h@x"}
	d.update(kw)
	return d


DATA = {
	"head": {"name": "DM-1", "technical_service_label": "A", "department": "K", "version_no": 1, "status": "Đã khóa", "test_system": "T", "tests_per_tube": 4},
	"has_test_system": False,
	"lines": [ln("L01", "S001", "Bước 1"), ln("L02", "S001", "Bước 1"), ln("L10", "", "Chung cho cả dịch vụ")],
}


class TestNormSetMeta(unittest.TestCase):
	def test_workbook_khong_meta_giu_nguyen(self):
		wb = load_workbook(io.BytesIO(norm_set.build_workbook(DATA)))
		self.assertEqual(wb.sheetnames, ["Bộ định mức"])

	def test_workbook_co_meta_trang_cuoi(self):
		wb = load_workbook(io.BytesIO(norm_set.build_workbook(DATA, META)))
		self.assertEqual(wb.sheetnames, ["Bộ định mức", meta_mod.INFO_SHEET])
		info = wb[meta_mod.INFO_SHEET]
		vals = {info.cell(r, 1).value: info.cell(r, 2).value for r in range(1, info.max_row + 1)}
		self.assertEqual(vals["Mã lần tính giá"], meta_mod.NO_RUN)

	def test_pdf_context_nhom_theo_buoc(self):
		c = norm_set.pdf_context(DATA, META)
		self.assertEqual([g["step_id"] for g in c["groups"]], ["S001", ""])
		self.assertEqual(len(c["groups"][0]["rows"]), 2)
		self.assertEqual(c["groups"][0]["title"], "S001 — Bước 1")
		self.assertEqual(c["groups"][1]["title"], norm_set.GENERAL_STEP)
		self.assertIn("Căn cứ", c["columns"])
		self.assertIn("Người xác nhận", c["columns"])
		self.assertNotIn("Nhân k", c["columns"])
		self.assertNotIn("Hệ thống xét nghiệm", [h[0] for h in c["head"]])
		self.assertIn(meta_mod.NO_RUN, c["footer"])

	def test_pdf_context_can_lam_sang(self):
		c = norm_set.pdf_context(dict(DATA, has_test_system=True), META)
		self.assertIn("Nhân k", c["columns"])
		self.assertIn("Hệ thống xét nghiệm", [h[0] for h in c["head"]])


def test_mau_norm_set_html():
	import jinja2
	from pathlib import Path

	tpl = (Path(norm_set.__file__).parent / "templates" / "norm_set.html").read_text(encoding="utf-8")
	html = jinja2.Environment(autoescape=True).from_string(tpl).render(**norm_set.pdf_context(DATA, META))
	assert "S001 — Bước 1" in html and "Chung cho cả dịch vụ" in html and "Căn cứ" in html
	assert "Người xác nhận" in html and "Thông tin xuất" in html and "footer-html" in html
	assert html.count("L01") == 1
	html2 = jinja2.Environment().from_string(tpl).render(**norm_set.pdf_context(dict(DATA, has_test_system=True, qc_plan=None), META))
	assert "Chưa có kế hoạch chất lượng" in html2 and "Chưa có chương trình ngoại kiểm" in html2
