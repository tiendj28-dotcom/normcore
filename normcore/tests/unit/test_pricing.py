"""FEAT-009: chọn đơn giá, cảnh báo, quy đổi đơn vị định mức, dòng vật chất (hàm thuần, không site)."""

import unittest
from datetime import date
from decimal import Decimal as D

from normcore.costing.pricing import (
	SOURCE_ORDER,
	STALE_WARNING,
	UNVERIFIED_WARNING,
	NoEffectivePrice,
	PriceRecord,
	material_line,
	price_warnings,
	select_price,
	unit_price_per_norm,
)


def P(name, source="Báo giá", valid_from=date(2026, 1, 1), valid_to=None, price="1000", doc=None, ok=True):
	return PriceRecord(
		name=name,
		unit_price=D(price),
		price_source=source,
		document_date=doc or valid_from,
		valid_from=valid_from,
		valid_to=valid_to,
		verified=ok,
	)


class TestSelectPrice(unittest.TestCase):
	def test_TC_RES_01_cung_nguon_lay_ngay_hieu_luc_gan_nhat(self):
		prices = [
			P("a", valid_from=date(2026, 1, 1)),
			P("b", valid_from=date(2026, 6, 1)),
			P("c", valid_from=date(2027, 1, 1)),
		]
		self.assertEqual(select_price(prices, date(2026, 12, 31)).name, "b")

	def test_TC_CLS_45_nguon_truoc_ngay_hieu_luc_sau(self):
		prices = [
			P("thau", "Trúng thầu", date(2025, 1, 1)),
			P("bg", "Báo giá", date(2026, 6, 1)),
		]
		self.assertEqual(select_price(prices, date(2026, 12, 31)).name, "thau")

	def test_TC_CLS_45_gia_trung_thau_het_hieu_luc_thi_lay_bao_gia(self):
		prices = [
			P("thau", "Trúng thầu", date(2025, 1, 1), valid_to=date(2026, 6, 30)),
			P("bg", "Báo giá", date(2026, 6, 1)),
		]
		self.assertEqual(select_price(prices, date(2026, 12, 31)).name, "bg")

	def test_FR_RES_004_thu_tu_nguon(self):
		self.assertEqual(SOURCE_ORDER, ("Trúng thầu", "Hợp đồng", "Hóa đơn", "Giá công bố", "Báo giá"))
		day = date(2026, 3, 1)
		for i, src in enumerate(SOURCE_ORDER):
			rest = [P(s, s, day) for s in SOURCE_ORDER[i:]]
			self.assertEqual(select_price(list(reversed(rest)), day).name, src)

	def test_FR_RES_004_bien_hieu_luc_gom_ca_hai_dau(self):
		p = P("a", valid_from=date(2026, 1, 1), valid_to=date(2026, 6, 30))
		self.assertEqual(select_price([p], date(2026, 1, 1)).name, "a")
		self.assertEqual(select_price([p], date(2026, 6, 30)).name, "a")
		self.assertIsNone(select_price([p], date(2025, 12, 31)))
		self.assertIsNone(select_price([p], date(2026, 7, 1)))

	def test_FR_RES_004_khong_co_gia_thi_none(self):
		self.assertIsNone(select_price([], date(2026, 1, 1)))

	def test_FR_RES_004_trung_het_thi_ngay_chung_tu_roi_ten(self):
		a = P("a", valid_from=date(2026, 1, 1), doc=date(2025, 12, 1))
		b = P("b", valid_from=date(2026, 1, 1), doc=date(2025, 12, 20))
		self.assertEqual(select_price([a, b], date(2026, 2, 1)).name, "b")  # ASM-063
		c = P("c", valid_from=date(2026, 1, 1), doc=date(2025, 12, 20))
		self.assertEqual(select_price([b, c], date(2026, 2, 1)).name, "c")

	def test_FR_RES_004_nguon_la_bi_tu_choi(self):
		with self.assertRaises(ValueError):
			select_price([P("a", "Nguồn lạ")], date(2026, 1, 1))


