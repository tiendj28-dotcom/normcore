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

	def test_K3_du_phong_khi_nut_bien_bi_khoa(self):
		# Bước chuyển tới đầu/cuối: nút vừa bấm bị disabled, tiêu điểm sang nút còn lại của cùng bước (ASM-064)
		body = self.vue.split("move(i, delta, ev) {", 1)[1].split("onType()", 1)[0]
		self.assertIn("stepId", body)
		self.assertRegex(body, r"\|\|\s*this\.\$el\.querySelector\(`\[data-move\^=")

	def test_C4_placeholder_dung_mau_text_muted(self):
		css = self.vue.split("<style", 1)[1]
		m = re.search(r"::placeholder\s*\{([^}]*)\}", css)
		self.assertIsNotNone(m)
		self.assertIn("var(--text-muted)", m.group(1))
		self.assertIn("opacity: 1", m.group(1))


class TestFeat006ListAndErrorStrip(unittest.TestCase):
	"""NORM-23: L1 (SCR-DSK-007) và E15 (SCR-DSK-009), ui-design.md FEAT-006."""

	@classmethod
	def setUpClass(cls):
		import json

		cls.vue = (UI_DIR / "ProcedureEditor.vue").read_text(encoding="utf-8")
		dt = ROOT / "nc_procedure" / "doctype" / "nc_clinical_procedure" / "nc_clinical_procedure.json"
		cls.fields = {f["fieldname"]: f for f in json.loads(dt.read_text(encoding="utf-8"))["fields"]}
		with open(ROOT / "translations" / "vi.csv", encoding="utf-8", newline="") as f:
			cls.vi = {row[0]: row[1] for row in csv.reader(f) if len(row) >= 2}

	def test_L1_cot_danh_sach_du_bon_truong(self):
		for fn in ("technical_service", "department", "version_no", "workflow_state"):
			self.assertTrue(self.fields[fn].get("in_list_view"), fn)

	def test_L1_list_view_settings_du_cot_cho_man_1366(self):
		# Desk cắt còn 4 cột ở ≤ 1366px (Tên, Tag, Trạng thái + 1); cần total_fields ≥ 6 để hiện đủ
		import ast

		# đọc bằng ast: CI unit không cài frappe nên không import normcore.setup
		tree = ast.parse((ROOT / "setup.py").read_text(encoding="utf-8"))
		const = next(
			ast.literal_eval(n.value)
			for n in tree.body
			if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "LIST_VIEW_TOTAL_FIELDS"
		)
		self.assertGreaterEqual(int(const["NC Clinical Procedure"]), 6)
		hooks = (ROOT / "hooks.py").read_text(encoding="utf-8")
		self.assertIn("normcore.setup.ensure_list_view_settings", hooks.split("after_migrate", 1)[1])

	def test_L1_ten_doctype_co_ban_dich(self):
		for name in (
			"NC Clinical Procedure",
			"NC Procedure Step",
			"NC Procedure Resource",
			"NC Procedure Citation",
		):
			self.assertTrue(self.vi.get(name, "").strip(), name)
		self.assertEqual(self.vi["NC Clinical Procedure"], "Quy trình kỹ thuật")  # data-model.md, srs.md

	def test_E15_loi_api_hien_o_dai_alert_khong_msgprint(self):
		self.assertNotIn("msgprint", self.vue)
		call = self.vue.split("call(method, args) {", 1)[1].split("refreshList()", 1)[0]
		self.assertIn("silent: true", call)
		self.assertIn("messageFromError", call)
		self.assertRegex(self.vue, r'<div v-if="error"[^>]*role="alert"')

	def test_E15_tao_quy_trinh_giu_thong_bao_may_chu_khi_khong_co_ban_co_san(self):
		body = self.vue.split("this.call(create ?", 1)[1].split("saveSection(", 1)[0]
		self.assertIn("const message = this.error", body)
		self.assertGreaterEqual(body.count("this.error = message"), 2)

	def test_E15_loi_403_doc_noi_dung_tu_responseJSON(self):
		# 403 (_deny): Desk gọi error_callback() không đối số; e là jqXHR, nội dung ở e.responseJSON
		self.assertIn("messageFromError(e && e.responseJSON)", self.vue)
		fn = self.vue.split("function messageFromError(r) {", 1)[1].split("\nexport default", 1)[0]
		self.assertIn("_server_messages", fn)
