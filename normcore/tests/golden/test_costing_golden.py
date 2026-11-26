"""Golden FEAT-015: engine/rates/runner so với docs/golden/golden_engine.py (không chép số vào test)."""

import sys
import unittest
from datetime import date
from decimal import Decimal as D
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "docs" / "golden"))
import golden_engine as g

from normcore.costing import engine, pricing, rates, resources, runner

ON = g.COSTING_DATE
DEPR_WARN = engine.DEPR_EXCLUDED_WARNING


def _params(include_depr=True):
	P = g.PARAM
	return engine.PricingParams(
		P["accumulation_mode"], P["accumulation_rate"], P["obligation_rate"], P["rounding_unit"], include_depr
	)


def _rate_for(line, include_depr):
	if line.comp == "LABOR":
		j = g.JOB[line.res]
		jr = engine.job_rate(
			g.PARAM["base_salary"],
			j["coef"],
			j["allow"],
			g.PARAM["contribution"],
			j["other"],
			g.PARAM["days"],
			g.PARAM["hours"],
		)
		return rates.labor_rate(jr.hourly_rate, f"PS · {line.res}")
	if line.comp in ("DRUG", "SUPPLY"):
		if line.res == "THUOCX" and _rate_for.missing_thuocx:
			return None
		it = g.ITEM[line.res]
		pr = pricing.PriceRecord(
			"DG-" + line.res, it["price"], "Hợp đồng", date(2026, 1, 1), date(2026, 1, 1), None, True
		)
		return rates.material_rate([pr], ON, None, "Vật tư", it["reuse"], False, {})
	if line.comp == "EQUIPMENT":
		e = g.EQUIP[line.res]
		machine = resources.machine_annual(
			resources.BUY, e["cost"], e["life"], e["in_service"], None, ON, resources.ZERO, include_depr
		)
		annual = resources.equipment_annual(machine, e["maint"], e["calib"])
		hourly = resources.machine_hourly_rate(annual, e["hours"], e["util"])
		return rates.equipment_rate(hourly, include_depr, True, line.res)
	if line.comp == "INFRA":
		r = g.ROOM[line.res]
		return rates.room_rate(r["annual"], r["hours"], include_depr, line.res)
	return rates.utility_rate("kWh", g.PARAM["electricity_price"], 0, "PS", None)  # UTILITY


_rate_for.missing_thuocx = False


def _input(svc, include_depr=True):
	lines = tuple(
		engine.NormLine(
			l.line_id,
			l.step,
			l.comp,
			l.res,
			l.res,
			l.qty,
			l.authority,
			l.headcount,
			l.wastage,
			l.excluded,
			"Thanh toán riêng" if l.excluded else None,
		)
		for l in g.NORMS[svc]
	)
	rts = {l.line_id: _rate_for(l, include_depr) for l in g.NORMS[svc]}
	return engine.ServiceInput(svc, "K01", "NS-" + svc, lines, rts, g.VOLUME[svc])


def _alloc(res, svc):
	return [
		engine.CostLine("Phân bổ", cat, amt, allocation_rule="R-" + cat)
		for cat, amt in res[svc]["alloc"].items()
	]


def _run_engine(include_depr=True):
	g_res, _, _ = g.run(include_depr)
	params = _params(include_depr)
	out = {}
	for s in g.NORMS:
		r = engine.cost_service(_input(s, include_depr), params)
		out[s] = engine.finish_service(r, _alloc(g_res, s), params)
	return out, g_res


class TestCostingGolden(unittest.TestCase):
	def test_TC_COST_01_thanh_tien_11_dong_DV_TEST_A(self):
		res, _ = _run_engine()
		a = res["DV-TEST-A"]
		expected = g.direct_lines("DV-TEST-A")
		direct = [x for x in a.lines if x.line_type == "Trực tiếp"]
		self.assertEqual(len(direct), 11)
		for line, (gl, q, rate, amt) in zip(direct, expected, strict=True):
			with self.subTest(line=gl.line_id):
				self.assertEqual(line.norm_line_id, gl.line_id)
				self.assertEqual(line.applied_qty, q)
				self.assertEqual(line.unit_rate, rate)
				self.assertEqual(line.amount, amt)
		self.assertEqual(a.direct_total, sum(x[3] for x in expected))
		self.assertEqual(a.direct_total, D("183963.06"))
		self.assertEqual(res["DV-TEST-B"].direct_total, sum(x[3] for x in g.direct_lines("DV-TEST-B")))

	def test_TC_COST_04_gia_thanh_tich_luy_lam_tron(self):
		res, gres = _run_engine()
		for s in g.NORMS:
			with self.subTest(service=s):
				p = res[s].price
				self.assertEqual(p.full_cost, gres[s]["full"])
				self.assertEqual(p.accumulation, gres[s]["accumulation"])
				self.assertEqual(p.calculated_price, gres[s]["calc"])
				self.assertEqual(p.rounded_price, gres[s]["rounded"])
				self.assertEqual(res[s].direct_by_category, gres[s]["by_cat"])

	def test_TC_COST_06_V1_khong_khau_hao(self):
		res, gres = _run_engine(False)
		a = res["DV-TEST-A"]
		by = {x.norm_line_id: x for x in a.lines if x.line_type == "Trực tiếp"}
		self.assertEqual(by["L07"].unit_rate, g.equip_rate("EQ1", False)[1])
		self.assertEqual(by["L08"].unit_rate, g.room_rate("R1", False))
		for lid in ("L07", "L08"):
			self.assertIn(DEPR_WARN, by[lid].warning)
		self.assertNotIn(DEPR_WARN, by["L01"].warning)
		self.assertEqual(a.direct_total, gres["DV-TEST-A"]["direct"])
		self.assertEqual(a.price.full_cost, gres["DV-TEST-A"]["full"])
		self.assertEqual(a.price.rounded_price, gres["DV-TEST-A"]["rounded"])

	def test_TC_COST_07_V4_thieu_don_gia_THUOCX(self):
		_rate_for.missing_thuocx = True
		try:
			params = _params()
			a = engine.cost_service(_input("DV-TEST-A"), params)
			b = engine.cost_service(_input("DV-TEST-B"), params)
		finally:
			_rate_for.missing_thuocx = False
		self.assertEqual(a.status, "Lỗi")
		self.assertIn("L05", a.message)
		self.assertEqual(a.lines, ())
		self.assertEqual(b.status, "Thành công")
		self.assertEqual(b.direct_total, sum(x[3] for x in g.direct_lines("DV-TEST-B")))

	def test_TC_COST_07_chay_runner_dich_vu_khac_van_tinh(self):
		_rate_for.missing_thuocx = True
		try:
			out = runner.run(
				[{"service": s, "department": "K01", "norm_set": "n"} for s in g.NORMS],
				lambda e: _input(e["service"]),
				_params(),
			)
		finally:
			_rate_for.missing_thuocx = False
		self.assertEqual([r.status for r in out], ["Lỗi", "Thành công"])
		self.assertIsNone(out[0].price)
		self.assertIsNotNone(out[1].price)

	def test_TC_COST_12_V3_ON_PRICE(self):
		old = g.PARAM["accumulation_mode"]
		g.PARAM["accumulation_mode"] = "ON_PRICE"
		try:
			res, gres = _run_engine()
		finally:
			g.PARAM["accumulation_mode"] = old
		for s in g.NORMS:
			with self.subTest(service=s):
				p = res[s].price
				self.assertEqual(p.accumulation, gres[s]["accumulation"])
				self.assertEqual(p.calculated_price, gres[s]["calc"])
				self.assertEqual(p.rounded_price, gres[s]["rounded"])
