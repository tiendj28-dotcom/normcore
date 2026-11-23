"""Golden FEAT-016: tổng số liệu kế toán (TC-ACCT-06) và tỷ lệ cấp 1 (TC-ACCT-09) khớp golden_engine."""

import sys
import unittest
from decimal import Decimal as D
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "docs" / "golden"))
import golden_engine as g

from normcore.costing import accounting as a
from normcore.costing import allocation_rules as ar

# Tệp vàng dạng tài khoản (technical-design mục 6): (mã TK, TTCP, số tiền)
FILE = (
	("61111", "K01", "500000000"),
	("61111", "K01", "200000000"),
	("61112", "K01", "260000000"),
	("61113", "K01", "300000000"),
	("611122", "K01", "40000000"),
	("61118", "K01", "100000000"),
	("811", "K01", "5000000"),
	("61111", "HC", "300000000"),
	("61118", "HC", "150000000"),
	("642", "HC", "250000000"),
)


def golden_lines():
	return [{"account_code": c, "cost_center": cc, "amount": amt} for c, cc, amt in FILE]


class TestAccountingGolden(unittest.TestCase):
	def test_TC_ACCT_06_tong_tep_vang_khop_golden(self):
		lines = golden_lines()
		a.assign_categories(lines, dict(a.DEFAULT_ACCOUNT_MAPPING))
		got = {}
		for cc, cat, v in a.totals(lines):
			got.setdefault(cc, {})[cat] = v
		self.assertEqual(got, g.ACCOUNTING)
		self.assertEqual(a.total_amount(lines), D("2105000000"))
		self.assertEqual(len(a.totals(lines)), 7)

	def test_TC_ACCT_09_ty_le_cap1_k01_khop_golden(self):
		shares = ar.driver_shares({"K01": 20, "K02": 30})
		self.assertEqual(shares["K01"], D("0.4"))
		self.assertEqual(shares["K01"], g.HEADCOUNT["K01"] / sum(g.HEADCOUNT.values()))
		self.assertEqual(g.L1_DRIVER, "HEADCOUNT")
