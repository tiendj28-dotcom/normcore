"""FEAT-024: giao diện soạn dự thảo bằng AI (ui-design.md): kiểm tĩnh trên mã nguồn JS/Vue và bản dịch."""

import csv
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIALOG = (ROOT / "public" / "js" / "ai_draft_dialog.js").read_text(encoding="utf-8")
VUE = (ROOT / "public" / "js" / "procedure_editor" / "ProcedureEditor.vue").read_text(encoding="utf-8")
SERVICE = (ROOT / "nc_procedure" / "doctype" / "nc_technical_service" / "nc_technical_service.js").read_text(
	encoding="utf-8"
)
HOOKS = (ROOT / "hooks.py").read_text(encoding="utf-8")
VI = {r[0]: r[1] for r in csv.reader((ROOT / "translations" / "vi.csv").open(encoding="utf-8")) if len(r) > 1}


def strings(text):
	return {m.group(1).replace('\\"', '"') for m in re.finditer(r'__\(\s*"((?:[^"\\]|\\.)*)"', text)}


class TestFeat024Ui(unittest.TestCase):
	def test_moi_chuoi_giao_dien_co_ban_dich(self):
		for text in (DIALOG, VUE, SERVICE):
			missing = [s for s in strings(text) if s not in VI]
			self.assertEqual(missing, [])

	def test_nhan_theo_thiet_ke(self):
		self.assertEqual(VI["Suggested"], "Đề xuất")
		self.assertEqual(VI["Accept all"], "Chấp nhận tất cả")
		self.assertEqual(VI["Draft procedure"], "Soạn quy trình")

	def test_nut_soan_quy_trinh_goi_dung_api_va_an_khi_khong_quyen(self):
		self.assertIn('__("Draft procedure")', SERVICE)
		self.assertIn('frappe.model.can_create("NC Clinical Procedure")', SERVICE)
		self.assertIn("normcore.ai.enabled()", SERVICE)  # AI tắt: tạo bản nháp trống (UC-004 1a)
		self.assertIn("normcore.api.procedure.create_procedure", SERVICE)
		self.assertIn("open_ai_draft_dialog", SERVICE)
		self.assertIn("ai_draft_dialog.js", HOOKS)

	def test_hop_thoai_goi_cac_api(self):
		for fn in (
			"prepare_ai_draft",
			"search_extra_sources",
			"start_ai_draft",
			"get_ai_draft_status",
			"create_procedure",
		):
			self.assertIn(fn, DIALOG)
		self.assertIn("normcore_ai_draft", DIALOG)
		self.assertIn("confirm_no_source", DIALOG)
		self.assertIn('aria-current="step"', DIALOG)

	def test_trinh_soan_co_chap_nhan_bo_va_nhan_quan_he(self):
		for fn in ("accept_suggestions", "reject_suggestion"):
			self.assertIn(fn, VUE)
		for text in ("Accept all", "Suggested", "Next suggestion", "Open source"):
			self.assertIn(f'__("{text}")', VUE)
		self.assertIn("ai_suggested", VUE)
		self.assertIn("relationsOf", VUE)
		self.assertIn("can_edit", VUE)  # nút ghi chỉ hiện khi có quyền sửa (Auditor chỉ đọc)

	def test_khong_ma_mau_cung(self):
		hex_ = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(")
		self.assertIsNone(hex_.search(DIALOG))
		self.assertIsNone(hex_.search(VUE))
