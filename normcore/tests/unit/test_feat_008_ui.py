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


CMP = (ROOT / "public/js/procedure_editor/ProcedureCompare.vue").read_text(encoding="utf-8")
BUNDLE = (ROOT / "public/js/procedure_editor/procedure_editor.bundle.js").read_text(encoding="utf-8")


class TestFeat008Compare(unittest.TestCase):
	def test_route_compare(self):
		self.assertIn('"compare"', PAGE)
		self.assertIn("show(", PAGE)
		self.assertIn("show(", BUNDLE)
		self.assertIn("<ProcedureCompare", VUE)
		self.assertIn("ProcedureCompare", BUNDLE)
		self.assertIn('"compare"', VUE)

	def test_goi_api_so_sanh(self):
		self.assertIn("compare_versions", CMP)
		self.assertIn("list_versions", CMP)

	def test_nhan_them_bo_doi_co_chu(self):
		for label in ("Added", "Removed", "Changed"):
			self.assertIn(f'__("{label}")', CMP)
			self.assertIn(label, VI)
		for cls in ("green", "red", "yellow"):
			self.assertIn(f'indicator-pill {cls}"', CMP)

	def test_ba_khoi_va_trang_thai(self):
		for label in ("Sections", "Steps", "Resource lines"):
			self.assertIn(f'__("{label}")', CMP)
		self.assertIn("v-else-if=\"error\"", CMP)
		self.assertIn("versions.length < 2", CMP)
		self.assertIn("Show differences only", CMP)

	def test_ban_phim_va_tiep_can(self):
		self.assertIn("@keydown.alt.left", CMP)
		self.assertIn("@keydown.alt.right", CMP)
		self.assertIn("@keydown.enter", CMP)
		self.assertIn('scope="col"', CMP)

	def test_trinh_soan_co_ba_nut_khi_chi_doc(self):
		for fn in ("create_revision", '"Thu hồi"', "openCompare"):
			self.assertIn(fn, VUE)
		self.assertIn("review.actions.includes(withdrawAction)", VUE)

	def test_chuoi_so_sanh_co_trong_vi_csv(self):
		for s in _strings(CMP):
			self.assertIn(s, VI, s)

	def test_khong_ma_mau_cung_trong_so_sanh(self):
		self.assertIsNone(re.search(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(", CMP))
