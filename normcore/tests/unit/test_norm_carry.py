"""FEAT-013: mang dòng định mức sang phiên bản theo quy trình mới (FR-NORM-015, TC-NORM-08)."""

import unittest

from normcore.norm.init_from_procedure import (
	carry_lines,
	format_note,
	removed_flag,
	steps_without_lines,
)

OLD_STEPS = ["S001", "S002", "S003", "S004"]
NEW_STEPS = ["S001", "S003", "S004", "S005"]  # TC-WF-06: bỏ S002, thêm S005


def ln(lid, step, **kw):
	base = {"line_id": lid, "step_id": step, "component": "SUPPLY", "confirmed_by": "x", "confirmed_on": "d"}
	base.update(kw)
	return base


OLD = [ln("L001", "S001"), ln("L002", "S002"), ln("L003", "S003"), ln("L004", "S004")]


class TestCarry(unittest.TestCase):
	def test_TC_NORM_08_carry_lines_mang_va_danh_dau(self):
		res = carry_lines(OLD, NEW_STEPS)
		self.assertEqual(res["carried"], ["L001", "L003", "L004"])
		self.assertEqual(res["removed"], ["L002"])
		self.assertEqual(res["removed_steps"], ["S002"])
		self.assertEqual([x["line_id"] for x in res["lines"]], ["L001", "L002", "L003", "L004"])
		flags = {x["line_id"]: x.get("step_removed", 0) for x in res["lines"]}
		self.assertEqual(flags, {"L001": 0, "L002": 1, "L003": 0, "L004": 0})
		self.assertEqual(res["lines"][1]["step_id"], "S002")

	def test_TC_NORM_08_carry_lines_bo_xac_nhan(self):
		for x in carry_lines(OLD, NEW_STEPS)["lines"]:
			self.assertFalse(x.get("confirmed_by"))
			self.assertFalse(x.get("confirmed_on"))

	def test_TC_NORM_08_carry_lines_khong_doi_dau_vao(self):
		carry_lines(OLD, NEW_STEPS)
		self.assertEqual(OLD[0]["confirmed_by"], "x")

	def test_TC_NORM_08_steps_without_lines_S005(self):
		res = carry_lines(OLD, NEW_STEPS)
		self.assertEqual(steps_without_lines(NEW_STEPS, res["lines"]), ["S005"])

	def test_TC_NORM_08_carry_lines_dong_chung(self):
		res = carry_lines([ln("L009", None, service_level=1)], NEW_STEPS)
		self.assertEqual(res["carried"], ["L009"])
		self.assertEqual(res["removed"], [])
		self.assertFalse(res["lines"][0].get("step_removed"))

	def test_TC_NORM_08_carry_lines_dong_them_tay_buoc_bo(self):
		res = carry_lines([ln("L010", "S002", procedure_resource_row=None)], NEW_STEPS)
		self.assertEqual(res["removed"], ["L010"])

	def test_TC_NORM_08_carry_lines_dong_loai_tru_tinh_la_co_dong(self):
		res = carry_lines([ln("L011", "S005", is_excluded=1)], NEW_STEPS)
		self.assertEqual(steps_without_lines(NEW_STEPS, res["lines"]), ["S001", "S003", "S004"])

	def test_TC_NORM_08_carry_lines_nguon_da_co_co(self):
		res = carry_lines([ln("L002", "S002", step_removed=1)], NEW_STEPS)
		self.assertEqual(res["removed"], ["L002"])
		self.assertEqual(res["lines"][0]["step_removed"], 1)

	def test_TC_NORM_08_carry_lines_nguon_co_nhung_buoc_da_lai_co(self):
		res = carry_lines([ln("L002", "S003", step_removed=1)], NEW_STEPS)
		self.assertEqual(res["carried"], ["L002"])
		self.assertFalse(res["lines"][0]["step_removed"])

	def test_TC_NORM_08_carry_lines_quy_trinh_khong_doi_buoc(self):
		res = carry_lines(OLD, OLD_STEPS)
		self.assertEqual(res["removed"], [])
		self.assertEqual(steps_without_lines(OLD_STEPS, res["lines"]), [])

	def test_TC_NORM_08_removed_steps_khong_trung(self):
		res = carry_lines([ln("A", "S002"), ln("B", "S002")], NEW_STEPS)
		self.assertEqual(res["removed_steps"], ["S002"])

	def test_TC_NORM_08_format_note(self):
		res = carry_lines(OLD, NEW_STEPS)
		missing = steps_without_lines(NEW_STEPS, res["lines"])
		self.assertEqual(
			format_note(res, missing),
			"Theo quy trình mới: mang sang S001, S003, S004; đánh dấu bước đã bỏ S002 (L002); bước chưa có dòng S005",
		)

	def test_TC_NORM_08_format_note_rong(self):
		res = carry_lines([], [])
		self.assertEqual(
			format_note(res, []),
			"Theo quy trình mới: mang sang không có; đánh dấu bước đã bỏ không có; bước chưa có dòng không có",
		)


class TestRemovedFlag(unittest.TestCase):
	STEPS = {"S001", "S003"}

	def test_tao_phien_ban_giu_co(self):
		self.assertEqual(removed_flag({"step_id": "S002"}, None, self.STEPS, True), 1)

	def test_dong_cu_co_co_giu(self):
		self.assertEqual(removed_flag({"step_id": "S002"}, {"step_removed": 1}, self.STEPS, False), 1)

	def test_client_tu_dat_khong_co_tac_dung(self):
		self.assertEqual(removed_flag({"step_id": "S002", "step_removed": 1}, {"step_removed": 0}, self.STEPS, False), 0)

	def test_buoc_hop_le_go_co(self):
		self.assertEqual(removed_flag({"step_id": "S003"}, {"step_removed": 1}, self.STEPS, False), 0)

	def test_service_level_go_co(self):
		self.assertEqual(removed_flag({"step_id": "S002", "service_level": 1}, {"step_removed": 1}, self.STEPS, False), 0)

	def test_khong_co_buoc(self):
		self.assertEqual(removed_flag({"step_id": None}, {"step_removed": 1}, self.STEPS, True), 0)
