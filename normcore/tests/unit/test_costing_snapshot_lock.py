"""Unit test FEAT-018 T01: snapshot.py mở rộng (lược đồ 2, pack/unpack/recompute/diff_rows), reconcile.depreciation_centers."""

import gzip
import json
import sys
import unittest
from decimal import Decimal as D
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "docs" / "golden"))
import golden_engine as g

from normcore.costing import allocation, reconcile, snapshot
from normcore.tests.golden import test_allocation_golden as ta
from normcore.tests.golden import test_costing_golden as tg


def _snap(include_depr=True, with_alloc=True):
	inputs = [tg._input(s, include_depr) for s in g.NORMS]
	alloc = None
	if with_alloc:
		alloc = {
			"input": ta._inputs(include_depr),
			"dept_center": {"K01": "K01"},
			"tolerance": repr(float(g.PARAM["recon_tolerance"])),
		}
	meta = {"run": "CR-1", "fiscal_year": "2026", "scope_services": [], "include": include_depr}
	return snapshot.build(inputs, tg._params(include_depr), allocation=alloc, meta=meta)


def _roundtrip(snap):
	return json.loads(snapshot.dumps(snap))


class TestMapKhoaTuple(unittest.TestCase):
	def test_khu_hoi_map_khoa_tuple(self):
		data = {("K01", "LABOR"): D("1.5"), ("HC", "MANAGEMENT"): D("2")}
		plain = json.loads(json.dumps(snapshot.to_plain(data)))
		self.assertEqual(snapshot.from_plain(plain), data)

	def test_khoa_str_giu_dang_cu(self):
		plain = snapshot.to_plain({"b": 1, "a": 2})
		self.assertEqual(plain, {"__map__": [["a", 2], ["b", 1]]})

	def test_khoa_hon_hop_sap_tat_dinh(self):
		a = snapshot.dumps({"x": snapshot.to_plain({("a", "b"): 1, "z": 2})})
		b = snapshot.dumps({"x": snapshot.to_plain({"z": 2, ("a", "b"): 1})})
		self.assertEqual(a, b)

	def test_float_van_bi_tu_choi(self):
		with self.assertRaises(TypeError):
			snapshot.to_plain({"a": 1.5})


class TestBuildPackUnpack(unittest.TestCase):
	def test_build_co_allocation_va_meta(self):
		snap = _snap()
		self.assertEqual(snap["version"], 2)
		self.assertIn("allocation", snap)
		self.assertEqual(snapshot.from_plain(snap["meta"])["run"], "CR-1")
		self.assertNotIn("allocation", snapshot.build([], tg._params()))

	def test_pack_hai_lan_cung_byte_va_ma_bam(self):
		a, ha = snapshot.pack(_snap())
		b, hb = snapshot.pack(_snap())
		self.assertEqual(a, b)
		self.assertEqual(ha, hb)
		self.assertEqual(len(ha), 64)
		self.assertEqual(ha, snapshot.digest(gzip.decompress(a)))

	def test_unpack_khu_hoi_va_kiem_ma_bam(self):
		blob, h = snapshot.pack(_snap())
		self.assertEqual(snapshot.unpack(blob, h), _roundtrip(_snap()))
		self.assertEqual(snapshot.unpack(blob), _roundtrip(_snap()))

	def test_unpack_sai_ma_bam(self):
		blob, h = snapshot.pack(_snap())
		with self.assertRaisesRegex(ValueError, "mã băm không khớp"):
			snapshot.unpack(blob, "0" * 64)
		other, _ = snapshot.pack(_snap(False))
		with self.assertRaisesRegex(ValueError, "mã băm không khớp"):
			snapshot.unpack(other, h)


