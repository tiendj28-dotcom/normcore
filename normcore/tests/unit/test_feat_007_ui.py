"""FEAT-007: giao diện duyệt (ui-design.md): kiểm tĩnh trên mã nguồn Vue và form JS."""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VUE = (ROOT / "public" / "js" / "procedure_editor" / "ProcedureEditor.vue").read_text(encoding="utf-8")
FORM = (ROOT / "nc_procedure" / "doctype" / "nc_clinical_procedure" / "nc_clinical_procedure.js").read_text(
	encoding="utf-8"
)
LIST = (
	ROOT / "nc_procedure" / "doctype" / "nc_clinical_procedure" / "nc_clinical_procedure_list.js"
).read_text(encoding="utf-8")
STATES = (
	"Nháp",
	"Chờ trưởng khoa duyệt",
	"Chờ hội đồng thẩm định",
	"Chờ ban hành",
	"Đã ban hành",
	"Đã thay thế",
	"Đã thu hồi",
)


class TestFeat007Ui(unittest.TestCase):
	def test_trinh_soan_goi_api_duyet(self):
		for fn in (
			"get_review",
			"apply_action",
			"add_review_comment",
			"set_comment_resolved",
			"download_pdf",
			"download_docx",
		):
			self.assertIn(fn, VUE)

	def test_nut_chi_hien_theo_actions_cua_may_chu(self):
		self.assertIn("review.actions.includes", VUE)
		self.assertIn("primaryActions", VUE)

	def test_auditor_khong_co_bieu_mau_y_kien(self):
		self.assertIn('can_create("NC Review Comment")', VUE)

	def test_hop_thoai_tu_choi_bat_buoc_ly_do_va_ban_hanh_co_so_qd_ngay(self):
		self.assertRegex(VUE, r'fieldname: "reason"[^}]*reqd: 1')
		self.assertIn('fieldname: "decision_no"', VUE)
		self.assertIn('fieldname: "effective_date"', VUE)

	def test_danh_sach_du_bay_trang_thai_co_chu(self):
		for s in STATES:
			self.assertIn(f'"{s}"', LIST)
			self.assertIn(f'"{s}"', VUE)

	def test_form_chan_workflow_action_va_goi_apply_action(self):
		self.assertIn("before_workflow_action", FORM)
		self.assertIn("apply_action", FORM)
		self.assertNotIn("apply_workflow", re.sub(r"//[^\n]*", "", FORM))

	def test_khong_ma_mau_cung(self):
		hex_ = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(")
		for text in (VUE, FORM, LIST):
			self.assertIsNone(hex_.search(text))
