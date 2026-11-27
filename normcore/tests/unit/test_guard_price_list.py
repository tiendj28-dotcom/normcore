"""FEAT-027 T02: nguồn gửi AI của bảng giá PDF (FR-AI-011, NFR-SEC-005)."""

import unittest

from normcore.ai import guard
from normcore.library.extract import Page


class TestGuardPriceList(unittest.TestCase):
	def test_FR_AI_011_guard_trang_bang_gia(self):
		out = guard.price_list_pages([Page(1, "Glucose 25.000"), Page(2, "  "), Page(None, "Siêu âm")])
		self.assertEqual(out, [{"page": 1, "text": "Glucose 25.000"}, {"page": 3, "text": "Siêu âm"}])
		for bad in (
			{"doctype": "NC Benchmark Price", "price": 1},
			{"page": 1, "text": "x"},
			"text",
			None,
		):
			with self.assertRaises(guard.GuardError):
				guard.price_list_pages([bad])
		self.assertEqual(guard.price_list_pages([]), [])
		for dt in ("NC Benchmark Price", "NC CPI Index", "NC Price Category"):
			self.assertIn(dt, guard.FORBIDDEN_DOCTYPES)
			self.assertFalse(guard.is_allowed(dt))
