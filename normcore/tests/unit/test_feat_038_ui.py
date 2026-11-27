"""FEAT-038: giao diện đề xuất định mức từ tài liệu của hãng (ui-design.md): kiểm tĩnh mã nguồn JS và bản dịch."""

import csv
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHARED = (ROOT / "public" / "js" / "cls_norm_suggest.js").read_text(encoding="utf-8")
PLAN = (ROOT / "nc_costing" / "doctype" / "nc_qc_plan" / "nc_qc_plan.js").read_text(encoding="utf-8")
NORM_SET = (ROOT / "nc_costing" / "doctype" / "nc_norm_set" / "nc_norm_set.js").read_text(encoding="utf-8")
LEGAL = (ROOT / "nc_library" / "doctype" / "nc_legal_document" / "nc_legal_document.js").read_text(
	encoding="utf-8"
)
HOOKS = (ROOT / "hooks.py").read_text(encoding="utf-8")
FRAGMENT = ROOT / "translations" / "vi.d" / "FEAT-038.csv"
VI = {r[0]: r[1] for r in csv.reader(FRAGMENT.open(encoding="utf-8")) if len(r) > 1}
VI_ALL = {
	r[0]: r[1] for r in csv.reader((ROOT / "translations" / "vi.csv").open(encoding="utf-8")) if len(r) > 1
}


def strings(text):
	return {m.group(1).replace('\\"', '"') for m in re.finditer(r'__\(\s*"((?:[^"\\]|\\.)*)"', text)}


class TestFeat038Ui(unittest.TestCase):
	def test_chi_goi_api_cls_norm_ai(self):
		self.assertIn('const API = "normcore.api.cls_norm_ai."', SHARED)
		called = set(re.findall(r'call\(\s*"(\w+)"', SHARED))
		self.assertEqual(
			called,
			{
				"start_cls_norm_suggestion",
				"get_cls_norm_suggestion_status",
				"list_cls_norm_suggestions",
				"accept_cls_norm_suggestion",
				"reject_cls_norm_suggestion",
				"link_cls_norm_suggestion",
			},
		)
		self.assertNotIn("normcore.api.norm.", SHARED)
		self.assertNotIn("normcore.api.norm_link.", SHARED)
		self.assertIn("normcore_cls_norm_ai", SHARED)

	def test_nut_theo_ai_bat_va_quyen(self):
		# FR-AI-015: AI tắt thì không có nút "AI đề xuất định mức"; đề xuất cũ vẫn xem, xử lý được (FR-AI-008)
		self.assertIn("normcore.ai.enabled() && data.can_edit", SHARED)
		self.assertIn("row.can_accept", SHARED)
		self.assertIn("row.can_edit", SHARED)
		self.assertIn(
			"if (data.pending)", SHARED
		)  # nút "Xem đề xuất AI" cho mọi người đọc được (gồm NC Auditor)
		self.assertNotIn("Accept all", SHARED)  # không có "Chấp nhận tất cả" (ASM-038-08)

	def test_trang_thai_va_nhan_theo_thiet_ke(self):
		for color, text in (("purple", "Suggested"), ("green", "Follows guideline"), ("red", "No basis yet")):
			self.assertRegex(SHARED, rf'"{color}", __\("{text}"\)')
		self.assertIn('"orange", __("Not in catalog")', SHARED)
		self.assertEqual(VI["Follows guideline"], "Theo hướng dẫn")
		self.assertEqual(VI["No basis yet"], "Chưa có căn cứ")
		self.assertEqual(VI_ALL["Suggested"], "Đề xuất")
		self.assertEqual(VI["Reject"], "Bỏ")
		self.assertEqual(VI_ALL["Accept"], "Chấp nhận")
		self.assertEqual(VI["AI norm suggestion"], "AI đề xuất định mức")

	def test_moi_chuoi_giao_dien_co_ban_dich(self):
		for text in (SHARED, PLAN, NORM_SET, LEGAL):
			missing = [s for s in strings(text) if s not in VI_ALL]
			self.assertEqual(missing, [])

	def test_form_goi_attach(self):
		self.assertIn("// FEAT-038", PLAN)
		self.assertIn("normcore.cls_norm_ai.attach(frm, frm.doc.test_system)", PLAN)
		self.assertIn("// FEAT-038", NORM_SET)
		self.assertIn("normcore.cls_norm_ai.attach(frm, frm.doc.test_system, { draft_only: true })", NORM_SET)
		# khối FEAT-038 ngoài khối FEAT-014 và FEAT-025
		self.assertNotIn("cls_norm_ai", NORM_SET.split("FEAT-025, AMD-025-02", 1)[1])

	def test_hooks_doctype_js(self):
		ns = {}
		exec(re.search(r"doctype_js = \{.*?\n\}", HOOKS, re.S).group(0), ns)
		js = ns["doctype_js"]
		self.assertEqual(js["NC Technical Service"], "public/js/ai_draft_dialog.js")
		self.assertEqual(js["NC QC Plan"], "public/js/cls_norm_suggest.js")
		self.assertEqual(js["NC Norm Set"], "public/js/cls_norm_suggest.js")

	def test_form_van_ban_tai_lieu_cua_hang(self):
		self.assertIn('"Tài liệu của hãng"', LEGAL)
		self.assertIn('frm.set_query("linked_doctype", "related_resources"', LEGAL)
		self.assertIn('["NC Item", "NC Equipment"]', LEGAL)

	def test_khong_ma_mau_cung(self):
		self.assertNotRegex(SHARED, r"#[0-9a-fA-F]{3,6}\b")
		self.assertNotRegex(SHARED, r"color:\s*#")

	def test_luoi_va_api_norm_khong_doi(self):
		out = subprocess.run(
			["git", "diff", "origin/develop", "--", "normcore/public/js/norm_grid/", "normcore/api/norm.py"],
			cwd=ROOT.parent,
			capture_output=True,
			text=True,
		)
		self.assertEqual(out.stdout, "")
