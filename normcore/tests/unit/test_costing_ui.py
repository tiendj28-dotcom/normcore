"""FEAT-015 — SCR-DSK-022, SCR-DSK-023: không mã màu cứng, chuỗi qua __() có bản dịch, đúng tên API, có role=alert."""

import csv
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / "nc_costing" / "doctype"
FILES = [
	DIR / "nc_costing_run" / "nc_costing_run.js",
	DIR / "nc_costing_run" / "nc_costing_run_list.js",
	DIR / "nc_service_cost" / "nc_service_cost.js",
	DIR / "nc_service_cost" / "nc_service_cost_list.js",
]
HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b(?![\w-])|rgba?\(|hsla?\(")
API = (ROOT / "api" / "costing.py").read_text(encoding="utf-8")


def _text(p):
	return p.read_text(encoding="utf-8")


class TestCostingUI(unittest.TestCase):
	def test_tep_ton_tai(self):
		for f in FILES:
			self.assertTrue(f.is_file(), f.name)

	def test_khong_ma_mau_cung(self):
		for f in FILES:
			self.assertIsNone(HEX.search(_text(f)), f.name)

	def test_chuoi_giao_dien_co_ban_dich(self):
		with open(ROOT / "translations" / "vi.csv", encoding="utf-8", newline="") as fh:
			vi = {row[0]: row[1] for row in csv.reader(fh) if len(row) >= 2}
		for f in FILES:
			used = set(re.findall(r"__\(\s*\"((?:[^\"\\]|\\.)*)\"", _text(f)))
			self.assertEqual(sorted(used - set(vi)), [], f.name)

	def test_chi_goi_api_whitelisted_cua_costing(self):
		called = set()
		for f in FILES:
			called |= set(re.findall(r'API \+ "(\w+)"', _text(f)))
			self.assertNotRegex(_text(f), r'method:\s*"(?!normcore\.api\.costing\.)[a-z_.]+\.', f.name)
		self.assertEqual(
			called, {"get_progress", "get_run_results", "start_costing", "check_scope", "get_explanation"}
		)
		for fn in called:
			self.assertRegex(API, rf"@frappe.whitelist\(\)\ndef {fn}\(")

	def test_du_lieu_chen_html_qua_escape(self):
		for f in (FILES[0], FILES[2]):
			self.assertIn("escape_html", _text(f))

	def test_dai_loi_co_role_alert(self):
		self.assertIn('role="alert"', _text(FILES[2]))
		self.assertIn('role="alert"', _text(FILES[0]))

	def test_nut_giu_chuoi_cu(self):
		t = _text(FILES[0])
		self.assertIn('__("Run costing")', t)
		self.assertIn('__("View costing results")', t)

	def test_hanh_dong_theo_trang_thai(self):
		t = _text(FILES[0])
		self.assertIn('["Nháp", "Tính lỗi", "Đã tính"].includes(frm.doc.status)', t)
		self.assertIn('status: "Đã chốt"', t)  # accounting_import chỉ chọn lần nhập đã chốt
		self.assertIn("normcore_costing_progress", t)
		self.assertNotIn("Khóa", t.replace("Đã khóa", ""))  # khóa, nhân bản là FEAT-018
