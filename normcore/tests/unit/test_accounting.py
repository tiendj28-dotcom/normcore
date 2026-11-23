"""FEAT-016 — hàm thuần số liệu kế toán (FR-ACCT-003..006, ADR-013). Không cần site."""

import unittest
from decimal import Decimal as D

from normcore.costing import accounting as a

MAP = dict(a.DEFAULT_ACCOUNT_MAPPING)


def line(code="61111", cc="K01", amount=100, cat="LABOR", excl=0, reason="", by=None, name="x"):
	return {
		"account_code": code,
		"account_name": "",
		"cost_center": cc,
		"amount": amount,
		"cost_category": cat,
		"is_excluded": excl,
		"change_reason": reason,
		"changed_by": by,
	}


class TestMapping(unittest.TestCase):
	def test_normalize(self):
		self.assertEqual(a.normalize_account(61111.0), "61111")
		self.assertEqual(a.normalize_account("61111.0"), "61111")
		self.assertEqual(a.normalize_account(" 611 .11 "), "61111")
		self.assertEqual(a.normalize_account("abc1"), "ABC1")
		self.assertEqual(a.normalize_account(None), "")

	def test_tien_to_dai_nhat(self):
		self.assertEqual(a.match_category("611122", MAP), "UTILITY")
		self.assertEqual(a.match_category("61112", MAP), "DRUG_SUPPLY")
		self.assertEqual(a.match_category("6111229", MAP), "UTILITY")
		self.assertEqual(a.match_category("642001", MAP), "MANAGEMENT")

	def test_khong_khop(self):
		self.assertIsNone(a.match_category("99999", MAP))
		self.assertIsNone(a.match_category("", MAP))
		self.assertIsNone(a.match_category("61111", {}))

	def test_bang_mac_dinh_13_dong_khong_trung(self):
		prefixes = [p for p, _ in a.DEFAULT_ACCOUNT_MAPPING]
		self.assertEqual(len(prefixes), 13)
		self.assertEqual(len(set(prefixes)), 13)
		for _, cat in a.DEFAULT_ACCOUNT_MAPPING:
			self.assertIn(cat, a.COST_CATEGORIES)

	def test_assign_categories(self):
		ls = [line("61111", cat=None), line("811", cat=None), line("99999", cat=None)]
		self.assertEqual(a.assign_categories(ls, MAP), 2)
		self.assertEqual([x["cost_category"] for x in ls], ["LABOR", "EXCLUDED", None])
		self.assertEqual([x["is_excluded"] for x in ls], [0, 1, 0])
		self.assertEqual(a.assign_categories(ls, MAP), 0)

	def test_assign_keep_manual(self):
		ls = [line("61111", cat="MANAGEMENT", by="u@x"), line("61111", cat=None)]
		self.assertEqual(a.assign_categories(ls, MAP, keep_manual=True), 1)
		self.assertEqual([x["cost_category"] for x in ls], ["MANAGEMENT", "LABOR"])
		a.assign_categories(ls, MAP)
		self.assertEqual(ls[0]["cost_category"], "LABOR")


class TestChanges(unittest.TestCase):
	def test_khong_doi(self):
		self.assertEqual(a.check_line_changes([line()], [line()]), [])

	def test_them_bot_dong(self):
		self.assertTrue(a.check_line_changes([line()], [line(), line()]))

	def test_doi_truong_nguon(self):
		for k, v in (("amount", 5), ("account_code", "1"), ("cost_center", "K02"), ("account_name", "z")):
			b, af = line(), line()
			af[k] = v
			errs = a.check_line_changes([b], [af])
			self.assertEqual(len(errs), 1, k)
			self.assertIn("đọc lại tệp", errs[0])

	def test_amount_so_sanh_decimal(self):
		self.assertEqual(a.check_line_changes([line(amount=100)], [line(amount="100.0")]), [])

	def test_TC_ACCT_04_doi_loai_khong_ly_do(self):
		errs = a.check_line_changes([line()], [line(cat="MANAGEMENT")])
		self.assertEqual(len(errs), 1)
		self.assertIn("lý do", errs[0])
		self.assertIn("Dòng 1", errs[0])

	def test_doi_loai_co_ly_do(self):
		self.assertEqual(a.check_line_changes([line()], [line(cat="MANAGEMENT", reason="Sai tài khoản")]), [])

	def test_ly_do_khong_doi_so_voi_truoc(self):
		b = line(reason="cũ")
		self.assertTrue(a.check_line_changes([b], [line(cat="MANAGEMENT", reason="cũ")]))

	def test_loai_tru_can_ly_do(self):
		self.assertTrue(a.check_line_changes([line()], [line(excl=1)]))
		self.assertEqual(a.check_line_changes([line()], [line(excl=1, reason="không tính")]), [])

	def test_chon_excluded_tu_dat_loai_tru(self):
		self.assertEqual(
			a.check_line_changes([line()], [line(cat="EXCLUDED", excl=0, reason="r")]), []
		)

	def test_bo_loai_tru_khi_van_excluded(self):
		b = line("811", cat="EXCLUDED", excl=1)
		errs = a.check_line_changes([b], [line("811", cat="EXCLUDED", excl=0, reason="r")])
		self.assertEqual(len(errs), 1)
		self.assertIn("loại chi phí khác", errs[0])


class TestFinalize(unittest.TestCase):
	def test_chot_duoc(self):
		self.assertEqual(a.finalize_blockers("Nháp", 0, [line()]), [])

	def test_da_chot(self):
		self.assertTrue(a.finalize_blockers("Đã chốt", 0, [line()]))

	def test_dong_loi_va_khong_dong(self):
		self.assertIn("còn 2 dòng lỗi khi đọc tệp", a.finalize_blockers("Nháp", 2, [line()])[0])
		self.assertEqual(a.finalize_blockers("Nháp", 0, []), ["không có dòng nào"])

	def test_TC_ACCT_03_dong_chua_gan(self):
		ls = [line(), line("99999", cat=None, amount=7)]
		out = a.finalize_blockers("Nháp", 0, ls)
		self.assertEqual(len(out), 1)
		self.assertIn("dòng 2", out[0])
		self.assertIn("99999", out[0])
		self.assertIn("K01", out[0])
		self.assertEqual([u["idx"] for u in a.unassigned(ls)], [2])

	def test_dong_loai_tru_khong_chan(self):
		self.assertEqual(a.unassigned([line("811", cat=None, excl=1)]), [])


class TestTotals(unittest.TestCase):
	def test_totals_bo_loai_tru_va_sap_xep(self):
		ls = [
			line("1", "K01", 5, "MANAGEMENT"),
			line("2", "K01", 3, "LABOR"),
			line("3", "K01", 2, "LABOR"),
			line("4", "HC", 9, "LABOR"),
			line("5", "K01", 100, "EXCLUDED", 1),
			line("6", "K01", 1, None),
		]
		self.assertEqual(
			a.totals(ls),
			[("HC", "LABOR", D(9)), ("K01", "LABOR", D(5)), ("K01", "MANAGEMENT", D(5))],
		)

	def test_total_amount_gom_dong_loai_tru(self):
		ls = [line(amount=1.5), line(amount="2.25", cat="EXCLUDED", excl=1), line(amount=None)]
		self.assertEqual(a.total_amount(ls), D("3.75"))
