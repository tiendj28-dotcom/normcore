"""FEAT-028 T02: gợi ý điều chỉnh BR-ADJ-001..007 (không import frappe). FR-ADJ-005."""

import unittest
from dataclasses import replace
from decimal import Decimal

from normcore.benchmark import rules
from normcore.costing import engine, resources

D = Decimal
PRICING = engine.PricingParams(engine.ON_COST, D("0.05"), D(0), D(1), True)
EQ1_RATE = resources.machine_hourly_rate(D("186000000"), D("2112"), D("0.4"))


def _line(line_id, component, resource, qty, step="S002", **kw):
	return engine.NormLine(line_id, step, component, resource, resource, D(qty), **kw)


def _facts(**kw):
	"""DV-TEST-A (golden): trực tiếp 183.963,06; phân bổ 103.782,40; tích lũy ON_COST 5% -> 302.132,73."""
	lines = (
		_line("L04", "LABOR", "DD", 20),
		_line("L05", "DRUG", "THUOCX", 1, wastage_rate=D("0.05")),
		_line("L07", "EQUIPMENT", "EQ1", 20),
		_line("L08", "INFRA", "R1", 30),
	)
	rates = {
		"L04": engine.LineRate(D("59644.89"), "t"),
		"L05": engine.LineRate(D("1000"), "t"),
		"L07": engine.LineRate(EQ1_RATE, "t"),
		"L08": engine.LineRate(D("100"), "t"),
	}
	base = dict(
		direct_total=D("183963.06"),
		alloc_by_category={"ALL": D("103782.40")},
		pricing=PRICING,
		norm_lines=lines,
		line_rates=rates,
		costing_date="2026-12-31",
		price_valid_months=12,
		equipment={
			"EQ1": {
				"annual_cost": D("186000000"),
				"planned_hours": D("2112"),
				"utilization": D("0.4"),
				"maintenance": D("1"),
			}
		},
		time_study={("S002", "DD"): D("15")},
		wastage_cap=D("0.10"),
		parameter_set="PS1",
	)
	base.update(kw)
	return rules.ServiceFacts(**base)


