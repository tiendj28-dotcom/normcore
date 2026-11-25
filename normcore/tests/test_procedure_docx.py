"""DOCX quy trình (FR-PROC-011; TC-PROC-07): cần python-docx nên chạy ở job site (thư viện khai trong pyproject.toml)."""

from datetime import date

from frappe.tests.utils import FrappeTestCase

from normcore.exports.procedure_docx import build_docx, docx_text
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


class TestDocx(FrappeTestCase):
	def test_TC_PROC_07_ban_nhap_co_du_thao(self):
		ctx = print_context(_doc(), {}, date(2026, 2, 1))
		self.assertIn("DỰ THẢO", docx_text(build_docx(ctx)))

	def test_TC_PROC_07_ban_ban_hanh(self):
		ctx = print_context(_doc("Đã ban hành", decision_no="123/QĐ-BV", effective_date="2026-03-05"), SIGS)
		text = docx_text(build_docx(ctx))
		self.assertNotIn("DỰ THẢO", text)
		for s in (
			"123/QĐ-BV",
			"Phiên bản 1",
			"05/03/2026",
			"Người soạn",
			"Trưởng khoa",
			"Hội đồng chuyên môn",
			"Giám đốc",
			"09/01/2026",
		):
			self.assertIn(s, text)

	def test_docx_cung_noi_dung_voi_ngu_canh(self):
		text = docx_text(build_docx(print_context(_doc(), {})))
		for s in ("Đại cương mẫu", "Lấy mẫu", "Mô tả A", "Găng tay", "đôi", "Xét nghiệm X", "QT-DV1-K1-v1"):
			self.assertIn(s, text)
