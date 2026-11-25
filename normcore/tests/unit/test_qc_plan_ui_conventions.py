"""FEAT-032 — SCR-DSK-032 (thẻ, nút), SCR-DSK-033, SCR-DSK-034: không mã màu cứng, chuỗi qua __() có bản dịch, gọi đúng API."""

import csv
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DT = ROOT / "nc_costing" / "doctype"
QP = DT / "nc_qc_plan" / "nc_qc_plan.js"
EQA = DT / "nc_eqa_program" / "nc_eqa_program.js"
EQA_LIST = DT / "nc_eqa_program" / "nc_eqa_program_list.js"
TS = DT / "nc_test_system" / "nc_test_system.js"
FILES = [QP, EQA, EQA_LIST, TS]
HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b(?![\w-])|rgba?\(|hsla?\(")


def _text(path):
	return path.read_text(encoding="utf-8")


class TestQcPlanUI(unittest.TestCase):
	def test_khong_ma_mau_cung(self):
		for f in FILES:
			self.assertIsNone(HEX.search(_text(f)), f.name)

	def test_chuoi_giao_dien_co_ban_dich(self):
		with open(ROOT / "translations" / "vi.csv", encoding="utf-8", newline="") as f:
			vi = {row[0]: row[1] for row in csv.reader(f) if len(row) >= 2}
		for f in FILES:
			used = set(re.findall(r"__\(\s*[\"']([^\"']+)[\"']", _text(f)))
			self.assertEqual(sorted(used - set(vi)), [], f.name)

	def test_goi_dung_ten_api(self):
		self.assertIn("normcore.api.qc_plan.estimate_tests", _text(QP))
		self.assertIn("normcore.api.qc_plan.missing_iqc_warning", _text(QP))
		self.assertIn("normcore.api.qc_plan.eqa_summary", _text(EQA))

	def test_chong_doi_300ms(self):
		for f in (QP, EQA):
			self.assertIn("300", _text(f), f.name)

	def test_du_lieu_chen_html_qua_escape(self):
		for f in (QP, EQA, TS):
			self.assertIn("escape_html", _text(f), f.name)

	def test_nut_ke_hoach_chat_luong_kiem_quyen_tao(self):
		text = _text(TS)
		self.assertIn("frappe.model.can_create(\"NC QC Plan\")", text)
		self.assertIn("frappe.new_doc(\"NC QC Plan\"", text)

	def test_bang_dich_vu_chi_goi_y_can_lam_sang(self):
		self.assertIn("is_paraclinical", _text(EQA))

	def test_workspace_co_loi_tat(self):
		text = _text(ROOT / "nc_core" / "workspace" / "normcore" / "normcore.json")
		for dt in ("NC QC Plan", "NC EQA Program"):
			self.assertIn(f'"link_to": "{dt}"', text)
