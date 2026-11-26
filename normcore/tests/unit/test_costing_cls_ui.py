"""FEAT-036 — SCR-DSK-022, SCR-DSK-023 (phần cận lâm sàng): chuỗi qua __() có bản dịch, không mã màu cứng,
chỉ gọi API costing, role cho dải lỗi/cảnh báo, đủ năm nhãn cấp phát sinh."""

import csv
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / "nc_costing" / "doctype"
RUN_JS = DIR / "nc_costing_run" / "nc_costing_run.js"
COST_JS = DIR / "nc_service_cost" / "nc_service_cost.js"
HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b(?![\w-])|rgba?\(|hsla?\(")


def _t(p):
	return p.read_text(encoding="utf-8")


class TestCostingClsUI(unittest.TestCase):
	def test_chuoi_moi_co_trong_vi_csv(self):
		with open(ROOT / "translations" / "vi.csv", encoding="utf-8", newline="") as fh:
			vi = {row[0]: row[1] for row in csv.reader(fh) if len(row) >= 2}
		for f in (RUN_JS, COST_JS):
			used = set(re.findall(r"__\(\s*\"((?:[^\"\\]|\\.)*)\"", _t(f)))
			self.assertEqual(sorted(used - set(vi)), [], f.name)
		for key in (
			"Paraclinical",
			"Estimated from plan",
			"Low volume",
			"How k is calculated",
			"Results by test system",
		):
			self.assertIn(key, vi)

	def test_khong_ma_mau_cung(self):
		for f in (RUN_JS, COST_JS):
			self.assertIsNone(HEX.search(_t(f)), f.name)

	def test_chi_goi_api_costing(self):
		for f in (RUN_JS, COST_JS):
			self.assertNotRegex(_t(f), r'method:\s*"(?!normcore\.api\.costing\.)[a-z_.]+\.')

	def test_role_cho_dai_loi_va_canh_bao(self):
		self.assertIn('role="status"', _t(RUN_JS))
		self.assertIn('role="alert"', _t(COST_JS))
		self.assertIn('role="status"', _t(COST_JS))

	def test_nhan_mau_co_chu(self):
		t = _t(RUN_JS) + _t(COST_JS)
		for color in ("blue", "orange", "yellow"):
			self.assertRegex(t, rf"indicator-pill {color}\">\$\{{[^}}]*\}}|indicator-pill {color}\">")
		self.assertIn("Ước tính từ kế hoạch", _t(COST_JS))

	def test_du_nam_nhan_cap_phat_sinh(self):
		api = (ROOT / "api" / "costing.py").read_text(encoding="utf-8")
		for label in ("Theo kết quả", "Theo ống mẫu", "Theo mẻ", "Theo ngày-máy", "Theo kỳ"):
			self.assertIn(f'"{label}"', api)

	def test_du_lieu_chen_html_qua_escape(self):
		for f in (RUN_JS, COST_JS):
			self.assertIn("escape_html", _t(f))

	def test_hien_thi_k_sau_chu_so(self):
		self.assertIn("num(s.k_factor, 6)", _t(COST_JS))
		self.assertIn("num(t.k_factor, 6)", _t(RUN_JS))
