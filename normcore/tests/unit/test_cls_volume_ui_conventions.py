"""FEAT-035 — SCR-DSK-037, SCR-DSK-021: không mã màu cứng, chuỗi qua __() có bản dịch, đúng khóa bộ nhập."""

import csv
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / "nc_costing" / "doctype"
LISTS = {
	DIR / "nc_test_system_volume" / "nc_test_system_volume_list.js": "nc_test_system_volume",
	DIR / "nc_equipment_usage" / "nc_equipment_usage_list.js": "nc_equipment_usage",
	DIR / "nc_stock_issue_actual" / "nc_stock_issue_actual_list.js": "nc_stock_issue_actual",
}
FILES = [
	*LISTS,
	DIR / "nc_test_system_volume" / "nc_test_system_volume.js",
	DIR / "nc_equipment_usage" / "nc_equipment_usage.js",
	DIR / "nc_stock_issue_actual" / "nc_stock_issue_actual.js",
	DIR / "nc_service_volume" / "nc_service_volume_list.js",
	DIR / "nc_test_system" / "nc_test_system.js",
]
HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b(?![\w-])|rgba?\(|hsla?\(")


def _text(p):
	return p.read_text(encoding="utf-8")


class TestClsVolumeUI(unittest.TestCase):
	def test_khong_ma_mau_cung(self):
		for f in FILES:
			self.assertIsNone(HEX.search(_text(f)), f.name)

	def test_chuoi_giao_dien_co_ban_dich(self):
		with open(ROOT / "translations" / "vi.csv", encoding="utf-8", newline="") as fh:
			vi = {row[0]: row[1] for row in csv.reader(fh) if len(row) >= 2}
		for f in FILES:
			used = set(re.findall(r"__\(\s*[\"']([^\"']+)[\"']", _text(f)))
			used |= set(re.findall(r"__\(\s*`([^`$]+)`", _text(f)))
			self.assertEqual(sorted(used - set(vi)), [], f.name)
		# nhãn bốn cột test phụ khai ở bảng AUX_LABELS rồi mới qua __()
		aux = re.findall(
			r':\s*"([A-Z][A-Za-z ]+)",', _text(DIR / "nc_test_system_volume" / "nc_test_system_volume.js")
		)
		self.assertEqual(len(aux), 4)
		self.assertEqual(sorted(set(aux) - set(vi)), [])

	def test_nut_nhap_excel_dung_khoa_bo_nhap_da_dang_ky(self):
		registered = _text(ROOT / "core" / "import_sets.py")
		for f, key in LISTS.items():
			self.assertIn(f'import_set: "{key}"', _text(f))
			self.assertIn(f'key="{key}"', registered)
			self.assertIn("can_create", _text(f))

	def test_ba_danh_sach_co_bo_loc_kich_ban_mac_dinh_dung_noi(self):
		for f in list(LISTS)[:2]:
			self.assertIn('["scenario", "=", "Thực tế 12 tháng"]', _text(f))

	def test_lien_ket_scr_dsk_021_sang_037(self):
		text = _text(DIR / "nc_service_volume" / "nc_service_volume_list.js")
		self.assertIn('frappe.set_route("List", "NC Test System Volume")', text)
		self.assertIn('import_set: "nc_service_volume"', text)  # nút cũ giữ nguyên

	def test_khoi_tinh_trang_co_chu_va_escape(self):
		text = _text(DIR / "nc_test_system" / "nc_test_system.js")
		self.assertIn("estimated", text)
		self.assertIn("escape_html", text)

	def test_workspace_co_nhom_san_luong_cls(self):
		text = _text(ROOT / "nc_core" / "workspace" / "normcore" / "normcore.json")
		for dt in ("NC Test System Volume", "NC Equipment Usage", "NC Stock Issue Actual"):
			self.assertIn(f'"link_to": "{dt}"', text)
