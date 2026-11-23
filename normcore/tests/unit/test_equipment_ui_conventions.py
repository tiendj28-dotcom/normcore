"""FEAT-010 — SCR-DSK-018: không mã màu cứng, chuỗi qua __() có bản dịch, dữ liệu chèn HTML qua escape."""

import csv
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / "nc_costing" / "doctype"
FILES = [
	DIR / "nc_equipment" / "nc_equipment.js",
	DIR / "nc_equipment" / "nc_equipment_list.js",
	DIR / "nc_room" / "nc_room.js",
]
HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b(?![\w-])|rgba?\(|hsla?\(")


def _text(path):
	return path.read_text(encoding="utf-8")


class TestEquipmentUI(unittest.TestCase):
	def test_khong_ma_mau_cung(self):
		for f in FILES:
			self.assertIsNone(HEX.search(_text(f)), f.name)

	def test_chuoi_giao_dien_co_ban_dich(self):
		with open(ROOT / "translations" / "vi.csv", encoding="utf-8", newline="") as f:
			vi = {row[0]: row[1] for row in csv.reader(f) if len(row) >= 2}
		for f in FILES:
			used = set(re.findall(r"__\(\s*[\"']([^\"']+)[\"']", _text(f)))
			if f.name != "nc_equipment_list.js":  # nhãn danh sách là giá trị tiếng Việt của DocType
				self.assertTrue(used, f.name)
			self.assertEqual(sorted(used - set(vi)), [], f.name)

	def test_hien_thi_so_qua_ham_dinh_dang_va_loi_qua_escape(self):
		text = _text(FILES[0])
		self.assertIn("frappe.format(", text)
		self.assertIn("escape_html", text)
		self.assertIn("normcore.api.equipment.get_indicative_rate", text)
		self.assertIn("normcore.api.equipment.get_room_rate", _text(FILES[2]))

	def test_danh_sach_co_chi_bao_hinh_thuc(self):
		text = _text(FILES[1])
		self.assertIn("get_indicator", text)
		self.assertIn("acquisition_mode", text)

	def test_workspace_co_loi_tat_thiet_bi_va_phong(self):
		text = _text(ROOT / "nc_core" / "workspace" / "normcore" / "normcore.json")
		for dt in ("NC Equipment", "NC Room"):
			self.assertIn(f'"link_to": "{dt}"', text)
