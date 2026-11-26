"""Unit test FEAT-036 T03: costing/snapshot.py."""

import json
import unittest
from datetime import date
from decimal import Decimal as D

from normcore.costing import cls, engine, snapshot
from normcore.tests.golden import cls_fixture as f


class TestSnapshot(unittest.TestCase):
	def test_khu_hoi_moi_dataclass(self):
		svc = f.service()
		plain = snapshot.to_plain(svc)
		again = snapshot.from_plain(json.loads(json.dumps(plain)))
		self.assertEqual(again, svc)
		self.assertEqual(snapshot.from_plain(snapshot.to_plain(f.PARAMS)), f.PARAMS)
		self.assertEqual(snapshot.from_plain(snapshot.to_plain([date(2026, 1, 2), None, True, 3])), [date(2026, 1, 2), None, True, 3])

	def test_kieu_la_bi_tu_choi(self):
		with self.assertRaises(TypeError):
			snapshot.to_plain(object())
		with self.assertRaises(TypeError):
			snapshot.to_plain(cls.TestSystemCost("a", None, D(1), D(1), D(0), D(0), D(0), D(0), D(0), D(1), False, D(1), False))
		with self.assertRaises(ValueError):
			snapshot.from_plain({"x": 1})

	def test_digest_on_dinh(self):
		snap = snapshot.build([f.service()], f.PARAMS, {"ghi_chu": "x"})
		a, b = snapshot.dumps(snap), snapshot.dumps(json.loads(snapshot.dumps(snap)))
		self.assertEqual(a, b)
		self.assertEqual(snapshot.digest(a), snapshot.digest(b))
		self.assertEqual(len(snapshot.digest(a)), 64)

	def test_reproduce_bo_du_lieu_vang(self):
		direct = f.cost()
		snap = json.loads(snapshot.dumps(snapshot.build([f.service()], f.PARAMS)))
		out = snapshot.reproduce(snap)
		self.assertEqual(len(out), 1)
		self.assertEqual([t.k_factor for t in out[0].test_system_costs], [D("1.108247"), D("1.221649")])
		self.assertEqual(out[0].direct_total, D("42278.67"))
		self.assertEqual(out[0].lines, direct.lines)
		self.assertEqual(out[0].direct_by_category, direct.direct_by_category)

	def test_phien_ban_la(self):
		with self.assertRaises(ValueError):
			snapshot.reproduce({"version": 99})

	def test_dich_vu_thuong_van_chup_duoc(self):
		line = engine.NormLine("L1", "S", "SUPPLY", "R", "R", D("2"))
		svc = engine.ServiceInput("S", "D", "N", (line,), {"L1": engine.LineRate(D("10"), "p")}, D("5"))
		snap = snapshot.build([svc], f.PARAMS)
		out = snapshot.reproduce(json.loads(snapshot.dumps(snap)))
		self.assertEqual(out[0].direct_total, D("20.00"))


if __name__ == "__main__":
	unittest.main()