class TestBenchmarkRules(unittest.TestCase):
	def test_gia_tinh_toan_golden(self):
		f = _facts()
		assert rules._price(f, f.direct_total) == D("302132.73")

	def test_TC_ADJ_04_goi_y_dv_test_a(self):
		out = rules.generate(_facts(), D("20.85"), D(10))
		by = {s.rule_code: s for s in out}
		eq1, l04 = by["BR-ADJ-001"], by["BR-ADJ-002"]
		assert (eq1.target_ref, eq1.current_value, eq1.suggested_value) == ("EQ1", "0,4", "0,5")
		assert eq1.direction == rules.DOWN and eq1.estimated_impact == D("-15411.93")
		assert (l04.target_ref, l04.current_value, l04.suggested_value) == ("L04", "20 phút", "15 phút")
		assert l04.estimated_impact == D("-5218.93")
		assert eq1.text and l04.text and not eq1.requires_procedure_change
		impacts = [abs(s.estimated_impact) for s in out]
		assert impacts == sorted(impacts, reverse=True)
		assert [s.rule_code for s in out][:2] == ["BR-ADJ-001", "BR-ADJ-002"]

	def test_FR_ADJ_005_trong_nguong_khong_goi_y(self):
		assert rules.generate(_facts(), D("10"), D(10)) == []
		assert rules.generate(_facts(), None, D(10)) == []

	def test_FR_ADJ_005_lech_am_chi_quy_tac_tang(self):
		f = _facts(equipment={"EQ1": {**_facts().equipment["EQ1"], "maintenance": 0}})
		out = rules.generate(f, D("-20"), D(10))
		codes = {s.rule_code for s in out}
		assert "BR-ADJ-001" not in codes and "BR-ADJ-002" not in codes
		assert "BR-ADJ-006" in codes and all(s.direction == rules.UP for s in out)
		assert {s.target_ref for s in out if s.rule_code == "BR-ADJ-006"} == {"EQ1", "UTILITY"}
		assert all(s.estimated_impact is None or s.rule_code == "BR-ADJ-005" for s in out)

	def test_rule_001_khong_kich_hoat_khi_he_so_du(self):
		eq = {"EQ1": {**_facts().equipment["EQ1"], "utilization": D("0.5")}}
		assert rules.rule_001_utilization(_facts(equipment=eq)) == []
		assert rules.rule_001_utilization(_facts(equipment={})) == []

	def test_rule_002_khong_kich_hoat(self):
		assert rules.rule_002_time_study(_facts(time_study={("S002", "DD"): D("18")})) == []  # 20 <= 18*1.15
		assert rules.rule_002_time_study(_facts(time_study={})) == []

	def test_rule_003_mat_hang_tuong_duong(self):
		cheap = {
			"L05": [("THUOCZ", engine.LineRate(D("500"), "t")), ("THUOCW", engine.LineRate(D("2000"), "t"))]
		}
		out = rules.rule_003_equivalent(_facts(equivalents=cheap))
		assert len(out) == 1
		s = out[0]
		assert (s.target_ref, s.current_value, s.suggested_value) == ("L05", "THUOCX", "THUOCZ")
		assert s.requires_procedure_change and s.estimated_impact < 0
		assert (
			rules.rule_003_equivalent(
				_facts(equivalents={"L05": [("THUOCW", engine.LineRate(D("2000"), "t"))]})
			)
			== []
		)
		assert rules.rule_003_equivalent(_facts()) == []

	def test_rule_004_hao_hut(self):
		out = rules.rule_004_wastage(_facts(wastage_cap=D("0.02")))
		assert [(s.target_ref, s.current_value, s.suggested_value) for s in out] == [("L05", "5%", "2%")]
		assert out[0].estimated_impact < 0
		assert rules.rule_004_wastage(_facts()) == []

	def test_rule_005_tich_luy_hai_huong(self):
		f = _facts()
		down = rules.rule_005_accumulation(f, rules.DOWN)[0]
		up = rules.rule_005_accumulation(f, rules.UP)[0]
		assert (down.current_value, down.suggested_value) == ("5%", "4%")
		assert (up.suggested_value) == "6%" and down.estimated_impact < 0 < up.estimated_impact
		assert down.estimated_impact == D("-2877.45")
		assert down.component == "PARAMETER" and down.target_ref == "PS1"

	def test_rule_005_khong_kich_hoat(self):
		assert (
			rules.rule_005_accumulation(_facts(pricing=replace(PRICING, accumulation_mode=None)), rules.DOWN)
			== []
		)
		assert (
			rules.rule_005_accumulation(_facts(pricing=replace(PRICING, accumulation_rate=D(0))), rules.UP)
			== []
		)

	def test_rule_005_khong_am(self):
		p = replace(PRICING, accumulation_rate=D("0.005"))
		assert rules.rule_005_accumulation(_facts(pricing=p), rules.DOWN) == []

	def test_rule_006_khong_kich_hoat_khi_du(self):
		lines = (*_facts().norm_lines, _line("L09", "UTILITY", "DIEN", 1))
		assert rules.rule_006_missing(_facts(norm_lines=lines)) == []

	def test_rule_007_don_gia_cu_va_bo_tham_so(self):
		stale = {
			"L05": {"item": "THUOCX", "valid_from": "2025-01-01"},
			"L04": {"item": "NEW", "valid_from": "2026-06-01"},
		}
		out = rules.rule_007_stale(_facts(stale_prices=stale, latest_parameter_set="PS2"))
		assert [(s.component, s.target_ref) for s in out] == [("ITEM", "THUOCX"), ("PARAMETER", "PS1")]
		assert all(s.estimated_impact is None and s.direction == rules.UP for s in out)

	def test_rule_007_khong_kich_hoat(self):
		assert rules.rule_007_stale(_facts(stale_prices={}, latest_parameter_set="PS1")) == []
		assert (
			rules.rule_007_stale(
				_facts(costing_date=None, stale_prices={"L05": {"item": "X", "valid_from": "2020-01-01"}})
			)
			== []
		)

	def test_tac_dong_bang_khong_bi_bo_va_sap_xep_khong_tac_dong_sau(self):
		a = rules._make("BR-ADJ-006", rules.UP, "INFRA", "INFRA", "a", "b", None)
		b = rules._make("BR-ADJ-001", rules.DOWN, "EQUIPMENT", "X", "a", "b", D("-3"))
		c = rules._make("BR-ADJ-004", rules.DOWN, "DRUG", "Y", "a", "b", D("-9"))
		assert [s.target_ref for s in sorted([a, b, c], key=rules._sort_key)] == ["Y", "X", "INFRA"]

	def test_impact_khong_doi_la_khong_va_bi_bo(self):
		f = _facts()
		assert rules.impact(f, 0) == 0

	def test_fmt(self):
		assert (
			rules._fmt(D("0.40")) == "0,4" and rules._fmt(D("20")) == "20" and rules._fmt(D("5.5")) == "5,5"
		)
