"""Golden BR-COST-001/002/007: so engine voi docs/golden/golden_engine.py (khong chep so vao test)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "docs" / "golden"))
import golden_engine as g

from normcore.costing.engine import LaborLine, compute_direct_lines, job_rate

P = g.PARAM
SERVICE = "DV-TEST-A"
LABOR_IDS = ("L01", "L03", "L04", "L09")


def _engine_job_rate(code):
	j = g.JOB[code]
	return job_rate(
		P["base_salary"], j["coef"], j["allow"], P["contribution"], j["other"], P["days"], P["hours"]
	)


class TestLaborGolden(unittest.TestCase):
	def test_TC_RES_05_golden_don_gia_gio_cong(self):
		for code in g.JOB:
			with self.subTest(job=code):
				annual, rate = g.job_rate(code)
				r = _engine_job_rate(code)
				self.assertEqual(r.annual_cost, annual)
				self.assertEqual(r.hourly_rate, rate)

	def test_TC_COST_01_golden_labor_l01_l03_l04_l09(self):
		expected = {line.line_id: (q, rate, amt) for line, q, rate, amt in g.direct_lines(SERVICE)}
		norm = {line.line_id: line for line in g.NORMS[SERVICE]}
		for line_id in LABOR_IDS:
			with self.subTest(line=line_id):
				n = norm[line_id]
				self.assertEqual(n.comp, "LABOR")
				rate = _engine_job_rate(n.res).hourly_rate
				(r,) = compute_direct_lines([LaborLine(line_id, n.qty, n.headcount, rate, n.authority)])
				q, unit_rate, amt = expected[line_id]
				self.assertEqual(r.applied_qty, q)
				self.assertEqual(r.unit_rate, unit_rate)
				self.assertEqual(r.amount, amt)
