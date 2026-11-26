"""Unit test FEAT-015: rates.py."""

import unittest
from datetime import date
from decimal import Decimal as D

from normcore.costing import pricing, rates
from normcore.costing.engine import DEPR_EXCLUDED_WARNING


def _p(name="DG-1", price="3000", valid_to=None, verified=True, doc=date(2026, 1, 1)):
	return pricing.PriceRecord(name, D(price), "Hợp đồng", doc, date(2026, 1, 1), valid_to, verified)


class TestRates(unittest.TestCase):
	def test_labor(self):
		self.assertIsNone(rates.labor_rate(None, "s"))
		self.assertEqual(rates.labor_rate("12.5", "s").rate, D("12.5"))

	def test_material(self):
		on = date(2026, 12, 31)
		r = rates.material_rate([_p()], on, None, "Vật tư", 200, False, {"DG-1": "lbl"})
		self.assertEqual((r.rate, r.source, r.reuse_count), (D("3000.0000"), "lbl", 200))
		self.assertEqual(rates.material_rate([_p()], on, 10, "Hóa chất", 1, False, {}).rate, D("300.0000"))
		self.assertEqual(rates.material_rate([_p()], on, 10, "Hóa chất", 0, False, {}).source, "DG-1")
		self.assertIsNone(rates.material_rate([], on, None, "Vật tư", 1, False, {}))
		self.assertIsNone(rates.material_rate([_p()], on, None, "Hóa chất", 1, False, {}))
		self.assertTrue(rates.material_rate([], on, None, "Vật tư", 1, True, {}).billed_separately)
		w = rates.material_rate([_p(verified=False)], on, None, "Vật tư", 1, False, {}).warnings
		self.assertEqual(w, (pricing.UNVERIFIED_WARNING,))

	def test_utility(self):
		m = rates.labor_rate("1", "m")
		self.assertEqual(rates.utility_rate("kWh", 3000, 0, "PS", m).rate, D("3000"))
		self.assertIn("Giá nước", rates.utility_rate("m3", 0, 9000, "PS", m).source)
		self.assertIs(rates.utility_rate("kWh", 0, 0, "PS", m), m)
		self.assertIsNone(rates.utility_rate("cái", 1, 1, "PS", None))

	def test_room_equipment(self):
		self.assertEqual(rates.room_rate("52800000", "2112", True, "R1").rate, D("25000.0000"))
		r = rates.room_rate("52800000", "2112", False, "R1")
		self.assertEqual((r.rate, r.warnings), (D("0"), (DEPR_EXCLUDED_WARNING,)))
		self.assertIsNone(rates.equipment_rate(None, True, True, "s"))
		self.assertEqual(rates.equipment_rate(1.5, False, True, "s").warnings, (DEPR_EXCLUDED_WARNING,))
		self.assertEqual(rates.equipment_rate(1.5, False, False, "s").warnings, ())
