"""FEAT-016 — SCR-DSK-020, SCR-DSK-021: không mã màu cứng, chuỗi qua __() có bản dịch, đúng tên API."""

import csv
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / "nc_costing" / "doctype"
FILES = [
	DIR / "nc_accounting_import" / "nc_accounting_import.js",
	DIR / "nc_accounting_import" / "nc_accounting_import_list.js",
	DIR / "nc_service_volume" / "nc_service_volume_list.js",
	DIR / "nc_cost_center_driver" / "nc_cost_center_driver_list.js",
	DIR / "nc_account_mapping" / "nc_account_mapping_list.js",
	DIR / "nc_allocation_rule" / "nc_allocation_rule.js",
]
HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b(?![\w-])|rgba?\(|hsla?\(")
API = (ROOT / "api" / "accounting.py").read_text(encoding="utf-8")


def _text(p):
	return p.read_text(encoding="utf-8")


class TestAccountingUI(unittest.TestCase):
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

	def test_nut_goi_dung_api_whitelisted(self):
		text = _text(FILES[0])
		for fn in (
			"get_import_summary",
			"update_line",
			"reapply_mapping",
			"reload_file",
			"finalize",
			"download_template",
		):
			self.assertIn(fn, text)
			self.assertRegex(API, rf"@frappe.whitelist\(\)\ndef {fn}\(")

	def test_du_lieu_chen_html_qua_escape(self):
		self.assertIn("escape_html", _text(FILES[0]))

	def test_nut_nhap_excel_tren_ba_danh_sach(self):
		for f, key in zip(
			FILES[2:5], ("nc_service_volume", "nc_cost_center_driver", "nc_account_mapping"), strict=True
		):
			self.assertIn(f'import_set: "{key}"', _text(f))

	def test_workspace_co_nhom_ke_toan(self):
		text = _text(ROOT / "nc_core" / "workspace" / "normcore" / "normcore.json")
		for dt in (
			"NC Accounting Import",
			"NC Account Mapping",
			"NC Service Volume",
			"NC Cost Center Driver",
			"NC Allocation Rule",
		):
			self.assertIn(f'"link_to": "{dt}"', text)