class TestWarnings(unittest.TestCase):
	def test_TC_RES_02_chung_tu_cu_25_thang(self):
		p = P("a", doc=date(2023, 11, 30))
		self.assertIn(STALE_WARNING, price_warnings(p, date(2025, 12, 31)))
		self.assertEqual(STALE_WARNING, "Đơn giá quá hạn tham chiếu")

	def test_FR_RES_003_dung_24_thang_khong_canh_bao(self):
		self.assertNotIn(STALE_WARNING, price_warnings(P("a", doc=date(2024, 12, 31)), date(2026, 12, 31)))
		self.assertIn(STALE_WARNING, price_warnings(P("a", doc=date(2024, 12, 30)), date(2026, 12, 31)))

	def test_FR_RES_003_cuoi_thang_29_2(self):
		# 29/02/2028 trừ 24 tháng = 29/02/2026 không có -> 28/02/2026
		self.assertNotIn(STALE_WARNING, price_warnings(P("a", doc=date(2026, 2, 28)), date(2028, 2, 29)))
		self.assertIn(STALE_WARNING, price_warnings(P("a", doc=date(2026, 2, 27)), date(2028, 2, 29)))

	def test_FR_RES_017_chua_xac_minh(self):
		w = price_warnings(P("a", doc=date(2026, 6, 1), ok=False), date(2026, 12, 31))
		self.assertEqual(w, (UNVERIFIED_WARNING,))
		self.assertEqual(UNVERIFIED_WARNING, "Đơn giá chưa xác minh")
		self.assertEqual(price_warnings(P("a", doc=date(2026, 6, 1)), date(2026, 12, 31)), ())


class TestUnitPrice(unittest.TestCase):
	def test_TC_CLS_47_hoa_chat_hop_200_test(self):
		r = unit_price_per_norm(D("6000000"), D("200"))
		self.assertEqual(r, D("30000.0000"))
		self.assertEqual(str(r), "30000.0000")

	def test_BR_CLS_002_lam_tron_4_so_le_half_up(self):
		self.assertEqual(unit_price_per_norm(D("100"), D("3")), D("33.3333"))
		self.assertEqual(unit_price_per_norm(D("1"), D("16")), D("0.0625"))
		self.assertEqual(unit_price_per_norm(D("0.00005"), D("1")), D("0.0001"))

	def test_BR_CLS_002_so_don_vi_phai_duong(self):
		for bad in (D("0"), D("-1")):
			with self.assertRaises(ValueError):
				unit_price_per_norm(D("10"), bad)


class TestMaterialLine(unittest.TestCase):
	DAY = date(2026, 12, 31)

	def test_BR_COST_003_cong_thuc(self):
		r = material_line(D("1"), D("0.05"), 1, [P("a", price="25000")], self.DAY)
		self.assertEqual(r.amount, D("26250.00"))
		self.assertEqual(r.unit_price, D("25000"))
		self.assertEqual(r.price_name, "a")
		self.assertIsNone(r.excluded_reason)

	def test_BR_COST_003_chia_so_lan_dung(self):
		r = material_line(D("1"), D("0"), 200, [P("a", price="2000000")], self.DAY)
		self.assertEqual(r.amount, D("10000.00"))

	def test_TC_RES_07_thanh_toan_rieng_bang_0_co_ly_do(self):
		r = material_line(D("1"), D("0"), 1, [P("a", price="80000")], self.DAY, billed_separately=True)
		self.assertEqual(r.amount, D("0"))
		self.assertEqual(r.excluded_reason, "Thanh toán riêng ngoài giá dịch vụ")
		self.assertEqual(r.warnings, ())

	def test_TC_RES_07_thanh_toan_rieng_khong_can_don_gia(self):
		r = material_line(D("1"), D("0"), 1, [], self.DAY, billed_separately=True)
		self.assertEqual(r.amount, D("0"))

	def test_TC_RES_02_qua_han_van_tinh(self):
		p = P("a", price="3000", valid_from=date(2023, 12, 1), doc=date(2023, 11, 30))
		r = material_line(D("2"), D("0"), 1, [p], date(2025, 12, 31))
		self.assertEqual(r.amount, D("6000.00"))
		self.assertIn(STALE_WARNING, r.warnings)

	def test_TC_CLS_46_chua_xac_minh_van_tinh_co_canh_bao(self):
		r = material_line(D("2"), D("0"), 1, [P("a", price="3000", ok=False)], self.DAY)
		self.assertEqual(r.amount, D("6000.00"))
		self.assertEqual(r.warnings, (UNVERIFIED_WARNING,))

	def test_FR_RES_004_khong_co_don_gia_hieu_luc_bao_loi_khong_bia_so(self):
		with self.assertRaises(NoEffectivePrice):
			material_line(D("1"), D("0"), 1, [P("a", valid_from=date(2027, 1, 1))], self.DAY)

	def test_BR_COST_003_dau_vao_sai(self):
		for args in ((D("-1"), D("0"), 1), (D("1"), D("-0.1"), 1), (D("1"), D("0"), 0)):
			with self.assertRaises(ValueError):
				material_line(*args, [P("a")], self.DAY)
