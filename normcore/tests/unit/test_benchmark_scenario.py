"""Unit test FEAT-029 T01: benchmark/scenario.py (FR-ADJ-006, FR-ADJ-009)."""

import json
import sys
import unittest
from decimal import Decimal as D
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "docs" / "golden"))
import golden_engine as g

from normcore.benchmark import scenario as sc
from normcore.costing import snapshot
from normcore.tests.golden import test_allocation_golden as ta
from normcore.tests.golden import test_costing_golden as tg


def _golden_snap(util="0.4"):
	"""Ảnh chụp vàng; EQ1 đặt hệ số sử dụng `util` (golden dùng 0,5)."""
	eq = dict(g.EQUIP["EQ1"], util=D(util))
	with mock.patch.dict(g.EQUIP, {"EQ1": eq}):
		alloc = {
			"input": ta._inputs(True),
			"dept_center": {"K01": "K01"},
			"tolerance": repr(float(g.PARAM["recon_tolerance"])),
		}
		inputs = [tg._input(s, True) for s in g.NORMS]
		snap = snapshot.build(inputs, tg._params(True), allocation=alloc, meta={"run": "CR"})
	return json.loads(snapshot.dumps(snap))


def _eq1_facts():
	e = g.EQUIP["EQ1"]
	depr, _ = g.equip_rate("EQ1")
	return {"EQ1": {"annual_cost": depr + e["maint"] + e["calib"], "planned_hours": e["hours"]}}


def _price(rec, svc="DV-TEST-A"):
	return {r.service: r for r in rec.results}[svc].price.calculated_price


def _eq_change(new="0.5"):
	return sc.Change(sc.EQUIPMENT, "EQ1", "utilization_rate", D(new), D("0.4"))


