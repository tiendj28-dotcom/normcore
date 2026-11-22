"""Golden BR-COST-003, BR-CLS-002 (đơn giá), FR-RES-014: so pricing với docs/golden (không chép số vào test)."""

import sys
import unittest
from datetime import date
from decimal import Decimal as D
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "docs" / "golden"))
import golden_cls as c
import golden_engine as g

from normcore.costing.pricing import PriceRecord, material_line, unit_price_per_norm

MATERIAL = ("DRUG", "SUPPLY")


def _price(code):
	return PriceRecord(
		name=code,
		unit_price=g.ITEM[code]["price"],
		price_source="Giá công bố",
		document_date=date(2026, 6, 1),
		valid_from=date(2026, 1, 1),
		valid_to=None,
		verified=True,
	)


class TestMaterialGolden(unittest.TestCase):
	def test_TC_RES_07_dong_vat_chat_khop_golden_engine(self):
		rows = [r for r in g.direct_lines("DV-TEST-A") if r[0].comp in MATERIAL]
		self.assertEqual({r[0].line_id for r in rows}, {"L02", "L05", "L06", "L11"})
		for line, qty, _rate, amount in rows:
			with self.subTest(line=line.line_id):
				res = material_line(
					qty,
					line.wastage,
					g.ITEM[line.res]["reuse"],
					[_price(line.res)],
					g.COSTING_DATE,
					billed_separately=line.excluded,
				)
				self.assertEqual(res.amount, amount)
				self.assertEqual(res.excluded_reason is not None, line.excluded)

	def test_TC_CLS_47_don_gia_dinh_muc_khop_golden_cls(self):
		for code, item in c.ITEM.items():
			with self.subTest(item=code):
				self.assertEqual(unit_price_per_norm(item["price"], item["units"]), c.unit_price(code))
		self.assertEqual(c.unit_price("HC_GLU"), D("30000.0000"))
