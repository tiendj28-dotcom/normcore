"""Golden FEAT-019: Phụ lục II, III, IV, V khớp golden_engine (TC-OUT-01; FR-OUT-001..004)."""

import sys
import unittest
from decimal import Decimal as D
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "docs" / "golden"))
import golden_engine as g

from normcore.exports import annex as a

FIELD = {
	"LABOR": "direct_labor",
	"DRUG": "direct_drug",
	"SUPPLY": "direct_supply",
	"EQUIPMENT": "direct_equipment",
	"INFRA": "direct_infra",
	"UTILITY": "direct_utility",
}
ALLOC = {
	"LABOR": "alloc_labor",
	"DRUG_SUPPLY": "alloc_drug_supply",
	"DEPRECIATION": "alloc_depreciation",
	"UTILITY": "alloc_utility",
	"MANAGEMENT": "alloc_management",
}


def services():
	res, _, _ = g.run()
	out = []
	for code, r in sorted(res.items()):
		s = {
			"service_code": code,
			"service_name": code,
			"department": "K01",
			"volume": g.VOLUME[code],
			"calc_status": "Thành công",
			"full_cost": r["full"],
			"accumulation": r["accumulation"],
			"obligation": D("0"),
			"calculated_price": r["calc"],
			"rounded_price": r["rounded"],
			"alloc_lines": [],
		}
		for f in FIELD.values():
			s[f] = D("0")
		for line, _q, _rate, amt in r["lines"]:
			s[FIELD[line.comp]] += amt
		for cat, f in ALLOC.items():
			s[f] = r["alloc"].get(cat, D("0"))
			if r["alloc"].get(cat, D("0")):
				s["alloc_lines"].append({"component": cat, "amount": r["alloc"][cat]})
		out.append(s)
	return out, res


def rows_ii(svc):
	return {(r[0], r[1]): r[2] for r in a.annex_rows_ii(svc)}


class TestExportsGolden(unittest.TestCase):
	def test_TC_OUT_01_phu_luc_ii_iii_v_khop_golden(self):
		svcs, res = services()
		for svc in svcs:
			r = res[svc["service_code"]]
			ii = rows_ii(svc)
			self.assertEqual(ii[("I", "Chi phí trực tiếp")], r["direct"])
			self.assertEqual(ii[("II", "Chi phí phân bổ")], r["alloc_sum"])
			self.assertEqual(ii[("III", "Giá thành toàn bộ (I + II)")], r["full"])
			self.assertEqual(ii[("IV", "Tích lũy")], r["accumulation"])
			self.assertEqual(ii[("VI", "Giá tính toán")], r["calc"])
			self.assertEqual(ii[("VII", "Giá đề nghị (đã làm tròn)")], r["rounded"])
			el = a.annex_rows_iii(svc)
			by_cat = r["by_cat"]
			for i, cat in enumerate(a.ELEMENT_ORDER):
				self.assertEqual(el[4 + i], by_cat.get(cat, D("0")) + r["alloc"].get(cat, D("0")))
			self.assertEqual(el[9], r["full"])
			v = a.annex_row_v(svc)
			self.assertEqual(v[5:8], [r["full"], r["calc"], r["rounded"]])
		# bảng mục 2.2 test-cases.md
		a_svc = svcs[0]
		self.assertEqual(rows_ii(a_svc)[("I", "Chi phí trực tiếp")], D("183963.06"))
		self.assertEqual(rows_ii(a_svc)[("II", "Chi phí phân bổ")], D("103782.40"))
		self.assertEqual(a.annex_rows_iii(a_svc)[9], D("287745.46"))
		self.assertEqual(rows_ii(a_svc)[("VII", "Giá đề nghị (đã làm tròn)")], D("302100"))
		self.assertEqual(rows_ii(svcs[1])[("VII", "Giá đề nghị (đã làm tròn)")], D("92600"))
		self.assertEqual(
			[str(x) for x in a.annex_rows_iii(a_svc)[4:9]],
			["121152.60", "49550.00", "75000.00", "4900.00", "37142.86"],
		)

	def test_phu_luc_iv_phan_bo_khop_golden(self):
		svcs, res = services()
		rows = a.annex_rows_iv(svcs[0])
		alloc = [r for r in rows if r[2] == "Phân bổ"]
		self.assertEqual(
			{r[1]: r[7] for r in alloc},
			{k: v for k, v in res["DV-TEST-A"]["alloc"].items()},
		)
		self.assertEqual(len(alloc), 5)
		self.assertEqual(rows[1][7], res["DV-TEST-A"]["direct"])
		self.assertEqual(rows[-1][7], D("287745.46"))
