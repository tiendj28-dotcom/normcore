"""Golden BR-COST-013: so apply_accumulation voi docs/golden/golden_engine.py (khong chep so vao test)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "docs" / "golden"))
import golden_engine as g

from normcore.costing.engine import apply_accumulation

RES, _, _ = g.run(True)


class TestAccumulationGolden(unittest.TestCase):
	def test_TC_COST_04_golden_tich_luy_gia_tinh_toan(self):
		for service in ("DV-TEST-A", "DV-TEST-B"):
			with self.subTest(service=service):
				exp = RES[service]
				r = apply_accumulation(
					exp["full"],
					g.PARAM["accumulation_mode"],
					g.PARAM["accumulation_rate"],
					g.PARAM["obligation_rate"],
				)
				self.assertEqual(r.accumulation, exp["accumulation"])
				self.assertEqual(r.calculated_price, exp["calc"])
