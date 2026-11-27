"""Unit test FEAT-019 T01: định dạng số của exports/explanation.py (NFR-LOC-001)."""

import unittest
from decimal import Decimal as D

from normcore.exports import explanation as e


class TestMoney(unittest.TestCase):
	def test_money(self):
		self.assertEqual(e.money(D("287745.46")), "287.745,46")
		self.assertEqual(e.money(287745.46), "287.745,46")
		self.assertEqual(e.money(D("-63636.36")), "\u221263.636,36")
		self.assertEqual(e.money(0), "0,00")
		self.assertEqual(e.money(None), "")
		self.assertEqual(e.money("1234.5"), "1.234,50")

	def test_money0(self):
		self.assertEqual(e.money0(302100), "302.100")
		self.assertEqual(e.money0(D("92600")), "92.600")
		self.assertEqual(e.money0(None), "")
		self.assertEqual(e.money0(-1500), "\u22121.500")

	def test_qty(self):
		self.assertEqual(e.qty(D("2")), "2")
		self.assertEqual(e.qty(D("0.5")), "0,5")
		self.assertEqual(e.qty(D("1234.5600")), "1.234,56")
		self.assertEqual(e.qty(None), "")
