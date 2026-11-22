"""Quy ước giao diện (design.md mục 2, 7): không mã màu cứng; chuỗi qua __(); có bản dịch vi.csv."""

import csv
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UI_DIR = ROOT / "public" / "js" / "procedure_editor"
HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(")


class TestUIConventions(unittest.TestCase):
	def test_khong_ma_mau_cung(self):
		for p in UI_DIR.glob("*"):
			text = p.read_text(encoding="utf-8")
			self.assertIsNone(HEX.search(text), p.name)

	def test_chuoi_giao_dien_co_ban_dich(self):
		with open(ROOT / "translations" / "vi.csv", encoding="utf-8", newline="") as f:
			vi = {row[0]: row[1] for row in csv.reader(f) if len(row) >= 2}
		used = set()
		for p in UI_DIR.glob("*"):
			used |= set(re.findall(r"__\(\s*[\"']([^\"']+)[\"']", p.read_text(encoding="utf-8")))
		page_js = (ROOT / "nc_procedure" / "page" / "procedure_editor" / "procedure_editor.js").read_text(
			encoding="utf-8"
		)
		used |= set(re.findall(r"__\(\s*[\"']([^\"']+)[\"']", page_js))
		self.assertTrue(used)
		self.assertEqual(sorted(used - set(vi)), [])


class TestEditorFeat006Fixes(unittest.TestCase):
	"""NORM-22: G1, K3, C4 (NFR-USE-004, ui-design.md FEAT-006). Kiểm tĩnh trên mã nguồn Vue."""

	@classmethod
	def setUpClass(cls):
		cls.vue = (UI_DIR / "ProcedureEditor.vue").read_text(encoding="utf-8")

	def test_G1_nut_ghi_an_khi_khong_co_quyen_tao(self):
		for label in ("Create procedure", "Copy from this procedure"):
			m = re.search(r"<button[^>]*>\s*\{\{ __\(\"" + re.escape(label) + r"\"\) \}\}", self.vue)
			self.assertIsNotNone(m, label)
			self.assertIn("canCreate", m.group(0), label)
		self.assertIn('can_create("NC Clinical Procedure")', self.vue)

	def test_K3_tieu_diem_sau_khi_busy_ve_false(self):
		body = self.vue.split("move(i, delta, ev) {", 1)[1].split("onType()", 1)[0]
		# focus nằm sau khi run(...) hoàn tất (busy đã false), không nằm trong chuỗi bên trong run
		self.assertRegex(body, r"\)\)\.then\(\(\) =>\s*(//[^\n]*\n\s*)?this\.\$nextTick\(")
		inner = body.split("this.run(", 1)[1].split(".then(() => this.reload())", 1)[0]
		self.assertNotIn("focus()", inner)
		self.assertLess(body.index(".then(() => this.reload())"), body.index("btn.focus()"))

	def test_C4_placeholder_dung_mau_text_muted(self):
		css = self.vue.split("<style", 1)[1]
		m = re.search(r"::placeholder\s*\{([^}]*)\}", css)
		self.assertIsNotNone(m)
		self.assertIn("var(--text-muted)", m.group(1))
		self.assertIn("opacity: 1", m.group(1))