class TestScenario(unittest.TestCase):
	def test_TC_ADJ_05_apply_thiet_bi_ve_golden(self):
		snap = _golden_snap("0.4")
		before = json.dumps(snap, sort_keys=True)
		base = snapshot.recompute(snap)
		self.assertNotEqual(_price(base), D("302132.73"))
		rec = sc.recompute(snap, [_eq_change()], _eq1_facts())
		self.assertEqual(_price(rec), D("302132.73"))
		g_res, _, _ = g.run()
		self.assertEqual(_price(rec), g_res["DV-TEST-A"]["calc"])
		self.assertEqual(json.dumps(snap, sort_keys=True), before)  # không sửa ảnh chụp vào
		self.assertEqual(_price(snapshot.recompute(snap)), _price(base))

	def test_FR_ADJ_006_parse_value(self):
		for text, want in (("0,5", "0.5"), ("15 phút", "15"), ("5%", "5"), ("0.5", "0.5"), (" 4,25% ", "4.25")):
			self.assertEqual(sc.parse_value(text), D(want), text)
		for bad in ("", None, "abc", "NaN"):
			with self.assertRaises(sc.InvalidChange):
				sc.parse_value(bad)

	def test_FR_ADJ_006_change_for_moi_quy_tac(self):
		c = sc.change_for("BR-ADJ-001", "EQ1", "0,4", "0,5", None, None)
		self.assertEqual((c.change_type, c.field, c.new_value, c.old_value), (sc.EQUIPMENT, "utilization_rate", D("0.5"), D("0.4")))
		c = sc.change_for("BR-ADJ-002", "L04", "20 phút", "15 phút", "DV-TEST-A", "K01")
		self.assertEqual((c.change_type, c.field, c.new_value, c.service, c.department), (sc.NORM_LINE, "hospital_qty", D(15), "DV-TEST-A", "K01"))
		c = sc.change_for("BR-ADJ-004", "L05", "10%", "5%", "DV-TEST-A", "K01")
		self.assertEqual((c.field, c.new_value, c.old_value), ("wastage_rate", D(5), D(10)))
		c = sc.change_for("BR-ADJ-005", "PS1", "5%", "4%", None, None)
		self.assertEqual((c.change_type, c.field, c.new_value), (sc.PARAM, "accumulation_rate", D(4)))
		self.assertIs(sc.change_for("BR-ADJ-003", "L05", "A", "B", "S", "D"), sc.PROCEDURE)
		self.assertIsNone(sc.change_for("BR-ADJ-006", "X", "Chưa có", "Bổ sung", "S", "D"))
		self.assertIsNone(sc.change_for("BR-ADJ-007", "X", "cũ", "mới", "S", "D"))
		with self.assertRaises(sc.InvalidChange):
			sc.change_for("BR-ADJ-999", "X", "1", "2", "S", "D")

	def test_FR_ADJ_006_merge_ghi_de_giu_gia_tri_cu(self):
		a = _eq_change("0.5")
		b = sc.Change(sc.PARAM, "PS1", "accumulation_rate", D(4), D(5))
		out = sc.merge([a], b)
		self.assertEqual(out, [a, b])
		again = sc.merge(out, sc.Change(sc.EQUIPMENT, "EQ1", "utilization_rate", D("0.6"), D("0.5")))
		self.assertEqual(len(again), 2)
		self.assertEqual((again[0].new_value, again[0].old_value), (D("0.6"), D("0.4")))

	def test_FR_ADJ_006_apply_tham_so(self):
		snap = _golden_snap("0.5")
		new = sc.apply(snap, [sc.Change(sc.PARAM, "PS1", "accumulation_rate", D(4), D(5))], {})
		self.assertEqual(snapshot.from_plain(new["params"]).accumulation_rate, D("0.04"))
		self.assertNotEqual(snapshot.from_plain(snap["params"]).accumulation_rate, D("0.04"))
		self.assertLess(_price(snapshot.recompute(new)), _price(snapshot.recompute(snap)))

	def test_FR_ADJ_006_apply_dong_dinh_muc(self):
		snap = _golden_snap("0.5")
		line = next(x for x in g.NORMS["DV-TEST-A"] if x.comp == "LABOR")
		base = _price(snapshot.recompute(snap))
		ch = sc.Change(sc.NORM_LINE, line.line_id, "hospital_qty", D(1), None, "DV-TEST-A", "K01")
		new = sc.apply(snap, [ch], {})
		self.assertLess(_price(snapshot.recompute(new)), base)
		ch = sc.Change(sc.NORM_LINE, "L05", "wastage_rate", D(5), None, "DV-TEST-A", "K01")
		inp = next(
			snapshot.from_plain(i)
			for i in sc.apply(snap, [ch], {})["inputs"]
			if i["service"] == "DV-TEST-A"
		)
		self.assertEqual(next(x for x in inp.lines if x.line_id == "L05").wastage_rate, D("0.05"))

	def test_FR_ADJ_006_khong_sua_anh_chup_vao(self):
		snap = _golden_snap("0.4")
		before = json.dumps(snap, sort_keys=True)
		sc.apply(snap, [_eq_change(), sc.Change(sc.PARAM, "PS1", "accumulation_rate", D(4), None)], _eq1_facts())
		self.assertEqual(json.dumps(snap, sort_keys=True), before)

	def test_FR_ADJ_006_loi_thay_doi(self):
		snap = _golden_snap("0.4")
		with self.assertRaises(sc.InvalidChange):
			sc.apply(snap, [_eq_change()], {})  # thiếu chi phí năm thiết bị
		with self.assertRaises(sc.InvalidChange):
			sc.apply(snap, [sc.Change(sc.NORM_LINE, "L99", "hospital_qty", D(1), None, "DV-TEST-A", "K01")], {})
		with self.assertRaises(sc.InvalidChange):
			sc.apply(snap, [sc.Change(sc.NORM_LINE, "L01", "hospital_qty", D(1), None, "DV-NONE", "K01")], {})
		with self.assertRaises(sc.InvalidChange):
			sc.apply(snap, [sc.Change(sc.PARAM, "PS1", "khong_co", D(1), None)], {})
		with self.assertRaises(sc.InvalidChange):
			sc.apply(snap, [sc.Change("Lạ", "X", "y", D(1), None)], {})
		with self.assertRaises(sc.InvalidChange):
			sc.apply(snap, [sc.Change(sc.EQUIPMENT, "EQ1", "utilization_rate", D(0), None)], _eq1_facts())

	def test_FR_ADJ_006_proposal_text(self):
		t = sc.proposal_text("BR-ADJ-003", "L05", "A", "B", "Có mặt hàng tương đương")
		self.assertIn("BR-ADJ-003", t)
		self.assertIn("Hiện tại: A → Đề xuất: B", t)
		self.assertIn("Lý do:", t)
		self.assertIn("Ghi chú: ghi chú", sc.proposal_text("BR-ADJ-003", "L05", "A", "B", "x", "ghi chú"))


if __name__ == "__main__":
	unittest.main()
