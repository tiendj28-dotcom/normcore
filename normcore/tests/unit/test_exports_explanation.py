"""Unit test FEAT-019 T01: định dạng số của exports/explanation.py (NFR-LOC-001)."""

import unittest
from decimal import Decimal as D

from normcore.exports import explanation as e


class TestMoney(unittest.TestCase):
	def test_money(self):
		self.assertEqual(e.money(D("287745.46")), "287.745,46")
		self.assertEqual(e.money(287745.46), "287.745,46")
		self.assertEqual(e.money(D("-63636.36")), "−63.636,36")
		self.assertEqual(e.money(0), "0,00")
		self.assertEqual(e.money(None), "")
		self.assertEqual(e.money("1234.5"), "1.234,50")

	def test_money0(self):
		self.assertEqual(e.money0(302100), "302.100")
		self.assertEqual(e.money0(D("92600")), "92.600")
		self.assertEqual(e.money0(None), "")
		self.assertEqual(e.money0(-1500), "−1.500")

	def test_qty(self):
		self.assertEqual(e.qty(D("2")), "2")
		self.assertEqual(e.qty(D("0.5")), "0,5")
		self.assertEqual(e.qty(D("1234.5600")), "1.234,56")
		self.assertEqual(e.qty(None), "")


# ---- T05: ngữ cảnh và mẫu Jinja ----
from datetime import datetime  # noqa: E402
from pathlib import Path  # noqa: E402

import jinja2  # noqa: E402

TPL = Path(e.__file__).parent / "templates"
META = {
	"run": "CR-1",
	"parameter_set": "PS",
	"parameter_set_title": "Bộ",
	"exported_at": datetime(2026, 1, 2, 3, 4, 5),
	"exported_by": "u@x",
	"exported_by_name": "U",
	"file_type": "Bảng giải trình (PDF)",
	"source": "NC Service Cost X",
}


def ln(lid, amount):
	return {"norm_line_id": lid, "resource_label": "Nguồn lực", "applied_qty": 2, "unit_rate": 100.5, "amount": amount, "rate_source": "Hồ sơ", "warning": ""}


EXPL = {
	"header": {"service": "S", "service_name": "Tên", "department": "K01", "costing_run": "CR-1", "price_category": "BHYT", "volume": 4000, "direct_total": 183963.06, "alloc_total": 103782.4, "full_cost": 287745.46, "accumulation": 14387.27, "obligation": 0, "calculated_price": 302132.73, "rounded_price": 302100},
	"direct_groups": [
		{"label": "Nhân công", "total": 100.0, "steps": [{"step_label": "S001 — Chuẩn bị", "total": 60.0, "lines": [ln("L01", 60.0)]}, {"step_label": "S002 — Thực hiện", "total": 40.0, "lines": [ln("L03", 40.0)]}]},
		{"label": "Thuốc", "total": 5.0, "steps": [{"step_label": "Chung", "total": 5.0, "lines": [ln("L10", 5.0)]}]},
	],
	"allocation_lines": [{"component": "LABOR", "allocation_rule": "R", "driver_value": 1, "driver_total": 2, "pool_amount": 9, "amount": 52151.66}],
	"structure": [{"label": "Nhân công", "amount": 100, "share_pct": 0.03}],
	"notes": ["Ghi chú A"],
	"paraclinical": None,
}


class TestPdfContext(unittest.TestCase):
	def render(self):
		ctx = e.pdf_context(EXPL, META)
		env = jinja2.Environment(autoescape=True)
		return ctx, env.from_string((TPL / "service_explanation.html").read_text(encoding="utf-8")).render(**ctx)

	def test_context(self):
		ctx, _ = self.render()
		self.assertEqual([g["label"] for g in ctx["direct_groups"]], ["Nhân công", "Thuốc"])
		self.assertEqual(ctx["full_cost"], "287.745,46")
		self.assertIn("CR-1", ctx["footer"])
		self.assertEqual(dict(ctx["totals"])["Giá làm tròn"], "302.100")

	def test_mau_html(self):
		_, html = self.render()
		for s in ("Nhân công", "S001 — Chuẩn bị", "S002 — Thực hiện", "287.745,46", "Thông tin xuất", "footer-html", "Ghi chú A", "52.151,66", "Cơ cấu giá"):
			self.assertIn(s, html)
		self.assertLess(html.index("Nhân công"), html.index("Thuốc"))
		self.assertEqual(html.count("L01"), 1)
		self.assertNotIn("http://", html)
		self.assertNotIn("https://", html)

	def test_khong_phan_bo(self):
		ctx = e.pdf_context(dict(EXPL, allocation_lines=[], structure=[], notes=[]), META)
		html = jinja2.Environment().from_string((TPL / "service_explanation.html").read_text(encoding="utf-8")).render(**ctx)
		self.assertIn("Không có chi phí phân bổ", html)
