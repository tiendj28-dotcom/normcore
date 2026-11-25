"""FEAT-033 — SCR-DSK-035, SCR-DSK-036: không mã màu cứng, chuỗi qua __() có bản dịch, chỉ báo dùng lớp Desk."""

import csv
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "nc_costing" / "doctype" / "nc_equipment_compliance"
REPORT = ROOT / "nc_costing" / "report" / "nc_compliance_expiry"
FILES = [
	DOC / "nc_equipment_compliance.js",
	DOC / "nc_equipment_compliance_list.js",
	REPORT / "nc_compliance_expiry.js",
]
HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b(?![\w-])|rgba?\(|hsla?\(")


def _text(path):
	return path.read_text(encoding="utf-8")


class TestComplianceUI(unittest.TestCase):
	def test_khong_ma_mau_cung(self):
		for f in FILES:
			self.assertIsNone(HEX.search(_text(f)), f.name)

	def test_chuoi_giao_dien_co_ban_dich(self):
		with open(ROOT / "translations" / "vi.csv", encoding="utf-8", newline="") as f:
			vi = {row[0]: row[1] for row in csv.reader(f) if len(row) >= 2}
		for f in FILES:
			used = set(re.findall(r"__\(\s*[\"']([^\"']+)[\"']", _text(f)))
			self.assertTrue(used, f.name)
			self.assertEqual(sorted(used - set(vi)), [], f.name)

	def test_chi_bao_dung_lop_desk(self):
		lst = _text(FILES[0].parent / "nc_equipment_compliance_list.js")
		for status, color in (("Còn hạn", "green"), ("Sắp hết hạn", "orange"), ("Hết hạn", "red")):
			self.assertIn(f'"{status}": "{color}"', lst)
		report = _text(FILES[2])
		self.assertIn("indicator-pill", report)
		for color in ("red", "orange"):
			self.assertIn(color, report)

	def test_nut_kiem_han_chi_khi_co_quyen_ghi_va_goi_api(self):
		lst = _text(FILES[1])
		self.assertIn('frappe.model.can_write("NC Equipment Compliance")', lst)
		self.assertIn("normcore.api.compliance.run_compliance_check", lst)

	def test_du_lieu_chen_html_qua_escape(self):
		self.assertIn("escape_html", _text(FILES[0]))

	def test_workspace_va_ket_noi_thiet_bi(self):
		ws = _text(ROOT / "nc_core" / "workspace" / "normcore" / "normcore.json")
		for link in ("NC Equipment Compliance", "NC Compliance Expiry", "NC Settings"):
			self.assertIn(f'"link_to": "{link}"', ws)
		eq = json.loads(_text(ROOT / "nc_costing" / "doctype" / "nc_equipment" / "nc_equipment.json"))
		self.assertIn(
			{
				"group": "Hồ sơ tuân thủ",
				"link_doctype": "NC Equipment Compliance",
				"link_fieldname": "equipment",
			},
			eq["links"],
		)
