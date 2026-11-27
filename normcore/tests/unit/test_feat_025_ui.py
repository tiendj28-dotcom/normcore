"""FEAT-025: giao diện kiểm tra nhất quán và đề xuất liên kết (ui-design.md): kiểm tĩnh trên mã nguồn JS/Vue và bản dịch."""

import csv
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EDITOR = (ROOT / "public" / "js" / "procedure_editor" / "ProcedureEditor.vue").read_text(encoding="utf-8")
FORM = (ROOT / "nc_costing" / "doctype" / "nc_norm_set" / "nc_norm_set.js").read_text(encoding="utf-8")
BLOCK = FORM.split("FEAT-025, AMD-025-02", 1)[1]
VI = {r[0]: r[1] for r in csv.reader((ROOT / "translations" / "vi.csv").open(encoding="utf-8")) if len(r) > 1}


def strings(text):
	return {m.group(1).replace('\\"', '"') for m in re.finditer(r'__\(\s*"((?:[^"\\]|\\.)*)"', text)}


class TestFeat025Ui(unittest.TestCase):
	def test_moi_chuoi_giao_dien_co_ban_dich(self):
		for text in (EDITOR, FORM):
			missing = [s for s in strings(text) if s not in VI]
			self.assertEqual(missing, [])

	def test_nhan_theo_thiet_ke(self):
		self.assertEqual(VI["Check consistency"], "Kiểm tra nhất quán")
		self.assertEqual(VI["Suggest links"], "Đề xuất liên kết")
		self.assertEqual(VI["Suggested"], "Đề xuất")
		self.assertEqual(VI["Accept"], "Chấp nhận")
		self.assertEqual(VI["Remove"], "Bỏ")
		self.assertEqual(VI["Accept all"], "Chấp nhận tất cả")

	def test_trinh_soan_goi_check_consistency_va_hien_ket_qua(self):
		self.assertIn('"check_consistency"', EDITOR)
		self.assertIn('v-if="doc && doc.can_edit"', EDITOR)  # Auditor, bản đã ban hành: không có nút
		self.assertIn("aria-busy", EDITOR)
		self.assertIn('aria-live="polite"', EDITOR)
		for kind in ("missing_in_preparation", "unused_in_steps", "no_performer", "no_preparation_step"):
			self.assertIn(kind, EDITOR)
		for status in ("failed", "skipped"):  # UC-005 6a; AI tắt (disabled): không hiện gì về AI
			self.assertIn(f"'{status}'", EDITOR)
		self.assertNotIn("'disabled'", EDITOR)
		self.assertIn("consistencyStale", EDITOR)

	def test_form_goi_cac_api_norm_link(self):
		for fn in (
			"start_link_suggestion",
			"get_link_suggestion_status",
			"accept_link_suggestions",
			"reject_link_suggestion",
			"list_link_suggestions",
		):
			self.assertIn(fn, BLOCK)
		self.assertIn('const API = "normcore.api.norm_link."', BLOCK)
		self.assertIn("normcore_ai_link", BLOCK)
		self.assertIn("ai_confidence", BLOCK)
		# AI tắt: không có nút "Đề xuất liên kết"; vẫn xem và xử lý đề xuất cũ (FR-AI-008)
		self.assertIn("normcore.ai.enabled()", BLOCK)
		self.assertIn('frappe.model.can_write("NC Norm Set")', BLOCK)
		self.assertIn("data.can_edit", BLOCK)  # nút ghi chỉ khi có quyền; Auditor chỉ xem
		self.assertIn("View link suggestions", BLOCK)

	def test_luoi_va_api_norm_giu_nguyen(self):
		# AMD-025-02: lưới và api/norm.py không đổi; ba test cũ không sửa
		import subprocess

		out = subprocess.run(
			["git", "diff", "origin/develop", "--", "normcore/public/js/norm_grid/", "normcore/api/norm.py"],
			cwd=ROOT.parent,
			capture_output=True,
			text=True,
		)
		self.assertEqual(out.stdout, "")

	def test_khong_ma_mau_cung(self):
		hex_ = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(")
		self.assertIsNone(hex_.search(EDITOR))
		self.assertIsNone(hex_.search(FORM))
