"""FEAT-028 T01: thống kê so sánh giá (không import frappe). BR-ADJ-008, FR-ADJ-001..004, 010."""

import unittest
from datetime import date
from decimal import Decimal

from normcore.benchmark import stats

D = Decimal


def _row(facility, price, eff, name=None, **kw):
	return {"name": name or f"{facility}-{eff}", "facility": facility, "price": price, "effective_date": eff, **kw}


class TestBenchmarkStats(unittest.TestCase):
	def test_window_start(self):
		assert stats.window_start(date(2026, 12, 31), 24) == date(2024, 12, 31)
		assert stats.window_start("2026-02-28", 12) == date(2025, 2, 28)
		# cuối tháng kẹp về ngày cuối tháng (29/02/2028 trừ 12 tháng)
		assert stats.window_start(date(2028, 2, 29), 12) == date(2027, 2, 28)

	def test_TC_ADJ_01_chon_gia_trong_24_thang(self):
		rows = [
			_row("P", 100, "2025-01-01"),
			_row("P", 120, "2026-06-01"),
			_row("Q", 90, "2024-10-01"),
		]
		sel, excluded = stats.select_prices(rows, date(2026, 12, 31), 24, with_excluded=True)
		assert [(r["facility"], r["effective_date"]) for r in sel] == [("P", "2026-06-01")]
		reasons = {(e["facility"], str(e["effective_date"])): e["reason"] for e in excluded}
		assert reasons[("Q", "2024-10-01")] == stats.REASON_OUTSIDE_WINDOW
		assert reasons[("P", "2025-01-01")] == stats.REASON_SUPERSEDED

	def test_select_prices_sau_ngay_tinh_va_hoa_ngay(self):
		rows = [
			_row("P", 100, "2027-01-01"),
			_row("R", 50, "2026-01-01", name="R2"),
			_row("R", 60, "2026-01-01", name="R1"),
		]
		sel, excluded = stats.select_prices(rows, "2026-12-31", 24, with_excluded=True)
		assert [r["name"] for r in sel] == ["R1"]
		assert {e["reason"] for e in excluded} == {stats.REASON_AFTER_DATE, stats.REASON_SUPERSEDED}
		# không yêu cầu excluded: chỉ trả danh sách, sắp theo giá tăng
		rows2 = [_row("A", 30, "2026-01-01"), _row("B", 10, "2026-01-01")]
		assert [r["facility"] for r in stats.select_prices(rows2, "2026-12-31", 24)] == ["B", "A"]

	def test_median(self):
		assert stats.median([D(3), D(1), D(2)]) == D(2)
		assert stats.median([D(1), D(2), D(3), D(4)]) == D("2.5")
		with self.assertRaises(ValueError):
			stats.median([])

	def test_TC_ADJ_02_trung_vi_va_do_lech(self):
		rows = [{"price": p} for p in (250000, 280000, 300000)]
		s = stats.summarize("302132.73", rows, 3)
		assert s["sufficient"] and s["count"] == 3
		assert (s["min"], s["median"], s["max"]) == (D(250000), D(280000), D(300000))
		assert s["deviation_pct"] == D("7.90")
		s4 = stats.summarize(D("302132.73"), rows + [{"price": 320000}], 3)
		assert s4["median"] == D(290000) and s4["deviation_pct"] == D("4.18")

	def test_FR_ADJ_003_duoi_nguong_chua_du_du_lieu(self):
		s = stats.summarize(300000, [{"price": 250000}, {"price": 280000}], 3)
		assert not s["sufficient"] and s["label"] == stats.LABEL_INSUFFICIENT
		assert s["median"] is None and s["deviation_pct"] is None and s["count"] == 2
		assert not stats.exceeds(s["deviation_pct"], 10)

	def test_deviation_median_zero(self):
		assert stats.deviation_pct(100, 0) is None

	def test_exceeds_bang_nguong_khong_vuot(self):
		assert stats.exceeds(D("10"), 10) is False
		assert stats.exceeds(D("10.01"), 10) is True
		assert stats.exceeds(D("-12"), 10) is True

	def test_use_adjusted(self):
		rows = [
			{"price": 100, "adjusted": {"adjusted_price": D("110")}},
			{"price": 200, "adjusted": {"adjusted_price": None}},
			{"price": 300, "adjusted": {"adjusted_price": D("330")}},
		]
		s = stats.summarize(220, rows, 3, use_adjusted=True)
		assert s["median"] == D(200) and s["adjusted_missing"] == 1
		assert (s["min"], s["max"]) == (D(110), D(330))

	def test_FR_ADJ_004_loc_don_vi(self):
		rows = [
			{"province": "HN", "facility_level": "I", "ownership": "Công", "price": 1},
			{"province": "HN", "facility_level": "II", "ownership": "Tư", "price": 2},
			{"province": "HCM", "facility_level": "I", "ownership": "Công", "price": 3},
		]
		assert len(stats.filter_rows(rows)) == 3
		assert [r["price"] for r in stats.filter_rows(rows, provinces=["HN"])] == [1, 2]
		assert [r["price"] for r in stats.filter_rows(rows, provinces=["HN", "HCM"], levels=["I"])] == [1, 3]
		assert [r["price"] for r in stats.filter_rows(rows, ownerships=["Tư"], levels=["I"])] == []

	def test_FR_ADJ_010_co_cau_tong_bang_gia_thanh(self):
		sc = {
			"direct_labor": 100,
			"direct_drug": 50,
			"direct_supply": 0,
			"direct_equipment": 25,
			"alloc_labor": 25,
			"eqa_cost": None,
			"full_cost": 200,
		}
		b = stats.breakdown(sc)
		fields = [r["field"] for r in b["rows"]]
		assert "eqa_cost" not in fields and "direct_labor" in fields
		assert b["total"] == D(200) == b["full_cost"]
		lab = next(r for r in b["rows"] if r["field"] == "direct_labor")
		assert lab["share_pct"] == D("50.00") and lab["group"] == "Trực tiếp"
		sc["eqa_cost"] = 0
		assert "eqa_cost" not in [r["field"] for r in stats.breakdown(sc)["rows"]]
		sc["eqa_cost"] = 5
		assert "eqa_cost" in [r["field"] for r in stats.breakdown(sc)["rows"]]
		assert stats.breakdown({"full_cost": 0})["rows"][0]["share_pct"] is None
