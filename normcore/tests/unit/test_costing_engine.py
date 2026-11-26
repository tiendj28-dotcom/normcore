"""Unit test FEAT-015: engine mở rộng (direct_line, round_price, price_service, cost_service, ...)."""

import unittest
from decimal import Decimal as D

from normcore.costing import engine as e


def _line(**kw):
	base = dict(line_id="L01", step_id="S1", component="LABOR", resource="DD", resource_label="DD",
		hospital_qty=D("10"))
	base.update(kw)
	return e.NormLine(**base)


PARAMS = e.PricingParams("ON_COST", D("0.05"), D("0"), D("100"), True)


class TestRound(unittest.TestCase):
	def test_TC_COST_13_lam_tron_302150_va_302149_99(self):
		self.assertEqual(e.round_price(D("302150.00"), D("100")), D("302200"))
		self.assertEqual(e.round_price(D("302149.99"), D("100")), D("302100"))

	def test_don_vi_khong_hop_le(self):
		with self.assertRaises(ValueError):
			e.round_price(D("1"), D("0"))


class TestDirectLine(unittest.TestCase):
	def test_labor(self):
		r = e.direct_line(_line(), e.LineRate(D("60"), "src"))
		self.assertEqual((r.applied_qty, r.amount, r.rate_source, r.warning), (D("10"), D("10.00"), "src", ""))

	def test_excluded(self):
		r = e.direct_line(_line(excluded=True, exclude_reason="x"), e.LineRate(D("60"), "src"))
		self.assertEqual((r.amount, r.rate_source), (D("0"), "Loại trừ: x"))

	def test_billed_separately(self):
		r = e.direct_line(_line(component="DRUG"), e.LineRate(D("0"), "s", billed_separately=True, warnings=("w",)))
		self.assertEqual(r.amount, D("0"))
		self.assertIn(e.EXCLUDED_REASON, r.warning)
		self.assertIn("w", r.warning)

	def test_authority_min_va_hao_hut(self):
		r = e.direct_line(
			_line(component="DRUG", hospital_qty=D("2"), authority_qty=D("1"), wastage_rate=D("0.05")),
			e.LineRate(D("100"), "s", warnings=("a", "b")),
		)
		self.assertEqual((r.applied_qty, r.amount, r.warning), (D("1"), D("105.00"), "a; b"))


class TestPriceAndCost(unittest.TestCase):
	def test_price_service(self):
		p = e.price_service(D("1000"), {"LABOR": D("100"), "UTILITY": D("0")}, PARAMS)
		self.assertEqual(p.full_cost, D("1100"))
		self.assertEqual(p.accumulation, D("55.00"))
		self.assertEqual(p.calculated_price, D("1155.00"))
		self.assertEqual(p.rounded_price, D("1200"))

	def test_from_values(self):
		pa = e.PricingParams.from_values(
			{"accumulation_mode": "ON_PRICE", "accumulation_rate": 5, "obligation_rate": 2, "rounding_unit": 100},
			{"include_depreciation": 0, "include_accumulation": 1},
		)
		self.assertEqual((pa.accumulation_mode, pa.accumulation_rate, pa.obligation_rate), ("ON_PRICE", D("0.05"), D("0.02")))
		self.assertFalse(pa.include_depreciation)
		for ps, pc in (({"accumulation_mode": "NONE"}, {}), ({"accumulation_mode": "ON_COST"}, {"include_accumulation": 0})):
			self.assertIsNone(e.PricingParams.from_values({**ps, "rounding_unit": 1}, pc).accumulation_mode)

	def _inp(self, rates, lines):
		return e.ServiceInput("S", "K", "NS", tuple(lines), rates, D("5"))

	def test_cost_service_thanh_cong_va_canh_bao(self):
		lines = [_line(line_id="L02", component="DRUG"), _line(line_id="L01")]
		rates = {"L01": e.LineRate(D("60"), "a"), "L02": e.LineRate(D("5"), "b", warnings=("Đơn giá chưa xác minh",))}
		r = e.cost_service(self._inp(rates, lines), PARAMS)
		self.assertEqual(r.status, "Cảnh báo")
		self.assertEqual([x.norm_line_id for x in r.lines], ["L01", "L02"])
		self.assertEqual(r.direct_by_category, {"LABOR": D("10.00"), "DRUG_SUPPLY": D("50.00")})
		self.assertEqual(r.direct_total, D("60.00"))
		ok = e.cost_service(self._inp({"L01": e.LineRate(D("60"), "a")}, [_line()]), PARAMS)
		self.assertEqual(ok.status, "Thành công")

	def test_cost_service_thieu_don_gia(self):
		r = e.cost_service(self._inp({"L01": None}, [_line(), _line(line_id="L00", excluded=True)]), PARAMS)
		self.assertEqual(r.status, "Lỗi")
		self.assertIn("L01 (DD)", r.message)
		self.assertNotIn("L00", r.message)
		self.assertEqual(r.lines, ())
		self.assertEqual(e.finish_service(r, [], PARAMS), r)

	def test_extension(self):
		cl = e.CostLine("Trực tiếp", "LABOR", D("7"))
		r = e.cost_service(self._inp({"L01": e.LineRate(D("1"), "a")}, [_line()]), PARAMS, extension=lambda inp: [cl])
		self.assertEqual(r.direct_total, D("7"))
		none = e.cost_service(self._inp({"L01": e.LineRate(D("60"), "a")}, [_line()]), PARAMS, extension=lambda i: None)
		self.assertEqual(none.direct_total, D("10.00"))

	def test_finish_service_gop_phan_bo(self):
		r = e.cost_service(self._inp({"L01": e.LineRate(D("600"), "a")}, [_line()]), PARAMS)
		al = e.CostLine("Phân bổ", "LABOR", D("20"), allocation_rule="R")
		f = e.finish_service(r, [al], PARAMS)
		self.assertEqual(f.alloc_by_category, {"LABOR": D("20")})
		self.assertEqual(f.price.full_cost, D("120.00"))
		self.assertEqual(len(f.lines), 2)

	def test_group_explanation(self):
		rows = [
			e.CostLine("Trực tiếp", "LABOR", D("1"), "S2"),
			e.CostLine("Trực tiếp", "LABOR", D("2"), ""),
			e.CostLine("Trực tiếp", "LABOR", D("3"), "S1"),
			e.CostLine("Trực tiếp", "UTILITY", D("4"), ""),
			e.CostLine("Phân bổ", "LABOR", D("9")),
		]
		g = e.group_explanation(rows)
		self.assertEqual([x["component"] for x in g], ["LABOR", "UTILITY"])
		self.assertEqual(g[0]["total"], D("6"))
		self.assertEqual([s["step_id"] for s in g[0]["steps"]], ["S1", "S2", ""])