class TestRecompute(unittest.TestCase):
	def test_recompute_khop_golden_engine(self):
		out = snapshot.recompute(_roundtrip(_snap()))
		g_res, g_recon, _ = g.run()
		by = {r.service: r for r in out.results}
		for s in g.NORMS:
			self.assertEqual(by[s].price.full_cost, g_res[s]["full"])
		self.assertEqual(
			[
				(r.cost_category, r.costed, r.accounting, r.variance_pct, r.over_tolerance)
				for r in out.recon_rows
			],
			[(c, cost, acc, pct, over) for c, cost, acc, _rem, pct, over in g_recon if c != "MANAGEMENT"],
		)
		self.assertEqual(out.warnings, [])

	def test_recompute_V1_co_dong_bo_qua_khau_hao(self):
		out = snapshot.recompute(_roundtrip(_snap(False)))
		g_res, _, _ = g.run(False)
		by = {r.service: r for r in out.results}
		self.assertEqual(by["DV-TEST-A"].price.full_cost, g_res["DV-TEST-A"]["full"])
		self.assertEqual([r.cost_category for r in out.recon_rows if r.skipped], ["DEPRECIATION"])

	def test_recompute_danh_dau_san_luong(self):
		snap = _snap()
		for i in snap["inputs"]:
			if i["service"] == "DV-TEST-B":
				i["volume"] = {"__dec__": "0"}
		out = snapshot.recompute(_roundtrip(snap))
		b = next(r for r in out.results if r.service == "DV-TEST-B")
		self.assertIn(allocation.VOLUME_WARNING, b.message)

	def test_luoc_do_1_khong_allocation(self):
		snap = _roundtrip(_snap(with_alloc=False))
		snap["version"] = 1
		snap.pop("meta")
		out = snapshot.recompute(snap)
		self.assertEqual(out.recon_rows, [])
		self.assertEqual(len(out.results), 2)
		self.assertEqual(
			[r.direct_total for r in snapshot.reproduce(snap)], [r.direct_total for r in out.results]
		)

	def test_phien_ban_la(self):
		snap = _roundtrip(_snap())
		snap["version"] = 3
		for fn in (snapshot.recompute, snapshot.reproduce):
			with self.assertRaisesRegex(ValueError, "Phiên bản ảnh chụp không được hỗ trợ"):
				fn(snap)

	def test_dich_vu_khong_co_trung_tam_co_canh_bao(self):
		snap = _snap()
		snap["allocation"]["dept_center"] = {"__map__": []}
		snap = _roundtrip(snap)
		out = snapshot.recompute(snap)
		self.assertTrue(any("chưa có trung tâm chi phí" in w for w in out.warnings))


def _cost(**kw):
	v = {"direct_labor": 1.5, "calc_message": None, "full_cost": D("10.123456")}
	v.update(kw)
	return {"key": ("cost", "S", "D"), "values": v}


class TestDiffRows(unittest.TestCase):
	def test_trung_thi_rong(self):
		rows = [_cost(), {"key": ("recon", "K01", "LABOR"), "values": {"variance": 1.0, "over": 1}}]
		same = [
			_cost(calc_message="", full_cost=10.123456),
			{"key": ("recon", "K01", "LABOR"), "values": {"variance": 1.0, "over": True}},
		]
		self.assertEqual(snapshot.diff_rows(rows, same), [])

	def test_khac_so(self):
		out = snapshot.diff_rows([_cost()], [_cost(direct_labor=2.5)])
		self.assertEqual(len(out), 1)
		self.assertIn("S · D", out[0])
		self.assertIn("direct_labor", out[0])

	def test_sai_so_duoi_places(self):
		self.assertEqual(snapshot.diff_rows([_cost()], [_cost(direct_labor=1.5000001)]), [])
		self.assertEqual(len(snapshot.diff_rows([_cost()], [_cost(direct_labor=1.5000001)], places=8)), 1)

	def test_thieu_va_thua(self):
		line = {"key": ("line", "S", "D", 2), "values": {"amount": 6000.0}}
		recon = {"key": ("recon", "K01", "LABOR"), "values": {"variance": 1.0}}
		system = {"key": ("system", "S", "D", 1), "values": {"k_factor": 1.0}}
		out = snapshot.diff_rows([_cost(), line, recon, system], [])
		self.assertEqual(len(out), 4)
		self.assertIn("Thiếu dòng đối soát K01 · LABOR", out)
		out = snapshot.diff_rows([], [_cost(), line, recon, system])
		self.assertEqual(len(out), 4)
		self.assertTrue(all(x.startswith("Thừa") for x in out))

	def test_cau_dong_dich_vu(self):
		exp = {"key": ("line", "DV-TEST-A", "K01", 2), "values": {"amount": 6000.0}}
		act = {"key": ("line", "DV-TEST-A", "K01", 2), "values": {"amount": 10000.0}}
		self.assertEqual(
			snapshot.diff_rows([exp], [act]), ["DV-TEST-A · K01 dòng 2 · amount: 6000.0 ≠ 10000.0"]
		)

	def test_chuoi_va_truong_vang(self):
		out = snapshot.diff_rows([_cost(calc_message="a")], [_cost(calc_message="b")])
		self.assertEqual(len(out), 1)
		out = snapshot.diff_rows([_cost(extra=1)], [_cost()])
		self.assertEqual(len(out), 1)


class TestDepreciationCenters(unittest.TestCase):
	def test_trung_tam_co_so_khau_hao_trong_pools(self):
		P = allocation.Pool
		pools = [
			P("K02", "DEPRECIATION", D(0), D(0), D(0), D(0), D(0)),
			P("K01", "DEPRECIATION", D(0), D(0), D(0), D(0), D(0)),
		]
		acc = {
			("K01", "DEPRECIATION"): D(5),
			("K02", "DEPRECIATION"): D(3),
			("K03", "DEPRECIATION"): D(9),
			("K01", "LABOR"): D(1),
			("K02", "UTILITY"): D(0),
		}
		self.assertEqual(reconcile.depreciation_centers(acc, pools), ["K01", "K02"])
		acc[("K02", "DEPRECIATION")] = D(0)
		self.assertEqual(reconcile.depreciation_centers(acc, pools), ["K01"])
