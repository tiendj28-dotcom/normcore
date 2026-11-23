"""FEAT-031 — SCR-DSK-032, SCR-DSK-006 (khối Cận lâm sàng): không mã màu cứng, chuỗi qua __() có bản dịch, gọi đúng API."""

import csv
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TS = ROOT / "nc_costing" / "doctype" / "nc_test_system"
SVC = ROOT / "nc_procedure" / "doctype" / "nc_technical_service"
FILES = [TS / "nc_test_system.js", TS / "nc_test_system_list.js", SVC / "nc_technical_service.js"]
HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b(?![\w-])|rgba?\(|hsla?\(")


def _text(path):
	return path.read_text(encoding="utf-8")


class TestTestSystemUI(unittest.TestCase):
	def test_khong_ma_mau_cung(self):
		for f in FILES:
			self.assertIsNone(HEX.search(_text(f).replace("#nc-chain-price", "")), f.name)

	def test_chuoi_giao_dien_co_ban_dich(self):
		with open(ROOT / "translations" / "vi.csv", encoding="utf-8", newline="") as f:
			vi = {row[0]: row[1] for row in csv.reader(f) if len(row) >= 2}
		for f in FILES:
			used = set(re.findall(r"__\(\s*[\"']([^\"']+)[\"']", _text(f)))
			self.assertEqual(sorted(used - set(vi)), [], f.name)

	def test_goi_dung_ten_api(self):
		self.assertIn("normcore.api.test_system.get_status", _text(FILES[0]))
		self.assertIn("normcore.api.test_system.get_service_systems", _text(FILES[2]))

	def test_du_lieu_chen_html_qua_escape(self):
		for f in (FILES[0], FILES[2]):
			self.assertIn("escape_html", _text(f), f.name)

	def test_nut_ngung_dung_dung_lai_va_xac_nhan(self):
		text = _text(FILES[0])
		for s in ("Deactivate", "Reactivate", "frappe.confirm", "frm.is_dirty()"):
			self.assertIn(s, text)
		self.assertIn("frm.perm[0]", text)

	def test_danh_sach_co_chi_bao_trang_thai_va_nut_nhap(self):
		text = _text(FILES[1])
		self.assertIn("get_indicator", text)
		self.assertIn("nc_test_system", text)

	def test_workspace_co_loi_tat_he_thong_xet_nghiem(self):
		text = _text(ROOT / "nc_core" / "workspace" / "normcore" / "normcore.json")
		self.assertIn('"link_to": "NC Test System"', text)
