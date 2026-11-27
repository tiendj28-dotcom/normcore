"""FEAT-027 T01: logic thuần trích bảng giá PDF (không import frappe). FR-BM-003, ASM-027-04..07."""

import unittest
from datetime import date
from decimal import Decimal
from unittest import mock

from normcore.benchmark import pdf_extract as px
from normcore.library.extract import Page

PAGES = [
	Page(1, "BẢNG GIÁ DỊCH VỤ\nĐịnh lượng Glucose máu 25.000\nSiêu âm ổ bụng 120.000"),
	Page(2, "Chụp X-quang ngực thẳng 90.000\nTổng cộng"),
	Page(3, "   "),
]


class TestDocGiaNgayTrang(unittest.TestCase):
	def test_FR_BM_003_doc_gia_ngay_trang(self):
		for v, want in [
			(25000, Decimal("25000")),
			(25000.5, Decimal("25000.5")),
			(Decimal("7"), Decimal("7")),
			("25.000", Decimal("25000")),
			("25,000 đ", Decimal("25000")),
			("1.250.000 VNĐ", Decimal("1250000")),
			(" 1.250.000 vnd ", Decimal("1250000")),
			("12,5", Decimal("12.5")),
			("100", Decimal("100")),
			("90000₫", Decimal("90000")),
		]:
			self.assertEqual(px.parse_price(v), want, v)
		for v in ["abc", 0, -5, True, False, None, "", "0", "-3", "1.2.3x", [1]]:
			self.assertIsNone(px.parse_price(v), v)
		self.assertEqual(px.parse_date("2026-01-15"), date(2026, 1, 15))
		self.assertEqual(px.parse_date("15/01/2026"), date(2026, 1, 15))
		self.assertEqual(px.parse_date("1/2/2026"), date(2026, 2, 1))
		self.assertEqual(px.parse_date("15-01-2026"), date(2026, 1, 15))
		self.assertEqual(px.parse_date("15.01.2026"), date(2026, 1, 15))
		self.assertEqual(px.parse_date(date(2026, 3, 4)), date(2026, 3, 4))
		for v in ["31/02/2026", "xx", "", None, 5, "2026-13-01"]:
			self.assertIsNone(px.parse_date(v), v)
		# locate
		self.assertEqual(px.locate("Siêu âm ổ bụng", PAGES), 1)
		self.assertEqual(px.locate("chup x-quang nguc thang", PAGES), 2)
		self.assertEqual(px.locate("Siêu âm ổ bụng", PAGES, hint=2), 1)
		self.assertEqual(px.locate("Siêu âm ổ bụng", PAGES, hint=1), 1)
		self.assertEqual(px.locate("Siêu âm ổ bụng", PAGES, hint="x"), 1)
		self.assertIsNone(px.locate("Nội soi", PAGES))
		self.assertIsNone(px.locate("", PAGES))
		# source_url
		self.assertEqual(px.source_url("/private/files/a.pdf", 2), "/private/files/a.pdf#page=2")
		self.assertIsNone(px.source_url("/private/files/a.pdf", None))
		self.assertIsNone(px.source_url("/p/" + "x" * 140 + ".pdf", 1))

	def test_page_sources_va_gioi_han_trang(self):
		self.assertEqual(
			px.page_sources(PAGES),
			[{"page": 1, "text": PAGES[0].text}, {"page": 2, "text": PAGES[1].text}],
		)
		self.assertEqual(px.page_sources([Page(None, "abc")]), [{"page": 1, "text": "abc"}])
		px.check_page_count(PAGES)
		with self.assertRaisesRegex(ValueError, "vượt 30 trang"):
			px.check_page_count([Page(i, "x") for i in range(31)])


class TestParseRows(unittest.TestCase):
	def _r(self, name, price, d=None, page=None):
		return {"service_name": name, "price": price, "effective_date": d, "page": page}

	def test_FR_BM_003_parse_rows(self):
		data = {
			"rows": [
				self._r("Định lượng Glucose máu", "25.000", "2026-01-15", 1),
				self._r("Siêu âm ổ bụng", 120000, None, 2),  # dùng ngày mặc định; trang sai -> tìm lại
				self._r("", 1000, "2026-01-15"),
				self._r("Chụp X-quang ngực thẳng", "abc", "2026-01-15"),
				self._r("Nội soi dạ dày", 500000, "2026-01-15"),
				"khong phai dict",
			]
		}
		rows, skipped = px.parse_rows(data, PAGES, default_date=date(2026, 2, 1))
		self.assertEqual([r["service_name_raw"] for r in rows], ["Định lượng Glucose máu", "Siêu âm ổ bụng"])
		self.assertEqual(rows[0]["price"], Decimal("25000"))
		self.assertEqual(rows[0]["effective_date"], date(2026, 1, 15))
		self.assertEqual(rows[1]["effective_date"], date(2026, 2, 1))
		self.assertEqual(rows[1]["page"], 1)
		self.assertEqual(
			[s["reason"] for s in skipped],
			[px.SKIP_NO_NAME, px.SKIP_BAD_PRICE, px.SKIP_NOT_IN_FILE, px.SKIP_NO_NAME],
		)
		s = px.summary(2, [{"service_name": "x", "message": "m"}], skipped)
		self.assertEqual(s["created"], 2)
		self.assertEqual(s["not_in_file"], 1)
		self.assertEqual(len(s["duplicates"]), 1)

	def test_khong_co_ngay(self):
		rows, skipped = px.parse_rows({"rows": [self._r("Siêu âm ổ bụng", 1, None)]}, PAGES)
		self.assertEqual(rows, [])
		self.assertEqual(skipped[0]["reason"], px.SKIP_NO_DATE)

	def test_tat_kiem_ten_trong_tep(self):
		with mock.patch.object(px, "REQUIRE_NAME_IN_SOURCE", False):
			rows, skipped = px.parse_rows({"rows": [self._r("Nội soi", 1, "2026-01-01")]}, PAGES)
		self.assertEqual(len(rows), 1)
		self.assertIsNone(rows[0]["page"])
		self.assertEqual(skipped, [])

	def test_cat_ten_140(self):
		long = "Siêu âm ổ bụng " + "x" * 200
		with mock.patch.object(px, "REQUIRE_NAME_IN_SOURCE", False):
			rows, _ = px.parse_rows({"rows": [self._r(long, 1, "2026-01-01")]}, PAGES)
		self.assertEqual(len(rows[0]["service_name_raw"]), 140)

	def test_cau_truc_sai(self):
		for bad in [None, [], {"rows": "x"}, {"x": 1}]:
			with self.assertRaisesRegex(ValueError, "thiếu danh sách rows"):
				px.parse_rows(bad, PAGES)


if __name__ == "__main__":
	unittest.main()
