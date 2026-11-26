"""FEAT-025: đề xuất liên kết định mức (FR-AI-007). Chỉ dùng provider giả lập (CLAUDE.md mục 3 luật 6)."""

import frappe

from normcore.api import norm as api
from normcore.api.test_norm import DEPT, NormBase


class TestAiLinkController(NormBase):
	def _suggest(self, name, comp="DRUG", resource="TH-N12", conf=80):
		ns = frappe.get_doc("NC Norm Set", name)
		row = next(r for r in ns.lines if r.component == comp and not r.resource)
		row.resource, row.ai_suggested, row.ai_confidence = resource, 1, conf
		ns.flags.norm_action = "ai_link"
		ns.save(ignore_permissions=True)
		return row.line_id

	def _row(self, name, line_id):
		return next(r for r in frappe.get_doc("NC Norm Set", name).lines if r.line_id == line_id)

	def test_FR_AI_007_chap_nhan_bo_sua_de_xuat_controller(self):
		name = self.make_set()
		lid = self._suggest(name)
		r = self._row(name, lid)
		self.assertEqual((r.resource, r.ai_suggested, r.ai_confidence), ("TH-N12", 1, 80))
		# đường khác (form, client): không đổi được ai_suggested / ai_confidence
		ns = frappe.get_doc("NC Norm Set", name)
		row = next(x for x in ns.lines if x.line_id == lid)
		row.ai_suggested, row.ai_confidence = 0, 5
		ns.save(ignore_permissions=True)
		r = self._row(name, lid)
		self.assertEqual((r.ai_suggested, r.ai_confidence), (1, 80))
		# dòng thêm mới không tự mang đề xuất
		ns = frappe.get_doc("NC Norm Set", name)
		ns.append(
			"lines",
			{
				"service_level": 1,
				"component": "UTILITY",
				"resource_doctype": "NC Item",
				"resource": "DIEN-N12",
				"hospital_qty": 1,
				"uom": "cái",
				"basis": "Ước tính",
				"ai_suggested": 1,
				"ai_confidence": 99,
			},
		)
		ns.save(ignore_permissions=True)
		new = frappe.get_doc("NC Norm Set", name).lines[-1]
		self.assertEqual((new.ai_suggested, new.ai_confidence), (0, 0))
		# "ai_link" trả dòng về trống không đòi nguồn lực (không phải sửa dòng)
		ns = frappe.get_doc("NC Norm Set", name)
		row = next(x for x in ns.lines if x.line_id == lid)
		row.resource, row.ai_suggested, row.ai_confidence = None, 0, 0
		ns.flags.norm_action = "ai_link"
		ns.save(ignore_permissions=True)
		r = self._row(name, lid)
		self.assertEqual((r.resource, r.ai_suggested, r.ai_confidence), (None, 0, 0))
		# "ai_link" không làm đổi trạng thái
		self.assertEqual(frappe.db.get_value("NC Norm Set", name, "status"), "Nháp")
