"""Kiểm điều kiện gửi duyệt (FR-PROC-008, FR-PROC-012). Thuần Python, không cần site."""

import unittest

from normcore.procedure.validation import submit_errors


def _step(sid, phase="Thực hiện", desc="Mô tả", ai=0):
	return {"step_id": sid, "phase": phase, "description": desc, "ai_suggested": ai}


def _res(rid, qty=1, uom="cái", ai=0):
	return {"resource_row_id": rid, "quantity": qty, "uom": uom, "ai_suggested": ai}


def _cit(relation="Theo hướng dẫn", reason="", section="Chỉ định", step=""):
	return {
		"relation": relation,
		"deviation_reason": reason,
		"target_section": section,
		"target_step_id": step,
	}


class TestSubmitErrors(unittest.TestCase):
	def test_hop_le_khong_loi(self):
		self.assertEqual(submit_errors([_step("S001")], [_res("R001")], [_cit()]), [])

	def test_TC_PROC_05_khac_biet_thieu_ly_do(self):
		errs = submit_errors([_step("S001")], [], [_cit("Khác biệt", "  ", "Chỉ định")])
		self.assertEqual(len(errs), 1)
		self.assertIn("dòng 1", errs[0])
		self.assertIn("Chỉ định", errs[0])
		self.assertIn("Khác biệt", errs[0])

	def test_TC_PROC_05_khac_biet_co_ly_do_hop_le(self):
		self.assertEqual(
			submit_errors([_step("S001")], [], [_cit("Khác biệt", "Có lý do")]), []
		)

	def test_TC_PROC_05_trich_dan_theo_buoc(self):
		errs = submit_errors([_step("S001")], [], [_cit("Khác biệt", "", "", "S001")])
		self.assertIn("S001", errs[0])

	def test_TC_PROC_06_liet_ke_du_ba_loi(self):
		steps = [_step("S001", phase="Chuẩn bị"), _step("S002", phase="Chuẩn bị", desc=" ")]
		errs = submit_errors(steps, [_res("R001", uom="")], [])
		self.assertEqual(len(errs), 3)
		self.assertIn("Thực hiện", errs[0])
		self.assertIn("S002", errs[1])
		self.assertIn("R001", errs[2])
		self.assertIn("đơn vị", errs[2])

	def test_thieu_so_luong(self):
		for q in (None, 0, -1):
			errs = submit_errors([_step("S001")], [_res("R001", qty=q)], [])
			self.assertEqual(len(errs), 1)
			self.assertIn("số lượng", errs[0])

	def test_thu_tu_co_dinh_va_ai_chua_xu_ly(self):
		errs = submit_errors(
			[_step("S001", phase="Chuẩn bị", desc="", ai=1)],
			[_res("R001", qty=0, uom="", ai=1)],
			[_cit("Khác biệt")],
		)
		self.assertEqual(len(errs), 7)
		self.assertIn("Thực hiện", errs[0])
		self.assertIn("thiếu mô tả", errs[1])
		self.assertIn("số lượng", errs[2])
		self.assertIn("đơn vị", errs[3])
		self.assertIn("Khác biệt", errs[4])
		self.assertIn("AI", errs[5])
		self.assertIn("AI", errs[6])

	def test_khong_sua_dau_vao(self):
		steps = [_step("S001")]
		submit_errors(steps, [], [])
		self.assertEqual(steps, [_step("S001")])
