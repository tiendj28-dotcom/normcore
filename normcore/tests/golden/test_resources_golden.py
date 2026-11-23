"""Golden BR-COST-004/005, BR-CLS-009/010: so costing/resources.py với docs/golden/*.py."""

import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "docs" / "golden"))
import golden_cls as c
import golden_engine as g

from normcore.costing import resources as r

MODES = {"MUA": r.BUY, "THUE": r.RENT, "DAT": r.VENDOR, "LDLK": r.JOINT}


def _machine(e, on, expired_mode, include_depr=True):
	return r.machine_annual(
		MODES[e["mode"]],
		e.get("cost"),
		e.get("life"),
		e.get("in_service"),
		e.get("contract"),
		on,
		expired_mode,
		include_depr,
	)


class TestResourcesGolden(unittest.TestCase):
	def test_TC_RES_03_golden_eq1_don_gia_gio_may(self):
		e = g.EQUIP["EQ1"]
		for include in (True, False):
			depr, rate = g.equip_rate("EQ1", include)
			m = r.machine_annual(
				r.BUY, e["cost"], e["life"], e["in_service"], None, g.COSTING_DATE, r.ZERO, include
			)
			self.assertEqual(m, depr)
			a = r.equipment_annual(m, e["maint"], e["calib"])
			self.assertEqual(r.machine_hourly_rate(a, e["hours"], e["util"]), rate)

	def test_TC_RES_04_golden_het_thoi_gian_su_dung(self):
		e = dict(g.EQUIP["EQ1"], in_service=date(2015, 1, 1))
		g.EQUIP["V2"] = e
		try:
			depr, rate = g.equip_rate("V2")
		finally:
			del g.EQUIP["V2"]
		m = r.machine_annual(r.BUY, e["cost"], e["life"], e["in_service"], None, g.COSTING_DATE, r.ZERO)
		self.assertEqual(m, depr)
		a = r.equipment_annual(m, e["maint"], e["calib"])
		self.assertEqual(r.machine_hourly_rate(a, e["hours"], e["util"]), rate)

	def test_TC_RES_10_golden_phong(self):
		for code, room in g.ROOM.items():
			self.assertEqual(r.room_hourly_rate(room["annual"], room["hours"]), g.room_rate(code))

	def test_BR_CLS_009_khop_golden_cls(self):
		late = date(2040, 1, 1)
		for code, e in c.EQUIP.items():
			for on, mode in ((c.COSTING_DATE, "ZERO"), (late, "ZERO"), (late, "CONTINUE")):
				for include in (True, False):
					with self.subTest(code=code, on=on, mode=mode, include=include):
						m = _machine(e, on, mode, include)
						self.assertEqual(m, c.machine_annual(code, include, on, mode))
						comps = [
							(
								p["cost"],
								{"MONTH": r.LIFE_MONTH}.get(p["basis"], p["basis"]),
								p["life"],
								p["vendor"],
							)
							for p in e["parts"]
						]
						calib = c._own_compliance(e)
						got = r.equipment_annual(
							m, e["maint"], calib, comps, MODES[e["mode"]], e["maint_vendor"], e["dept_share"]
						)
						self.assertEqual(
							got,
							c.equipment_annual(
								code, "DIRECT", include_depr=include, on=on, expired_mode=mode
							),
						)
