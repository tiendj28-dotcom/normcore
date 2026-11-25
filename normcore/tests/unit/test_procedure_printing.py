"""Ngữ cảnh in quy trình (FR-PROC-010; TC-PROC-07 mức đơn vị). DOCX kiểm ở tests/test_procedure_docx.py (cần python-docx)."""

import unittest
from datetime import date

from normcore.procedure.printing import print_context


def _doc(state="Nháp", **kw):
	d = {
		"name": "QT-DV1-K1-v1",
		"version_no": 1,
		"workflow_state": state,
		"service_name": "Xét nghiệm X",
		"department": "Khoa Hóa sinh",
		"overview": "<p>Đại cương mẫu</p>",
		"steps": [
			{
				"step_id": "S001",
				"phase": "Thực hiện",
				"step_title": "Lấy mẫu",
				"description": "Mô tả A",
				"reference_minutes": 5,
			},
		],
		"resources": [{"step_id": "S001", "resource_text": "Găng tay", "quantity": 2, "uom": "đôi"}],
	}
	d.update(kw)
	return d


SIGS = {
	"drafter": {"user": "a@x", "date": date(2026, 1, 2)},
	"director": {"user": "d@x", "date": date(2026, 1, 9)},
}


class TestPrinting(unittest.TestCase):
	def test_TC_PROC_07_ban_nhap_co_du_thao(self):
		ctx = print_context(_doc(), {}, date(2026, 2, 1))
		self.assertTrue(ctx["is_draft"])
		self.assertEqual(ctx["watermark"], "DỰ THẢO")

	def test_TC_PROC_07_ban_ban_hanh(self):
		ctx = print_context(_doc("Đã ban hành", decision_no="123/QĐ-BV", effective_date="2026-03-05"), SIGS)
		self.assertFalse(ctx["is_draft"])
		self.assertEqual(ctx["watermark"], "")
		self.assertEqual(ctx["decision_no"], "123/QĐ-BV")
		self.assertEqual(ctx["version"], "Phiên bản 1")
		self.assertEqual(ctx["effective_date"], "05/03/2026")
		self.assertEqual(
			[s["label"] for s in ctx["signatures"]],
			["Người soạn", "Trưởng khoa", "Hội đồng chuyên môn", "Giám đốc"],
		)
		self.assertEqual(ctx["signatures"][3]["date"], "09/01/2026")

	def test_da_thay_the_khong_du_thao_co_ghi_chu(self):
		ctx = print_context(_doc("Đã thay thế"), {})
		self.assertFalse(ctx["is_draft"])
		self.assertEqual(ctx["status_note"], "Đã thay thế")

	def test_tam_phan_va_buoc_nhom_theo_giai_doan(self):
		ctx = print_context(_doc(), {})
		self.assertEqual(len(ctx["sections"]), 8)
		self.assertEqual([p["phase"] for p in ctx["phases"]], ["Thực hiện"])
		self.assertEqual(ctx["phases"][0]["steps"][0]["resources"][0]["uom"], "đôi")
