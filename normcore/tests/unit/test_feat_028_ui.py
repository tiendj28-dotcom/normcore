"""FEAT-028: giao diện Bàn so sánh giá (ui-design.md): kiểm tĩnh mã nguồn JS/Vue, Page, bản dịch."""

import csv
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VUE = (ROOT / "public" / "js" / "price_compare" / "PriceCompare.vue").read_text(encoding="utf-8")
PAGE_DIR = ROOT / "nc_benchmark" / "page" / "price_compare"
PAGE_JS = (PAGE_DIR / "price_compare.js").read_text(encoding="utf-8")
PAGE = json.loads((PAGE_DIR / "price_compare.json").read_text(encoding="utf-8"))
ADJ = ROOT / "nc_benchmark" / "doctype" / "nc_adjustment_suggestion"
FORM = (ADJ / "nc_adjustment_suggestion.js").read_text(encoding="utf-8")
LIST = (ADJ / "nc_adjustment_suggestion_list.js").read_text(encoding="utf-8")
RUN_FORM = (ROOT / "nc_costing" / "doctype" / "nc_costing_run" / "nc_costing_run.js").read_text(encoding="utf-8")
FRAGMENT = {
	r[0]: r[1]
	for r in csv.reader((ROOT / "translations" / "vi.d" / "FEAT-028.csv").open(encoding="utf-8"))
	if len(r) > 1
}
BASE = {
	r[0]: r[1]
	for f in (ROOT / "translations" / "vi.d").glob("*.csv")
	for r in csv.reader(f.open(encoding="utf-8"))
	if len(r) > 1
}


def strings(text):
	return {m.group(1).replace('\\"', '"') for m in re.finditer(r'__\(\s*"((?:[^"\\]|\\.)*)"', text)}


class TestFeat028Ui(unittest.TestCase):
	def test_moi_chuoi_giao_dien_co_ban_dich(self):
		for text in (VUE, PAGE_JS, FORM, LIST):
			self.assertEqual([s for s in strings(text) if s not in BASE], [])
		self.assertIn("Price comparison", strings(RUN_FORM))

	def test_nhan_theo_thiet_ke(self):
		self.assertEqual(FRAGMENT["Not enough comparison data"], "Chưa đủ dữ liệu so sánh")
		self.assertEqual(FRAGMENT["Over tolerance"], "Vượt ngưỡng")
		self.assertEqual(FRAGMENT["Requires procedure change"], "Cần sửa quy trình")
		self.assertEqual(FRAGMENT["Excluded prices ({0})"], "Giá bị loại ({0})")
		self.assertEqual(FRAGMENT["Price comparison"], "So sánh giá")

	def test_page_dung_vai_tro(self):
		roles = {r["role"] for r in PAGE["roles"]}
		self.assertEqual(roles, {"NC Finance", "NC Department Head", "NC Director", "NC Admin", "NC Auditor"})
		self.assertEqual(PAGE["page_name"], "price-compare")
		self.assertEqual(PAGE["module"], "NC Benchmark")
		self.assertIn("price_compare.bundle.js", PAGE_JS)

	def test_vue_goi_dung_api_va_thao_tac(self):
		for fn in ("get_comparison", "get_service_detail", "generate_suggestions", "decide_suggestion"):
			self.assertIn(fn, VUE)
		self.assertIn('const API = "normcore.api.price_compare."', VUE)
		self.assertIn("detail.can_generate", VUE)
		self.assertIn("detail.can_decide", VUE)
		self.assertIn("reqd: 1", VUE)  # lý do từ chối bắt buộc
		self.assertIn("aria-busy", VUE)
		self.assertIn('aria-live="polite"', VUE)
		self.assertIn('scope="col"', VUE)

	def test_vue_khong_mau_tu_dat(self):
		self.assertEqual(re.findall(r"#[0-9a-fA-F]{3,8}\b", VUE), [])
		self.assertEqual(re.findall(r"\brgba?\(", VUE), [])

	def test_nut_so_sanh_gia_chi_khi_da_tinh_hoac_da_khoa(self):
		block = RUN_FORM.split('__("Price comparison")')[0].rsplit("if (", 1)[1]
		self.assertIn('"Đã tính", "Đã khóa"', block)
		self.assertIn('frappe.set_route("price-compare"', RUN_FORM)

	def test_form_goi_y_mo_ban_so_sanh(self):
		self.assertIn('frappe.set_route("price-compare"', FORM)
		for color in ('"blue"', '"green"', '"gray"', '"purple"'):
			self.assertIn(color, LIST)
