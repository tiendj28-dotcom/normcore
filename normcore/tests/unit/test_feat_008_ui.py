"""FEAT-008: giao diện sửa đổi, so sánh, thu hồi (ui-design.md): kiểm tĩnh trên mã nguồn JS, Vue và vi.csv."""

import csv
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FORM = (ROOT / "nc_procedure/doctype/nc_clinical_procedure/nc_clinical_procedure.js").read_text(encoding="utf-8")
NORM_JS = (ROOT / "nc_costing/doctype/nc_norm_set/nc_norm_set.js").read_text(encoding="utf-8")
NORM_LIST = (ROOT / "nc_costing/doctype/nc_norm_set/nc_norm_set_list.js").read_text(encoding="utf-8")
VUE = (ROOT / "public/js/procedure_editor/ProcedureEditor.vue").read_text(encoding="utf-8")
PAGE = (ROOT / "nc_procedure/page/procedure_editor/procedure_editor.js").read_text(encoding="utf-8")
VI = {r[0] for r in csv.reader(open(ROOT / "translations/vi.csv", encoding="utf-8", newline="")) if r}
SOURCES = (FORM, NORM_JS, NORM_LIST, VUE)


def _strings(text):
	return set(re.findall(r'__\(\s*"((?:[^"\\]|\\.)*)"', text))


class TestFeat008Ui(unittest.TestCase):
	def test_form_co_ba_nut_va_goi_dung_api(self):
		for label in ("Revise", "Compare versions", "Withdraw"):
			self.assertIn(f'__("{label}")', FORM)
		self.assertIn("create_revision", FORM)
		self.assertIn('action: "Thu hồi"', FORM)
		self.assertIn('NC_WF + "get_review"', FORM)

	def test_thu_hoi_bat_buoc_ly_do_o_hop_thoai(self):
		self.assertRegex(FORM, r'fieldname: "reason"[^}]*reqd: 1')

	def test_nut_thu_hoi_chi_cho_director(self):
		self.assertRegex(FORM, r'"Đã ban hành" && frappe\.user\.has_role\("NC Director"\)')

	def test_norm_set_co_dai_can_cap_nhat(self):
		self.assertIn("needs_update", NORM_JS)
		self.assertIn("step_change_note", NORM_JS)
		self.assertIn('"yellow"', NORM_JS)
		self.assertIn("needs_update", NORM_LIST)

	def test_chuoi_moi_co_trong_vi_csv(self):
		for text in (FORM, NORM_JS, NORM_LIST, VUE):
			for s in _strings(text):
				if re.search(r"Revise|Compare|Withdraw|withdrawn|Needs update|draft already", s):
					self.assertIn(s, VI, s)

	def test_khong_ma_mau_cung(self):
		hex_ = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(")
		for text in SOURCES:
			self.assertIsNone(hex_.search(text))
